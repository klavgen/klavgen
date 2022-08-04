import cadquery as cq

from .classes import Controller, RenderedSideHolder
from .config import CaseConfig, ControllerConfig
from .renderer_side_holder import render_holder_latches, render_side_holder
from .utils import grow_yz


def render_controller_case_cutout_and_support(
    controller: Controller,
    config: ControllerConfig = ControllerConfig(),
    case_config: CaseConfig = CaseConfig(),
) -> RenderedSideHolder:
    return render_side_holder(controller, config, case_config)


def render_controller_holder(config: ControllerConfig = ControllerConfig()):
    wp = cq.Workplane("XY")
    wp_yz = cq.Workplane("YZ")

    # Base
    base_center_width = 8
    base_height = 0.4
    base_side_width = 0.5
    base_front_depth = 2
    base_back_depth = 0.4

    # PCB lips
    pcb_lips_start_height_from_pcb_bottom = 1.2
    pcb_lips_height = 1
    pcb_lips_depth = 0.2
    pcb_lips_front_side_margin = 1
    pcb_lips_back_width = 10.6

    # USB port hole
    usb_port_hole_width = 8.8
    usb_port_hole_start_height_from_pcb_bottom = 1.2

    # Calculated
    pcb_width = config.item_width  # + 2 * config.item_width_tolerance
    pcb_depth = config.item_depth  # + 2 * config.item_depth_tolerance

    # Base

    holder = wp.box(
        pcb_width + 2 * config.side_supports_width,
        pcb_depth + config.front_support_depth + config.back_support_depth,
        base_height,
        centered=grow_yz,
    )

    base_hole_width = pcb_width / 2 - base_side_width - base_center_width / 2
    base_hole_depth = pcb_depth - base_front_depth - base_back_depth

    base_hole_left = wp.center(
        -base_center_width / 2 - base_hole_width,
        config.front_support_depth + base_front_depth,
    ).box(base_hole_width, base_hole_depth, base_height, centered=False)

    base_hole_right = wp.center(
        base_center_width / 2, config.front_support_depth + base_front_depth
    ).box(base_hole_width, base_hole_depth, base_height, centered=False)

    holder = holder.cut(base_hole_left).cut(base_hole_right)

    # Front support
    front_support = wp.box(
        config.width, config.front_support_depth, config.holder_height, centered=grow_yz
    )

    holder = holder.union(front_support)

    # PCB lips

    front_pcb_lips = (
        wp_yz.workplane(offset=-pcb_width / 2 + pcb_lips_front_side_margin)
        .center(
            config.front_support_depth,
            base_height + pcb_lips_start_height_from_pcb_bottom,
        )
        .lineTo(pcb_lips_depth, pcb_lips_depth)
        .lineTo(pcb_lips_depth, pcb_lips_height - pcb_lips_depth)
        .lineTo(0, pcb_lips_height)
        .close()
        .extrude(pcb_width - 2 * pcb_lips_front_side_margin)
    )

    holder = holder.union(front_pcb_lips)

    back_pcb_lips = (
        wp_yz.workplane(offset=-pcb_lips_back_width / 2)
        .center(
            config.front_support_depth + pcb_depth,
            base_height + pcb_lips_start_height_from_pcb_bottom,
        )
        .lineTo(-pcb_lips_depth, pcb_lips_depth)
        .lineTo(-pcb_lips_depth, pcb_lips_height - pcb_lips_depth)
        .lineTo(0, pcb_lips_height)
        .close()
        .extrude(pcb_lips_back_width)
    )

    holder = holder.union(back_pcb_lips)

    # Side and back supports
    sides_and_back_support_height = (
        base_height + pcb_lips_start_height_from_pcb_bottom + pcb_lips_height
    )

    side_back_supports_outer_shape = wp.box(
        pcb_width + 2 * config.side_supports_width,
        pcb_depth + config.front_support_depth + config.back_support_depth,
        sides_and_back_support_height,
        centered=grow_yz,
    )

    side_back_supports_inner_shape = wp.box(
        pcb_width,
        pcb_depth + config.front_support_depth,
        sides_and_back_support_height,
        centered=grow_yz,
    )

    side_back_supports = side_back_supports_outer_shape.cut(side_back_supports_inner_shape)

    holder = holder.union(side_back_supports)

    # USB port hole on front
    usb_port_hole = wp.workplane(
        offset=base_height + usb_port_hole_start_height_from_pcb_bottom
    ).box(
        usb_port_hole_width,
        config.front_support_depth + pcb_lips_depth,
        config.holder_height,
        centered=grow_yz,
    )

    holder = holder.cut(usb_port_hole)

    # Rail latches
    # holder = holder.union(render_holder_latches(config))

    # Rotate 180 degrees to orient so USB port is on the back
    holder = holder.rotate((0, 0, 0), (0, 0, 1), 180)

    return holder


def export_controller_holder_to_stl(controller_holder):
    cq.exporters.export(controller_holder, "controller_holder.stl")


def export_controller_holder_to_step(controller_holder):
    cq.exporters.export(controller_holder, "controller_holder.step")
