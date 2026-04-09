"""ATO minimum residual value percentages for novated leases.

Source: ATO TD 93/145 (as amended). These are the minimum residual
values expressed as a percentage of the vehicle's cost base.
"""

# term_months -> minimum residual percentage
_ATO_MINIMUM_RESIDUALS: dict[int, float] = {
    12: 65.63,
    24: 56.25,
    36: 46.88,
    48: 37.50,
    60: 28.13,
}


def get_minimum_residual_pct(term_months: int) -> float:
    """Get the ATO minimum residual percentage for a given lease term.

    Raises ValueError if the term is not a standard ATO term.
    """
    pct = _ATO_MINIMUM_RESIDUALS.get(term_months)
    if pct is None:
        valid = sorted(_ATO_MINIMUM_RESIDUALS.keys())
        raise ValueError(
            f"No ATO residual defined for {term_months}-month term. "
            f"Valid terms: {valid}"
        )
    return pct


def residual_amount(cost_base: float, term_months: int) -> float:
    """Calculate the residual/balloon amount."""
    pct = get_minimum_residual_pct(term_months)
    return round(cost_base * pct / 100, 2)
