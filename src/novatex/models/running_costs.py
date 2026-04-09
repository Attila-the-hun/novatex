"""Running cost pool — budget tracking for lease operating expenses."""
from enum import Enum

from pydantic import BaseModel, computed_field


class CostCategory(str, Enum):
    FUEL = "fuel"
    INSURANCE = "insurance"
    REGISTRATION = "registration"
    TYRES = "tyres"
    MAINTENANCE = "maintenance"
    ROADSIDE = "roadside"
    CHARGING = "charging"

    @classmethod
    def ice_defaults(cls) -> list["CostCategory"]:
        return [cls.FUEL, cls.INSURANCE, cls.REGISTRATION,
                cls.TYRES, cls.MAINTENANCE, cls.ROADSIDE]

    @classmethod
    def ev_defaults(cls) -> list["CostCategory"]:
        return [cls.CHARGING, cls.INSURANCE, cls.REGISTRATION,
                cls.TYRES, cls.MAINTENANCE, cls.ROADSIDE]


class RunningCostPool(BaseModel):
    """Monthly running cost budget and expense tracking."""
    monthly_budget: float
    categories: list[CostCategory]
    total_spent: float = 0.0

    @computed_field
    @property
    def balance(self) -> float:
        return self.monthly_budget - self.total_spent

    def record_expense(self, amount: float) -> "RunningCostPool":
        """Record an expense. Returns a new pool (immutable pattern)."""
        return self.model_copy(
            update={"total_spent": self.total_spent + amount}
        )
