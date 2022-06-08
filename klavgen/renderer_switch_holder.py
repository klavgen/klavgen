import math
import cadquery as cq

from .classes import RenderedSwitchHolder
from .config import Config, MXSwitchHolderConfig, CaseConfig, SwitchType
from .renderer_kailh_mx_socket import draw_mx_socket
from .renderer_kailh_choc_socket import draw_choc_socket
from .utils import grow_z, grow_yz, union_list


def render_switch_hole(case_config: CaseConfig, config: MXSwitchHolderConfig):
    wp = cq.Workplane("XY").workplane(
        offset=-case_config.case_base_height + case_config.case_thickness
    )

    switch_hole = wp.box(
        config.key_config.switch_hole_width,
        config.key_config.switch_hole_depth,
        config.switch_hole_min_height,
        centered=grow_z,
    )

    if case_config.use_switch_holders:
        side_hole_left = wp.center(
            -config.key_config.switch_hole_width / 2 - config.plate_side_hole_width,
            -config.key_config.switch_hole_depth / 2,
        ).box(
            config.plate_side_hole_width,
            config.plate_side_hole_depth,
            config.switch_hole_min_height,
            centered=False,
        )
        switch_hole = switch_hole.union(side_hole_left)

        side_hole_right = wp.center(
            config.key_config.switch_hole_width / 2, -config.key_config.switch_hole_depth / 2
        ).box(
            config.plate_side_hole_width,
            config.plate_side_hole_depth,
            config.switch_hole_min_height,
            centered=False,
        )
        switch_hole = switch_hole.union(side_hole_right)

        front_hole = wp.center(
            -config.plate_front_hole_width / 2, config.plate_front_hole_start_y
        ).box(
            config.plate_front_hole_width,
            config.plate_front_hole_depth,
            config.switch_hole_min_height,
            centered=False,
        )
        switch_hole = switch_hole.union(front_hole)

    return switch_hole


def switch_holder_orient_and_center(obj, cf: MXSwitchHolderConfig):
    return (
        obj.rotate((0, -cf.holder_depth / 2, 0), (1, -cf.holder_depth / 2, 0), 90)
        .translate((0, cf.holder_depth / 2 + cf.holder_total_height / 2, 0))
        .rotate((0, 0, 0), (0, 0, 1), 180)
    )


def render_switch_holder(
    config: Config = Config(), orient_for_printing=True
) -> RenderedSwitchHolder:
    if config.case_config.switch_type == SwitchType.MX:
        return render_mx_switch_holder(config, orient_for_printing)
    else:
        return render_choc_switch_holder(config, orient_for_printing)


def render_mx_switch_holder(
    config: Config = Config(), orient_for_printing=True
) -> RenderedSwitchHolder:
    wp = cq.Workplane("XY")
    socket = draw_mx_socket(wp, config)
    return _render_switch_holder(
        socket=socket,
        cf=config.switch_holder_mx_config,
        orient_for_printing=orient_for_printing,
    )


def render_choc_switch_holder(
    config: Config = Config(), orient_for_printing=True
) -> RenderedSwitchHolder:
    wp = cq.Workplane("XY")
    socket = draw_choc_socket(wp, config)
    return _render_switch_holder(
        socket=socket,
        cf=config.switch_holder_choc_config,
        orient_for_printing=orient_for_printing,
    )


