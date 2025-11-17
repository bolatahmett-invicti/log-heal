# AI Agent System - Web Arayüzü

Modern ve kullanıcı dostu web arayüzü ile ELK log analizi ve otomatik kod düzeltme sistemi.

## 🚀 Kurulum

```powershell
# Gerekli paketleri yükleyin
pip install -r requirements.txt
```

## ▶️ Çalıştırma

```powershell
# API Key'i ayarlayın
$env:OPENAI_API_KEY="sk-proj-..."

# Web arayüzünü başlatın
streamlit run app.py
```

Tarayıcınızda otomatik olarak `http://localhost:8501` açılacak.

## 🎨 Özellikler

### 📋 Log Listesi
- ELK'den gelen tüm ERROR logları listelenir
- Her log için özet bilgiler gösterilir
- Tek tıkla analiz başlatma

### 🔍 Log Detayları
- Seçilen logun tüm bilgileri
- JSON formatında tam görünüm
- Hata mesajı ve stack trace

### 🤖 AI Analizi
- Otomatik hata tespiti
- Kök neden analizi
- Kod değişikliği önerisi
- Otomatik git branch oluşturma

### 📝 Kod Değişiklikleri
- **Değişiklikler**: Diff görünümü (eklenen/çıkarılan satırlar)
- **Orijinal**: Değişiklik öncesi kod
- **Düzeltilmiş**: Yeni kod

### ⚙️ Ayarlar (Sidebar)

**ELK Bağlantısı:**
- Host ve Port ayarları
- Kimlik doğrulama (opsiyonel)
- Mock veri seçeneği (test için)

**Codebase:**
- Proje yolu belirleme
- Otomatik RAG indexleme

**Hata Filtreleme:**
- İşlenecek hata tiplerini seçin
- Default: NullReferenceException

## 📸 Ekran Görüntüleri

### Ana Ekran
```
┌─────────────────┬────────────────────────────────┐
│  📋 Log Listesi │  🔍 Detaylar & Analiz         │
│                 │                                │
│  • Log 1        │  Hata Tipi: NRE                │
│  • Log 2        │  Servis: UserService           │
│  • Log 3        │  Mesaj: ...                    │
│                 │                                │
│                 │  [🤖 AI Analizi Başlat]        │
└─────────────────┴────────────────────────────────┘
```

### Kod Değişiklikleri
```
┌────────────────────────────────────────────────┐
│  📄 UserController.cs                          │
│  ┌──────────┬──────────┬───────────────────┐  │
│  │Değişiklik│ Orijinal │ Düzeltilmiş       │  │
│  ├──────────┼──────────┼───────────────────┤  │
│  │ + Line 45: null check eklendi            │  │
│  │ - Line 50: gereksiz kod silindi          │  │
│  └──────────┴──────────┴───────────────────┘  │
└────────────────────────────────────────────────┘
```

## 🎯 Kullanım Akışı

1. **Ayarları Yapılandırın** (Sol sidebar)
   - ELK bağlantı bilgileri
   - Proje yolu
   - Hedef hata tipleri

2. **Logları Yükleyin**
   - "Logları Yenile" butonuna tıklayın
   - ELK'den loglar çekilir

3. **Log Seçin**
   - Listeden analiz etmek istediğiniz logu seçin

4. **AI Analizi Başlatın**
   - "AI Analizi Başlat" butonuna tıklayın
   - Agent'lar otomatik çalışır

5. **Sonuçları İnceleyin**
   - Kod değişikliklerini görüntüleyin
   - Branch bilgilerini kontrol edin
   - Git'e gidip değişiklikleri review edin

## 🔧 İpuçları

- **Mock Veri**: Test için ELK olmadan çalışabilirsiniz
- **Zaman Aralığı**: Son X dakikadaki logları çeker
- **Hata Filtreleme**: Birden fazla hata tipi ekleyebilirsiniz
- **Diff Görünümü**: Değişiklikleri kolayca görmek için kullanın

## ⚡ Performans

- Async işlemler ile hızlı analiz
- RAG ile sadece ilgili dosyalar işlenir
- Token optimizasyonu

## 🛠️ Sorun Giderme

**ELK'ye bağlanamıyorum:**
- Host ve port ayarlarını kontrol edin
- ELK'nin erişilebilir olduğundan emin olun
- Mock veri ile test edin

**Log bulunamadı:**
- Zaman aralığını artırın
- ELK'de ERROR seviyesinde log olduğundan emin olun

**Analiz tamamlanamadı:**
- OPENAI_API_KEY'in doğru olduğundan emin olun
- Proje yolunun geçerli olduğunu kontrol edin
