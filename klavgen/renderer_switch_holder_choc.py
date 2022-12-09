import cadquery as cq

from .classes import RenderedSwitchHolder
from .config import ChocSwitchHolderConfig, MXSwitchHolderConfig
from .utils import grow_z


def render_switch_holder_choc(socket, cf: ChocSwitchHolderConfig) -> RenderedSwitchHolder:
    socket_cf = cf.kailh_socket_config
    key_cf = cf.key_config
    case_cf = cf.case_config

    components_height = socket_cf.socket_height  # + 0.6

    wp = cq.Workplane("XY")
    wp_component = wp.workplane(offset=-components_height)

    # Position socket
    socket = socket.translate((0, 0, -socket_cf.socket_height))

    # Base
    min_wall_size = 1
    extra_switch_bottom_buffer_height = 0.4
    extra_switch_hole = 0.4

    wall_height = (
        cf.switch_bottom_buffer_height
        + extra_switch_bottom_buffer_height
        + cf.switch_bottom_height
        - case_cf.case_top_wall_height
    )

    base_left_x = -9.2
    base_right_x = key_cf.switch_hole_width / 2 + min_wall_size
    base_front_y = -8.1
    base_back_y = key_cf.switch_hole_depth / 2 + min_wall_size

    base_width = base_right_x - base_left_x
    base_depth = base_back_y - base_front_y

    base = wp.center(base_left_x, base_front_y).box(
        base_width, base_depth, socket_cf.socket_bump_height + wall_height, centered=False
    )
    holder = base

    # Margin

    back_height_decrease = 0.6

    margin_size = 5

    margin = wp.workplane(offset=back_height_decrease).box(
        key_cf.switch_hole_width + 2 * margin_size,
        key_cf.switch_hole_depth + 2 * margin_size,
        socket_cf.socket_bump_height + wall_height - back_height_decrease,
        centered=grow_z,
    )

    holder = holder.union(margin)

    # Diode holder
    diode_x_center = 3.4
    diode_y_center = -2.6
    diode_rotate = 14

    diode_holder_side_wall_width = 2
    diode_holder_front_back_wall_depth = 1

    diode_support = (
        wp_component.box(
            1.9 + 2 * diode_holder_side_wall_width,
            4 + 2 * diode_holder_front_back_wall_depth,
            components_height,
            centered=(True, True, False),
        )
        .rotate((0, 0, 0), (0, 0, 1), diode_rotate)
        .translate((diode_x_center, diode_y_center, 0))
    )
    holder = holder.union(diode_support)

    diode = (
        render_diode()
        .rotate((0, 0, 0), (0, 0, 1), diode_rotate)
        .translate((diode_x_center, diode_y_center, -components_height))
    )
    holder = holder.cut(diode)

    # Back vertical cutout to decrease the base height
    back_height_decrease_start_y = 1.2
    back_components_height = components_height + back_height_decrease

    back_height_cutout = (
        wp.center(base_left_x, back_height_decrease_start_y)
        .rect(base_width, base_back_y - back_height_decrease_start_y, centered=False)
        .extrude(back_height_decrease)
    )
    holder = holder.cut(back_height_cutout)

    # Col (=left) front wire wrapper. Make height same as the top of the shared wrap

    col_front_wrapper = render_wrapper_new(
        2.5, 2, 1.5, 1, components_height - (back_components_height / 2), back_components_height / 2
    )
    col_front_wrapper = col_front_wrapper.translate((base_left_x + 1.25, base_front_y + 1, 0))
    holder = holder.union(col_front_wrapper)

    # Row (=back) right wire wrapper
    row_y_inset_from_back = 3

    row_right_wrapper = render_wrapper_new(
        3, 3, 2, 2, back_components_height / 2, back_components_height / 2
    )
    row_right_wrapper = row_right_wrapper.translate(
        (base_right_x - 3.5, base_back_y - row_y_inset_from_back, back_height_decrease)
    )
    holder = holder.union(row_right_wrapper)

    # Col and row wrapper, back left
    col_row_wrapper = render_wrapper_new(3, 3, 2, 2, 0, back_components_height / 2)

    col_row_wrapper_level_2 = col_row_wrapper.translate((0, 0, -back_components_height / 2))
    col_row_wrapper = col_row_wrapper.union(col_row_wrapper_level_2)
    col_row_wrapper = col_row_wrapper.translate(
        (base_left_x + 2, base_back_y - row_y_inset_from_back, back_height_decrease)
    )
    holder = holder.union(col_row_wrapper)

    # Switch hole
    switch_hole = (
        wp.workplane(offset=socket_cf.socket_bump_height)
        .rect(
            key_cf.switch_hole_width + 2 * extra_switch_hole,
            key_cf.switch_hole_depth + 2 * extra_switch_hole,
        )
        .extrude(wall_height)
    )
    holder = holder.cut(switch_hole)

    # Plastic pin holes
    plastic_pin_holes = render_switch_plastic_pin_holes(cf)
    # holder = holder.cut(plastic_pin_holes)

    # Socket hole
    socket_sweep = socket.faces("<Z").wires().toPending().extrude(-10)
    holder = holder.cut(socket_sweep)

    clearance = switch_hole.union(plastic_pin_holes).union(socket_sweep)

    # Move in place vertically
    holder = holder.translate(
        (0, 0, -socket_cf.socket_bump_height - wall_height - case_cf.case_top_wall_height)
    )
    clearance = clearance.translate(
        (0, 0, -socket_cf.socket_bump_height - wall_height - case_cf.case_top_wall_height)
    )
    socket = socket.translate(
        (0, 0, -socket_cf.socket_bump_height - wall_height - case_cf.case_top_wall_height)
    )

    # TODO: Make this configurable
    # holder = holder.mirror(mirrorPlane="YZ")
    # clearance = clearance.mirror(mirrorPlane="YZ")
    # socket = socket.mirror(mirrorPlane="YZ")

    return RenderedSwitchHolder(holder, clearance, socket)


def render_wrapper_new(width, depth, narrow_width, narrow_depth, base_height, wrapper_height):
    wp = cq.Workplane("XY")

    wrapper = (
        wp.workplane(offset=-base_height)
        .rect(narrow_width, narrow_depth)
        .workplane(offset=-wrapper_height)
        .rect(width, depth)
        .loft()
    )

    if base_height > 0:
        base = wp.rect(width, depth).extrude(-base_height)
        wrapper = wrapper.union(base)

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

    diode_height = 1.8  # 1.8
    diode_width = 1.9  # 1.8
    diode_depth = 4  # 3.8
    diode_wire_diam = 0.4
    diode_wire_channel_width = 1.9  # 0.4
    diode_wire_length_per_side = 1

    body = wp.box(diode_width, diode_depth, diode_height)

    # Chamfer body top for lips
    body = body.edges("|Y and <Z").chamfer(0.9, 0.1)

    wp_wire = wp.workplane(offset=-diode_height / 2)

    wire_front = wp_wire.center(0, diode_depth / 2).box(
        diode_wire_channel_width,
        diode_wire_length_per_side,
        diode_height / 2 + diode_wire_diam / 2,
        centered=(True, False, False),
    )
    wire_back = wp_wire.center(0, -diode_depth / 2 - diode_wire_length_per_side).box(
        diode_wire_channel_width,
        diode_wire_length_per_side,
        diode_height / 2 + diode_wire_diam / 2,
        centered=(True, False, False),
    )

    return body.union(wire_front).union(wire_back).translate((0, 0, diode_height / 2))


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
