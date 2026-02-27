# drive_handler.py

import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

import config # Ayarlarımızı import ediyoruz

def upload_to_drive(filepath):
    """
    Dosyayı Google Drive'a yükler.
    Artık arayüz göstermek yerine (başarılı_mı, mesaj) şeklinde bir tuple döndürür.
    """
    creds = None
    if not os.path.exists(config.CREDENTIALS_FILE):
        return (False, f"Google Drive API için '{config.CREDENTIALS_FILE}' dosyası bulunamadı!")

    if os.path.exists(config.TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(config.TOKEN_FILE, config.SCOPES)
        except Exception:
            if os.path.exists(config.TOKEN_FILE): os.remove(config.TOKEN_FILE)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None
        
        if not creds:
            try:
                flow = InstalledAppFlow.from_client_secrets_file(config.CREDENTIALS_FILE, config.SCOPES)
                creds = flow.run_local_server(port=0, timeout_seconds=120)
            except Exception as e:
                return (False,f"Google Drive oturum açma işlemi iptal edildi veya zaman aşımına uğradı:\nDetay: {e}")
        
        with open(config.TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('drive', 'v3', credentials=creds)
        file_metadata = {'name': os.path.basename(filepath)}
        media = MediaFileUpload(filepath, resumable=True)
        # Yükleme işlemi bitene kadar bekle
        service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        return (True, "Dosya başarıyla Drive'a yüklendi.")
    except Exception as e:
        return (False, f"Dosya Drive'a yüklenirken hata oluştu:\n{e}")