import importlib
import math
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional

import cadquery as cq

from . import renderer_controller, renderer_trrs_jack
from .classes import Cut, Key, LocationOrientation, PalmRest, Patch, Renderable, Text
from .config import Config, SwitchType
from .renderer_connector import (
    render_case_connector_support,
    render_connector,
    render_connector_cutout,
)
from .renderer_cut import render_cut
from .renderer_key import render_key, render_key_templates
from .renderer_palm_rest import render_palm_rest
from .renderer_patch import render_patch
from .renderer_switch_holder import render_switch_holder
from .renderer_text import render_text
from .rendering import RENDERERS, RenderingPipelineStage, SeparateComponentRender
from .utils import position, union_list

importlib.reload(renderer_controller)
importlib.reload(renderer_trrs_jack)


@dataclass
class RenderCaseResult:
    config: Optional[Config] = None
    keys: Optional[List[Key]] = (None,)
    switch_holes: Optional[cq.Workplane] = None
    fused_switch_holders: Optional[cq.Workplane] = None
    fused_switch_holder_clearances: Optional[cq.Workplane] = None
    fused_switch_holders_mirrored: Optional[cq.Workplane] = None
    fused_switch_holder_clearances_mirrored: Optional[cq.Workplane] = None
    inner_clearances: Optional[cq.Workplane] = None
    patches: Optional[cq.Workplane] = None
    cuts: Optional[cq.Workplane] = None
    case_extras: Optional[cq.Workplane] = None
    case_before_fillet: Optional[cq.Workplane] = None
    top_before_fillet: Optional[cq.Workplane] = None
    vertical_clearance_before_fillet: Optional[cq.Workplane] = None
    case_after_fillet: Optional[cq.Workplane] = None
    inner_volume_after_fillet: Optional[cq.Workplane] = None
    case_after_shell: Optional[cq.Workplane] = None
    shell_cut: Optional[cq.Workplane] = None
    top: Optional[cq.Workplane] = None
    palm_rests_before_case_clearance: Optional[List[cq.Workplane]] = None
    palm_rests_before_fillet: Optional[List[cq.Workplane]] = None
    palm_rests_after_side_fillet: Optional[List[cq.Workplane]] = None
    palm_rests_after_fillet: Optional[List[cq.Workplane]] = None
    palm_rests: Optional[List[cq.Workplane]] = None
    case_with_rests_before_fillet: Optional[cq.Workplane] = None
    bottom_before_fillet: Optional[cq.Workplane] = None
    bottom: Optional[cq.Workplane] = None
    switch_holders: Optional[cq.Workplane] = None
    switch_holders_mirrored: Optional[cq.Workplane] = None
    debug: Optional[cq.Workplane] = None
    standard_components: Optional[cq.Workplane] = None
    components: Optional[Dict[str, Dict[str, List[cq.Workplane]]]] = None
    separate_components: Optional[List[SeparateComponentRender]] = None


