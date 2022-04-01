import json

from .classes import Key
from .renderer_case import render_case, RenderCaseResult
from .config import Config


def generate_from_kle_json(
    json_file_path, debug: bool = False, r: RenderCaseResult = None, config: Config = Config()
):
    with open(json_file_path) as fin:
        kle_keys = json.load(fin)

    step = 19.05

    half_step = step / 2

    cur_x = 0
    cur_y = 0
    width = 1
    height = 1
    rotation = 0

    # Center of rotation is top left of top-left key
    rx = -half_step
    ry = half_step

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
                    cur_x = new_rxu * step
                    rx = cur_x - half_step

                cur_x += item.pop("x", 0) * step

                new_ryu = item.pop("ry", None)

                if new_ryu is not None:
                    cur_y = -new_ryu * step
                    ry = cur_y + half_step

                cur_y -= item.pop("y", 0) * step

                width = item.pop("w", width)
                height = item.pop("h", height)
                rotation = item.pop("r", rotation)

                # Ignore label formatting
                item.pop("a", None)

                # Ignore homing
                item.pop("n", None)

                if item:
                    raise Exception(f"Items remaining in config dict: {item} for row {row}")
            else:
                # print(item)
                key_label = item.replace("\n", " ")
                x = cur_x + (width - 1) * half_step
                y = cur_y - (height - 1) * half_step

                keys.append(Key(x=x, y=y, z=0, rotate=-rotation, rotate_around=(rx, ry)))
                if debug:
                    print(
                        f"Added {key_label} at x {x} (base {cur_x}), y {y} (base {cur_y}), rotation {-rotation} around rx {rx} ry {ry}"
                    )

                cur_x += width * step
                width = 1
                height = 1

        i += 1
        cur_y -= step
        cur_x = rx + half_step

    return render_case(keys=keys, debug=debug, result=r, config=config)
