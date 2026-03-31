"""Marker definitions for interaction visualization."""

from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass

Color = str


@dataclass(frozen=True)
class MarkerBase(ABC):
    """Base marker definition used by visualization layers."""

    color: Color
    radius: float

    @classmethod
    @abstractmethod
    def marker_type(cls) -> str:
        """Return marker key used in registries and serialization."""


@dataclass(frozen=True)
class HydrophobicMarker(MarkerBase):
    color: Color = "slategray"
    radius: float = 1.0

    @classmethod
    def marker_type(cls) -> str:
        return "hydrophobic"


@dataclass(frozen=True)
class HydrogenDonorMarker(MarkerBase):
    color: Color = "dodgerblue"
    radius: float = 1.0

    @classmethod
    def marker_type(cls) -> str:
        return "hydrogen_donor"


@dataclass(frozen=True)
class HydrogenAcceptorMarker(MarkerBase):
    color: Color = "deepskyblue"
    radius: float = 1.0

    @classmethod
    def marker_type(cls) -> str:
        return "hydrogen_acceptor"


@dataclass(frozen=True)
class WaterMarker(MarkerBase):
    color: Color = "mediumturquoise"
    radius: float = 1.0

    @classmethod
    def marker_type(cls) -> str:
        return "water"


@dataclass(frozen=True)
class PiSystemMarker(MarkerBase):
    color: Color = "orchid"
    radius: float = 1.0

    @classmethod
    def marker_type(cls) -> str:
        return "pi_system"


@dataclass(frozen=True)
class PositiveIonMarker(MarkerBase):
    color: Color = "orangered"
    radius: float = 1.0

    @classmethod
    def marker_type(cls) -> str:
        return "positive_ion"


@dataclass(frozen=True)
class NegativeIonMarker(MarkerBase):
    color: Color = "royalblue"
    radius: float = 1.0

    @classmethod
    def marker_type(cls) -> str:
        return "negative_ion"


@dataclass(frozen=True)
class HalogenMarker(MarkerBase):
    color: Color = "goldenrod"
    radius: float = 1.0

    @classmethod
    def marker_type(cls) -> str:
        return "halogen"


MARKERS: dict[str, MarkerBase] = {
    marker.marker_type(): marker
    for marker in [
        HydrophobicMarker(),
        HydrogenDonorMarker(),
        HydrogenAcceptorMarker(),
        WaterMarker(),
        PiSystemMarker(),
        PositiveIonMarker(),
        NegativeIonMarker(),
        HalogenMarker(),
    ]
}
