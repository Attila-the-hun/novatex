# Phase 0: Contract Kernel — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the foundational contract kernel — signed event ledger, domain models, state machine, obligation engine, YAML contract templates, and ATO reference tables — so that a novated lease can be instantiated from YAML, transitioned through lifecycle states, and have every event cryptographically signed and Merkle-chained.

**Architecture:** Event-sourced system where the lease state is a projection of an append-only event log. Each event is signed with Ed25519 by the originating party and linked to the previous event's hash (Merkle chain). DuckDB stores events with a `LedgerBackend` protocol for future Postgres swap. Build order: ledger primitives first (signing, Merkle, storage), then domain models, then state machine, then obligation engine, then YAML contract templates, then ATO reference tables.

**Tech Stack:** Python 3.14, Pydantic 2.12, DuckDB 1.4, PyNaCl (Ed25519), PyYAML, pytest

---

## File Structure

```
novatex/
  pyproject.toml                          # Package config, dependencies
  src/novatex/
    __init__.py                           # Re-exports key types
    ledger/
      __init__.py
      events.py                           # LeaseEvent model, EventType enum
      signing.py                          # Ed25519 sign/verify using PyNaCl
      merkle.py                           # Hash chaining + chain verification
      backend.py                          # LedgerBackend protocol
      duckdb_ledger.py                    # DuckDB implementation
    models/
      __init__.py
      party.py                            # Party, PartyRole enum
      vehicle.py                          # Vehicle, VehicleType enum
      terms.py                            # LeaseTerms, SalarySacrifice, ResidualConfig
      fbt.py                              # FBTConfig, FBTMethod enum, ECM
      running_costs.py                    # RunningCostPool, CostCategory enum
      lease.py                            # NovatedLease (top-level aggregate)
    engine/
      __init__.py
      states.py                           # LeaseState enum
      transitions.py                      # Transition definitions + guard conditions
      machine.py                          # StateMachine class
    obligations/
      __init__.py
      definitions.py                      # Obligation templates per transition
      tracker.py                          # ObligationTracker — deadline + escalation
    contracts/
      __init__.py
      schema.py                           # YAML schema validation
      parser.py                           # Load YAML → NovatedLease + bind legal hash
    reference/
      __init__.py
      ato_residuals.py                    # ATO minimum residual tables
      ato_fbt.py                          # FBT rates, LCT thresholds
  tests/
    conftest.py                           # Shared fixtures (keypairs, sample events, sample lease)
    ledger/
      test_signing.py
      test_merkle.py
      test_duckdb_ledger.py
    models/
      test_party.py
      test_vehicle.py
      test_terms.py
      test_fbt.py
      test_running_costs.py
      test_lease.py
    engine/
      test_states.py
      test_transitions.py
      test_machine.py
    obligations/
      test_definitions.py
      test_tracker.py
    contracts/
      test_schema.py
      test_parser.py
    reference/
      test_ato_residuals.py
      test_ato_fbt.py
```

---

## Task 1: Project Setup + Dependencies

**Files:**
- Create: `pyproject.toml`
- Create: `src/novatex/__init__.py`
- Create: `tests/conftest.py` (empty placeholder)

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "novatex"
version = "0.1.0"
description = "Novated Lease Soft Contract Platform"
requires-python = ">=3.12"
dependencies = [
    "pydantic>=2.12,<3",
    "pynacl>=1.5,<2",
    "duckdb>=1.0,<2",
    "pyyaml>=6.0,<7",
]

[project.optional-dependencies]
dev = [
    "pytest>=9.0,<10",
    "pytest-cov>=6.0,<7",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]

[tool.hatch.build.targets.wheel]
packages = ["src/novatex"]
```

- [ ] **Step 2: Create package init**

```python
# src/novatex/__init__.py
"""NovateX — Novated Lease Soft Contract Platform."""
```

- [ ] **Step 3: Create empty test conftest**

```python
# tests/conftest.py
"""Shared test fixtures for NovateX."""
```

- [ ] **Step 4: Install dependencies**

Run:
```bash
cd /Users/timothymessieh/Desktop/Machine\ Learning\ and\ Coding/novatex
pip install pynacl
pip install -e ".[dev]"
```

Expected: Clean install, no errors.

- [ ] **Step 5: Verify imports work**

Run:
```bash
python -c "import pydantic; import nacl; import duckdb; import yaml; print('all imports ok')"
```

Expected: `all imports ok`

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml src/ tests/
git commit -m "feat(phase0): project setup with pyproject.toml and dependencies"
```

---

## Task 2: Event Model + Canonical Signing Format

**Files:**
- Create: `src/novatex/ledger/__init__.py`
- Create: `src/novatex/ledger/events.py`
- Create: `tests/ledger/__init__.py`
- Create: `tests/ledger/test_signing.py`

The event model is the atomic unit of the entire system. Every mutation to a lease creates a signed event. The signing format must be deterministic — same event always produces the same bytes for signing.

- [ ] **Step 1: Create ledger package init**

```python
# src/novatex/ledger/__init__.py
"""Signed event ledger — append-only log with Ed25519 signatures and Merkle chaining."""
```

- [ ] **Step 2: Write the failing test for LeaseEvent and canonical bytes**

```python
# tests/ledger/test_signing.py
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
```

Also create test package init:
```python
# tests/ledger/__init__.py
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd /Users/timothymessieh/Desktop/Machine\ Learning\ and\ Coding/novatex && python -m pytest tests/ledger/test_signing.py -v`

Expected: FAIL — `ModuleNotFoundError: No module named 'novatex.ledger.events'`

- [ ] **Step 4: Implement events.py**

```python
# src/novatex/ledger/events.py
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
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd /Users/timothymessieh/Desktop/Machine\ Learning\ and\ Coding/novatex && python -m pytest tests/ledger/test_signing.py -v`

Expected: 4 passed

- [ ] **Step 6: Commit**

```bash
git add src/novatex/ledger/ tests/ledger/
git commit -m "feat(ledger): LeaseEvent model with canonical signing bytes and EventType enum"
```

---

## Task 3: Ed25519 Signing + Verification

**Files:**
- Create: `src/novatex/ledger/signing.py`
- Modify: `tests/ledger/test_signing.py` (add signing tests)

- [ ] **Step 1: Write failing tests for sign/verify**

Append to `tests/ledger/test_signing.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/timothymessieh/Desktop/Machine\ Learning\ and\ Coding/novatex && python -m pytest tests/ledger/test_signing.py::TestSigning -v`

Expected: FAIL — `ModuleNotFoundError: No module named 'novatex.ledger.signing'`

- [ ] **Step 3: Implement signing.py**

```python
# src/novatex/ledger/signing.py
"""Ed25519 signing and verification for lease events."""
import nacl.signing
import nacl.encoding
import nacl.exceptions

from .events import LeaseEvent


def generate_keypair() -> tuple[str, str]:
    """Generate an Ed25519 keypair. Returns (private_hex, public_hex)."""
    signing_key = nacl.signing.SigningKey.generate()
    private_hex = signing_key.encode(encoder=nacl.encoding.HexEncoder).decode("ascii")
    public_hex = (
        signing_key.verify_key.encode(encoder=nacl.encoding.HexEncoder).decode("ascii")
    )
    return private_hex, public_hex


def sign_event(event: LeaseEvent, private_key_hex: str) -> LeaseEvent:
    """Sign an event with Ed25519. Returns a NEW event with signature + public_key set."""
    signing_key = nacl.signing.SigningKey(
        private_key_hex.encode("ascii"), encoder=nacl.encoding.HexEncoder
    )
    public_hex = (
        signing_key.verify_key.encode(encoder=nacl.encoding.HexEncoder).decode("ascii")
    )
    signed = signing_key.sign(event.canonical_bytes())
    return event.model_copy(
        update={
            "signature": signed.signature.hex(),
            "public_key": public_hex,
        }
    )


def verify_event(event: LeaseEvent) -> bool:
    """Verify an event's Ed25519 signature. Returns False if missing or invalid."""
    if not event.signature or not event.public_key:
        return False
    try:
        verify_key = nacl.signing.VerifyKey(
            event.public_key.encode("ascii"), encoder=nacl.encoding.HexEncoder
        )
        verify_key.verify(
            event.canonical_bytes(), bytes.fromhex(event.signature)
        )
        return True
    except nacl.exceptions.BadSignatureError:
        return False
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/timothymessieh/Desktop/Machine\ Learning\ and\ Coding/novatex && python -m pytest tests/ledger/test_signing.py -v`

Expected: 9 passed (4 from Task 2 + 5 new)

