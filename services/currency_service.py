"""
currency_service.py — Canlı döviz kuru (dış API: Frankfurter, ücretsiz, anahtar istemez).

İnternet yoksa ya da API cevap vermezse yaklaşık sabit kurlar kullanılır,
böylece uygulama asla çökmez.
"""
import time

import httpx

API_URL = "https://api.frankfurter.app/latest"
FALLBACK_RATES = {"TRY": 1.0, "USD": 42.0, "EUR": 49.0}  # yaklaşık değerler (yedek)
CACHE_SECONDS = 3600  # kuru 1 saat hafızada tut, her istekte API'ye gitme

_cache = {"rates": None, "time": 0.0}


def get_rates() -> dict:
    """{"rates": {"TRY": 1, "USD": ..., "EUR": ...}, "source": "live" | "fallback"}"""
    if _cache["rates"] and time.time() - _cache["time"] < CACHE_SECONDS:
        return {"rates": _cache["rates"], "source": "live"}

    try:
        rates = {"TRY": 1.0}
        for code in ("USD", "EUR"):
            response = httpx.get(
                API_URL,
                params={"from": code, "to": "TRY"},
                timeout=5,
                follow_redirects=True,
            )
            response.raise_for_status()
            rates[code] = response.json()["rates"]["TRY"]

        _cache["rates"] = rates
        _cache["time"] = time.time()
        return {"rates": rates, "source": "live"}

    except Exception:
        return {"rates": FALLBACK_RATES, "source": "fallback"}
