from typing import Any
from matplotlib.figure import Figure
from .utils import Path, generate_unique_save_name, save_dict, save_figs
from .utils import time_stamp


def save_raw(path: Path, content: str, add_timestamp: bool = True):
    # adding timen stamp before the extension
    if add_timestamp:
        path = path.with_stem(f'{path.stem}_{time_stamp()}')
    path.write_text(content)


def save_debug_script(name, path: Path | str, debug_script: str):
    Path(path).mkdir(parents=True, exist_ok=True)
    with open(Path(path, f'debug_{name}_{time_stamp()}').with_suffix('.py'), 'w') as f:
        f.write(debug_script)


def save_all(name,
             path,
             data: Any | None = None,
             figs: list[Figure] | None = None,
             save_format='json',
             suffix: str = '',
             date: str | None = None,
             debug_data: str | None = None,
             save_data: bool = True) -> bool:
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

    suffix = '' if suffix == '' else f'_{suffix}'
    timestamp = date if date else time_stamp()

    # Create directory if it does not exist
    Path(path).mkdir(parents=True, exist_ok=True)

    # Save data (JSON or other format) if requested
    path_for_data_iter = generate_unique_save_name(path, name, f'data{suffix}', timestamp)
    path_for_data_no_extension = next(path_for_data_iter)

    # Add extension manually (e.g., .json)
    path_for_data = f'{path_for_data_no_extension}.{save_format}'

    # Convert experiment data into a dictionary
    save_dict(path_for_data, data, save_format=save_format)

    # # Optionally store compressed data separately
    # data_compressed = data.pop(ExperimentConstants.DATA_COMPRESSED, None)
    # if data_compressed is not None:
    #     save_array(path_for_data_no_extension, data_compressed)

    # Save figures if provided
    if figs is not None:
        path_for_figs = generate_unique_save_name(path, name, f'plot{suffix}', timestamp, 'png')
        save_figs(path_for_figs, figs)

    if debug_data:
        path_for_debug = next(generate_unique_save_name(path, name, f'debug{suffix}', timestamp, 'py'))
        Path(path_for_debug).write_text(debug_data)


    return path_for_data
