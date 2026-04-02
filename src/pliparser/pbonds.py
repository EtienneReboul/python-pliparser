"""Pseudobond parameter definitions.

This module exposes typed dataclass models for Pseudobond styling
"""

from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass

RGB = tuple[int, int, int]


@dataclass(frozen=True)
class PseudobondParamsBase(ABC):
    """Base style definition for one PLIP Pseudobond type."""

    rgb: RGB
    color: str
    radius: float
    dashes: int

    @classmethod
    @abstractmethod
    def Pseudobond_type(cls) -> str:
        """Return the PLIP Pseudobond key used in serialized mappings."""

    def as_legacy_dict(self) -> dict[str, object]:
        """Return the legacy dict format used by old code paths."""

        return {
            "RGB": list(self.rgb),
            "color": self.color,
            "radius": self.radius,
            "dashes": self.dashes,
        }


@dataclass(frozen=True)
class HydrophobicPb(PseudobondParamsBase):
    rgb: RGB = (0, 0, 0)
    color: str = "black"
    radius: float = 0.075
    dashes: int = 6

    @classmethod
    def Pseudobond_type(cls) -> str:
        return "Hydrophobic_Pseudobonds"


@dataclass(frozen=True)
class HydrogenBondsPb(PseudobondParamsBase):
    rgb: RGB = (0, 0, 255)
    color: str = "blue"
    radius: float = 0.075
    dashes: int = 0

    @classmethod
    def Pseudobond_type(cls) -> str:
        return "Hydrogen_Bonds"


@dataclass(frozen=True)
class WaterBridgesPb(PseudobondParamsBase):
    rgb: RGB = (191, 191, 255)
    color: str = "light blue"
    radius: float = 0.075
    dashes: int = 0

    @classmethod
    def Pseudobond_type(cls) -> str:
        return "Water_Bridges"


@dataclass(frozen=True)
class PiStackingParallelPb(PseudobondParamsBase):
    rgb: RGB = (0, 255, 0)
    color: str = "green"
    radius: float = 0.075
    dashes: int = 6

    @classmethod
    def Pseudobond_type(cls) -> str:
        return "pi-Stacking_parallel"


@dataclass(frozen=True)
class PiStackingPerpendicularPb(PseudobondParamsBase):
    rgb: RGB = (60, 32, 240)
    color: str = "purple"
    radius: float = 0.075
    dashes: int = 6

    @classmethod
    def Pseudobond_type(cls) -> str:
        return "pi-Stacking_perpendicular"


@dataclass(frozen=True)
class PiCationPb(PseudobondParamsBase):
    rgb: RGB = (255, 128, 0)
    color: str = "orange"
    radius: float = 0.075
    dashes: int = 6

    @classmethod
    def Pseudobond_type(cls) -> str:
        return "pi-Cation_Pseudobonds"


@dataclass(frozen=True)
class HalogenPb(PseudobondParamsBase):
    rgb: RGB = (54, 255, 191)
    color: str = "Dark cyan"
    radius: float = 0.075
    dashes: int = 0

    @classmethod
    def Pseudobond_type(cls) -> str:
        return "Halogen_Bond"


@dataclass(frozen=True)
class SaltBridgesPb(PseudobondParamsBase):
    rgb: RGB = (255, 255, 0)
    color: str = "yellow"
    radius: float = 0.075
    dashes: int = 6

    @classmethod
    def Pseudobond_type(cls) -> str:
        return "Salt_Bridges"


@dataclass(frozen=True)
class MetalComplexPb(PseudobondParamsBase):
    rgb: RGB = (140, 64, 153)
    color: str = "violetpurple"
    radius: float = 0.075
    dashes: int = 6

    @classmethod
    def Pseudobond_type(cls) -> str:
        return "Metal_Complex"


PBONDS: dict[str, PseudobondParamsBase] = {
    params.Pseudobond_type(): params
    for params in [
        HydrophobicPb(),
        HydrogenBondsPb(),
        WaterBridgesPb(),
        PiStackingParallelPb(),
        PiStackingPerpendicularPb(),
        PiCationPb(),
        HalogenPb(),
        SaltBridgesPb(),
        MetalComplexPb(),
    ]
}
