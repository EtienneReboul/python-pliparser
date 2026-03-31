"""Interaction parameter definitions.

This module exposes typed dataclass models for interaction styling and keeps a
legacy ``params_dict`` mapping for compatibility with existing consumers.
"""

from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from typing import Optional

RGB = tuple[int, int, int]


@dataclass(frozen=True)
class InteractionParamsBase(ABC):
    """Base style definition for one PLIP interaction type."""

    rgb: RGB
    color: str
    representation: str

    @classmethod
    @abstractmethod
    def interaction_type(cls) -> str:
        """Return the PLIP interaction key used in serialized mappings."""

    def as_legacy_dict(self) -> dict[str, object]:
        """Return the legacy dict format used by old code paths."""

        return {
            "RGB": list(self.rgb),
            "color": self.color,
            "Representation": self.representation,
        }


@dataclass(frozen=True)
class HydrophobicInteractionsParams(InteractionParamsBase):
    rgb: RGB = (0, 0, 0)
    color: str = "black"
    representation: str = "dashed_line"

    @classmethod
    def interaction_type(cls) -> str:
        return "Hydrophobic_Interactions"


@dataclass(frozen=True)
class HydrogenBondsParams(InteractionParamsBase):
    rgb: RGB = (0, 0, 255)
    color: str = "blue"
    representation: str = "solid_line"

    @classmethod
    def interaction_type(cls) -> str:
        return "Hydrogen_Bonds"


@dataclass(frozen=True)
class WaterBridgesParams(InteractionParamsBase):
    rgb: RGB = (191, 191, 255)
    color: str = "light blue"
    representation: str = "solid_line"

    @classmethod
    def interaction_type(cls) -> str:
        return "Water_Bridges"


@dataclass(frozen=True)
class PiStackingParallelParams(InteractionParamsBase):
    rgb: RGB = (0, 255, 0)
    color: str = "green"
    representation: str = "dashed_line"

    @classmethod
    def interaction_type(cls) -> str:
        return "pi-Stacking_parallel"


@dataclass(frozen=True)
class PiStackingPerpendicularParams(InteractionParamsBase):
    rgb: RGB = (60, 32, 240)
    color: str = "purple"
    representation: str = "dashed_line"

    @classmethod
    def interaction_type(cls) -> str:
        return "pi-Stacking_perpendicular"


@dataclass(frozen=True)
class PiCationInteractionsParams(InteractionParamsBase):
    rgb: RGB = (255, 128, 0)
    color: str = "orange"
    representation: str = "dashed_line"

    @classmethod
    def interaction_type(cls) -> str:
        return "pi-Cation_Interactions"


@dataclass(frozen=True)
class HalogenBondParams(InteractionParamsBase):
    rgb: RGB = (54, 255, 191)
    color: str = "Dark cyan"
    representation: str = "solid_line"

    @classmethod
    def interaction_type(cls) -> str:
        return "Halogen_Bond"


@dataclass(frozen=True)
class SaltBridgesParams(InteractionParamsBase):
    rgb: RGB = (255, 255, 0)
    color: str = "yellow"
    representation: str = "dashed_line"

    @classmethod
    def interaction_type(cls) -> str:
        return "Salt_Bridges"


@dataclass(frozen=True)
class MetalComplexParams(InteractionParamsBase):
    rgb: RGB = (140, 64, 153)
    color: str = "violetpurple"
    representation: str = "dashed_line"

    @classmethod
    def interaction_type(cls) -> str:
        return "Metal_Complex"


PARAMS: dict[str, InteractionParamsBase] = {
    params.interaction_type(): params
    for params in [
        HydrophobicInteractionsParams(),
        HydrogenBondsParams(),
        WaterBridgesParams(),
        PiStackingParallelParams(),
        PiStackingPerpendicularParams(),
        PiCationInteractionsParams(),
        HalogenBondParams(),
        SaltBridgesParams(),
        MetalComplexParams(),
    ]
}


def to_legacy_params_dict(params: Optional[dict[str, InteractionParamsBase]] = None) -> dict[str, dict[str, object]]:
    """Convert typed params to the legacy dict-of-dicts schema."""

    source = PARAMS if params is None else params
    return {interaction: style.as_legacy_dict() for interaction, style in source.items()}


# Backward-compatible export name used by legacy callers.
params_dict: dict[str, dict[str, object]] = to_legacy_params_dict()
