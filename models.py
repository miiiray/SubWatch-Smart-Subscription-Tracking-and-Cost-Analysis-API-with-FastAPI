from datetime import date, datetime
from enum import Enum

from sqlmodel import Field, SQLModel


# ---------- Sabit seçenekler ----------
class BillingCycle(str, Enum):
    monthly = "monthly"
    yearly = "yearly"


class Currency(str, Enum):
    TRY = "TRY"
    USD = "USD"
    EUR = "EUR"


# ---------- USER ----------
class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    email: str = Field(unique=True, index=True)
    password_hash: str
    monthly_budget: float = 1000


class UserRegister(SQLModel):
    name: str
    email: str
    password: str = Field(min_length=6)
    monthly_budget: float = Field(default=1000, ge=0)


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
    service_name: str
    category: str = "other"
    price: float = Field(gt=0)
    currency: Currency = Currency.TRY
    billing_cycle: BillingCycle = BillingCycle.monthly
    next_payment_date: date
    is_trial: bool = False
    trial_end_date: date | None = None


class Subscription(SubscriptionBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    is_active: bool = True
    created_on: date = Field(default_factory=date.today)


class SubscriptionCreate(SubscriptionBase):
    pass


class SubscriptionUpdate(SQLModel):
    service_name: str | None = None
    category: str | None = None
    price: float | None = Field(default=None, gt=0)
    currency: Currency | None = None
    billing_cycle: BillingCycle | None = None
    next_payment_date: date | None = None
    is_trial: bool | None = None
    trial_end_date: date | None = None


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