def _render_switch_holder(
    socket,
    cf: MXSwitchHolderConfig,
    orient_for_printing=True,
) -> RenderedSwitchHolder:
    case_config = cf.case_config
    socket_cf = cf.kailh_socket_config

    wp = cq.Workplane("XY")
    wp_yz = cq.Workplane("YZ")

    # Create holder block, trimming it at the back
    holder = wp.center(0, -cf.holder_depth / 2).box(
        cf.holder_width,
        cf.holder_depth / 2 + cf.cutoff_y_before_back_wrappers_and_separator,
        cf.holder_height,
        centered=grow_yz,
    )

    # Cut hole on front for easy socket removal
    if cf.has_front_cutout_for_removal:
        mid_x_between_bumps = (
            socket_cf.socket_bump_2_x_from_center + socket_cf.socket_bump_1_x_from_center
        ) / 2

        removal_cutout = (
            wp.workplane(offset=cf.socket_base_height)
            .center(mid_x_between_bumps, -cf.holder_depth / 2)
            .box(
                cf.front_removal_cutout_width,
                cf.holder_front_wall_depth,
                socket_cf.socket_height,
                centered=grow_yz,
            )
        )
        holder = holder.cut(removal_cutout)

    # Cut out holes in the base for the switch metal pins
    template_socket_metal_pin_hole = wp.circle(cf.switch_metal_pin_base_hole_radius).extrude(
        cf.socket_base_height
    )

    socket_metal_pin_extension_hole_1 = template_socket_metal_pin_hole.translate(
        (
            socket_cf.socket_bump_1_x_from_center,
            socket_cf.socket_bump_1_y_from_center,
            0,
        )
    )
    holder = holder.cut(socket_metal_pin_extension_hole_1)

    socket_metal_pin_extension_hole_2 = template_socket_metal_pin_hole.translate(
        (
            socket_cf.socket_bump_2_x_from_center,
            socket_cf.socket_bump_2_y_from_center,
            0,
        )
    )
    holder = holder.cut(socket_metal_pin_extension_hole_2)

    # Position socket vertically above the base
    socket = socket.translate((0, 0, cf.socket_base_height))

    # Sweep socket and cut from holder
    socket_sweep = sweep_socket(socket, cf)
    holder = holder.cut(socket_sweep)

    # Bottom angled cutouts
    bottom_angled_cutouts = draw_bottom_angled_cutouts(cf)
    holder = holder.cut(bottom_angled_cutouts)

    # Socket locking lip
    socket_locking_lip = (
        wp_yz.workplane(offset=socket_cf.socket_locking_lip_start_x)
        .center(socket_cf.socket_locking_lip_start_y, cf.socket_base_height)
        .box(
            cf.socket_lip_depth,
            cf.socket_lip_height,
            socket_cf.socket_locking_lip_width,
            centered=False,
        )
    )
    holder = holder.union(socket_locking_lip)

    # Diode wire front hole
    if cf.reverse_diode_and_col_wire:
        diode_wire_front_hole_start_x = (
            socket_cf.socket_right_end_x + cf.diode_wire_front_hole_distance_from_socket
        )
    else:
        diode_wire_front_hole_start_x = (
            socket_cf.socket_left_end_x
            - cf.diode_wire_front_hole_distance_from_socket
            - cf.diode_wire_front_hole_width
        )

    diode_wire_front_hole = wp.center(diode_wire_front_hole_start_x, -cf.holder_depth / 2).box(
        cf.diode_wire_front_hole_width,
        cf.front_wire_supports_depth,
        cf.socket_base_height + socket_cf.socket_height,
        centered=False,
    )
    holder = holder.cut(diode_wire_front_hole)

    # Col wire front wrapping post
    if cf.reverse_diode_and_col_wire:
        diode_wire_front_hole_narrow_start_x = (
            socket_cf.socket_left_end_x
            - cf.col_wire_front_hole_distance_from_socket
            - cf.col_wire_front_hole_narrow_width
        )
        diode_wire_front_hole_wide_start_x = (
            socket_cf.socket_left_end_x
            - cf.col_wire_front_hole_distance_from_socket
            - cf.col_wire_front_hole_wide_width
        )
    else:
        diode_wire_front_hole_narrow_start_x = (
            socket_cf.socket_right_end_x + cf.col_wire_front_hole_distance_from_socket
        )
        diode_wire_front_hole_wide_start_x = diode_wire_front_hole_narrow_start_x

    col_wire_front_wrapper_cutout_narrow = wp.center(
        diode_wire_front_hole_narrow_start_x, -cf.holder_depth / 2
    ).box(
        cf.col_wire_front_hole_narrow_width,
        cf.front_wire_supports_depth,
        cf.socket_base_height + socket_cf.socket_height,
        centered=False,
    )
    holder = holder.cut(col_wire_front_wrapper_cutout_narrow)

    col_wire_front_wrapper_cutout_wide = (
        wp.center(diode_wire_front_hole_wide_start_x, -cf.holder_depth / 2)
        .workplane(offset=cf.col_wire_front_hole_narrow_height)
        .box(
            cf.col_wire_front_hole_wide_width,
            cf.front_wire_supports_depth,
            cf.socket_base_height + socket_cf.socket_height - cf.col_wire_front_hole_narrow_height,
            centered=False,
        )
    )
    holder = holder.cut(col_wire_front_wrapper_cutout_wide)

    # Top lips
    top_lips = draw_top_lips(cf, case_config)
    holder = holder.union(top_lips)

    # Switch bottom hole
    switch_bottom_hole = (
        wp.workplane(offset=cf.holder_bottom_height)
        .center(0, -cf.key_config.switch_hole_depth / 2)
        .box(
            cf.key_config.switch_hole_width,
            cf.holder_depth * 2,
            cf.holder_height,
            centered=grow_yz,
        )
    )
    holder = holder.cut(switch_bottom_hole)

    # Holes for switch plastic pins

    switch_plastic_pin_hole_left = (
        wp.center(-cf.switch_side_pin_distance, cf.switch_side_pin_y)
        .circle(cf.switch_side_pin_radius)
        .extrude(20)
    )
    holder = holder.cut(switch_plastic_pin_hole_left)

    switch_plastic_pin_hole_center = (
        wp.center(0, cf.switch_center_pin_y).circle(cf.switch_center_pin_radius).extrude(20)
    )
    holder = holder.cut(switch_plastic_pin_hole_center)

    switch_plastic_pin_hole_right = (
        wp.center(cf.switch_side_pin_distance, cf.switch_side_pin_y)
        .circle(cf.switch_side_pin_radius)
        .extrude(20)
    )
    holder = holder.cut(switch_plastic_pin_hole_right)

    #
    # Back wrapping posts and col/row separator
    #

    # Row wire wrapping posts

    if cf.has_row_wire_wrappers:
        row_wire_left_wrapper = (
            wp_yz.workplane(offset=-cf.holder_width / 2)
            .center(
                cf.cutoff_y_before_back_wrappers_and_separator,
                cf.holder_height - cf.row_wire_wrappers_offset_from_plate,
            )
            .lineTo(cf.back_wrappers_and_separator_depth, 0)
            .lineTo(cf.back_wrappers_and_separator_depth, -cf.row_wire_wrappers_tip_height)
            .lineTo(0, -cf.row_wire_wrappers_base_height)
            .close()
            .extrude(cf.holder_side_bottom_wall_width + cf.row_wire_wrapper_extra_width)
        )

        if cf.has_left_row_wire_wrapper:
            holder = holder.union(row_wire_left_wrapper)

        row_wire_right_wrapper = row_wire_left_wrapper.mirror(
            mirrorPlane=cq.Workplane("YZ").plane.zDir,
            basePointVector=cq.Workplane("YZ").val(),
        )
        holder = holder.union(row_wire_right_wrapper)

    # Separator between column and row wires
    if cf.reverse_diode_and_col_wire:
        separator_start_x = -cf.holder_width / 2 + cf.back_side_cut_left_width
    else:
        separator_start_x = (
            cf.holder_width / 2 - cf.back_side_cut_right_width - cf.col_wire_wrapper_head_width
        )

    col_row_separator = (
        wp.workplane(offset=cf.col_row_separator_z)
        .center(separator_start_x, cf.cutoff_y_before_back_wrappers_and_separator)
        .box(
            cf.col_wire_wrapper_head_width,
            cf.back_wrappers_and_separator_depth,
            cf.col_row_separator_height,
            centered=False,
        )
    )
    holder = holder.union(col_row_separator)

    #
    # Col wire back wrapping post
    #
    col_wire_back_wrapper_additions, col_wire_back_wrapper_cutouts = render_col_wire_back_wrapper(
        cf
    )
    holder = holder.union(col_wire_back_wrapper_additions).cut(col_wire_back_wrapper_cutouts)

    #
    # Diode holder
    #
    diode_holder_cutout = render_diode_holder_cutout(cf)
    holder = holder.cut(diode_holder_cutout)

    #
    # Central vertical cut
    #

    # Calculate side (x and y) of the 45 degree point of a unit circle (hypotenuse is 1), 0.5 = (1 ** 2) / 2
    unit_circle_45_deg_side = math.sqrt(0.5)

    # TODO move to config
    if not cf.reverse_diode_and_col_wire:
        # Start of the col wire back wrapper
        col_wire_back_wrapper_start_x = (
            cf.holder_width / 2 - cf.back_side_cut_right_width - cf.col_wire_wrapper_head_width
        )

        # Determine 45 degree side of left switch hole
        switch_left_hole_45_deg_side = unit_circle_45_deg_side * cf.switch_side_pin_radius

        # Determine the left hole left 45 degree point X
        switch_left_hole_45_deg_x = -cf.switch_side_pin_distance - switch_left_hole_45_deg_side

        # Determine the side of the triangle we're cutting starting from the left hole
        left_triangle_cut_side = (
            cf.cutoff_y_before_back_wrappers_and_separator - switch_left_hole_45_deg_side
        )

        # Cut, starting from front center of left hole, going counter-clockwise
        vertical_cut = (
            wp.moveTo(-cf.switch_side_pin_distance, -cf.switch_side_pin_radius)
            .lineTo(switch_left_hole_45_deg_x, switch_left_hole_45_deg_side)
            .lineTo(
                switch_left_hole_45_deg_x + left_triangle_cut_side,
                cf.cutoff_y_before_back_wrappers_and_separator,
            )
            .lineTo(col_wire_back_wrapper_start_x, cf.cutoff_y_before_back_wrappers_and_separator)
            .lineTo(col_wire_back_wrapper_start_x, 0)
            .lineTo(cf.switch_side_pin_distance, -cf.switch_side_pin_radius)
            .close()
            .extrude(cf.holder_total_height)
        )
    else:
        # Start of the col wire back wrapper
        left_wall_end_x = -cf.holder_width / 2 + cf.holder_side_bottom_wall_width
        col_wire_back_wrapper_end_x = (
            -cf.holder_width / 2 + cf.back_side_cut_left_width + cf.col_wire_wrapper_head_width
        )
        left_triangle_side = col_wire_back_wrapper_end_x - left_wall_end_x

        switch_center_hole_45_deg_side = unit_circle_45_deg_side * cf.switch_center_pin_radius

        right_cutout_end_x = 1

        vertical_cut = (
            wp.moveTo(left_wall_end_x, -cf.switch_side_pin_radius)
            .lineTo(left_wall_end_x, cf.bottom_angled_cutout_right_end_top_y)
            .lineTo(
                left_wall_end_x + left_triangle_side,
                cf.bottom_angled_cutout_right_end_top_y + left_triangle_side,
            )
            .lineTo(
                left_wall_end_x + left_triangle_side, cf.cutoff_y_before_back_wrappers_and_separator
            )
            .lineTo(right_cutout_end_x, cf.cutoff_y_before_back_wrappers_and_separator)
            .lineTo(
                right_cutout_end_x,
                switch_center_hole_45_deg_side
                + (switch_center_hole_45_deg_side - right_cutout_end_x),
            )
            .lineTo(switch_center_hole_45_deg_side, switch_center_hole_45_deg_side)
            .lineTo(right_cutout_end_x, -cf.switch_side_pin_radius)
            .close()
            .extrude(cf.holder_total_height)
        )

    holder = holder.cut(vertical_cut)

    #
    # Bottom back side cuts
    #

    # Left cut
    bottom_back_cut_left = wp.center(
        -cf.holder_width / 2,
        -cf.key_config.switch_hole_depth / 2
        + cf.holder_lips_depth
        + cf.back_side_cut_start_behind_lips,
    ).box(cf.back_side_cut_left_width, cf.holder_depth, cf.holder_height, centered=False)
    holder = holder.cut(bottom_back_cut_left)

    # Right cut
    bottom_back_cut_right = wp.center(
        cf.holder_width / 2 - cf.back_side_cut_right_width,
        -cf.key_config.switch_hole_depth / 2
        + cf.holder_lips_depth
        + cf.back_side_cut_start_behind_lips,
    ).box(cf.back_side_cut_right_width, cf.holder_depth, cf.holder_height, centered=False)
    holder = holder.cut(bottom_back_cut_right)

    if orient_for_printing:
        holder = switch_holder_orient_and_center(holder, cf)
        socket = switch_holder_orient_and_center(socket, cf)

    return RenderedSwitchHolder(holder, socket)


