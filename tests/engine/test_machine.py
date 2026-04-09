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
