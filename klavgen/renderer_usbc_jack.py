import cadquery as cq

from .classes import LocationOrientation, USBCJack
from .config import Config, SideHolderConfig, USBCJackConfig
from .renderer_side_holder import render_side_case_hole_rail, render_side_mount_bracket
from .rendering import (
    RENDERERS,
    RenderedItem,
    RenderingPipelineStage,
    RenderResult,
    SeparateComponentRender,
)
from .utils import grow_yz, position


def render_usbc_jack(usbc_jack: USBCJack, config: Config) -> RenderResult:
    result = render_side_case_hole_rail(usbc_jack, config.usbc_jack_config, config.case_config)

    def render_in_place():
        usbc_jack_holder = render_usbc_jack_holder(config, orient_for_printing=False)

        usbc_jack_lr = LocationOrientation(
            x=usbc_jack.x,
            y=usbc_jack.y,
            z=usbc_jack.z - config.case_config.case_base_height + config.case_config.case_thickness,
            rotate=usbc_jack.rotate,
            rotate_around=usbc_jack.rotate_around,
        )

        return position(usbc_jack_holder, usbc_jack_lr)

    return RenderResult(
        name=usbc_jack.name or "usbc_jack",
        items=[
            RenderedItem(result.case_column, pipeline_stage=RenderingPipelineStage.CASE_SOLID),
            RenderedItem(result.rail, pipeline_stage=RenderingPipelineStage.AFTER_SHELL_ADDITIONS),
            RenderedItem(result.hole, pipeline_stage=RenderingPipelineStage.BOTTOM_CUTS),
            RenderedItem(result.debug, pipeline_stage=RenderingPipelineStage.DEBUG),
        ],
        separate_components=[
            SeparateComponentRender(
                name="usbc_jack_holder",
                render_func=lambda: render_usbc_jack_holder(config, orient_for_printing=True),
                render_in_place_func=render_in_place,
            )
        ],
    )


RENDERERS.set_renderer("usbc_jack", render_usbc_jack)


def render_usbc_jack_holder(config: Config = Config(), orient_for_printing=True):
    usbc_jack_config = config.usbc_jack_config

    wp = cq.Workplane("XY")

    # Mount bracket
    holder = render_side_mount_bracket(
        config=config, side_holder_config=usbc_jack_config, fill_case_wall_hole=True
    )

    # Holder
    case_config = config.case_config
    back_wrapper = wp.center(0, usbc_jack_config.holder_bracket_depth).box(
        usbc_jack_config.base_width,
        usbc_jack_config.item_depth,
        case_config.case_inner_height - usbc_jack_config.vertical_tolerance,
        centered=grow_yz,
    )
    holder = holder.union(back_wrapper)

    # USBC jack
    offset_y = -case_config.case_thickness - config.usbc_jack_config.horizontal_tolerance

    jack_wp = wp.workplane(offset=usbc_jack_config.base_height).center(0, offset_y)
    jack_depth = (
        case_config.case_thickness
        + config.usbc_jack_config.horizontal_tolerance
        + usbc_jack_config.holder_bracket_depth
        + usbc_jack_config.item_depth
    )

    jack_center = jack_wp.box(
        usbc_jack_config.item_width - usbc_jack_config.jack_height,
        jack_depth,
        usbc_jack_config.jack_height,
        centered=grow_yz,
    )
    holder = holder.cut(jack_center)

    jack_left_side = (
        jack_wp.transformed(rotate=(90, 0, 0))
        .center(
            -usbc_jack_config.item_width / 2 + usbc_jack_config.jack_height / 2,
            usbc_jack_config.jack_height / 2,
        )
        .circle(usbc_jack_config.jack_height / 2)
        .extrude(-jack_depth)
    )
    holder = holder.cut(jack_left_side)

    jack_right_side = jack_left_side.mirror(mirrorPlane="YZ")
    holder = holder.cut(jack_right_side)

    # Chamfer back
    holder = holder.edges(
        cq.NearestToPointSelector(
            (
                0,
                usbc_jack_config.holder_bracket_depth + usbc_jack_config.item_depth,
                usbc_jack_config.base_height + usbc_jack_config.jack_height / 2,
            )
        )
    ).chamfer(0.5)

    # Rotate 180 degrees to orient so USB port is on the back
    holder = holder.rotate((0, 0, 0), (0, 0, 1), 180)

    # Move forward because part that aligns with case wall is now in positive Y
    holder = holder.translate((0, offset_y, 0))

    if orient_for_printing:
        # No need to orient
        pass

    return holder


def export_usbc_jack_holder_to_stl(usbc_jack_holder):
    cq.exporters.export(usbc_jack_holder, "usbc_jack_holder.stl")


def export_usbc_jack_holder_to_step(usbc_jack_holder):
    cq.exporters.export(usbc_jack_holder, "usbc_jack_holder.step")
