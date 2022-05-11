import math
import cadquery as cq

from .classes import RenderedSwitchHolder
from .config import Config, SwitchHolderConfig, CaseConfig
from .renderer_kailh_socket import draw_socket
from .utils import grow_z, grow_yz


def render_switch_hole(case_config: CaseConfig, config: SwitchHolderConfig):
    wp = cq.Workplane("XY").workplane(
        offset=-case_config.case_base_height + case_config.case_thickness
    )

    switch_hole = wp.box(
        config.switch_hole_width,
        config.switch_hole_depth,
        config.switch_hole_min_height,
        centered=grow_z,
    )

    side_hole_left = wp.center(
        -config.switch_hole_width / 2 - config.plate_side_hole_width, -config.switch_hole_depth / 2
    ).box(
        config.plate_side_hole_width,
        config.plate_left_side_hole_depth,
        config.switch_hole_min_height,
        centered=False,
    )

    side_hole_right = wp.center(config.switch_hole_width / 2, -config.switch_hole_depth / 2).box(
        config.plate_side_hole_width,
        config.plate_right_side_hole_depth,
        config.switch_hole_min_height,
        centered=False,
    )

    front_hole = wp.center(-config.plate_front_hole_width / 2, config.plate_front_hole_start_y).box(
        config.plate_front_hole_width,
        config.plate_front_hole_depth,
        config.switch_hole_min_height,
        centered=False,
    )

    hole = switch_hole.union(side_hole_left).union(side_hole_right).union(front_hole)

    return hole


def switch_holder_orient_and_center(obj, cf: SwitchHolderConfig):
    return (
        obj.rotate((0, -cf.holder_depth / 2, 0), (1, -cf.holder_depth / 2, 0), 90)
        .translate((0, cf.holder_depth / 2 + cf.holder_total_height / 2, 0))
        .rotate((0, 0, 0), (0, 0, 1), 180)
    )


