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
