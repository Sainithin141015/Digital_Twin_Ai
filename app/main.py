from fastapi import FastAPI

from app.core.database import Base, engine
from app.models import user, finance  # noqa: F401 -- import so tables are registered on Base
from app.api import auth, profile, finance as finance_api

app = FastAPI(title="FinLife AI", version="0.2.0")

# For a real project, use Alembic migrations instead of create_all.
# create_all is fine for development / getting things running quickly.
Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(finance_api.router)


@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "FinLife AI",
        "modules_active": ["1: Profile & Data Collection", "2: Financial Analysis & Forecasting"],
    }
