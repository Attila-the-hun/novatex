"""Tests for Vehicle model."""
import pytest
from novatex.models.vehicle import Vehicle, VehicleType


class TestVehicle:
    def test_create_ev(self):
        v = Vehicle(
            make="Tesla",
            model="Model 3",
            year=2026,
            vehicle_type=VehicleType.BEV,
            cost_base=55000.00,
            gst_credit=5000.00,
        )
        assert v.vehicle_type == VehicleType.BEV
        assert v.is_ev is True
        assert v.cost_ex_gst == 50000.00

    def test_create_ice(self):
        v = Vehicle(
            make="Toyota",
            model="Camry",
            year=2026,
            vehicle_type=VehicleType.ICE,
            cost_base=42000.00,
            gst_credit=3818.18,
        )
        assert v.is_ev is False

    def test_vehicle_types(self):
        expected = {"bev", "phev", "fcev", "ice"}
        actual = {t.value for t in VehicleType}
        assert expected == actual

    def test_fbt_exempt_ev_under_threshold(self):
        v = Vehicle(
            make="Tesla", model="Model 3", year=2026,
            vehicle_type=VehicleType.BEV,
            cost_base=55000.00, gst_credit=5000.00,
        )
        assert v.is_fbt_exempt(lct_threshold=89332.00) is True

    def test_fbt_not_exempt_ev_over_threshold(self):
        v = Vehicle(
            make="Tesla", model="Model S Plaid", year=2026,
            vehicle_type=VehicleType.BEV,
            cost_base=150000.00, gst_credit=13636.36,
        )
        assert v.is_fbt_exempt(lct_threshold=89332.00) is False

    def test_fbt_not_exempt_ice(self):
        v = Vehicle(
            make="Toyota", model="Camry", year=2026,
            vehicle_type=VehicleType.ICE,
            cost_base=42000.00, gst_credit=3818.18,
        )
        assert v.is_fbt_exempt(lct_threshold=89332.00) is False
