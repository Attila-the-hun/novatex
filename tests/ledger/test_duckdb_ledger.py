"""Tests for DuckDB ledger backend."""
from datetime import datetime, timezone

from novatex.ledger.events import EventType, LeaseEvent
from novatex.ledger.signing import sign_event
from novatex.ledger.merkle import hash_event
from novatex.ledger.duckdb_ledger import DuckDBLedger


def _make_signed_event(
    event_id: str,
    lease_id: str,
    private_key: str,
    prev_hash: str | None = None,
) -> LeaseEvent:
    event = LeaseEvent(
        event_id=event_id,
        lease_id=lease_id,
        event_type=EventType.CONTRACT_CREATED,
        timestamp=datetime(2026, 7, 1, 9, 0, 0, tzinfo=timezone.utc),
        originator="employee",
        payload={"test": True},
        prev_hash=prev_hash,
    )
    return sign_event(event, private_key)


class TestDuckDBLedger:
    def test_append_and_retrieve(self, duckdb_path, keypair):
        ledger = DuckDBLedger(duckdb_path)
        private_key, _ = keypair
        event = _make_signed_event("evt-001", "NL-001", private_key)

        ledger.append(event)
        history = ledger.get_history("NL-001")

        assert len(history) == 1
        assert history[0].event_id == "evt-001"
        assert history[0].signature == event.signature

    def test_get_history_returns_chronological(self, duckdb_path, keypair):
        ledger = DuckDBLedger(duckdb_path)
        private_key, _ = keypair

        e1 = _make_signed_event("evt-001", "NL-001", private_key)
        h1 = hash_event(e1)
        e2 = LeaseEvent(
            event_id="evt-002",
            lease_id="NL-001",
            event_type=EventType.PAYROLL_CYCLE,
            timestamp=datetime(2026, 8, 1, 9, 0, 0, tzinfo=timezone.utc),
            originator="employer",
            payload={"period": "2026-08"},
            prev_hash=h1,
        )
        e2 = sign_event(e2, private_key)

        ledger.append(e1)
        ledger.append(e2)
        history = ledger.get_history("NL-001")

        assert len(history) == 2
        assert history[0].event_id == "evt-001"
        assert history[1].event_id == "evt-002"
        assert history[1].prev_hash == h1

    def test_get_history_filters_by_lease(self, duckdb_path, keypair):
        ledger = DuckDBLedger(duckdb_path)
        private_key, _ = keypair

        e1 = _make_signed_event("evt-001", "NL-001", private_key)
        e2 = _make_signed_event("evt-002", "NL-002", private_key)

        ledger.append(e1)
        ledger.append(e2)

        assert len(ledger.get_history("NL-001")) == 1
        assert len(ledger.get_history("NL-002")) == 1

    def test_get_latest_hash_empty(self, duckdb_path):
        ledger = DuckDBLedger(duckdb_path)
        assert ledger.get_latest_hash("NL-001") is None

    def test_get_latest_hash_returns_last(self, duckdb_path, keypair):
        ledger = DuckDBLedger(duckdb_path)
        private_key, _ = keypair
        event = _make_signed_event("evt-001", "NL-001", private_key)
        ledger.append(event)

        latest = ledger.get_latest_hash("NL-001")
        assert latest == hash_event(event)

    def test_duplicate_event_id_rejected(self, duckdb_path, keypair):
        ledger = DuckDBLedger(duckdb_path)
        private_key, _ = keypair
        event = _make_signed_event("evt-001", "NL-001", private_key)
        ledger.append(event)

        import pytest
        with pytest.raises(Exception):
            ledger.append(event)

    def test_persistence_across_connections(self, duckdb_path, keypair):
        private_key, _ = keypair
        event = _make_signed_event("evt-001", "NL-001", private_key)

        ledger1 = DuckDBLedger(duckdb_path)
        ledger1.append(event)
        ledger1.close()

        ledger2 = DuckDBLedger(duckdb_path)
        history = ledger2.get_history("NL-001")
        assert len(history) == 1
        ledger2.close()
