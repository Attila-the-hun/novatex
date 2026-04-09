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
