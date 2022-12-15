import cadquery as cq

from .classes import LocationOrientation, TRRSJack
from .config import Config
from .renderer_side_holder import render_side_case_hole_rail
from .rendering import (
    RENDERERS,
    RenderedItem,
    RenderingPipelineStage,
    RenderResult,
    SeparateComponentRender,
)
from .utils import grow_yz, position


def render_trrs_jack(controller: TRRSJack, config: Config) -> RenderResult:
    result = render_side_case_hole_rail(controller, config.trrs_jack_config, config.case_config)

    def render_in_place():
        trrs_jack_holder = render_trrs_jack_holder(config)

        trrs_jack_lr = LocationOrientation(
            x=controller.x,
            y=controller.y
            - config.case_config.case_side_wall_thickness
            - config.controller_config.horizontal_tolerance,
            z=controller.z
            - config.case_config.case_base_height
            + config.case_config.case_bottom_wall_height,
            rotate=controller.rotate,
            rotate_around=controller.rotate_around,
        )

        return position(trrs_jack_holder, trrs_jack_lr)

    return RenderResult(
        name=controller.name or "trrs_jack",
        items=[
            RenderedItem(result.case_column, pipeline_stage=RenderingPipelineStage.CASE_SOLID),
            RenderedItem(
                result.rail, pipeline_stage=RenderingPipelineStage.BOTTOM_AFTER_SHELL_ADDITIONS
            ),
            RenderedItem(result.hole, pipeline_stage=RenderingPipelineStage.BOTTOM_CUTOUTS),
            RenderedItem(
                result.inner_clearance, pipeline_stage=RenderingPipelineStage.INNER_CLEARANCES
            ),
            RenderedItem(result.debug, pipeline_stage=RenderingPipelineStage.DEBUG),
        ],
        separate_components=[
            SeparateComponentRender(
                name="trrs_jack_holder",
                render_func=lambda: render_trrs_jack_holder(config),
                render_in_place_func=render_in_place,
            )
        ],
    )


RENDERERS.set_renderer("trrs_jack", render_trrs_jack)


def render_trrs_jack_holder(config: Config = Config()):
    t_config = config.trrs_jack_config

    wp = cq.Workplane("XY")

    base_width = (
        t_config.item_width + 2 * t_config.side_supports_width  # + 2 * config.item_width_tolerance
    )

    # Front support

    holder = wp.box(
        t_config.width, t_config.holder_bracket_depth, t_config.holder_height, centered=False
    )

    # Bounding box

    wp_mid_xy = wp.center(t_config.width / 2, 0)
    bounding_box = wp_mid_xy.box(
        base_width, t_config.depth, t_config.holder_height, centered=grow_yz
    )

    holder = holder.union(bounding_box)

    # Cutouts

    front_hole = wp_mid_xy.box(
        t_config.holder_hole_width,
        t_config.holder_bracket_depth,
        t_config.holder_height,
        centered=grow_yz,
    )

    holder = holder.cut(front_hole)

    trrs_jack = wp_mid_xy.center(0, t_config.holder_bracket_depth).box(
        t_config.item_width,  # + 2 * config.item_width_tolerance,
        t_config.item_depth,  # + 2 * config.item_depth_tolerance,
        t_config.holder_height,
        centered=grow_yz,
    )

    holder = holder.cut(trrs_jack)

    back_hole = (
        wp_mid_xy.workplane(offset=t_config.holder_height / 2)
        .transformed(rotate=(90, 0, 0))
        .workplane(offset=-t_config.depth + t_config.back_support_depth)
        .circle(t_config.holder_back_hole_radius)
        .extrude(-t_config.holder_back_hole_depth)
    )

    holder = holder.cut(back_hole)

    # Top lips

    lip_sketch = (
        wp.transformed(rotate=(90, 0, 0))
        .lineTo(0, t_config.holder_bracket_lip_height)
        .lineTo(t_config.holder_bracket_lip_protrusion, t_config.holder_bracket_lip_height / 2)
        .close()
    )

    lip_base_height = (
        t_config.holder_bracket_lip_height - t_config.holder_bracket_lip_start_before_top
    )
    lip_start_height = t_config.holder_height - t_config.holder_bracket_lip_start_before_top

    right_lip_base = (
        wp.workplane(offset=t_config.holder_height)
        .center(t_config.holder_bracket_width, t_config.holder_bracket_depth)
        .box(
            t_config.side_supports_width,
            t_config.holder_right_bracket_depth,
            lip_base_height,
            centered=False,
        )
    )

    holder = holder.union(right_lip_base)

    left_front_lip_base = (
        wp.workplane(offset=t_config.holder_height)
        .center(
            t_config.width - t_config.holder_bracket_width - t_config.side_supports_width,
            t_config.holder_bracket_depth,
        )
        .box(
            t_config.side_supports_width,
            t_config.holder_left_front_bracket_depth,
            lip_base_height,
            centered=False,
        )
    )

    holder = holder.union(left_front_lip_base)

    left_back_lip_base = (
        wp.workplane(offset=t_config.holder_height)
        .center(
            t_config.width - t_config.holder_bracket_width - t_config.side_supports_width,
            t_config.holder_bracket_depth
            + t_config.holder_left_front_bracket_depth
            + t_config.holder_left_bracket_gap,
        )
        .box(
            t_config.side_supports_width,
            t_config.holder_left_back_bracket_depth,
            lip_base_height,
            centered=False,
        )
    )

    holder = holder.union(left_back_lip_base)

    right_lip = lip_sketch.extrude(-t_config.holder_right_bracket_depth).translate(
        (
            t_config.holder_bracket_width + t_config.side_supports_width,
            t_config.holder_bracket_depth,
            lip_start_height,
        )
    )

    holder = holder.union(right_lip)

    left_front_lip = (
        lip_sketch.toPending()
        .extrude(t_config.holder_left_front_bracket_depth)
        .rotate((0, 0, 0), (0, 0, 1), 180)
        .translate(
            (
                t_config.width - t_config.holder_bracket_width - t_config.side_supports_width,
                t_config.holder_bracket_depth,
                lip_start_height,
            )
        )
    )

    holder = holder.union(left_front_lip)

    left_back_lip = (
        lip_sketch.toPending()
        .extrude(t_config.holder_left_back_bracket_depth)
        .rotate((0, 0, 0), (0, 0, 1), 180)
        .translate(
            (
                t_config.width - t_config.holder_bracket_width - t_config.side_supports_width,
                t_config.holder_bracket_depth
                + t_config.holder_left_front_bracket_depth
                + t_config.holder_left_bracket_gap,
                lip_start_height,
            )
        )
    )

    holder = holder.union(left_back_lip)

    # Center on workplane
    holder = holder.translate((-t_config.width / 2, 0, 0))

    # Rotate 180 degrees to orient so USB port is on the back
    holder = holder.rotate((0, 0, 0), (0, 0, 1), 180)

    return holder


def export_trrs_jack_holder_to_stl(trrs_jack_holder):
    cq.exporters.export(trrs_jack_holder, "trrs_jack_holder.stl")


def export_trrs_jack_holder_to_step(trrs_jack_holder):
    cq.exporters.export(trrs_jack_holder, "trrs_jack_holder.step")