- [ ] **Step 5: Commit**

```bash
git add src/novatex/ledger/signing.py tests/ledger/test_signing.py
git commit -m "feat(ledger): Ed25519 signing and verification with tamper detection"
```

---

## Task 4: Merkle Chain

**Files:**
- Create: `src/novatex/ledger/merkle.py`
- Create: `tests/ledger/test_merkle.py`

The Merkle chain links each event to the previous one via SHA-256 hash. This is the tamper-evidence layer — modifying any historical event breaks the chain.

- [ ] **Step 1: Write failing tests**

```python
# tests/ledger/test_merkle.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/timothymessieh/Desktop/Machine\ Learning\ and\ Coding/novatex && python -m pytest tests/ledger/test_merkle.py -v`

Expected: FAIL — `ModuleNotFoundError: No module named 'novatex.ledger.merkle'`

- [ ] **Step 3: Implement merkle.py**

```python
# src/novatex/ledger/merkle.py
"""Merkle hash chaining for tamper evidence."""
import hashlib

from .events import LeaseEvent


def hash_event(event: LeaseEvent) -> str:
    """SHA-256 hash of an event's canonical bytes. Returns hex digest."""
    return hashlib.sha256(event.canonical_bytes()).hexdigest()


def verify_chain(events: list[LeaseEvent]) -> bool:
    """Verify the Merkle chain integrity of an ordered event list.

    Rules:
    - First event must have prev_hash=None
    - Each subsequent event's prev_hash must equal hash of previous event
    """
    if not events:
        return True

    if events[0].prev_hash is not None:
        return False

    for i in range(1, len(events)):
        expected_hash = hash_event(events[i - 1])
        if events[i].prev_hash != expected_hash:
            return False

    return True
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/timothymessieh/Desktop/Machine\ Learning\ and\ Coding/novatex && python -m pytest tests/ledger/test_merkle.py -v`

Expected: 8 passed

- [ ] **Step 5: Commit**

```bash
git add src/novatex/ledger/merkle.py tests/ledger/test_merkle.py
git commit -m "feat(ledger): Merkle hash chaining with SHA-256 and chain verification"
```

---

## Task 5: LedgerBackend Protocol + DuckDB Implementation

**Files:**
- Create: `src/novatex/ledger/backend.py`
- Create: `src/novatex/ledger/duckdb_ledger.py`
- Create: `tests/ledger/test_duckdb_ledger.py`
- Modify: `tests/conftest.py` (add shared fixtures)

- [ ] **Step 1: Write shared fixtures in conftest.py**

```python
# tests/conftest.py
"""Shared test fixtures for NovateX."""
import os
import pytest

from novatex.ledger.signing import generate_keypair


@pytest.fixture
def keypair():
    """A fresh Ed25519 keypair for testing."""
    return generate_keypair()


@pytest.fixture
def duckdb_path(tmp_path):
    """Temporary DuckDB file path, auto-cleaned."""
    return str(tmp_path / "test_ledger.db")
```

- [ ] **Step 2: Write failing tests for DuckDB ledger**

```python
# tests/ledger/test_duckdb_ledger.py
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
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd /Users/timothymessieh/Desktop/Machine\ Learning\ and\ Coding/novatex && python -m pytest tests/ledger/test_duckdb_ledger.py -v`

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 4: Implement backend.py (protocol)**

```python
# src/novatex/ledger/backend.py
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
```

- [ ] **Step 5: Implement duckdb_ledger.py**

```python
# src/novatex/ledger/duckdb_ledger.py
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
        if isinstance(ts, datetime) and ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
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
```

- [ ] **Step 6: Run test to verify it passes**

Run: `cd /Users/timothymessieh/Desktop/Machine\ Learning\ and\ Coding/novatex && python -m pytest tests/ledger/test_duckdb_ledger.py -v`

Expected: 7 passed

- [ ] **Step 7: Run all ledger tests together**

Run: `cd /Users/timothymessieh/Desktop/Machine\ Learning\ and\ Coding/novatex && python -m pytest tests/ledger/ -v`

Expected: 21 passed (9 signing + 8 merkle + 7 duckdb — note: counts may differ slightly, 3 test files)

- [ ] **Step 8: Commit**

```bash
git add src/novatex/ledger/backend.py src/novatex/ledger/duckdb_ledger.py tests/ledger/test_duckdb_ledger.py tests/conftest.py
git commit -m "feat(ledger): DuckDB backend with LedgerBackend protocol, persistence tests"
```

---

## Task 6: Domain Models — Party + Vehicle

**Files:**
- Create: `src/novatex/models/__init__.py`
- Create: `src/novatex/models/party.py`
- Create: `src/novatex/models/vehicle.py`
- Create: `tests/models/__init__.py`
- Create: `tests/models/test_party.py`
- Create: `tests/models/test_vehicle.py`

- [ ] **Step 1: Write failing tests for Party**

```python
# tests/models/__init__.py
```

```python
# tests/models/test_party.py
"""Tests for Party model."""
from novatex.models.party import Party, PartyRole


class TestParty:
    def test_create_employee(self):
        p = Party(
            party_id="EMP-001",
            role=PartyRole.EMPLOYEE,
            name="Jane Smith",
            abn=None,
        )
        assert p.role == PartyRole.EMPLOYEE
        assert p.abn is None

    def test_create_employer(self):
        p = Party(
            party_id="ORG-001",
            role=PartyRole.EMPLOYER,
            name="Acme Corp",
            abn="12 345 678 901",
        )
        assert p.role == PartyRole.EMPLOYER
        assert p.abn == "12 345 678 901"

    def test_create_financier(self):
        p = Party(
            party_id="FIN-001",
            role=PartyRole.FINANCIER,
            name="SG Fleet Finance",
            abn="98 765 432 109",
        )
        assert p.role == PartyRole.FINANCIER

    def test_create_fleet_manager(self):
        p = Party(
            party_id="FLT-001",
            role=PartyRole.FLEET_MANAGER,
            name="SG Fleet Mgmt",
            abn="11 222 333 444",
        )
        assert p.role == PartyRole.FLEET_MANAGER

    def test_all_roles_exist(self):
        expected = {"employee", "employer", "financier", "fleet_manager"}
        actual = {r.value for r in PartyRole}
        assert expected == actual
```

- [ ] **Step 2: Write failing tests for Vehicle**

```python
# tests/models/test_vehicle.py
"""Tests for Vehicle model."""
import pytest
from novatex.models.vehicle import Vehicle, VehicleType


class TestVehicle:
    def test_create_ev(self):
        v = Vehicle(
            make="Tesla",
            model="Model 3",
            year=2026,
            vehicle_type=VehicleType.BEV,
            cost_base=55000.00,
            gst_credit=5000.00,
        )
        assert v.vehicle_type == VehicleType.BEV
        assert v.is_ev is True
        assert v.cost_ex_gst == 50000.00

    def test_create_ice(self):
        v = Vehicle(
            make="Toyota",
            model="Camry",
            year=2026,
            vehicle_type=VehicleType.ICE,
            cost_base=42000.00,
            gst_credit=3818.18,
        )
        assert v.is_ev is False

    def test_vehicle_types(self):
        expected = {"bev", "phev", "fcev", "ice"}
        actual = {t.value for t in VehicleType}
        assert expected == actual

    def test_fbt_exempt_ev_under_threshold(self):
        v = Vehicle(
            make="Tesla", model="Model 3", year=2026,
            vehicle_type=VehicleType.BEV,
            cost_base=55000.00, gst_credit=5000.00,
        )
        assert v.is_fbt_exempt(lct_threshold=89332.00) is True

    def test_fbt_not_exempt_ev_over_threshold(self):
        v = Vehicle(
            make="Tesla", model="Model S Plaid", year=2026,
            vehicle_type=VehicleType.BEV,
            cost_base=150000.00, gst_credit=13636.36,
        )
        assert v.is_fbt_exempt(lct_threshold=89332.00) is False

    def test_fbt_not_exempt_ice(self):
        v = Vehicle(
            make="Toyota", model="Camry", year=2026,
            vehicle_type=VehicleType.ICE,
            cost_base=42000.00, gst_credit=3818.18,
        )
        assert v.is_fbt_exempt(lct_threshold=89332.00) is False
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd /Users/timothymessieh/Desktop/Machine\ Learning\ and\ Coding/novatex && python -m pytest tests/models/ -v`

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 4: Implement party.py**

```python
# src/novatex/models/__init__.py
"""Domain models for novated lease contracts."""
```

