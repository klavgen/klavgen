import cadquery as cq

from .classes import RenderedSideHolder, TrrsJack
from .config import CaseConfig, TrrsJackConfig
from .renderer_side_holder import render_holder_latches, render_side_holder
from .utils import grow_yz


def render_trrs_jack_case_cutout_and_support(
    trrs_jack: TrrsJack,
    config: TrrsJackConfig = TrrsJackConfig(),
    case_config: CaseConfig = CaseConfig(),
) -> RenderedSideHolder:
    return render_side_holder(trrs_jack, config, case_config)


def render_trrs_jack_holder(config: TrrsJackConfig = TrrsJackConfig()):
    wp = cq.Workplane("XY")

    base_width = (
        config.item_width + 2 * config.side_supports_width + 2 * config.item_width_tolerance
    )

    # Front support

    holder = wp.box(config.width, config.front_support_depth, config.holder_height, centered=False)

    # Bounding box

    wp_mid_xy = wp.center(config.width / 2, 0)
    bounding_box = wp_mid_xy.box(base_width, config.depth, config.holder_height, centered=grow_yz)

    holder = holder.union(bounding_box)

    # Cutouts

    front_hole = wp_mid_xy.box(
        config.holder_hole_width,
        config.front_support_depth,
        config.holder_height,
        centered=grow_yz,
    )

    holder = holder.cut(front_hole)

    trrs_jack = wp_mid_xy.center(0, config.front_support_depth).box(
        config.item_width + 2 * config.item_width_tolerance,
        config.item_depth + 2 * config.item_depth_tolerance,
        config.holder_height,
        centered=grow_yz,
    )

    holder = holder.cut(trrs_jack)

    back_hole = (
        wp_mid_xy.workplane(offset=config.holder_height / 2)
        .transformed(rotate=(90, 0, 0))
        .workplane(offset=-config.depth + config.back_support_depth)
        .circle(config.holder_back_hole_radius)
        .extrude(-config.holder_back_hole_depth)
    )

    holder = holder.cut(back_hole)

    # Top lips

    lip_sketch = (
        wp.transformed(rotate=(90, 0, 0))
        .lineTo(0, config.holder_bracket_lip_height)
        .lineTo(config.holder_bracket_lip_protrusion, config.holder_bracket_lip_height / 2)
        .close()
    )

    lip_base_height = config.holder_bracket_lip_height - config.holder_bracket_lip_start_before_top
    lip_start_height = config.holder_height - config.holder_bracket_lip_start_before_top

    right_lip_base = (
        wp.workplane(offset=config.holder_height)
        .center(config.rail_width, config.front_support_depth)
        .box(
            config.side_supports_width,
            config.holder_right_bracket_depth,
            lip_base_height,
            centered=False,
        )
    )

    holder = holder.union(right_lip_base)

    left_front_lip_base = (
        wp.workplane(offset=config.holder_height)
        .center(
            config.width - config.rail_width - config.side_supports_width,
            config.front_support_depth,
        )
        .box(
            config.side_supports_width,
            config.holder_left_front_bracket_depth,
            lip_base_height,
            centered=False,
        )
    )

    holder = holder.union(left_front_lip_base)

    left_back_lip_base = (
        wp.workplane(offset=config.holder_height)
        .center(
            config.width - config.rail_width - config.side_supports_width,
            config.front_support_depth
            + config.holder_left_front_bracket_depth
            + config.holder_left_bracket_gap,
        )
        .box(
            config.side_supports_width,
            config.holder_left_back_bracket_depth,
            lip_base_height,
            centered=False,
        )
    )

    holder = holder.union(left_back_lip_base)

    right_lip = lip_sketch.extrude(-config.holder_right_bracket_depth).translate(
        (
            config.rail_width + config.side_supports_width,
            config.front_support_depth,
            lip_start_height,
        )
    )

    holder = holder.union(right_lip)

    left_front_lip = (
        lip_sketch.toPending()
        .extrude(config.holder_left_front_bracket_depth)
        .rotate((0, 0, 0), (0, 0, 1), 180)
        .translate(
            (
                config.width - config.rail_width - config.side_supports_width,
                config.front_support_depth,
                lip_start_height,
            )
        )
    )

    holder = holder.union(left_front_lip)

    left_back_lip = (
        lip_sketch.toPending()
        .extrude(config.holder_left_back_bracket_depth)
        .rotate((0, 0, 0), (0, 0, 1), 180)
        .translate(
            (
                config.width - config.rail_width - config.side_supports_width,
                config.front_support_depth
                + config.holder_left_front_bracket_depth
                + config.holder_left_bracket_gap,
                lip_start_height,
            )
        )
    )

    holder = holder.union(left_back_lip)

    # Center on workplane
    holder = holder.translate((-config.width / 2, 0, 0))

    # Rail latches
    holder = holder.union(render_holder_latches(config))

    # Rotate 180 degrees to orient so USB port is on the back
    holder = holder.rotate((0, 0, 0), (0, 0, 1), 180)

    return holder


def export_trrs_jack_holder_to_stl(trrs_jack_holder):
    cq.exporters.export(trrs_jack_holder, "trrs_jack_holder.stl")


def export_trrs_jack_holder_to_step(trrs_jack_holder):
    cq.exporters.export(trrs_jack_holder, "trrs_jack_holder.step")
