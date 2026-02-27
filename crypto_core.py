# crypto_core.py
import cv2
import os
import time
import shutil
import tempfile
import zipfile
import datetime
import speedtest
from drive_handler import upload_to_drive
import config
from base64 import urlsafe_b64encode
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from tkinter import messagebox

# Diğer dosyamızdan ayarları import ediyoruz
import config
from drive_handler import upload_to_drive # Drive fonksiyonunu daha sonra oluşturacağımız dosyadan alacağız

# --- ANAHTAR ÜRETİMİ ---
def generate_key(password, salt):
    """Paroladan ve verilen salt'tan güvenli bir şifreleme anahtarı oluşturur."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=config.PBKDF2_ITERATIONS,
        backend=default_backend()
    )
    return urlsafe_b64encode(kdf.derive(password.encode()))

# --- ZIP İŞLEMLERİ ---
def create_zip_from_folder(folder_path, zip_path):
    """Bir klasörü ZIP dosyası olarak sıkıştırır."""
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, folder_path)
                zipf.write(file_path, arcname)

def extract_zip_to_folder(zip_path, extract_path):
    """Bir ZIP dosyasını belirtilen klasöre çıkarır."""
    with zipfile.ZipFile(zip_path, 'r') as zipf:
        zipf.extractall(extract_path)

# --- İŞÇİ FONKSİYONLAR (WORKER THREADS) ---
def encryption_worker(filepath, password, is_folder, q):
    """(WORKER THREAD) Dosya veya klasör şifreleme işlemini yapar ve kuyruğa bilgi yollar."""
    try:
        if is_folder:
            q.put(('update', 20, 'Klasör sıkıştırılıyor...'))
            temp_dir = tempfile.gettempdir()
            folder_name = os.path.basename(filepath.rstrip('/\\'))
            temp_zip_path = os.path.join(temp_dir, f"{folder_name}_temp.zip")
            create_zip_from_folder(filepath, temp_zip_path)

            q.put(('update', 50, 'Veri okunuyor...'))
            with open(temp_zip_path, 'rb') as file:
                data_to_encrypt = file.read()
            
            original_path_to_remove = filepath
            final_encrypted_path = filepath + '.enc'
        else:
            q.put(('update', 50, 'Dosya okunuyor...'))
            with open(filepath, 'rb') as file:
                data_to_encrypt = file.read()
            
            original_path_to_remove = filepath
            final_encrypted_path = filepath + '.enc'

        q.put(('update', 70, 'Veri şifreleniyor...'))
        salt = os.urandom(config.SALT_SIZE_BYTES)
        key = generate_key(password, salt)
        fernet = Fernet(key)
        encrypted_data = fernet.encrypt(data_to_encrypt)

        q.put(('update', 90, 'Dosya yazılıyor...'))
        with open(final_encrypted_path, 'wb') as enc_file:
            enc_file.write(salt)
            enc_file.write(encrypted_data)
        
        # --- ANA DEĞİŞİKLİK BURADA ---
        # DÜZELTME: Mesajı (value, text) yerine value, text olarak ayrı ayrı gönder.
        q.put(('update', 95, 'Orijinal dosya güvenli bir şekilde siliniyor...'))

        if config.SECURE_DELETE_ENABLED:
            if is_folder:
                # original_path_to_remove, is_folder=True ise zip dosyasının yoluydu. Düzeltme:
                secure_delete_folder(filepath, config.SECURE_DELETE_PASSES)
                os.remove(temp_zip_path) # Geçici zip dosyasını da sil
            else:
                secure_delete_file(filepath, config.SECURE_DELETE_PASSES)
        else:
            if is_folder:
                shutil.rmtree(filepath)
                os.remove(temp_zip_path) # Geçici zip dosyasını da sil
            else:
                os.remove(filepath)
        # --- DEĞİŞİKLİK BİTTİ ---

        q.put(('complete', f"Şifreleme başarıyla tamamlandı:\n{final_encrypted_path}"))
    except Exception as e:
        q.put(('error', f"Şifreleme sırasında hata oluştu: {e}"))

def decryption_worker(filepath, password, q):
    """(WORKER THREAD) Deşifreleme işlemini yapar ve kuyruğa bilgi yollar."""
    try:
        q.put(('update', 30, 'Dosya okunuyor...'))
        with open(filepath, 'rb') as file:
            salt = file.read(config.SALT_SIZE_BYTES)
            encrypted_data = file.read()
        
        if len(salt) < config.SALT_SIZE_BYTES:
            raise ValueError("Geçersiz veya bozuk şifreli dosya formatı.")

        q.put(('update', 60, 'Veri deşifre ediliyor...'))
        key = generate_key(password, salt)
        fernet = Fernet(key)
        decrypted_data = fernet.decrypt(encrypted_data)

        # Deşifre edilen verinin ZIP olup olmadığını kontrol et
        # (Bu bölüm orijinal kodunuzdaki gibi kalabilir, sadelik için burayı özet geçiyorum)
        original_path = filepath.replace('.enc', '')
        is_zip = False
        try:
            with tempfile.NamedTemporaryFile(delete=False) as temp_f:
                temp_f.write(decrypted_data)
            with zipfile.ZipFile(temp_f.name, 'r'): is_zip = True
            os.remove(temp_f.name)
        except zipfile.BadZipFile:
            is_zip = False
        
        q.put(('update', 90, 'Orijinal dosya oluşturuluyor...'))
        if is_zip:
             with tempfile.NamedTemporaryFile(delete=False) as temp_f: temp_f.write(decrypted_data)
             extract_zip_to_folder(temp_f.name, original_path)
             os.remove(temp_f.name)
        else:
            with open(original_path, 'wb') as dec_file: dec_file.write(decrypted_data)
        
        os.remove(filepath)
        clear_wrong_attempts(filepath)
        q.put(('complete', f"Deşifreleme başarıyla tamamlandı:\n{original_path}"))
    except InvalidToken:
        q.put(('wrong_password', filepath))
    except Exception as e:
        q.put(('error', f"Deşifreleme sırasında hata oluştu: {e}"))

def _check_upload_speed_and_time(filepath, q=None):
    """
    İnternet upload hızını ölçer ve tahmini yüklenme süresini hesaplar.
    (Mesaj formatı diğer worker'larla %100 uyumlu hale getirildi).
    """
    try:
        file_size_bytes = os.path.getsize(filepath)
        
        if q:
            # DÜZELTME: Mesajı (value, text) yerine value, text olarak ayrı ayrı gönder.
            q.put(('update', 10, 'İnternet hızı ölçülüyor...'))
        else:
            print("İnternet hızı ölçülüyor, lütfen bekleyin...")

        st = speedtest.Speedtest()
        st.get_best_server()
        upload_speed_bps = st.upload(pre_allocate=False)
        
        if not upload_speed_bps or upload_speed_bps == 0:
            return float('inf')

        file_size_bits = file_size_bytes * 8
        estimated_time_seconds = file_size_bits / upload_speed_bps
        estimated_time_minutes = estimated_time_seconds / 60
        
        if q:
            # DÜZELTME: Mesajı (value, text) yerine value, text olarak ayrı ayrı gönder.
            q.put(('update', 20, f'Tahmini süre: {estimated_time_minutes:.1f} dakika'))
            time.sleep(2)
        else:
            print(f"Tahmini Süre: {estimated_time_minutes:.2f} dakika")

        return estimated_time_minutes
    
    except Exception as e:
        print(f"Hız ölçüm hatası: {e}")
        return float('inf')

# --- YANLIŞ GİRİŞ YÖNETİMİ ---
def _read_log_file_to_dict():
    """
    Log dosyasını okur ve içeriğini bir sözlüğe dönüştürür.
    (Nihai, '|' ayraçlı en sağlam versiyon)
    """
    log_data = {}
    if not os.path.exists(config.WRONG_ATTEMPTS_FILE):
        return log_data
    
    try:
        with open(config.WRONG_ATTEMPTS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip(): continue
                parts = line.strip().split('|', 1) 
                if len(parts) == 2:
                    filepath_key = parts[0]
                    value = parts[1]
                    log_data[filepath_key] = value
    except Exception as e:
        print(f"Uyarı: Log dosyası okunurken hata oluştu: {e}")
        return {}
            
    return log_data
def _write_dict_to_log_file(log_data):
    """
    Verilen sözlüğü log dosyasına yazar. Her zaman '|' ayracı ve UTF-8 kullanır.
    """
    try:
        with open(config.WRONG_ATTEMPTS_FILE, 'w', encoding='utf-8') as f:
            for filepath, value in log_data.items():
                f.write(f"{filepath}|{value}\n")
    except Exception as e:
        print(f"Hata: Log dosyasına yazılırken hata oluştu: {e}")
def secure_delete_file(filepath, passes=3):
    """
    Bir dosyanın üzerine belirlenen sayıda rastgele veri yazarak
    kurtarılamaz hale getirir ve ardından siler. Büyük dosyalar için hafıza dostudur.
    """
    try:
        with open(filepath, "wb") as f:
            file_size = os.path.getsize(filepath)
            chunk_size = 1024 * 1024 # 1MB'lık parçalar halinde yaz

            for _ in range(passes):
                f.seek(0) # Her seferinde dosyanın başına dön
                remaining_size = file_size
                while remaining_size > 0:
                    size_to_write = min(chunk_size, remaining_size)
                    f.write(os.urandom(size_to_write))
                    remaining_size -= size_to_write
        
        os.remove(filepath)
        print(f"DEBUG: '{filepath}' güvenli bir şekilde silindi.")
    except Exception as e:
        print(f"HATA: Güvenli silme sırasında hata oluştu: {e}")
        # Hata oluşursa, en kötü ihtimalle normal silmeyi dene
        if os.path.exists(filepath):
            os.remove(filepath)

def secure_delete_folder(folder_path, passes=3):
    """
    Bir klasör içindeki tüm dosyaları secure_delete_file ile siler
    ve ardından boş klasör yapısını kaldırır.
    """
    try:
        for root, dirs, files in os.walk(folder_path, topdown=False):
            for name in files:
                filepath = os.path.join(root, name)
                secure_delete_file(filepath, passes)
        
        # Tüm dosyalar silindikten sonra boş klasör ağacını sil
        shutil.rmtree(folder_path)
        print(f"DEBUG: '{folder_path}' klasörü ve içeriği güvenli bir şekilde silindi.")
    except Exception as e:
        print(f"HATA: Klasör güvenli silinirken hata oluştu: {e}")
        # Hata oluşursa, en kötü ihtimalle normal silmeyi dene
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)

def log_wrong_attempt(filepath):
    """
    SADECE yanlış denemeleri sayar. Limit dolarsa True, dolmazsa False döner.
    Tüm ağır işleri (hız ölçme, kilitleme) 'decision_worker'a bırakır.
    """
    normalized_filepath = os.path.normcase(os.path.normpath(filepath))
    log_data = _read_log_file_to_dict()
    current_value = log_data.get(normalized_filepath, '0')
    new_count = 0
    try:
        if not current_value.startswith('LOCKED_UNTIL'):
            new_count = int(current_value) + 1
        else:
            new_count = 1
    except ValueError:
        new_count = 1

    if new_count < config.WRONG_ATTEMPTS_LIMIT:
        remaining = config.WRONG_ATTEMPTS_LIMIT - new_count
        log_data[normalized_filepath] = str(new_count)
        _write_dict_to_log_file(log_data)
        return False # Limit dolmadı
    else:
        # Limit doldu. Kayıt yapma, karar verme. Sadece arayüze haber ver.
        return True
def clear_wrong_attempts(filepath):
    """Başarılı deşifre sonrası yanlış deneme kayıtlarını temizler."""
    normalized_filepath = os.path.normcase(os.path.normpath(filepath))
    log_data = _read_log_file_to_dict()
    log_data.pop(normalized_filepath, None)
    _write_dict_to_log_file(log_data)

def drive_upload_worker(filepath, q):
    """
    (WORKER THREAD) Dosyayı Google Drive'a yükler ve sonucu kuyruğa yazar.
    (Mesaj formatı diğer worker'larla uyumlu hale getirildi).
    """
    try:
        # DEĞİŞTİ: Mesaj artık ('update', value, text) formatında, iç içe tuple yok.
        q.put(('update', 50, 'Dosya Google Drive\'a yükleniyor...'))
        was_successful, message = upload_to_drive(filepath)
        
        if was_successful:
            # DEĞİŞTİ: Mesaj artık ('update', value, text) formatında.
            q.put(('update', 90, 'Yerel dosya siliniyor...'))
            os.remove(filepath)
            clear_wrong_attempts(filepath)
            q.put(('complete', "Dosya başarıyla Drive'a yüklendi ve yerelden silindi."))
        else:
            q.put(('error', f"Yükleme Başarısız: {message}"))
            
    except Exception as e:
        q.put(('error', f"Drive yükleme sırasında beklenmedik bir hata oluştu: {e}"))


def decision_worker(filepath, q):
    """
    (WORKER THREAD) Hız ölçer, karar verir ve uygular.
    (Mesaj formatı diğer worker'larla %100 uyumlu hale getirildi).
    """
    try:
        estimated_minutes = _check_upload_speed_and_time(filepath, q)
        
        if estimated_minutes <= config.MAX_UPLOAD_TIME_MINUTES:
            # DÜZELTME: Mesaj (value, text) yerine value, text olarak ayrı ayrı gönderiliyor.
            q.put(('update', 30, f"Süre uygun ({estimated_minutes:.1f} dk). Yükleme başlıyor..."))
            was_successful, message = upload_to_drive(filepath)
            
            if was_successful:
                # DÜZELTME: Mesaj ayrı ayrı gönderiliyor.
                q.put(('update', 90, 'Yerel dosya siliniyor...'))
                os.remove(filepath)
                clear_wrong_attempts(filepath)
                q.put(('complete', "Dosya başarıyla Drive'a yüklendi ve yerelden silindi."))
            else:
                q.put(('error', f"Yükleme Başarısız: {message}"))
        else:
            if estimated_minutes == float('inf'):
                reason = "İnternet bağlantısı yok."
            else:
                reason = f"Tahmini süre çok uzun ({estimated_minutes:.1f} dk)."
            
            # DÜZELTME: Mesaj ayrı ayrı gönderiliyor.
            q.put(('update', 50, f"{reason} Zaman kilidi uygulanıyor..."))
            
            # --- Zaman kilidi mantığının geri kalanı aynı ---
            log_data = _read_log_file_to_dict()
            normalized_filepath = os.path.normcase(os.path.normpath(filepath))
            current_value = log_data.get(normalized_filepath, '0')
            current_lock_level = 0
            if current_value.startswith('LOCKED_UNTIL'):
                parts = current_value.split(',')
                if len(parts) == 3: current_lock_level = int(parts[2])

            new_lock_level = current_lock_level + 1
            durations = config.LOCK_LEVEL_DURATIONS_MINUTES
            duration_index = min(new_lock_level - 1, len(durations) - 1)
            lock_duration_minutes = durations[duration_index]
            
            lock_duration_seconds = lock_duration_minutes * 60
            unlock_time = int(time.time()) + lock_duration_seconds
            
            log_data[normalized_filepath] = f"LOCKED_UNTIL,{unlock_time},{new_lock_level}"
            _write_dict_to_log_file(log_data)
            
            q.put(('complete', f"Dosya {lock_duration_minutes} dakika boyunca kilitlenmiştir (Seviye {new_lock_level})."))

    except Exception as e:
        q.put(('error', f"Karar mekanizmasında beklenmedik hata: {e}"))


def capture_intruder_photo():
    try:
        cam = cv2.VideoCapture(0)

        if not cam.isOpened():
            return None
        
        for _ in range(5):
            cam.read()

        ret, frame = cam.read()
        if ret:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            photo_path = f"intruder_{timestamp}.jpg"
            cv2.imwrite(photo_path, frame)
            cam.release()
            return photo_path
        
        cam.release()
    
    except Exception as e:
        print(f"Kamera hatası: {e}")

def silent_photo_upload(photo_path):
    """Saldırgan fotoğrafını arka planda yükler ve yerelden siler."""
    if photo_path and os.path.exists(photo_path):
        was_successful, _ = upload_to_drive(photo_path)
        if was_successful:
            os.remove(photo_path) # İz bırakma

    return None

