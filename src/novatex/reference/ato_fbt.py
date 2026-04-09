"""ATO FBT rates, statutory fractions, and LCT thresholds.

These values are updated annually by the ATO. The tables here
cover FY2025-2027. Add new years as the ATO publishes them.
"""

# FBT year -> FBT rate (FBT rate = top marginal tax rate + Medicare levy)
_FBT_RATES: dict[int, float] = {
    2025: 0.47,
    2026: 0.47,
    2027: 0.47,
}

# LCT thresholds: year -> (standard, fuel_efficient)
_LCT_THRESHOLDS: dict[int, tuple[int, int]] = {
    2025: (76950, 89332),
    2026: (76950, 89332),
    2027: (76950, 89332),  # placeholder — update when ATO publishes
}


def get_fbt_rate(year: int) -> float:
    """Get the FBT rate for a given FBT year. Defaults to latest known."""
    if year in _FBT_RATES:
        return _FBT_RATES[year]
    latest = max(_FBT_RATES.keys())
    return _FBT_RATES[latest]


def get_statutory_fraction() -> float:
    """The statutory fraction for FBT car benefit calculation.

    Fixed at 20% since 1 April 2014 (all km brackets collapsed).
    """
    return 0.20


def get_lct_threshold(year: int, fuel_efficient: bool = False) -> int:
    """Get the Luxury Car Tax threshold for a given year.

    fuel_efficient=True returns the higher threshold for EVs/PHEVs/FCEVs.
    """
    if year in _LCT_THRESHOLDS:
        standard, efficient = _LCT_THRESHOLDS[year]
    else:
        latest = max(_LCT_THRESHOLDS.keys())
        standard, efficient = _LCT_THRESHOLDS[latest]
    return efficient if fuel_efficient else standard