def sweep_socket(socket, cf: MXSwitchHolderConfig):
    socket_cf = cf.kailh_socket_config

    wp_xz = cq.Workplane("XZ")
    socket_x_split_wp_base = cq.Workplane("YZ").workplane(
        offset=(socket_cf.socket_bump_1_x_from_center + socket_cf.socket_bump_2_x_from_center) / 2
    )

    # Overlap the left and right sweeps in case one of them doesn't capture the full profile of the half (e.g. in the
    # case of the MX socket where the right bump cross-section doesn't reach the middle)
    socket_x_split_wp_left = socket_x_split_wp_base.workplane(offset=1)
    socket_x_split_wp_right = socket_x_split_wp_base.workplane(offset=-1)

    hole_1_wp = wp_xz.workplane(offset=-socket_cf.socket_bump_1_y_from_center)

    hole_1_seep_until_y = (
        cf.bottom_angled_cutout_right_socket_top_y
        if cf.reverse_diode_and_col_wire
        else cf.bottom_angled_cutout_left_socket_top_y
    )
    hole_1_sweep_distance = hole_1_seep_until_y - socket_cf.socket_bump_1_y_from_center

    hole_1_extrusion = (
        socket.copyWorkplane(socket_x_split_wp_left)
        .split(keepBottom=True)
        .copyWorkplane(hole_1_wp)
        .split(keepTop=True)
        .faces(">Y")
        .wires()
        .toPending()
        .extrude(-hole_1_sweep_distance, combine=False)
    )
    socket_swept = socket.union(hole_1_extrusion)

    hole_2_wp = wp_xz.workplane(offset=-socket_cf.socket_bump_2_y_from_center)

    hole_2_seep_until_y = (
        cf.bottom_angled_cutout_left_socket_top_y
        if cf.reverse_diode_and_col_wire
        else cf.bottom_angled_cutout_right_socket_top_y
    )
    hole_2_sweep_distance = hole_2_seep_until_y - socket_cf.socket_bump_2_y_from_center

    hole_2_extrusion = (
        socket.copyWorkplane(socket_x_split_wp_right)
        .split(keepTop=True)
        .copyWorkplane(hole_2_wp)
        .split(keepTop=True)
        .faces(">Y")
        .wires()
        .toPending()
        .extrude(-hole_2_sweep_distance, combine=False)
    )
    socket_swept = socket_swept.union(hole_2_extrusion)

    return socket_swept


