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
