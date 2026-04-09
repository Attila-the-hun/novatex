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
