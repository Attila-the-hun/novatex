"""FBT (Fringe Benefits Tax) configuration."""
from enum import Enum
from typing import Optional

from pydantic import BaseModel, computed_field


class FBTMethod(str, Enum):
    STATUTORY = "statutory"
    OPERATING_COST = "operating_cost"
    EV_EXEMPT = "ev_exempt"


class FBTConfig(BaseModel):
    """FBT calculation configuration for a novated lease."""
    method: FBTMethod
    base_value: float              # Vehicle cost base (incl GST)
    statutory_rate: float          # Currently 0.20 (20%)
    # Operating cost method fields (optional)
    total_operating_costs: Optional[float] = None
    private_use_pct: Optional[float] = None
    employee_contributions: Optional[float] = None

    @computed_field
    @property
    def taxable_value(self) -> float:
        if self.method == FBTMethod.EV_EXEMPT:
            return 0.0
        if self.method == FBTMethod.OPERATING_COST:
            costs = self.total_operating_costs or 0.0
            private_pct = self.private_use_pct or 0.0
            contributions = self.employee_contributions or 0.0
            return max(0.0, (costs * private_pct) - contributions)
        # Statutory formula
        return self.base_value * self.statutory_rate

    @computed_field
    @property
    def ecm_contribution_required(self) -> float:
        """Post-tax contribution needed to zero out FBT via ECM."""
        return self.taxable_value
