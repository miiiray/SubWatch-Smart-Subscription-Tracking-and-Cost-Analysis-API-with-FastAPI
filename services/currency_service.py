import time

import httpx

API_URL = "https://api.frankfurter.app/latest"
FALLBACK_RATES = {"TRY": 1.0, "USD": 42.0, "EUR": 49.0}
CACHE_SECONDS = 3600
FALLBACK_CACHE_SECONDS = 300  # internet yoksa 5 dakika boyunca tekrar deneme

_cache = {"rates": None, "time": 0.0, "source": "live"}


def get_rates() -> dict:
    age = time.time() - _cache["time"]
    limit = CACHE_SECONDS if _cache["source"] == "live" else FALLBACK_CACHE_SECONDS
    if _cache["rates"] and age < limit:
        return {"rates": _cache["rates"], "source": _cache["source"]}

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

        _cache.update(rates=rates, time=time.time(), source="live")
        return {"rates": rates, "source": "live"}

    except Exception:
        _cache.update(rates=FALLBACK_RATES, time=time.time(), source="fallback")
        return {"rates": FALLBACK_RATES, "source": "fallback"}