"""DuckDB implementation of LedgerBackend."""
import json
from datetime import datetime, timezone

import duckdb

from .events import EventType, LeaseEvent
from .merkle import hash_event


class DuckDBLedger:
    """Append-only event ledger backed by DuckDB."""

    def __init__(self, db_path: str = "novatex.db"):
        self._con = duckdb.connect(db_path)
        self._con.execute("""
            CREATE TABLE IF NOT EXISTS ledger (
                event_id VARCHAR PRIMARY KEY,
                lease_id VARCHAR NOT NULL,
                event_type VARCHAR NOT NULL,
                ts TIMESTAMPTZ NOT NULL,
                originator VARCHAR NOT NULL,
                payload JSON NOT NULL,
                prev_hash VARCHAR,
                signature VARCHAR,
                public_key VARCHAR
            )
        """)

    def append(self, event: LeaseEvent) -> None:
        """Append a signed event. Raises on duplicate event_id."""
        self._con.execute(
            """INSERT INTO ledger
               (event_id, lease_id, event_type, ts, originator,
                payload, prev_hash, signature, public_key)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                event.event_id,
                event.lease_id,
                event.event_type.value,
                event.timestamp,
                event.originator,
                json.dumps(event.payload),
                event.prev_hash,
                event.signature,
                event.public_key,
            ],
        )

    def get_history(self, lease_id: str) -> list[LeaseEvent]:
        """Return all events for a lease, chronologically."""
        rows = self._con.execute(
            """SELECT event_id, lease_id, event_type, ts, originator,
                      payload, prev_hash, signature, public_key
               FROM ledger
               WHERE lease_id = ?
               ORDER BY ts ASC, event_id ASC""",
            [lease_id],
        ).fetchall()
        return [self._row_to_event(row) for row in rows]

    def get_latest_hash(self, lease_id: str) -> str | None:
        """Return hash of the most recent event for a lease."""
        history = self.get_history(lease_id)
        if not history:
            return None
        return hash_event(history[-1])

    def close(self) -> None:
        """Close the DuckDB connection."""
        self._con.close()

    @staticmethod
    def _row_to_event(row: tuple) -> LeaseEvent:
        (event_id, lease_id, event_type, ts, originator,
         payload, prev_hash, signature, public_key) = row
        # DuckDB returns datetime objects; ensure UTC
        if isinstance(ts, datetime):
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            else:
                ts = ts.astimezone(timezone.utc)
        # DuckDB may return payload as str or dict
        if isinstance(payload, str):
            payload = json.loads(payload)
        return LeaseEvent(
            event_id=event_id,
            lease_id=lease_id,
            event_type=EventType(event_type),
            timestamp=ts,
            originator=originator,
            payload=payload,
            prev_hash=prev_hash,
            signature=signature,
            public_key=public_key,
        )
