"""NovatedLease — top-level aggregate model."""
from typing import Optional

from pydantic import BaseModel, computed_field

from .party import Party, PartyRole
from .vehicle import Vehicle
from .terms import LeaseTerms
from .fbt import FBTConfig
from .running_costs import RunningCostPool


class NovatedLease(BaseModel):
    """A complete novated lease agreement.

    This is the aggregate root. All other models compose into this.
    """
    lease_id: str
    parties: list[Party]
    vehicle: Vehicle
    terms: LeaseTerms
    fbt: FBTConfig
    running_costs: RunningCostPool
    legal_document_hash: Optional[str] = None

    def get_party(self, role: PartyRole) -> Optional[Party]:
        """Find a party by role. Returns None if not present."""
        for party in self.parties:
            if party.role == role:
                return party
        return None

    @computed_field
    @property
    def residual_amount(self) -> float:
        return self.terms.residual_amount(self.vehicle.cost_base)