def draw_bottom_angled_cutouts(cf: MXSwitchHolderConfig):
    socket_cf = cf.kailh_socket_config

    socket_bumps_midpoint_x = (
        socket_cf.socket_bump_1_x_from_center + socket_cf.socket_bump_2_x_from_center
    ) / 2

    end_pin_cutouts_start_y = -cf.holder_depth / 2 + cf.front_wire_supports_depth
    socket_cutouts_start_y = cf.cutoff_base_y

    cutouts = []

    # Left, end
    left_side_end_angled_cutout = draw_angled_side_cutout(
        left_x=-cf.holder_width / 2,
        right_x=socket_cf.socket_left_end_x - socket_cf.solder_pin_width,
        front_y=end_pin_cutouts_start_y,
        back_angled_top_y=cf.bottom_angled_cutout_right_end_top_y
        if cf.reverse_diode_and_col_wire
        else cf.bottom_angled_cutout_left_end_top_y,
        cf=cf,
    )

    if left_side_end_angled_cutout:
        cutouts.append(left_side_end_angled_cutout)

    # Left, pin
    left_side_pin_angled_cutout = draw_angled_side_cutout(
        left_x=socket_cf.socket_left_end_x - socket_cf.solder_pin_width,
        right_x=socket_cf.socket_left_end_x,
        front_y=end_pin_cutouts_start_y,
        back_angled_top_y=cf.bottom_angled_cutout_right_socket_top_y
        if cf.reverse_diode_and_col_wire
        else cf.bottom_angled_cutout_left_socket_top_y,
        cf=cf,
    )

    if left_side_pin_angled_cutout:
        cutouts.append(left_side_pin_angled_cutout)

    # Left, socket
    left_socket_pin_angled_cutout = draw_angled_side_cutout(
        left_x=socket_cf.socket_left_end_x,
        right_x=socket_bumps_midpoint_x,
        front_y=socket_cutouts_start_y,
        back_angled_top_y=cf.bottom_angled_cutout_right_socket_top_y
        if cf.reverse_diode_and_col_wire
        else cf.bottom_angled_cutout_left_socket_top_y,
        cf=cf,
        to_pin_top=False,
    )

    if left_socket_pin_angled_cutout:
        cutouts.append(left_socket_pin_angled_cutout)

    # Right, socket
    right_socket_pin_angled_cutout = draw_angled_side_cutout(
        left_x=socket_bumps_midpoint_x,
        right_x=socket_cf.socket_right_end_x,
        front_y=socket_cutouts_start_y,
        back_angled_top_y=cf.bottom_angled_cutout_left_socket_top_y
        if cf.reverse_diode_and_col_wire
        else cf.bottom_angled_cutout_right_socket_top_y,
        cf=cf,
        to_pin_top=False,
    )

    if right_socket_pin_angled_cutout:
        cutouts.append(right_socket_pin_angled_cutout)

    # Right, pin
    right_side_pin_angled_cutout = draw_angled_side_cutout(
        left_x=socket_cf.socket_right_end_x,
        right_x=socket_cf.socket_right_end_x + socket_cf.solder_pin_width,
        front_y=end_pin_cutouts_start_y,
        back_angled_top_y=cf.bottom_angled_cutout_left_socket_top_y
        if cf.reverse_diode_and_col_wire
        else cf.bottom_angled_cutout_right_socket_top_y,
        cf=cf,
    )

    if right_side_pin_angled_cutout:
        cutouts.append(right_side_pin_angled_cutout)

    # Right, end
    right_side_end_angled_cutout = draw_angled_side_cutout(
        left_x=socket_cf.socket_right_end_x + socket_cf.solder_pin_width,
        right_x=cf.holder_width / 2,
        front_y=end_pin_cutouts_start_y,
        back_angled_top_y=cf.bottom_angled_cutout_left_end_top_y
        if cf.reverse_diode_and_col_wire
        else cf.bottom_angled_cutout_right_end_top_y,
        cf=cf,
    )

    if right_side_end_angled_cutout:
        cutouts.append(right_side_end_angled_cutout)

    return union_list(cutouts)


