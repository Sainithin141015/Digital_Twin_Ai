import enum
from datetime import date as date_type

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Date,
    DateTime,
    ForeignKey,
    Enum as SAEnum,
)
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.user import utcnow


class TransactionType(str, enum.Enum):
    income = "income"
    expense = "expense"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    type = Column(SAEnum(TransactionType), nullable=False)
    category = Column(String(80), nullable=False)   # e.g. "salary", "rent", "food", "transport"
    amount = Column(Float, nullable=False)
    date = Column(Date, nullable=False, default=date_type.today, index=True)
    note = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    user = relationship("User")


class SavingsGoal(Base):
    __tablename__ = "savings_goals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(120), nullable=False)
    target_amount = Column(Float, nullable=False)
    target_date = Column(Date, nullable=True)
    current_amount = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    user = relationship("User")


class Forecast(Base):
    """
    Stored output of the forecasting engine, one row per (user, month).
    Kept so the dashboard/chatbot can read past projections without
    recomputing, and so we can later compare 'predicted vs actual'.
    """
    __tablename__ = "forecasts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    month = Column(Date, nullable=False)  # stored as first-of-month
    projected_income = Column(Float, nullable=False)
    projected_expense = Column(Float, nullable=False)
    projected_savings = Column(Float, nullable=False)
    model_version = Column(String(50), default="moving_average_v1")
    created_at = Column(DateTime(timezone=True), default=utcnow)

    user = relationship("User")
