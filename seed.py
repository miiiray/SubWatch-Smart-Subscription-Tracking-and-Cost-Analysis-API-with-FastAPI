import random
from datetime import date, timedelta

from sqlmodel import Session, SQLModel

from database import engine
from models import BillingCycle, Currency, PriceHistory, Subscription, UsageLog, User
from security import hash_password

random.seed(42)
today = date.today()


def days_ago(n):
    return today - timedelta(days=n)


def days_later(n):
    return today + timedelta(days=n)


def add_usage(session, subscription_id, pattern):
    if pattern == "daily":
        dates = [days_ago(d) for d in range(0, 90) if random.random() < 0.6]
    elif pattern == "rare":
        dates = [days_ago(random.randint(3, 28)), days_ago(random.randint(40, 80))]
    else:
        dates = [days_ago(75), days_ago(90)]
    for d in dates:
        session.add(UsageLog(subscription_id=subscription_id, used_on=d))


# (kısa ad, ad soyad, şifre, aylık bütçe)
USERS = [
    ("miray", "Miray Şahin", "miray123", 1000),
    ("alp", "Alp Eren Sarı", "alp123", 900),
    ("enes", "Enes Meriç Tükenmez", "enes123", 1200),
]

# (kimin, servis, kategori, fiyat, para birimi, döngü, kaç gün sonra ödeme, kullanım, deneme bitişi)
SUBSCRIPTIONS = [
    ("miray", "Netflix", "entertainment", 229.99, "TRY", "monthly", 3, "rare", None),
    ("miray", "Spotify", "music", 99.00, "TRY", "monthly", 10, "daily", None),
    ("miray", "YouTube Premium", "entertainment", 79.99, "TRY", "monthly", 5, "daily", None),
    ("miray", "iCloud+", "cloud", 39.99, "TRY", "monthly", 18, "none", None),
    ("miray", "ChatGPT Plus", "productivity", 20.00, "USD", "monthly", 12, "daily", None),
    ("miray", "Duolingo Super", "education", 1199.00, "TRY", "yearly", 140, "rare", None),
    ("miray", "Disney+", "entertainment", 134.99, "TRY", "monthly", 2, "rare", days_later(2)),
    ("alp", "Spotify", "music", 99.00, "TRY", "monthly", 7, "daily", None),
    ("alp", "Amazon Prime", "shopping", 69.90, "TRY", "monthly", 20, "none", None),
    ("alp", "Adobe Creative Cloud", "productivity", 12.00, "EUR", "monthly", 4, "rare", None),
    ("enes", "Xbox Game Pass", "gaming", 359.00, "TRY", "monthly", 6, "daily", None),
    ("enes", "Apple Music", "music", 64.99, "TRY", "monthly", 15, "none", None),
    ("enes", "Notion Plus", "productivity", 10.00, "USD", "monthly", 1, "rare", None),
]


def main():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        users = {}
        for key, name, password, budget in USERS:
            user = User(
                name=name,
                email=f"{key}@test.com",
                password_hash=hash_password(password),
                monthly_budget=budget,
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            users[key] = user

        subs = {}
        for key, name, cat, price, cur, cycle, pay_in, pattern, trial_end in SUBSCRIPTIONS:
            sub = Subscription(
                user_id=users[key].id,
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
            add_usage(session, sub.id, pattern)
            subs[(key, name)] = sub

        session.add_all([
            PriceHistory(subscription_id=subs[("miray", "Netflix")].id,
                         old_price=149.99, new_price=189.99, changed_on=days_ago(300)),
            PriceHistory(subscription_id=subs[("miray", "Netflix")].id,
                         old_price=189.99, new_price=229.99, changed_on=days_ago(60)),
            PriceHistory(subscription_id=subs[("miray", "Spotify")].id,
                         old_price=79.00, new_price=99.00, changed_on=days_ago(150)),
            PriceHistory(subscription_id=subs[("enes", "Xbox Game Pass")].id,
                         old_price=249.00, new_price=359.00, changed_on=days_ago(90)),
        ])
        session.commit()

    print("Örnek veri eklendi. Giriş bilgileri:")
    for key, name, password, _ in USERS:
        print(f"  {name:<22} {key}@test.com / {password}")


if __name__ == "__main__":
    main()