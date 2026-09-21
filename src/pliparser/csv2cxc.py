import csv
from pathlib import Path
from typing import Union

from pliparser.markers import MARKERS
from pliparser.pbonds import PBONDS
from pliparser.pbonds import PseudobondParamsBase

# Top-level model id where per-interaction-type marker sets start. Markers must NOT be
# nested as sub-models of the receptor structure (e.g. "#1.1"): ChimeraX itself claims
# low sub-model numbers under a structure for its own overlays (e.g. residue/atom labels
# land on "#1.1" the first time something on model #1 is labeled), so reusing that space
# for our marker sets causes "Cannot create a marker set #1.1 with same model id as
# another model" and aborts the rest of the command script. Using a reserved top-level
# range instead avoids colliding with both the receptor model and its auto-created children.
MARKER_MODEL_BASE = 1000


def _get_pbond_params(interaction_type: str, type: Union[str, None] = None) -> Union[PseudobondParamsBase, None]:
    # type must be taken into account for pi-stacking interactions to determine the correct parallel vs perpendicular style
    if type is not None:
        if "pi-stacking" in interaction_type:
            if type == "P":
                return PBONDS.get("pi-stacking_parallel")
            elif type == "T":
                return PBONDS.get("pi-stacking_perpendicular")
            else:
                raise ValueError(f"Unknown pi-stacking type: {type}")
    pbond_params = PBONDS.get(interaction_type)
    if pbond_params is not None:
        return pbond_params

    normalized_type = interaction_type.lower()
    suffix_replacements = {
        "_interaction": "_interactions",
        "_bond": "_bonds",
        "_bridge": "_bridges",
        "_complex": "_complexes",
    }
    for suffix, replacement in suffix_replacements.items():
        if normalized_type.endswith(suffix):
            normalized_type = normalized_type[: -len(suffix)] + replacement
            break

    pbond_params = PBONDS.get(normalized_type)
    if pbond_params is not None:
        return pbond_params

    return None


def _parse_xyz(coords: str, field_name: str) -> tuple[float, float, float]:
    values = [value.strip() for value in coords.split(",")]
    if len(values) != 3:
        raise ValueError(f"Row must contain '{field_name}' as 'x,y,z'")
    return (float(values[0]), float(values[1]), float(values[2]))


def get_marker_type_from_row(row: dict[str, str], entity_type: str) -> str:  # pyright: ignore[reportReturnType] # will raise no None return possible
    """
    Determine the marker type based on the interaction type in the row.

    ``entity_type`` ('receptor'/'ligand'/'water') describes which side of a single PLIP
    CSV row a residue is on, per PLIP's own report schema (unsuffixed columns = receptor
    side, ``_lig``-suffixed columns = ligand side). This is independent of, and unrelated
    to, the visualization-layer "primary"/"partner" chain styling used elsewhere in this
    module (see ``create_cxc_header``) -- a single PLIP run always has exactly two sides,
    regardless of how many chains the resulting ``.cxc`` file ends up coloring.

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
    elif "pi-stacking" in interaction_type:
        return "pi_system"

    elif "pi-cation" in interaction_type:
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

    # For metal complexes, map ligand metal to the metal center marker
    # and receptor partner to the metal-binding marker.
    elif "metal_complexes" in interaction_type:
        if entity_type == "ligand":
            return "metal_complex"
        else:
            return "metal_binding"
    else:
        raise ValueError(f"Unknown interaction type: {interaction_type}")


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
    # interaction (hydrogen_bond): ARG45A <-> LIG10B
    """
    interaction_type = row.get("interaction_type", "unknown_interaction")
    resnr = row.get("resnr", "unknown_resnr")
    restype = row.get("restype", "unknown_restype")
    reschain = row.get("reschain", "unknown_reschain")
    resnr_lig = row.get("resnr_lig", "unknown_resnr_lig")
    restype_lig = row.get("restype_lig", "unknown_restype_lig")
    reschain_lig = row.get("reschain_lig", "unknown_reschain_lig")

    comment = f"# interaction ({interaction_type}): "
    comment += f"{restype}{resnr}{reschain} <-> {restype_lig}{resnr_lig}{reschain_lig}\n"

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