def render_case(
    keys: List[Key],
    components: Optional[List[Renderable]] = None,
    patches: Optional[List[Patch]] = None,
    cuts: Optional[List[Cut]] = None,
    case_extras: Optional[List[cq.Workplane]] = None,
    palm_rests: Optional[List[PalmRest]] = None,
    texts: Optional[List[Text]] = None,
    mirror_switch_holders: bool = False,
    debug: bool = False,
    render_standard_components: bool = False,
    result: Optional[RenderCaseResult] = None,
    config: Config = Config(),
) -> RenderCaseResult:
    """
    The core method that renders the keyboard case.

    :param keys: A list of Key objects defining the key positions. Required.
    :param components: A list of components to add to the keyboard
    :param patches: A list of Patch objects that add volume to the case. Optional.
    :param cuts: A list of Cut objects that remove volume from the case. Optional.
    :param case_extras: A list of CadQuery objects to be added to the case. Can be used for custom outlines. Optional.
    :param palm_rests: A list of PalmRest objects that define palm rests (overlapping with keys is fine). Optional.
    :param texts: A list of Text objects with text to be drawn to either the top or palm rests. Optional.
    :param mirror_switch_holders: Whether to also produce a mirrored version of the Choc switch holders. Needs to be
                                  use on split keyboards where both sides are the same.
    :param debug: A boolean defining whether to run in debug mode which skips the finicky shell step (that produces
                  the empty internal volume of the case.
    :param render_standard_components: A boolean defining whether to render all the holders and connectors in the
                                       RenderCaseResult.standard_components value.
    :param result: Pass an existing instance of RenderCaseResult which will be populated as rendering proceeds. This
                   way if the code crashes, you can inspect all the completed steps. Most useful to troubleshoot issues
                   with the shell step and fillets.
    :param config: Pass a custom Config object to override the keyboard configuration.
    :return: A new or existing RenderCaseResult, if one was provided via the result parameter.
    """

    if not result:
        result = RenderCaseResult()

    result.config = config
    result.keys = keys

    case_config = config.case_config
    key_config = config.get_key_config()

    assert (
        case_config.switch_plate_top_fillet is None
        or case_config.switch_plate_top_fillet < case_config.case_top_wall_height
    ), (
        "Switch plate top fillet (switch_plate_top_fillet) needs to be smaller than case top wall height "
        "(case_top_wall_height)"
    )

    if case_config.side_fillet:
        assert (
            abs(case_config.side_fillet - case_config.case_side_wall_thickness) >= 0.01
        ), "Side fillet needs to be at least 0.01 above or below case thickness (case_side_wall_thickness)"

    key_templates = render_key_templates(config)

    # Do rendering
    stage_rendered_components: Dict[RenderingPipelineStage, List[cq.Workplane]] = defaultdict(list)
    result.separate_components = []
    result.components = {}
    if components:
        for component in components:
            if not component.render_func_name:
                raise Exception(f"Component {type(component)} needs to define render_func_name")
            render_func = RENDERERS.get_renderer(component.render_func_name)
            if not render_func:
                raise Exception(
                    f"Rendering function {component.render_func_name} for component {type(component)} not found"
                )

            render_result = render_func(component, config)

            for rendered_item in render_result.items:
                stage_rendered_components[rendered_item.pipeline_stage].append(rendered_item.shape)

                # Add to result
                stage_lower = rendered_item.pipeline_stage.name.lower()
                if stage_lower not in result.components:
                    result.components[stage_lower] = {}

                stage_results = result.components[stage_lower]
                if render_result.name not in stage_results:
                    stage_results[render_result.name] = []

                stage_results[render_result.name].append(rendered_item.shape)

            if render_result.separate_components:
                result.separate_components.extend(render_result.separate_components)

    rendered_keys = [render_key(key, key_templates, case_config, key_config) for key in keys]
    rendered_patches = [render_patch(patch, case_config) for patch in (patches or [])]
    rendered_cuts = [render_cut(cut, case_config) for cut in (cuts or [])]
    rendered_palm_rests = [
        render_palm_rest(palm_rest, case_config) for palm_rest in (palm_rests or [])
    ]
    rendered_texts = [render_text(text) for text in (texts or [])]

    standard_components = []

    case_columns = union_list(
        [rk.case_column for rk in rendered_keys]
        + stage_rendered_components[RenderingPipelineStage.CASE_SOLID]
    )

    case_clearances = union_list([rk.case_clearance for rk in rendered_keys])

    switch_rims = union_list([rk.switch_rim for rk in rendered_keys])

    keycap_clearances = union_list([rk.keycap_clearance for rk in rendered_keys])

    result.switch_holes = union_list([rk.switch_hole for rk in rendered_keys])

    # Fused Choc switch holders
    result.fused_switch_holders = union_list([rk.fused_switch_holder for rk in rendered_keys])
    result.fused_switch_holder_clearances = union_list(
        [rk.fused_switch_holder_clearance for rk in rendered_keys]
    )

    # Mirrored fused Choc switch holders for split keyboards
    result.fused_switch_holders_mirrored = None
    result.fused_switch_holder_clearances_mirrored = None
    if mirror_switch_holders:
        result.fused_switch_holders_mirrored = union_list(
            [rk.fused_switch_holder_mirrored for rk in rendered_keys]
        )

        result.fused_switch_holder_clearances_mirrored = union_list(
            [rk.fused_switch_holder_clearance_mirrored for rk in rendered_keys]
        )

    result.debug = union_list([rendered_key.debug for rendered_key in rendered_keys])

    if rendered_patches:
        result.patches = union_list(rendered_patches)

    if rendered_cuts:
        result.cuts = union_list(rendered_cuts)

    if case_extras:
        result.case_extras = union_list(case_extras)

    # Create case

    case = case_columns.clean()
    if result.patches:
        case = case.union(result.patches)
    if result.cuts:
        case = case.cut(result.cuts)
    if result.case_extras:
        case = case.union(result.case_extras)
    case = case.cut(case_clearances)
    case = case.union(switch_rims).clean()
    case = case.cut(keycap_clearances).clean()

    result.case_before_fillet = case

    result.top_before_fillet = result.case_before_fillet.copyWorkplane(
        cq.Workplane("XY").workplane(offset=-case_config.case_top_wall_height)
    ).split(keepTop=True)

    # The switch part of the case extended vertically to cut any higher palm rest
    result.vertical_clearance_before_fillet = (
        result.top_before_fillet.faces("<Z")
        .wires()
        .toPending()
        .offset2D(case_config.switch_plate_gap_to_palm_rest, kind="intersection")
        .extrude(case_config.clearance_height * 2)
        .translate((0, 0, -case_config.clearance_height))
    )

    if case_config.side_fillet and not debug:
        try:
            result.case_after_fillet = (
                result.case_before_fillet.edges("|Z").fillet(case_config.side_fillet).clean()
            )
        except Exception:
            print(
                "The case side fillet step failed, which likely means your keyboard has features smaller than the "
                "fillet. Try lowering CaseConfig.side_fillet or setting it to None. To troubleshoot, pass in the "
                "result param and inspect result.case_before_fillet."
            )
            raise
    else:
        result.case_after_fillet = result.case_before_fillet

    result.inner_volume_after_fillet = (
        result.case_after_fillet.faces("<Z")
        .wires()
        .toPending()
        .offset2D(
            -case_config.case_side_wall_thickness - case_config.inner_volume_clearance,
            kind="intersection",
        )
        .extrude(case_config.case_inner_height, combine=False)
        .translate((0, 0, case_config.case_bottom_wall_height))
    )

    if not debug:
        try:
            result.shell_cut = (
                result.case_after_fillet.faces("<Z")
                .wires()
                .toPending()
                .offset2D(-case_config.case_side_wall_thickness, kind="intersection")
                .extrude(case_config.case_inner_height, combine=False)
                .translate((0, 0, case_config.case_bottom_wall_height))
            )
        except Exception:
            print(
                "The case side wall generation step failed, which likely means your keyboard is not continuous or "
                "there are very sharp angles. To troubleshoot, pass in the result param and inspect "
                "result.case_after_fillet."
            )
            raise

        try:
            result.case_after_shell = result.case_after_fillet.cut(result.shell_cut)
        except Exception:
            print(
                "The case inner volume removal step failed, which likely means the side wall generation step "
                "produced invalid results. To troubleshoot, pass in the result param and inspect "
                "result.case_after_shell and result.shell_cut."
            )
            raise

        # try:
        #     result.case_after_shell = result.case_after_fillet.shell(
        #         thickness=-case_config.case_side_wall_thickness
        #     ).clean()
        #
        # except Exception:
        #     print(
        #         "The case shell step failed, which likely means your keyboard is not continuous or there are very "
        #         "sharp angles. To troubleshoot, pass in the result param and inspect result.case_after_fillet."
        #     )
        #     raise
        #
        # try:
        #     result.shell_cut = result.case_after_fillet.cut(result.case_after_shell)
        # except Exception:
        #     print(
        #         "The case inner volume step failed, which likely means the shell step produced invalid results. To "
        #         "troubleshoot, pass in the result param and inspect result.case_after_shell."
        #     )
        #     raise
    else:
        result.case_after_shell = None
        result.shell_cut = None

    result.top = result.case_after_fillet.copyWorkplane(
        cq.Workplane("XY").workplane(offset=-case_config.case_top_wall_height)
    ).split(keepTop=True)

    if case_config.switch_plate_top_fillet and not debug:
        try:
            result.top = result.top.edges(">Z").fillet(case_config.switch_plate_top_fillet).clean()
        except Exception:
            print(
                "The top fillet step failed, which likely means your keyboard top has features smaller than the "
                "fillet. Try lowering CaseConfig.switch_plate_top_fillet or setting it to None. To troubleshoot, pass "
                "in the result param and inspect result.top."
            )
            raise

    result.palm_rests_before_case_clearance = None
    result.palm_rests_before_fillet = None
    result.palm_rests_after_fillet = None
    result.palm_rests = None
    result.case_with_rests_before_fillet = result.case_before_fillet

    connector_cutouts = []
    case_connector_supports = []
    if rendered_palm_rests:
        if not case_config.detachable_palm_rests:
            palm_rests_before_case_clearance = union_list(rendered_palm_rests)
            result.palm_rests_before_case_clearance = [palm_rests_before_case_clearance]

            palm_rests_before_fillet = palm_rests_before_case_clearance.cut(
                result.vertical_clearance_before_fillet
            )
            result.palm_rests_before_fillet = [palm_rests_before_fillet]

            palm_rests_after_side_fillet = palm_rests_before_fillet
            if case_config.side_fillet and not debug:
                try:
                    palm_rests_after_side_fillet = (
                        palm_rests_before_fillet.edges("|Z").fillet(case_config.side_fillet).clean()
                    )
                except Exception:
                    print(
                        "The palm rests side fillet step failed, which likely means your palm rests have features "
                        "smaller than the fillet. Try lowering CaseConfig.side_fillet or setting it to None. To "
                        "troubleshoot, pass in the result param and inspect result.palm_rests_before_fillet (note that "
                        "it's a list)."
                    )
                    raise

            result.palm_rests_after_side_fillet = [palm_rests_after_side_fillet]

            palm_rests_after_fillet = palm_rests_after_side_fillet
            if case_config.palm_rests_top_fillet and not debug:
                try:
                    palm_rests_after_fillet = (
                        palm_rests_after_side_fillet.edges(">Z")
                        .fillet(case_config.palm_rests_top_fillet)
                        .clean()
                    )
                except Exception:
                    print(
                        "The palm rests top fillet step failed, which likely means your palm rests have features "
                        "smaller than the fillet. Try lowering CaseConfig.palm_rests_top_fillet or setting it to "
                        "None. To troubleshoot, pass in the result param and inspect "
                        "result.palm_rests_after_side_fillet (note that it's a list)."
                    )
                    raise

            result.palm_rests_after_fillet = [palm_rests_after_fillet]

            result.case_with_rests_before_fillet = result.case_before_fillet.union(
                palm_rests_before_case_clearance
            )

        else:
            result.palm_rests_before_case_clearance = []
            result.palm_rests_before_fillet = []
            result.palm_rests_after_side_fillet = []
            result.palm_rests_after_fillet = []
            result.palm_rests = []

            connector_template = render_connector(config)
            connector_cutout_template = render_connector_cutout(config)
            (
                case_connector_support_template,
                case_connector_support_clearance_template,
            ) = render_case_connector_support(config)

            for palm_rest_tuple in zip(rendered_palm_rests, palm_rests):
                palm_rest_before_case_clearance, palm_rest = palm_rest_tuple
                result.palm_rests_before_case_clearance.append(palm_rest_before_case_clearance)

                palm_rest_before_fillet = palm_rest_before_case_clearance.cut(
                    result.vertical_clearance_before_fillet
                )
                result.palm_rests_before_fillet.append(palm_rest_before_fillet)

                palm_rest_after_side_fillet = palm_rest_before_fillet
                if case_config.side_fillet and not debug:
                    try:
                        palm_rest_after_side_fillet = (
                            palm_rest_before_fillet.edges("|Z")
                            .fillet(case_config.side_fillet)
                            .clean()
                        )
                    except Exception:
                        print(
                            "The palm rests side fillet step failed, which likely means your palm rests have features "
                            "smaller than the fillet. Try lowering CaseConfig.side_fillet or setting it to None. To "
                            "troubleshoot, pass in the result param and inspect result.palm_rests_before_fillet (note "
                            "that it's a list)."
                        )
                        raise

                result.palm_rests_after_side_fillet.append(palm_rest_after_side_fillet)

                palm_rest_after_fillet = palm_rest_after_side_fillet
                if case_config.palm_rests_top_fillet and not debug:
                    try:
                        palm_rest_after_fillet = (
                            palm_rest_after_side_fillet.edges(">Z")
                            .fillet(case_config.palm_rests_top_fillet)
                            .clean()
                        )
                    except Exception:
                        print(
                            "The palm rests top fillet step failed, which likely means your palm rests have features "
                            "smaller than the fillet. Try lowering CaseConfig.palm_rests_top_fillet or setting it to "
                            "None. To troubleshoot, pass in the result param and inspect "
                            "result.palm_rests_after_side_fillet (note that it's a list)."
                        )
                        raise

                result.palm_rests_after_fillet.append(palm_rest_after_fillet)

                final_palm_rest = palm_rest_after_fillet
                if palm_rest.connector_locations_x:
                    for connector_location_x in palm_rest.connector_locations_x:
                        # Palm rest
                        (
                            palm_rest_link_location_y,
                            palm_rest_link_angle,
                        ) = get_y_and_angle_at_x_intersection(
                            palm_rest_after_fillet, connector_location_x
                        )

                        # Body
                        (
                            body_link_location_y,
                            body_link_angle,
                        ) = get_y_and_angle_at_x_intersection(
                            result.case_after_fillet,
                            connector_location_x,
                            highest_y=False,
                        )

                        # Mid-point Y for connector
                        connector_location_y = (
                            palm_rest_link_location_y + body_link_location_y
                        ) / 2

                        # Angle of connector
                        connector_angle = (palm_rest_link_angle + body_link_angle) / 2

                        # Debug
                        # connector_wp = cq.Workplane("XY").transformed(
                        #     rotate=(0, 0, connector_angle),
                        #     offset=(connector_location_x, connector_location_y, 0),
                        # )
                        # debug_line = connector_wp.workplane(offset=15).box(
                        #     1, 10, 1, centered=grow_z
                        # )
                        # r.debug = r.debug.union(debug_line) if r.debug else debug_line

                        connector_location = LocationOrientation(
                            x=connector_location_x,
                            y=connector_location_y,
                            z=-case_config.case_base_height,
                            rotate=connector_angle,
                        )

                        connector_cutout = position(connector_cutout_template, connector_location)
                        case_connector_support = position(
                            case_connector_support_template, connector_location
                        )
                        case_connector_support_clearance = position(
                            case_connector_support_clearance_template, connector_location
                        )

                        result.inner_clearances = union_list(
                            [result.inner_clearances, case_connector_support_clearance]
                        )

                        final_palm_rest = final_palm_rest.cut(connector_cutout)

                        # Add modifiers for the case
                        connector_cutouts.append(connector_cutout)
                        case_connector_supports.append(case_connector_support)

                        if render_standard_components:
                            connector = position(connector_template, connector_location)
                            standard_components.append(connector)

                result.palm_rests.append(final_palm_rest)

    # Collect component inner clearances
    stage_inner_clearances = union_list(
        stage_rendered_components[RenderingPipelineStage.INNER_CLEARANCES]
    )
    if stage_inner_clearances:
        result.inner_clearances = union_list([result.inner_clearances, stage_inner_clearances])

    if result.inner_clearances:
        result.inner_volume_after_fillet = result.inner_volume_after_fillet.cut(
            result.inner_clearances
        )

    result.bottom_before_fillet = result.case_with_rests_before_fillet.copyWorkplane(
        cq.Workplane("XY").workplane(offset=-case_config.case_top_wall_height)
    ).split(keepBottom=True)

    if case_config.side_fillet and not debug:
        result.bottom = (
            result.bottom_before_fillet.edges("|Z").fillet(case_config.side_fillet).clean()
        )
    else:
        result.bottom = result.bottom_before_fillet

    # Add back the palm rests to get the top which was cut above
    if result.palm_rests_after_fillet and not case_config.detachable_palm_rests:
        result.bottom = result.bottom.union(result.palm_rests_after_fillet[0])

    # Remove component cutouts from top
    top_cutouts = union_list(stage_rendered_components[RenderingPipelineStage.TOP_CUTOUTS])
    if top_cutouts:
        result.top = result.top.cut(top_cutouts)

    result.top = result.top.cut(result.switch_holes).clean()

    result.debug = union_list(result.debug, stage_rendered_components[RenderingPipelineStage.DEBUG])

    # Fused Choc switch holder
    result.switch_holders = None
    if result.fused_switch_holders:
        result.switch_holders = result.fused_switch_holders

        if result.fused_switch_holder_clearances:
            result.switch_holders = result.switch_holders.cut(result.fused_switch_holder_clearances)

        if result.inner_clearances:
            result.switch_holders = result.switch_holders.cut(result.inner_clearances)

        result.switch_holders = result.switch_holders.intersect(result.inner_volume_after_fillet)

    # Mirrored fused Choc switch holders
    result.switch_holders_mirrored = None
    if result.fused_switch_holders_mirrored:
        result.switch_holders_mirrored = result.fused_switch_holders_mirrored

        if result.fused_switch_holder_clearances_mirrored:
            result.switch_holders_mirrored = result.switch_holders_mirrored.cut(
                result.fused_switch_holder_clearances_mirrored
            )

        if result.inner_clearances:
            result.switch_holders_mirrored = result.switch_holders_mirrored.cut(
                result.inner_clearances
            )

        result.switch_holders_mirrored = result.switch_holders_mirrored.intersect(
            result.inner_volume_after_fillet
        )

        # Flip so the mirrored switch holders are in the right orientation
        result.switch_holders_mirrored = result.switch_holders_mirrored.mirror(mirrorPlane="YZ")

    if result.shell_cut:
        result.bottom = result.bottom.cut(result.shell_cut)

    for connector_cut in connector_cutouts:
        result.bottom = result.bottom.cut(connector_cut)

    for connector_support in case_connector_supports:
        result.bottom = result.bottom.union(connector_support)

    # Add component additions to bottom
    additions = union_list(
        stage_rendered_components[RenderingPipelineStage.BOTTOM_AFTER_SHELL_ADDITIONS]
    )
    if additions:
        result.bottom = result.bottom.union(additions)

    # Remove component cutouts from bottom
    cuts = union_list(stage_rendered_components[RenderingPipelineStage.BOTTOM_CUTOUTS])
    if cuts:
        result.bottom = result.bottom.cut(cuts)

    result.bottom = result.bottom.cut(result.switch_holes).clean()

    # TODO: remove
    # Add 1.2 mm bottom platform for the switch holders to rest on
    platform = (
        result.inner_volume_after_fillet.faces(">Z")
        .wires()
        .toPending()
        .extrude(1.2, combine=False)
        .translate((0, 0, -case_config.case_inner_height))
    )
    result.bottom = result.bottom.union(platform)

    if rendered_texts:
        top_texts = []
        for text in rendered_texts:
            # Lower by a bit to check for intersection in case text is positioned right on top of an object
            text_lower = text.translate((0, 0, -0.1))

            if result.bottom.intersect(text_lower).val():
                # Intersects or on top of bottom part
                result.bottom = result.bottom.union(text)

            if result.top.intersect(text_lower).val():
                # Intersects or on top of top part
                top_texts.append(text)

            for index, palm_rest in enumerate(result.palm_rests or []):
                if palm_rest.intersect(text_lower).val():
                    # Intersects or on top of palm rest
                    result.palm_rests[index] = palm_rest.union(text)

        # Remove keycap clearances and switch holes from top
        if top_texts:
            top_text_union = top_texts[0]
            for top_text in top_texts[1:]:
                top_text_union = top_text_union.union(top_text)

            top_text_union = top_text_union.cut(keycap_clearances).cut(result.switch_holes).clean()

            result.top = result.top.union(top_text_union)

    if render_standard_components:
        # Add switch holders
        if case_config.use_switch_holders and case_config.switch_type == SwitchType.MX:
            switch_holder_template = render_switch_holder(
                config, orient_for_printing=False
            ).switch_holder
            if not key_config.north_facing:
                switch_holder_template = switch_holder_template.rotate((0, 0, 0), (0, 0, 1), 180)

            switch_holder_config = config.get_switch_holder_config()

            for key in keys:
                switch_holder_lr = LocationOrientation(
                    x=key.x,
                    y=key.y,
                    z=key.z - case_config.case_top_wall_height - switch_holder_config.holder_height,
                    rotate=key.rotate,
                    rotate_around=key.rotate_around,
                )
                standard_components.append(position(switch_holder_template, switch_holder_lr))

        for component in result.separate_components:
            standard_components.append(component.render_in_place_func())

        result.standard_components = union_list(standard_components)

    return result


