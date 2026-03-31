from dataclasses import FrozenInstanceError

import pytest

from pliparser.markers import MARKERS
from pliparser.markers import HalogenMarker
from pliparser.markers import HydrogenAcceptorMarker
from pliparser.markers import HydrogenDonorMarker
from pliparser.markers import HydrophobicMarker
from pliparser.markers import MarkerBase
from pliparser.markers import NegativeIonMarker
from pliparser.markers import PiSystemMarker
from pliparser.markers import PositiveIonMarker
from pliparser.markers import WaterMarker


def test_markers_registry_contains_expected_keys() -> None:
    assert sorted(MARKERS.keys()) == [
        "halogen",
        "hydrogen_acceptor",
        "hydrogen_donor",
        "hydrophobic",
        "negative_ion",
        "pi_system",
        "positive_ion",
        "water",
    ]


def test_marker_instances_derive_from_abstract_base() -> None:
    assert all(isinstance(value, MarkerBase) for value in MARKERS.values())


def test_marker_defaults_match_visual_schema() -> None:
    marker_classes = [
        HydrophobicMarker,
        HydrogenDonorMarker,
        HydrogenAcceptorMarker,
        WaterMarker,
        PiSystemMarker,
        PositiveIonMarker,
        NegativeIonMarker,
        HalogenMarker,
    ]

    for marker_cls in marker_classes:
        marker = marker_cls()
        assert marker.radius == 1.0
        assert marker.color


def test_dataclasses_are_frozen() -> None:
    style = HydrophobicMarker()

    with pytest.raises(FrozenInstanceError):
        style.color = "white"  # pyright: ignore[reportAttributeAccessIssue]
