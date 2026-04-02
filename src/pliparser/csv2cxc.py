import csv
import math
from pathlib import Path

from pliparser.markers import MARKERS
from pliparser.pbonds import PBONDS

_PBOND_ALIASES = {
    "hydrophobic_interactions": "Hydrophobic_Pseudobonds",
    "hydrophobic_interaction": "Hydrophobic_Pseudobonds",
    "hydrogen_bonds": "Hydrogen_Bonds",
    "hydrogen_bond": "Hydrogen_Bonds",
    "water_bridges": "Water_Bridges",
    "water_bridge": "Water_Bridges",
    "halogen_bonds": "Halogen_Bond",
    "halogen_bond": "Halogen_Bond",
    "salt_bridges": "Salt_Bridges",
    "salt_bridge": "Salt_Bridges",
    "metal_complexes": "Metal_Complex",
    "metal_complex": "Metal_Complex",
}


def _get_pbond_params(interaction_type: str):
    pbond_params = PBONDS.get(interaction_type)
    if pbond_params is not None:
        return pbond_params

    mapped_key = _PBOND_ALIASES.get(interaction_type.lower())
    if mapped_key is not None:
        return PBONDS.get(mapped_key)

    return None


def _parse_xyz(coords: str, field_name: str) -> tuple[float, float, float]:
    values = [value.strip() for value in coords.split(",")]
    if len(values) != 3:
        raise ValueError(f"Row must contain '{field_name}' as 'x,y,z'")
    return (float(values[0]), float(values[1]), float(values[2]))


def triangulate_water_coordinate(row: dict[str, str], consistency_tolerance: float = 0.35) -> tuple[float, float, float]:
    """Triangulate a 3D water position for a water-bridge interaction row.

    The function uses:
    - ``ligcoo`` and ``protcoo`` as ligand/protein interaction centers,
    - ``protisdon`` to identify donor vs acceptor,
    - ``dist_a-w`` and ``dist_d-w`` as acceptor-water and donor-water distances,
    - ``water_angle`` as the donor-water-acceptor angle in degrees.

    Because two mirrored 3D points can satisfy the same triangle constraints, this
    implementation returns a deterministic solution by choosing a fixed normal
    orientation based on global axes.
    """

    interaction_type = row.get("interaction_type", "")
    if "water_bridge" not in interaction_type:
        raise ValueError("triangulate_water_coordinate requires a water_bridge interaction row")

    ligcoo = row.get("ligcoo", "")
    protcoo = row.get("protcoo", "")
    protisdon = row.get("protisdon")
    dist_aw = row.get("dist_a-w")
    dist_dw = row.get("dist_d-w")
    water_angle = row.get("water_angle")

    if not ligcoo:
        raise ValueError("Row must contain 'ligcoo' key with coordinates")
    if not protcoo:
        raise ValueError("Row must contain 'protcoo' key with coordinates")
    if protisdon not in {"True", "False"}:
        raise ValueError("Row must contain 'protisdon' key with value 'True' or 'False'")
    if dist_aw is None:
        raise ValueError("Row must contain 'dist_a-w' key")
    if dist_dw is None:
        raise ValueError("Row must contain 'dist_d-w' key")
    if water_angle is None:
        raise ValueError("Row must contain 'water_angle' key")

    lig = _parse_xyz(ligcoo, "ligcoo")
    prot = _parse_xyz(protcoo, "protcoo")
    acceptor_water = float(dist_aw)
    donor_water = float(dist_dw)
    angle_deg = float(water_angle)

    if protisdon == "True":
        donor = prot
        acceptor = lig
    else:
        donor = lig
        acceptor = prot

    adx = donor[0] - acceptor[0]
    ady = donor[1] - acceptor[1]
    adz = donor[2] - acceptor[2]
    acceptor_donor = math.sqrt(adx * adx + ady * ady + adz * adz)
    if acceptor_donor == 0:
        raise ValueError("ligcoo and protcoo must not be identical for water triangulation")

    theta = math.radians(angle_deg)
    expected_acceptor_donor = math.sqrt(
        max(
            0.0,
            acceptor_water * acceptor_water + donor_water * donor_water - 2.0 * acceptor_water * donor_water * math.cos(theta),
        )
    )
    if abs(expected_acceptor_donor - acceptor_donor) > consistency_tolerance:
        raise ValueError("Inconsistent water-bridge geometry: distances/angle do not match ligcoo-protcoo separation")

    ux = adx / acceptor_donor
    uy = ady / acceptor_donor
    uz = adz / acceptor_donor

    x = (acceptor_water * acceptor_water - donor_water * donor_water + acceptor_donor * acceptor_donor) / (2.0 * acceptor_donor)
    radial2 = acceptor_water * acceptor_water - x * x
    if radial2 < -1e-8:
        raise ValueError("Inconsistent water-bridge geometry: no real 3D water solution")
    radial = math.sqrt(max(0.0, radial2))

    refx, refy, refz = (0.0, 0.0, 1.0)
    if abs(ux * refx + uy * refy + uz * refz) > 0.99:
        refx, refy, refz = (0.0, 1.0, 0.0)

    # Build a deterministic perpendicular basis from the donor-acceptor axis.
    nx = uy * refz - uz * refy
    ny = uz * refx - ux * refz
    nz = ux * refy - uy * refx
    n_norm = math.sqrt(nx * nx + ny * ny + nz * nz)
    if n_norm == 0:
        raise ValueError("Failed to build a stable triangulation frame")
    nx /= n_norm
    ny /= n_norm
    nz /= n_norm

    water = (
        acceptor[0] + x * ux + radial * nx,
        acceptor[1] + x * uy + radial * ny,
        acceptor[2] + x * uz + radial * nz,
    )

    return water


