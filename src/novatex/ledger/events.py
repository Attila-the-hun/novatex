"""LeaseEvent model and EventType enum."""
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """All event types in the novated lease lifecycle."""
    CONTRACT_CREATED = "contract_created"
    STATE_TRANSITION = "state_transition"
    PAYROLL_CYCLE = "payroll_cycle"
    RUNNING_COST_CLAIM = "running_cost_claim"
    FBT_RECONCILIATION = "fbt_reconciliation"
    OBLIGATION_TRIGGERED = "obligation_triggered"
    OBLIGATION_ESCALATED = "obligation_escalated"
    SIGNATURE_ATTACHED = "signature_attached"
    VEHICLE_PROCURED = "vehicle_procured"
    NOVATION_TRANSFER = "novation_transfer"
    LEASE_TERMINATED = "lease_terminated"
    LEASE_MATURED = "lease_matured"


def _sort_dict(obj: Any) -> Any:
    """Recursively sort dict keys for canonical JSON."""
    if isinstance(obj, dict):
        return {k: _sort_dict(v) for k, v in sorted(obj.items())}
    if isinstance(obj, list):
        return [_sort_dict(item) for item in obj]
    return obj


class LeaseEvent(BaseModel):
    """A single immutable event in a novated lease's lifecycle.

    Every event is signed by the originating party and linked to the
    previous event's hash to form a Merkle chain.
    """
    event_id: str
    lease_id: str
    event_type: EventType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    originator: str
    payload: dict[str, Any] = Field(default_factory=dict)
    prev_hash: Optional[str] = None
    signature: Optional[str] = None
    public_key: Optional[str] = None

    def canonical_bytes(self) -> bytes:
        """Deterministic byte representation for signing.

        Excludes signature and public_key fields. Sorts all dict keys
        recursively so field insertion order doesn't affect the output.
        """
        data = {
            "event_id": self.event_id,
            "lease_id": self.lease_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "originator": self.originator,
            "payload": _sort_dict(self.payload),
            "prev_hash": self.prev_hash,
        }
        return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
