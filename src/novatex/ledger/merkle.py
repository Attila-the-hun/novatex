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
