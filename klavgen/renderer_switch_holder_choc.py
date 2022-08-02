import math

import cadquery as cq

from .classes import RenderedSwitchHolder
from .config import ChocSwitchHolderConfig, MXSwitchHolderConfig


def render_new_choc_switch_holder(socket, cf: ChocSwitchHolderConfig) -> RenderedSwitchHolder:
    case_config = cf.case_config
    socket_cf = cf.kailh_socket_config

    wp = cq.Workplane("XY")
    wp_yz = cq.Workplane("YZ")
    wp_xz = cq.Workplane("XZ")

    base_left_x = -9
    base_right_x = 7.5
    base_front_y = -9
    base_back_y = 6.5

    wrappers_inset_from_back_end = 0.75
    wrappers_center_y = base_back_y - wrappers_inset_from_back_end

    base_width = base_right_x - base_left_x
    base_depth = base_back_y - base_front_y
    base_height = socket_cf.socket_bump_height + 0.2  # socket_cf.socket_height +

    holder = wp.center(base_left_x, base_front_y).box(
        base_width, base_depth, base_height, centered=False
    )

    # chop off pins
    # socket_offset = socket.translate((0, 0, 1.4))
    # core_socket_bounding_box = wp.center(
    #     socket_cf.socket_left_end_x, socket_cf.socket_front_end_y
    # ).box(socket_cf.total_width, socket_cf.socket_total_depth, 5, centered=False)
    # socket_offset = socket_offset.intersect(core_socket_bounding_box)
    # holder = holder.cut(socket_offset)

    # bridge_front_right = (
    #     wp.workplane(offset=socket_cf.socket_height)
    #     .center(socket_cf.socket_right_end_x, socket_cf.socket_front_end_y)
    #     .center(-1.5, 0)
    #     .lineTo(2, 0)
    #     .lineTo(2, 1)
    #     .close()
    #     .extrude(1)
    # )
    # holder = holder.union(bridge_front_right)
    #
    # bridge_back_right = (
    #     wp.workplane(offset=socket_cf.socket_height)
    #     .center(
    #         socket_cf.socket_right_end_x - socket_cf.front_right_corner_protrusion_width,
    #         socket_cf.socket_front_end_y + socket_cf.right_depth,
    #     )
    #     .center(-1.5, 0)
    #     .lineTo(2, 0)
    #     .lineTo(2, -1)
    #     .close()
    #     .extrude(1)
    # )
    # holder = holder.union(bridge_back_right)
    #
    # bridge_front_left = (
    #     wp.workplane(offset=socket_cf.socket_height)
    #     .center(socket_cf.socket_left_end_x, socket_cf.socket_back_end_y)
    #     .lineTo(2, 0)
    #     .lineTo(0, -1)
    #     .close()
    #     .extrude(1)
    # )
    # holder = holder.union(bridge_front_left)
    #
    # bridge_back_left = (
    #     wp.workplane(offset=socket_cf.socket_height)
    #     .center(socket_cf.socket_left_end_x, socket_cf.socket_front_end_y + socket_cf.left_y_offset)
    #     .lineTo(2, 0)
    #     .lineTo(0, 1)
    #     .close()
    #     .extrude(1)
    # )
    # holder = holder.union(bridge_back_left)

    # diode_x_center = 0
    # diode_y_center = 3

    # diode_x_center = -5.5
    # diode_y_center = 2
    # diode_rotate = 0

    diode_x_center = 3.5
    diode_y_center = -2.8
    diode_rotate = 104

    # diode_holder_side_wall_width = 1
    diode_holder_side_wall_width = 1.5
    diode_holder_frontback_wall_depth = 1.5

    # diode holder
    diode_holder = (
        wp.workplane(offset=-socket_cf.socket_height)
        .box(
            4 + 2 * diode_holder_side_wall_width,
            2 + 2 * diode_holder_frontback_wall_depth,
            socket_cf.socket_height,
            centered=(True, True, False),
        )
        .rotate((0, 0, 0), (0, 0, 1), diode_rotate)
        .translate((diode_x_center, diode_y_center, 0))
    )
    holder = holder.union(diode_holder)

    diode = render_diode()

    diode = diode.rotate((0, 0, 0), (0, 0, 1), 90 + diode_rotate)
    diode = diode.translate((diode_x_center, diode_y_center, -socket_cf.socket_height))
    holder = holder.cut(diode)

    # diode front slit
    col_wire_front_slit_left = (
        wp.workplane(-socket_cf.socket_height)
        .center(base_left_x, base_front_y)
        .box(1.5, 2, socket_cf.socket_height, centered=False)
    )
    holder = holder.union(col_wire_front_slit_left)

    col_wire_front_slit_right = (
        wp.workplane(-socket_cf.socket_height)
        .center(base_left_x + 1.7, base_front_y)
        .box(2.5, 2, socket_cf.socket_height, centered=False)
    )
    holder = holder.union(col_wire_front_slit_right)

    diode_front_slit = (
        wp.workplane(-socket_cf.socket_height)
        .center(socket_cf.socket_right_end_x + 0.7, base_front_y)
        .box(3, 1.2, socket_cf.socket_height, centered=False)
    )
    holder = holder.union(diode_front_slit)

    plastic_pin_holes = render_switch_plastic_pin_holes(cf)
    holder = holder.cut(plastic_pin_holes)

    # diode_wire_cutout = wp.center(
    #     socket_cf.socket_right_end_x + socket_cf.solder_pin_width, base_front_y + 1
    # ).box(2, 3.5, base_height, centered=False)
    # holder = holder.cut(diode_wire_cutout)

    # wire_front_slit = wp.center(
    #     socket_cf.socket_right_end_x + socket_cf.solder_pin_width, base_front_y
    # ).box(0.6, 1, 1.3, centered=False)
    # holder = holder.cut(wire_front_slit)

    # cutout_slope = 0.75
    # left_sloped_cutout = (
    #     wp_xz.workplane(offset=-base_back_y)
    #     .center(base_left_x, 0)
    #     .lineTo(0, base_height)
    #     .lineTo(base_height * cutout_slope, 0)
    #     .close()
    #     .extrude(base_depth)
    # )
    # holder = holder.cut(left_sloped_cutout)

    # row_wire_clearance_depth = 3.5
    row_wire_clearance_depth = 4.5
    row_wire_clearance_height = base_height - 0.8

    row_wire_clearance_front_y = base_back_y - row_wire_clearance_depth

    row_wire_clearance = (
        wp.workplane(offset=-socket_cf.socket_height)
        .center(base_left_x, row_wire_clearance_front_y)
        .box(
            base_width,
            row_wire_clearance_depth,
            socket_cf.socket_height + row_wire_clearance_height,
            centered=False,
        )
    )
    holder = holder.cut(row_wire_clearance)

    # cutouts = (
    #     wp.workplane(-socket_cf.socket_height)
    #     .center(3.5, base_front_y)
    #     .box(10, base_depth - 4, 10, centered=False)
    # )

    # col_wire_clearance = (
    #     wp.workplane(offset=-socket_cf.socket_height)
    #     .center(socket_cf.socket_right_end_x, base_back_y - 6)
    #     .box(
    #         base_width,
    #         row_wire_clearance_depth,
    #         socket_cf.socket_height + row_wire_clearance_height,
    #         centered=False,
    #     )
    # )
    # holder = holder.cut(col_wire_clearance)

    # row_y_offset = 1.5
    row_y_offset = 3
    row_wrapper = render_wrapper_new(with_channel=False)
    # row_wrapper = row_wrapper.translate(
    #     (base_left_x + 3.5, base_back_y - row_y_offset, row_wire_clearance_height)
    # )
    row_wrapper = row_wrapper.translate(
        (base_right_x - 3.5, base_back_y - row_y_offset, row_wire_clearance_height)
    )
    holder = holder.union(row_wrapper)

    # col_y_offset = 2.75
    col_y_offset = 2.25
    col_wrapper = render_wrapper_new(with_channel=True)
    # col_wrapper = col_wrapper.translate(
    #     (base_right_x - 2, base_back_y - col_y_offset, row_wire_clearance_height)
    # )
    col_wrapper = col_wrapper.translate(
        (base_left_x + 3, base_back_y - col_y_offset, row_wire_clearance_height)
    )
    holder = holder.union(col_wrapper)

    # wrapper_left_offset_from_left_end = (base_height - row_wire_clearance_height) * cutout_slope + 1
    # wrapper_left_center_x = base_left_x + wrapper_left_offset_from_left_end
    #
    # row_wrapper_offset_from_right_end = 3
    # row_wrapper_center_x = base_right_x - row_wrapper_offset_from_right_end

    # wrappers_unsupported_center_cutout = wp.center(
    #     wrapper_left_center_x + 1, row_wire_clearance_front_y
    # ).box(
    #     (row_wrapper_center_x - 1) - (wrapper_left_center_x + 1),
    #     row_wire_clearance_depth,
    #     base_height,
    #     centered=False,
    # )
    # holder = holder.cut(wrappers_unsupported_center_cutout)
    #
    # wrapper_unsupported_right_cutout = wp.center(
    #     row_wrapper_center_x + 1, row_wire_clearance_front_y
    # ).box(
    #     base_right_x - (row_wrapper_center_x + 1),
    #     row_wire_clearance_depth,
    #     base_height,
    #     centered=False,
    # )
    # holder = holder.cut(wrapper_unsupported_right_cutout)

    # col_wrapper = render_wrapper(with_channel=True)
    # col_wrapper = col_wrapper.translate((wrapper_left_center_x, wrappers_center_y, 0))
    # # holder = holder.union(col_wrapper)
    #
    # row_wrapper = render_wrapper(with_channel=False)
    #
    # row_wrapper = row_wrapper.translate((row_wrapper_center_x, wrappers_center_y, 0))
    # # holder = holder.union(row_wrapper)

    # unnecessary vertical cutouts
    # cutouts = wp.center(wrapper_left_center_x + 1, -0.5).box(7.5, 3, base_height, centered=False)
    cutouts = (
        wp.workplane(-socket_cf.socket_height)
        .center(3.5, base_front_y)
        .box(10, base_depth - 5, 10, centered=False)
    )
    # holder = holder.cut(cutouts)

    socket = socket.translate((0, 0, -socket_cf.socket_height))
    holder = holder.cut(socket)

    # Top part
    # top_height = 0.4
    # top = (
    #     wp.workplane(offset=base_height - top_height)
    #     .rect(18, 18)
    #     .rect(13.8, 13.8)
    #     .extrude(top_height)
    # )
    # top = top.intersect(holder)
    # top = top.translate((0, 0, top_height))
    # holder = holder.union(top)

    return RenderedSwitchHolder(holder, socket)