```python
# src/novatex/models/party.py
"""Party model — participants in a novated lease."""
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class PartyRole(str, Enum):
    EMPLOYEE = "employee"
    EMPLOYER = "employer"
    FINANCIER = "financier"
    FLEET_MANAGER = "fleet_manager"


class Party(BaseModel):
    """A participant in a novated lease agreement."""
    party_id: str
    role: PartyRole
    name: str
    abn: Optional[str] = None
```

- [ ] **Step 5: Implement vehicle.py**

```python
# src/novatex/models/vehicle.py
"""Vehicle model — the leased asset."""
from enum import Enum

from pydantic import BaseModel, computed_field


class VehicleType(str, Enum):
    BEV = "bev"      # Battery Electric Vehicle
    PHEV = "phev"    # Plug-in Hybrid
    FCEV = "fcev"    # Fuel Cell Electric Vehicle
    ICE = "ice"      # Internal Combustion Engine


class Vehicle(BaseModel):
    """The vehicle under novated lease."""
    make: str
    model: str
    year: int
    vehicle_type: VehicleType
    cost_base: float       # Including GST
    gst_credit: float      # GST claimed by employer

    @computed_field
    @property
    def is_ev(self) -> bool:
        return self.vehicle_type in (VehicleType.BEV, VehicleType.PHEV, VehicleType.FCEV)

    @computed_field
    @property
    def cost_ex_gst(self) -> float:
        return self.cost_base - self.gst_credit

    def is_fbt_exempt(self, lct_threshold: float) -> bool:
        """EV FBT exemption: EV + cost below LCT threshold for fuel-efficient vehicles."""
        return self.is_ev and self.cost_base <= lct_threshold
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd /Users/timothymessieh/Desktop/Machine\ Learning\ and\ Coding/novatex && python -m pytest tests/models/ -v`

Expected: 11 passed (5 party + 6 vehicle)

- [ ] **Step 7: Commit**

```bash
git add src/novatex/models/ tests/models/
git commit -m "feat(models): Party and Vehicle domain models with FBT exemption logic"
```

---

## Task 7: Domain Models — LeaseTerms + SalarySacrifice

**Files:**
- Create: `src/novatex/models/terms.py`
- Create: `tests/models/test_terms.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/models/test_terms.py
"""Tests for LeaseTerms and SalarySacrifice models."""
from datetime import date

import pytest
from novatex.models.terms import LeaseTerms, SalarySacrifice, PayFrequency


class TestSalarySacrifice:
    def test_create(self):
        ss = SalarySacrifice(
            frequency=PayFrequency.FORTNIGHTLY,
            pre_tax=612.00,
            post_tax_ecm=183.00,
        )
        assert ss.total_deduction == 795.00

    def test_monthly(self):
        ss = SalarySacrifice(
            frequency=PayFrequency.MONTHLY,
            pre_tax=1326.00,
            post_tax_ecm=396.50,
        )
        assert ss.total_deduction == 1722.50


class TestLeaseTerms:
    def test_create(self):
        terms = LeaseTerms(
            start_date=date(2026, 7, 1),
            term_months=36,
            residual_pct=46.88,
            finance_rate=6.49,
            salary_sacrifice=SalarySacrifice(
                frequency=PayFrequency.FORTNIGHTLY,
                pre_tax=612.00,
                post_tax_ecm=183.00,
            ),
        )
        assert terms.end_date == date(2029, 7, 1)
        assert terms.residual_pct == 46.88

    def test_residual_amount(self):
        terms = LeaseTerms(
            start_date=date(2026, 7, 1),
            term_months=36,
            residual_pct=46.88,
            finance_rate=6.49,
            salary_sacrifice=SalarySacrifice(
                frequency=PayFrequency.FORTNIGHTLY,
                pre_tax=612.00,
                post_tax_ecm=183.00,
            ),
        )
        # residual_amount needs vehicle cost_base, so it's a method
        assert terms.residual_amount(cost_base=55000.00) == pytest.approx(25784.00)

    def test_end_date_60_months(self):
        terms = LeaseTerms(
            start_date=date(2026, 1, 1),
            term_months=60,
            residual_pct=28.13,
            finance_rate=5.99,
            salary_sacrifice=SalarySacrifice(
                frequency=PayFrequency.MONTHLY,
                pre_tax=900.00,
                post_tax_ecm=270.00,
            ),
        )
        assert terms.end_date == date(2031, 1, 1)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/timothymessieh/Desktop/Machine\ Learning\ and\ Coding/novatex && python -m pytest tests/models/test_terms.py -v`

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement terms.py**

```python
# src/novatex/models/terms.py
"""Lease terms, salary sacrifice configuration."""
from datetime import date
from enum import Enum

from dateutil.relativedelta import relativedelta
from pydantic import BaseModel, computed_field


class PayFrequency(str, Enum):
    WEEKLY = "weekly"
    FORTNIGHTLY = "fortnightly"
    MONTHLY = "monthly"


class SalarySacrifice(BaseModel):
    """Salary sacrifice deduction configuration."""
    frequency: PayFrequency
    pre_tax: float
    post_tax_ecm: float

    @computed_field
    @property
    def total_deduction(self) -> float:
        return self.pre_tax + self.post_tax_ecm


class LeaseTerms(BaseModel):
    """Lease duration, residual, and payment configuration."""
    start_date: date
    term_months: int
    residual_pct: float       # ATO minimum residual percentage
    finance_rate: float       # Annual interest rate (%)
    salary_sacrifice: SalarySacrifice

    @computed_field
    @property
    def end_date(self) -> date:
        return self.start_date + relativedelta(months=self.term_months)

    def residual_amount(self, cost_base: float) -> float:
        """Calculate residual/balloon amount from vehicle cost base."""
        return round(cost_base * self.residual_pct / 100, 2)
```

**Note:** This requires `python-dateutil`. Add to pyproject.toml dependencies:

Add `"python-dateutil>=2.9,<3"` to the `dependencies` list in `pyproject.toml`, then run:
```bash
pip install python-dateutil
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/timothymessieh/Desktop/Machine\ Learning\ and\ Coding/novatex && python -m pytest tests/models/test_terms.py -v`

Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add src/novatex/models/terms.py tests/models/test_terms.py pyproject.toml
git commit -m "feat(models): LeaseTerms and SalarySacrifice with end date and residual calc"
```

---

## Task 8: Domain Models — FBT + Running Costs

**Files:**
- Create: `src/novatex/models/fbt.py`
- Create: `src/novatex/models/running_costs.py`
- Create: `tests/models/test_fbt.py`
- Create: `tests/models/test_running_costs.py`

- [ ] **Step 1: Write failing tests for FBT**

```python
# tests/models/test_fbt.py
"""Tests for FBT configuration models."""
from novatex.models.fbt import FBTConfig, FBTMethod


class TestFBTConfig:
    def test_statutory_method(self):
        fbt = FBTConfig(
            method=FBTMethod.STATUTORY,
            base_value=55000.00,
            statutory_rate=0.20,
        )
        assert fbt.taxable_value == 11000.00

    def test_ecm_zeroes_fbt(self):
        fbt = FBTConfig(
            method=FBTMethod.STATUTORY,
            base_value=55000.00,
            statutory_rate=0.20,
        )
        assert fbt.ecm_contribution_required == 11000.00

    def test_ev_exempt(self):
        fbt = FBTConfig(
            method=FBTMethod.EV_EXEMPT,
            base_value=55000.00,
            statutory_rate=0.20,
        )
        assert fbt.taxable_value == 0.0
        assert fbt.ecm_contribution_required == 0.0

    def test_operating_cost_method(self):
        fbt = FBTConfig(
            method=FBTMethod.OPERATING_COST,
            base_value=55000.00,
            statutory_rate=0.20,
            total_operating_costs=15000.00,
            private_use_pct=0.60,
            employee_contributions=9000.00,
        )
        # (15000 * 0.60) - 9000 = 0
        assert fbt.taxable_value == 0.0

    def test_methods_exist(self):
        expected = {"statutory", "operating_cost", "ev_exempt"}
        actual = {m.value for m in FBTMethod}
        assert expected == actual
```

- [ ] **Step 2: Write failing tests for RunningCosts**

```python
# tests/models/test_running_costs.py
"""Tests for RunningCostPool model."""
import pytest
from novatex.models.running_costs import RunningCostPool, CostCategory