def draw_angled_side_cutout(
    left_x: float,
    right_x: float,
    front_y: float,
    back_angled_top_y: float,
    cf: MXSwitchHolderConfig,
    to_pin_top: bool = True,
):
    width = right_x - left_x
    if width <= 0 or front_y >= back_angled_top_y:
        return None

    wp_yz = cq.Workplane("YZ")

    top_z = (
        cf.holder_height_to_socket_pin_top
        if to_pin_top
        else (cf.socket_base_height + cf.kailh_socket_config.socket_height)
    )
    y_adjustment = 0 if to_pin_top else cf.kailh_socket_config.pin_top_clearance_height

    angled_cutout = (
        wp_yz.workplane(offset=left_x)
        .moveTo(back_angled_top_y + y_adjustment, top_z)
        .lineTo(
            front_y,
            top_z,
        )
        .lineTo(front_y, 0)
        .lineTo(back_angled_top_y + y_adjustment + top_z, 0)
        .close()
        .extrude(width)
    )

    return angled_cutout


def draw_top_lips(cf: MXSwitchHolderConfig, case_config: CaseConfig):
    # Top side lips

    holder_lips_base_height = case_config.case_thickness - cf.holder_lips_start_below_case_top
    holder_side_lips_total_height = (
        holder_lips_base_height + cf.holder_side_lips_width + cf.holder_side_lips_top_lip_height
    )

    # Left lip
    lips = (
        cq.Workplane("XZ")
        .workplane(offset=cf.key_config.switch_hole_depth / 2)
        .center(
            -cf.holder_width / 2 + cf.holder_side_top_wall_x_offset,
            cf.holder_height,
        )
        .lineTo(0, holder_lips_base_height)
        .lineTo(
            -cf.holder_side_lips_width,
            holder_lips_base_height + cf.holder_side_lips_width,
        )
        .lineTo(
            -cf.holder_side_lips_width + cf.holder_side_lips_top_lip_height,
            holder_side_lips_total_height,
        )
        .lineTo(cf.holder_side_lips_base_width, holder_side_lips_total_height)
        .lineTo(cf.holder_side_lips_base_width, 0)
        .close()
        .extrude(-cf.holder_lips_depth)
    )

    # Cut lip so it slopes on the front
    top_left_lip_side_cut = (
        cq.Workplane("YZ")
        .workplane(offset=-cf.holder_width / 2 - 2)
        .center(-cf.key_config.switch_hole_depth / 2, cf.holder_height)
        .lineTo(5, 5)
        .lineTo(0, 5)
        .close()
        .extrude(cf.holder_width)
    )
    lips = lips.cut(top_left_lip_side_cut)

    # Chamfer lip at the back for easier insertion
    lips = lips.edges(">Y and >Z and |X").chamfer(cf.holder_lips_chamfer_top)

    # Right lip is a mirror image of the left
    top_right_lip = lips.mirror(
        mirrorPlane=cq.Workplane("YZ").plane.zDir,
        basePointVector=cq.Workplane("YZ").val(),
    )
    lips = lips.union(top_right_lip)

    # Draw front lip
    front_lip = (
        cq.Workplane("XY")
        .workplane(offset=cf.holder_height)
        .center(0, -cf.holder_depth / 2)
        .box(
            cf.holder_front_lock_bump_width,
            cf.holder_front_wall_depth,
            cf.holder_front_lip_height,
            centered=grow_yz,
        )
    )

    # Chamfer front lip
    front_lip = front_lip.edges("<Y and >Z and |X").chamfer(cf.holder_lips_chamfer_top)

    lips = lips.union(front_lip)

    return lips