def create_label_command(row: dict[str, str], model_idces: tuple[int, int]) -> str:
    """
    Create a ChimeraX command string to label the receptor and ligand residues involved in an interaction.

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
        A ChimeraX command string that labels the receptor and ligand residues.

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
    >>> cmd = create_label_command(row, (1, 2))
    >>> print(cmd)
    label #1/A:45 text "ARG45A"
    label #1/B:10 text "LIG10B"
    """
    resnr = row.get("resnr")
    restype = row.get("restype")
    reschain = row.get("reschain")
    resnr_lig = row.get("resnr_lig")
    restype_lig = row.get("restype_lig")
    reschain_lig = row.get("reschain_lig")

    cmd = f'label #{model_idces[0]}/{reschain}:{resnr} text "{restype}{resnr}{reschain}"\n'
    cmd += f'label #{model_idces[0]}/{reschain_lig}:{resnr_lig} text "{restype_lig}{resnr_lig}{reschain_lig}"\n'
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

    # label residues involved in the interaction
    if config.get("label_residues"):
        chimerax_command += create_label_command(row, model_idces)

    # extract interaction type and coordinates from the row
    interaction_type = row.get("interaction_type")
    if interaction_type is None:
        raise ValueError("Row must contain 'interaction_type' key")

    # create ligand marker
    coords: str = row.get("ligcoo", "")
    if not coords:
        coords = row.get("metalcoo", "")
    if not coords:
        raise ValueError("Row must contain 'ligcoo' key with coordinates")
    coords_tuple = coords.split(",")
    coords_tuple = (float(coords_tuple[0]), float(coords_tuple[1]), float(coords_tuple[2]))
    marker_key = get_marker_type_from_row(row, entity_type="ligand")
    chimerax_command += create_marker(marker_key, f"#{model_idces[1]}", coords_tuple)
    marker_counter += 1

    # create receptor marker
    coords = row.get("protcoo", "")
    if not coords:
        coords = row.get("targetcoo", "")
    if not coords:
        raise ValueError("Row must contain 'protcoo' key with coordinates")
    coords_tuple = coords.split(",")
    coords_tuple = (float(coords_tuple[0]), float(coords_tuple[1]), float(coords_tuple[2]))
    marker_key = get_marker_type_from_row(row, entity_type="receptor")
    chimerax_command += create_marker(marker_key, f"#{model_idces[1]}", coords_tuple)
    marker_counter += 1

    if "water_bridge" in interaction_type:
        # PLIP's report already includes the water molecule's own coordinates
        # (the WATERCOO column), so use them directly instead of reconstructing
        # them from distances/angle.
        watercoo = row.get("watercoo", "")
        if not watercoo:
            raise ValueError("Row must contain 'watercoo' key with coordinates for water_bridge interactions")
        water_coords = _parse_xyz(watercoo, "watercoo")
        marker_key = get_marker_type_from_row(row, entity_type="water")
        chimerax_command += create_marker(marker_key, f"#{model_idces[1]}", water_coords)
        marker_counter += 1

    # create pseudo-bond command between the two markers
    if interaction_type == "pi-stacking":
        pbond_params = _get_pbond_params(interaction_type, row.get("type"))
    else:
        pbond_params = _get_pbond_params(interaction_type)
    if pbond_params is None:
        raise ValueError(f"No PBOND parameters found for interaction type: {interaction_type}")

    chimerax_command += f"pbond #{model_idces[1]}:{marker_counter - 1} #{model_idces[1]}:{marker_counter} "
    chimerax_command += f"color {pbond_params.color} radius {pbond_params.radius} dashes {pbond_params.dashes} name {interaction_type}\n"

    if "water_bridge" in interaction_type:
        # The generic pbond above already connects receptor-water (the last two
        # markers created). Add the missing ligand-water leg here so the bridge
        # is ligand<->water<->receptor instead of a direct ligand-receptor bond.
        chimerax_command += f"pbond #{model_idces[1]}:{marker_counter - 2} #{model_idces[1]}:{marker_counter} "
        chimerax_command += (
            f"color {pbond_params.color} radius {pbond_params.radius} dashes {pbond_params.dashes} name {interaction_type}\n"
        )

    return chimerax_command, marker_counter


