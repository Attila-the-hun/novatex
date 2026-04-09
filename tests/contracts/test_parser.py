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
