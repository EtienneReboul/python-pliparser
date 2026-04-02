import math
from pathlib import Path

import pytest

import pliparser.csv2cxc as csv2cxc
from pliparser.csv2cxc import _parse_xyz
from pliparser.csv2cxc import create_cxc_header
from pliparser.csv2cxc import create_interaction_commands
from pliparser.csv2cxc import create_interaction_comment
from pliparser.csv2cxc import create_marker
from pliparser.csv2cxc import create_reveal_command
from pliparser.csv2cxc import get_marker_type_from_row
from pliparser.csv2cxc import triangulate_water_coordinate
from pliparser.csv2cxc import write_cxc_file
from pliparser.pbonds import PBONDS

_DUMMY_CONFIG = {"issmalmol": False}


def _angle_at_water(
    acceptor: tuple[float, float, float],
    donor: tuple[float, float, float],
    water: tuple[float, float, float],
) -> float:
    aw = (acceptor[0] - water[0], acceptor[1] - water[1], acceptor[2] - water[2])
    dw = (donor[0] - water[0], donor[1] - water[1], donor[2] - water[2])
    dot = aw[0] * dw[0] + aw[1] * dw[1] + aw[2] * dw[2]
    aw_norm = math.sqrt(aw[0] ** 2 + aw[1] ** 2 + aw[2] ** 2)
    dw_norm = math.sqrt(dw[0] ** 2 + dw[1] ** 2 + dw[2] ** 2)
    return math.degrees(math.acos(dot / (aw_norm * dw_norm)))


def test_triangulate_water_coordinate_matches_distances_and_angle() -> None:
    row = {
        "interaction_type": "water_bridge",
        "protisdon": "True",
        "ligcoo": "0.0,0.0,0.0",
        "protcoo": "3.0,0.0,0.0",
        "dist_a-w": "2.0",
        "dist_d-w": "2.5",
        "water_angle": "82.81924421854171",
    }

    water = triangulate_water_coordinate(row)

    acceptor = (0.0, 0.0, 0.0)
    donor = (3.0, 0.0, 0.0)
    assert math.isclose(math.dist(acceptor, water), 2.0, abs_tol=1e-6)
    assert math.isclose(math.dist(donor, water), 2.5, abs_tol=1e-6)
    assert math.isclose(_angle_at_water(acceptor, donor, water), 82.81924421854171, abs_tol=1e-6)


def test_triangulate_water_coordinate_handles_protisdon_false() -> None:
    row = {
        "interaction_type": "water_bridge",
        "protisdon": "False",
        "ligcoo": "3.0,0.0,0.0",
        "protcoo": "0.0,0.0,0.0",
        "dist_a-w": "2.0",
        "dist_d-w": "2.5",
        "water_angle": "82.81924421854171",
    }

    water = triangulate_water_coordinate(row)

    acceptor = (0.0, 0.0, 0.0)
    donor = (3.0, 0.0, 0.0)
    assert math.isclose(math.dist(acceptor, water), 2.0, abs_tol=1e-6)
    assert math.isclose(math.dist(donor, water), 2.5, abs_tol=1e-6)


def test_triangulate_water_coordinate_rejects_non_water_bridge_row() -> None:
    row = {
        "interaction_type": "hydrogen_bond",
        "protisdon": "True",
        "ligcoo": "0.0,0.0,0.0",
        "protcoo": "3.0,0.0,0.0",
        "dist_a-w": "2.0",
        "dist_d-w": "2.5",
        "water_angle": "82.0",
    }

    with pytest.raises(ValueError, match="requires a water_bridge"):
        triangulate_water_coordinate(row)


def test_triangulate_water_coordinate_rejects_inconsistent_geometry() -> None:
    row = {
        "interaction_type": "water_bridge",
        "protisdon": "True",
        "ligcoo": "0.0,0.0,0.0",
        "protcoo": "10.0,0.0,0.0",
        "dist_a-w": "2.0",
        "dist_d-w": "2.5",
        "water_angle": "82.0",
    }

    with pytest.raises(ValueError, match="Inconsistent water-bridge geometry"):
        triangulate_water_coordinate(row)