def render_wrapper_new(with_channel: bool):
    wp = cq.Workplane("XY")

    large_width = 5
    large_depth = 2
    small_width = 3
    small_depth = 2
    height = 2.25

    channel_depth = 0.3
    channel_height = 0.8

    if with_channel:
        large_depth = 3
        small_depth = 2.5
        small_width = 2.5

    wrapper = (
        wp.workplane(offset=-height)
        .rect(large_width, large_depth)
        .workplane(offset=height)
        .rect(small_width, small_depth)
        .loft()
    )

    if with_channel:
        channel = wp.workplane(offset=-height).box(
            large_width, channel_depth, channel_height, centered=(True, True, False)
        )
        wrapper = wrapper.cut(channel)

        # col_channel = wp.workplane(offset=-height).box(channel_depth, large_depth, height, centered=(True, True, False))
        # wrapper = wrapper.cut(col_channel)

    return wrapper


def render_wrapper(with_channel: bool):
    wp = cq.Workplane("XY")
    head_width = 4
    head_depth = 3
    head_height = 1.2
    head_channel_depth = 0.8
    head_channel_height = 0.8
    neck_width = 2
    neck_depth = 1.5
    neck_height = 0.8

    head = wp.box(head_width, head_depth, head_height, centered=(True, True, False))
    neck = wp.workplane(offset=head_height).box(
        neck_width, neck_depth, neck_height, centered=(True, True, False)
    )

    wrapper = head.union(neck)
    if with_channel:
        head_channel = wp.box(
            head_width, head_channel_depth, head_channel_height, centered=(True, True, False)
        )
        wrapper = wrapper.cut(head_channel)

    return wrapper


