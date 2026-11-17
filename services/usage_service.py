"""
usage_service.py — Kullanım analizi ve akıllı öneriler.
"""
from datetime import date

UNUSED_DAYS = 60        # bu kadar gün kullanılmayan abonelik "kullanılmıyor" sayılır
TRIAL_WARNING_DAYS = 3  # deneme bitmeden kaç gün önce uyarılsın


def days_idle(last_used: date | None, created_on: date, today: date) -> int:
    """Son kullanımdan bu yana kaç gün geçti? Hiç kullanılmadıysa eklendiği günden sayar."""
    reference = last_used or created_on
    return (today - reference).days


def is_unused(idle_days: int, threshold: int = UNUSED_DAYS) -> bool:
    return idle_days >= threshold


def cost_per_use(monthly_try: float, uses_last_30_days: int) -> float | None:
    """Kullanım başına maliyet. Hiç kullanılmadıysa None."""
    if uses_last_30_days == 0:
        return None
    return round(monthly_try / uses_last_30_days, 2)


def build_insights(items: list[dict], summary: dict, today: date) -> list[dict]:
    """
    items içindeki her abonelik için:
      service_name, monthly_try, idle_days, uses_30, is_trial, trial_end_date,
      price_changes: [(old_price, new_price, changed_on), ...]
    Her öneri: {"level": "danger" | "warning" | "info" | "success", "message": "..."}
    """
    insights = []

    # 1) Bütçe aşımı
    if summary["over_budget"]:
        over = -summary["budget_left"]
        insights.append({
            "level": "danger",
            "message": f"Aylık bütçeni {over:.2f} TL aştın.",
        })

    for item in items:
        name = item["service_name"]

        # 2) Deneme sürümü bitiyor
        if item["is_trial"] and item["trial_end_date"]:
            left = (item["trial_end_date"] - today).days
            if 0 <= left <= TRIAL_WARNING_DAYS:
                insights.append({
                    "level": "warning",
                    "message": f"{name} deneme süren {left} gün sonra bitiyor. "
                               f"İptal etmezsen ücret alınacak.",
                })

        # 3) Kullanılmayan abonelik
        if is_unused(item["idle_days"]):
            yearly_saving = item["monthly_try"] * 12
            insights.append({
                "level": "danger",
                "message": f"{name} aboneliğini {item['idle_days']} gündür kullanmıyorsun. "
                           f"İptal edersen yılda {yearly_saving:.0f} TL tasarruf edersin.",
            })

        # 4) Az kullanılıyor ama pahalı
        elif 0 < item["uses_30"] <= 2:
            per_use = cost_per_use(item["monthly_try"], item["uses_30"])
            insights.append({
                "level": "info",
                "message": f"{name} aboneliğini son 30 günde {item['uses_30']} kez kullandın, "
                           f"kullanım başına {per_use:.2f} TL ödüyorsun.",
            })

        # 5) Son 1 yıldaki zamlar
        recent = [c for c in item["price_changes"] if (today - c[2]).days <= 365 and c[1] > c[0]]
        if recent:
            first_price = recent[0][0]
            last_price = recent[-1][1]
            increase = (last_price - first_price) / first_price * 100
            insights.append({
                "level": "info",
                "message": f"{name} son 1 yılda {len(recent)} kez zam yaptı "
                           f"({first_price:.2f} → {last_price:.2f}, %{increase:.0f} artış).",
            })

    if not insights:
        insights.append({"level": "success", "message": "Her şey yolunda, gereksiz abonelik yok. 🎉"})

    return insights
