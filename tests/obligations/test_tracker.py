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