def render_switch_holder(
    config: Config = Config(), orient_for_printing=True
) -> RenderedSwitchHolder:

    #
    # TODO: This code needs to be fully parametric
    #

    case_config = config.case_config
    cf = config.switch_holder_config
    socket_cf = cf.kailh_socket_config

    wp = cq.Workplane("XY")
    wp_yz = cq.Workplane("YZ")

    # Front workplane with Z facing away. Not sure why I made this.
    # Note that positive local Y is negative global Z
    wp_xz = cq.Workplane("XZ").workplane(invert=True)
    wp_xz2 = cq.Workplane("XZ")

    # Draw and position socket
    socket = draw_socket(wp, config).translate((0, 0, cf.socket_base_height))

    # Give extra 2 to back
    holder = wp.center(0, 1).box(
        cf.holder_width, cf.holder_depth + 2, cf.holder_height, centered=grow_z
    )

    # Cut hole on front for easy socket removal
    mid_x_between_bumps = (
        socket_cf.socket_bump_2_x_from_center + socket_cf.socket_bump_1_x_from_center
    ) / 2

    removal_cutout = (
        wp.workplane(offset=cf.socket_base_height)
        .center(mid_x_between_bumps, -cf.holder_depth / 2)
        .box(
            cf.front_removal_cutout_width,
            cf.holder_front_back_wall_depth,
            socket_cf.socket_height,
            centered=grow_yz,
        )
    )

    holder = holder.cut(removal_cutout)

    # Base holes for extension of switch metal pins
    template_socket_metal_pin_extension_hole = wp.circle(
        cf.switch_metal_pin_base_hole_radius
    ).extrude(cf.socket_base_height)

    socket_metal_pin_extension_hole_1 = template_socket_metal_pin_extension_hole.translate(
        (socket_cf.socket_bump_1_x_from_center, socket_cf.socket_bump_1_y_from_center, 0)
    )

    socket_metal_pin_extension_hole_2 = template_socket_metal_pin_extension_hole.translate(
        (socket_cf.socket_bump_2_x_from_center, socket_cf.socket_bump_2_y_from_center, 0)
    )

    holder = holder.cut(socket_metal_pin_extension_hole_1).cut(socket_metal_pin_extension_hole_2)

    # Sweep socket and cut from holder
    socket_sweep = sweep_socket(socket, socket_cf)

    holder = holder.cut(socket_sweep)

    # Socket locking lips
    socket_lip_left = (
        cq.Workplane("YZ")
        .workplane(socket_cf.socket_left_end_x)
        .center(socket_cf.socket_back_left_end_y, cf.socket_base_height)
        .box(cf.socket_lip_width, cf.socket_lip_height, socket_cf.back_flat_width, centered=False)
    )

    socket_lip_right = (
        cq.Workplane("YZ")
        .workplane(
            socket_cf.socket_left_end_x
            + socket_cf.socket_total_width
            - socket_cf.back_right_flat_width
        )
        .center(socket_cf.socket_back_right_end_y, cf.socket_base_height)
        .box(
            cf.socket_lip_width,
            cf.socket_lip_height,
            socket_cf.back_right_flat_width,
            centered=False,
        )
    )

    holder = holder.union(socket_lip_left).union(socket_lip_right)

    # Cut lower plate to make inserting and soldering easier

    base_cutout_left = (
        wp.center(-cf.holder_width / 2, -cf.holder_depth / 2 + cf.front_wire_supports_depth)
        .rect(
            socket_cf.socket_left_end_x - -cf.holder_width / 2,
            cf.cutoff_front_base_y - -cf.holder_depth / 2 - cf.front_wire_supports_depth,
            centered=False,
        )
        .extrude(cf.socket_base_height + socket_cf.socket_height)
    )

    base_cutout_right = (
        wp.center(socket_cf.socket_right_end_x, -cf.holder_depth / 2 + cf.front_wire_supports_depth)
        .rect(
            cf.holder_width / 2 - socket_cf.socket_right_end_x,
            cf.cutoff_front_base_y - -cf.holder_depth / 2 - cf.front_wire_supports_depth,
            centered=False,
        )
        .extrude(cf.socket_base_height + socket_cf.socket_height)
    )

    holder = holder.cut(base_cutout_right).cut(base_cutout_left)

    # Diode wire front support

    diode_wire_front_support_wire_cutout = wp.center(
        socket_cf.socket_left_end_x - 1.5, -cf.holder_depth / 2
    ).box(
        0.9,
        cf.front_wire_supports_depth,
        cf.socket_base_height + socket_cf.socket_height,
        centered=False,
    )

    holder = holder.cut(diode_wire_front_support_wire_cutout)

    diode_wire_front_support_right_cutout = wp.center(
        cf.holder_width / 2 - 3, -cf.holder_depth / 2
    ).box(
        1,
        cf.front_wire_supports_depth,
        cf.socket_base_height + socket_cf.socket_height,
        centered=False,
    )

    holder = holder.cut(diode_wire_front_support_right_cutout)

    diode_wire_front_support_right_cutout = (
        wp.workplane(offset=1)
        .center(cf.holder_width / 2 - 3, -cf.holder_depth / 2)
        .box(
            1.5,
            cf.front_wire_supports_depth,
            cf.socket_base_height + socket_cf.socket_height - 1,
            centered=False,
        )
    )

    holder = holder.cut(diode_wire_front_support_right_cutout)

    # Top lips

    top_lips = draw_top_lips(cf, case_config, wp_xz)

    holder = holder.union(top_lips)

    #
    # Trims
    #

    # Trim holder base in Y, including pin spacing

    front_base_y_trim = wp.center(0, cf.cutoff_front_base_y).box(
        cf.holder_width + 1, cf.holder_depth, cf.holder_height_to_pin_top, centered=grow_yz
    )

    holder = holder.cut(front_base_y_trim)

    # Trim full holder in Y

    y_trim = wp.center(0, cf.cutoff_y).box(
        cf.holder_width + 1, cf.holder_depth, cf.holder_total_height, centered=grow_yz
    )

    holder = holder.cut(y_trim)

    # Cut switch hole, including back wall

    switch_hole = (
        wp.workplane(offset=cf.holder_bottom_height)
        .center(0, -cf.switch_hole_depth / 2)
        .box(cf.switch_hole_width, cf.holder_depth + 2, cf.holder_height, centered=grow_yz)
    )

    holder = holder.cut(switch_hole)

    # Left side profile

    left_side_profile = (
        wp_yz.workplane(offset=-cf.holder_width / 2)
        .moveTo(cf.left_profile_bottom_start_y, 0)
        .lineTo(cf.left_profile_bottom_start_y - cf.holder_bottom_height, cf.holder_bottom_height)
        .lineTo(cf.cutoff_back_bottom_y, cf.holder_bottom_height)
        .lineTo(cf.cutoff_back_bottom_y, 0)
        .close()
        .extrude(cf.holder_width / 2)
    )

    holder = holder.union(left_side_profile)

    # Right side profile
    right_side_profile = (
        wp_yz.moveTo(cf.right_profile_bottom_start_y, 0)
        .lineTo(cf.right_profile_bottom_start_y - cf.holder_bottom_height, cf.holder_bottom_height)
        .lineTo(cf.cutoff_back_bottom_y, cf.holder_bottom_height)
        .lineTo(cf.cutoff_back_bottom_y, 0)
        .close()
        .extrude(cf.holder_width / 2)
    )

    holder = holder.union(right_side_profile)

    # Cut plastic pin holes

    switch_hole_1 = (
        wp.center(cf.switch_hole_1_x, cf.switch_hole_1_y)
        .circle(cf.switch_hole_1_radius)
        .extrude(20)
    )
    switch_hole_2 = (
        wp.center(cf.switch_hole_2_x, cf.switch_hole_2_y)
        .circle(cf.switch_hole_2_radius)
        .extrude(20)
    )
    switch_hole_3 = (
        wp.center(cf.switch_hole_3_x, cf.switch_hole_3_y)
        .circle(cf.switch_hole_3_radius)
        .extrude(20)
    )

    holder = holder.cut(switch_hole_1).cut(switch_hole_2).cut(switch_hole_3)

    # Row wire cutout

    row_wire_cutout = (
        wp_yz.workplane(offset=-cf.holder_width / 2)
        .center(cf.cutoff_back_bottom_y - 1.6, 5.6)
        .moveTo(0, -10)
        .lineTo(0, -1)
        .lineTo(1.6, -2)
        .lineTo(1.6, 0)
        .lineTo(0, 0)
        .lineTo(0, 10)
        .lineTo(10, 10)
        .lineTo(10, -10)
        .close()
        .extrude(20)
    )

    holder = holder.cut(row_wire_cutout)

    row_wire_protrusion_cut = (
        wp.workplane(offset=cf.holder_bottom_height - 0.5)
        .center(0, cf.cutoff_y - 0.5)
        .box(cf.holder_width / 2 - cf.holder_side_bottom_wall_width, 0.5, 0.5, centered=False)
    )

    holder = holder.cut(row_wire_protrusion_cut)

    col_row_isolation = (
        wp_yz.workplane(offset=cf.holder_width / 2 - 5)
        .center(cf.cutoff_back_bottom_y - 1.6, 2)
        .lineTo(1.6, 0)
        .lineTo(1.6, 1)
        .lineTo(0, 1)
        .close()
        .extrude(5)
    )

    holder = holder.union(col_row_isolation)

    back_col_wire_cutout = (
        wp.workplane(offset=1)
        .center(cf.holder_width / 2 - 5, cf.cutoff_back_bottom_y - 1.6 - 0.4)
        .box(5, 0.4, 1, centered=False)
    )

    holder = holder.cut(back_col_wire_cutout)

    back_col_wire_leg = wp.center(cf.holder_width / 2 - 5, cf.cutoff_back_bottom_y - 1.6).box(
        5, 0.6, 1, centered=False
    )

    holder = holder.union(back_col_wire_leg)

    back_col_wire_cutout2 = (
        wp.workplane(offset=1)
        .center(cf.holder_width / 2 - cf.back_side_cut_right - 0.85, cf.cutoff_back_bottom_y - 5)
        .box(0.85, 5, 1, centered=False)
    )

    holder = holder.cut(back_col_wire_cutout2)

    # 2.7 total
    back_col_wire_cutout3 = (
        wp.workplane(offset=1)
        .center(cf.holder_width / 2 - cf.back_side_cut_right - 2.7, cf.cutoff_back_bottom_y - 5)
        .box(0.85, 5, 1, centered=False)
    )

    holder = holder.cut(back_col_wire_cutout3)

    # Angled cutouts
    angled_cutout_right = (
        wp.center(
            cf.holder_width / 2 - cf.back_side_cut_right - 0.85, cf.right_profile_bottom_start_y - 1
        )
        .lineTo(0.85, 0)
        .lineTo(0.85, 0.85)
        .close()
        .extrude(1)
    )

    holder = holder.cut(angled_cutout_right)

    angled_cutout_left = (
        wp.center(
            cf.holder_width / 2 - cf.back_side_cut_right - 2.7, cf.right_profile_bottom_start_y - 1
        )
        .lineTo(0.85, 0)
        .lineTo(0, 0.85)
        .close()
        .extrude(1)
    )

    holder = holder.cut(angled_cutout_left)

    # Diode and wire

    diode_center_x = -cf.holder_width / 2 + cf.diode_center_from_left_end

    # Diode cutout

    diode_cutout = (
        wp_xz2.transformed(rotate=(0, -45, 0), offset=(diode_center_x, 0, -cf.diode_center_y))
        .workplane(offset=cf.diode_depth / 2)
        .center(-cf.diode_diameter / 2, 0)
        .lineTo(0, cf.diode_bottom_lips_z_offset)
        .lineTo(
            cf.diode_bottom_lips_width, cf.diode_bottom_lips_z_offset + cf.diode_bottom_lips_width
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

    holder = holder.cut(diode_cutout)

    # Diode wire cutout

    diode_wire_cotout = (
        wp.transformed(rotate=(0, 0, -45), offset=(diode_center_x, cf.diode_center_y, 0))
        .rect(cf.diode_wire_diameter, 20)
        .extrude(cf.holder_bottom_height - (cf.diode_diameter - cf.diode_wire_diameter) / 2)
    )

    holder = holder.cut(diode_wire_cotout)

    # Diode wire front triangular cutout

    diode_wire_y_cross_section_depth = math.sqrt(2 * cf.diode_wire_diameter ** 2)

    # Move 0.1 so 45% degree lines don't overlap exactly
    diode_wire_holder_left_end_front_intersection_y = (
        cf.diode_center_y
        - cf.diode_center_from_left_end
        - diode_wire_y_cross_section_depth / 2
        + 0.1
    )

    diode_wire_front_triangular_cutout = (
        wp.workplane(
            offset=cf.holder_bottom_height - cf.diode_diameter / 2 + cf.diode_wire_diameter / 2
        )
        .center(-cf.holder_width / 2, diode_wire_holder_left_end_front_intersection_y)
        .lineTo(cf.diode_wire_front_triangular_cutout_edge, 0)
        .lineTo(
            cf.diode_wire_front_triangular_cutout_edge, cf.diode_wire_front_triangular_cutout_edge
        )
        .close()
        .extrude(-5)
    )

    holder = holder.cut(diode_wire_front_triangular_cutout)

    # Diode back cutout

    diode_back_cutout = (
        wp.transformed(rotate=(0, 0, -45), offset=(diode_center_x, cf.diode_center_y, 0))
        .center(0, cf.diode_depth / 2 + cf.diode_back_wall_depth)
        .box(cf.diode_back_cutout_width, cf.holder_depth, cf.holder_height, centered=grow_yz)
    )

    holder = holder.cut(diode_back_cutout)

    # Diode back left wall cutout, because it's unsupported

    diode_back_left_wall_cutout = (
        wp.transformed(rotate=(0, 0, -45), offset=(diode_center_x, cf.diode_center_y, 0))
        .center(-cf.diode_diameter / 2, cf.diode_depth / 2)
        .box(
            cf.diode_diameter / 2,
            cf.diode_back_wall_depth,
            cf.holder_bottom_height - cf.diode_diameter / 2 + cf.diode_wire_diameter / 2,
            centered=False,
        )
    )

    holder = holder.cut(diode_back_left_wall_cutout)

    # Vertical cut

    col_wire_support_start_x = (
        cf.holder_width / 2
        - cf.back_side_cut_right
        - cf.col_wire_cutout_offset_from_right_end
        - cf.col_wire_cutout_width
        - cf.col_wire_support_width_on_left
    )

    circle_loc_45_deg = math.sqrt(2) / 2

    switch_hole_3_loc_45_deg = cf.switch_hole_3_radius * circle_loc_45_deg

    angled_wall_start_x = cf.switch_hole_3_x + switch_hole_3_loc_45_deg

    triangle_side = (
        cf.cutoff_back_bottom_y
        - cf.row_wire_cutout_depth
        - switch_hole_3_loc_45_deg
        - cf.vertical_cut_left_hole_start_y_offset
    )

    vertical_cut = (
        wp.moveTo(cf.switch_hole_1_x, -cf.switch_hole_1_radius)
        .lineTo(-angled_wall_start_x, switch_hole_3_loc_45_deg)
        .lineTo(
            -angled_wall_start_x,
            switch_hole_3_loc_45_deg + cf.vertical_cut_left_hole_start_y_offset,
        )
        .lineTo(
            -angled_wall_start_x + triangle_side, cf.cutoff_back_bottom_y - cf.row_wire_cutout_depth
        )
        .lineTo(
            -cf.holder_width / 2 + cf.holder_side_bottom_wall_width,
            cf.cutoff_back_bottom_y - cf.row_wire_cutout_depth,
        )
        .lineTo(-cf.holder_width / 2 + cf.holder_side_bottom_wall_width, cf.cutoff_back_bottom_y)
        .lineTo(col_wire_support_start_x, cf.cutoff_back_bottom_y)
        .lineTo(col_wire_support_start_x, 0)
        .lineTo(cf.switch_hole_3_x, -cf.switch_hole_3_radius)
        .close()
        .extrude(cf.holder_total_height)
    )

    holder = holder.cut(vertical_cut)

    # Back side cuts

    back_cut_left = wp.center(
        -cf.holder_width / 2,
        -cf.switch_hole_depth / 2 + cf.holder_left_lips_depth + cf.back_side_cut_start_behind_lips,
    ).box(cf.back_side_cut_left, cf.holder_depth, cf.holder_height, centered=False)

    holder = holder.cut(back_cut_left)

    back_cut_right = wp.center(
        cf.holder_width / 2 - cf.back_side_cut_right,
        -cf.switch_hole_depth / 2 + cf.holder_right_lips_depth + cf.back_side_cut_start_behind_lips,
    ).box(cf.back_side_cut_right, cf.holder_depth, cf.holder_height, centered=False)

    holder = holder.cut(back_cut_right)

    # Trim back bottom

    back_bottom_y_trim = wp.center(0, cf.cutoff_back_bottom_y).box(
        cf.holder_width + 1, cf.holder_depth, cf.holder_bottom_height, centered=grow_yz
    )

    holder = holder.cut(back_bottom_y_trim)

    if orient_for_printing:
        holder = switch_holder_orient_and_center(holder, cf)
        socket = switch_holder_orient_and_center(socket, cf)

    return RenderedSwitchHolder(holder, socket)


def sweep_socket(socket, socket_cf):
    # Front workplane with Z facing away. Note that positive plane Y is negative global Z
    wp_xz = cq.Workplane("XZ").workplane(invert=True)

    hole_1_wp = wp_xz.workplane(offset=socket_cf.socket_bump_1_y_from_center)

    hole_1_extrusion = (
        socket.copyWorkplane(hole_1_wp)
        .split(keepBottom=True)
        .faces(">Y")
        .wires()
        .toPending()
        .extrude(30, combine=False)
    )

    hole_2_wp = wp_xz.workplane(offset=socket_cf.socket_bump_2_y_from_center)

    hole_2_extrusion = (
        socket.copyWorkplane(hole_2_wp)
        .split(keepBottom=True)
        .faces(">Y")
        .wires()
        .toPending()
        .extrude(30, combine=False)
    )

    return socket.union(hole_1_extrusion).union(hole_2_extrusion)


def draw_top_lips(cf, case_config, wp_xz):
    # Top side lips

    holder_lips_base_height = case_config.case_thickness - cf.holder_lips_start_below_case_top
    holder_side_lips_total_height = (
        holder_lips_base_height + cf.holder_side_lips_width + cf.holder_side_lips_top_lip_height
    )

    top_left_lip_side_cut = (
        cq.Workplane("YZ")
        .workplane(offset=-cf.holder_width / 2 - 2)
        .center(-cf.switch_hole_depth / 2, cf.holder_height)
        .lineTo(5, 5)
        .lineTo(0, 5)
        .close()
        .extrude(cf.holder_width)
    )

    def draw_top_left_lip(lip_depth):
        lip = (
            wp_xz.workplane(offset=-cf.switch_hole_depth / 2)
            .center(-cf.holder_width / 2 + cf.holder_side_top_wall_x_offset, -cf.holder_height)
            .lineTo(0, -holder_lips_base_height)
            .lineTo(
                -cf.holder_side_lips_width, -holder_lips_base_height - cf.holder_side_lips_width
            )
            .lineTo(
                -cf.holder_side_lips_width + cf.holder_side_lips_top_lip_height,
                -holder_side_lips_total_height,
            )
            .lineTo(cf.holder_side_lips_base_width, -holder_side_lips_total_height)
            .lineTo(cf.holder_side_lips_base_width, 0)
            .close()
            .extrude(lip_depth)
        )

        lip = lip.cut(top_left_lip_side_cut)

        lip = lip.edges(">Z").edges(">Y").chamfer(cf.holder_lips_chamfer_top)

        return lip

    top_left_lip = draw_top_left_lip(cf.holder_left_lips_depth)
    top_right_lip = draw_top_left_lip(cf.holder_right_lips_depth)

    top_right_lip = top_right_lip.mirror(
        mirrorPlane=cq.Workplane("YZ").plane.zDir, basePointVector=cq.Workplane("YZ").val()
    )

    lips = top_left_lip

    lips = lips.union(top_right_lip)

    # Draw front lock bump

    front_lock_bump = (
        cq.Workplane("XY")
        .workplane(offset=cf.holder_height)
        .center(0, -cf.holder_depth / 2)
        .box(
            cf.holder_front_lock_bump_width,
            cf.holder_front_back_wall_depth,
            cf.holder_front_lock_bump_height,
            centered=grow_yz,
        )
    )

    # Chamfer front lock bump
    front_lock_bump = front_lock_bump.edges(
        cq.NearestToPointSelector(
            (0, -cf.holder_depth / 2, cf.holder_height + cf.holder_front_lock_bump_height)
        )
    ).chamfer(cf.holder_lips_chamfer_top)

    lips = lips.union(front_lock_bump)

    return lips


def export_switch_holder_to_stl(result: RenderedSwitchHolder):
    cq.exporters.export(result.switch_holder, "switch_holder.stl")


def export_switch_holder_to_step(result: RenderedSwitchHolder):
    cq.exporters.export(result.switch_holder, "switch_holder.step")
