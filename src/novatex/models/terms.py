"""Lease terms, salary sacrifice configuration."""
from datetime import date
from enum import Enum

from dateutil.relativedelta import relativedelta
from pydantic import BaseModel, computed_field


class PayFrequency(str, Enum):
    WEEKLY = "weekly"
    FORTNIGHTLY = "fortnightly"
    MONTHLY = "monthly"


class SalarySacrifice(BaseModel):
    """Salary sacrifice deduction configuration."""
    frequency: PayFrequency
    pre_tax: float
    post_tax_ecm: float

    @computed_field
    @property
    def total_deduction(self) -> float:
        return self.pre_tax + self.post_tax_ecm


class LeaseTerms(BaseModel):
    """Lease duration, residual, and payment configuration."""
    start_date: date
    term_months: int
    residual_pct: float       # ATO minimum residual percentage
    finance_rate: float       # Annual interest rate (%)
    salary_sacrifice: SalarySacrifice

    @computed_field
    @property
    def end_date(self) -> date:
        return self.start_date + relativedelta(months=self.term_months)

    def residual_amount(self, cost_base: float) -> float:
        """Calculate residual/balloon amount from vehicle cost base."""
        return round(cost_base * self.residual_pct / 100, 2)