def test_parse_xyz_parses_values() -> None:
    assert _parse_xyz("1.0, 2.5, -3.0", "ligcoo") == (1.0, 2.5, -3.0)


def test_parse_xyz_rejects_invalid_count() -> None:
    with pytest.raises(ValueError, match="Row must contain 'ligcoo' as 'x,y,z'"):
        _parse_xyz("1.0,2.0", "ligcoo")


@pytest.mark.parametrize(
    ("row", "entity_type", "expected"),
    [
        ({"interaction_type": "hydrogen_bond", "protisdon": "True"}, "receptor", "hydrogen_donor"),
        ({"interaction_type": "hydrogen_bond", "protisdon": "False"}, "receptor", "hydrogen_acceptor"),
        ({"interaction_type": "hydrogen_bond", "protisdon": "True"}, "ligand", "hydrogen_acceptor"),
        ({"interaction_type": "hydrogen_bond", "protisdon": "False"}, "ligand", "hydrogen_donor"),
        ({"interaction_type": "hydrophobic_interaction"}, "ligand", "hydrophobic"),
        ({"interaction_type": "pi_stack"}, "receptor", "pi_system"),
        ({"interaction_type": "pi_cation", "protcharged": "True"}, "receptor", "positive_ion"),
        ({"interaction_type": "pi_cation", "protcharged": "False"}, "ligand", "positive_ion"),
        ({"interaction_type": "water_bridge", "protisdon": "True"}, "water", "water"),
        ({"interaction_type": "water_bridge", "protisdon": "False"}, "receptor", "hydrogen_acceptor"),
        ({"interaction_type": "salt_bridge", "protispos": "True"}, "receptor", "positive_ion"),
        ({"interaction_type": "salt_bridge", "protispos": "False"}, "ligand", "positive_ion"),
        ({"interaction_type": "halogen_bond"}, "ligand", "halogen"),
        ({"interaction_type": "halogen_bond"}, "receptor", "halogen_acceptor"),
    ],
)
def test_get_marker_type_from_row_mappings(row: dict[str, str], entity_type: str, expected: str) -> None:
    assert get_marker_type_from_row(row, entity_type=entity_type) == expected


def test_get_marker_type_from_row_requires_interaction_type() -> None:
    with pytest.raises(ValueError, match="Row must contain 'interaction_type' key"):
        get_marker_type_from_row({}, entity_type="ligand")


def test_create_marker_renders_expected_command() -> None:
    cmd = create_marker("hydrogen_donor", "#1.2", (1.0, 2.0, 3.0))
    assert cmd == "marker #1.2 position 1.0,2.0,3.0 radius 0.4 color dodgerblue\n"


def test_create_marker_rejects_unknown_marker_type() -> None:
    with pytest.raises(ValueError, match="Unknown marker type"):
        create_marker("unknown_marker", "#1.1", (0.0, 0.0, 0.0))


def test_create_interaction_comment_uses_values() -> None:
    row = {
        "interaction_type": "hydrogen_bond",
        "resnr": "45",
        "restype": "ARG",
        "reschain": "A",
        "resnr_lig": "10",
        "restype_lig": "LIG",
        "reschain_lig": "B",
    }

    assert create_interaction_comment(row) == "# interaction between receptor hydrogen_bond: ARG45A and LIG10B\n"


def test_create_interaction_comment_has_defaults() -> None:
    comment = create_interaction_comment({})
    assert "unknown_interaction" in comment
    assert "unknown_restypeunknown_resnrunknown_reschain" in comment


def test_create_reveal_command_for_macromolecule() -> None:
    row = {
        "resnr": "45",
        "reschain": "A",
        "resnr_lig": "10",
        "reschain_lig": "B",
    }
    cmd = create_reveal_command(row, model_idces=(1, 2), config={"issmalmol": False})

    assert "show #1/A:45\n" in cmd
    assert "show #1/B:10 & sidechain\n" in cmd
    assert "color #1/B:10 & sidechain byhetero\n" in cmd


