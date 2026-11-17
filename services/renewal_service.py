"""
renewal_service.py — Yenileme (ödeme) tarihi hesapları.
Bu dosyada veritabanı yok, sadece tarih hesabı var.
"""
import calendar
from datetime import date


def add_months(d: date, months: int) -> date:
    """Tarihe ay ekler. 31 Ocak + 1 ay → 28/29 Şubat (ayın son günü)."""
    month_index = d.month - 1 + months
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(d.day, last_day))


def next_payment(d: date, cycle: str) -> date:
    """Bir sonraki ödeme günü: aylıksa +1 ay, yıllıksa +12 ay."""
    return add_months(d, 1 if cycle == "monthly" else 12)


def roll_forward(payment_date: date, cycle: str, today: date) -> date:
    """Ödeme günü geçmişte kaldıysa, bugüne gelene kadar ileri sarar."""
    while payment_date < today:
        payment_date = next_payment(payment_date, cycle)
    return payment_date


def days_until(payment_date: date, today: date) -> int:
    """Ödemeye kaç gün kaldı?"""
    return (payment_date - today).days
