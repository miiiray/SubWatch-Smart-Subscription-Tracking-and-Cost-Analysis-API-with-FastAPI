"""
routers/subscriptions.py — Abonelik CRUD + kullanım kaydı + fiyat geçmişi.
"""
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

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


def get_subscription_or_404(session, subscription_id: int) -> Subscription:
    sub = session.get(Subscription, subscription_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Abonelik bulunamadı.")
    return sub


@router.post("", response_model=Subscription, status_code=201)
def create_subscription(sub_in: SubscriptionCreate, session: SessionDep):
    if not session.get(User, sub_in.user_id):
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")
    if sub_in.is_trial and not sub_in.trial_end_date:
        raise HTTPException(status_code=400, detail="Deneme sürümü için bitiş tarihi gerekli.")

    sub = Subscription.model_validate(sub_in)
    session.add(sub)
    session.commit()
    session.refresh(sub)
    return sub


@router.get("", response_model=list[Subscription])
def list_subscriptions(
    session: SessionDep,
    user_id: int | None = None,
    category: str | None = None,
    active_only: bool = True,
):
    """Örnek: /subscriptions?user_id=1&category=music"""
    query = select(Subscription)
    if user_id is not None:
        query = query.where(Subscription.user_id == user_id)
    if category:
        query = query.where(Subscription.category == category)
    if active_only:
        query = query.where(Subscription.is_active == True)  # noqa: E712
    return session.exec(query.order_by(Subscription.next_payment_date)).all()


@router.get("/{subscription_id}", response_model=Subscription)
def get_subscription(subscription_id: int, session: SessionDep):
    return get_subscription_or_404(session, subscription_id)


@router.patch("/{subscription_id}", response_model=Subscription)
def update_subscription(subscription_id: int, sub_in: SubscriptionUpdate, session: SessionDep):
    sub = get_subscription_or_404(session, subscription_id)
    data = sub_in.model_dump(exclude_unset=True)   # sadece gönderilen alanlar

    # Fiyat değiştiyse fiyat geçmişine otomatik kaydet (zam takibi)
    if "price" in data and data["price"] != sub.price:
        session.add(PriceHistory(
            subscription_id=sub.id,
            old_price=sub.price,
            new_price=data["price"],
        ))

    sub.sqlmodel_update(data)
    session.add(sub)
    session.commit()
    session.refresh(sub)
    return sub


@router.delete("/{subscription_id}")
def cancel_subscription(subscription_id: int, session: SessionDep):
    """Silmek yerine pasif yapıyoruz: geçmiş veriler (kullanım, zam) kaybolmasın."""
    sub = get_subscription_or_404(session, subscription_id)
    sub.is_active = False
    session.add(sub)
    session.commit()
    return {"message": f"{sub.service_name} aboneliği iptal edildi."}


@router.post("/{subscription_id}/usage", response_model=UsageLog, status_code=201)
def log_usage(subscription_id: int, session: SessionDep, usage_in: UsageCreate | None = None):
    """'Bugün kullandım' kaydı. Gövde boş gönderilebilir."""
    sub = get_subscription_or_404(session, subscription_id)
    if not sub.is_active:
        raise HTTPException(status_code=400, detail="İptal edilmiş aboneliğe kullanım eklenemez.")

    used_on = usage_in.used_on if usage_in and usage_in.used_on else date.today()
    if used_on > date.today():
        raise HTTPException(status_code=400, detail="Gelecek tarihli kullanım eklenemez.")

    log = UsageLog(subscription_id=sub.id, used_on=used_on)
    session.add(log)
    session.commit()
    session.refresh(log)
    return log


@router.get("/{subscription_id}/price-history", response_model=list[PriceHistory])
def price_history(subscription_id: int, session: SessionDep):
    get_subscription_or_404(session, subscription_id)
    query = (
        select(PriceHistory)
        .where(PriceHistory.subscription_id == subscription_id)
        .order_by(PriceHistory.changed_on)
    )
    return session.exec(query).all()
