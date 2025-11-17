# Hızlı Başlangıç Kılavuzu

## 🚀 5 Dakikada Başlangıç

### 1. Kurulum
```bash
# Proje dizinine git
cd C:\Users\AhmetBolat\Projects\Claude\ai-agent-system

# Bağımlılıkları yükle
pip install -r requirements.txt

# Demo'yu çalıştır
python demo.py
```

### 2. İlk Kullanım (Mock Mod)
```bash
# Sistem testi
python cli.py --mock
```

### 3. Gerçek ELK ile Kullanım
```bash
# ELK bağlantısını konfigüre et
python cli.py --elk-host your-elk-host.com --elk-port 9200 --elk-user admin --elk-password yourpassword --time-range 60
```

## 📁 Dosya Yapısı

```
ai-agent-system/
├── orchestrator.py      # Ana orchestrator ve agent'lar
├── elk_connector.py     # ELK entegrasyonu
├── cli.py              # Komut satırı arayüzü
├── demo.py             # Demo scripti
├── config.example.yaml # Yapılandırma örneği
├── requirements.txt    # Python bağımlılıkları
├── README.md          # Detaylı dokümantasyon
└── QUICKSTART.md      # Bu dosya
```

## 🔧 Agent'lar

### Log Analyzer Agent
- **Görev**: ELK loglarını analiz eder
- **Çıktı**: Hata tipi, mesaj, stack trace, severity
- **Süre**: ~5-10 saniye

### Solution Architect Agent
- **Görev**: Çözüm önerir
- **Çıktı**: Çözüm açıklaması, etkilenen dosyalar, kod değişiklikleri
- **Süre**: ~5-15 saniye

### Code Generator Agent
- **Görev**: Kodu düzeltir
- **Çıktı**: Fix edilmiş dosyalar
- **Süre**: ~10-20 saniye per dosya

### Git Manager Agent
- **Görev**: Branch oluşturur ve commit eder
- **Çıktı**: Branch adı, commit mesajı
- **Süre**: ~2-5 saniye

## 💡 Örnek Senaryolar

### Senaryo 1: NullPointerException
```
Hata: UserService null
Çözüm: Dependency Injection ekle
Değişiklik: Constructor'a @Autowired ekle
Sonuç: Fix branch'i oluşturuldu
```

### Senaryo 2: Database Timeout
```
Hata: Connection timeout after 30s
Çözüm: Connection pool ayarlarını optimize et
Değişiklik: application.properties güncelle
Sonuç: Yapılandırma düzeltildi
```

### Senaryo 3: API Rate Limit
```
Hata: 429 Too Many Requests
Çözüm: Rate limiting ve retry logic ekle
Değişiklik: API client'a exponential backoff ekle
Sonuç: Resilient API client oluşturuldu
```

## ⚙️ Yapılandırma

### Minimal Config (config.yaml)
```yaml
elk:
  host: localhost
  port: 9200

git:
  repo_path: "."
  branch_prefix: "fix/"
```

### Tam Config
`config.example.yaml` dosyasına bakın.

## 🔍 Debugging

### Log Dosyası
Agent logları console'da görünür. İsterseniz redirect edebilirsiniz:
```bash
python cli.py --mock > system.log 2>&1
```

## 🎯 Best Practices

### ✅ Yapılması Gerekenler
- [ ] İlk önce mock modda test edin
- [ ] Üretilen kodu mutlaka gözden geçirin
- [ ] Testleri çalıştırın
- [ ] Küçük time range ile başlayın (15-30 dk)
- [ ] Branch'i push'lamadan önce inceleyin

### ❌ Yapılmaması Gerekenler
- [ ] Auto-push'u production'da aktif etmeyin
- [ ] Code review atlayıp merge etmeyin
- [ ] API key'leri config dosyasına yazmayın
- [ ] Çok büyük time range kullanmayın (>240 dk)
- [ ] Test çalıştırmadan production'a deploy etmeyin

## 🚨 Önemli Notlar

1. **Claude API**: Sistem Claude API kullanır, credential'lar gereklidir
2. **Review Zorunlu**: Tüm kod değişiklikleri review gerektirir
3. **Test**: Auto-generated kod test edilmelidir
4. **Backup**: Değişikliklerden önce backup alın
5. **Staging**: İlk önce staging'de test edin

## 📞 Yardım

```bash
# Tüm parametreleri görmek için
python cli.py --help

# Demo'yu çalıştır
python demo.py

# Detaylı dokümantasyon
type README.md
```

## 🔄 Tipik Workflow

```
1. Hata oluşur → ELK'de loglanır
                    ↓
2. Sistem her X dakikada bir çalışır (cron job / scheduled task)
                    ↓
3. Log Analyzer → Hataları tespit eder
                    ↓
4. Solution Architect → Çözüm önerir
                    ↓
5. Code Generator → Kodu düzeltir
                    ↓
6. Git Manager → Branch oluşturur
                    ↓
7. Developer → Review yapar → Merge eder
```

## 📊 Başarı Metrikleri

Sistem başarıyı şu metriklerde ölçer:
- **Fix Accuracy**: Çözümün doğruluğu
- **Time to Fix**: Hatadan fix'e kadar geçen süre
- **Auto-Fix Rate**: Otomatik fix edilebilen hataların oranı
- **False Positive**: Yanlış tespit edilen hataların sayısı

---

**İyi kodlamalar! 🚀**