def get_marker_type_from_row(row: dict[str, str], entity_type: str) -> str:  # pyright: ignore[reportReturnType] # will raise no None return possible
    """
    Determine the marker type based on the interaction type in the row.

    Parameters
    ----------
    row : dict[str, str]
        A dictionary containing information about the interaction, including:
        - 'interaction_type': The type of interaction (e.g., 'hydrogen_bond').
    entity_type : str
        The entity type for which to determine the marker type (e.g., 'receptor' or 'ligand').

    Returns
    -------
    str
        The marker type corresponding to the interaction type.

    Raises
    ------
    ValueError
        If the interaction type is not recognized or does not have a corresponding marker type.
    """
    interaction_type = row.get("interaction_type")
    if interaction_type is None:
        raise ValueError("Row must contain 'interaction_type' key")

    # Map PLIP interaction types to marker types

    # For hydrogen bonds, we need to determine if it's a donor or acceptor based on the entity type and protisdon field
    if "hydrogen_bond" in interaction_type:
        if entity_type == "receptor" and row["protisdon"] == "True":
            return "hydrogen_donor"
        elif entity_type == "receptor" and row["protisdon"] == "False":
            return "hydrogen_acceptor"
        elif entity_type == "ligand" and row["protisdon"] == "True":
            return "hydrogen_acceptor"
        elif entity_type == "ligand" and row["protisdon"] == "False":
            return "hydrogen_donor"

    # For hydrophobic interactions, we can directly map to the hydrophobic marker type
    elif "hydrophobic_interaction" in interaction_type:
        return "hydrophobic"

    # For pi-stacking interactions, we can directly map to the pi_system marker type
    elif "pi_stack" in interaction_type:
        return "pi_system"

    elif "pi_cation" in interaction_type:
        if entity_type == "receptor" and row["protcharged"] == "True":
            return "positive_ion"
        elif entity_type == "receptor" and row["protcharged"] == "False":
            return "pi_system"
        elif entity_type == "ligand" and row["protcharged"] == "True":
            return "pi_system"
        elif entity_type == "ligand" and row["protcharged"] == "False":
            return "positive_ion"

    # For water bridges, we need to determine the marker type based on the entity type and protisdon field
    elif "water_bridge" in interaction_type:
        if entity_type == "water":
            return "water"
        elif entity_type == "receptor" and row["protisdon"] == "True":
            return "hydrogen_donor"
        elif entity_type == "receptor" and row["protisdon"] == "False":
            return "hydrogen_acceptor"
        elif entity_type == "ligand" and row["protisdon"] == "True":
            return "hydrogen_acceptor"
        elif entity_type == "ligand" and row["protisdon"] == "False":
            return "hydrogen_donor"

    # For salt bridges, we need to determine the marker type based on the entity type and protispos field
    elif "salt_bridge" in interaction_type:
        if entity_type == "receptor" and row["protispos"] == "True":
            return "positive_ion"
        elif entity_type == "receptor" and row["protispos"] == "False":
            return "negative_ion"
        elif entity_type == "ligand" and row["protispos"] == "True":
            return "negative_ion"
        elif entity_type == "ligand" and row["protispos"] == "False":
            return "positive_ion"

    # For halogen bonds, we need to determine the marker type based on the entity type
    elif "halogen_bond" in interaction_type:
        if entity_type == "ligand":
            return "halogen"
        else:
            return "halogen_acceptor"