def render_col_wire_back_wrapper(cf: MXSwitchHolderConfig):
    wp = cq.Workplane("XY")

    if cf.reverse_diode_and_col_wire:
        start_x = -cf.holder_width / 2 + cf.back_side_cut_left_width
        neck_left_margin = cf.col_wire_wrapper_neck_outer_margin
        neck_right_margin = cf.col_wire_wrapper_neck_inner_margin
    else:
        start_x = (
            cf.holder_width / 2 - cf.back_side_cut_right_width - cf.col_wire_wrapper_head_width
        )
        neck_left_margin = cf.col_wire_wrapper_neck_inner_margin
        neck_right_margin = cf.col_wire_wrapper_neck_outer_margin

    # Neck left cutout (so neck is narrower than head)
    neck_left_cutout = (
        wp.workplane(offset=cf.col_wire_wrapper_back_head_height)
        .center(start_x, 0)
        .box(
            neck_left_margin,
            cf.holder_depth / 2,
            cf.col_wire_wrapper_back_neck_height,
            centered=False,
        )
    )
    cutouts = neck_left_cutout

    # Neck right cutout (so neck is narrower than head)
    neck_right_cutout = (
        wp.workplane(offset=cf.col_wire_wrapper_back_head_height)
        .center(
            start_x + neck_left_margin + cf.col_wire_wrapper_neck_width,
            0,
        )
        .box(
            neck_right_margin,
            cf.holder_depth / 2,
            cf.col_wire_wrapper_back_head_height,
            centered=False,
        )
    )
    cutouts = cutouts.union(neck_right_cutout)

    # Neck cutout at the back (so the neck is much less deep than head and the wire has more space for wrapping)
    neck_back_cutout = (
        wp.workplane(offset=cf.col_wire_wrapper_back_head_height)
        .center(
            start_x + neck_left_margin,
            cf.cutoff_y_before_back_wrappers_and_separator
            - cf.col_wire_wrapper_back_neck_back_cutout_depth,
        )
        .box(
            cf.col_wire_wrapper_neck_width,
            cf.col_wire_wrapper_back_neck_back_cutout_depth,
            cf.col_wire_wrapper_back_neck_height,
            centered=False,
        )
    )
    cutouts = cutouts.union(neck_back_cutout)

    angled_cuts_start_y = (
        cf.bottom_angled_cutout_right_end_top_y
        + cf.holder_height_to_socket_pin_top
        - cf.col_wire_wrapper_back_head_height
    )

    # Head front 45 degrees cutout on the left (for 3D printing without supports)
    head_angled_cutout_left = (
        wp.center(start_x, angled_cuts_start_y)
        .lineTo(neck_left_margin, 0)
        .lineTo(0, neck_left_margin)
        .close()
        .extrude(cf.col_wire_wrapper_back_head_height)
    )
    cutouts = cutouts.union(head_angled_cutout_left)

    # Head front 45 degrees cutout on the right (for 3D printing without supports)
    head_angled_cutout_right = (
        wp.center(start_x + neck_left_margin + cf.col_wire_wrapper_neck_width, angled_cuts_start_y)
        .lineTo(neck_right_margin, 0)
        .lineTo(neck_right_margin, neck_right_margin)
        .close()
        .extrude(cf.col_wire_wrapper_back_head_height)
    )
    cutouts = cutouts.union(head_angled_cutout_right)

    # Head extra depth (to make wrapping easier)
    head_extra_depth = wp.center(start_x, cf.cutoff_y_before_back_wrappers_and_separator).box(
        cf.col_wire_wrapper_head_width,
        cf.col_wire_wrapper_back_head_extra_depth,
        cf.col_wire_wrapper_back_head_height,
        centered=False,
    )

    return head_extra_depth, cutouts


