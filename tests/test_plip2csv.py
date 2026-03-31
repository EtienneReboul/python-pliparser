from pathlib import Path

import pytest

from pliparser.plip2csv import iter_plip_interactions
from pliparser.plip2csv import plip2csv_stream
from pliparser.plip2csv import plip2dictlist
from pliparser.plip2csv import write2csv


def _write_report(path: Path, content: str) -> Path:
    path.write_text(content, encoding="UTF-8")
    return path


def _sample_report() -> str:
    return """Prediction of noncovalent interactions for PDB structure 1VSN
=============================================================
Created on 2026/03/31 using PLIP v3.0.0

If you are using PLIP in your work, please cite:
Schake,P. Bolz,SN. et al. PLIP 2025: introducing protein–protein interactions to the protein–ligand interaction profiler. Nucl. Acids Res. (10 May 2025), gkaf361. doi: 10.1093/nar/gkaf361
Analysis was done on model 1.

NFT:A:283 (NFT) - SMALLMOLECULE
-------------------------------
Interacting chain(s): A


**Hydrophobic Interactions**
+-------+---------+----------+-----------+-------------+--------------+------+--------------+---------------+-----------------------+-----------------------+
| RESNR | RESTYPE | RESCHAIN | RESNR_LIG | RESTYPE_LIG | RESCHAIN_LIG | DIST | LIGCARBONIDX | PROTCARBONIDX | LIGCOO                | PROTCOO               |
+=======+=========+==========+===========+=============+==============+======+==============+===============+=======================+=======================+
| 61    | ASP     | A        | 283       | NFT         | A            | 3.67 | 1639         | 448           | -7.395, 24.225, 6.614 | -6.900, 21.561, 9.090 |
+-------+---------+----------+-----------+-------------+--------------+------+--------------+---------------+-----------------------+-----------------------+
| 67    | TYR     | A        | 283       | NFT         | A            | 3.73 | 1622         | 482           | -2.692, 25.499, 5.958 | -2.449, 29.118, 6.843 |
+-------+---------+----------+-----------+-------------+--------------+------+--------------+---------------+-----------------------+-----------------------+
| 67    | TYR     | A        | 283       | NFT         | A            | 3.84 | 1636         | 481           | 3.244, 26.542, 6.729  | 0.294, 28.886, 7.491  |
+-------+---------+----------+-----------+-------------+--------------+------+--------------+---------------+-----------------------+-----------------------+
| 133   | ALA     | A        | 283       | NFT         | A            | 3.97 | 1636         | 994           | 3.244, 26.542, 6.729  | 6.575, 27.872, 5.025  |
+-------+---------+----------+-----------+-------------+--------------+------+--------------+---------------+-----------------------+-----------------------+


**Hydrogen Bonds**
+-------+---------+----------+-----------+-------------+--------------+-----------+----------+----------+-----------+-----------+----------+-----------+-------------+--------------+------------------------+-----------------------+
| RESNR | RESTYPE | RESCHAIN | RESNR_LIG | RESTYPE_LIG | RESCHAIN_LIG | SIDECHAIN | DIST_H-A | DIST_D-A | DON_ANGLE | PROTISDON | DONORIDX | DONORTYPE | ACCEPTORIDX | ACCEPTORTYPE | LIGCOO                 | PROTCOO               |
+=======+=========+==========+===========+=============+==============+===========+==========+==========+===========+===========+==========+===========+=============+==============+========================+=======================+
| 19    | GLN     | A        | 283       | NFT         | A            | True      | 2.16     | 3.11     | 160.05    | True      | 153      | Nam       | 1649        | N2           | 2.820, 18.145, 6.806   | 3.976, 15.409, 7.712  |
+-------+---------+----------+-----------+-------------+--------------+-----------+----------+----------+-----------+-----------+----------+-----------+-------------+--------------+------------------------+-----------------------+
| 25    | CYS     | A        | 283       | NFT         | A            | False     | 2.21     | 3.09     | 146.90    | True      | 183      | Nam       | 1649        | N2           | 2.820, 18.145, 6.806   | 3.306, 18.620, 9.817  |
+-------+---------+----------+-----------+-------------+--------------+-----------+----------+----------+-----------+-----------+----------+-----------+-------------+--------------+------------------------+-----------------------+
| 61    | ASP     | A        | 283       | NFT         | A            | True      | 2.26     | 2.99     | 134.61    | True      | 451      | O3        | 1645        | N3           | -9.805, 23.545, 10.596 | -9.236, 20.949, 9.223 |
+-------+---------+----------+-----------+-------------+--------------+-----------+----------+----------+-----------+-----------+----------+-----------+-------------+--------------+------------------------+-----------------------+
| 61    | ASP     | A        | 283       | NFT         | A            | True      | 1.98     | 2.99     | 170.22    | False     | 1645     | N3        | 451         | O3           | -9.805, 23.545, 10.596 | -9.236, 20.949, 9.223 |
+-------+---------+----------+-----------+-------------+--------------+-----------+----------+----------+-----------+-----------+----------+-----------+-------------+--------------+------------------------+-----------------------+
| 66    | GLY     | A        | 283       | NFT         | A            | False     | 2.33     | 3.18     | 140.42    | False     | 1631     | N3        | 473         | O2           | 0.027, 24.446, 5.449   | 0.194, 25.010, 8.576  |
+-------+---------+----------+-----------+-------------+--------------+-----------+----------+----------+-----------+-----------+----------+-----------+-------------+--------------+------------------------+-----------------------+
| 66    | GLY     | A        | 283       | NFT         | A            | False     | 2.05     | 2.95     | 150.59    | True      | 470      | Nam       | 1638        | O2           | 0.422, 22.065, 7.006   | -1.810, 23.106, 8.621 |
+-------+---------+----------+-----------+-------------+--------------+-----------+----------+----------+-----------+-----------+----------+-----------+-------------+--------------+------------------------+-----------------------+
| 158   | ASN     | A        | 283       | NFT         | A            | False     | 1.95     | 2.92     | 167.45    | False     | 1629     | Nam       | 1199        | O2           | 1.645, 21.274, 5.306   | 3.137, 21.570, 2.817  |
+-------+---------+----------+-----------+-------------+--------------+-----------+----------+----------+-----------+-----------+----------+-----------+-------------+--------------+------------------------+-----------------------+


**Halogen Bonds**
+-------+---------+----------+-----------+-------------+--------------+-----------+------+-----------+-----------+---------+-----------+---------+--------------+-----------------------+-----------------------+
| RESNR | RESTYPE | RESCHAIN | RESNR_LIG | RESTYPE_LIG | RESCHAIN_LIG | SIDECHAIN | DIST | DON_ANGLE | ACC_ANGLE | DON_IDX | DONORTYPE | ACC_IDX | ACCEPTORTYPE | LIGCOO                | PROTCOO               |
+=======+=========+==========+===========+=============+==============+===========+======+===========+===========+=========+===========+=========+==============+=======================+=======================+
| 67    | TYR     | A        | 283       | NFT         | A            | True      | 3.37 | 156.70    | 100.53    | 1627    | F         | 485     | O3           | -1.005, 26.276, 3.287 | -1.862, 29.303, 4.507 |
+-------+---------+----------+-----------+-------------+--------------+-----------+------+-----------+-----------+---------+-----------+---------+--------------+-----------------------+-----------------------+
| 157   | LEU     | A        | 283       | NFT         | A            | False     | 3.24 | 141.32    | 129.13    | 1628    | F         | 1191    | O2           | 0.124, 24.593, 2.500  | 2.348, 25.905, 0.550  |
+-------+---------+----------+-----------+-------------+--------------+-----------+------+-----------+-----------+---------+-----------+---------+--------------+-----------------------+-----------------------+
"""