def test_create_reveal_command_for_small_molecule() -> None:
    row = {
        "resnr": "45",
        "reschain": "A",
        "resnr_lig": "10",
        "reschain_lig": "B",
    }
    cmd = create_reveal_command(row, model_idces=(1, 2), config={"issmalmol": True})

    assert "show #1/B:10 & sidechain" not in cmd
    assert cmd.endswith("byhetero\n")


def test_create_reveal_command_uses_backbone_when_sidechain_false() -> None:
    row = {
        "resnr": "45",
        "reschain": "A",
        "resnr_lig": "10",
        "reschain_lig": "B",
        "sidechain": "False",
    }
    cmd = create_reveal_command(row, model_idces=(1, 2), config={"issmalmol": False})

    assert "color #1/A:45 & backbone byhetero\n" in cmd
    assert "show #1/B:10 & sidechain\n" in cmd
    assert "color #1/B:10 & sidechain byhetero\n" in cmd


def test_create_interaction_commands_requires_interaction_type() -> None:
    with pytest.raises(ValueError, match="Row must contain 'interaction_type' key"):
        create_interaction_commands({}, marker_counter=0, model_idces=(1, 1), config=_DUMMY_CONFIG)


def test_create_interaction_commands_requires_ligand_coordinates() -> None:
    row = {"interaction_type": "hydrogen_bond", "protcoo": "1.0,2.0,3.0", "protisdon": "True"}
    with pytest.raises(ValueError, match="Row must contain 'ligcoo' key with coordinates"):
        create_interaction_commands(row, marker_counter=0, model_idces=(1, 1), config=_DUMMY_CONFIG)


def test_create_interaction_commands_requires_protein_coordinates() -> None:
    row = {"interaction_type": "hydrogen_bond", "ligcoo": "1.0,2.0,3.0", "protisdon": "True"}
    with pytest.raises(ValueError, match="Row must contain 'protcoo' key with coordinates"):
        create_interaction_commands(row, marker_counter=0, model_idces=(1, 1), config=_DUMMY_CONFIG)


