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
    rim_bottom = rim.copyWorkplane(
        cq.Workplane("XY").workplane(offset=-case_config.case_thickness)
    ).split(keepBottom=True)

    # Rim clearance
    rim_inner_clearance = base_wp.circle(
        config.screw_rim_radius + case_config.inner_volume_clearance
    ).extrude(screw_hole.z + case_config.case_base_height)

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

    return RenderedScrewHole(
        rim=rim,
        rim_bottom=rim_bottom,
        rim_inner_clearance=rim_inner_clearance,
        hole=hole,
        debug=debug,
    )
