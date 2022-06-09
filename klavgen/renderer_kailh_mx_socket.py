from .config import Config, KailhMXSocketConfig


def draw_socket_base(wp, cf: KailhMXSocketConfig):
    return (
        wp.lineTo(cf.front_flat_width, 0)
        .radiusArc(
            (cf.front_flat_width + cf.large_radius, cf.large_radius),
            radius=-cf.large_radius,
        )
        .lineTo(cf.front_flat_width + cf.large_radius, cf.socket_total_depth)
        .lineTo(
            cf.front_flat_width + cf.large_radius - cf.back_right_flat_width,
            cf.socket_total_depth,
        )
        .radiusArc(
            (
                cf.front_flat_width + cf.large_radius - cf.back_right_flat_width - cf.small_radius,
                cf.socket_thin_part_depth,
            ),
            radius=cf.small_radius,
        )
        .lineTo(0, cf.socket_thin_part_depth)
        .close()
    )


def draw_socket_left_pin(wp, cf: KailhMXSocketConfig):
    return (
        wp.moveTo(0, cf.socket_thin_part_depth - cf.left_flat_depth_behind_solder_pin)
        .lineTo(
            -cf.solder_pin_width,
            cf.socket_thin_part_depth - cf.left_flat_depth_behind_solder_pin,
        )
        .lineTo(-cf.solder_pin_width, cf.left_flat_depth_in_front_of_solder_pin)
        .lineTo(0, cf.left_flat_depth_in_front_of_solder_pin)
        .close()
    )


def draw_socket_right_pin(wp, cf: KailhMXSocketConfig):
    return (
        wp.moveTo(
            cf.front_flat_width + cf.large_radius,
            cf.large_radius + cf.right_flat_depth_in_front_of_solder_pin,
        )
        .lineTo(
            cf.front_flat_width + cf.large_radius + cf.solder_pin_width,
            cf.large_radius + cf.right_flat_depth_in_front_of_solder_pin,
        )
        .lineTo(
            cf.front_flat_width + cf.large_radius + cf.solder_pin_width,
            cf.large_radius
            + cf.right_flat_depth_in_front_of_solder_pin
            + cf.right_flat_depth_solder_pin,
        )
        .lineTo(
            cf.front_flat_width + cf.large_radius,
            cf.large_radius
            + cf.right_flat_depth_in_front_of_solder_pin
            + cf.right_flat_depth_solder_pin,
        )
        .close()
    )


def center_socket(obj, cf: KailhMXSocketConfig):
    return obj.translate((cf.socket_center_x_offset, cf.socket_center_y_offset, 0))


def draw_socket_bump_1(wp, cf: KailhMXSocketConfig):
    return wp.center(cf.socket_bump_1_x, cf.socket_bump_1_y).circle(cf.socket_bump_radius)


def draw_socket_bump_2(wp, cf: KailhMXSocketConfig):
    return wp.center(cf.socket_bump_2_x, cf.socket_bump_2_y).circle(cf.socket_bump_radius)


def draw_mx_socket(wp, config: Config = Config()):
    cf = config.kailh_mx_socket_config

    socket = draw_socket_base(wp, cf)
    socket = socket.extrude(cf.socket_height)

    socket_left_pin = draw_socket_left_pin(wp, cf)
    socket_left_pin = socket_left_pin.extrude(cf.socket_height + cf.pin_top_clearance_height)

    socket_right_pin = draw_socket_right_pin(wp, cf)
    socket_right_pin = socket_right_pin.extrude(cf.socket_height + cf.pin_top_clearance_height)

    socket_bump_1 = draw_socket_bump_1(wp.workplane(cf.socket_height), cf).extrude(
        cf.socket_bump_height
    )
    socket_bump_2 = draw_socket_bump_2(wp.workplane(cf.socket_height), cf).extrude(
        cf.socket_bump_height
    )

    return center_socket(
        socket.union(socket_bump_1)
        .union(socket_bump_2)
        .union(socket_left_pin)
        .union(socket_right_pin),
        cf,
    )
