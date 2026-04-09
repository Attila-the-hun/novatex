"""Tests for RunningCostPool model."""
import pytest
from novatex.models.running_costs import RunningCostPool, CostCategory


class TestRunningCostPool:
    def test_create_pool(self):
        pool = RunningCostPool(
            monthly_budget=580.00,
            categories=[
                CostCategory.FUEL,
                CostCategory.INSURANCE,
                CostCategory.REGISTRATION,
                CostCategory.TYRES,
                CostCategory.MAINTENANCE,
                CostCategory.ROADSIDE,
            ],
        )
        assert pool.monthly_budget == 580.00
        assert len(pool.categories) == 6
        assert pool.total_spent == 0.0
        assert pool.balance == 580.00

    def test_record_expense(self):
        pool = RunningCostPool(monthly_budget=580.00, categories=[CostCategory.FUEL])
        updated = pool.record_expense(150.00)
        assert updated.total_spent == 150.00
        assert updated.balance == 430.00

    def test_ev_categories_exclude_fuel(self):
        ev_cats = CostCategory.ev_defaults()
        assert CostCategory.FUEL not in ev_cats
        assert CostCategory.CHARGING in ev_cats

    def test_all_categories(self):
        expected = {
            "fuel", "insurance", "registration", "tyres",
            "maintenance", "roadside", "charging",
        }
        actual = {c.value for c in CostCategory}
        assert expected == actual

    def test_surplus_deficit(self):
        pool = RunningCostPool(monthly_budget=580.00, categories=[CostCategory.FUEL])
        pool = pool.record_expense(600.00)
        assert pool.balance == -20.00
