import json

from .classes import Key
from typing import List


def generate_keys_from_kle_json(
    json_file_path: str, step_size: float = 19.05, debug: bool = False
) -> List[Key]:
    with open(json_file_path) as fin:
        kle_keys = json.load(fin)

    half_step_size = step_size / 2

    cur_x = 0
    cur_y = 0
    width = 1
    height = 1
    rotation = 0

    # Center of rotation is top left of top-left key
    rx = -half_step_size
    ry = half_step_size

    keys = []
    i = 0
    for row in kle_keys:
        if isinstance(row, dict):
            # This is metadata
            continue

        for item in row:
            if isinstance(item, dict):
                new_rxu = item.pop("rx", None)

                if new_rxu is not None:
                    cur_x = new_rxu * step_size
                    rx = cur_x - half_step_size

                cur_x += item.pop("x", 0) * step_size

                new_ryu = item.pop("ry", None)

                if new_ryu is not None:
                    cur_y = -new_ryu * step_size
                    ry = cur_y + half_step_size

                cur_y -= item.pop("y", 0) * step_size

                width = item.pop("w", width)
                height = item.pop("h", height)
                rotation = item.pop("r", rotation)

                # Ignore label formatting
                item.pop("a", None)

                # Ignore label font sizes
                item.pop("fa", None)

                # Ignore homing
                item.pop("n", None)

                # Ignore profile
                item.pop("p", None)

                # Ignore switch type
                item.pop("sm", None)

                # Ignore switch manufacturer
                item.pop("sb", None)

                # Ignore switch model
                item.pop("st", None)

                if item:
                    print(
                        f"Unknown items in KLE JSON, please submit an issue at https://github.com/klavgen/klavgen/issues: {item}"
                    )
            else:
                key_label = item.replace("\n", " ")
                x = cur_x + (width - 1) * half_step_size
                y = cur_y - (height - 1) * half_step_size

                keys.append(Key(x=x, y=y, z=0, rotate=-rotation, rotate_around=(rx, ry)))
                if debug:
                    print(
                        f"Added {key_label} at x {x} (base {cur_x}), y {y} (base {cur_y}), rotation {-rotation} around rx {rx} ry {ry}"
                    )

                cur_x += width * step_size
                width = 1
                height = 1

        i += 1
        cur_y -= step_size
        cur_x = rx + half_step_size

    return keys
