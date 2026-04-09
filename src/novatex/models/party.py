"""Party model — participants in a novated lease."""
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class PartyRole(str, Enum):
    EMPLOYEE = "employee"
    EMPLOYER = "employer"
    FINANCIER = "financier"
    FLEET_MANAGER = "fleet_manager"


class Party(BaseModel):
    """A participant in a novated lease agreement."""
    party_id: str
    role: PartyRole
    name: str
    abn: Optional[str] = None