class TestRunningCostPool:
    def test_create_pool(self):
        pool = RunningCostPool(
            monthly_budget=580.00,
            categories=[
                CostCategory.FUEL,
                CostCategory.INSURANCE,
                CostCategory.REGISTRATION,
                CostCategory.TYRES,
                CostCategory.MAINTENANCE,
                CostCategory.ROADSIDE,
            ],
        )
        assert pool.monthly_budget == 580.00
        assert len(pool.categories) == 6
        assert pool.total_spent == 0.0
        assert pool.balance == 580.00

    def test_record_expense(self):
        pool = RunningCostPool(monthly_budget=580.00, categories=[CostCategory.FUEL])
        updated = pool.record_expense(150.00)
        assert updated.total_spent == 150.00
        assert updated.balance == 430.00

    def test_ev_categories_exclude_fuel(self):
        ev_cats = CostCategory.ev_defaults()
        assert CostCategory.FUEL not in ev_cats
        assert CostCategory.CHARGING in ev_cats

    def test_all_categories(self):
        expected = {
            "fuel", "insurance", "registration", "tyres",
            "maintenance", "roadside", "charging",
        }
        actual = {c.value for c in CostCategory}
        assert expected == actual

    def test_surplus_deficit(self):
        pool = RunningCostPool(monthly_budget=580.00, categories=[CostCategory.FUEL])
        pool = pool.record_expense(600.00)
        assert pool.balance == -20.00
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd /Users/timothymessieh/Desktop/Machine\ Learning\ and\ Coding/novatex && python -m pytest tests/models/test_fbt.py tests/models/test_running_costs.py -v`

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 4: Implement fbt.py**

```python
# src/novatex/models/fbt.py
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
```

- [ ] **Step 5: Implement running_costs.py**

```python
# src/novatex/models/running_costs.py
"""Running cost pool — budget tracking for lease operating expenses."""
from enum import Enum

from pydantic import BaseModel, computed_field


class CostCategory(str, Enum):
    FUEL = "fuel"
    INSURANCE = "insurance"
    REGISTRATION = "registration"
    TYRES = "tyres"
    MAINTENANCE = "maintenance"
    ROADSIDE = "roadside"
    CHARGING = "charging"

    @classmethod
    def ice_defaults(cls) -> list["CostCategory"]:
        return [cls.FUEL, cls.INSURANCE, cls.REGISTRATION,
                cls.TYRES, cls.MAINTENANCE, cls.ROADSIDE]

    @classmethod
    def ev_defaults(cls) -> list["CostCategory"]:
        return [cls.CHARGING, cls.INSURANCE, cls.REGISTRATION,
                cls.TYRES, cls.MAINTENANCE, cls.ROADSIDE]


class RunningCostPool(BaseModel):
    """Monthly running cost budget and expense tracking."""
    monthly_budget: float
    categories: list[CostCategory]
    total_spent: float = 0.0

    @computed_field
    @property
    def balance(self) -> float:
        return self.monthly_budget - self.total_spent

    def record_expense(self, amount: float) -> "RunningCostPool":
        """Record an expense. Returns a new pool (immutable pattern)."""
        return self.model_copy(
            update={"total_spent": self.total_spent + amount}
        )
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd /Users/timothymessieh/Desktop/Machine\ Learning\ and\ Coding/novatex && python -m pytest tests/models/test_fbt.py tests/models/test_running_costs.py -v`

Expected: 10 passed (5 fbt + 5 running costs)

- [ ] **Step 7: Commit**

```bash
git add src/novatex/models/fbt.py src/novatex/models/running_costs.py tests/models/test_fbt.py tests/models/test_running_costs.py
git commit -m "feat(models): FBT config (statutory/operating/EV-exempt) and RunningCostPool"
```

---

## Task 9: Domain Models — NovatedLease (Top-Level Aggregate)

**Files:**
- Create: `src/novatex/models/lease.py`
- Create: `tests/models/test_lease.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/models/test_lease.py
"""Tests for NovatedLease aggregate model."""
from datetime import date

from novatex.models.lease import NovatedLease
from novatex.models.party import Party, PartyRole
from novatex.models.vehicle import Vehicle, VehicleType
from novatex.models.terms import LeaseTerms, SalarySacrifice, PayFrequency
from novatex.models.fbt import FBTConfig, FBTMethod
from novatex.models.running_costs import RunningCostPool, CostCategory


def _sample_lease() -> NovatedLease:
    return NovatedLease(
        lease_id="NL-2026-00001",
        parties=[
            Party(party_id="EMP-001", role=PartyRole.EMPLOYEE, name="Jane Smith"),
            Party(party_id="ORG-001", role=PartyRole.EMPLOYER, name="Acme Corp", abn="12 345 678 901"),
            Party(party_id="FIN-001", role=PartyRole.FINANCIER, name="SG Fleet Finance", abn="98 765 432 109"),
        ],
        vehicle=Vehicle(
            make="Tesla", model="Model 3", year=2026,
            vehicle_type=VehicleType.BEV,
            cost_base=55000.00, gst_credit=5000.00,
        ),
        terms=LeaseTerms(
            start_date=date(2026, 7, 1),
            term_months=36,
            residual_pct=46.88,
            finance_rate=6.49,
            salary_sacrifice=SalarySacrifice(
                frequency=PayFrequency.FORTNIGHTLY,
                pre_tax=612.00, post_tax_ecm=183.00,
            ),
        ),
        fbt=FBTConfig(
            method=FBTMethod.EV_EXEMPT,
            base_value=55000.00,
            statutory_rate=0.20,
        ),
        running_costs=RunningCostPool(
            monthly_budget=580.00,
            categories=CostCategory.ev_defaults(),
        ),
    )


class TestNovatedLease:
    def test_create(self):
        lease = _sample_lease()
        assert lease.lease_id == "NL-2026-00001"
        assert len(lease.parties) == 3

    def test_get_party_by_role(self):
        lease = _sample_lease()
        emp = lease.get_party(PartyRole.EMPLOYEE)
        assert emp is not None
        assert emp.name == "Jane Smith"

    def test_get_party_missing_role(self):
        lease = _sample_lease()
        fm = lease.get_party(PartyRole.FLEET_MANAGER)
        assert fm is None

    def test_residual_amount(self):
        lease = _sample_lease()
        assert lease.residual_amount == 25784.00

    def test_is_ev(self):
        lease = _sample_lease()
        assert lease.vehicle.is_ev is True

    def test_fbt_exempt(self):
        lease = _sample_lease()
        assert lease.fbt.taxable_value == 0.0

    def test_legal_document_hash_optional(self):
        lease = _sample_lease()
        assert lease.legal_document_hash is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/timothymessieh/Desktop/Machine\ Learning\ and\ Coding/novatex && python -m pytest tests/models/test_lease.py -v`

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement lease.py**

```python
# src/novatex/models/lease.py
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/timothymessieh/Desktop/Machine\ Learning\ and\ Coding/novatex && python -m pytest tests/models/test_lease.py -v`

Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add src/novatex/models/lease.py tests/models/test_lease.py
git commit -m "feat(models): NovatedLease aggregate with party lookup and residual calc"
```

---

## Task 10: State Machine — States + Transitions

**Files:**
- Create: `src/novatex/engine/__init__.py`
- Create: `src/novatex/engine/states.py`
- Create: `src/novatex/engine/transitions.py`
- Create: `src/novatex/engine/machine.py`
- Create: `tests/engine/__init__.py`
- Create: `tests/engine/test_machine.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/engine/__init__.py
```

