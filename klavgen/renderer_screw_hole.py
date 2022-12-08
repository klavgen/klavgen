import cadquery as cq

from .classes import RenderedScrewHole, ScrewHole
from .config import CaseConfig, Config, ScrewHoleConfig
from .rendering import RENDERERS, RenderedItem, RenderingPipelineStage, RenderResult


def render_screw_hole(screw_hole: ScrewHole, config: Config) -> RenderResult:
    result = _render_screw_hole(screw_hole, config.screw_hole_config, config.case_config)

    return RenderResult(
        name=screw_hole.name or "screw_hole",
        items=[
            RenderedItem(result.rim, pipeline_stage=RenderingPipelineStage.CASE_SOLID),
            RenderedItem(result.hole, pipeline_stage=RenderingPipelineStage.TOP_CUTOUTS),
            RenderedItem(
                result.rim_bottom,
                pipeline_stage=RenderingPipelineStage.BOTTOM_AFTER_SHELL_ADDITIONS,
            ),
            RenderedItem(result.hole, pipeline_stage=RenderingPipelineStage.BOTTOM_CUTOUTS),
            RenderedItem(
                result.rim_inner_clearance, pipeline_stage=RenderingPipelineStage.INNER_CLEARANCES
            ),
            RenderedItem(result.debug, pipeline_stage=RenderingPipelineStage.DEBUG),
        ],
    )


RENDERERS.set_renderer("screw_hole", render_screw_hole)


def _render_screw_hole(
    screw_hole: ScrewHole, config: ScrewHoleConfig, case_config: CaseConfig
) -> RenderedScrewHole:
    base_wp = cq.Workplane("XY").transformed(
        offset=(screw_hole.x, screw_hole.y, -case_config.case_base_height)
    )

    # Rim
    rim = base_wp.circle(config.screw_rim_radius).extrude(
        screw_hole.z + case_config.case_base_height
    )

    # Rim that should be added back to the bottom (=cut the top off)
    rim_bottom = base_wp.circle(config.screw_rim_radius).extrude(
        screw_hole.z + case_config.case_base_height - case_config.case_top_wall_height
    )

    # Rim clearance
    rim_inner_clearance = base_wp.circle(
        config.screw_rim_radius + case_config.inner_volume_clearance
    ).extrude(screw_hole.z + case_config.case_base_height)

    # Vertical clearance above the top plate
    hole = (
        base_wp.workplane(offset=screw_hole.z + case_config.case_base_height)
        .circle(config.screw_head_radius)
        .extrude(case_config.clearance_height)
    )

    # Hole for top plate
    hole_top = (
        base_wp.workplane(
            offset=screw_hole.z + case_config.case_base_height - case_config.case_top_wall_height
        )
        .circle(config.screw_hole_plate_radius)
        .extrude(case_config.case_top_wall_height)
    )
    hole = hole.union(hole_top)

    # Hole for insert
    hole_insert = (
        base_wp.workplane(
            offset=screw_hole.z
            + case_config.case_base_height
            - case_config.case_top_wall_height
            - config.screw_insert_depth
        )
        .circle(config.screw_insert_hole_width)
        .extrude(config.screw_insert_depth)
    )
    hole = hole.union(hole_insert)

    # Hole below insert
    hole_below_insert_height = (
        screw_hole.z + case_config.case_inner_height - config.screw_insert_depth
    )
    if hole_below_insert_height > 0:
        hole_below_insert = (
            base_wp.workplane(offset=case_config.case_bottom_wall_height)
            .circle(config.screw_hole_body_radius)
            .extrude(screw_hole.z + case_config.case_inner_height - config.screw_insert_depth)
        )
        hole = hole.union(hole_below_insert)

    # Debug: rim outline in the air
    debug = (
        base_wp.workplane(offset=case_config.case_base_height + 5)
        .circle(config.screw_rim_radius)
        .circle(config.screw_rim_radius - 0.5)
        .extrude(1)
    )

    return RenderedScrewHole(
        rim=rim,
        rim_bottom=rim_bottom,
        rim_inner_clearance=rim_inner_clearance,
        hole=hole,
        debug=debug,
    )
