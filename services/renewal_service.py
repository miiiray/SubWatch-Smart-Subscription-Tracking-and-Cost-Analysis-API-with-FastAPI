import calendar
from datetime import date


def add_months(d: date, months: int) -> date:
    month_index = d.month - 1 + months
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(d.day, last_day))


def next_payment(d: date, cycle: str) -> date:
    return add_months(d, 1 if cycle == "monthly" else 12)


def roll_forward(payment_date: date, cycle: str, today: date) -> date:
    while payment_date < today:
        payment_date = next_payment(payment_date, cycle)
    return payment_date


def days_until(payment_date: date, today: date) -> int:
    return (payment_date - today).days