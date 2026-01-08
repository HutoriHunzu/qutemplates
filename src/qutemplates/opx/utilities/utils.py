from pathlib import Path
import numpy as np
from typing import Dict, Iterable, Generator, Optional, Any, Union
from dataclasses import dataclass
import matplotlib.pyplot as plt
import pickle
import json
from lmfit.model import ModelResult
from dataclasses import is_dataclass, asdict
from datetime import datetime
from pydantic import BaseModel


def ns_to_clock_cycles(duration_ns: int) -> int:
    """
    Convert nanoseconds to OPX clock cycles.

    OPX operates at 1 GHz with 4ns clock cycles. This function converts
    a duration in nanoseconds to the equivalent number of clock cycles,
    rounding to the nearest multiple of 4ns.

    Args:
        duration_ns: Duration in nanoseconds

    Returns:
        Duration in clock cycles (1 cycle = 4ns)

    Example:
        >>> ns_to_clock_cycles(1000)  # 1000ns = 250 cycles
        250
        >>> ns_to_clock_cycles(1002)  # Rounds down to 1000ns = 250 cycles
        250
    """
    return int((duration_ns // 4) * 4)


def time_stamp(fmt="%d_%m_%Y__%H_%M_%S") -> str:
    now = datetime.now()
    return now.strftime(fmt)


class JsonEncoder(json.JSONEncoder):
    def default(self, obj: Any):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            if np.iscomplexobj(obj):
                return {
                    "real part": np.real(obj).tolist(),
                    "imaginary part": np.imag(obj).tolist(),
                }
            else:
                return obj.tolist()
        elif isinstance(obj, complex):
            return {"real part": obj.real, "imaginary part": obj.imag}
        elif isinstance(obj, BaseModel):
            return obj.model_dump(mode="json")
        elif is_dataclass(obj):
            return asdict(obj)
        elif isinstance(obj, (tuple, set)):
            return list(obj)
        elif isinstance(obj, ModelResult):
            return {
                param_name: {"value": param.value, "stderr": param.stderr}
                for param_name, param in obj.params.items()
            }
        else:
            print(f"Couldn't serialize {type(obj)}. Solve it or save it as `pickle`.")
            return super(JsonEncoder, self).default(obj)


def json_save(path: Path | str, data):
    _ = json.dumps(data, cls=JsonEncoder)
    with open(Path(path).with_suffix(".json"), "w") as f:
        json.dump(data, f, indent=2, cls=JsonEncoder)


def pickle_save(path, data_obj):
    with open(Path(path).with_suffix(".json"), "wb") as f:
        pickle.dump(data_obj, f)


SAVE_FUNCTION_MAPPING = {"pickle": pickle_save, "json": json_save}

DELIMITER = "__"

FIGS = Union[Iterable[plt.Figure], plt.Figure]
AXES = Union[Iterable[plt.Axes], plt.Axes]


@dataclass
class ExperimentStatus:
    pre_run: str = "pre run"
    running: str = "running"
    running_with_live_plotting: str = "running with live plotting"
    simulating: str = "simulating"
    finished: str = "finished"
    crashed: str = "crashed"
    stopped: str = "stopped"


def convert_to_iterable(d: Any) -> Iterable[Any]:
    if not isinstance(d, Iterable):
        d = [d]
    else:
        d = np.array(d, dtype=object).flatten()
    return d


def convert_to_canonical_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    def _helper():
        for k, v in data.items():
            if not isinstance(v, dict):
                yield k, v
            else:
                v = convert_to_canonical_dict(v)
                for new_k, new_v in v.items():
                    yield DELIMITER.join([k, new_k]), new_v

    return dict(_helper())


def save_dict(path: str, data: Dict, save_format: str = "json"):
    func = SAVE_FUNCTION_MAPPING[save_format]
    validate_file_existence(path)
    func(path, data)


def save_array(path: str, data: Dict[str, Iterable]):
    # if the data is dict we want to flatten it
    canonical_data = convert_to_canonical_dict(data)
    np.savez_compressed(f"{path}.npz", **canonical_data)


def save_fig(path, fig):
    validate_file_existence(path)
    fig.savefig(path, bbox_inches="tight")


def save_figs(paths: Iterable[str], figs: FIGS):
    for path, fig in zip(paths, convert_to_iterable(figs)):
        save_fig(path, fig)


def validate_file_existence(path: str, raise_error=True) -> bool:
    """returns whether validation is OK (true) and Not Ok (false)"""

    is_exists = Path(path).is_file()
    if is_exists and raise_error:
        raise FileExistsError(f"Cannot save file at {path} as it already exists")
    return not is_exists


def generate_unique_save_name(
    path: str, name: str, suffix: str, saving_time: str, extension: Optional[str] = None
) -> Generator[str, None, None]:
    """
    returns a generator which generates full path for a file with the format of {name}_{suffix}_{saving_time}.
    each time one apply 'next' operation on the generator the file name is incremented:
        e.g.:   next(gen) --> some_name_my_suffix_22022022.txt
                next(gen) --> some_name_my_suffix_22022022_1.txt
    """
    # create the path with format
    file_path = f"{path}\\{name}_{suffix}_{saving_time}"
    increment = 0
    while True:
        incremented_file_path = f"{file_path}_{increment}" if increment > 0 else file_path
        full_path = f"{incremented_file_path}.{extension}" if extension else incremented_file_path
        yield full_path
        increment += 1
