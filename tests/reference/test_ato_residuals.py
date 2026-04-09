"""Tests for ATO minimum residual value tables."""
import pytest
from novatex.reference.ato_residuals import get_minimum_residual_pct


class TestATOResiduals:
    def test_12_months(self):
        assert get_minimum_residual_pct(12) == 65.63

    def test_24_months(self):
        assert get_minimum_residual_pct(24) == 56.25

    def test_36_months(self):
        assert get_minimum_residual_pct(36) == 46.88

    def test_48_months(self):
        assert get_minimum_residual_pct(48) == 37.50

    def test_60_months(self):
        assert get_minimum_residual_pct(60) == 28.13

    def test_invalid_term_raises(self):
        with pytest.raises(ValueError, match="No ATO residual"):
            get_minimum_residual_pct(18)

    def test_residual_amount(self):
        from novatex.reference.ato_residuals import residual_amount
        assert residual_amount(55000.00, 36) == pytest.approx(25784.00)
