from datetime import date as date_
from typing import Optional, Literal

from pydantic import BaseModel, ConfigDict, Field


class TransactionCreate(BaseModel):
    type: Literal["income", "expense"]
    category: str
    amount: float = Field(gt=0)
    date: Optional[date_] = None
    note: Optional[str] = None


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    category: str
    amount: float
    date: date_
    note: Optional[str]


class SavingsGoalCreate(BaseModel):
    name: str
    target_amount: float = Field(gt=0)
    target_date: Optional[date_] = None
    current_amount: float = 0.0


class SavingsGoalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    target_amount: float
    target_date: Optional[date_]
    current_amount: float


class MonthlySummary(BaseModel):
    month: str  # "YYYY-MM"
    total_income: float
    total_expense: float
    net_savings: float
    savings_rate: float  # net_savings / total_income, 0 if no income
    by_category: dict[str, float]  # expense breakdown


class ForecastOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    month: date_
    projected_income: float
    projected_expense: float
    projected_savings: float
    model_version: str


class SimulationRequest(BaseModel):
    """
    'What if' inputs. All optional -- only supply the ones you want to change
    relative to the historical average.
    """
    extra_monthly_income: float = 0.0
    extra_monthly_expense: float = 0.0
    months_ahead: int = Field(default=6, ge=1, le=36)
