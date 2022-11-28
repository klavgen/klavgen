import cadquery as cq

from .classes import Controller, LocationOrientation
from .config import Config
from .renderer_side_holder import render_side_case_hole_rail, render_side_mount_bracket
from .rendering import (
    RENDERERS,
    RenderedItem,
    RenderingPipelineStage,
    RenderResult,
    SeparateComponentRender,
)
from .utils import grow_yz, position


def render_controller(controller: Controller, config: Config) -> RenderResult:
    result = render_side_case_hole_rail(controller, config.controller_config, config.case_config)

    def render_in_place():
        controller_holder = render_controller_holder(config)

        controller_lr = LocationOrientation(
            x=controller.x,
            y=controller.y
            - config.case_config.case_thickness
            - config.controller_config.horizontal_tolerance,
            z=controller.z
            - config.case_config.case_base_height
            + config.case_config.case_thickness,
            rotate=controller.rotate,
            rotate_around=controller.rotate_around,
        )

        return position(controller_holder, controller_lr)

    return RenderResult(
        name=controller.name or "controller",
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
                name="controller_holder",
                render_func=lambda: render_controller_holder(config),
                render_in_place_func=render_in_place,
            )
        ],
    )


RENDERERS.set_renderer("controller", render_controller)


def render_controller_holder(config: Config = Config()):
    c_config = config.controller_config

    wp = cq.Workplane("XY")
    wp_yz = cq.Workplane("YZ")

    # Mount bracket

    holder = render_side_mount_bracket(
        config=config, side_holder_config=c_config, fill_case_wall_hole=False
    )

    # Side and back supports wrapper

    sides_and_back_support_height = (
        c_config.base_height + c_config.pcb_lips_z_from_pcb_bottom + c_config.pcb_lips_height
    )

    side_back_supports_wp = wp.center(0, c_config.holder_bracket_depth)

    side_back_supports_outer_perimeter = side_back_supports_wp.box(
        c_config.item_width + 2 * c_config.side_supports_width,
        c_config.item_depth + c_config.back_support_depth,
        sides_and_back_support_height,
        centered=grow_yz,
    )

    holder = holder.union(side_back_supports_outer_perimeter)

    # PCB hole

    pcb_hole = side_back_supports_wp.workplane(offset=c_config.base_height).box(
        c_config.item_width,
        c_config.item_depth,
        sides_and_back_support_height,
        centered=grow_yz,
    )

    holder = holder.cut(pcb_hole)

    # Base holes

    base_hole_width = (
        c_config.item_width / 2 - c_config.base_side_width - c_config.base_center_width / 2
    )
    base_hole_depth = c_config.item_depth - c_config.base_front_depth - c_config.base_back_depth

    base_hole_left = wp.center(
        -c_config.base_center_width / 2 - base_hole_width,
        c_config.holder_bracket_depth + c_config.base_front_depth,
    ).box(base_hole_width, base_hole_depth, c_config.base_height, centered=False)

    holder = holder.cut(base_hole_left)

    base_hole_right = wp.center(
        c_config.base_center_width / 2, c_config.holder_bracket_depth + c_config.base_front_depth
    ).box(base_hole_width, base_hole_depth, c_config.base_height, centered=False)

    holder = holder.cut(base_hole_right)

    # Front PCB lips

    front_pcb_lips = (
        wp_yz.workplane(offset=-c_config.item_width / 2 + c_config.pcb_lips_front_side_inset)
        .center(
            c_config.holder_bracket_depth,
            c_config.base_height + c_config.pcb_lips_z_from_pcb_bottom,
        )
        .lineTo(c_config.pcb_lips_depth, c_config.pcb_lips_depth)
        .lineTo(c_config.pcb_lips_depth, c_config.pcb_lips_height - c_config.pcb_lips_depth)
        .lineTo(0, c_config.pcb_lips_height)
        .close()
        .extrude(c_config.item_width - 2 * c_config.pcb_lips_front_side_inset)
    )

    holder = holder.union(front_pcb_lips)

    # Back PCB lips

    back_pcb_lips = (
        wp_yz.workplane(offset=-c_config.pcb_lips_back_width / 2)
        .center(
            c_config.holder_bracket_depth + c_config.item_depth,
            c_config.base_height + c_config.pcb_lips_z_from_pcb_bottom,
        )
        .lineTo(-c_config.pcb_lips_depth, c_config.pcb_lips_depth)
        .lineTo(-c_config.pcb_lips_depth, c_config.pcb_lips_height - c_config.pcb_lips_depth)
        .lineTo(0, c_config.pcb_lips_height)
        .close()
        .extrude(c_config.pcb_lips_back_width)
    )

    holder = holder.union(back_pcb_lips)

    # USB port hole on front
    usb_port_hole = wp.workplane(
        offset=c_config.base_height + c_config.usb_port_hole_start_height_from_pcb_bottom
    ).box(
        c_config.usb_port_hole_width,
        c_config.holder_bracket_depth + c_config.pcb_lips_depth,
        config.case_config.case_inner_height,
        centered=grow_yz,
    )

    holder = holder.cut(usb_port_hole)

    # Rotate 180 degrees around Z so USB port is on the back
    holder = holder.rotate((0, 0, 0), (0, 0, 1), 180)

    return holder


def export_controller_holder_to_stl(controller_holder):
    cq.exporters.export(controller_holder, "controller_holder.stl")


def export_controller_holder_to_step(controller_holder):
    cq.exporters.export(controller_holder, "controller_holder.step")