```python
# tests/engine/test_machine.py
"""Tests for the lease state machine."""
import pytest

from novatex.engine.states import LeaseState
from novatex.engine.machine import StateMachine, TransitionError


class TestLeaseStates:
    def test_all_states(self):
        expected = {
            "draft", "active", "reconciliation",
            "novation_transfer", "termination",
            "maturity", "total_loss", "closed",
        }
        actual = {s.value for s in LeaseState}
        assert expected == actual


class TestStateMachine:
    def test_initial_state_is_draft(self):
        sm = StateMachine()
        assert sm.state == LeaseState.DRAFT

    def test_draft_to_active(self):
        sm = StateMachine()
        sm.transition(LeaseState.ACTIVE)
        assert sm.state == LeaseState.ACTIVE

    def test_active_to_reconciliation(self):
        sm = StateMachine(state=LeaseState.ACTIVE)
        sm.transition(LeaseState.RECONCILIATION)
        assert sm.state == LeaseState.RECONCILIATION

    def test_reconciliation_back_to_active(self):
        sm = StateMachine(state=LeaseState.RECONCILIATION)
        sm.transition(LeaseState.ACTIVE)
        assert sm.state == LeaseState.ACTIVE

    def test_active_to_maturity(self):
        sm = StateMachine(state=LeaseState.ACTIVE)
        sm.transition(LeaseState.MATURITY)
        assert sm.state == LeaseState.MATURITY

    def test_maturity_to_closed(self):
        sm = StateMachine(state=LeaseState.MATURITY)
        sm.transition(LeaseState.CLOSED)
        assert sm.state == LeaseState.CLOSED

    def test_active_to_termination(self):
        sm = StateMachine(state=LeaseState.ACTIVE)
        sm.transition(LeaseState.TERMINATION)
        assert sm.state == LeaseState.TERMINATION

    def test_termination_to_closed(self):
        sm = StateMachine(state=LeaseState.TERMINATION)
        sm.transition(LeaseState.CLOSED)
        assert sm.state == LeaseState.CLOSED

    def test_active_to_novation_transfer(self):
        sm = StateMachine(state=LeaseState.ACTIVE)
        sm.transition(LeaseState.NOVATION_TRANSFER)
        assert sm.state == LeaseState.NOVATION_TRANSFER

    def test_novation_transfer_to_active(self):
        sm = StateMachine(state=LeaseState.NOVATION_TRANSFER)
        sm.transition(LeaseState.ACTIVE)
        assert sm.state == LeaseState.ACTIVE

    def test_active_to_total_loss(self):
        sm = StateMachine(state=LeaseState.ACTIVE)
        sm.transition(LeaseState.TOTAL_LOSS)
        assert sm.state == LeaseState.TOTAL_LOSS

    def test_total_loss_to_closed(self):
        sm = StateMachine(state=LeaseState.TOTAL_LOSS)
        sm.transition(LeaseState.CLOSED)
        assert sm.state == LeaseState.CLOSED

    def test_invalid_transition_raises(self):
        sm = StateMachine()
        with pytest.raises(TransitionError) as exc_info:
            sm.transition(LeaseState.MATURITY)
        assert "draft" in str(exc_info.value).lower()
        assert "maturity" in str(exc_info.value).lower()

    def test_closed_is_terminal(self):
        sm = StateMachine(state=LeaseState.CLOSED)
        with pytest.raises(TransitionError):
            sm.transition(LeaseState.ACTIVE)

    def test_transition_history(self):
        sm = StateMachine()
        sm.transition(LeaseState.ACTIVE)
        sm.transition(LeaseState.RECONCILIATION)
        sm.transition(LeaseState.ACTIVE)
        assert sm.history == [
            LeaseState.DRAFT,
            LeaseState.ACTIVE,
            LeaseState.RECONCILIATION,
            LeaseState.ACTIVE,
        ]

    def test_allowed_transitions_from_active(self):
        sm = StateMachine(state=LeaseState.ACTIVE)
        allowed = sm.allowed_transitions()
        expected = {
            LeaseState.RECONCILIATION,
            LeaseState.NOVATION_TRANSFER,
            LeaseState.TERMINATION,
            LeaseState.MATURITY,
            LeaseState.TOTAL_LOSS,
        }
        assert set(allowed) == expected
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/timothymessieh/Desktop/Machine\ Learning\ and\ Coding/novatex && python -m pytest tests/engine/test_machine.py -v`

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement states.py**

```python
# src/novatex/engine/__init__.py
"""Lease lifecycle state machine."""
```

```python
# src/novatex/engine/states.py
"""Lease lifecycle states."""
from enum import Enum


class LeaseState(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    RECONCILIATION = "reconciliation"
    NOVATION_TRANSFER = "novation_transfer"
    TERMINATION = "termination"
    MATURITY = "maturity"
    TOTAL_LOSS = "total_loss"
    CLOSED = "closed"
```

- [ ] **Step 4: Implement transitions.py**

```python
# src/novatex/engine/transitions.py
"""Valid state transitions for the novated lease lifecycle."""
from .states import LeaseState

# Map of (from_state) -> set of valid (to_states)
TRANSITIONS: dict[LeaseState, set[LeaseState]] = {
    LeaseState.DRAFT: {LeaseState.ACTIVE},
    LeaseState.ACTIVE: {
        LeaseState.RECONCILIATION,
        LeaseState.NOVATION_TRANSFER,
        LeaseState.TERMINATION,
        LeaseState.MATURITY,
        LeaseState.TOTAL_LOSS,
    },
    LeaseState.RECONCILIATION: {LeaseState.ACTIVE},
    LeaseState.NOVATION_TRANSFER: {LeaseState.ACTIVE},
    LeaseState.TERMINATION: {LeaseState.CLOSED},
    LeaseState.MATURITY: {LeaseState.CLOSED},
    LeaseState.TOTAL_LOSS: {LeaseState.CLOSED},
    LeaseState.CLOSED: set(),  # terminal
}
```

- [ ] **Step 5: Implement machine.py**

```python
# src/novatex/engine/machine.py
"""State machine for novated lease lifecycle."""
from .states import LeaseState
from .transitions import TRANSITIONS


class TransitionError(Exception):
    """Raised when an invalid state transition is attempted."""
    pass


class StateMachine:
    """Manages the lifecycle state of a novated lease."""

    def __init__(self, state: LeaseState = LeaseState.DRAFT):
        self._state = state
        self._history: list[LeaseState] = [state]

    @property
    def state(self) -> LeaseState:
        return self._state

    @property
    def history(self) -> list[LeaseState]:
        return list(self._history)

    def transition(self, to_state: LeaseState) -> None:
        """Transition to a new state. Raises TransitionError if invalid."""
        allowed = TRANSITIONS.get(self._state, set())
        if to_state not in allowed:
            raise TransitionError(
                f"Cannot transition from {self._state.value} to {to_state.value}. "
                f"Allowed: {sorted(s.value for s in allowed) if allowed else 'none (terminal state)'}"
            )
        self._state = to_state
        self._history.append(to_state)

    def allowed_transitions(self) -> list[LeaseState]:
        """Return list of states reachable from current state."""
        return sorted(TRANSITIONS.get(self._state, set()), key=lambda s: s.value)
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd /Users/timothymessieh/Desktop/Machine\ Learning\ and\ Coding/novatex && python -m pytest tests/engine/test_machine.py -v`

Expected: 17 passed

- [ ] **Step 7: Commit**

```bash
git add src/novatex/engine/ tests/engine/
git commit -m "feat(engine): state machine with lifecycle transitions and history tracking"
```

---

## Task 11: Obligation Engine

**Files:**
- Create: `src/novatex/obligations/__init__.py`
- Create: `src/novatex/obligations/definitions.py`
- Create: `src/novatex/obligations/tracker.py`
- Create: `tests/obligations/__init__.py`
- Create: `tests/obligations/test_tracker.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/obligations/__init__.py
```

