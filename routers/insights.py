"""
routers/insights.py — "Akıllı" endpoint'ler.
Router veriyi veritabanından toplar, hesabı services/ klasöründeki fonksiyonlar yapar.
"""
from datetime import date, timedelta

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from database import SessionDep
from models import PriceHistory, Subscription, UsageLog, User
from services import cost_service, currency_service, renewal_service, usage_service

router = APIRouter(tags=["Insights"])


# ---------- Yardımcı fonksiyonlar ----------
def get_user_or_404(session, user_id: int) -> User:
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")
    return user


def active_subscriptions(session, user_id: int, today: date) -> list[Subscription]:
    """Aktif abonelikleri getirir; ödeme günü geçmiş olanların tarihini ileri sarar."""
    subs = session.exec(
        select(Subscription)
        .where(Subscription.user_id == user_id, Subscription.is_active == True)  # noqa: E712
    ).all()

    changed = False
    for sub in subs:
        new_date = renewal_service.roll_forward(sub.next_payment_date, sub.billing_cycle, today)
        if new_date != sub.next_payment_date:
            sub.next_payment_date = new_date
            session.add(sub)
            changed = True
    if changed:
        session.commit()
    return subs


def monthly_try(sub: Subscription, rates: dict) -> float:
    monthly = cost_service.monthly_cost(sub.price, sub.billing_cycle)
    return cost_service.to_try(monthly, sub.currency, rates)


def usage_stats(session, sub: Subscription, today: date) -> tuple[int, int, date | None]:
    """(boşta geçen gün, son 30 gündeki kullanım sayısı, son kullanım tarihi)"""
    last_used = session.exec(
        select(func.max(UsageLog.used_on)).where(UsageLog.subscription_id == sub.id)
    ).one()
    uses_30 = session.exec(
        select(func.count(UsageLog.id)).where(
            UsageLog.subscription_id == sub.id,
            UsageLog.used_on >= today - timedelta(days=30),
        )
    ).one()
    idle = usage_service.days_idle(last_used, sub.created_on, today)
    return idle, uses_30, last_used


# ---------- Endpoint'ler ----------
@router.get("/rates")
def exchange_rates():
    """Canlı döviz kuru (Frankfurter API)."""
    return currency_service.get_rates()


@router.get("/users/{user_id}/upcoming")
def upcoming_payments(user_id: int, session: SessionDep, days: int = 7):
    """Önümüzdeki X gün içinde yenilenecek abonelikler."""
    get_user_or_404(session, user_id)
    today = date.today()
    result = []
    for sub in active_subscriptions(session, user_id, today):
        left = renewal_service.days_until(sub.next_payment_date, today)
        if left <= days:
            result.append({
                "id": sub.id,
                "service_name": sub.service_name,
                "next_payment_date": sub.next_payment_date,
                "days_left": left,
                "price": sub.price,
                "currency": sub.currency,
            })
    return sorted(result, key=lambda item: item["days_left"])


@router.get("/users/{user_id}/summary")
def cost_summary(user_id: int, session: SessionDep):
    """Aylık/yıllık toplam (TL), kategori dağılımı, bütçe durumu."""
    user = get_user_or_404(session, user_id)
    rate_info = currency_service.get_rates()
    items = [
        {
            "service_name": sub.service_name,
            "category": sub.category,
            "monthly_try": monthly_try(sub, rate_info["rates"]),
        }
        for sub in active_subscriptions(session, user_id, date.today())
    ]
    summary = cost_service.build_summary(items, user.monthly_budget)
    summary["rates_source"] = rate_info["source"]
    return summary


@router.get("/users/{user_id}/unused")
def unused_subscriptions(user_id: int, session: SessionDep, threshold: int = 60):
    """X gündür kullanılmayan abonelikler."""
    get_user_or_404(session, user_id)
    today = date.today()
    rates = currency_service.get_rates()["rates"]
    result = []
    for sub in active_subscriptions(session, user_id, today):
        idle, _, last_used = usage_stats(session, sub, today)
        if usage_service.is_unused(idle, threshold):
            cost = monthly_try(sub, rates)
            result.append({
                "id": sub.id,
                "service_name": sub.service_name,
                "idle_days": idle,
                "last_used": last_used,
                "monthly_try": round(cost, 2),
                "yearly_saving": round(cost * 12, 2),
            })
    return sorted(result, key=lambda item: item["idle_days"], reverse=True)


@router.get("/users/{user_id}/insights")
def smart_insights(user_id: int, session: SessionDep):
    """Tüm akıllı öneriler: bütçe, deneme bitişi, kullanılmayan, az kullanılan, zamlar."""
    user = get_user_or_404(session, user_id)
    today = date.today()
    rates = currency_service.get_rates()["rates"]

    items = []
    for sub in active_subscriptions(session, user_id, today):
        idle, uses_30, _ = usage_stats(session, sub, today)
        changes = session.exec(
            select(PriceHistory)
            .where(PriceHistory.subscription_id == sub.id)
            .order_by(PriceHistory.changed_on)
        ).all()
        items.append({
            "service_name": sub.service_name,
            "category": sub.category,
            "monthly_try": monthly_try(sub, rates),
            "idle_days": idle,
            "uses_30": uses_30,
            "is_trial": sub.is_trial,
            "trial_end_date": sub.trial_end_date,
            "price_changes": [(c.old_price, c.new_price, c.changed_on) for c in changes],
        })

    summary = cost_service.build_summary(items, user.monthly_budget)
    return usage_service.build_insights(items, summary, today)
