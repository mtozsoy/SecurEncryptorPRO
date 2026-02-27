
-----

# 🛡️ SecurEncryptor

### "Aktif Savunma" ve Akıllı Karar Mekanizmalı Siber Güvenlik Kalkanı

SecurEncryptor PRO, kişisel verilerinizi korumak için klasik şifreleme yöntemlerini "Aktif Savunma" (Active Defense) konseptiyle birleştiren, profesyonel bir masaüstü güvenlik aracıdır. Sadece veriyi kilitlemekle kalmaz, yetkisiz erişim denemelerine karşı dijital ve fiziksel karşı önlemler alır.

## Ana Özellikler

  * **🛡️ Askeri Seviye Şifreleme: Her işlem için benzersiz Dynamic Salt (Tuzlama) mekanizması ile güçlendirilmiş AES-256 standardı.** Her şifreleme işlemi için benzersiz ve rastgele bir "tuz" (Dynamic Salt) ile güçlendirilmiş **AES-256** standardını kullanır.
  * **📸 Aktif Savunma (Intruder Capture):** Hatalı şifre denemelerinde OpenCV kullanarak saldırganın fotoğrafını webcam üzerinden anında yakalar.
  * **☁️ Sessiz Bulut Kanıtı (Silent Upload):** Yakalanan saldırgan fotoğraflarını, arayüzü dondurmadan arka planda sessizce **Google Drive**'a yükler ve yerelden izlerini siler.
  * **🧠 Akıllı Karar Mekanizması:** 5 hatalı deneme sonrası internet hızınızı ölçer; dosya boyutuna göre "Drive'a Yedekleme" veya "Zaman Kilidi" seçeneklerinden en optimize olanı otomatik uygular.
  * **⏳ Aşamalı Zaman Kilidi:** Tekrarlanan hatalı denemelere karşı caydırıcılığı katlanarak artırır. Kilit süreleri **15 dakika**, **1 saat** ve **24 saat** gibi seviyelerle artar.
  * **🔥 "Paranoya Modu" (Güvenli Silme):** Şifrelenen orijinal dosyayı, veri kurtarma yazılımlarıyla geri getirilemeyecek şekilde, üzerine defalarca anlamsız veri yazarak **kalıcı olarak imha eder**.
  * **⚙️ Yapılandırılabilir Ayarlar:** Programın içindeki "Ayarlar" menüsü sayesinde tüm güvenlik parametrelerini (hatalı deneme limiti, kilit süreleri, güvenli silme vb.) kendi ihtiyacınıza göre özelleştirebilirsiniz.
  * **💻 Modern PyQt6 Arayüzü:** Akıcı animasyonlar, sürükle-bırak desteği ve profesyonel karanlık tema (QSS).

## Gereksinimler

  * **Python 3.7+**
  * **pip** (Python Paket Yöneticisi)

## Kurulum ve Yapılandırma

1.  **Projeyi klonlayın:**

    ```bash
    git clone https://github.com/mtozsoy/SecurEncryptor_PRO.git
    cd SecurEncryptor_PRO
    ```

2.  **Gerekli kütüphaneleri yükleyin:**
    `requirements.txt` dosyası, projenin ihtiyaç duyduğu tüm kütüphaneleri içerir. Tek bir komutla hepsini kurabilirsiniz:

    ```bash
    pip install -r requirements.txt
    ```

3.  **Google Drive API kimlik bilgilerini alın (İsteğe Bağlı):**
    Eğer hatalı deneme sonrası Google Drive'a yedekleme özelliğini kullanmak istiyorsanız:

      * [Google Cloud Console](https://console.cloud.google.com/)'a gidin.
      * Yeni bir proje oluşturun veya mevcut birini seçin.
      * "Google Drive API"ını etkinleştirin.
      * "Masaüstü uygulaması" (Desktop application) için yeni bir "OAuth istemci kimliği" oluşturun.
      * İndirdiğiniz `credentials.json` dosyasını projenin ana klasörüne yerleştirin.

## Kullanım

Uygulamayı başlatmak için projenin ana klasöründe aşağıdaki komutu çalıştırın:

```bash
python main.py
```

Grafiksel kullanıcı arayüzü (GUI) açılacaktır. Buradan "Dosya Şifrele", "Klasör Şifrele" veya "Şifreli Dosyayı Aç" seçeneklerini kullanabilirsiniz.

## Ayarlar Menüsü

Programın davranışını "Ayarlar" menüsünden (⚙️ ikonu) kolayca özelleştirebilirsiniz. Değiştirebileceğiniz bazı ayarlar:

| Ayar | Açıklama |
| :--- | :--- |
| **Maks. Yükleme Süresi (dk)** | Güvenlik prosedürünün Drive'a yükleme ve Zaman Kilidi arasında karar vereceği süre limiti. |
| **Hatalı Deneme Limiti** | Güvenlik prosedürünün tetiklenmesi için gereken hatalı şifre denemesi sayısı. |
| **Kilit Seviyeleri (dk)** | Aşamalı zaman kilidinin her seviye için ne kadar süreceği (virgülle ayırarak). |
| **Güvenli Silme Aktif** | "Paranoya Modu"nu açar veya kapatır. |
| **Güvenli Silme Geçiş Sayısı**| Orijinal dosyanın üzerine kaç kez rastgele veri yazılacağı. |

Tüm ayarlar, programın yanındaki `settings.json` dosyasına otomatik olarak kaydedilir.

## Katkıda Bulunma

Katkılarınızı bekliyoruz\! Katkıda bulunmak için:

1.  Bu depoyu fork'layın.
2.  Yeni özelliğiniz için yeni bir branch oluşturun (`git checkout -b ozellik/HarikaBirFikir`).
3.  Değişikliklerinizi commit'leyin (`git commit -m 'Yeni ve harika bir özellik eklendi'`).
4.  Branch'inizi push'layın (`git push origin ozellik/HarikaBirFikir`).
5.  Bir Pull Request açın.

## Lisans

Bu proje **MIT Lisansı** ile korunmaktadır. Detaylar için dosyasına bakınız.

## Teşekkürler

Bu proje aşağıdaki harika kütüphaneleri kullanmaktadır:

  * [cryptography](https://cryptography.io/)
  * [Google API Client Library for Python](https://github.com/googleapis/google-api-python-client)
  * [speedtest-cli](https://github.com/sivel/speedtest-cli)
  * [PyQt6](https://pypi.org/project/PyQt6/)
  * [OpenCV](https://opencv.org/)

  
