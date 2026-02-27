# main.py

import sys
import os
import queue
import threading
from tkinter import simpledialog, messagebox, Tk

# Diğer modüllerimizden gerekli fonksiyonları import ediyoruz
from ui import build_gui
from crypto_core import encryption_worker, decryption_worker

def handle_command_line_args():
    """Komut satırından gelen argümanları işler."""
    if len(sys.argv) <= 1:
        return False # Argüman yok, GUI'yi başlat

    path = sys.argv[1]
    if not os.path.exists(path):
        # Komut satırı için basit bir messagebox yeterli
        root = Tk(); root.withdraw() # Arka planda gizli bir root penceresi
        messagebox.showerror("Hata", f"Belirtilen yol bulunamadı:\n{path}")
        return True

    # Komut satırı için de worker thread'leri kullanalım ki kod tekrarı olmasın.
    # Ancak ilerleme çubuğu yerine konsolda bekleyeceğiz.
    q = queue.Queue()
    password = None
    target_func = None
    args = ()
    
    # Geçici bir root penceresi oluşturarak simpledialog'un çalışmasını sağlıyoruz
    root = Tk()
    root.withdraw()

    if path.endswith('.enc') and os.path.isfile(path):
        password = simpledialog.askstring("Şifre Çözme", f"'{os.path.basename(path)}' için şifreyi girin:", show="*")
        target_func = decryption_worker
        args = (path, password)
    elif os.path.isdir(path):
        password = simpledialog.askstring("Klasör Şifrele", f"'{os.path.basename(path)}' için bir şifre belirleyin:", show="*")
        target_func = encryption_worker
        args = (path, password, True)
    elif os.path.isfile(path):
        password = simpledialog.askstring("Dosya Şifrele", f"'{os.path.basename(path)}' için bir şifre belirleyin:", show="*")
        target_func = encryption_worker
        args = (path, password, False)

    if password and target_func:
        thread_args = args + (q,)
        thread = threading.Thread(target=target_func, args=thread_args)
        thread.start()
        
        # İşlem bitene kadar bekle ve sonucu al
        while thread.is_alive():
            thread.join(0.1)
        
        try:
            message_type, message_content = q.get_nowait()
            if message_type == 'complete':
                messagebox.showinfo("Başarılı", message_content)
            else: # error, vs.
                messagebox.showerror("Hata", message_content)
        except queue.Empty:
            messagebox.showerror("Hata", "İşlem bir sonuç döndürmedi.")
    
    return True # Argüman işlendi, GUI başlamasın

if __name__ == "__main__":
    if not handle_command_line_args():
        build_gui()