def create_marker(marker_type: str, model_id: str, coords: tuple[float, float, float]) -> str:
    """
    Create a ChimeraX marker command string.

    Parameters
    ----------
    marker_type : str
        The type of marker to create. Must be a valid key in the MARKERS dictionary.
    coords : tuple[float, float, float]
        The 3D coordinates (x, y, z) for the marker position.
    model_id : str
        The ChimeraX model ID where the marker will be placed.

    Returns
    -------
    str
        A ChimeraX command string to create a marker with the specified properties.

    Raises
    ------
    ValueError
        If marker_type is not found in the MARKERS dictionary.

    Examples
    --------
    >>> cmd = create_marker('sphere', '#1.1', (10.5, 20.3, 15.7))
    >>> print(cmd)
    marker #1.1 position 10.5,20.3,15.7 radius ... color ...
    """
    marker = MARKERS.get(marker_type)
    if marker is None:
        raise ValueError(f"Unknown marker type: {marker_type}")
    chimerax_command = f"marker {model_id} "
    chimerax_command += f"position {coords[0]},{coords[1]},{coords[2]} "
    chimerax_command += f"radius {marker.radius} "
    chimerax_command += f"color {marker.color}\n"

    return chimerax_command


def create_interaction_comment(row: dict[str, str]) -> str:
    """
    Create a comment string describing an interaction between two markers.

    Parameters
    ----------
    row : dict[str, str]
        A dictionary containing information about the interaction, including:
        - 'interaction_type': The type of interaction (e.g., 'hydrogen_bond').
        - 'resnr': Residue number of the receptor.
        - 'restype': Residue type of the receptor.
        - 'reschain': Chain identifier of the receptor.
        - 'resnr_lig': Residue number of the ligand.
        - 'restype_lig': Residue type of the ligand.
        - 'reschain_lig': Chain identifier of the ligand.

    Returns
    -------
    str
        A formatted comment string describing the interaction.

    Examples
    --------
    >>> row = {
    ...     'interaction_type': 'hydrogen_bond',
    ...     'resnr': '45',
    ...     'restype': 'ARG',
    ...     'reschain': 'A',
    ...     'resnr_lig': '10',
    ...     'restype_lig': 'LIG',
    ...     'reschain_lig': 'B'
    ... }
    >>> comment = create_interaction_comment(row)
    >>> print(comment)
    # interaction between receptor hydrogen_bond: ARG45A and ligand LIG10B
    """
    interaction_type = row.get("interaction_type", "unknown_interaction")
    resnr = row.get("resnr", "unknown_resnr")
    restype = row.get("restype", "unknown_restype")
    reschain = row.get("reschain", "unknown_reschain")
    resnr_lig = row.get("resnr_lig", "unknown_resnr_lig")
    restype_lig = row.get("restype_lig", "unknown_restype_lig")
    reschain_lig = row.get("reschain_lig", "unknown_reschain_lig")

    comment = f"# interaction between receptor {interaction_type}: "
    comment += f"{restype}{resnr}{reschain} and {restype_lig}{resnr_lig}{reschain_lig}\n"

    return comment