def create_cxc_header(config_params: dict, marker_range_size: int = 100) -> str:
    """
    Create the header line for a ChimeraX command file.

    Each entry in ``config_params['chains']`` gets its own show/hide, transparency, and
    color, instead of the structure being split into a single receptor/ligand pair. This
    lets a structure with more than two biologically distinct chains (e.g. a
    protein-protein-RNA complex) have every chain styled independently.

    Parameters
    ----------
    config_params : dict
        Must contain 'pdb', 'model_id', and a non-empty 'chains' list. Each chain entry
        is a dict with keys:
        - 'chain' (required): a ChimeraX atom-spec chain string, e.g. 'A' or 'C,D'.
        - 'color' (required unless 'small_molecule' is true): the chain's color.
        - 'transparency' (optional, default 0): percent transparency for the chain.
        - 'show' (optional, default True): whether to reveal the chain at all.
        - 'small_molecule' (optional, default False): show only ligand atoms colored
          by heteroatom instead of the whole chain in an explicit color.
    marker_range_size : int
        Size of the reserved marker-set model-id range to clear at the top of the file.
        Must be at least as large as the total number of marker sets that will be
        created across all sources.

    Returns
    -------
    str
        A string containing the header for a ChimeraX command file.

    Raises
    ------
    ValueError
        If 'chains' is missing/empty, or a chain entry is missing 'chain', or a
        non-small-molecule chain entry is missing 'color'.
    """
    # general comment header
    header = "# ChimeraX Command File\n"
    header += "# Generated by pliparser\n"

    model_id = config_params["model_id"]

    # open
    header += f"open {config_params['pdb']}\n"
    header += f"close #{model_id}.1-100\n"  # in case there is some sub models in the pdb (e.g. NMR ensembles)
    # Clear any marker sets left over from a previous run of this script in the same session.
    header += f"close #{MARKER_MODEL_BASE}-{MARKER_MODEL_BASE + marker_range_size - 1}\n"

    header += f"hide #{model_id} target ac\n"

    chains = config_params.get("chains")
    if not chains:
        raise ValueError("config must include a non-empty 'chains' list")

    for chain_cfg in chains:
        chain = chain_cfg.get("chain")
        if not chain:
            raise ValueError("each chain entry must include a 'chain' key")
        if not chain_cfg.get("show", True):
            continue

        if chain_cfg.get("small_molecule", False):
            header += f"show #{model_id}/{chain} & ligand target a\n"
            header += f"color #{model_id}/{chain} & ligand byhetero\n"
        else:
            if "color" not in chain_cfg:
                raise ValueError(f"chain '{chain}' must include 'color' unless 'small_molecule' is true")
            transparency = chain_cfg.get("transparency", 0)
            header += f"show #{model_id}/{chain} target c\n"
            header += f"transparency #{model_id}/{chain} {transparency} target c \n"
            header += f"color #{model_id}/{chain} {chain_cfg['color']}\n"

    header += 'preset "overall look" "publication 1 (silhouettes)"\n'
    header += "style stick\n"
    return header


def write_cxc_file(
    output_cxc: Path,
    config: dict,
    interaction_types: Union[set[str], None] = None,
    label_residues_override: Union[bool, None] = None,
) -> None:
    """
    Write ChimeraX command strings aggregated from one or more PLIP CSV sources to a .cxc file.

    Parameters
    ----------
    output_cxc : Path
        The file path where the .cxc file will be created.
    config : dict
        Must contain 'pdb', 'model_id', a non-empty 'chains' list (see
        ``create_cxc_header``), and a non-empty 'sources' list. Each source entry is a
        dict with keys:
        - 'name' (required): a unique label, used to prefix marker-set 'rename' commands
          so that identical interaction-type filenames from different sources don't
          collide (e.g. two sources both producing 'hydrogen_bonds.csv').
        - 'input' (required): directory containing that source's interaction CSV files.
        - 'issmalmol' (optional, default False): whether this source's ligand side is a
          small molecule, controlling per-row sidechain-reveal behavior.
        - 'label_residues' (optional, default False): add text labels for this source's
          interactions.
        - 'interaction_types' (optional, default None): substring filter restricting
          this source's rows to the given interaction types.
    interaction_types : set[str], optional
        Global interaction-type filter. When given, it overrides every source's own
        'interaction_types'.
    label_residues_override : bool, optional
        Global label_residues override. When given, it overrides every source's own
        'label_residues'.

    Returns
    -------
    None

    Raises
    ------
    ValueError
        If 'sources' is missing/empty, source names are missing/duplicated, or a source
        is missing 'input'.
    IOError
        If there is an error writing to the specified file path.
    """
    sources = config.get("sources")
    if not sources:
        raise ValueError("config must include a non-empty 'sources' list")

    names = [source.get("name") for source in sources]
    if any(name is None for name in names) or len(set(names)) != len(names):
        raise ValueError("every source must have a unique 'name'")

    flattened: list[tuple[dict, Path]] = []
    for source in sources:
        if "input" not in source:
            raise ValueError(f"source '{source.get('name')}' is missing 'input'")
        csv_list = sorted(path for path in Path(source["input"]).glob("*.csv") if "summary" not in path.name)
        flattened.extend((source, csv_path) for csv_path in csv_list)

    with output_cxc.open("w", encoding="UTF-8") as file:
        file.write(create_cxc_header(config, marker_range_size=max(100, len(flattened))))
        for flat_index, (source, csv_path) in enumerate(flattened):
            model_idces = (config["model_id"], MARKER_MODEL_BASE + flat_index)
            source_types = (
                interaction_types
                if interaction_types is not None
                else (set(source["interaction_types"]) if source.get("interaction_types") else None)
            )
            source_label_residues = label_residues_override if label_residues_override is not None else source.get("label_residues", False)
            source_config = {
                "issmalmol": source.get("issmalmol", False),
                "label_residues": source_label_residues,
            }
            markercounter = 0
            isfirst = True
            with csv_path.open("r", encoding="UTF-8") as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if source_types is not None and not any(t in row.get("interaction_type", "") for t in source_types):
                        continue
                    cmd, markercounter = create_interaction_commands(
                        row, marker_counter=markercounter, model_idces=model_idces, config=source_config
                    )
                    file.write(cmd)
                    if isfirst:
                        file.write(f"rename #{model_idces[1]} {source['name']}_{csv_path.stem}\n")
                        isfirst = False
