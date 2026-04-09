"""ObligationTracker — manages obligation lifecycle."""
from datetime import datetime

from .definitions import Obligation, ObligationStatus


class ObligationTracker:
    """Tracks obligations across leases, finds overdue, manages completion."""

    def __init__(self) -> None:
        self._obligations: dict[str, Obligation] = {}

    def add(self, obligation: Obligation) -> None:
        """Register a new obligation."""
        self._obligations[obligation.obligation_id] = obligation

    def complete(self, obligation_id: str, at: datetime) -> None:
        """Mark an obligation as completed."""
        ob = self._obligations[obligation_id]
        self._obligations[obligation_id] = ob.complete(at)

    def escalate(self, obligation_id: str, at: datetime) -> None:
        """Mark an obligation as escalated."""
        ob = self._obligations[obligation_id]
        self._obligations[obligation_id] = ob.escalate(at)

    def find_overdue(self, now: datetime) -> list[Obligation]:
        """Return all pending obligations past their deadline."""
        return [
            ob for ob in self._obligations.values()
            if ob.is_overdue(now)
        ]

    def get_pending(self, lease_id: str) -> list[Obligation]:
        """Return all pending obligations for a lease."""
        return [
            ob for ob in self._obligations.values()
            if ob.lease_id == lease_id and ob.status == ObligationStatus.PENDING
        ]

    def get_completed(self, lease_id: str) -> list[Obligation]:
        """Return all completed obligations for a lease."""
        return [
            ob for ob in self._obligations.values()
            if ob.lease_id == lease_id and ob.status == ObligationStatus.COMPLETED
        ]

    def get_by_owner(self, lease_id: str, owner: str) -> list[Obligation]:
        """Return all obligations for a specific party on a lease."""
        return [
            ob for ob in self._obligations.values()
            if ob.lease_id == lease_id and ob.owner == owner
        ]
