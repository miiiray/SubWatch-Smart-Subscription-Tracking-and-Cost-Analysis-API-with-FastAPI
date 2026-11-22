# SubWatch — Smart Subscription Tracking and Cost Analysis API with FastAPI

SubWatch is a FastAPI project that lets users track all their subscriptions (Netflix, Spotify,
iCloud, etc.) in one place. It reminds users of upcoming renewals, calculates monthly and yearly
costs, and detects subscriptions that are no longer being used. It includes a full authentication
system, so each user can **only see their own data**.

## Tech Stack
- **FastAPI** — backend / REST API
- **SQLModel + SQLite** — database
- **HTML + CSS + JavaScript** — web interface
- **Frankfurter API** — live exchange rates (USD/EUR → TRY)

## Installation
```bash
git clone https://github.com/miiiray/SubWatch-Smart-Subscription-Tracking-and-Cost-Analysis-API-with-FastAPI.git
cd SubWatch-Smart-Subscription-Tracking-and-Cost-Analysis-API-with-FastAPI
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Running the App
```bash
python seed.py          # loads sample data (resets the database!)
fastapi dev main.py     # starts the server
```
- Web app: http://127.0.0.1:8000
- API docs (Swagger UI): http://127.0.0.1:8000/docs

### Demo Accounts
| User | Email | Password |
|---|---|---|
| Miray Şahin | miray@test.com | miray123 |
| Alp Eren Sarı | alp@test.com | alp123 |
| Enes Meriç Tükenmez | enes@test.com | enes123 |

## Architecture
```
Browser (static/)  →  Routers (routers/)  →  Security (security.py)
                                          →  Services (services/)  →  Models (models.py)  →  SQLite
                                                    └──► Frankfurter API (exchange rates)
```

| Layer | Folder / File | Responsibility |
|---|---|---|
| Router | `routers/` | Receives HTTP requests and returns responses |
| Security | `security.py` | Password hashing, token creation, identifying the current user |
| Service | `services/` | Business logic: renewal dates, costs, usage analysis, smart insights |
| Model | `models.py` | Database tables and request/response schemas |
| Database | `database.py` | SQLite connection and sessions |

## Authentication
- Passwords are hashed with **PBKDF2-SHA256 + salt** (plain passwords are never stored).
- On login, a random **token** is generated and stored in the `AuthToken` table (valid for 7 days).
- Every request sends the `Authorization: Bearer <token>` header; the token is deleted on logout.
- If a user tries to access another user's subscription, the API returns **404**.

## API Endpoints
| Method | Path | Description |
|---|---|---|
| POST | /auth/register | Register a new user |
| POST | /auth/login | Log in (returns a token) |
| POST | /auth/logout | Log out |
| GET | /auth/me | Get the current user |
| POST | /subscriptions | Add a subscription |
| GET | /subscriptions?category= | List my subscriptions |
| GET | /subscriptions/{id} | Get subscription details |
| PATCH | /subscriptions/{id} | Update (price changes are saved to price history) |
| DELETE | /subscriptions/{id} | Cancel a subscription |
| POST | /subscriptions/{id}/usage | Log a usage ("I used it today") |
| GET | /subscriptions/{id}/price-history | Price change history |
| GET | /me/summary | Monthly/yearly totals, budget status, category breakdown |
| GET | /me/upcoming?days=7 | Upcoming payments |
| GET | /me/unused?threshold=60 | Unused subscriptions |
| GET | /me/insights | Smart insights |
| GET | /rates | Live exchange rates |

## Smart Insights (Rule-Based)
1. Has the monthly budget been exceeded?
2. Does a free trial end within 3 days?
3. Is there a subscription unused for 60+ days? → yearly savings estimate
4. Was a subscription used only 1–2 times in the last 30 days? → cost per use
5. Which services raised their prices in the last year?

## Project Structure
```
subwatch/
├── main.py              # app entry point
├── database.py          # SQLite connection
├── models.py            # tables and schemas
├── security.py          # hashing, tokens, current user
├── seed.py              # sample data
├── routers/
│   ├── auth.py          # register, login, logout, me
│   ├── subscriptions.py # subscription CRUD, usage, price history
│   └── insights.py      # summary, upcoming, unused, insights
├── services/
│   ├── renewal_service.py
│   ├── cost_service.py
│   ├── usage_service.py
│   └── currency_service.py
└── static/
    ├── login.html / login.js   # login & register page
    ├── index.html / app.js     # dashboard
    └── style.css
```

## Team
Miray Şahin · Alp Eren Sarı · Enes Meriç Tükenmez