def test_iter_plip_interactions_yields_rows(tmp_path: Path) -> None:
    report = _write_report(tmp_path / "report.txt", _sample_report())

    rows = list(iter_plip_interactions(report))

    assert len(rows) == 13
    interaction_type, header, row = rows[0]
    assert interaction_type == "hydrophobic_interactions"
    assert header[0] == "resnr"
    assert row["resnr"] == "61"
    assert row["restype"] == "ASP"


def test_iter_plip_interactions_raises_on_invalid_column_count(tmp_path: Path) -> None:
    invalid_report = "** Hydrogen Bonds **\n+----+\n|RESNR|RESTYPE|\n+----+\n|10|SER|A|\n\n"
    report = _write_report(tmp_path / "invalid.txt", invalid_report)

    with pytest.raises(ValueError, match="expected 2, got 3"):
        list(iter_plip_interactions(report))


def test_iter_plip_interactions_returns_on_missing_header_line(tmp_path: Path) -> None:
    truncated_report = "** Hydrogen Bonds **\n+----+\n"
    report = _write_report(tmp_path / "truncated_header.txt", truncated_report)

    assert list(iter_plip_interactions(report)) == []


def test_iter_plip_interactions_returns_on_missing_first_data_line(tmp_path: Path) -> None:
    truncated_report = "** Hydrogen Bonds **\n+----+\n|RESNR|RESTYPE|\n+----+\n"
    report = _write_report(tmp_path / "truncated_data_start.txt", truncated_report)

    assert list(iter_plip_interactions(report)) == []