def create_reveal_command(row: dict[str, str], model_idces: tuple[int, int], config: dict) -> str:
    """
    Create a ChimeraX command string to reveal the residues involved in an interaction.

    Parameters
    ----------
    row : dict[str, str]
        A dictionary containing information about the interaction, including:
        - 'resnr': Residue number of the receptor.
        - 'restype': Residue type of the receptor.
        - 'reschain': Chain identifier of the receptor.
        - 'resnr_lig': Residue number of the ligand.
        - 'restype_lig': Residue type of the ligand.
        - 'reschain_lig': Chain identifier of the ligand.
    model_idces : tuple[int, int]
        A tuple containing the model indices for the receptor and ligand.

    Returns
    -------
    str
        A ChimeraX command string to reveal the residues involved in the interaction.

    Examples
    --------
    >>> row = {
    ...     'resnr': '45',
    ...     'restype': 'ARG',
    ...     'reschain': 'A',
    ...     'resnr_lig': '10',
    ...     'restype_lig': 'LIG',
    ...     'reschain_lig': 'B'
    ... }
    >>> cmd = create_reveal_command(row, (1, 2))
    >>> print(cmd)
    show #1:ARG45A; show #2:LIG10B;
    """
    resnr = row.get("resnr")
    reschain = row.get("reschain")
    resnr_lig = row.get("resnr_lig")
    reschain_lig = row.get("reschain_lig")
    receptor_residue_part = "sidechain"
    if row.get("sidechain", "").strip().lower() == "false":
        receptor_residue_part = "backbone"

    # reveal the residues involved in the interaction
    cmd = ""
    if receptor_residue_part == "backbone":
        # Backbone atoms are hidden by the cartoon representation unless it is disabled.
        cmd += f"hide #{model_idces[0]}/{reschain}:{resnr} target c\n"

    cmd += f"show #{model_idces[0]}/{reschain}:{resnr} & {receptor_residue_part} target a\n"
    if not config["issmalmol"]:
        cmd += f"show #{model_idces[0]}/{reschain_lig}:{resnr_lig} & sidechain\n"

    # color
    cmd += f"color #{model_idces[0]}/{reschain}:{resnr} & {receptor_residue_part} byhetero\n"
    if not config["issmalmol"]:
        cmd += f"color #{model_idces[0]}/{reschain_lig}:{resnr_lig} & sidechain byhetero\n"

    return cmd


def create_interaction_commands(row: dict[str, str], marker_counter: int, model_idces: tuple[int, int], config: dict) -> tuple[str, int]:
    """
    Create a ChimeraX command string for an interaction between two markers.

    Parameters
    ----------
    interaction_type : str
        The type of interaction to create. Must be a valid key in the MARKERS dictionary.
    model_id : str
        The ChimeraX model ID where the interaction will be visualized.
    coords1 : tuple[float, float, float]
        The 3D coordinates (x, y, z) for the first marker position.
    coords2 : tuple[float, float, float]
        The 3D coordinates (x, y, z) for the second marker position.

    Returns
    -------
    str
        A ChimeraX command string to create an interaction between the specified markers.

    Raises
    ------
    ValueError
        If interaction_type is not found in the MARKERS dictionary or if required keys are missing from the row.
        If the geometry for a water bridge interaction is inconsistent.
        If the row does not contain necessary keys for triangulating water coordinates in a water bridge interaction.
        if the ligand and protein coordinates are identical for a water bridge interaction.
        if the ligand and protein coordinates are missing from the row.


    Examples
    --------
    >>> cmd = create_interaction_command('hydrogen_bond', '#1.1', (10.5, 20.3, 15.7), (12.0, 22.0, 18.0))
    >>> print(cmd)
    distance #1.1 at 10.5,20.3,15.7 #1.1 at 12.0,22.0,18.0 color ...
    """
    # declare local variable
    chimerax_command = create_interaction_comment(row)

    # reveal residues involved in the interaction
    chimerax_command += create_reveal_command(row, model_idces, config)

    # extract interaction type and coordinates from the row
    interaction_type = row.get("interaction_type")
    if interaction_type is None:
        raise ValueError("Row must contain 'interaction_type' key")

    # create ligand marker
    coords: str = row.get("ligcoo", "")
    if not coords:
        raise ValueError("Row must contain 'ligcoo' key with coordinates")
    coords_tuple = coords.split(",")
    coords_tuple = (float(coords_tuple[0]), float(coords_tuple[1]), float(coords_tuple[2]))
    marker_key = get_marker_type_from_row(row, entity_type="ligand")
    chimerax_command += create_marker(marker_key, f"#{model_idces[0]}.{model_idces[1]}", coords_tuple)
    marker_counter += 1

    # create receptor marker
    coords = row.get("protcoo", "")
    if not coords:
        raise ValueError("Row must contain 'protcoo' key with coordinates")
    coords_tuple = coords.split(",")
    coords_tuple = (float(coords_tuple[0]), float(coords_tuple[1]), float(coords_tuple[2]))
    marker_key = get_marker_type_from_row(row, entity_type="receptor")
    chimerax_command += create_marker(marker_key, f"#{model_idces[0]}.{model_idces[1]}", coords_tuple)
    marker_counter += 1

    if "water_bridge" in interaction_type:
        # triangulate water coordinates and create water marker
        water_coords = triangulate_water_coordinate(row)
        marker_key = get_marker_type_from_row(row, entity_type="water")
        chimerax_command += create_marker(marker_key, f"#{model_idces[0]}.{model_idces[1]}", water_coords)
        marker_counter += 1

    # create pseudo-bond command between the two markers
    pbond_params = _get_pbond_params(interaction_type)
    if pbond_params is None:
        raise ValueError(f"No PBOND parameters found for interaction type: {interaction_type}")

    chimerax_command += (
        f"pbond #{model_idces[0]}.{model_idces[1]}:{marker_counter - 1} #{model_idces[0]}.{model_idces[1]}:{marker_counter} "
    )
    chimerax_command += f"color {pbond_params.color} radius {pbond_params.radius} dashes {pbond_params.dashes} name {interaction_type}\n"

    if "water_bridge" in interaction_type:
        chimerax_command += (
            f"pbond #{model_idces[0]}.{model_idces[1]}:{marker_counter - 2} #{model_idces[0]}.{model_idces[1]}:{marker_counter - 1} "
        )
        chimerax_command += (
            f"color {pbond_params.color} radius {pbond_params.radius} dashes {pbond_params.dashes} name {interaction_type}\n"
        )

    return chimerax_command, marker_counter


