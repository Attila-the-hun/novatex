"""Tests for event model and Ed25519 signing."""
import json
from datetime import datetime, timezone

from novatex.ledger.events import EventType, LeaseEvent


class TestLeaseEvent:
    def test_create_event(self):
        event = LeaseEvent(
            event_id="evt-001",
            lease_id="NL-2026-00001",
            event_type=EventType.CONTRACT_CREATED,
            timestamp=datetime(2026, 7, 1, 9, 0, 0, tzinfo=timezone.utc),
            originator="employee",
            payload={"vehicle_make": "Tesla Model 3", "cost_base": 55000.00},
        )
        assert event.event_id == "evt-001"
        assert event.lease_id == "NL-2026-00001"
        assert event.event_type == EventType.CONTRACT_CREATED
        assert event.signature is None
        assert event.prev_hash is None

    def test_canonical_bytes_deterministic(self):
        """Same event must always produce identical bytes for signing."""
        ts = datetime(2026, 7, 1, 9, 0, 0, tzinfo=timezone.utc)
        event1 = LeaseEvent(
            event_id="evt-001",
            lease_id="NL-2026-00001",
            event_type=EventType.CONTRACT_CREATED,
            timestamp=ts,
            originator="employee",
            payload={"b_key": 2, "a_key": 1},
        )
        event2 = LeaseEvent(
            event_id="evt-001",
            lease_id="NL-2026-00001",
            event_type=EventType.CONTRACT_CREATED,
            timestamp=ts,
            originator="employee",
            payload={"a_key": 1, "b_key": 2},
        )
        assert event1.canonical_bytes() == event2.canonical_bytes()

    def test_canonical_bytes_excludes_signature(self):
        ts = datetime(2026, 7, 1, 9, 0, 0, tzinfo=timezone.utc)
        event = LeaseEvent(
            event_id="evt-001",
            lease_id="NL-2026-00001",
            event_type=EventType.CONTRACT_CREATED,
            timestamp=ts,
            originator="employee",
            payload={},
        )
        unsigned_bytes = event.canonical_bytes()
        event.signature = "fakesig"
        event.public_key = "fakepk"
        assert event.canonical_bytes() == unsigned_bytes

    def test_event_types_cover_lifecycle(self):
        expected = {
            "contract_created", "state_transition", "payroll_cycle",
            "running_cost_claim", "fbt_reconciliation",
            "obligation_triggered", "obligation_escalated",
            "signature_attached", "vehicle_procured",
            "novation_transfer", "lease_terminated", "lease_matured",
        }
        actual = {e.value for e in EventType}
        assert expected == actual


import nacl.signing
import nacl.encoding

from novatex.ledger.signing import sign_event, verify_event, generate_keypair


class TestSigning:
    def test_generate_keypair(self):
        private_hex, public_hex = generate_keypair()
        assert len(private_hex) == 64  # 32 bytes hex-encoded
        assert len(public_hex) == 64

    def test_sign_and_verify_roundtrip(self):
        private_hex, public_hex = generate_keypair()
        event = LeaseEvent(
            event_id="evt-sign-001",
            lease_id="NL-2026-00001",
            event_type=EventType.CONTRACT_CREATED,
            timestamp=datetime(2026, 7, 1, 9, 0, 0, tzinfo=timezone.utc),
            originator="employee",
            payload={"test": True},
        )
        signed = sign_event(event, private_hex)
        assert signed.signature is not None
        assert signed.public_key == public_hex
        assert verify_event(signed) is True

    def test_verify_rejects_tampered_event(self):
        private_hex, public_hex = generate_keypair()
        event = LeaseEvent(
            event_id="evt-tamper-001",
            lease_id="NL-2026-00001",
            event_type=EventType.CONTRACT_CREATED,
            timestamp=datetime(2026, 7, 1, 9, 0, 0, tzinfo=timezone.utc),
            originator="employee",
            payload={"amount": 1000},
        )
        signed = sign_event(event, private_hex)
        # Tamper with payload after signing
        signed.payload["amount"] = 9999
        assert verify_event(signed) is False

    def test_verify_rejects_missing_signature(self):
        event = LeaseEvent(
            event_id="evt-nosig-001",
            lease_id="NL-2026-00001",
            event_type=EventType.CONTRACT_CREATED,
            timestamp=datetime(2026, 7, 1, 9, 0, 0, tzinfo=timezone.utc),
            originator="employee",
            payload={},
        )
        assert verify_event(event) is False

    def test_sign_preserves_original_event(self):
        """sign_event returns a new event, does not mutate the original."""
        private_hex, _ = generate_keypair()
        event = LeaseEvent(
            event_id="evt-immut-001",
            lease_id="NL-2026-00001",
            event_type=EventType.CONTRACT_CREATED,
            timestamp=datetime(2026, 7, 1, 9, 0, 0, tzinfo=timezone.utc),
            originator="employee",
            payload={},
        )
        sign_event(event, private_hex)
        assert event.signature is None  # original unchanged
