"""Tests for ATO FBT rate tables."""
from novatex.reference.ato_fbt import (
    get_fbt_rate, get_statutory_fraction, get_lct_threshold,
)


class TestATOFBT:
    def test_fbt_rate_2026(self):
        assert get_fbt_rate(2026) == 0.47

    def test_statutory_fraction(self):
        assert get_statutory_fraction() == 0.20

    def test_lct_threshold_fuel_efficient_2026(self):
        assert get_lct_threshold(2026, fuel_efficient=True) == 89332

    def test_lct_threshold_standard_2026(self):
        assert get_lct_threshold(2026, fuel_efficient=False) == 76950
