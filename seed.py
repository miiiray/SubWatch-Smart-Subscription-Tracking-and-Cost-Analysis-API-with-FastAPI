"""
seed.py — Sunum için örnek veri ekler.
DİKKAT: Çalıştırınca veritabanını SIFIRLAR ve baştan doldurur.
Çalıştırmak için:  python seed.py
"""
import random
from datetime import date, timedelta

from sqlmodel import Session, SQLModel

from database import engine
from models import BillingCycle, Currency, PriceHistory, Subscription, UsageLog, User

random.seed(42)          # her çalıştırmada aynı "rastgele" veri
today = date.today()


def days_ago(n: int) -> date:
    return today - timedelta(days=n)


def days_later(n: int) -> date:
    return today + timedelta(days=n)


def add_usage(session, sub: Subscription, pattern: str):
    """pattern: 'daily' (sık), 'rare' (ayda 1-2), 'none' (75 gündür yok)"""
    if pattern == "daily":
        dates = [days_ago(d) for d in range(0, 90) if random.random() < 0.6]
    elif pattern == "rare":
        dates = [days_ago(random.randint(3, 28)), days_ago(random.randint(40, 80))]
    else:  # none
        dates = [days_ago(75), days_ago(90)]
    for d in dates:
        session.add(UsageLog(subscription_id=sub.id, used_on=d))


def main():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        ayse = User(name="Ayşe Yılmaz", email="ayse@example.com", monthly_budget=900)
        can = User(name="Can Demir", email="can@example.com", monthly_budget=600)
        session.add_all([ayse, can])
        session.commit()
        session.refresh(ayse)
        session.refresh(can)

        # (kullanıcı, servis, kategori, fiyat, para birimi, döngü, kaç gün sonra ödeme, kullanım, deneme bitişi)
        data = [
            (ayse, "Netflix", "entertainment", 229.99, "TRY", "monthly", 3, "rare", None),
            (ayse, "Spotify", "music", 99.00, "TRY", "monthly", 10, "daily", None),
            (ayse, "YouTube Premium", "entertainment", 79.99, "TRY", "monthly", 5, "daily", None),
            (ayse, "iCloud+", "cloud", 39.99, "TRY", "monthly", 18, "none", None),
            (ayse, "ChatGPT Plus", "productivity", 20.00, "USD", "monthly", 12, "daily", None),
            (ayse, "Duolingo Super", "education", 1199.00, "TRY", "yearly", 140, "rare", None),
            (ayse, "Disney+", "entertainment", 134.99, "TRY", "monthly", 2, "rare", days_later(2)),
            (can, "Spotify", "music", 99.00, "TRY", "monthly", 7, "daily", None),
            (can, "Amazon Prime", "shopping", 69.90, "TRY", "monthly", 20, "none", None),
            (can, "Adobe Creative Cloud", "productivity", 12.00, "EUR", "monthly", 4, "rare", None),
        ]

        subs = {}
        for user, name, cat, price, cur, cycle, pay_in, pattern, trial_end in data:
            sub = Subscription(
                user_id=user.id,
                service_name=name,
                category=cat,
                price=price,
                currency=Currency(cur),
                billing_cycle=BillingCycle(cycle),
                next_payment_date=days_later(pay_in),
                is_trial=trial_end is not None,
                trial_end_date=trial_end,
                created_on=days_ago(120),
            )
            session.add(sub)
            session.commit()
            session.refresh(sub)
            add_usage(session, sub, pattern)
            subs[(user.id, name)] = sub

        # Zam geçmişi
        netflix = subs[(ayse.id, "Netflix")]
        spotify = subs[(ayse.id, "Spotify")]
        session.add_all([
            PriceHistory(subscription_id=netflix.id, old_price=149.99, new_price=189.99, changed_on=days_ago(300)),
            PriceHistory(subscription_id=netflix.id, old_price=189.99, new_price=229.99, changed_on=days_ago(60)),
            PriceHistory(subscription_id=spotify.id, old_price=79.00, new_price=99.00, changed_on=days_ago(150)),
        ])
        session.commit()

    print("Örnek veri eklendi: 2 kullanıcı, 10 abonelik, kullanım kayıtları ve zamlar.")


if __name__ == "__main__":
    main()