def get_y_and_angle_at_x_intersection(obj, x, highest_y=True):
    # Y intersect
    intersection_y = get_y_at_x_intersection(obj, x, highest_y)

    # Angle
    dx = 0.01
    right_x = x + dx

    right_intersection_y = get_y_at_x_intersection(obj, right_x, highest_y)

    dy = right_intersection_y - intersection_y

    angle = math.atan2(dy, dx) * 180 / math.pi

    return intersection_y, angle


def get_y_at_x_intersection(obj, x, highest_y=True):
    y_selector = ">Y" if highest_y else "<Y"

    cut_wp = cq.Workplane("YZ").workplane(offset=x)

    left_side = obj.copyWorkplane(cut_wp).split(keepBottom=True)
    vertices = left_side.vertices(">X").vertices(y_selector)

    return vertices.vals()[0].Y


def export_case_to_stl(result: RenderCaseResult):
    cq.exporters.export(result.top, "keyboard_top.stl")
    cq.exporters.export(result.bottom, "keyboard_bottom.stl")

    if result.palm_rests:
        if len(result.palm_rests) == 1:
            cq.exporters.export(result.palm_rests[0], f"palm_rest.stl")
        else:
            for index, palm_rest in enumerate(result.palm_rests):
                cq.exporters.export(palm_rest, f"palm_rest_{index}.stl")

    if result.switch_holders:
        # Flip around Y so it's in printing orientation
        switch_holders_oriented = result.switch_holders.rotate((0, 0, 0), (0, 1, 0), 180)
        cq.exporters.export(switch_holders_oriented, "switch_holders.stl")

    if result.switch_holders_mirrored:
        # Flip around Y so it's in printing orientation
        switch_holders_mirrored_oriented = result.switch_holders_mirrored.rotate(
            (0, 0, 0), (0, 1, 0), 180
        )
        cq.exporters.export(switch_holders_mirrored_oriented, "switch_holders_mirrored.stl")


def export_case_to_step(result: RenderCaseResult):
    cq.exporters.export(result.top, "keyboard_top.step")
    cq.exporters.export(result.bottom, "keyboard_bottom.step")


def move_top(top):
    return top.translate((0, 200, 0))
