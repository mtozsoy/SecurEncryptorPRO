import os
import sys
import time
import re
import config
import threading
import queue # Orijinal worker'lar queue kullandığı için Worker sınıfımız da bunu kullanacak
import crypto_core

# --- PyQt6 İçe Aktarmaları ---
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QFrame, QFileDialog, QMessageBox, 
    QInputDialog, QDialog, QLineEdit, QDialogButtonBox, 
    QProgressBar, QCheckBox, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QThread, QSize, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QIcon, QFont, QDragEnterEvent, QDropEvent

# --- Diğer modüllerimizden gerekli fonksiyonları import ediyoruz ---
from crypto_core import (
    capture_intruder_photo,
    encryption_worker,
    decryption_worker,
    log_wrong_attempt,
    drive_upload_worker,
    decision_worker
)

# --- ARKA UÇ HELPER FONKSİYONLARI (DEĞİŞİKLİK YOK) ---

def check_for_lock(filepath):
    """
    Verilen dosyanın kilitli olup olmadığını ve kilit süresinin dolup dolmadığını kontrol eder.
    Aşamalı kilit formatı ('LOCKED_UNTIL,zaman,seviye') ile tam uyumludur.
    """
    normalized_filepath_to_check = os.path.normcase(os.path.normpath(filepath))
    
    log_file = config.WRONG_ATTEMPTS_FILE
    if not os.path.exists(log_file):
        return 0, False

    try:
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if not line.strip(): continue
                
                parts = line.strip().split('|', 1)
                
                if len(parts) == 2:
                    normalized_filepath_in_log = os.path.normcase(os.path.normpath(parts[0]))

                    if normalized_filepath_in_log == normalized_filepath_to_check:
                        value_parts = parts[1].split(',')
                        
                        if value_parts[0] == 'LOCKED_UNTIL' and len(value_parts) >= 2:
                            try:
                                unlock_time = int(value_parts[1])
                                current_time = int(time.time())
                                
                                if current_time < unlock_time:
                                    return unlock_time - current_time, True
                            except (ValueError, IndexError):
                                pass
                        
                        return 0, False 
    except FileNotFoundError:
        return 0, False
    except Exception:
        return 0, False
            
    return 0, False


def check_password_strength(password):
    """ Parola gücünü ve rengini döndürür. """
    length = len(password)
    if length == 0: return 0, "", "#ffffff"
    if length < 8: return 0, "Çok Zayıf", "#ff4757"
    score = 0
    if re.search(r"\d", password): score += 1
    if re.search(r"[a-z]", password) or re.search(r"[A-Z]", password): score += 1
    if re.search(r"[!@#$%^&*(),.?\":{}|<>]", password): score += 1
    if length >= 12 and score >= 3: return 4, "Çok Güçlü", "#2ed573"
    if score == 3: return 3, "Güçlü", "#009432"
    elif score == 2: return 2, "Orta", "#ffa502"
    else: return 1, "Zayıf", "#ff6348"

# --- PYQT İŞ PARÇACIĞI (THREADING) YÖNETİCİSİ ---

class Worker(QObject):
    """
    Ağır kripto işlemlerini ayrı bir QThread üzerinde çalıştırmak için QObject tabanlı bir 'worker'.
    """
    update = pyqtSignal(int, str)
    complete = pyqtSignal(str)
    error = pyqtSignal(str)
    wrong_password = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, target_function, *args):
        super().__init__()
        self.target_function = target_function
        self.args = args
        self.q = queue.Queue()
        self.is_running = True

    def run(self):
        """Worker'ın ana çalışma fonksiyonu. QThread tarafından çağrılır."""
        thread_args = self.args + (self.q,)
        thread = threading.Thread(target=self.target_function, args=thread_args, daemon=True)
        thread.start()

        while self.is_running:
            try:
                message = self.q.get(timeout=0.1)
                if message is None:
                    continue

                message_type = message[0]
                message_content = message[1:]

                if message_type == 'update':
                    value, text = message_content
                    self.update.emit(int(value), text)
                
                elif message_type == 'complete':
                    self.complete.emit(message_content[0])
                    self.is_running = False
                
                elif message_type == 'error':
                    self.error.emit(message_content[0])
                    self.is_running = False
                
                elif message_type == 'wrong_password':
                    self.wrong_password.emit(message_content[0])
                    self.is_running = False

                self.q.task_done()
                
            except queue.Empty:
                if not thread.is_alive() and self.q.empty():
                    self.is_running = False
            except Exception as e:
                self.error.emit(f"Beklenmeyen bir worker hatası: {e}")
                self.is_running = False

        self.finished.emit()

    def stop(self):
        self.is_running = False

