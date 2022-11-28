import cadquery as cq

from .classes import LocationOrientation, RenderedSideHolder
from .config import CaseConfig, Config, SideHolderConfig
from .utils import create_workplane, grow_yz, grow_z


def render_side_case_hole_rail(
    lr: LocationOrientation, config: SideHolderConfig, case_config: CaseConfig
) -> RenderedSideHolder:
    base_wp = create_workplane(lr)

    # We want the user coordinates to be at the point of exit from the case. We want to draw from the back of the
    # controller, so move the center
    # base_wp = base_wp.center(0, -case_config.case_thickness - config.depth)

    total_depth = case_config.case_thickness + config.horizontal_tolerance + config.depth

    # Case column (full-height), only adding margin to the back, not the front (where we have to add the case thickness)
    case_column = (
        base_wp.workplane(offset=-case_config.case_base_height)
        .center(0, -total_depth - config.case_tile_margin)
        .box(
            config.width + 2 * config.rail_wall_width + 2 * config.case_tile_margin,
            total_depth + config.case_tile_margin,
            case_config.case_base_height,
            centered=grow_yz,
        )
    )

    # Case hole
    hole = (
        base_wp.workplane(
            offset=-case_config.case_base_height + config.case_hole_start_from_case_bottom
        )
        .center(0, -case_config.case_thickness - config.case_hole_depth_in_front_of_case_wall)
        .box(
            config.case_hole_width,
            config.case_hole_clearance_depth,
            case_config.case_base_height
            - config.case_hole_start_from_case_bottom
            - case_config.case_thickness,
            centered=grow_yz,
        )
    )

    # Left rail
    rail_wp = base_wp.workplane(
        offset=-case_config.case_base_height + case_config.case_thickness
    ).center(0, -case_config.case_thickness)

    rail_left = (
        rail_wp.center(-config.rail_wall_width - config.width / 2 - config.horizontal_tolerance, 0)
        .lineTo(config.rail_wall_width, 0)
        .lineTo(
            config.rail_wall_width, -2 * config.horizontal_tolerance - config.holder_bracket_depth
        )
        .lineTo(
            config.rail_wall_width + config.horizontal_tolerance + config.rail_width,
            -2 * config.horizontal_tolerance - config.holder_bracket_depth,
        )
        .lineTo(
            config.rail_wall_width + config.horizontal_tolerance + config.rail_width,
            -2 * config.horizontal_tolerance - config.holder_bracket_depth - config.rail_wall_depth,
        )
        .lineTo(
            0,
            -2 * config.horizontal_tolerance - config.holder_bracket_depth - config.rail_wall_depth,
        )
        .close()
        .extrude(case_config.case_inner_height)
    )

    # Right rail as mirror of the left rail
    center_yz_plane = rail_wp.transformed(rotate=(0, 90, 0))
    rail_right = rail_left.mirror(
        mirrorPlane=center_yz_plane.plane.zDir, basePointVector=center_yz_plane.val()
    )

    rail = rail_left.union(rail_right)

    # Inner clearance
    inner_clearance = (
        base_wp.workplane(offset=-case_config.case_base_height + case_config.case_thickness)
        .center(0, -total_depth / 2)
        .box(
            config.width
            + 2 * config.horizontal_tolerance
            + 2 * config.rail_wall_width
            + 2 * case_config.inner_volume_clearance,
            total_depth + 2 * case_config.inner_volume_clearance,
            case_config.case_inner_height,
            centered=grow_z,
        )
    )

    # Debug: outline in the air
    debug = (
        base_wp.workplane(offset=5)
        .center(0, -total_depth / 2)
        .rect(
            config.width + 2 * config.horizontal_tolerance + 2 * config.rail_wall_width,
            total_depth,
        )
        .rect(
            config.width + 2 * config.horizontal_tolerance + 2 * config.rail_wall_width - 1,
            total_depth - 1,
        )
        .extrude(1)
    )

    return RenderedSideHolder(
        case_column=case_column, rail=rail, inner_clearance=inner_clearance, hole=hole, debug=debug
    )


def render_side_mount_bracket(
    config: Config, side_holder_config: SideHolderConfig, fill_case_wall_hole: bool
):
    case_config = config.case_config

    wp = cq.Workplane("XY")

    # Mount
    mount = wp.box(
        side_holder_config.width,
        side_holder_config.holder_bracket_depth,
        case_config.case_inner_height - side_holder_config.vertical_tolerance,
        centered=grow_yz,
    )

    if fill_case_wall_hole:
        case_wall_fill = wp.center(
            0, -case_config.case_thickness - side_holder_config.horizontal_tolerance
        ).box(
            side_holder_config.case_hole_width - 2 * side_holder_config.horizontal_tolerance,
            case_config.case_thickness + side_holder_config.horizontal_tolerance,
            case_config.case_inner_height - side_holder_config.vertical_tolerance,
            centered=grow_yz,
        )
        mount = mount.union(case_wall_fill)

    return mount
