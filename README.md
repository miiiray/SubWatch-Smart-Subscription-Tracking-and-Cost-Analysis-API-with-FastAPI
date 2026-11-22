# SubWatch — Smart Subscription Tracking and Cost Analysis API with FastAPI

Kullanıcıların Netflix, Spotify, iCloud gibi aboneliklerini tek yerden takip ettiği,
yenileme tarihlerini hatırlatan, maliyeti hesaplayan ve kullanılmayan abonelikleri
tespit eden bir FastAPI projesi. Giriş sistemi vardır; her kullanıcı **sadece kendi verisini** görür.

## Teknolojiler
- **FastAPI** — backend / REST API
- **SQLModel + SQLite** — veritabanı
- **HTML + CSS + JavaScript** — web arayüzü
- **Frankfurter API** — canlı döviz kuru (USD/EUR → TRY)

## Kurulum
```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Çalıştırma
```bash
python seed.py          # örnek veri (veritabanını sıfırlar!)
fastapi dev main.py     # sunucuyu başlatır
```
- Web sitesi: http://127.0.0.1:8000
- API dokümanı (Swagger): http://127.0.0.1:8000/docs

### Demo hesapları
| Kullanıcı | E-posta | Şifre |
|---|---|---|
| Miray Şahin | miray@test.com | miray123 |
| Alp Eren Sarı | alp@test.com | alp123 |
| Enes Meriç Tükenmez | enes@test.com | enes123 |

## Mimari
```
Tarayıcı (static/)  →  Router (routers/)  →  Security (security.py)
                                         →  Service (services/)  →  Model (models.py)  →  SQLite
                                                   └──► Frankfurter API (döviz kuru)
```

## Giriş sistemi
- Şifreler **PBKDF2-SHA256 + salt** ile hash'lenerek saklanır (düz şifre tutulmaz).
- Girişte rastgele bir **token** üretilir ve `AuthToken` tablosuna yazılır (7 gün geçerli).
- Her istekte `Authorization: Bearer <token>` başlığı gönderilir; çıkışta token silinir.
- Bir kullanıcı başkasının aboneliğine erişmeye çalışırsa **404** döner.

## Endpoint'ler
| Metot | Yol | Açıklama |
|---|---|---|
| POST | /auth/register | Kayıt ol |
| POST | /auth/login | Giriş yap (token döner) |
| POST | /auth/logout | Çıkış yap |
| GET | /auth/me | Giriş yapan kullanıcı |
| POST | /subscriptions | Abonelik ekle |
| GET | /subscriptions?category= | Aboneliklerimi listele |
| GET | /subscriptions/{id} | Abonelik detayı |
| PATCH | /subscriptions/{id} | Güncelle (fiyat değişirse zam geçmişine yazılır) |
| DELETE | /subscriptions/{id} | İptal et |
| POST | /subscriptions/{id}/usage | "Bugün kullandım" kaydı |
| GET | /subscriptions/{id}/price-history | Zam geçmişi |
| GET | /me/summary | Aylık/yıllık toplam, bütçe, kategori dağılımı |
| GET | /me/upcoming?days=7 | Yaklaşan ödemeler |
| GET | /me/unused?threshold=60 | Kullanılmayan abonelikler |
| GET | /me/insights | Akıllı öneriler |
| GET | /rates | Canlı döviz kuru |

## Akıllı öneriler (kural tabanlı)
1. Aylık bütçe aşıldı mı?
2. Deneme sürümü 3 gün içinde bitiyor mu?
3. 60+ gündür kullanılmayan abonelik var mı? → yıllık tasarruf hesabı
4. Son 30 günde 1-2 kez kullanılan abonelik → kullanım başına maliyet
5. Son 1 yılda zam yapan servisler

## Takım
Miray Şahin · Alp Eren Sarı · Enes Meriç Tükenmez
