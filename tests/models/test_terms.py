"""Tests for LeaseTerms and SalarySacrifice models."""
from datetime import date

import pytest
from novatex.models.terms import LeaseTerms, SalarySacrifice, PayFrequency


class TestSalarySacrifice:
    def test_create(self):
        ss = SalarySacrifice(
            frequency=PayFrequency.FORTNIGHTLY,
            pre_tax=612.00,
            post_tax_ecm=183.00,
        )
        assert ss.total_deduction == 795.00

    def test_monthly(self):
        ss = SalarySacrifice(
            frequency=PayFrequency.MONTHLY,
            pre_tax=1326.00,
            post_tax_ecm=396.50,
        )
        assert ss.total_deduction == 1722.50


class TestLeaseTerms:
    def test_create(self):
        terms = LeaseTerms(
            start_date=date(2026, 7, 1),
            term_months=36,
            residual_pct=46.88,
            finance_rate=6.49,
            salary_sacrifice=SalarySacrifice(
                frequency=PayFrequency.FORTNIGHTLY,
                pre_tax=612.00,
                post_tax_ecm=183.00,
            ),
        )
        assert terms.end_date == date(2029, 7, 1)
        assert terms.residual_pct == 46.88

    def test_residual_amount(self):
        terms = LeaseTerms(
            start_date=date(2026, 7, 1),
            term_months=36,
            residual_pct=46.88,
            finance_rate=6.49,
            salary_sacrifice=SalarySacrifice(
                frequency=PayFrequency.FORTNIGHTLY,
                pre_tax=612.00,
                post_tax_ecm=183.00,
            ),
        )
        # residual_amount needs vehicle cost_base, so it's a method
        assert terms.residual_amount(cost_base=55000.00) == pytest.approx(25784.00)

    def test_end_date_60_months(self):
        terms = LeaseTerms(
            start_date=date(2026, 1, 1),
            term_months=60,
            residual_pct=28.13,
            finance_rate=5.99,
            salary_sacrifice=SalarySacrifice(
                frequency=PayFrequency.MONTHLY,
                pre_tax=900.00,
                post_tax_ecm=270.00,
            ),
        )
        assert terms.end_date == date(2031, 1, 1)
