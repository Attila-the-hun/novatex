"""Tests for NovatedLease aggregate model."""
from datetime import date

from novatex.models.lease import NovatedLease
from novatex.models.party import Party, PartyRole
from novatex.models.vehicle import Vehicle, VehicleType
from novatex.models.terms import LeaseTerms, SalarySacrifice, PayFrequency
from novatex.models.fbt import FBTConfig, FBTMethod
from novatex.models.running_costs import RunningCostPool, CostCategory


def _sample_lease() -> NovatedLease:
    return NovatedLease(
        lease_id="NL-2026-00001",
        parties=[
            Party(party_id="EMP-001", role=PartyRole.EMPLOYEE, name="Jane Smith"),
            Party(party_id="ORG-001", role=PartyRole.EMPLOYER, name="Acme Corp", abn="12 345 678 901"),
            Party(party_id="FIN-001", role=PartyRole.FINANCIER, name="SG Fleet Finance", abn="98 765 432 109"),
        ],
        vehicle=Vehicle(
            make="Tesla", model="Model 3", year=2026,
            vehicle_type=VehicleType.BEV,
            cost_base=55000.00, gst_credit=5000.00,
        ),
        terms=LeaseTerms(
            start_date=date(2026, 7, 1),
            term_months=36,
            residual_pct=46.88,
            finance_rate=6.49,
            salary_sacrifice=SalarySacrifice(
                frequency=PayFrequency.FORTNIGHTLY,
                pre_tax=612.00, post_tax_ecm=183.00,
            ),
        ),
        fbt=FBTConfig(
            method=FBTMethod.EV_EXEMPT,
            base_value=55000.00,
            statutory_rate=0.20,
        ),
        running_costs=RunningCostPool(
            monthly_budget=580.00,
            categories=CostCategory.ev_defaults(),
        ),
    )


class TestNovatedLease:
    def test_create(self):
        lease = _sample_lease()
        assert lease.lease_id == "NL-2026-00001"
        assert len(lease.parties) == 3

    def test_get_party_by_role(self):
        lease = _sample_lease()
        emp = lease.get_party(PartyRole.EMPLOYEE)
        assert emp is not None
        assert emp.name == "Jane Smith"

    def test_get_party_missing_role(self):
        lease = _sample_lease()
        fm = lease.get_party(PartyRole.FLEET_MANAGER)
        assert fm is None

    def test_residual_amount(self):
        lease = _sample_lease()
        assert lease.residual_amount == 25784.00

    def test_is_ev(self):
        lease = _sample_lease()
        assert lease.vehicle.is_ev is True

    def test_fbt_exempt(self):
        lease = _sample_lease()
        assert lease.fbt.taxable_value == 0.0

    def test_legal_document_hash_optional(self):
        lease = _sample_lease()
        assert lease.legal_document_hash is None