```python
# tests/obligations/test_tracker.py
"""Tests for obligation tracking and escalation."""
from datetime import datetime, timezone, timedelta

from novatex.obligations.definitions import Obligation, ObligationStatus
from novatex.obligations.tracker import ObligationTracker


class TestObligation:
    def test_create(self):
        now = datetime(2026, 7, 15, 9, 0, 0, tzinfo=timezone.utc)
        ob = Obligation(
            obligation_id="OB-001",
            lease_id="NL-001",
            owner="employer",
            description="Remit payroll deduction to financier",
            deadline=now + timedelta(days=5),
            created_at=now,
        )
        assert ob.status == ObligationStatus.PENDING
        assert ob.is_overdue(now) is False

    def test_overdue(self):
        now = datetime(2026, 7, 15, 9, 0, 0, tzinfo=timezone.utc)
        ob = Obligation(
            obligation_id="OB-001",
            lease_id="NL-001",
            owner="employer",
            description="Remit payroll deduction",
            deadline=now - timedelta(days=1),
            created_at=now - timedelta(days=6),
        )
        assert ob.is_overdue(now) is True

    def test_complete(self):
        now = datetime(2026, 7, 15, 9, 0, 0, tzinfo=timezone.utc)
        ob = Obligation(
            obligation_id="OB-001",
            lease_id="NL-001",
            owner="employer",
            description="Remit payroll deduction",
            deadline=now + timedelta(days=5),
            created_at=now,
        )
        completed = ob.complete(now + timedelta(days=2))
        assert completed.status == ObligationStatus.COMPLETED
        assert completed.completed_at == now + timedelta(days=2)
        assert ob.status == ObligationStatus.PENDING  # original unchanged

    def test_escalate(self):
        now = datetime(2026, 7, 15, 9, 0, 0, tzinfo=timezone.utc)
        ob = Obligation(
            obligation_id="OB-001",
            lease_id="NL-001",
            owner="employer",
            description="Remit payroll deduction",
            deadline=now - timedelta(days=1),
            created_at=now - timedelta(days=6),
        )
        escalated = ob.escalate(now)
        assert escalated.status == ObligationStatus.ESCALATED


class TestObligationTracker:
    def test_add_and_list(self):
        tracker = ObligationTracker()
        now = datetime(2026, 7, 15, 9, 0, 0, tzinfo=timezone.utc)
        ob = Obligation(
            obligation_id="OB-001",
            lease_id="NL-001",
            owner="employer",
            description="Remit deduction",
            deadline=now + timedelta(days=5),
            created_at=now,
        )
        tracker.add(ob)
        assert len(tracker.get_pending("NL-001")) == 1

    def test_find_overdue(self):
        tracker = ObligationTracker()
        now = datetime(2026, 7, 20, 9, 0, 0, tzinfo=timezone.utc)
        ob1 = Obligation(
            obligation_id="OB-001", lease_id="NL-001", owner="employer",
            description="Overdue one",
            deadline=now - timedelta(days=2), created_at=now - timedelta(days=7),
        )
        ob2 = Obligation(
            obligation_id="OB-002", lease_id="NL-001", owner="employee",
            description="Not due yet",
            deadline=now + timedelta(days=5), created_at=now,
        )
        tracker.add(ob1)
        tracker.add(ob2)
        overdue = tracker.find_overdue(now)
        assert len(overdue) == 1
        assert overdue[0].obligation_id == "OB-001"

    def test_complete_obligation(self):
        tracker = ObligationTracker()
        now = datetime(2026, 7, 15, 9, 0, 0, tzinfo=timezone.utc)
        ob = Obligation(
            obligation_id="OB-001", lease_id="NL-001", owner="employer",
            description="Remit",
            deadline=now + timedelta(days=5), created_at=now,
        )
        tracker.add(ob)
        tracker.complete("OB-001", now + timedelta(days=2))
        assert len(tracker.get_pending("NL-001")) == 0
        assert len(tracker.get_completed("NL-001")) == 1

    def test_get_by_owner(self):
        tracker = ObligationTracker()
        now = datetime(2026, 7, 15, 9, 0, 0, tzinfo=timezone.utc)
        ob1 = Obligation(
            obligation_id="OB-001", lease_id="NL-001", owner="employer",
            description="Employer task",
            deadline=now + timedelta(days=5), created_at=now,
        )
        ob2 = Obligation(
            obligation_id="OB-002", lease_id="NL-001", owner="employee",
            description="Employee task",
            deadline=now + timedelta(days=5), created_at=now,
        )
        tracker.add(ob1)
        tracker.add(ob2)
        employer_obs = tracker.get_by_owner("NL-001", "employer")
        assert len(employer_obs) == 1
        assert employer_obs[0].owner == "employer"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/timothymessieh/Desktop/Machine\ Learning\ and\ Coding/novatex && python -m pytest tests/obligations/test_tracker.py -v`

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement definitions.py**

```python
# src/novatex/obligations/__init__.py
"""Obligation tracking and escalation."""
```

```python
# src/novatex/obligations/definitions.py
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
```

- [ ] **Step 4: Implement tracker.py**

```python
# src/novatex/obligations/tracker.py
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
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd /Users/timothymessieh/Desktop/Machine\ Learning\ and\ Coding/novatex && python -m pytest tests/obligations/test_tracker.py -v`

Expected: 7 passed

- [ ] **Step 6: Commit**

```bash
git add src/novatex/obligations/ tests/obligations/
git commit -m "feat(obligations): obligation tracker with deadline detection and escalation"
```

---

## Task 12: ATO Reference Tables

**Files:**
- Create: `src/novatex/reference/__init__.py`
- Create: `src/novatex/reference/ato_residuals.py`
- Create: `src/novatex/reference/ato_fbt.py`
- Create: `tests/reference/__init__.py`
- Create: `tests/reference/test_ato_residuals.py`
- Create: `tests/reference/test_ato_fbt.py`

- [ ] **Step 1: Write failing tests for ATO residuals**

```python
# tests/reference/__init__.py
```

```python
# tests/reference/test_ato_residuals.py
"""Tests for ATO minimum residual value tables."""
import pytest
from novatex.reference.ato_residuals import get_minimum_residual_pct


class TestATOResiduals:
    def test_12_months(self):
        assert get_minimum_residual_pct(12) == 65.63

    def test_24_months(self):
        assert get_minimum_residual_pct(24) == 56.25

    def test_36_months(self):
        assert get_minimum_residual_pct(36) == 46.88

    def test_48_months(self):
        assert get_minimum_residual_pct(48) == 37.50

    def test_60_months(self):
        assert get_minimum_residual_pct(60) == 28.13

    def test_invalid_term_raises(self):
        with pytest.raises(ValueError, match="No ATO residual"):
            get_minimum_residual_pct(18)

    def test_residual_amount(self):
        from novatex.reference.ato_residuals import residual_amount
        assert residual_amount(55000.00, 36) == pytest.approx(25784.00)
```

- [ ] **Step 2: Write failing tests for ATO FBT rates**

```python
# tests/reference/test_ato_fbt.py
"""Tests for ATO FBT rate tables."""
from novatex.reference.ato_fbt import (
    get_fbt_rate, get_statutory_fraction, get_lct_threshold,
)


class TestATOFBT:
    def test_fbt_rate_2026(self):
        assert get_fbt_rate(2026) == 0.47

    def test_statutory_fraction(self):
        assert get_statutory_fraction() == 0.20

    def test_lct_threshold_fuel_efficient_2026(self):
        assert get_lct_threshold(2026, fuel_efficient=True) == 89332

    def test_lct_threshold_standard_2026(self):
        assert get_lct_threshold(2026, fuel_efficient=False) == 76950
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd /Users/timothymessieh/Desktop/Machine\ Learning\ and\ Coding/novatex && python -m pytest tests/reference/ -v`

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 4: Implement ato_residuals.py**

```python
# src/novatex/reference/__init__.py
"""ATO reference tables — residuals, FBT rates, LCT thresholds."""
```

```python
# src/novatex/reference/ato_residuals.py
"""ATO minimum residual value percentages for novated leases.

Source: ATO TD 93/145 (as amended). These are the minimum residual
values expressed as a percentage of the vehicle's cost base.
"""

# term_months -> minimum residual percentage
_ATO_MINIMUM_RESIDUALS: dict[int, float] = {
    12: 65.63,
    24: 56.25,
    36: 46.88,
    48: 37.50,
    60: 28.13,
}


def get_minimum_residual_pct(term_months: int) -> float:
    """Get the ATO minimum residual percentage for a given lease term.

    Raises ValueError if the term is not a standard ATO term.
    """
    pct = _ATO_MINIMUM_RESIDUALS.get(term_months)
    if pct is None:
        valid = sorted(_ATO_MINIMUM_RESIDUALS.keys())
        raise ValueError(
            f"No ATO residual defined for {term_months}-month term. "
            f"Valid terms: {valid}"
        )
    return pct


def residual_amount(cost_base: float, term_months: int) -> float:
    """Calculate the residual/balloon amount."""
    pct = get_minimum_residual_pct(term_months)
    return round(cost_base * pct / 100, 2)
```

- [ ] **Step 5: Implement ato_fbt.py**

```python
# src/novatex/reference/ato_fbt.py
"""ATO FBT rates, statutory fractions, and LCT thresholds.

These values are updated annually by the ATO. The tables here
cover FY2025-2027. Add new years as the ATO publishes them.
"""

# FBT year -> FBT rate (FBT rate = top marginal tax rate + Medicare levy)
_FBT_RATES: dict[int, float] = {
    2025: 0.47,
    2026: 0.47,
    2027: 0.47,
}

# LCT thresholds: year -> (standard, fuel_efficient)
_LCT_THRESHOLDS: dict[int, tuple[int, int]] = {
    2025: (76950, 89332),
    2026: (76950, 89332),
    2027: (76950, 89332),  # placeholder — update when ATO publishes
}


def get_fbt_rate(year: int) -> float:
    """Get the FBT rate for a given FBT year. Defaults to latest known."""
    if year in _FBT_RATES:
        return _FBT_RATES[year]
    latest = max(_FBT_RATES.keys())
    return _FBT_RATES[latest]


def get_statutory_fraction() -> float:
    """The statutory fraction for FBT car benefit calculation.

    Fixed at 20% since 1 April 2014 (all km brackets collapsed).
    """
    return 0.20


def get_lct_threshold(year: int, fuel_efficient: bool = False) -> int:
    """Get the Luxury Car Tax threshold for a given year.

    fuel_efficient=True returns the higher threshold for EVs/PHEVs/FCEVs.
    """
    if year in _LCT_THRESHOLDS:
        standard, efficient = _LCT_THRESHOLDS[year]
    else:
        latest = max(_LCT_THRESHOLDS.keys())
        standard, efficient = _LCT_THRESHOLDS[latest]
    return efficient if fuel_efficient else standard
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd /Users/timothymessieh/Desktop/Machine\ Learning\ and\ Coding/novatex && python -m pytest tests/reference/ -v`

