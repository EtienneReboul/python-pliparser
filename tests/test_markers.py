from dataclasses import FrozenInstanceError

import pytest

from pliparser.markers import MARKERS
from pliparser.markers import HalogenMarker
from pliparser.markers import HydrogenAcceptorMarker
from pliparser.markers import HydrogenDonorMarker
from pliparser.markers import HydrophobicMarker
from pliparser.markers import MarkerBase
from pliparser.markers import MetalBindingMarker
from pliparser.markers import MetalMarker
from pliparser.markers import NegativeIonMarker
from pliparser.markers import PiSystemMarker
from pliparser.markers import PositiveIonMarker
from pliparser.markers import WaterMarker


def test_markers_registry_contains_expected_keys() -> None:
    assert sorted(MARKERS.keys()) == [
        "halogen",
        "halogen_acceptor",
        "hydrogen_acceptor",
        "hydrogen_donor",
        "hydrophobic",
        "metal_binding",
        "metal_complex",
        "negative_ion",
        "pi_system",
        "positive_ion",
        "water",
    ]


def test_marker_instances_derive_from_abstract_base() -> None:
    assert all(isinstance(value, MarkerBase) for value in MARKERS.values())


def test_marker_defaults_match_visual_schema() -> None:
    expected_radii = {
        HydrophobicMarker: 0.40,
        HydrogenDonorMarker: 0.40,
        HydrogenAcceptorMarker: 0.40,
        WaterMarker: 0.40,
        PiSystemMarker: 0.80,
        PositiveIonMarker: 0.40,
        NegativeIonMarker: 0.40,
        HalogenMarker: 0.40,
        MetalMarker: 0.40,
        MetalBindingMarker: 0.40,
    }

    for marker_cls, expected_radius in expected_radii.items():
        marker = marker_cls()
        assert marker.radius == expected_radius
        assert marker.color


def test_dataclasses_are_frozen() -> None:
    style = HydrophobicMarker()

    with pytest.raises(FrozenInstanceError):
        style.color = "white"  # pyright: ignore[reportAttributeAccessIssue]
