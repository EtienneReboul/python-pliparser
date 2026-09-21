from pathlib import Path

import pytest

import pliparser.csv2cxc as csv2cxc
from pliparser.csv2cxc import _parse_xyz
from pliparser.csv2cxc import create_cxc_header
from pliparser.csv2cxc import create_interaction_commands
from pliparser.csv2cxc import create_interaction_comment
from pliparser.csv2cxc import create_label_command
from pliparser.csv2cxc import create_marker
from pliparser.csv2cxc import create_reveal_command
from pliparser.csv2cxc import get_marker_type_from_row
from pliparser.csv2cxc import write_cxc_file
from pliparser.pbonds import PBONDS

_DUMMY_CONFIG = {"issmalmol": False}


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
        ({"interaction_type": "pi-stacking"}, "receptor", "pi_system"),
        ({"interaction_type": "pi-cation", "protcharged": "True"}, "receptor", "positive_ion"),
        ({"interaction_type": "pi-cation", "protcharged": "False"}, "ligand", "positive_ion"),
        ({"interaction_type": "water_bridge", "protisdon": "True"}, "water", "water"),
        ({"interaction_type": "water_bridge", "protisdon": "False"}, "receptor", "hydrogen_acceptor"),
        ({"interaction_type": "salt_bridge", "protispos": "True"}, "receptor", "positive_ion"),
        ({"interaction_type": "salt_bridge", "protispos": "False"}, "ligand", "positive_ion"),
        ({"interaction_type": "halogen_bond"}, "ligand", "halogen"),
        ({"interaction_type": "halogen_bond"}, "receptor", "halogen_acceptor"),
        ({"interaction_type": "metal_complexes"}, "ligand", "metal_complex"),
        ({"interaction_type": "metal_complexes"}, "receptor", "metal_binding"),
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

    assert create_interaction_comment(row) == "# interaction (hydrogen_bond): ARG45A <-> LIG10B\n"


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

    assert "hide #1/A:45 target c\n" not in cmd
    assert "show #1/A:45 & sidechain target a\n" in cmd
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

    assert "hide #1/A:45 target c\n" in cmd
    assert "color #1/A:45 & backbone byhetero\n" in cmd
    assert "show #1/B:10 & sidechain\n" in cmd
    assert "color #1/B:10 & sidechain byhetero\n" in cmd


def test_create_label_command_labels_receptor_and_ligand() -> None:
    row = {
        "resnr": "45",
        "restype": "ARG",
        "reschain": "A",
        "resnr_lig": "10",
        "restype_lig": "LIG",
        "reschain_lig": "B",
    }

    cmd = create_label_command(row, model_idces=(1, 2))

    assert cmd == 'label #1/A:45 text "ARG45A"\nlabel #1/B:10 text "LIG10B"\n'


def test_create_interaction_commands_requires_interaction_type() -> None:
    with pytest.raises(ValueError, match="Row must contain 'interaction_type' key"):
        create_interaction_commands({}, marker_counter=0, model_idces=(1, 1000), config=_DUMMY_CONFIG)


def test_create_interaction_commands_requires_ligand_coordinates() -> None:
    row = {"interaction_type": "hydrogen_bond", "protcoo": "1.0,2.0,3.0", "protisdon": "True"}
    with pytest.raises(ValueError, match="Row must contain 'ligcoo' key with coordinates"):
        create_interaction_commands(row, marker_counter=0, model_idces=(1, 1000), config=_DUMMY_CONFIG)


def test_create_interaction_commands_requires_protein_coordinates() -> None:
    row = {"interaction_type": "hydrogen_bond", "ligcoo": "1.0,2.0,3.0", "protisdon": "True"}
    with pytest.raises(ValueError, match="Row must contain 'protcoo' key with coordinates"):
        create_interaction_commands(row, marker_counter=0, model_idces=(1, 1000), config=_DUMMY_CONFIG)


def test_create_interaction_commands_requires_water_coordinates() -> None:
    row = {
        "interaction_type": "water_bridge",
        "protisdon": "True",
        "ligcoo": "0.0,0.0,0.0",
        "protcoo": "3.0,0.0,0.0",
    }
    with pytest.raises(ValueError, match="Row must contain 'watercoo' key with coordinates"):
        create_interaction_commands(row, marker_counter=0, model_idces=(1, 1000), config=_DUMMY_CONFIG)