# --- YENİDEN YAZILAN PyQt DİYALOGLARI ---

class PasswordDialog(QDialog):
    """ Parola gücünü gösteren diyalog. """
    def __init__(self, parent=None, title="Lütfen bir şifre girin:"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(400, 180)
        self.setModal(True)
        self.password = None

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Parola:"))
        
        self.password_entry = QLineEdit(self)
        self.password_entry.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_entry.textChanged.connect(self.update_strength)
        layout.addWidget(self.password_entry)
        
        self.strength_label = QLabel("", self)
        self.strength_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.strength_label)
        
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.ok_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        self.ok_button.setText("Tamam")
        self.ok_button.setEnabled(False)
        
        cancel_button = self.button_box.button(QDialogButtonBox.StandardButton.Cancel)
        cancel_button.setText("İptal")

        self.button_box.accepted.connect(self.on_ok)
        self.button_box.rejected.connect(self.reject)
        
        layout.addWidget(self.button_box)
        self.password_entry.setFocus()

    def update_strength(self):
        password = self.password_entry.text()
        level, text, color = check_password_strength(password)
        self.strength_label.setText(text)
        self.strength_label.setStyleSheet(f"color: {color}; font-weight: bold;")
        self.ok_button.setEnabled(level > 0)

    def on_ok(self):
        self.password = self.password_entry.text()
        self.accept()

    def get_password(self):
        if self.exec() == QDialog.DialogCode.Accepted:
            return self.password
        return None


class SettingsWindow(QDialog):
    """ Ayarları değiştirmek için kullanılan diyalog penceresi. """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ayarlar")
        self.setFixedSize(450, 320)
        self.setModal(True)
        
        self.settings = config.load_settings()
        
        layout = QVBoxLayout(self)
        grid_layout = QGridLayout()

        self.max_upload_entry = QLineEdit(str(self.settings["max_upload_time_minutes"]))
        self.attempts_limit_entry = QLineEdit(str(self.settings["wrong_attempts_limit"]))
        self.lock_levels_entry = QLineEdit(', '.join(map(str, self.settings["lock_level_durations_minutes"])))
        self.delete_passes_entry = QLineEdit(str(self.settings["secure_delete_passes"]))
        self.secure_delete_check = QCheckBox("Güvenli Silme (Paranoya Modu) Aktif")
        self.secure_delete_check.setChecked(self.settings["secure_delete_enabled"])

        grid_layout.addWidget(QLabel("Maks. Yükleme Süresi (dk):"), 0, 0)
        grid_layout.addWidget(self.max_upload_entry, 0, 1)
        grid_layout.addWidget(QLabel("Hatalı Deneme Limiti:"), 1, 0)
        grid_layout.addWidget(self.attempts_limit_entry, 1, 1)
        grid_layout.addWidget(QLabel("Kilit Seviyeleri (dk, virgülle ayır):"), 2, 0)
        grid_layout.addWidget(self.lock_levels_entry, 2, 1)
        grid_layout.addWidget(QLabel("Güvenli Silme Geçiş Sayısı:"), 3, 0)
        grid_layout.addWidget(self.delete_passes_entry, 3, 1)
        grid_layout.addWidget(self.secure_delete_check, 4, 0, 1, 2)

        layout.addLayout(grid_layout)
        layout.addStretch()

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.button(QDialogButtonBox.StandardButton.Save).setText("Kaydet ve Kapat")
        self.button_box.button(QDialogButtonBox.StandardButton.Cancel).setText("İptal")
        
        self.button_box.accepted.connect(self.save_and_close)
        self.button_box.rejected.connect(self.reject)
        
        layout.addWidget(self.button_box)

    def save_and_close(self):
        try:
            self.settings["max_upload_time_minutes"] = int(self.max_upload_entry.text())
            self.settings["wrong_attempts_limit"] = int(self.attempts_limit_entry.text())
            self.settings["secure_delete_passes"] = int(self.delete_passes_entry.text())
            self.settings["secure_delete_enabled"] = self.secure_delete_check.isChecked()
            
            lock_levels_str = self.lock_levels_entry.text().split(',')
            self.settings["lock_level_durations_minutes"] = [int(level.strip()) for level in lock_levels_str]
            
            config.save_settings(self.settings)
            QMessageBox.information(self, "Başarılı", "Ayarlar başarıyla kaydedildi! Değişiklikler program yeniden başlatıldığında geçerli olacaktır.")
            self.accept()
        except ValueError:
            QMessageBox.critical(self, "Hata", "Lütfen sayısal alanlara geçerli tam sayılar girin.")