Expected: 11 passed (7 residuals + 4 fbt)

- [ ] **Step 7: Commit**

```bash
git add src/novatex/reference/ tests/reference/
git commit -m "feat(reference): ATO residual tables, FBT rates, and LCT thresholds"
```

---

## Task 13: YAML Contract Template Schema + Parser

**Files:**
- Create: `src/novatex/contracts/__init__.py`
- Create: `src/novatex/contracts/schema.py`
- Create: `src/novatex/contracts/parser.py`
- Create: `src/novatex/contracts/templates/novated_lease_v1.yaml`
- Create: `tests/contracts/__init__.py`
- Create: `tests/contracts/test_parser.py`

- [ ] **Step 1: Create the example YAML template**

```yaml
# src/novatex/contracts/templates/novated_lease_v1.yaml
---
schema_version: "1.0"
legal_document_hash: "sha256:placeholder_replace_with_real_hash"

lease_id: "NL-2026-00001"

parties:
  - party_id: "EMP-001"
    role: employee
    name: "Jane Smith"
  - party_id: "ORG-001"
    role: employer
    name: "Acme Corp"
    abn: "12 345 678 901"
  - party_id: "FIN-001"
    role: financier
    name: "SG Fleet Finance"
    abn: "98 765 432 109"

vehicle:
  make: "Tesla"
  model: "Model 3"
  year: 2026
  vehicle_type: bev
  cost_base: 55000.00
  gst_credit: 5000.00

terms:
  start_date: "2026-07-01"
  term_months: 36
  residual_pct: 46.88
  finance_rate: 6.49
  salary_sacrifice:
    frequency: fortnightly
    pre_tax: 612.00
    post_tax_ecm: 183.00

fbt:
  method: ev_exempt
  base_value: 55000.00
  statutory_rate: 0.20

running_costs:
  monthly_budget: 580.00
  categories:
    - charging
    - insurance
    - registration
    - tyres
    - maintenance
    - roadside
```

- [ ] **Step 2: Write failing tests**

```python
# tests/contracts/__init__.py
```

```python
# tests/contracts/test_parser.py
"""Tests for YAML contract template parsing."""
import os
from pathlib import Path

import pytest

from novatex.contracts.parser import parse_contract, ContractParseError
from novatex.models.lease import NovatedLease
from novatex.models.party import PartyRole
from novatex.models.vehicle import VehicleType
from novatex.models.fbt import FBTMethod


TEMPLATE_DIR = Path(__file__).parent.parent.parent / "src" / "novatex" / "contracts" / "templates"


class TestParseContract:
    def test_parse_v1_template(self):
        path = TEMPLATE_DIR / "novated_lease_v1.yaml"
        lease = parse_contract(path)
        assert isinstance(lease, NovatedLease)
        assert lease.lease_id == "NL-2026-00001"

    def test_parties_parsed(self):
        path = TEMPLATE_DIR / "novated_lease_v1.yaml"
        lease = parse_contract(path)
        assert len(lease.parties) == 3
        emp = lease.get_party(PartyRole.EMPLOYEE)
        assert emp is not None
        assert emp.name == "Jane Smith"

    def test_vehicle_parsed(self):
        path = TEMPLATE_DIR / "novated_lease_v1.yaml"
        lease = parse_contract(path)
        assert lease.vehicle.vehicle_type == VehicleType.BEV
        assert lease.vehicle.cost_base == 55000.00

    def test_fbt_parsed(self):
        path = TEMPLATE_DIR / "novated_lease_v1.yaml"
        lease = parse_contract(path)
        assert lease.fbt.method == FBTMethod.EV_EXEMPT
        assert lease.fbt.taxable_value == 0.0

    def test_legal_hash_bound(self):
        path = TEMPLATE_DIR / "novated_lease_v1.yaml"
        lease = parse_contract(path)
        assert lease.legal_document_hash == "sha256:placeholder_replace_with_real_hash"

    def test_invalid_yaml_raises(self, tmp_path):
        bad_file = tmp_path / "bad.yaml"
        bad_file.write_text("not: valid: yaml: {{{{")
        with pytest.raises(ContractParseError):
            parse_contract(bad_file)

    def test_missing_required_field_raises(self, tmp_path):
        incomplete = tmp_path / "incomplete.yaml"
        incomplete.write_text("schema_version: '1.0'\nlease_id: 'NL-001'\n")
        with pytest.raises(ContractParseError):
            parse_contract(incomplete)
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd /Users/timothymessieh/Desktop/Machine\ Learning\ and\ Coding/novatex && python -m pytest tests/contracts/test_parser.py -v`

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 4: Implement schema.py and parser.py**

```python
# src/novatex/contracts/__init__.py
"""YAML contract template parsing and validation."""
```

```python
# src/novatex/contracts/schema.py
"""Schema version validation for contract templates."""

SUPPORTED_VERSIONS = {"1.0"}


def validate_version(version: str) -> None:
    """Raise ValueError if schema version is not supported."""
    if version not in SUPPORTED_VERSIONS:
        raise ValueError(
            f"Unsupported schema version '{version}'. "
            f"Supported: {sorted(SUPPORTED_VERSIONS)}"
        )
```

```python
# src/novatex/contracts/parser.py
"""Parse YAML contract templates into NovatedLease models."""
from datetime import date
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from .schema import validate_version
from ..models.lease import NovatedLease
from ..models.party import Party, PartyRole
from ..models.vehicle import Vehicle, VehicleType
from ..models.terms import LeaseTerms, SalarySacrifice, PayFrequency
from ..models.fbt import FBTConfig, FBTMethod
from ..models.running_costs import RunningCostPool, CostCategory


class ContractParseError(Exception):
    """Raised when a contract template cannot be parsed."""
    pass


def parse_contract(path: Path) -> NovatedLease:
    """Parse a YAML contract template file into a NovatedLease.

    Raises ContractParseError on invalid YAML, missing fields,
    or validation failures.
    """
    try:
        with open(path) as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ContractParseError(f"Invalid YAML in {path}: {e}") from e

    if not isinstance(data, dict):
        raise ContractParseError(f"Expected a mapping at top level, got {type(data).__name__}")

    try:
        validate_version(data.get("schema_version", ""))

        parties = [
            Party(
                party_id=p["party_id"],
                role=PartyRole(p["role"]),
                name=p["name"],
                abn=p.get("abn"),
            )
            for p in data["parties"]
        ]

        v = data["vehicle"]
        vehicle = Vehicle(
            make=v["make"],
            model=v["model"],
            year=v["year"],
            vehicle_type=VehicleType(v["vehicle_type"]),
            cost_base=v["cost_base"],
            gst_credit=v["gst_credit"],
        )

        t = data["terms"]
        ss = t["salary_sacrifice"]
        terms = LeaseTerms(
            start_date=_parse_date(t["start_date"]),
            term_months=t["term_months"],
            residual_pct=t["residual_pct"],
            finance_rate=t["finance_rate"],
            salary_sacrifice=SalarySacrifice(
                frequency=PayFrequency(ss["frequency"]),
                pre_tax=ss["pre_tax"],
                post_tax_ecm=ss["post_tax_ecm"],
            ),
        )

        fb = data["fbt"]
        fbt = FBTConfig(
            method=FBTMethod(fb["method"]),
            base_value=fb["base_value"],
            statutory_rate=fb["statutory_rate"],
            total_operating_costs=fb.get("total_operating_costs"),
            private_use_pct=fb.get("private_use_pct"),
            employee_contributions=fb.get("employee_contributions"),
        )

        rc = data["running_costs"]
        running_costs = RunningCostPool(
            monthly_budget=rc["monthly_budget"],
            categories=[CostCategory(c) for c in rc["categories"]],
        )

        return NovatedLease(
            lease_id=data["lease_id"],
            parties=parties,
            vehicle=vehicle,
            terms=terms,
            fbt=fbt,
            running_costs=running_costs,
            legal_document_hash=data.get("legal_document_hash"),
        )

    except (KeyError, ValueError, ValidationError) as e:
        raise ContractParseError(f"Failed to parse contract {path}: {e}") from e


def _parse_date(value: Any) -> date:
    """Parse a date from string or date object (YAML may auto-parse dates)."""
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd /Users/timothymessieh/Desktop/Machine\ Learning\ and\ Coding/novatex && python -m pytest tests/contracts/test_parser.py -v`

