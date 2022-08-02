import math

import cadquery as cq

from .classes import RenderedSwitchHolder
from .config import ChocSwitchHolderConfig, MXSwitchHolderConfig


def render_new_choc_switch_holder(socket, cf: ChocSwitchHolderConfig) -> RenderedSwitchHolder:
    case_config = cf.case_config
    socket_cf = cf.kailh_socket_config
    key_cf = cf.key_config

    wp = cq.Workplane("XY")

    base_left_x = -9.2
    base_right_x = 8
    base_front_y = -8.1
    base_back_y = 8.1

    base_width = base_right_x - base_left_x
    base_depth = base_back_y - base_front_y
    base_height = 1

    # Base
    holder = (
        wp.workplane(offset=-base_height)
        .center(base_left_x, base_front_y)
        .box(base_width, base_depth, base_height, centered=False)
    )

    holder_cutout = (
        wp.center(base_left_x - 5, base_front_y - 5)
        .rect(base_width + 10, base_depth + 10, centered=False)
        .center(5, 5)
        .rect(base_width, base_depth, centered=False)
        .extrude(10)
    )

    # Switch holder wall
    wall_size = 2
    extra_switch_bottom_buffer_height = 0.4

    wall_height = (
        socket_cf.socket_height
        + socket_cf.socket_bump_height
        + cf.switch_bottom_buffer_height
        + extra_switch_bottom_buffer_height
        + cf.switch_bottom_height
    )

    wall = (
        wp.rect(key_cf.switch_width, key_cf.switch_depth)
        .rect(key_cf.switch_width + wall_size * 2, key_cf.switch_depth + wall_size * 2)
        .extrude(wall_height)
    )

    holder = holder.union(wall)

    # Socket supports

    # socket_support_left = (
    #     wp.center(-key_cf.switch_width / 2 - wall_size - 0.8, -6)
    #     .rect(1, 6 + base_back_y, centered=False)
    #     .extrude(wall_height)
    # )
    # holder = holder.union(socket_support_left)

    socket_support_back = wp.center(-1, -2.5).rect(6, 4).extrude(socket_cf.socket_height)
    holder = holder.union(socket_support_back)

    # socket_support_front_right = (
    #     wp.center(-key_cf.switch_width / 2 - wall_size, base_front_y)
    #     .rect(7, 3, centered=False)
    #     .extrude(wall_height)
    # )
    # holder = holder.union(socket_support_front_right)

    # Column (=left) wire wrappers
    # col_wrapper, col_clearance = render_wrapper_new(2, 2, 1, 1, 1, 1)
    #
    # col_wrapper_front_clearance = col_clearance.translate((base_left_x + 1, base_front_y + 1.25, 0))
    # holder = holder.cut(col_wrapper_front_clearance)
    #
    # col_wrapper_front = col_wrapper.translate((base_left_x + 1, base_front_y + 1.25, 0))
    # holder = holder.union(col_wrapper_front)

    front_center_support_width = 5

    # Column wire slit
    column_wire_slit_left_x = -front_center_support_width / 2 - 0.5
    column_wire_slit = wp.center(column_wire_slit_left_x, 0).box(
        0.5, 20, 10, centered=(False, True, False)
    )
    holder = holder.cut(column_wire_slit)

    # Column wrapper
    row_wire_cutout_y = 3.15
    back_left_corner_width = column_wire_slit_left_x - (-key_cf.switch_width / 2 - wall_size)
    back_left_corner_depth = base_back_y - row_wire_cutout_y

    back_left_corner = (
        wp.center(-key_cf.switch_width / 2 - wall_size, row_wire_cutout_y)
        .rect(back_left_corner_width, back_left_corner_depth, centered=False)
        .extrude(4)
    )
    back_left_corner_chamfered = back_left_corner.edges("<Z").chamfer(1.4, 0.4)
    chamfer = back_left_corner.cut(back_left_corner_chamfered)

    holder = holder.cut(chamfer)

    # Row (=back) wire cutout
    row_wire_cutout = wp.center(0, row_wire_cutout_y).rect(20, 1.5).extrude(10)
    holder = holder.cut(row_wire_cutout)

    # Row (=back) wire wrappers
    row_wrapper, row_wrapper_clearance = render_wrapper_new(2, 2, 1, 1, 1, 1)

    # row_wrapper_right_clearance = row_wrapper_clearance.translate((4, 2.2, 0))
    # holder = holder.cut(row_wrapper_right_clearance)

    row_wrapper_right = row_wrapper.translate((4, 2.2, 0))
    holder = holder.union(row_wrapper_right)

    # Col and row wrapper, bottom left
    col_row_wrapper, col_row_wrapper_clearance = render_wrapper_new(2, 2, 1, 1, 0, 1.4)

    col_row_wrapper_clearance = col_row_wrapper_clearance.translate((base_left_x + 1, 2.2, 0))
    holder = holder.cut(col_row_wrapper_clearance)

    col_row_wrapper_level_2 = col_row_wrapper.translate((0, 0, 1.5))
    col_row_wrapper = col_row_wrapper.union(col_row_wrapper_level_2)
    col_row_wrapper = col_row_wrapper.translate((base_left_x + 1, 2.2, 0))
    holder = holder.union(col_row_wrapper)

    # Diode holder
    diode_x_center = 3.4
    diode_y_center = -2.7
    diode_rotate = 14

    diode_holder_side_wall_width = 1.5
    diode_holder_front_back_wall_depth = 1

    diode_support = (
        wp.box(
            1.8 + 2 * diode_holder_side_wall_width,
            3.8 + 2 * diode_holder_front_back_wall_depth,
            1.8,
            centered=(True, True, False),
        )
        .rotate((0, 0, 0), (0, 0, 1), diode_rotate)
        .translate((diode_x_center, diode_y_center, 0))
    )
    holder = holder.union(diode_support)

    diode = (
        render_diode()
        .rotate((0, 0, 0), (0, 0, 1), diode_rotate)
        .translate((diode_x_center, diode_y_center, 0))
    )
    holder = holder.cut(diode)

    # Diode front wire cutout
    diode_front_cutout = (
        wp.center(2.5, -key_cf.switch_depth / 2 - 1)
        .rect(2.2, 2, centered=False)
        .extrude(wall_height)
    )
    holder = holder.cut(diode_front_cutout)

    # Diode front wire support
    diode_front_wire_support = wp.center(3, base_front_y).rect(2, 1, centered=False).extrude(2)
    holder = holder.union(diode_front_wire_support)

    #
    # # diode front slit
    # col_wire_front_slit_left = (
    #     wp.workplane(-socket_cf.socket_height)
    #         .center(base_left_x, base_front_y)
    #         .box(1.5, 2, socket_cf.socket_height, centered=False)
    # )
    # holder = holder.union(col_wire_front_slit_left)
    #
    # col_wire_front_slit_right = (
    #     wp.workplane(-socket_cf.socket_height)
    #         .center(base_left_x + 1.7, base_front_y)
    #         .box(2.5, 2, socket_cf.socket_height, centered=False)
    # )
    # holder = holder.union(col_wire_front_slit_right)
    #
    # diode_front_slit = (
    #     wp.workplane(-socket_cf.socket_height)
    #         .center(socket_cf.socket_right_end_x + 0.7, base_front_y)
    #         .box(3, 1.2, socket_cf.socket_height, centered=False)
    # )
    # holder = holder.union(diode_front_slit)

    # Cut outlines
    holder = holder.cut(holder_cutout)

    # Back center cutout (to accommodate front socket support)
    front_socket_support_depth = 1.5

    front_socket_support = (
        wp.workplane(offset=-base_height)
        .center(0, base_back_y - front_socket_support_depth)
        .box(
            front_center_support_width + 1,
            front_socket_support_depth,
            10,
            centered=(True, False, False),
        )
    )
    holder = holder.cut(front_socket_support)

    # Front socket support
    front_socket_support = (
        wp.workplane(offset=-base_height)
        .center(0, base_front_y - front_socket_support_depth)
        .box(
            front_center_support_width,
            front_socket_support_depth,
            base_height + wall_height,
            centered=(True, False, False),
        )
    )
    holder = holder.union(front_socket_support)

    # Cut socket
    socket_sweep = socket.faces("<Z").wires().toPending().extrude(10)
    holder = holder.cut(socket_sweep)

    # Cut plastic pins
    plastic_pin_holes = render_switch_plastic_pin_holes(cf)
    holder = holder.cut(plastic_pin_holes)

    # Cut switch bottom
    switch_bottom = wp.workplane(offset=socket_cf.socket_height + socket_cf.socket_bump_height).box(
        key_cf.switch_width, key_cf.switch_depth, 10, centered=(True, True, False)
    )
    holder = holder.cut(switch_bottom)

    return RenderedSwitchHolder(holder, socket)


