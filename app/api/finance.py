from datetime import date as date_type

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.models.finance import Transaction, SavingsGoal, TransactionType
from app.schemas.finance import (
    TransactionCreate,
    TransactionOut,
    SavingsGoalCreate,
    SavingsGoalOut,
    MonthlySummary,
    ForecastOut,
    SimulationRequest,
)
from app.api.deps import get_current_user, log_activity
from app.services import finance as finance_service

router = APIRouter(prefix="/finance", tags=["finance"])


# ---------- Transactions ----------

@router.post("/transactions", response_model=TransactionOut, status_code=201)
def create_transaction(
    txn_in: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    txn = Transaction(
        user_id=current_user.id,
        type=TransactionType(txn_in.type),
        category=txn_in.category,
        amount=txn_in.amount,
        date=txn_in.date or date_type.today(),
        note=txn_in.note,
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)

    log_activity(db, current_user.id, "finance", "transaction_created", {
        "type": txn.type.value, "category": txn.category, "amount": txn.amount,
    })
    return txn


@router.get("/transactions", response_model=list[TransactionOut])
def list_transactions(
    month: str | None = Query(None, description="Filter by 'YYYY-MM'"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Transaction).filter(Transaction.user_id == current_user.id)
    if month:
        year, mon = map(int, month.split("-"))
        start = date_type(year, mon, 1)
        end = date_type(year + 1, 1, 1) if mon == 12 else date_type(year, mon + 1, 1)
        q = q.filter(Transaction.date >= start, Transaction.date < end)
    return q.order_by(Transaction.date.desc()).all()


@router.delete("/transactions/{txn_id}", status_code=204)
def delete_transaction(
    txn_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    txn = db.query(Transaction).filter(
        Transaction.id == txn_id, Transaction.user_id == current_user.id
    ).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    db.delete(txn)
    db.commit()
    log_activity(db, current_user.id, "finance", "transaction_deleted", {"id": txn_id})


# ---------- Savings goals ----------

@router.post("/goals", response_model=SavingsGoalOut, status_code=201)
def create_goal(
    goal_in: SavingsGoalCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    goal = SavingsGoal(user_id=current_user.id, **goal_in.model_dump())
    db.add(goal)
    db.commit()
    db.refresh(goal)
    log_activity(db, current_user.id, "finance", "goal_created", {"name": goal.name})
    return goal


@router.get("/goals", response_model=list[SavingsGoalOut])
def list_goals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(SavingsGoal).filter(SavingsGoal.user_id == current_user.id).all()


# ---------- Analysis & forecasting ----------

@router.get("/summary/{month}", response_model=MonthlySummary)
def monthly_summary(
    month: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """month format: YYYY-MM, e.g. 2026-07"""
    return finance_service.get_monthly_summary(db, current_user.id, month)


@router.get("/history", response_model=list[MonthlySummary])
def monthly_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return finance_service.get_monthly_history(db, current_user.id)


@router.get("/forecast", response_model=list[ForecastOut])
def forecast(
    months_ahead: int = 6,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    results = finance_service.generate_forecast(
        db, current_user.id, months_ahead=months_ahead, persist=True
    )
    log_activity(db, current_user.id, "finance", "forecast_generated", {"months_ahead": months_ahead})
    return results


@router.post("/simulate", response_model=list[ForecastOut])
def simulate(
    sim_in: SimulationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    'What if' scenario: re-runs the forecast with adjusted income/expense,
    WITHOUT persisting to the forecasts table (this is hypothetical, not
    a real prediction to track against). Module 5 will build on this.
    """
    results = finance_service.generate_forecast(
        db,
        current_user.id,
        months_ahead=sim_in.months_ahead,
        extra_monthly_income=sim_in.extra_monthly_income,
        extra_monthly_expense=sim_in.extra_monthly_expense,
        persist=False,
    )
    log_activity(db, current_user.id, "finance", "simulation_run", sim_in.model_dump())
    return results
