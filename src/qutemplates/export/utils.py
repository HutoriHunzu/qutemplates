import json
import pickle
from collections.abc import Generator, Iterable
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
from pydantic import BaseModel


def time_stamp(fmt="%d_%m_%Y__%H_%M_%S") -> str:
    now = datetime.now()
    return now.strftime(fmt)


class JsonEncoder(json.JSONEncoder):
    def default(self, o: Any):
        if isinstance(o, np.integer):
            return int(o)
        elif isinstance(o, np.floating):
            return float(o)
        elif isinstance(o, np.ndarray):
            if np.iscomplexobj(o):
                return {
                    "real part": np.real(o).tolist(),
                    "imaginary part": np.imag(o).tolist(),
                }
            else:
                return o.tolist()
        elif isinstance(o, complex):
            return {"real part": o.real, "imaginary part": o.imag}
        elif isinstance(o, BaseModel):
            return o.model_dump(mode="json")
        elif is_dataclass(o):
            return asdict(o)
        elif isinstance(o, (tuple, set)):
            return list(o)
        else:
            print(f"Couldn't serialize {type(o)}. Solve it or save it as `pickle`.")
            return super().default(o)


def json_save(path: Path, data):
    s = json.dumps(data, cls=JsonEncoder, indent=2)
    path.write_text(s)


def pickle_save(path, data_o):
    with open(Path(path).with_suffix(".json"), "wb") as f:
        pickle.dump(data_o, f)


SAVE_FUNCTION_MAPPING = {"pickle": pickle_save, "json": json_save}

DELIMITER = "__"


def convert_to_iterable(d: Any) -> Iterable[Any]:
    if not isinstance(d, Iterable):
        d = [d]
    else:
        d = np.array(d, dtype=object).flatten()
    return d


def convert_to_canonical_dict(data: dict[str, Any]) -> dict[str, Any]:
    def _helper():
        for k, v in data.items():
            if not isinstance(v, dict):
                yield k, v
            else:
                v = convert_to_canonical_dict(v)
                for new_k, new_v in v.items():
                    yield DELIMITER.join([k, new_k]), new_v

    return dict(_helper())


def save_dict(path: Path, data: Any, save_format: str = "json"):
    func = SAVE_FUNCTION_MAPPING[save_format]
    validate_file_existence(path)
    func(path, data)


def save_array(path: str, data: dict[str, Iterable]):
    # if the data is dict we want to flatten it
    canonical_data = convert_to_canonical_dict(data)
    np.savez_compressed(f"{path}.npz", **canonical_data)


def save_fig(path: Path, fig):
    validate_file_existence(path)
    fig.savefig(path, bbox_inches="tight")


def validate_file_existence(path: Path, raise_error=True):
    """returns whether validation is OK (true) and Not Ok (false)"""
    if path.is_file() and raise_error:
        raise FileExistsError(f"Cannot save file at {path} as it already exists")


def generate_unique_save_name(
    path: str, name: str, suffix: str, saving_time: str, extension: str | None = None
) -> Generator[Path, None, None]:
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
        yield Path(full_path)
        increment += 1


def add_time_stamp(path: Path) -> Path:
    return path.with_stem(f"{path.stem}_{time_stamp()}")
