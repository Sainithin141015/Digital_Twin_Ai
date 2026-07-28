# FinLife AI — Module 1: Personal Data Collection & Profile Management

## What's included
- FastAPI app with JWT auth (register/login)
- PostgreSQL models: `users`, `profiles`, `activity_log`
- `activity_log` is a **shared event feed** — every future module (finance,
  study, habits, simulation, chat) will write into this same table, so the
  system has one unified "behavioral history" to draw insights from later.

## Setup

1. Install PostgreSQL and create a database:
   ```bash
   createdb finlife_db
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. (Optional) Set environment variables, or edit the defaults in
   `app/core/config.py`:
   ```bash
   export DATABASE_URL="postgresql+psycopg2://postgres:postgres@localhost:5432/finlife_db"
   export SECRET_KEY="something-long-and-random"
   ```

4. Run the server:
   ```bash
   uvicorn app.main:app --reload
   ```

5. Open the interactive API docs at http://localhost:8000/docs

## Endpoints

| Method | Path              | Description                          |
|--------|-------------------|--------------------------------------|
| POST   | /auth/register     | Create a new user (auto-creates a profile row) |
| POST   | /auth/login        | Get a JWT access token (form fields: username=email, password) |
| GET    | /profile/me         | View your profile                    |
| PUT    | /profile/me         | Update age/occupation/goals/preferences |
| GET    | /profile/activity   | View your full activity history      |

## Tested flow (verified working)
```bash
curl -X POST http://localhost:8000/auth/register -H "Content-Type: application/json" \
  -d '{"name":"Aditi Sharma","email":"aditi@example.com","password":"securepass123"}'

curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=aditi@example.com&password=securepass123"

# copy the access_token from the response, then:
curl http://localhost:8000/profile/me -H "Authorization: Bearer <TOKEN>"
```

## Design notes for what comes next
- `app/api/deps.py` has `get_current_user` (reuse this in every future router)
  and `log_activity()` (call this from every module so all behavior data
  flows into one place).

---

# Module 2: Financial Analysis & Forecasting Engine

## What's included
- `app/models/finance.py` — `transactions`, `savings_goals`, `forecasts` tables
- `app/schemas/finance.py` — request/response shapes
- `app/services/finance.py` — the actual analysis logic (monthly summaries,
  moving-average forecasting), kept separate from routes so Module 5
  (Simulation Engine) can reuse these same functions later
- `app/api/finance.py` — endpoints, all reusing Module 1's `get_current_user`
  and `log_activity`

## How it attaches to Module 1
- Every finance table has a `user_id` foreign key into Module 1's `users` table,
  exactly like `profiles` does.
- Every finance action (add transaction, create goal, run forecast, run
  simulation) calls the same `log_activity()` helper from Module 1, writing
  into the same `activity_log` table — so `GET /profile/activity` now shows
  a combined feed across both modules.
- `app/main.py` just adds one line (`app.include_router(finance_api.router)`)
  and imports the new models so `create_all` picks up the new tables.

## Endpoints

| Method | Path                     | Description |
|--------|--------------------------|--------------|
| POST   | /finance/transactions     | Log an income or expense |
| GET    | /finance/transactions     | List transactions (optional `?month=YYYY-MM`) |
| DELETE | /finance/transactions/{id}| Delete a transaction |
| POST   | /finance/goals            | Create a savings goal |
| GET    | /finance/goals            | List savings goals |
| GET    | /finance/summary/{month}  | Income/expense/savings breakdown for one month (YYYY-MM) |
| GET    | /finance/history          | Summary for every month with data |
| GET    | /finance/forecast         | Moving-average projection for the next N months (persisted) |
| POST   | /finance/simulate         | "What if" scenario — same forecast logic with adjusted income/expense, NOT persisted |

## Forecasting approach
Starts deliberately simple: average of the last 3 months' actual
income/expense, projected forward. This is intentional — a moving average is
easy to reason about and easy to validate, and the output shape
(`{month, projected_income, projected_expense, projected_savings}`) is stable,
so swapping in a more sophisticated model (e.g. statsmodels ARIMA or Prophet)
later is a change confined to `app/services/finance.py` — no caller needs to change.

## Tested flow (verified working end-to-end against real PostgreSQL)
```bash
# Add a transaction
curl -X POST http://localhost:8000/finance/transactions \
  -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" \
  -d '{"type":"income","category":"salary","amount":40000,"date":"2026-07-05"}'

# See monthly summary
curl http://localhost:8000/finance/summary/2026-07 -H "Authorization: Bearer <TOKEN>"

# Generate a 6-month forecast
curl "http://localhost:8000/finance/forecast?months_ahead=6" -H "Authorization: Bearer <TOKEN>"

# Run a what-if scenario (raise + expense cut), without saving it as a real forecast
curl -X POST http://localhost:8000/finance/simulate \
  -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" \
  -d '{"extra_monthly_income":5000,"extra_monthly_expense":-2000,"months_ahead":3}'
```

## A bug worth knowing about (Pydantic gotcha)
If a Pydantic field is named the same as its type (e.g. `date: Optional[date] = None`),
Pydantic v2 can fail to resolve the type correctly because the field name shadows
the imported type inside the class namespace. Fix: alias the import, e.g.
`from datetime import date as date_` and annotate as `date: Optional[date_]`.
This bit us in `TransactionCreate`/`TransactionOut`/`ForecastOut` — now fixed.

## What's next
Module 3 (Study & Productivity Intelligence) will follow the exact same
pattern: new models linked by `user_id`, a `services/study.py` for the
analysis logic, and routes that call `log_activity()` — all attaching to
this same foundation.
