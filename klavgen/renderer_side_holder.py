import cadquery as cq

from .classes import LocationRotation, RenderedSideHolder
from .config import SideHolderConfig, CaseConfig
from .utils import grow_yz, create_workplane


def render_side_holder(
    lr: LocationRotation, config: SideHolderConfig, case_config: CaseConfig
) -> RenderedSideHolder:
    base_wp = create_workplane(lr)

    # We want the user coordinates to be at the point of exit from the case (before the wall), however we want to draw
    # from back of controller, so move center
    base_wp = base_wp.center(0, -case_config.case_thickness - config.depth)

    # Case column (full-height), only adding margin to the back, not the front (where we have to add the case thickness)
    case_column = (
        base_wp.workplane(offset=-case_config.case_base_height)
        .center(0, -config.case_tile_margin)
        .box(
            config.width + 2 * config.rail_wall_width + 2 * config.case_tile_margin,
            config.depth + config.case_tile_margin + case_config.case_thickness,
            case_config.case_base_height,
            centered=grow_yz,
        )
    )

    # Case hole
    hole = (
        base_wp.workplane(
            offset=-case_config.case_base_height + config.case_hole_start_from_case_bottom
        )
        .center(0, config.depth - config.case_hole_depth_in_front_of_wall)
        .box(
            config.case_hole_width,
            config.case_hole_clearance_depth,
            case_config.case_base_height
            - config.case_hole_start_from_case_bottom
            - case_config.case_thickness,
            centered=grow_yz,
        )
    )

    rail_wp = base_wp.workplane(
        offset=-case_config.case_base_height + case_config.case_thickness
    ).center(0, config.depth)

    rail_left = (
        rail_wp.center(-config.rail_wall_width - config.width / 2 - config.tolerance, 0)
        .lineTo(config.rail_wall_width, 0)
        .lineTo(config.rail_wall_width, -2 * config.tolerance - config.front_support_depth)
        .lineTo(
            config.rail_wall_width + config.tolerance + config.holder_rail_width,
            -2 * config.tolerance - config.front_support_depth,
        )
        .lineTo(
            config.rail_wall_width + config.tolerance + config.holder_rail_width,
            -2 * config.tolerance - config.front_support_depth - config.rail_wall_depth,
        )
        .lineTo(0, -2 * config.tolerance - config.front_support_depth - config.rail_wall_depth)
        .close()
        .extrude(case_config.case_inner_height)
    )

    latch_hole_left = (
        rail_wp.workplane(
            offset=config.rail_latch_offset_from_bottom + config.rail_latch_base_height / 2
        )
        .center(
            -config.width / 2
            + config.rail_latch_offset_from_side
            + config.rail_latch_base_width / 2,
            -2 * config.tolerance - config.front_support_depth,
        )
        .transformed(rotate=(90, 0, 0))
        .rect(config.rail_latch_base_width, config.rail_latch_base_height)
        .workplane(offset=config.rail_latch_hole_depth)
        .rect(config.rail_latch_tip_width, config.rail_latch_tip_height)
        .loft()
    )

    rail_left = rail_left.cut(latch_hole_left)

    center_yz_plane = rail_wp.transformed(rotate=(0, 90, 0))
    rail_right = rail_left.mirror(
        mirrorPlane=center_yz_plane.plane.zDir, basePointVector=center_yz_plane.val()
    )

    rail = rail_left.union(rail_right)

    # Debug: outline in the air
    debug = (
        base_wp.workplane(offset=5)
        .center(0, config.depth / 2)
        .rect(config.width + 2 * config.tolerance + 2 * config.rail_wall_width, config.depth)
        .rect(
            config.width + 2 * config.tolerance + 2 * config.rail_wall_width - 1, config.depth - 1
        )
        .extrude(1)
    )

    return RenderedSideHolder(case_column=case_column, rail=rail, hole=hole, debug=debug)


def render_holder_latches(config: SideHolderConfig):
    rail_latch_left = (
        cq.Workplane("XZ")
        .workplane(offset=-config.front_support_depth)
        .center(
            config.width / 2
            - config.rail_latch_offset_from_side
            - config.rail_latch_base_width / 2,
            config.rail_latch_offset_from_bottom + config.rail_latch_base_height / 2,
        )
        .rect(config.rail_latch_base_width, config.rail_latch_base_height)
        .workplane(offset=-config.rail_latch_depth)
        .rect(config.rail_latch_tip_width, config.rail_latch_tip_height)
        .loft()
    )

    rail_latch_right = rail_latch_left.mirror("YZ")

    return rail_latch_left.union(rail_latch_right)
