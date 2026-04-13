from dataclasses import FrozenInstanceError

import pytest

from pliparser.pbonds import PBONDS
from pliparser.pbonds import HalogenPb
from pliparser.pbonds import HydrophobicPb
from pliparser.pbonds import PseudobondParamsBase


def test_pbonds_registry_contains_expected_keys() -> None:
    assert sorted(PBONDS.keys()) == [
        "halogen_bonds",
        "hydrogen_bonds",
        "hydrophobic_interactions",
        "metal_complexes",
        "pi-cation_interactions",
        "pi-stacking_parallel",
        "pi-stacking_perpendicular",
        "salt_bridges",
        "water_bridges",
    ]


def test_pbonds_registry_values_are_base_type() -> None:
    assert all(isinstance(value, PseudobondParamsBase) for value in PBONDS.values())


def test_hydrophobic_pb_defaults() -> None:
    style = HydrophobicPb()

    assert style.rgb == (0, 0, 0)
    assert style.color == "black"
    assert style.radius == 0.075
    assert style.dashes == 6
    assert style.Pseudobond_type() == "hydrophobic_interactions"


def test_halogen_pb_legacy_schema() -> None:
    style = HalogenPb()

    assert style.as_legacy_dict() == {
        "RGB": [54, 255, 191],
        "color": "dark cyan",
        "radius": 0.075,
        "dashes": 0,
    }


def test_pbonds_dataclasses_are_frozen() -> None:
    style = HydrophobicPb()

    with pytest.raises(FrozenInstanceError):
        style.color = "white"  # pyright: ignore[reportAttributeAccessIssue]
