from typing import Any

from matplotlib.figure import Figure

from .utils import Path, generate_unique_save_name, save_dict, save_fig, time_stamp


def save_all(
    name,
    path,
    data: Any | None = None,
    figs: list[Figure] | Figure | None = None,
    suffix: str = "",
    date: str | None = None,
    debug_data: str | None = None,
) -> Path:
    """
    Save the experiment's data and optional figures to disk.

    :param path: Directory path where files should be saved.
    :param figs: A list of matplotlib Figure objects to save as images.
                 If None, no figures are saved.
    :param save_format: Format for the experiment's data (e.g., 'json').
    :param suffix: Optional suffix appended to the saved filenames.
    :param save_data: If True, the experiment's data is saved; otherwise, only figures are saved.

    :return: True if saved successfully, False if `self.name` is None or an error occurs.
    """

    suffix = "" if suffix == "" else f"_{suffix}"
    timestamp = date if date else time_stamp()

    # Create directory if it does not exist
    Path(path).mkdir(parents=True, exist_ok=True)

    # Save data (JSON or other format) if requested
    path_for_data_iter = generate_unique_save_name(path, name, f"data{suffix}", timestamp, "json")
    path_for_data = next(path_for_data_iter)

    # Convert experiment data into a dictionary
    save_dict(path_for_data, data)

    # Save figures if provided
    if figs is not None:
        if isinstance(figs, Figure):
            figs = [figs]
        path_for_figs_iter = generate_unique_save_name(path, name, f"plot{suffix}", timestamp, "png")
        for fig in figs:
            path_for_fig = next(path_for_figs_iter)
            save_fig(path_for_fig, fig)

    if debug_data:
        path_for_debug = next(generate_unique_save_name(path, name, f"debug{suffix}", timestamp, "py"))
        path_for_debug.write_text(debug_data)

    return path_for_data