def render_diode():
    wp = cq.Workplane("XY")

    diode_depth = 1.9  # 1.8
    diode_width = 1.8  # 1.8
    diode_length = 3.8  # 3.8
    diode_wire_diam = 0.4
    diode_wire_channel_width = 5  # 0.4
    diode_wire_length_per_side = 4

    body = wp.box(diode_width, diode_length, diode_depth)

    # Chamfer body top for lips
    body = body.edges("|Y and <Z").chamfer(0.7, 0.2)

    wire_front = (
        wp.workplane(offset=-diode_depth / 2)
        .center(0, diode_length / 2)
        .box(
            diode_wire_channel_width,
            diode_wire_length_per_side,
            diode_depth / 2 + diode_wire_diam / 2,
            centered=(True, False, False),
        )
    )
    wire_back = (
        wp.workplane(offset=-diode_depth / 2)
        .center(0, -diode_length / 2 - diode_wire_length_per_side)
        .box(
            diode_wire_channel_width,
            diode_wire_length_per_side,
            diode_depth / 2 + diode_wire_diam / 2,
            centered=(True, False, False),
        )
    )

    return body.union(wire_front).union(wire_back).translate((0, 0, diode_depth / 2))


def render_switch_plastic_pin_holes(cf: MXSwitchHolderConfig):
    wp = cq.Workplane("XY").workplane(offset=-5)

    switch_plastic_pin_hole_left = (
        wp.center(-cf.switch_side_pin_distance, cf.switch_side_pin_y)
        .circle(cf.switch_side_pin_radius)
        .extrude(20)
    )
    holes = switch_plastic_pin_hole_left

    switch_plastic_pin_hole_center = (
        wp.center(0, cf.switch_center_pin_y).circle(cf.switch_center_pin_radius).extrude(20)
    )
    holes = holes.union(switch_plastic_pin_hole_center)

    switch_plastic_pin_hole_right = (
        wp.center(cf.switch_side_pin_distance, cf.switch_side_pin_y)
        .circle(cf.switch_side_pin_radius)
        .extrude(20)
    )
    holes = holes.union(switch_plastic_pin_hole_right)

    return holes