def test_create_interaction_commands_builds_non_water_bridge(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(csv2cxc.PBONDS, "hydrogen_bonds", PBONDS["hydrogen_bonds"])
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

    cmd, marker_counter = create_interaction_commands(row, marker_counter=0, model_idces=(1, 1000), config=_DUMMY_CONFIG)

    assert marker_counter == 2
    assert cmd.count("marker #1000 position") == 2
    assert "pbond #1000:1 #1000:2" in cmd
    assert "name hydrogen_bond" in cmd


def test_create_interaction_commands_omits_labels_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(csv2cxc.PBONDS, "hydrogen_bonds", PBONDS["hydrogen_bonds"])
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

    cmd, _ = create_interaction_commands(row, marker_counter=0, model_idces=(1, 1000), config=_DUMMY_CONFIG)

    assert "label" not in cmd


def test_create_interaction_commands_includes_labels_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(csv2cxc.PBONDS, "hydrogen_bonds", PBONDS["hydrogen_bonds"])
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
    config = {"issmalmol": False, "label_residues": True}

    cmd, _ = create_interaction_commands(row, marker_counter=0, model_idces=(1, 1000), config=config)

    assert 'label #1/A:1 text "ALA1A"\n' in cmd
    assert 'label #1/B:2 text "LIG2B"\n' in cmd


def test_create_interaction_commands_builds_water_bridge(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(csv2cxc.PBONDS, "water_bridges", PBONDS["water_bridges"])
    row = {
        "interaction_type": "water_bridge",
        "protisdon": "True",
        "ligcoo": "0.0,0.0,0.0",
        "protcoo": "3.0,0.0,0.0",
        "watercoo": "1.2,0.5,-0.3",
        "resnr": "1",
        "restype": "ALA",
        "reschain": "A",
        "resnr_lig": "2",
        "restype_lig": "LIG",
        "reschain_lig": "B",
    }

    cmd, marker_counter = create_interaction_commands(row, marker_counter=0, model_idces=(1, 1000), config=_DUMMY_CONFIG)

    assert "marker #1000 position 1.2,0.5,-0.3" in cmd
    assert marker_counter == 3
    assert cmd.count("marker #1000 position") == 3
    assert cmd.count("name water_bridge") == 2
    # Markers are created in order ligand(1), receptor(2), water(3). The bridge must be
    # ligand<->water and receptor<->water, never a direct ligand<->receptor bond.
    assert "pbond #1000:2 #1000:3 " in cmd
    assert "pbond #1000:1 #1000:3 " in cmd
    assert "pbond #1000:1 #1000:2 " not in cmd


@pytest.mark.parametrize(
    ("stacking_type", "expected_color"),
    [
        ("P", "green"),
        ("T", "purple"),
    ],
)
def test_create_interaction_commands_handles_pi_stacking_annotations(stacking_type: str, expected_color: str) -> None:
    row = {
        "interaction_type": "pi-stacking",
        "type": stacking_type,
        "ligcoo": "0.0,0.0,0.0",
        "protcoo": "3.0,0.0,0.0",
        "resnr": "1",
        "restype": "ALA",
        "reschain": "A",
        "resnr_lig": "2",
        "restype_lig": "LIG",
        "reschain_lig": "B",
    }

    cmd, marker_counter = create_interaction_commands(row, marker_counter=0, model_idces=(1, 1000), config=_DUMMY_CONFIG)

    assert marker_counter == 2
    assert "name pi-stacking" in cmd
    assert f"color {expected_color}" in cmd


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

    cmd, marker_counter = create_interaction_commands(row, marker_counter=0, model_idces=(1, 1000), config=_DUMMY_CONFIG)

    assert marker_counter == 2
    assert "name halogen_bonds" in cmd


def test_create_interaction_commands_uses_metal_coordination_coordinate_fallbacks() -> None:
    row = {
        "interaction_type": "metal_complexes",
        "metalcoo": "10.0,20.0,30.0",
        "targetcoo": "40.0,50.0,60.0",
        "resnr": "67",
        "restype": "HIS",
        "reschain": "A",
        "resnr_lig": "283",
        "restype_lig": "ZN",
        "reschain_lig": "B",
    }

    cmd, marker_counter = create_interaction_commands(row, marker_counter=0, model_idces=(1, 1000), config=_DUMMY_CONFIG)

    assert marker_counter == 2
    assert "marker #1000 position 10.0,20.0,30.0" in cmd
    assert "marker #1000 position 40.0,50.0,60.0" in cmd
    assert "color lightsteelblue" in cmd
    assert "color steelblue" in cmd
    assert "name metal_complexes" in cmd


@pytest.mark.parametrize("small_molecule", [False, True])
def test_create_cxc_header_contains_expected_sections(small_molecule: bool) -> None:
    cfg = {
        "pdb": "protein.pdb",
        "model_id": 1,
        "chains": [
            {"chain": "A", "color": "gray", "transparency": 65},
            {"chain": "B", "color": "green", "small_molecule": small_molecule},
        ],
    }

    header = create_cxc_header(cfg)
    assert header.startswith("# ChimeraX Command File\n# Generated by pliparser\nopen protein.pdb\n")
    assert "close #1.1-100\n" in header
    # Marker sets live in a reserved top-level range so they never collide with the
    # receptor's own sub-models (e.g. ChimeraX's per-structure label overlay, which
    # otherwise claims "#1.1" itself). Stale marker sets from a prior run must be cleared too.
    assert f"close #{csv2cxc.MARKER_MODEL_BASE}-{csv2cxc.MARKER_MODEL_BASE + 99}\n" in header
    assert "show #1/A target c\n" in header
    assert "transparency #1/A 65 target c \n" in header
    assert "color #1/A gray\n" in header
    assert "style stick\n" in header
    if small_molecule:
        assert "show #1/B & ligand target a\n" in header
        assert "color #1/B & ligand byhetero\n" in header
    else:
        assert "show #1/B target c\n" in header
        assert "color #1/B green\n" in header


def test_create_cxc_header_supports_more_than_two_chains() -> None:
    cfg = {
        "pdb": "9kbz",
        "model_id": 1,
        "chains": [
            {"chain": "A", "color": "gray"},
            {"chain": "B", "color": "orange"},
            {"chain": "C,D", "color": "cornflowerblue", "transparency": 65},
        ],
    }

    header = create_cxc_header(cfg)

    assert "color #1/A gray\n" in header
    assert "color #1/B orange\n" in header
    assert "color #1/C,D cornflowerblue\n" in header
    assert "transparency #1/C,D 65 target c \n" in header


def test_create_cxc_header_skips_hidden_chains() -> None:
    cfg = {
        "pdb": "9kbz",
        "model_id": 1,
        "chains": [
            {"chain": "A", "color": "gray"},
            {"chain": "B", "color": "orange", "show": False},
        ],
    }

    header = create_cxc_header(cfg)

    assert "#1/B" not in header


def test_create_cxc_header_uses_marker_range_size() -> None:
    cfg = {"pdb": "9kbz", "model_id": 1, "chains": [{"chain": "A", "color": "gray"}]}

    header = create_cxc_header(cfg, marker_range_size=5)

    assert f"close #{csv2cxc.MARKER_MODEL_BASE}-{csv2cxc.MARKER_MODEL_BASE + 4}\n" in header


def test_create_cxc_header_raises_on_empty_chains() -> None:
    with pytest.raises(ValueError, match="non-empty 'chains'"):
        create_cxc_header({"pdb": "9kbz", "model_id": 1, "chains": []})


def test_create_cxc_header_raises_on_missing_color() -> None:
    cfg = {"pdb": "9kbz", "model_id": 1, "chains": [{"chain": "A"}]}
    with pytest.raises(ValueError, match="must include 'color'"):
        create_cxc_header(cfg)


_MIN_CHAINS = [{"chain": "A", "color": "gray"}]


def _write_hydrogen_bond_csv(folder: Path, name: str = "hydrogen_bonds.csv") -> Path:
    csv_path = folder / name
    csv_path.write_text(
        "interaction_type,ligcoo,protcoo,protisdon\nhydrogen_bond,0.0,0.0,0.0,1.0,0.0,0.0,True\n",
        encoding="UTF-8",
    )
    return csv_path


def test_write_cxc_file_writes_header_and_commands(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_hydrogen_bond_csv(tmp_path)
    (tmp_path / "summary.csv").write_text("ignored,header\n", encoding="UTF-8")

    def fake_create_header(_config: dict, marker_range_size: int = 100) -> str:
        return "# HEADER\n"

    def fake_create_commands(row: dict[str, str], marker_counter: int, model_idces: tuple[int, int], config: dict) -> tuple[str, int]:
        assert row["interaction_type"] == "hydrogen_bond"
        assert model_idces == (1, csv2cxc.MARKER_MODEL_BASE)
        assert config == {"issmalmol": False, "label_residues": False}
        return f"CMD:{marker_counter}\n", marker_counter + 1

    monkeypatch.setattr(csv2cxc, "create_cxc_header", fake_create_header)
    monkeypatch.setattr(csv2cxc, "create_interaction_commands", fake_create_commands)

    out = tmp_path / "out.cxc"
    config = {"model_id": 1, "chains": _MIN_CHAINS, "sources": [{"name": "main", "input": str(tmp_path)}]}
    write_cxc_file(out, config)

    content = out.read_text(encoding="UTF-8")
    assert content.startswith("# HEADER\n")
    assert "CMD:0\n" in content
    assert "rename #1000 main_hydrogen_bonds\n" in content


def test_write_cxc_file_filters_interaction_types(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    csv_path = tmp_path / "interactions.csv"
    csv_path.write_text(
        "interaction_type,ligcoo,protcoo,protisdon\n"
        "hydrogen_bond,0.0,0.0,0.0,1.0,0.0,0.0,True\n"
        "hydrophobic_interaction,0.0,0.0,0.0,1.0,0.0,0.0,\n",
        encoding="UTF-8",
    )

    seen_types: list[str] = []

    def fake_create_header(_config: dict, marker_range_size: int = 100) -> str:
        return "# HEADER\n"

    def fake_create_commands(row: dict[str, str], marker_counter: int, model_idces: tuple[int, int], config: dict) -> tuple[str, int]:
        seen_types.append(row["interaction_type"])
        return f"CMD:{row['interaction_type']}\n", marker_counter + 1

    monkeypatch.setattr(csv2cxc, "create_cxc_header", fake_create_header)
    monkeypatch.setattr(csv2cxc, "create_interaction_commands", fake_create_commands)

    out = tmp_path / "out.cxc"
    config = {"model_id": 1, "chains": _MIN_CHAINS, "sources": [{"name": "main", "input": str(tmp_path)}]}
    write_cxc_file(out, config, interaction_types={"hydrogen_bond"})

    assert seen_types == ["hydrogen_bond"]
    content = out.read_text(encoding="UTF-8")
    assert "CMD:hydrogen_bond" in content
    assert "CMD:hydrophobic_interaction" not in content


def test_write_cxc_file_with_none_filter_passes_all_rows(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    csv_path = tmp_path / "interactions.csv"
    csv_path.write_text(
        "interaction_type,ligcoo,protcoo,protisdon\n"
        "hydrogen_bond,0.0,0.0,0.0,1.0,0.0,0.0,True\n"
        "hydrophobic_interaction,0.0,0.0,0.0,1.0,0.0,0.0,\n",
        encoding="UTF-8",
    )

    seen_types: list[str] = []

    monkeypatch.setattr(csv2cxc, "create_cxc_header", lambda _config, marker_range_size=100: "# HEADER\n")
    monkeypatch.setattr(
        csv2cxc,
        "create_interaction_commands",
        lambda row, marker_counter, model_idces, config: seen_types.append(row["interaction_type"]) or ("CMD\n", marker_counter + 1),
    )

    out = tmp_path / "out.cxc"
    config = {"model_id": 1, "chains": _MIN_CHAINS, "sources": [{"name": "main", "input": str(tmp_path)}]}
    write_cxc_file(out, config, interaction_types=None)

    assert seen_types == ["hydrogen_bond", "hydrophobic_interaction"]


def test_write_cxc_file_skips_summary_only(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "summary.csv").write_text("ignored\n", encoding="UTF-8")
    monkeypatch.setattr(csv2cxc, "create_cxc_header", lambda _config, marker_range_size=100: "# HEADER\n")

    out = tmp_path / "out.cxc"
    config = {"model_id": 1, "chains": _MIN_CHAINS, "sources": [{"name": "main", "input": str(tmp_path)}]}
    write_cxc_file(out, config)

    assert out.read_text(encoding="UTF-8") == "# HEADER\n"


def test_write_cxc_file_aggregates_multiple_sources_with_collision_free_marker_ids(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source_a = tmp_path / "source_a"
    source_b = tmp_path / "source_b"
    source_a.mkdir()
    source_b.mkdir()
    _write_hydrogen_bond_csv(source_a, "hydrogen_bonds.csv")
    _write_hydrogen_bond_csv(source_a, "salt_bridges.csv")
    _write_hydrogen_bond_csv(source_b, "hydrogen_bonds.csv")

    seen_model_ids: list[int] = []

    def fake_create_commands(row: dict[str, str], marker_counter: int, model_idces: tuple[int, int], config: dict) -> tuple[str, int]:
        seen_model_ids.append(model_idces[1])
        return "CMD\n", marker_counter + 1

    monkeypatch.setattr(csv2cxc, "create_cxc_header", lambda _config, marker_range_size=100: "# HEADER\n")
    monkeypatch.setattr(csv2cxc, "create_interaction_commands", fake_create_commands)

    out = tmp_path / "out.cxc"
    config = {
        "model_id": 1,
        "chains": _MIN_CHAINS,
        "sources": [
            {"name": "alpha", "input": str(source_a)},
            {"name": "beta", "input": str(source_b)},
        ],
    }
    write_cxc_file(out, config)

    base = csv2cxc.MARKER_MODEL_BASE
    assert set(seen_model_ids) == {base, base + 1, base + 2}
    content = out.read_text(encoding="UTF-8")
    assert f"rename #{base} alpha_hydrogen_bonds\n" in content
    assert f"rename #{base + 1} alpha_salt_bridges\n" in content
    assert f"rename #{base + 2} beta_hydrogen_bonds\n" in content


def test_write_cxc_file_per_source_issmalmol_and_label_residues_differ(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source_a = tmp_path / "source_a"
    source_b = tmp_path / "source_b"
    source_a.mkdir()
    source_b.mkdir()
    _write_hydrogen_bond_csv(source_a)
    _write_hydrogen_bond_csv(source_b)

    seen_configs: list[dict] = []

    def fake_create_commands(row: dict[str, str], marker_counter: int, model_idces: tuple[int, int], config: dict) -> tuple[str, int]:
        seen_configs.append(config)
        return "CMD\n", marker_counter + 1

    monkeypatch.setattr(csv2cxc, "create_cxc_header", lambda _config, marker_range_size=100: "# HEADER\n")
    monkeypatch.setattr(csv2cxc, "create_interaction_commands", fake_create_commands)

    out = tmp_path / "out.cxc"
    config = {
        "model_id": 1,
        "chains": _MIN_CHAINS,
        "sources": [
            {"name": "alpha", "input": str(source_a), "issmalmol": False, "label_residues": False},
            {"name": "beta", "input": str(source_b), "issmalmol": True, "label_residues": True},
        ],
    }
    write_cxc_file(out, config)

    assert seen_configs == [
        {"issmalmol": False, "label_residues": False},
        {"issmalmol": True, "label_residues": True},
    ]


def test_write_cxc_file_per_source_interaction_types_filter(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source_a = tmp_path / "source_a"
    source_b = tmp_path / "source_b"
    source_a.mkdir()
    source_b.mkdir()
    for folder in (source_a, source_b):
        (folder / "interactions.csv").write_text(
            "interaction_type,ligcoo,protcoo,protisdon\n"
            "hydrogen_bond,0.0,0.0,0.0,1.0,0.0,0.0,True\n"
            "hydrophobic_interaction,0.0,0.0,0.0,1.0,0.0,0.0,\n",
            encoding="UTF-8",
        )

    seen_types: list[str] = []

    def fake_create_commands(row: dict[str, str], marker_counter: int, model_idces: tuple[int, int], config: dict) -> tuple[str, int]:
        seen_types.append(row["interaction_type"])
        return "CMD\n", marker_counter + 1

    monkeypatch.setattr(csv2cxc, "create_cxc_header", lambda _config, marker_range_size=100: "# HEADER\n")
    monkeypatch.setattr(csv2cxc, "create_interaction_commands", fake_create_commands)

    out = tmp_path / "out.cxc"
    config = {
        "model_id": 1,
        "chains": _MIN_CHAINS,
        "sources": [
            {"name": "alpha", "input": str(source_a), "interaction_types": ["hydrogen_bond"]},
            {"name": "beta", "input": str(source_b), "interaction_types": ["hydrophobic_interaction"]},
        ],
    }
    write_cxc_file(out, config)

    assert seen_types == ["hydrogen_bond", "hydrophobic_interaction"]


def test_write_cxc_file_global_interaction_types_override_all_sources(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source_a = tmp_path / "source_a"
    source_a.mkdir()
    (source_a / "interactions.csv").write_text(
        "interaction_type,ligcoo,protcoo,protisdon\n"
        "hydrogen_bond,0.0,0.0,0.0,1.0,0.0,0.0,True\n"
        "hydrophobic_interaction,0.0,0.0,0.0,1.0,0.0,0.0,\n",
        encoding="UTF-8",
    )

    seen_types: list[str] = []

    monkeypatch.setattr(csv2cxc, "create_cxc_header", lambda _config, marker_range_size=100: "# HEADER\n")
    monkeypatch.setattr(
        csv2cxc,
        "create_interaction_commands",
        lambda row, marker_counter, model_idces, config: seen_types.append(row["interaction_type"]) or ("CMD\n", marker_counter + 1),
    )

    out = tmp_path / "out.cxc"
    config = {
        "model_id": 1,
        "chains": _MIN_CHAINS,
        "sources": [{"name": "alpha", "input": str(source_a), "interaction_types": ["hydrogen_bond"]}],
    }
    write_cxc_file(out, config, interaction_types={"hydrophobic_interaction"})

    assert seen_types == ["hydrophobic_interaction"]


def test_write_cxc_file_global_label_residues_override_all_sources(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source_a = tmp_path / "source_a"
    source_a.mkdir()
    _write_hydrogen_bond_csv(source_a)

    seen_configs: list[dict] = []

    monkeypatch.setattr(csv2cxc, "create_cxc_header", lambda _config, marker_range_size=100: "# HEADER\n")
    monkeypatch.setattr(
        csv2cxc,
        "create_interaction_commands",
        lambda row, marker_counter, model_idces, config: seen_configs.append(config) or ("CMD\n", marker_counter + 1),
    )

    out = tmp_path / "out.cxc"
    config = {
        "model_id": 1,
        "chains": _MIN_CHAINS,
        "sources": [{"name": "alpha", "input": str(source_a), "label_residues": False}],
    }
    write_cxc_file(out, config, label_residues_override=True)

    assert seen_configs[0]["label_residues"] is True


def test_write_cxc_file_raises_on_missing_sources(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="non-empty 'sources'"):
        write_cxc_file(tmp_path / "out.cxc", {"model_id": 1, "chains": _MIN_CHAINS})


def test_write_cxc_file_raises_on_duplicate_source_names(tmp_path: Path) -> None:
    config = {
        "model_id": 1,
        "chains": _MIN_CHAINS,
        "sources": [
            {"name": "dup", "input": str(tmp_path)},
            {"name": "dup", "input": str(tmp_path)},
        ],
    }
    with pytest.raises(ValueError, match="unique 'name'"):
        write_cxc_file(tmp_path / "out.cxc", config)


def test_write_cxc_file_raises_on_source_missing_input(tmp_path: Path) -> None:
    config = {"model_id": 1, "chains": _MIN_CHAINS, "sources": [{"name": "alpha"}]}
    with pytest.raises(ValueError, match="missing 'input'"):
        write_cxc_file(tmp_path / "out.cxc", config)
