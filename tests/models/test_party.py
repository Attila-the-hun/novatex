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