def test_create_interaction_commands_builds_non_water_bridge(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(csv2cxc.PBONDS, "hydrogen_bond", PBONDS["Hydrogen_Bonds"])
    row = {
        "interaction_type": "hydrogen_bond",
        "protisdon": "True",
        "ligcoo": "0.0,0.0,0.0",
        "protcoo": "3.0,0.0,0.0",
        "resnr": "1",
        "restype": "ALA",
        "reschain": "A",
        "resnr_lig": "2",
        "restype_lig": "LIG",
        "reschain_lig": "B",
    }

    cmd, marker_counter = create_interaction_commands(row, marker_counter=0, model_idces=(1, 1), config=_DUMMY_CONFIG)

    assert marker_counter == 2
    assert cmd.count("marker #1.1 position") == 2
    assert "pbond #1.1:1 #1.1:2" in cmd
    assert "name hydrogen_bond" in cmd


def test_create_interaction_commands_builds_water_bridge(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(csv2cxc.PBONDS, "water_bridge", PBONDS["Water_Bridges"])
    row = {
        "interaction_type": "water_bridge",
        "protisdon": "True",
        "ligcoo": "0.0,0.0,0.0",
        "protcoo": "3.0,0.0,0.0",
        "dist_a-w": "2.0",
        "dist_d-w": "2.5",
        "water_angle": "82.81924421854171",
        "resnr": "1",
        "restype": "ALA",
        "reschain": "A",
        "resnr_lig": "2",
        "restype_lig": "LIG",
        "reschain_lig": "B",
    }

    cmd, marker_counter = create_interaction_commands(row, marker_counter=0, model_idces=(1, 1), config=_DUMMY_CONFIG)

    assert marker_counter == 3
    assert cmd.count("marker #1.1 position") == 3
    assert cmd.count("name water_bridge") == 2


def test_create_interaction_commands_rejects_unknown_pbond_type() -> None:
    row = {
        "interaction_type": "pi_stack",
        "protisdon": "True",
        "ligcoo": "0.0,0.0,0.0",
        "protcoo": "3.0,0.0,0.0",
        "resnr": "1",
        "restype": "ALA",
        "reschain": "A",
        "resnr_lig": "2",
        "restype_lig": "LIG",
        "reschain_lig": "B",
    }

    with pytest.raises(ValueError, match="No PBOND parameters found"):
        create_interaction_commands(row, marker_counter=0, model_idces=(1, 1), config=_DUMMY_CONFIG)


def test_create_interaction_commands_accepts_plural_interaction_type_from_csv() -> None:
    row = {
        "interaction_type": "halogen_bonds",
        "ligcoo": "-1.0,2.0,3.0",
        "protcoo": "0.0,1.0,4.0",
        "resnr": "67",
        "restype": "TYR",
        "reschain": "A",
        "resnr_lig": "283",
        "restype_lig": "NFT",
        "reschain_lig": "A",
    }

    cmd, marker_counter = create_interaction_commands(row, marker_counter=0, model_idces=(1, 1), config=_DUMMY_CONFIG)

    assert marker_counter == 2
    assert "name halogen_bonds" in cmd


@pytest.mark.parametrize("issmalmol", [False, True])
def test_create_cxc_header_contains_expected_sections(issmalmol: bool) -> None:
    cfg = {
        "pdb": "protein.pdb",
        "model_id": 1,
        "receptor_chain": "A",
        "ligand_chain": "B",
        "transparency": 65,
        "issmalmol": issmalmol,
        "receptor_color": "gray",
        "ligand_color": "green",
    }

    header = create_cxc_header(cfg)
    assert header.startswith("# ChimeraX Command File\n# Generated by pliparser\nopen protein.pdb\n")
    assert "show #1/A target c\n" in header
    assert "style stick\n" in header
    if issmalmol:
        assert "show #1/B & ligand target a\n" in header
        assert "color #1 & ligand byhetero\n" in header
    else:
        assert "show #1/B target c\n" in header
        assert "color #1/B green\n" in header


def test_write_cxc_file_writes_header_and_commands(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    csv_path = tmp_path / "hydrogen_bonds.csv"
    csv_path.write_text(
        "interaction_type,ligcoo,protcoo,protisdon\nhydrogen_bond,0.0,0.0,0.0,1.0,0.0,0.0,True\n",
        encoding="UTF-8",
    )
    (tmp_path / "summary.csv").write_text("ignored,header\n", encoding="UTF-8")

    def fake_create_header(_: dict) -> str:
        return "# HEADER\n"

    def fake_create_commands(row: dict[str, str], marker_counter: int, model_idces: tuple[int, int], config: dict) -> tuple[str, int]:
        assert row["interaction_type"] == "hydrogen_bond"
        assert model_idces == (1, 1)
        assert config == {"model_id": 1}
        return f"CMD:{marker_counter}\n", marker_counter + 1

    monkeypatch.setattr(csv2cxc, "create_cxc_header", fake_create_header)
    monkeypatch.setattr(csv2cxc, "create_interaction_commands", fake_create_commands)

    out = tmp_path / "out.cxc"
    write_cxc_file(tmp_path, out, parser_config={"model_id": 1})

    content = out.read_text(encoding="UTF-8")
    assert content.startswith("# HEADER\n")
    assert "CMD:0\n" in content
    assert "rename #1.1 hydrogen_bonds\n" in content


def test_write_cxc_file_skips_summary_only(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "summary.csv").write_text("ignored\n", encoding="UTF-8")
    monkeypatch.setattr(csv2cxc, "create_cxc_header", lambda _cfg: "# HEADER\n")

    out = tmp_path / "out.cxc"
    write_cxc_file(tmp_path, out, parser_config={"model_id": 1})

    assert out.read_text(encoding="UTF-8") == "# HEADER\n"