def render_wrapper_new(width, depth, narrow_width, narrow_depth, base_height, wrapper_height):
    wp = cq.Workplane("XY")

    wrapper = (
        wp.workplane(offset=base_height)
        .rect(narrow_width, narrow_depth)
        .workplane(offset=wrapper_height)
        .rect(width, depth)
        .loft()
    )

    clearance = wp.rect(width + 1.2, depth + 1.2).extrude(10)

    if base_height > 0:
        base = wp.rect(width, depth).extrude(base_height)
        wrapper = wrapper.union(base)

    return wrapper, clearance


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

    diode_height = 1.8  # 1.8
    diode_width = 1.9  # 1.8
    diode_depth = 3.8  # 3.8
    diode_wire_diam = 0.4
    diode_wire_channel_width = 1.8  # 0.4
    diode_wire_length_per_side = 1

    body = wp.box(diode_width, diode_depth, diode_height)

    # Chamfer body top for lips
    body = body.edges("|Y and >Z").chamfer(0.9, 0.1)

    wire_front = wp.center(0, diode_depth / 2).box(
        diode_wire_channel_width,
        diode_wire_length_per_side,
        diode_height / 2 + diode_wire_diam / 2,
        centered=(True, False, False),
    )
    wire_back = wp.center(0, -diode_depth / 2 - diode_wire_length_per_side).box(
        diode_wire_channel_width,
        diode_wire_length_per_side,
        diode_height / 2 + diode_wire_diam / 2,
        centered=(True, False, False),
    )

    return body.union(wire_front).union(wire_back).translate((0, 0, diode_height / 2))


def render_switch_plastic_pin_holes(cf: MXSwitchHolderConfig):
    wp = cq.Workplane("XY")

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