def create_cxc_header(config_params: dict) -> str:
    """
    Create the header line for a ChimeraX command file.

    Returns
    -------
    str
        A string containing the header for a ChimeraX command file.
    """
    # general comment header
    header = "# ChimeraX Command File\n"
    header += "# Generated by pliparser\n"

    # open
    header += f"open {config_params['pdb']}\n"

    header += f"hide #{config_params['model_id']} target ac\n"
    header += f"show #{config_params['model_id']}/{config_params['receptor_chain']} target c\n"
    header += f"transparency #{config_params['model_id']}/{config_params['receptor_chain']} {config_params['transparency']} target c \n"
    if not config_params["issmalmol"]:
        header += f"show #{config_params['model_id']}/{config_params['ligand_chain']} target c\n"
    else:
        header += f"show #{config_params['model_id']}/{config_params['ligand_chain']} & ligand target a\n"

    # color the receptor and ligand
    header += f"color #{config_params['model_id']}/{config_params['receptor_chain']} {config_params['receptor_color']}\n"
    if not config_params["issmalmol"]:
        header += f"color #{config_params['model_id']}/{config_params['ligand_chain']} {config_params['ligand_color']}\n"
    else:
        header += f"color #{config_params['model_id']} & ligand byhetero\n"

    header += 'preset "overall look" "publication 1 (silhouettes)"\n'
    header += "style stick\n"
    return header


def write_cxc_file(input_csv_folder: Path, output_cxc: Path, parser_config: dict) -> None:
    """
    Write a list of ChimeraX command strings to a .cxc file.

    Parameters
    ----------
    commands : list[str]
        A list of ChimeraX command strings to be written to the file.
    output_cxc : Path
        The file path where the .cxc file will be created.

    Returns
    -------
    None

    Raises
    ------
    IOError
        If there is an error writing to the specified file path.
    """
    csv_list = [path for path in input_csv_folder.glob("*.csv") if "summary" not in path.name]

    with output_cxc.open("w", encoding="UTF-8") as file:
        file.write(create_cxc_header(parser_config))
        for i, csv_path in enumerate(csv_list):
            models_idces = (parser_config["model_id"], i + 1)
            markercounter = 0
            isfirst = True
            with csv_path.open("r", encoding="UTF-8") as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    cmd, markercounter = create_interaction_commands(
                        row, marker_counter=markercounter, model_idces=models_idces, config=parser_config
                    )
                    file.write(cmd)
                    if isfirst:
                        file.write(f"rename #{models_idces[0]}.{models_idces[1]} {csv_path.stem}\n")
                        isfirst = False
