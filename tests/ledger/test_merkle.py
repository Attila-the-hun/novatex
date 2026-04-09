"""Tests for Merkle hash chaining."""
from datetime import datetime, timezone

from novatex.ledger.events import EventType, LeaseEvent
from novatex.ledger.merkle import hash_event, verify_chain


def _make_event(event_id: str, prev_hash: str | None = None) -> LeaseEvent:
    return LeaseEvent(
        event_id=event_id,
        lease_id="NL-2026-00001",
        event_type=EventType.CONTRACT_CREATED,
        timestamp=datetime(2026, 7, 1, 9, 0, 0, tzinfo=timezone.utc),
        originator="employee",
        payload={"seq": event_id},
        prev_hash=prev_hash,
    )


class TestMerkleChain:
    def test_hash_event_returns_hex_sha256(self):
        event = _make_event("evt-001")
        h = hash_event(event)
        assert isinstance(h, str)
        assert len(h) == 64  # SHA-256 hex digest

    def test_hash_is_deterministic(self):
        event = _make_event("evt-001")
        assert hash_event(event) == hash_event(event)

    def test_hash_changes_with_different_payload(self):
        e1 = _make_event("evt-001")
        e2 = _make_event("evt-002")
        assert hash_event(e1) != hash_event(e2)

    def test_verify_chain_valid(self):
        e1 = _make_event("evt-001", prev_hash=None)
        h1 = hash_event(e1)
        e2 = _make_event("evt-002", prev_hash=h1)
        h2 = hash_event(e2)
        e3 = _make_event("evt-003", prev_hash=h2)
        assert verify_chain([e1, e2, e3]) is True

    def test_verify_chain_detects_tampering(self):
        e1 = _make_event("evt-001", prev_hash=None)
        h1 = hash_event(e1)
        e2 = _make_event("evt-002", prev_hash=h1)
        h2 = hash_event(e2)
        e3 = _make_event("evt-003", prev_hash=h2)
        # Tamper with e2's payload
        e2.payload["seq"] = "TAMPERED"
        assert verify_chain([e1, e2, e3]) is False

    def test_verify_chain_single_event(self):
        e1 = _make_event("evt-001", prev_hash=None)
        assert verify_chain([e1]) is True

    def test_verify_chain_empty(self):
        assert verify_chain([]) is True

    def test_verify_chain_broken_first_link(self):
        """First event must have prev_hash=None."""
        e1 = _make_event("evt-001", prev_hash="bogus")
        assert verify_chain([e1]) is False