def render_diode_holder_cutout(cf):
    wp = cq.Workplane("XY")
    wp_xz = cq.Workplane("XZ")

    back_side_cut_width = (
        cf.back_side_cut_right_width
        if cf.reverse_diode_and_col_wire
        else cf.back_side_cut_left_width
    )

    diode_center_x = -cf.holder_width / 2 + back_side_cut_width + cf.diode_center_x_from_side_end

    #
    # Diode holder and wire cutout
    #

    # Diode holder hole
    diode_holder_cutout = (
        wp_xz.transformed(
            offset=(diode_center_x, 0, -cf.diode_center_y), rotate=(0, cf.diode_rotation, 0)
        )
        .workplane(offset=cf.diode_depth / 2)
        .center(-cf.diode_diameter / 2, 0)
        .lineTo(0, cf.diode_bottom_lips_z_offset)
        .lineTo(
            cf.diode_bottom_lips_width,
            cf.diode_bottom_lips_z_offset + cf.diode_bottom_lips_width,
        )
        .lineTo(
            cf.diode_bottom_lips_width,
            cf.diode_bottom_lips_z_offset
            + cf.diode_bottom_lips_width
            + cf.diode_bottom_lips_height,
        )
        .lineTo(
            0,
            cf.diode_bottom_lips_z_offset
            + cf.diode_bottom_lips_width
            + cf.diode_bottom_lips_height
            + cf.diode_bottom_lips_width,
        )
        .lineTo(0, cf.holder_bottom_height - cf.diode_top_lips_size)
        .lineTo(cf.diode_top_lips_size, cf.holder_bottom_height)
        .lineTo(cf.diode_diameter - cf.diode_top_lips_size, cf.holder_bottom_height)
        .lineTo(cf.diode_diameter, cf.holder_bottom_height - cf.diode_top_lips_size)
        .lineTo(
            cf.diode_diameter,
            cf.diode_bottom_lips_z_offset
            + cf.diode_bottom_lips_width
            + cf.diode_bottom_lips_height
            + cf.diode_bottom_lips_width,
        )
        .lineTo(
            cf.diode_diameter - cf.diode_bottom_lips_width,
            cf.diode_bottom_lips_z_offset
            + cf.diode_bottom_lips_width
            + cf.diode_bottom_lips_height,
        )
        .lineTo(
            cf.diode_diameter - cf.diode_bottom_lips_width,
            cf.diode_bottom_lips_z_offset + cf.diode_bottom_lips_width,
        )
        .lineTo(cf.diode_diameter, cf.diode_bottom_lips_z_offset)
        .lineTo(cf.diode_diameter, 0)
        .close()
        .extrude(-cf.diode_depth)
    )

    # Diode wire straight cutout
    diode_wire_cutout = (
        wp.transformed(
            offset=(diode_center_x, cf.diode_center_y, 0), rotate=(0, 0, cf.diode_rotation)
        )
        .rect(cf.diode_wire_diameter, 15)
        .extrude(cf.holder_bottom_height - (cf.diode_diameter - cf.diode_wire_diameter) / 2)
    )
    diode_holder_cutout = diode_holder_cutout.union(diode_wire_cutout)

    #
    # Diode wire channel front triangular cutout
    #

    # Determine the wire size in the Y direction (it's the hypotenuse since it's at a 45 degree angle)
    diode_wire_y_depth = math.sqrt(2 * cf.diode_wire_diameter**2)

    # Determine the Y where the inside wall of the wire channel intersects the holder left end. Move by 0.01 so the 45
    # degree channel wall will not overlap with the 45 degree line of the triangular cutout.
    # We use cf.diode_center_x_from_side_end and cf.back_side_cut_width since the wire is at 45 degrees, therefore it
    # forms a square between the center of the diode and the crossing of the holder left end.
    diode_wire_y_intersect_with_holder_left_end = (
        cf.diode_center_y
        - cf.diode_center_x_from_side_end
        - back_side_cut_width
        - diode_wire_y_depth / 2
        + 0.01
    )

    # Determine the triangle to cut out, starting from the intersection point of the wire channel inner wall and the
    # holder left end
    if cf.has_diode_wire_triangular_cutout:
        diode_wire_front_triangular_cutout = (
            wp.workplane(
                offset=cf.holder_bottom_height - cf.diode_diameter / 2 + cf.diode_wire_diameter / 2
            )
            .center(-cf.holder_width / 2, diode_wire_y_intersect_with_holder_left_end)
            .lineTo(cf.diode_wire_triangular_cutout_width_depth, 0)
            .lineTo(
                cf.diode_wire_triangular_cutout_width_depth,
                cf.diode_wire_triangular_cutout_width_depth,
            )
            .close()
            .extrude(-5)
        )
        diode_holder_cutout = diode_holder_cutout.union(diode_wire_front_triangular_cutout)

    #
    # Diode back cutouts
    #

    if cf.has_diode_back_wall_cutout:
        # Cut a consistent back wall to allow empty space behind for easier soldering
        diode_back_wall_cutout = (
            wp.transformed(
                offset=(diode_center_x, cf.diode_center_y, 0), rotate=(0, 0, cf.diode_rotation)
            )
            .center(0, cf.diode_depth / 2 + cf.diode_back_wall_depth)
            .box(
                cf.diode_back_wall_cutout_width,
                cf.holder_depth,
                cf.holder_height,
                centered=grow_yz,
            )
        )
        diode_holder_cutout = diode_holder_cutout.union(diode_back_wall_cutout)

    # Diode back wall top left cutout, since it's unsupported for 3D-printing
    diode_back_wall_top_left_cutout = (
        wp.transformed(
            offset=(diode_center_x, cf.diode_center_y, 0), rotate=(0, 0, cf.diode_rotation)
        )
        .center(-cf.diode_diameter / 2, cf.diode_depth / 2)
        .box(
            (cf.diode_diameter / 2) if cf.diode_back_wall_top_cut_half_width else cf.diode_diameter,
            cf.diode_back_wall_depth,
            cf.holder_bottom_height - cf.diode_diameter / 2 + cf.diode_wire_diameter / 2,
            centered=False,
        )
    )
    diode_holder_cutout = diode_holder_cutout.union(diode_back_wall_top_left_cutout)

    if cf.reverse_diode_and_col_wire:
        diode_holder_cutout = diode_holder_cutout.mirror(
            mirrorPlane=cq.Workplane("YZ").plane.zDir,
            basePointVector=cq.Workplane("YZ").val(),
        )

    return diode_holder_cutout


def export_switch_holder_to_stl(result: RenderedSwitchHolder):
    cq.exporters.export(result.switch_holder, "switch_holder.stl")


def export_switch_holder_to_step(result: RenderedSwitchHolder):
    cq.exporters.export(result.switch_holder, "switch_holder.step")
