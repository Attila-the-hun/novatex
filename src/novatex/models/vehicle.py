"""Vehicle model — the leased asset."""
from enum import Enum

from pydantic import BaseModel, computed_field


class VehicleType(str, Enum):
    BEV = "bev"      # Battery Electric Vehicle
    PHEV = "phev"    # Plug-in Hybrid
    FCEV = "fcev"    # Fuel Cell Electric Vehicle
    ICE = "ice"      # Internal Combustion Engine


class Vehicle(BaseModel):
    """The vehicle under novated lease."""
    make: str
    model: str
    year: int
    vehicle_type: VehicleType
    cost_base: float       # Including GST
    gst_credit: float      # GST claimed by employer

    @computed_field
    @property
    def is_ev(self) -> bool:
        return self.vehicle_type in (VehicleType.BEV, VehicleType.PHEV, VehicleType.FCEV)

    @computed_field
    @property
    def cost_ex_gst(self) -> float:
        return self.cost_base - self.gst_credit

    def is_fbt_exempt(self, lct_threshold: float) -> bool:
        """EV FBT exemption: EV + cost below LCT threshold for fuel-efficient vehicles."""
        return self.is_ev and self.cost_base <= lct_threshold
