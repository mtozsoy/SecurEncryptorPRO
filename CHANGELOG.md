SecurEncryptor Değişiklik Günlüğü
Bu dosya, projenin her sürümünde yapılan önemli değişiklikleri belgeler. Format, Keep a Changelog standardını takip eder.
[1.9.1] - 2026-02-28 - Sessiz Yükleme ve Stabilite Güncellemesi
Bu yama, "Aktif Savunma" sistemini bir adım ileri taşıyarak kanıtların gizlice buluta aktarılmasını sağlar ve Google Drive entegrasyonu ile arayüz iletişimindeki kritik donma/takılma sorunlarını çözer.

Eklendi
Sessiz Arka Plan Yüklemesi (Silent Upload): Hatalı şifre girişinde çekilen saldırgan fotoğrafı, artık ana arayüzü dondurmadan ve ekranda herhangi bir ilerleme çubuğu göstermeden, gizli bir iş parçacığı (daemon thread) üzerinden Google Drive'a yükleniyor. Yükleme başarıyla tamamlandığında dosyanın yerel kopyası iz bırakmamak adına otomatik olarak siliniyor.

Düzeltildi
Drive Yetkilendirme Donması: Google Drive yetkilendirme sekmesi açıldığında, kullanıcının tarayıcı sekmesini kapatması veya onay vermemesi durumunda ilerleme çubuğunun (görselde olduğu gibi %30'da) sonsuza kadar takılı kalması hatası giderildi. OAuth2 yetkilendirme sunucusuna zaman aşımı (timeout_seconds=120) eklenerek bu iptal işlemlerinin havada yakalanıp arayüzde düzgün bir hata mesajı ile sonlandırılması sağlandı.

Kalan Hak Bildirimi Eksikliği: Saldırgan fotoğrafı çekme (Intruder Capture) özelliği eklendikten sonra yanlışlıkla devre dışı kalan "Kalan deneme hakkı" uyarı penceresi geri getirildi. Kullanıcılar artık güvenlik limiti dolmadan önceki rutin hatalı denemelerde, kaç şifre giriş hakları kaldığını anlık olarak görebiliyor.
[1.9] - 2026-01-21 - Aktif Savunma ve PyQt6 Dönüşümü
Bu sürüm, projenin mimarisini tamamen değiştirerek endüstri standardı olan PyQt6 framework'üne geçiş yapmış ve pasif korumadan "Aktif Savunma" aşamasına geçerek "Saldırgan Fotoğraf Yakalama" özelliğini sisteme entegre etmiştir.

Eklendi
Aktif Savunma Sistemi (Intruder Capture): Hatalı şifre denemesi yapıldığında OpenCV kütüphanesi kullanılarak webcam üzerinden saldırganın fotoğrafının gizlice çekilmesi özelliği eklendi. Bu fotoğraflar, adli kanıt olarak kullanılmak üzere zaman damgasıyla kaydedilir.

PyQt6 Mimari Geçişi: Uygulamanın tüm arayüz altyapısı customtkinter'dan PyQt6 (Qt6) framework'üne taşındı. Bu sayede:

Daha profesyonel ve özelleştirilebilir bir görsel tasarım (CSS tabanlı QSS).

Daha kararlı bir Sürükle-Bırak (Drag-and-Drop) mekanizması.

QThread ve QObject (Worker) yapısı ile daha güvenli ve akıcı çoklu iş parçacığı yönetimi sağlandı.

Dinamik Stil Sayfası (QSS): Uygulamanın tüm görsel öğeleri merkezi bir karanlık tema stil dosyası üzerinden yönetilebilir hale getirildi.

Değiştirildi
Sürükle-Bırak Altyapısı: tkinterdnd2 kütüphanesine olan bağımlılık kaldırılarak, PyQt6'nın yerel dragEnterEvent ve dropEvent olayları kullanılmaya başlandı. Bu sayede 32/64-bit uyuşmazlığı ve Tcl/Tk hataları kökten çözüldü.

Thread İletişimi: Eski queue.Queue yapısı, PyQt'nin yerleşik pyqtSignal mekanizması ile birleştirilerek arayüz ve işçi thread'ler arasındaki iletişim daha hızlı ve güvenli hale getirildi.

Düzeltildi
Paranoya Modu Checkbox Hatası: Ayarlar menüsündeki "Güvenli Silme" kutucuğunun tıklanmasına rağmen durumunun değişmemesi ve kaydedilmemesi sorunu, PyQt6 isChecked() ve setChecked() metotları ile doğru şekilde senkronize edilerek çözüldü.

Webcam 'strftime' Hatası: Fotoğraf çekimi sırasında datetime.datetime.now fonksiyonunun parantez eksikliği nedeniyle oluşturduğu çalışma zamanı hatası düzeltildi.

Checkbox Görsel Geri Bildirimi: Stil sayfasındaki eksiklik nedeniyle checkbox işaretlendiğinde görsel olarak değişmemesi sorunu, :checked pseudo-state'i eklenerek giderildi.

[1.8] - 2025-10-20 - Modern Arayüz ve Sürükle-Bırak Entegrasyonu

Bu sürüm, uygulamanın kullanıcı arayüzünü temelden modernize ederek customtkinter kütüphanesine geçirmiş ve Sürükle-Bırak gibi önemli bir kullanım kolaylığı özelliği eklemiştir. Bu iki büyük sistemin entegrasyonu için kapsamlı hata ayıklamaları yapılmıştır.

Değiştirildi

    Modern Arayüz Altyapısı (customtkinter): Tüm kullanıcı arayüzü (UI) altyapısı, standart tkinter'dan modernize edilerek customtkinter kütüphanesine geçirildi. Bu değişiklik, programa daha modern bir görünüm, daha iyi ölçeklendirme ve yerleşik tema desteği (koyu mod) kazandırdı.

Eklendi

    Sürükle ve Bırak (Drag-and-Drop) Desteği: Dosya ve klasörleri şifrelemek için ana pencereye Sürükle-Bırak desteği eklendi. Kullanıcılar artık dosya seçme pencereleri yerine dosyalarını doğrudan uygulama üzerine sürükleyerek şifreleme işlemini başlatabilir.

    customtkinter arayüzüne, önceki versiyonlarda kaldırılmış olan Ayarlar (⚙️) butonu yeniden entegre edildi.

Düzeltildi

    Kütüphane Uyumluluk Sorunları: Kapsamlı bir hata ayıklama süreci sonucunda, customtkinter ve tkinterdnd2 kütüphaneleri arasındaki temel uyumluluk sorunları giderildi. Bu, AttributeError, TclError: invalid command name, can't find package ve 32/64-bit mismatch gibi bir dizi hatayı çözerek Sürükle-Bırak özelliğinin yeni arayüzle sorunsuz çalışmasını sağladı.

    Widget Komut Hataları: customtkinter'a geçiş sırasında, eski tkinter komutları (.config, ['state']) yeni ve uyumlu olan (.configure, .cget('state')) komutlarla değiştirilerek çeşitli AttributeError ve TclError hataları düzeltildi.

[1.7] - 2025-10-19 - Kullanıcı Kontrolü ve Paranoya Modu
Bu yama, kullanıcıya program üzerinde daha fazla kontrol imkanı sunan kapsamlı bir Ayarlar Menüsü eklerken, veri güvenliğini en üst seviyeye çıkaran "Güvenli Silme" özelliğini de entegre etmiştir.

Eklendi
Kapsamlı Ayarlar Menüsü:

Kullanıcıların programın temel davranışlarını bir arayüz üzerinden değiştirebilmesi için yeni bir "Ayarlar" penceresi eklendi.

Artık aşağıdaki ayarlar kullanıcı tarafından anlık olarak yapılandırılabilir:

Hatalı deneme limiti.

Maksimum yükleme süresi (Drive/Zaman Kilidi kararı için).

Aşamalı kilit seviyelerinin süreleri.

Güvenli Silme özelliğinin aktif olup olmadığı.

Güvenli Silme geçiş sayısı.

settings.json Dosyası: Kullanıcı tarafından yapılan ayarların program kapatılıp açıldığında kaybolmaması için kalıcı olarak kaydedildiği bir yapılandırma dosyası altyapısı kuruldu. Bu sistem, gelecekte eklenecek yeni ayarlarla geriye dönük uyumlu çalışacak şekilde tasarlandı.

"Paranoya Modu" (Güvenli Dosya Silme):

Başarılı bir şifreleme işleminden sonra, orijinal dosyanın veri kurtarma yazılımlarıyla geri getirilemeyecek şekilde, üzerine birkaç kez rastgele veri yazılarak kalıcı olarak imha edilmesi özelliği eklendi.

Bu özellik, Ayarlar menüsünden açılıp kapatılabilir.

Değiştirildi
Dinamik Ayar Altyapısı: Program artık config.py dosyasındaki sabit değerler yerine, başlangıçta settings.json dosyasından okunan dinamik ayarları kullanacak şekilde yeniden yapılandırıldı.

Arayüz İyileştirmesi: Ana arayüzdeki "Ayarlar" butonu, daha modern ve erişilebilir bir tasarım için metin yerine bir ikon (⚙️) ile değiştirilerek pencerenin sol üst köşesine taşındı.

Düzeltildi
İş Parçacığı İletişim Hatası (ValueError): "Güvenli Silme" işlemi sırasında ilerleme çubuğunu güncelleyen mesaj formatının, programın geri kalanıyla uyumsuz olmasından kaynaklanan ValueError hatası giderildi.

[1.6] - 2025-10-18 - Akıllı Kale Güncellemesi
Bu yama, programın güvenlik mekanizmalarını daha akıllı, caydırıcı ve hataya karşı dayanıklı hale getirmeye odaklanmıştır. Kullanıcı deneyimini donma ve takılmalara karşı korumak için mimari iyileştirmeler yapılmıştır.

Eklendi
Aşamalı Zaman Kilidi (Escalating Time-Lock): Standart 15 dakikalık tek seviyeli kilit sistemi terk edildi. Artık program, tekrarlanan hatalı denemelere karşı caydırıcılığı katlanarak artırıyor:

1. Kilit: 15 dakika

2. Kilit: 60 dakika (1 saat)

3. Kilit ve sonrası: 1440 dakika (24 saat)

Değiştirildi
Asenkron Karar Mekanizması: 5 hatalı deneme sonrası başlayan internet hızı ölçümü gibi uzun işlemler ana arayüzü donduruyordu. Bu sorunu çözmek için tüm ağır işler (_check_upload_speed_and_time, upload_to_drive, kilitleme mantığı) decision_worker adında yeni bir arka plan iş parçacığına (thread) devredildi. Bu sayede, en karmaşık güvenlik prosedürleri sırasında bile program arayüzü akıcı kalır.

Düzeltildi
İş Parçacığı İletişim Hatası (ValueError): Farklı "işçi" fonksiyonların (worker) arayüze farklı formatlarda mesaj göndermesinden kaynaklanan not enough values to unpack hatası, tüm iletişim protokolü standart hale getirilerek düzeltildi.

İçe Aktarma Hatası (ImportError): Yeni eklenen decision_worker fonksiyonunun ui.py tarafından tanınmaması sorunu, eksik import ifadeleri eklenerek giderildi.

[1.5] - 2025-10-16 - Demir Gibi Sağlam Güncellemesi
Bu yama, önceki güncellemeler sonrası ortaya çıkan can sıkıcı ve karmaşık hataları çözerek programı bugüne kadarki en stabil haline getirdi.

Düzeltildi
Efsanevi Sayaç Hatası: Hatalı deneme sayacının, dosya adında virgül (,) veya Türkçe karakter (ö, ç vb.) olduğunda takılıp kalması sorunu kökünden çözüldü. Loglama mekanizması, bu sorunları tamamen ortadan kaldıran, standartlaştırılmış dosya yolları ve güvenli bir ayraç (|) kullanan sağlam bir sözlük (dictionary) yapısına geçirildi.

Zaman Kilidi Kontrol Eksikliği: Bir dosyanın kilitlenmesine rağmen, deşifreleme ekranının bu kilidi kontrol etmeden şifre sorması hatası giderildi. Artık kilitli dosyalar, süre dolmadan doğru şifre girilse bile açılamaz.

config.py Eksikliği: İnternet olmadığında devreye giren zaman kilidi mekanizmasının, config.py dosyasında LOCK_DURATION_MINUTES ayarı eksik olduğu için çökmesi hatası düzeltildi.

speedtest-cli Engelleme Hatası: İnternet hızı testinin sunucu tarafından engellenmesine (HTTP 403) neden olan sorun, kütüphanenin en son sürüme güncellenmesiyle çözüldü.

[1.4] - 2025-10-15 - Akıllı Güvenlik Güncellemesi
Bu yama, 5 hatalı deneme sonrası uygulanan güvenlik prosedürünü daha akıllı ve esnek hale getirdi.

Eklendi
Dinamik Güvenlik Aksiyonu: Program artık 5 hatalı deneme sonrası körü körüne tek bir işlem yapmıyor. Önce speedtest-cli ile internet hızını ölçüp, tahmini yükleme süresini hesaplıyor.

Zaman Kilidi (Time-Lock) Mekanizması: Eğer tahmini yükleme süresi belirlenen limitten uzunsa veya internet yoksa, Drive'a yükleme yerine dosyayı belirli bir süre açılmaya karşı kilitleyen bir sistem eklendi.

[1.3] - 2025-10-15 - Kod Mimarisi Güncellemesi
Projenin gelecekteki gelişimini kolaylaştırmak için kod tabanında büyük bir yeniden yapılandırma (refactoring) yapıldı.

Değiştirildi
Proje Modüler Hale Getirildi: Tüm kodun bulunduğu tek dosya yapısı terk edildi. Proje; main.py, ui.py, crypto_core.py, drive_handler.py ve config.py gibi mantıksal modüllere bölündü.

[1.2] - 2025-10-14 - Konfor ve Performans Güncellemesi
Bu yama, kullanıcı deneyimini iyileştirmeye ve programın büyük dosyalarla daha verimli çalışmasına odaklandı.

Eklendi
İlerleme Çubuğu (Progress Bar): Büyük dosyalarla çalışırken arayüzün donmasını engellemek için tüm kripto işlemleri arka plan iş parçacıklarına (multithreading) taşındı ve kullanıcıya ilerlemeyi gösteren bir pencere eklendi.

[1.1] - 2025-10-12 - Güvenlik Duvarı Güncellemesi
Bu yama, programın kriptografik temelini ve kullanıcı güvenliğini önemli ölçüde güçlendirdi.

Eklendi
Dinamik Salt (Tuz) Kullanımı: Güvenliği artırmak için her şifreleme işleminde rastgele ve benzersiz bir "tuz" kullanma özelliği eklendi.

Parola Gücü Kontrolcüsü: Kullanıcıların daha güvenli şifreler seçmesini sağlamak için parola gücünü anlık olarak gösteren özel bir arayüz eklendi.

[1.0] - 2025-10-10 - Temel Sürüm
Eklendi
Dosya ve klasörler için AES-256 tabanlı şifreleme ve deşifreleme.

Modern ve animasyonlu Tkinter kullanıcı arayüzü.

5 hatalı şifre denemesi sonrası Google Drive'a otomatik yükleme.