def test_iter_plip_interactions_returns_on_eof_after_last_row(tmp_path: Path) -> None:
    truncated_report = "** Hydrogen Bonds **\n+----+\n|RESNR|RESTYPE|\n+----+\n|10|SER|\n"
    report = _write_report(tmp_path / "truncated_after_row.txt", truncated_report)

    rows = list(iter_plip_interactions(report))
    assert len(rows) == 1
    assert rows[0][2]["resnr"] == "10"


def test_plip2dictlist_groups_rows_by_interaction_type(tmp_path: Path) -> None:
    report = _write_report(tmp_path / "report.txt", _sample_report())

    result = plip2dictlist(report)

    assert sorted(result.keys()) == ["halogen_bonds", "hydrogen_bonds", "hydrophobic_interactions"]
    assert len(result["hydrophobic_interactions"]) == 4
    assert len(result["hydrogen_bonds"]) == 7
    assert len(result["halogen_bonds"]) == 2
    assert result["hydrophobic_interactions"][0]["restype"] == "ASP"


def test_write2csv_creates_interaction_and_summary_files(tmp_path: Path) -> None:
    report = _write_report(tmp_path / "report.txt", _sample_report())
    parsed = plip2dictlist(report)
    output_dir = tmp_path / "csv"

    write2csv(parsed, output_dir)

    hydrophobic_file = output_dir / "hydrophobic_interactions.csv"
    hydrogen_file = output_dir / "hydrogen_bonds.csv"
    halogen_file = output_dir / "halogen_bonds.csv"
    summary_file = output_dir / "summary.csv"
    assert hydrophobic_file.exists()
    assert hydrogen_file.exists()
    assert halogen_file.exists()
    assert summary_file.exists()

    hydrophobic_lines = hydrophobic_file.read_text(encoding="UTF-8").splitlines()
    hydrogen_lines = hydrogen_file.read_text(encoding="UTF-8").splitlines()
    halogen_lines = halogen_file.read_text(encoding="UTF-8").splitlines()
    summary_lines = summary_file.read_text(encoding="UTF-8").splitlines()
    assert (
        hydrophobic_lines[0] == "resnr,restype,reschain,resnr_lig,restype_lig,reschain_lig,dist,ligcarbonidx,protcarbonidx,ligcoo,protcoo"
    )
    assert hydrogen_lines[0] == (
        "resnr,restype,reschain,resnr_lig,restype_lig,reschain_lig,sidechain,dist_h-a,dist_d-a,don_angle,"
        "protisdon,donoridx,donortype,acceptoridx,acceptortype,ligcoo,protcoo"
    )
    assert halogen_lines[0] == (
        "resnr,restype,reschain,resnr_lig,restype_lig,reschain_lig,sidechain,dist,don_angle,acc_angle,"
        "don_idx,donortype,acc_idx,acceptortype,ligcoo,protcoo"
    )
    assert len(hydrogen_lines) == 8
    assert summary_lines[0] == "resnr,restype,reschain,resnr_lig,restype_lig,reschain_lig,dist,ligcoo,protcoo"
    assert len(summary_lines) == 14


def test_plip2csv_stream_writes_csv_without_buffering(tmp_path: Path) -> None:
    report = _write_report(tmp_path / "report.txt", _sample_report())
    output_dir = tmp_path / "stream"

    plip2csv_stream(report, output_dir)

    assert (output_dir / "hydrogen_bonds.csv").exists()
    assert (output_dir / "hydrophobic_interactions.csv").exists()
    assert (output_dir / "halogen_bonds.csv").exists()
    summary_lines = (output_dir / "summary.csv").read_text(encoding="UTF-8").splitlines()
    assert len(summary_lines) == 14


def test_plip2csv_stream_raises_on_inconsistent_headers(tmp_path: Path) -> None:
    inconsistent = (
        "** Hydrogen Bonds **\n"
        "+----+\n"
        "|RESNR|RESTYPE|\n"
        "+----+\n"
        "|10|SER|\n"
        "\n"
        "** Hydrogen Bonds **\n"
        "+----+\n"
        "|RESNR|RESTYPE|RESCHAIN|\n"
        "+----+\n"
        "|11|THR|A|\n"
        "\n"
    )
    report = _write_report(tmp_path / "inconsistent.txt", inconsistent)

    with pytest.raises(ValueError, match="inconsistent header"):
        plip2csv_stream(report, tmp_path / "out")
