"""Obligation model — deadline-tracked responsibilities per party."""
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class ObligationStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    ESCALATED = "escalated"


class Obligation(BaseModel):
    """A time-bound obligation assigned to a party."""
    obligation_id: str
    lease_id: str
    owner: str                          # party role or party_id
    description: str
    deadline: datetime
    created_at: datetime
    status: ObligationStatus = ObligationStatus.PENDING
    completed_at: Optional[datetime] = None

    def is_overdue(self, now: datetime) -> bool:
        return self.status == ObligationStatus.PENDING and now > self.deadline

    def complete(self, at: datetime) -> "Obligation":
        """Mark completed. Returns new Obligation (immutable)."""
        return self.model_copy(
            update={"status": ObligationStatus.COMPLETED, "completed_at": at}
        )

    def escalate(self, at: datetime) -> "Obligation":
        """Mark escalated. Returns new Obligation (immutable)."""
        return self.model_copy(
            update={"status": ObligationStatus.ESCALATED}
        )
