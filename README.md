# SubWatch — Smart Subscription Tracking and Cost Analysis API

FastAPI + SQLModel (SQLite) ile yazılmış abonelik takip API'si ve web arayüzü.

## Kurulum
```bash
pip install -r requirements.txt
```

## Çalıştırma
```bash
python seed.py        # (isteğe bağlı) örnek veri ekler — veritabanını sıfırlar!
fastapi dev main.py   # sunucuyu başlatır
```
- Web sitesi: http://127.0.0.1:8000
- API dokümanı (Swagger): http://127.0.0.1:8000/docs

## Mimari
```
Router (routers/)  →  Service (services/)  →  Model (models.py)  →  SQLite (subwatch.db)
                            └──► Frankfurter API (canlı döviz kuru)
```

## Endpoint'ler
| Metot | Yol | Açıklama |
|---|---|---|
| POST | /users | Kullanıcı oluştur |
| GET | /users, /users/{id} | Kullanıcıları listele / getir |
| POST | /subscriptions | Abonelik ekle |
| GET | /subscriptions?user_id=&category= | Listele / filtrele |
| GET | /subscriptions/{id} | Abonelik detayı |
| PATCH | /subscriptions/{id} | Güncelle (fiyat değişirse zam geçmişine yazılır) |
| DELETE | /subscriptions/{id} | İptal et (pasif yapar) |
| POST | /subscriptions/{id}/usage | "Bugün kullandım" kaydı |
| GET | /subscriptions/{id}/price-history | Zam geçmişi |
| GET | /users/{id}/upcoming?days=7 | Yaklaşan ödemeler |
| GET | /users/{id}/summary | Aylık/yıllık toplam, kategori, bütçe |
| GET | /users/{id}/unused?threshold=60 | Kullanılmayan abonelikler |
| GET | /users/{id}/insights | Akıllı öneriler |
| GET | /rates | Canlı döviz kuru |