Expected: 7 passed

- [ ] **Step 6: Commit**

```bash
git add src/novatex/contracts/ tests/contracts/
git commit -m "feat(contracts): YAML contract template parser with v1 example template"
```

---

## Task 14: Package Re-exports + Full Integration Test

**Files:**
- Modify: `src/novatex/__init__.py`
- Create: `tests/test_integration.py`

- [ ] **Step 1: Update package init with re-exports**

```python
# src/novatex/__init__.py
"""NovateX — Novated Lease Soft Contract Platform."""

from .models.lease import NovatedLease
from .models.party import Party, PartyRole
from .models.vehicle import Vehicle, VehicleType
from .models.terms import LeaseTerms, SalarySacrifice, PayFrequency
from .models.fbt import FBTConfig, FBTMethod
from .models.running_costs import RunningCostPool, CostCategory

from .ledger.events import LeaseEvent, EventType
from .ledger.signing import sign_event, verify_event, generate_keypair
from .ledger.merkle import hash_event, verify_chain
from .ledger.duckdb_ledger import DuckDBLedger

from .engine.states import LeaseState
from .engine.machine import StateMachine, TransitionError

from .obligations.definitions import Obligation, ObligationStatus
from .obligations.tracker import ObligationTracker

from .contracts.parser import parse_contract, ContractParseError

__all__ = [
    "NovatedLease", "Party", "PartyRole", "Vehicle", "VehicleType",
    "LeaseTerms", "SalarySacrifice", "PayFrequency",
    "FBTConfig", "FBTMethod", "RunningCostPool", "CostCategory",
    "LeaseEvent", "EventType", "sign_event", "verify_event", "generate_keypair",
    "hash_event", "verify_chain", "DuckDBLedger",
    "LeaseState", "StateMachine", "TransitionError",
    "Obligation", "ObligationStatus", "ObligationTracker",
    "parse_contract", "ContractParseError",
]
```

- [ ] **Step 2: Write the "Hello Lease" integration test**

This test proves Phase 0 works end-to-end: parse YAML → create events → sign → store in DuckDB → verify chain → track obligations.

```python
# tests/test_integration.py
"""End-to-end integration test: the full Phase 0 contract kernel."""
from datetime import datetime, timezone, timedelta
from pathlib import Path

from novatex import (
    parse_contract, NovatedLease, PartyRole,
    LeaseEvent, EventType, sign_event, verify_event,
    generate_keypair, hash_event, verify_chain,
    DuckDBLedger, StateMachine, LeaseState,
    Obligation, ObligationTracker,
)


TEMPLATE = Path(__file__).parent.parent / "src" / "novatex" / "contracts" / "templates" / "novated_lease_v1.yaml"


class TestPhase0Integration:
    def test_full_lifecycle(self, duckdb_path):
        """Parse YAML → sign events → store → verify → track obligations."""

        # 1. Parse the contract template
        lease = parse_contract(TEMPLATE)
        assert lease.lease_id == "NL-2026-00001"
        assert lease.vehicle.is_ev is True
        assert lease.fbt.taxable_value == 0.0

        # 2. Generate keys for each party
        emp_priv, emp_pub = generate_keypair()
        org_priv, org_pub = generate_keypair()
        fin_priv, fin_pub = generate_keypair()

        # 3. Create the ledger
        ledger = DuckDBLedger(duckdb_path)

        # 4. Create and sign the contract_created event
        now = datetime(2026, 7, 1, 9, 0, 0, tzinfo=timezone.utc)
        e1 = LeaseEvent(
            event_id="evt-001",
            lease_id=lease.lease_id,
            event_type=EventType.CONTRACT_CREATED,
            timestamp=now,
            originator="employee",
            payload={
                "vehicle": f"{lease.vehicle.make} {lease.vehicle.model}",
                "cost_base": lease.vehicle.cost_base,
                "term_months": lease.terms.term_months,
            },
        )
        e1 = sign_event(e1, emp_priv)
        ledger.append(e1)

        # 5. State machine: DRAFT → ACTIVE
        sm = StateMachine()
        sm.transition(LeaseState.ACTIVE)

        e2 = LeaseEvent(
            event_id="evt-002",
            lease_id=lease.lease_id,
            event_type=EventType.STATE_TRANSITION,
            timestamp=now + timedelta(hours=1),
            originator="employer",
            payload={"from": "draft", "to": "active"},
            prev_hash=hash_event(e1),
        )
        e2 = sign_event(e2, org_priv)
        ledger.append(e2)

        # 6. First payroll cycle
        e3 = LeaseEvent(
            event_id="evt-003",
            lease_id=lease.lease_id,
            event_type=EventType.PAYROLL_CYCLE,
            timestamp=now + timedelta(days=14),
            originator="employer",
            payload={
                "period": "2026-07-15",
                "pre_tax": lease.terms.salary_sacrifice.pre_tax,
                "post_tax": lease.terms.salary_sacrifice.post_tax_ecm,
                "total": lease.terms.salary_sacrifice.total_deduction,
            },
            prev_hash=hash_event(e2),
        )
        e3 = sign_event(e3, org_priv)
        ledger.append(e3)

        # 7. Verify the full chain
        history = ledger.get_history(lease.lease_id)
        assert len(history) == 3
        assert verify_chain(history) is True

        # 8. Verify each signature
        for event in history:
            assert verify_event(event) is True

        # 9. Track an obligation
        tracker = ObligationTracker()
        ob = Obligation(
            obligation_id="OB-001",
            lease_id=lease.lease_id,
            owner="employer",
            description="Remit payroll deduction to financier within 5 business days",
            deadline=now + timedelta(days=14) + timedelta(days=5),
            created_at=now + timedelta(days=14),
        )
        tracker.add(ob)

        # Not overdue yet
        check_time = now + timedelta(days=16)
        assert len(tracker.find_overdue(check_time)) == 0

        # Complete the obligation
        tracker.complete("OB-001", check_time)
        assert len(tracker.get_completed(lease.lease_id)) == 1

        # 10. Close the ledger
        ledger.close()

        print(f"\n  Phase 0 integration test passed!")
        print(f"  Lease: {lease.lease_id}")
        print(f"  Vehicle: {lease.vehicle.make} {lease.vehicle.model} ({lease.vehicle.vehicle_type.value})")
        print(f"  Events: {len(history)}")
        print(f"  Chain valid: True")
        print(f"  Signatures valid: True")
        print(f"  FBT taxable value: ${lease.fbt.taxable_value:.2f} (EV exempt)")
        print(f"  Residual: ${lease.residual_amount:.2f}")
```

- [ ] **Step 3: Run the integration test**

Run: `cd /Users/timothymessieh/Desktop/Machine\ Learning\ and\ Coding/novatex && python -m pytest tests/test_integration.py -v -s`

Expected: 1 passed, with output showing the lease details

- [ ] **Step 4: Run the FULL test suite**

Run: `cd /Users/timothymessieh/Desktop/Machine\ Learning\ and\ Coding/novatex && python -m pytest -v`

Expected: All tests pass (~60+ tests across all modules)

- [ ] **Step 5: Commit**

```bash
git add src/novatex/__init__.py tests/test_integration.py
git commit -m "feat(phase0): integration test — full lifecycle from YAML to verified event chain"
```

- [ ] **Step 6: Push to GitHub**

```bash
git push origin main
```

---

## Self-Review Checklist

**Spec coverage:**
- [x] 0.1 YAML contract template schema → Task 13 (schema.py, parser.py, v1 template)
- [x] 0.2 Pydantic models → Tasks 6, 7, 8, 9 (party, vehicle, terms, fbt, running_costs, lease)
- [x] 0.3 State machine → Task 10 (states, transitions, machine)
- [x] 0.4 Signed event ledger → Tasks 2, 3, 4, 5 (events, signing, merkle, duckdb_ledger)
- [x] 0.5 Contract template parser → Task 13 (parser.py)
- [x] 0.6 Obligation engine v1 → Task 11 (definitions, tracker)
- [x] 0.7 Unit test suite → Tests in every task + Task 14 integration
- [x] 0.8 ATO residual value table → Task 12 (ato_residuals, ato_fbt)

**Placeholder scan:** No TBD/TODO/placeholder steps found.

**Type consistency:** Verified — `LeaseEvent`, `EventType`, `LeaseState`, `NovatedLease`, `Obligation`, `ObligationTracker`, `StateMachine`, `DuckDBLedger` used consistently across all tasks.
