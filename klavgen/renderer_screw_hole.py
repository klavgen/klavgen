import cadquery as cq

from .classes import RenderedScrewHole, ScrewHole
from .config import CaseConfig, ScrewHoleConfig


def render_screw_hole(
    screw_hole: ScrewHole, config: ScrewHoleConfig, case_config: CaseConfig
) -> RenderedScrewHole:
    base_wp = cq.Workplane("XY").transformed(
        offset=(screw_hole.x, screw_hole.y, -case_config.case_base_height)
    )

    rim = base_wp.circle(config.screw_rim_radius).extrude(
        screw_hole.z + case_config.case_base_height
    )

    # Hole below insert
    hole = (
        base_wp.workplane(offset=case_config.case_thickness)
        .circle(config.screw_hole_body_radius)
        .extrude(
            screw_hole.z
            + case_config.case_base_height
            - 2 * case_config.case_thickness
            - config.screw_insert_depth
        )
    )

    # Hole for insert
    hole = (
        hole.faces(">Z")
        .workplane()
        .circle(config.screw_insert_hole_width)
        .extrude(config.screw_insert_depth)
        .faces(">Z")
        .workplane()
    )

    # Hole for top plate
    hole = hole.circle(config.screw_hole_plate_radius).extrude(case_config.case_thickness)

    # Vertical clearance on top for the head
    hole = (
        hole.faces(">Z")
        .workplane()
        .circle(config.screw_head_radius)
        .extrude(case_config.clearance_height)
    )

    # Debug: rim outline in the air
    debug = (
        base_wp.workplane(offset=case_config.case_base_height + 5)
        .circle(config.screw_rim_radius)
        .circle(config.screw_rim_radius - 0.5)
        .extrude(1)
    )

    return RenderedScrewHole(rim, hole, debug)
