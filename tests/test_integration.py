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
        """Parse YAML -> sign events -> store -> verify -> track obligations."""

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

        # 5. State machine: DRAFT -> ACTIVE
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
