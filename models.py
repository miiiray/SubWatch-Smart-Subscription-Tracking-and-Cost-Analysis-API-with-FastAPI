"""
models.py — Veritabanı tabloları ve API'ye gelen verinin şekli.

SQLModel'de:
  - table=True olan sınıflar  → veritabanında TABLO olur
  - table=True olmayan sınıflar → sadece gelen veriyi kontrol eder (şema)
"""
from datetime import date
from enum import Enum

from sqlmodel import Field, SQLModel


# ---------- Sabit seçenekler ----------
class BillingCycle(str, Enum):
    monthly = "monthly"   # aylık
    yearly = "yearly"     # yıllık


class Currency(str, Enum):
    TRY = "TRY"
    USD = "USD"
    EUR = "EUR"


# ---------- USER (Kullanıcı) ----------
class UserBase(SQLModel):
    name: str
    email: str = Field(unique=True, index=True)
    monthly_budget: float = Field(default=1000, ge=0)   # aylık abonelik bütçesi (TL)


class User(UserBase, table=True):
    id: int | None = Field(default=None, primary_key=True)


class UserCreate(UserBase):
    pass


# ---------- SUBSCRIPTION (Abonelik) ----------
class SubscriptionBase(SQLModel):
    service_name: str                                   # Netflix, Spotify...
    category: str = "other"                             # entertainment, music, cloud...
    price: float = Field(gt=0)                          # 0'dan büyük olmalı
    currency: Currency = Currency.TRY
    billing_cycle: BillingCycle = BillingCycle.monthly
    next_payment_date: date                             # sonraki ödeme günü
    is_trial: bool = False                              # deneme sürümü mü?
    trial_end_date: date | None = None


class Subscription(SubscriptionBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    is_active: bool = True                              # iptal edilince False olur
    created_on: date = Field(default_factory=date.today)


class SubscriptionCreate(SubscriptionBase):
    user_id: int


class SubscriptionUpdate(SQLModel):
    """Güncellemede her alan isteğe bağlı: sadece gönderilen alan değişir."""
    service_name: str | None = None
    category: str | None = None
    price: float | None = Field(default=None, gt=0)
    currency: Currency | None = None
    billing_cycle: BillingCycle | None = None
    next_payment_date: date | None = None
    is_trial: bool | None = None
    trial_end_date: date | None = None


# ---------- USAGE LOG (Kullanım kaydı) ----------
class UsageLog(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    subscription_id: int = Field(foreign_key="subscription.id", index=True)
    used_on: date = Field(default_factory=date.today)


class UsageCreate(SQLModel):
    used_on: date | None = None     # boş bırakılırsa bugün sayılır


# ---------- PRICE HISTORY (Fiyat geçmişi / zamlar) ----------
class PriceHistory(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    subscription_id: int = Field(foreign_key="subscription.id", index=True)
    old_price: float
    new_price: float
    changed_on: date = Field(default_factory=date.today)
