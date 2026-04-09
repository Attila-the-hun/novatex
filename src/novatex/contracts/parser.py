"""Parse YAML contract templates into NovatedLease models."""
from datetime import date
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from .schema import validate_version
from ..models.lease import NovatedLease
from ..models.party import Party, PartyRole
from ..models.vehicle import Vehicle, VehicleType
from ..models.terms import LeaseTerms, SalarySacrifice, PayFrequency
from ..models.fbt import FBTConfig, FBTMethod
from ..models.running_costs import RunningCostPool, CostCategory


class ContractParseError(Exception):
    """Raised when a contract template cannot be parsed."""
    pass


def parse_contract(path: Path) -> NovatedLease:
    """Parse a YAML contract template file into a NovatedLease.

    Raises ContractParseError on invalid YAML, missing fields,
    or validation failures.
    """
    try:
        with open(path) as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ContractParseError(f"Invalid YAML in {path}: {e}") from e

    if not isinstance(data, dict):
        raise ContractParseError(f"Expected a mapping at top level, got {type(data).__name__}")

    try:
        validate_version(data.get("schema_version", ""))

        parties = [
            Party(
                party_id=p["party_id"],
                role=PartyRole(p["role"]),
                name=p["name"],
                abn=p.get("abn"),
            )
            for p in data["parties"]
        ]

        v = data["vehicle"]
        vehicle = Vehicle(
            make=v["make"],
            model=v["model"],
            year=v["year"],
            vehicle_type=VehicleType(v["vehicle_type"]),
            cost_base=v["cost_base"],
            gst_credit=v["gst_credit"],
        )

        t = data["terms"]
        ss = t["salary_sacrifice"]
        terms = LeaseTerms(
            start_date=_parse_date(t["start_date"]),
            term_months=t["term_months"],
            residual_pct=t["residual_pct"],
            finance_rate=t["finance_rate"],
            salary_sacrifice=SalarySacrifice(
                frequency=PayFrequency(ss["frequency"]),
                pre_tax=ss["pre_tax"],
                post_tax_ecm=ss["post_tax_ecm"],
            ),
        )

        fb = data["fbt"]
        fbt = FBTConfig(
            method=FBTMethod(fb["method"]),
            base_value=fb["base_value"],
            statutory_rate=fb["statutory_rate"],
            total_operating_costs=fb.get("total_operating_costs"),
            private_use_pct=fb.get("private_use_pct"),
            employee_contributions=fb.get("employee_contributions"),
        )

        rc = data["running_costs"]
        running_costs = RunningCostPool(
            monthly_budget=rc["monthly_budget"],
            categories=[CostCategory(c) for c in rc["categories"]],
        )

        return NovatedLease(
            lease_id=data["lease_id"],
            parties=parties,
            vehicle=vehicle,
            terms=terms,
            fbt=fbt,
            running_costs=running_costs,
            legal_document_hash=data.get("legal_document_hash"),
        )

    except (KeyError, ValueError, ValidationError) as e:
        raise ContractParseError(f"Failed to parse contract {path}: {e}") from e


def _parse_date(value: Any) -> date:
    """Parse a date from string or date object (YAML may auto-parse dates)."""
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))
