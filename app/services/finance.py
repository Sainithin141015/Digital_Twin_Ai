from collections import defaultdict
from datetime import date
from typing import List

from sqlalchemy.orm import Session

from app.models.finance import Transaction, TransactionType, Forecast


def _month_key(d: date) -> str:
    return f"{d.year:04d}-{d.month:02d}"


def _first_of_month(d: date) -> date:
    return date(d.year, d.month, 1)


def get_monthly_summary(db: Session, user_id: int, month: str) -> dict:
    """
    month: 'YYYY-MM'. Returns totals + category breakdown for that month.
    """
    year, mon = map(int, month.split("-"))
    txns = (
        db.query(Transaction)
        .filter(
            Transaction.user_id == user_id,
            Transaction.date >= date(year, mon, 1),
            Transaction.date < (date(year + 1, 1, 1) if mon == 12 else date(year, mon + 1, 1)),
        )
        .all()
    )

    total_income = sum(t.amount for t in txns if t.type == TransactionType.income)
    total_expense = sum(t.amount for t in txns if t.type == TransactionType.expense)
    by_category: dict = defaultdict(float)
    for t in txns:
        if t.type == TransactionType.expense:
            by_category[t.category] += t.amount

    net_savings = total_income - total_expense
    savings_rate = (net_savings / total_income) if total_income > 0 else 0.0

    return {
        "month": month,
        "total_income": round(total_income, 2),
        "total_expense": round(total_expense, 2),
        "net_savings": round(net_savings, 2),
        "savings_rate": round(savings_rate, 4),
        "by_category": {k: round(v, 2) for k, v in by_category.items()},
    }


def get_monthly_history(db: Session, user_id: int) -> List[dict]:
    """All months that have transaction data, oldest to newest, summarized."""
    txns = db.query(Transaction).filter(Transaction.user_id == user_id).all()
    months = sorted({_month_key(t.date) for t in txns})
    return [get_monthly_summary(db, user_id, m) for m in months]


def generate_forecast(
    db: Session,
    user_id: int,
    months_ahead: int = 6,
    extra_monthly_income: float = 0.0,
    extra_monthly_expense: float = 0.0,
    lookback_months: int = 3,
    persist: bool = True,
) -> List[dict]:
    """
    Simple moving-average forecast: average of the last `lookback_months`
    of actual income/expense, projected forward `months_ahead` months,
    with optional what-if adjustments applied.

    This intentionally starts simple (moving average) rather than jumping
    straight to ARIMA/Prophet -- easy to swap the model later without
    touching any callers, since they only depend on this function's output shape.
    """
    history = get_monthly_history(db, user_id)
    recent = history[-lookback_months:] if history else []

    if recent:
        avg_income = sum(m["total_income"] for m in recent) / len(recent)
        avg_expense = sum(m["total_expense"] for m in recent) / len(recent)
    else:
        avg_income = 0.0
        avg_expense = 0.0

    projected_income = avg_income + extra_monthly_income
    projected_expense = avg_expense + extra_monthly_expense

    # anchor forecast to the month after the latest known data (or today if no data)
    if history:
        last_year, last_mon = map(int, history[-1]["month"].split("-"))
        cursor = date(last_year, last_mon, 1)
    else:
        cursor = _first_of_month(date.today())

    results = []
    for _ in range(months_ahead):
        cursor = date(cursor.year + 1, 1, 1) if cursor.month == 12 else date(cursor.year, cursor.month + 1, 1)
        projected_savings = projected_income - projected_expense
        row = {
            "month": cursor,
            "projected_income": round(projected_income, 2),
            "projected_expense": round(projected_expense, 2),
            "projected_savings": round(projected_savings, 2),
            "model_version": "moving_average_v1",
        }
        results.append(row)

        if persist:
            db.add(Forecast(user_id=user_id, **row))

    if persist:
        db.commit()

    return results
