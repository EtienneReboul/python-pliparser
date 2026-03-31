from dataclasses import FrozenInstanceError

import pytest

from pliparser.params import MARKERS
from pliparser.params import HalogenMarker
from pliparser.params import HydrogenAcceptorMarker
from pliparser.params import HydrogenDonorMarker
from pliparser.params import HydrophobicMarker
from pliparser.params import MarkerBase
from pliparser.params import NegativeIonMarker
from pliparser.params import PiSystemMarker
from pliparser.params import PositiveIonMarker
from pliparser.params import WaterMarker


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
