import re
from datetime import date, datetime
from enum import Enum

from pydantic import field_validator
from sqlmodel import Field, SQLModel


# ---------- Sabit seçenekler ----------
class BillingCycle(str, Enum):
    monthly = "monthly"
    yearly = "yearly"


class Currency(str, Enum):
    TRY = "TRY"
    USD = "USD"
    EUR = "EUR"


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ---------- USER ----------
class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    email: str = Field(unique=True, index=True)
    password_hash: str
    monthly_budget: float = 1000


class UserRegister(SQLModel):
    name: str = Field(max_length=100)
    email: str = Field(max_length=254)
    password: str = Field(min_length=6)
    monthly_budget: float = Field(default=1000, ge=0)

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Ad boş olamaz.")
        return value

    @field_validator("email")
    @classmethod
    def email_format(cls, value: str) -> str:
        value = value.strip().lower()
        if not EMAIL_PATTERN.match(value):
            raise ValueError("Geçerli bir e-posta adresi gir.")
        return value


class UserLogin(SQLModel):
    email: str
    password: str


class UserPublic(SQLModel):
    id: int
    name: str
    email: str
    monthly_budget: float

# ---------- AUTH TOKEN ----------
class AuthToken(SQLModel, table=True):
    token: str = Field(primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    expires_at: datetime

# ---------- SUBSCRIPTION ----------
class SubscriptionBase(SQLModel):
    service_name: str = Field(max_length=100)
    category: str = "other"
    price: float = Field(gt=0)
    currency: Currency = Currency.TRY
    billing_cycle: BillingCycle = BillingCycle.monthly
    next_payment_date: date
    is_trial: bool = False
    trial_end_date: date | None = None

    @field_validator("service_name")
    @classmethod
    def service_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Servis adı boş olamaz.")
        return value


class Subscription(SubscriptionBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    is_active: bool = True
    created_on: date = Field(default_factory=date.today)


class SubscriptionCreate(SubscriptionBase):
    pass


class SubscriptionUpdate(SQLModel):
    service_name: str | None = Field(default=None, max_length=100)
    category: str | None = None
    price: float | None = Field(default=None, gt=0)
    currency: Currency | None = None
    billing_cycle: BillingCycle | None = None
    next_payment_date: date | None = None
    is_trial: bool | None = None
    trial_end_date: date | None = None

    @field_validator("service_name")
    @classmethod
    def service_not_blank(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("Servis adı boş olamaz.")
        return value.strip() if value else value


# ---------- USAGE LOG ----------
class UsageLog(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    subscription_id: int = Field(foreign_key="subscription.id", index=True)
    used_on: date = Field(default_factory=date.today)


class UsageCreate(SQLModel):
    used_on: date | None = None


# ---------- PRICE HISTORY ----------
class PriceHistory(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    subscription_id: int = Field(foreign_key="subscription.id", index=True)
    old_price: float
    new_price: float
    changed_on: date = Field(default_factory=date.today)