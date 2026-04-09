"""LedgerBackend protocol — swap DuckDB for Postgres without changing consumers."""
from typing import Protocol

from .events import LeaseEvent


class LedgerBackend(Protocol):
    """Interface for event ledger storage backends."""

    def append(self, event: LeaseEvent) -> None:
        """Append a signed event. Must reject duplicate event_ids."""
        ...

    def get_history(self, lease_id: str) -> list[LeaseEvent]:
        """Return all events for a lease, ordered by timestamp ASC."""
        ...

    def get_latest_hash(self, lease_id: str) -> str | None:
        """Return the SHA-256 hash of the most recent event, or None if empty."""
        ...

    def close(self) -> None:
        """Release resources."""
        ...