# --- ANA UYGULAMA PENCERESİ ---

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("SecurEncryptor | Profesyonel Şifreleme Aracı")
        self.setFixedSize(550, 480)
        self.setAcceptDrops(True)
        
        self.thread = None
        self.worker = None
        self.progress_dialog = None

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(30, 20, 30, 10)
        
        header_layout = QHBoxLayout()
        header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lock_icon = QLabel("🔒")
        lock_icon.setObjectName("LockIcon")
        
        title_label = QLabel("SecurEncryptor")
        title_label.setObjectName("TitleLabel")
        
        header_layout.addWidget(lock_icon)
        header_layout.addWidget(title_label)
        main_layout.addLayout(header_layout) # Başlığı ana layout'a ekle
        
        self.main_frame = QFrame(self)
        self.main_frame.setObjectName("DropZone")
        self.main_frame.setFrameShape(QFrame.Shape.StyledPanel)
        
        main_layout.addWidget(self.main_frame, stretch=1)
        
        frame_layout = QVBoxLayout(self.main_frame)
        frame_layout.setContentsMargins(40, 10, 40, 20)

        settings_layout = QHBoxLayout()
        settings_layout.addStretch()
        btn_settings = QPushButton("⚙️")
        btn_settings.setObjectName("SettingsButton")
        btn_settings.setFixedSize(30, 30)
        btn_settings.clicked.connect(self.open_settings)
        settings_layout.addWidget(btn_settings)
        frame_layout.addLayout(settings_layout)

        encrypt_label = QLabel("ŞİFRELEMEK VEYA ÇÖZMEK İÇİN SÜRÜKLEYİN VEYA BUTONLARI KULLANIN")
        encrypt_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        encrypt_label.setObjectName("HintLabel")
        encrypt_label.setWordWrap(True)
        frame_layout.addWidget(encrypt_label)

        btn_encrypt_file = QPushButton("Dosya Şifrele")
        btn_encrypt_file.clicked.connect(self.select_file_encrypt)
        frame_layout.addWidget(btn_encrypt_file)
        
        btn_encrypt_folder = QPushButton("Klasör Şifrele")
        btn_encrypt_folder.clicked.connect(self.select_folder_encrypt)
        frame_layout.addWidget(btn_encrypt_folder)
        
        separator = QFrame(self)
        separator.setFrameShape(QFrame.Shape.HLine)
        # DÜZELTME 1: FrameShadow -> Shadow
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setObjectName("Separator")
        frame_layout.addWidget(separator)
        frame_layout.addSpacing(20) # Boşluk ekle

        decrypt_label = QLabel("ŞİFRE ÇÖZME İŞLEMİ")
        decrypt_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        decrypt_label.setObjectName("DecryptLabel")
        frame_layout.addWidget(decrypt_label)

        btn_decrypt = QPushButton("Şifreli Dosyayı Aç (.enc)")
        btn_decrypt.setObjectName("DecryptButton")
        btn_decrypt.clicked.connect(self.select_file_decrypt)
        frame_layout.addWidget(btn_decrypt)
        
        frame_layout.addStretch()
        
        footer_label = QLabel("Tüm dosyalar AES-256 standardı ile şifrelenir.")
        footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer_label.setObjectName("FooterLabel")
        main_layout.addWidget(footer_label)
        
        self.setWindowOpacity(0.0)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.main_frame.setObjectName("DropZoneHover")
            self.update_style()
        else:
            event.ignore()
            
    def dragLeaveEvent(self, event):
        self.main_frame.setObjectName("DropZone")
        self.update_style()

    def dropEvent(self, event: QDropEvent):
        self.main_frame.setObjectName("DropZone")
        self.update_style()
        
        urls = event.mimeData().urls()
        if urls:
            filepath = urls[0].toLocalFile()
            self.handle_drop(filepath)

    def update_style(self):
        """ QFrame'in stilini dinamik olarak yeniler. """
        self.main_frame.style().unpolish(self.main_frame)
        self.main_frame.style().polish(self.main_frame)
        
    def showEvent(self, event):
        """ Pencere gösterildiğinde fade-in animasyonunu başlat. """
        super().showEvent(event)
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(400)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.animation.start()

    def open_settings(self):
        dialog = SettingsWindow(self)
        dialog.exec()
        
    def handle_drop(self, filepath):
        if not os.path.exists(filepath):
            return

        if os.path.isfile(filepath):
            if filepath.endswith('.enc'):
                remaining_seconds, is_locked = check_for_lock(filepath)
                if is_locked:
                    self.show_lock_error(remaining_seconds)
                    return
                
                password, ok = QInputDialog.getText(self, "Şifre Çözme", 
                                                    "Lütfen şifreyi girin:", 
                                                    QLineEdit.EchoMode.Password)
                if ok and password:
                    self.start_task(decryption_worker, filepath, password)
            else:
                dialog = PasswordDialog(self, f"'{os.path.basename(filepath)}' için şifre belirle")
                password = dialog.get_password()
                if password:
                    self.start_task(encryption_worker, filepath, password, False)
                    
        elif os.path.isdir(filepath):
            dialog = PasswordDialog(self, f"'{os.path.basename(filepath)}' için şifre belirle")
            password = dialog.get_password()
            if password:
                self.start_task(encryption_worker, filepath, password, True)

    def select_file_encrypt(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Şifrelenecek Dosyayı Seç")
        if filepath:
            dialog = PasswordDialog(self, f"'{os.path.basename(filepath)}' için şifre belirle")
            password = dialog.get_password()
            if password:
                self.start_task(encryption_worker, filepath, password, False)

    def select_folder_encrypt(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Şifrelenecek Klasörü Seç")
        if folder_path:
            dialog = PasswordDialog(self, f"'{os.path.basename(folder_path)}' için şifre belirle")
            password = dialog.get_password()
            if password:
                self.start_task(encryption_worker, folder_path, password, True)

    def select_file_decrypt(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Şifreli Dosyayı Seç", 
                                                filter="Şifreli Dosyalar (*.enc)")
        if not filepath:
            return

        remaining_seconds, is_locked = check_for_lock(filepath)
        if is_locked:
            self.show_lock_error(remaining_seconds)
            return

        password, ok = QInputDialog.getText(self, "Şifre Çözme", 
                                            "Lütfen şifreyi girin:", 
                                            QLineEdit.EchoMode.Password)
        if ok and password:
            self.start_task(decryption_worker, filepath, password)

    def show_lock_error(self, remaining_seconds):
        remaining_minutes = max(1, round(remaining_seconds / 60))
        QMessageBox.critical(self, "Dosya Kilitli",
                             f"Bu dosya çok fazla hatalı deneme nedeniyle geçici olarak kilitlenmiştir.\n\n"
                             f"Lütfen yaklaşık {remaining_minutes} dakika sonra tekrar deneyin.")

    def start_task(self, target_function, *args):
        self.progress_dialog = QProgressBar(self)
        self.progress_dialog.setRange(0, 100)
        self.progress_dialog.setValue(0)
        self.progress_dialog.setTextVisible(True)
        self.progress_dialog.setFormat("Lütfen bekleyin... %p%")
        
        self.progress_window = QDialog(self)
        self.progress_window.setWindowTitle("İşlem Sürüyor...")
        self.progress_window.setFixedSize(350, 100)
        self.progress_window.setModal(True)
        self.progress_window.setWindowFlag(Qt.WindowType.CustomizeWindowHint, True)
        self.progress_window.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)

        progress_layout = QVBoxLayout(self.progress_window)
        self.progress_status_label = QLabel("İşlem başlatılıyor...")
        self.progress_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progress_layout.addWidget(self.progress_status_label)
        progress_layout.addWidget(self.progress_dialog)

        self.thread = QThread()
        self.worker = Worker(target_function, *args)
        self.worker.moveToThread(self.thread)

        self.worker.update.connect(self.update_progress)
        self.worker.complete.connect(self.on_task_complete)
        self.worker.error.connect(self.on_task_error)
        self.worker.wrong_password.connect(self.on_task_wrong_password)
        
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        
        self.thread.started.connect(self.worker.run)
        
        self.thread.start()
        self.progress_window.show()

    def update_progress(self, value, text):
        if self.progress_dialog:
            self.progress_dialog.setValue(value)
            self.progress_status_label.setText(text)
    
    def on_task_complete(self, message):
        if self.progress_window:
            self.progress_window.close()
        QMessageBox.information(self, "Başarılı", message)
    
    def on_task_error(self, message):
        if self.progress_window:
            self.progress_window.close()
        QMessageBox.critical(self, "Hata", message)
    
    def on_task_wrong_password(self, filepath):
        if self.progress_window:
            self.progress_window.close()


        intruder_photo = capture_intruder_photo()
        if intruder_photo:
            print(f"Saldırganın fotoğrafı çekildi: {intruder_photo}")
            
        limit_reached = log_wrong_attempt(filepath)
        
        if limit_reached:
            QMessageBox.information(self, "Kontrol Başlatılıyor",
                                  "Çok fazla hatalı deneme yapıldı! Güvenlik prosedürü başlatılıyor.\n\n"
                                  "İnternet hızınız ve dosya boyutuna göre en uygun eylem belirlenecek.")
            
            QMessageBox.warning(self, "Güvenlik İhlali","Şüpheli hareketler algılandı ve kaydedildi.")

            self.start_task(decision_worker, filepath)
        else:
            QMessageBox.warning(self,"Hatalı Şifre","Girdiğiniz şifre yanlış. Lütfen tekrar deneyin.")

# --- UYGULAMAYI BAŞLATMA ---

def build_gui():
    """ Ana uygulama arayüzünü kurar ve çalıştırır. """
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    dark_stylesheet = """
        QWidget {
            background-color: #2E2E2E;
            color: #FFFFFF;
            font-family: "Segoe UI";
            font-size: 10pt;
        }
        QLabel#LockIcon {
            font-family: "Segoe UI Emoji";
            font-size: 30pt;
            color: #FFFFFF; /* Veya temanıza uygun bir renk, örn: #007ACC */
        }
        QLabel#TitleLabel {
            font-family: "Segoe UI";
            font-size: 22pt;
            font-weight: bold;
            color: #FFFFFF;
        }
        QMainWindow {
            background-color: #252525;
        }
        QLabel#HintLabel, QLabel#DecryptLabel {
            color: #888888;
            font-weight: bold;
        }
        QLabel#FooterLabel {
            color: #888888;
            font-size: 9pt;
        }
        QFrame#DropZone, QFrame#DropZoneHover {
            background-color: #3A3A3A;
            border-radius: 8px;
            border: 2px dashed #555555;
        }
        QFrame#DropZoneHover {
            border: 2px dashed #007ACC;
        }
        QFrame#Separator {
            background-color: #555555;
            min-height: 2px; /* Yüksekliği min-height ile ayarlamak daha iyi */
            max-height: 2px;
        }
        QPushButton {
            background-color: #007ACC;
            color: white;
            border: none;
            padding: 10px;
            border-radius: 5px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #008AE6;
        }
        QPushButton:pressed {
            background-color: #006BB3;
        }
        QPushButton#DecryptButton {
            background-color: #2ca02c;
        }
        QPushButton#DecryptButton:hover {
            background-color: #32b832;
        }
        QPushButton#DecryptButton:pressed {
            background-color: #217621;
        }
        QPushButton#SettingsButton {
            background-color: transparent;
            font-size: 16pt;
            padding: 0px;
            border-radius: 4px; /* Hafif yuvarlak köşe */
        }
        QPushButton#SettingsButton:hover {
            background-color: #555555;
        }

        /* --- STİL DÜZELTMESİ BAŞLANGICI --- */
        
        QLineEdit { /* Sadece yazı giriş kutuları için stil */
            background-color: #555555;
            border: 1px solid #777777;
            border-radius: 4px;
            padding: 5px;
            color: #FFFFFF; /* Yazı rengini de ekleyelim */
        }

        QCheckBox { /* Checkbox'ın metni için genel ayarlar */
            spacing: 5px; /* Kutu ile metin arasındaki boşluk */
        }
        QCheckBox::indicator { /* Kutunun kendisi (işaretsizken) */
            width: 15px;
            height: 15px;
            border: 1px solid #777777;
            border-radius: 3px;
            background-color: #444444; /* Biraz daha koyu bir arka plan */
        }
        QCheckBox::indicator:hover { /* Üzerine gelince kenarlık rengi değişsin */
            border: 1px solid #999999;
        }
        QCheckBox::indicator:checked { /* İşaretliyken görünümü */
            background-color: #007ACC; /* Ana tema rengi */
            border: 1px solid #007ACC;
            /* Opsiyonel: İçine beyaz bir check işareti ekleyebiliriz (Unicode karakteri) */
            /* content: "\\2713"; */ /* Bu her zaman çalışmayabilir */
        }
        QCheckBox::indicator:checked:hover { /* İşaretliyken üzerine gelince */
             border: 1px solid #009AEF; /* Biraz daha açık mavi */
        }
        
        /* --- STİL DÜZELTMESİ BİTTİ --- */

        QDialog, QMessageBox {
             background-color: #3A3A3A;
        }
        QProgressBar {
             border: 1px solid #555555;
             border-radius: 4px;
             text-align: center;
             color: #FFFFFF; /* Yüzde yazısının rengi */
             background-color: #444444; /* Arka plan rengi */
        }
        QProgressBar::chunk {
             background-color: #007ACC;
             border-radius: 3px;
             margin: 1px; /* Çubuk ile kenarlık arasında küçük bir boşluk */
        }
    """
    app.setStyleSheet(dark_stylesheet)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

# DÜZELTME 3: Bu blok main.py'de olduğu için buradan kaldırıldı.
