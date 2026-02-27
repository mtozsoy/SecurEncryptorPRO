# config.py

import json
import os

# --- AYAR YÖNETİCİSİ FONKSİYONLARI ---

SETTINGS_FILE = "settings.json"

def load_settings():
    """
    settings.json dosyasını okur. Eğer dosya yoksa veya bozuksa,
    varsayılan ayarları oluşturur ve kullanır.
    Ayrıca yeni eklenen ayarları otomatik olarak mevcut dosyaya entegre eder.
    """
    # Varsayılan ayarlar, hem ilk kurulum hem de hata durumları için şablon görevi görür.
    defaults = {
        "max_upload_time_minutes": 10,
        "lock_level_durations_minutes": [15, 60, 1440],
        "secure_delete_enabled": True,
        "secure_delete_passes": 3,
        "wrong_attempts_limit": 5
    }
    
    if not os.path.exists(SETTINGS_FILE):
        save_settings(defaults) # Dosya yoksa, varsayılanlarla sıfırdan oluştur.
        return defaults

    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            settings = json.load(f)
            # Yüklenen ayarlarda eksik anahtar varsa, varsayılanla tamamla.
            # Bu, yeni bir ayar eklendiğinde programın çökmesini engeller.
            updated = False
            for key, value in defaults.items():
                if key not in settings:
                    settings[key] = value
                    updated = True
            
            # Eğer eksik bir ayar tamamlandıysa, dosyayı güncel haliyle tekrar kaydet.
            if updated:
                save_settings(settings)
                
            return settings
    except (json.JSONDecodeError, FileNotFoundError):
        save_settings(defaults) # Dosya bozuksa, varsayılanlarla üzerine yaz.
        return defaults

def save_settings(settings_data):
    """Verilen ayar sözlüğünü settings.json dosyasına güzel formatlanmış şekilde yazar."""
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings_data, f, indent=4)


# --- UYGULAMA BAŞLANGICINDA AYARLARI YÜKLEME ---

# Program ilk çalıştığında ayarları settings.json dosyasından yükler.
SETTINGS = load_settings()


# --- DİNAMİK AYARLAR (Kullanıcı tarafından değiştirilebilir) ---

# Bu değişkenler, programın her yerinde kullanılmak üzere SETTINGS sözlüğünden okunur.
MAX_UPLOAD_TIME_MINUTES = SETTINGS['max_upload_time_minutes']
LOCK_LEVEL_DURATIONS_MINUTES = SETTINGS['lock_level_durations_minutes']
SECURE_DELETE_ENABLED = SETTINGS['secure_delete_enabled']
SECURE_DELETE_PASSES = SETTINGS['secure_delete_passes']
WRONG_ATTEMPTS_LIMIT = SETTINGS['wrong_attempts_limit']


# --- SABİT AYARLAR (Kullanıcı tarafından değiştirilmesi amaçlanmamıştır) ---

# Bu ayarlar genellikle programın temel işleyişiyle ilgilidir ve değiştirilmez.
PBKDF2_ITERATIONS = 100000
SALT_SIZE_BYTES = 16
WRONG_ATTEMPTS_FILE = "wrong_attempts.log"

# Google Drive API sabitleri
SCOPES = ['https://www.googleapis.com/auth/drive.file']
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'