"""Tests for FBT configuration models."""
from novatex.models.fbt import FBTConfig, FBTMethod


class TestFBTConfig:
    def test_statutory_method(self):
        fbt = FBTConfig(
            method=FBTMethod.STATUTORY,
            base_value=55000.00,
            statutory_rate=0.20,
        )
        assert fbt.taxable_value == 11000.00

    def test_ecm_zeroes_fbt(self):
        fbt = FBTConfig(
            method=FBTMethod.STATUTORY,
            base_value=55000.00,
            statutory_rate=0.20,
        )
        assert fbt.ecm_contribution_required == 11000.00

    def test_ev_exempt(self):
        fbt = FBTConfig(
            method=FBTMethod.EV_EXEMPT,
            base_value=55000.00,
            statutory_rate=0.20,
        )
        assert fbt.taxable_value == 0.0
        assert fbt.ecm_contribution_required == 0.0

    def test_operating_cost_method(self):
        fbt = FBTConfig(
            method=FBTMethod.OPERATING_COST,
            base_value=55000.00,
            statutory_rate=0.20,
            total_operating_costs=15000.00,
            private_use_pct=0.60,
            employee_contributions=9000.00,
        )
        # (15000 * 0.60) - 9000 = 0
        assert fbt.taxable_value == 0.0

    def test_methods_exist(self):
        expected = {"statutory", "operating_cost", "ev_exempt"}
        actual = {m.value for m in FBTMethod}
        assert expected == actual
