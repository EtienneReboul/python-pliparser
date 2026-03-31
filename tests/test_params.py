from dataclasses import FrozenInstanceError

import pytest

from pliparser.params import PARAMS
from pliparser.params import HydrophobicInteractionsParams
from pliparser.params import InteractionParamsBase
from pliparser.params import params_dict
from pliparser.params import to_legacy_params_dict


def test_params_registry_contains_expected_keys() -> None:
    assert sorted(PARAMS.keys()) == [
        "Halogen_Bond",
        "Hydrogen_Bonds",
        "Hydrophobic_Interactions",
        "Metal_Complex",
        "Salt_Bridges",
        "Water_Bridges",
        "pi-Cation_Interactions",
        "pi-Stacking_parallel",
        "pi-Stacking_perpendicular",
    ]


def test_params_instances_derive_from_abstract_base() -> None:
    assert all(isinstance(value, InteractionParamsBase) for value in PARAMS.values())


def test_legacy_schema_matches_original_contract() -> None:
    legacy = to_legacy_params_dict()

    assert legacy["Hydrogen_Bonds"] == {
        "RGB": [0, 0, 255],
        "color": "blue",
        "Representation": "solid_line",
    }
    assert legacy == params_dict


def test_dataclasses_are_frozen() -> None:
    style = HydrophobicInteractionsParams()

    with pytest.raises(FrozenInstanceError):
        style.color = "white"  # pyright: ignore[reportAttributeAccessIssue] # This is a test to confirm that the dataclass is frozen, so we expect an error when trying to modify an attribute.
