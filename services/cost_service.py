"""
cost_service.py — Maliyet hesapları: aylık/yıllık toplam, kategori, bütçe.
"""


def code_of(currency) -> str:
    """Currency.USD veya "USD" gelse de "USD" döndürür."""
    return getattr(currency, "value", currency)


def monthly_cost(price: float, cycle: str) -> float:
    """Yıllık aboneliği aylığa çevirir (fiyat / 12)."""
    return price if cycle == "monthly" else price / 12


def to_try(amount: float, currency, rates: dict) -> float:
    """Tutarı TL'ye çevirir. rates örneği: {"TRY": 1, "USD": 42.1, "EUR": 49.3}"""
    return amount * rates.get(code_of(currency), 1.0)


def build_summary(items: list[dict], monthly_budget: float) -> dict:
    """
    items: [{"service_name": "Netflix", "category": "entertainment", "monthly_try": 229.99}, ...]
    """
    total_monthly = sum(item["monthly_try"] for item in items)

    by_category: dict[str, float] = {}
    for item in items:
        by_category[item["category"]] = by_category.get(item["category"], 0) + item["monthly_try"]

    most_expensive = max(items, key=lambda item: item["monthly_try"]) if items else None

    return {
        "subscription_count": len(items),
        "total_monthly": round(total_monthly, 2),
        "total_yearly": round(total_monthly * 12, 2),
        "monthly_budget": monthly_budget,
        "budget_left": round(monthly_budget - total_monthly, 2),
        "over_budget": total_monthly > monthly_budget,
        "by_category": [
            {"category": cat, "monthly": round(value, 2)}
            for cat, value in sorted(by_category.items(), key=lambda pair: pair[1], reverse=True)
        ],
        "most_expensive": most_expensive["service_name"] if most_expensive else None,
    }
