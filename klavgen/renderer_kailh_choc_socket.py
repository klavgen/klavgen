from .config import Config, KailhChocSocketConfig


def center_socket(obj, cf: KailhChocSocketConfig):
    return obj.translate((cf.socket_center_x_offset, cf.socket_center_y_offset, 0))


def draw_choc_socket(wp, config: Config = Config()):
    cf = config.kailh_choc_socket_config

    socket = (
        wp.moveTo(0, cf.left_y_offset)
        .lineTo(cf.total_width - cf.front_right_width - cf.left_y_offset, cf.left_y_offset)
        .lineTo(cf.total_width - cf.front_right_width, 0)
        .lineTo(cf.total_width + cf.front_right_corner_protrusion_width, 0)
        .lineTo(cf.total_width + cf.front_right_corner_protrusion_width, cf.pins_inset_depth)
        .lineTo(cf.total_width, cf.pins_inset_depth)
        .lineTo(cf.total_width, cf.right_depth)
        .lineTo(cf.back_left_width + cf.right_y_space_behind, cf.right_depth)
        .lineTo(cf.back_left_width, cf.socket_total_depth)
        .lineTo(0, cf.socket_total_depth)
        .close()
    )

    socket = socket.extrude(cf.socket_height)

    left_pin = (
        wp.moveTo(0, cf.left_y_offset + cf.pins_inset_depth)
        .lineTo(-cf.solder_pin_width, cf.left_y_offset + cf.pins_inset_depth)
        .lineTo(-cf.solder_pin_width, cf.socket_total_depth - cf.pins_inset_depth)
        .lineTo(0, cf.socket_total_depth - cf.pins_inset_depth)
        .close()
    ).extrude(cf.socket_height + cf.pin_top_clearance_height)

    socket = socket.union(left_pin)

    right_pin = (
        wp.moveTo(cf.total_width, cf.pins_inset_depth)
        .lineTo(
            cf.total_width + cf.solder_pin_width,
            cf.pins_inset_depth,
        )
        .lineTo(cf.total_width + cf.solder_pin_width, cf.right_depth - cf.pins_inset_depth)
        .lineTo(cf.total_width, cf.right_depth - cf.pins_inset_depth)
        .close()
    ).extrude(cf.socket_height + cf.pin_top_clearance_height)

    socket = socket.union(right_pin)

    socket_bump_1 = (
        wp.workplane(offset=cf.socket_height)
        .center(cf.socket_bump_1_x, cf.socket_bump_1_y)
        .circle(cf.socket_bump_radius)
        .extrude(cf.socket_bump_height)
    )

    socket = socket.union(socket_bump_1)

    socket_bump_2 = (
        wp.workplane(offset=cf.socket_height)
        .center(cf.socket_bump_2_x, cf.socket_bump_2_y)
        .circle(cf.socket_bump_radius)
        .extrude(cf.socket_bump_height)
    )

    socket = socket.union(socket_bump_2)

    return center_socket(
        socket,
        cf,
    )
