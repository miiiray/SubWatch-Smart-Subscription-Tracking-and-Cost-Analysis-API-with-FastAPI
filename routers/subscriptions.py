from datetime import date

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from database import SessionDep
from models import (
    PriceHistory,
    Subscription,
    SubscriptionCreate,
    SubscriptionUpdate,
    UsageCreate,
    UsageLog,
    User,
)
from security import CurrentUser

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


def get_own_subscription(session, subscription_id: int, user: User) -> Subscription:
    sub = session.get(Subscription, subscription_id)
    if sub is None or sub.user_id != user.id:
        raise HTTPException(status_code=404, detail="Abonelik bulunamadı.")
    return sub


@router.post("", response_model=Subscription, status_code=201)
def create_subscription(data: SubscriptionCreate, user: CurrentUser, session: SessionDep):
    if data.is_trial and not data.trial_end_date:
        raise HTTPException(status_code=400, detail="Deneme sürümü için bitiş tarihi gerekli.")

    sub = Subscription.model_validate(data, update={"user_id": user.id})
    session.add(sub)
    session.commit()
    session.refresh(sub)
    return sub


@router.get("", response_model=list[Subscription])
def list_subscriptions(
    user: CurrentUser,
    session: SessionDep,
    category: str | None = None,
    active_only: bool = True,
):
    query = select(Subscription).where(Subscription.user_id == user.id)
    if category:
        query = query.where(Subscription.category == category)
    if active_only:
        query = query.where(Subscription.is_active == True)
    return session.exec(query.order_by(Subscription.next_payment_date)).all()


@router.get("/{subscription_id}", response_model=Subscription)
def get_subscription(subscription_id: int, user: CurrentUser, session: SessionDep):
    return get_own_subscription(session, subscription_id, user)


@router.patch("/{subscription_id}", response_model=Subscription)
def update_subscription(
    subscription_id: int, data: SubscriptionUpdate, user: CurrentUser, session: SessionDep
):
    sub = get_own_subscription(session, subscription_id, user)
    changes = data.model_dump(exclude_unset=True)
    # Zorunlu alanlara null gönderilirse yok say (sadece trial_end_date boş olabilir)
    changes = {k: v for k, v in changes.items() if v is not None or k == "trial_end_date"}

    if "price" in changes and changes["price"] != sub.price:
        session.add(PriceHistory(
            subscription_id=sub.id,
            old_price=sub.price,
            new_price=changes["price"],
        ))

    sub.sqlmodel_update(changes)
    session.add(sub)
    session.commit()
    session.refresh(sub)
    return sub


@router.delete("/{subscription_id}")
def cancel_subscription(subscription_id: int, user: CurrentUser, session: SessionDep):
    sub = get_own_subscription(session, subscription_id, user)
    sub.is_active = False
    session.add(sub)
    session.commit()
    return {"message": f"{sub.service_name} aboneliği iptal edildi."}


@router.post("/{subscription_id}/usage", response_model=UsageLog, status_code=201)
def log_usage(
    subscription_id: int, user: CurrentUser, session: SessionDep, data: UsageCreate | None = None
):
    sub = get_own_subscription(session, subscription_id, user)
    if not sub.is_active:
        raise HTTPException(status_code=400, detail="İptal edilmiş aboneliğe kullanım eklenemez.")

    used_on = data.used_on if data and data.used_on else date.today()
    if used_on > date.today():
        raise HTTPException(status_code=400, detail="Gelecek tarihli kullanım eklenemez.")

    log = UsageLog(subscription_id=sub.id, used_on=used_on)
    session.add(log)
    session.commit()
    session.refresh(log)
    return log


@router.get("/{subscription_id}/price-history", response_model=list[PriceHistory])
def price_history(subscription_id: int, user: CurrentUser, session: SessionDep):
    get_own_subscription(session, subscription_id, user)
    query = (
        select(PriceHistory)
        .where(PriceHistory.subscription_id == subscription_id)
        .order_by(PriceHistory.changed_on)
    )
    return session.exec(query).all()