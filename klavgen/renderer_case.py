import math
import cadquery as cq
from typing import List, Optional, Any
from dataclasses import dataclass

from . import renderer_controller, renderer_trrs_jack

from .classes import (
    Key,
    ScrewHole,
    Patch,
    Cut,
    Text,
    PalmRest,
    Controller,
    TrrsJack,
    LocationRotation,
)
from .config import Config

from .renderer_cut import render_cut
from .renderer_key import render_key, render_key_templates
from .renderer_palm_rest import render_palm_rest
from .renderer_patch import render_patch
from .renderer_screw_hole import render_screw_hole
from .renderer_text import render_text
from .renderer_connector import (
    render_connector,
    render_connector_cutout,
    render_case_connector_support,
)
from .renderer_switch_holder import render_switch_holder

import importlib

from .utils import position, union_list

importlib.reload(renderer_controller)
importlib.reload(renderer_trrs_jack)
from .renderer_controller import render_controller_case_cutout_and_support, render_controller_holder
from .renderer_trrs_jack import render_trrs_jack_case_cutout_and_support, render_trrs_jack_holder


@dataclass
class RenderCaseResult:
    keys: Optional[List[Key]] = (None,)
    switch_holes: Any = None
    screw_hole_rims: Any = None
    case_extras: Any = None
    patches: Any = None
    cuts: Any = None
    controller_hole: Any = None
    controller_rail: Any = None
    trrs_jack_hole: Any = None
    trrs_jack_rail: Any = None
    case_before_fillet: Any = None
    top_before_fillet: Any = None
    vertical_clearance_before_fillet: Any = None
    case_after_fillet: Any = None
    case_after_shell: Any = None
    shell_cut: Any = None
    top: Any = None
    palm_rests_before_case_clearance: Optional[List[Any]] = None
    palm_rests_before_fillet: Optional[List[Any]] = None
    palm_rests_after_side_fillet: Optional[List[Any]] = None
    palm_rests_after_fillet: Optional[List[Any]] = None
    palm_rests: Optional[List[Any]] = None
    case_with_rests_before_fillet: Any = None
    bottom_before_fillet: Any = None
    bottom: Any = None
    debug: Any = None
    standard_components: Any = None


def render_case(
    keys: List[Key],
    screw_holes: Optional[List[ScrewHole]] = None,
    controller: Optional[Controller] = None,
    trrs_jack: Optional[TrrsJack] = None,
    case_extras: Optional[List[Any]] = None,
    patches: Optional[List[Patch]] = None,
    cuts: Optional[List[Cut]] = None,
    palm_rests: Optional[List[PalmRest]] = None,
    texts: Optional[List[Text]] = None,
    debug: bool = False,
    render_standard_components: bool = False,
    result: Optional[RenderCaseResult] = None,
    config: Config = Config(),
) -> RenderCaseResult:
    """
    The core method that renders the keyboard case.

    :param case_extras:
    :param keys: A list of Key objects defining the key positions. Required.
    :param screw_holes: A list of ScrewHole objects defining the screw hole positions. Optional.
    :param controller: A Controller object defining where the controller back center is. Optional.
    :param trrs_jack: A TrrsJack object defining where the TRRS jack back center is. Optional.
    :param case_extras: A list of CadQuery objects to be added to the case. Can be used for custom outlines. Optional.
    :param patches: A list of Patch objects that add volume to the case. Optional.
    :param cuts: A list of Cut objects that remove volume from the case. Optional.
    :param palm_rests: A list of PalmRest objects that define palm rests (overlapping with keys is fine). Optional.
    :param texts: A list of Text objects with text to be drawn to either the top or palm rests. Optional.
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

    result.keys = keys

    case_config = config.case_config
    key_config = config.key_config

    assert (
        case_config.switch_plate_top_fillet is None
        or case_config.switch_plate_top_fillet < case_config.case_thickness
    ), "Switch plate top fillet (switch_plate_top_fillet) needs to be smaller than case thickness (case_thickness)"

    if case_config.side_fillet:
        assert (
            abs(case_config.side_fillet - case_config.case_thickness) >= 0.01
        ), "Side fillet needs to be at least 0.01 above or below case thickness"

    key_templates = render_key_templates(case_config, config.key_config)

    rendered_keys = [render_key(key, key_templates, case_config, key_config) for key in keys]
    rendered_screw_holes = [
        render_screw_hole(screw_hole, config.screw_hole_config, case_config)
        for screw_hole in (screw_holes or [])
    ]
    rendered_controller = (
        render_controller_case_cutout_and_support(controller, config.controller_config, case_config)
        if controller
        else None
    )
    rendered_trrs_jack = (
        render_trrs_jack_case_cutout_and_support(trrs_jack, config.trrs_jack_config, case_config)
        if trrs_jack
        else None
    )
    rendered_patches = [render_patch(patch, case_config) for patch in (patches or [])]
    rendered_cuts = [render_cut(cut, case_config) for cut in (cuts or [])]
    rendered_palm_rests = [
        render_palm_rest(palm_rest, case_config) for palm_rest in (palm_rests or [])
    ]
    rendered_texts = [render_text(text) for text in (texts or [])]

    standard_components = []

    case_columns = union_list([rk.case_column for rk in rendered_keys])

    if rendered_controller:
        case_columns = case_columns.union(rendered_controller.case_column)
        result.controller_rail = rendered_controller.rail
        result.controller_hole = rendered_controller.hole
    else:
        result.controller_rail = None
        result.controller_hole = None

    if rendered_trrs_jack:
        case_columns = case_columns.union(rendered_trrs_jack.case_column)
        result.trrs_jack_rail = rendered_trrs_jack.rail
        result.trrs_jack_hole = rendered_trrs_jack.hole
    else:
        result.trrs_jack_rail = None
        result.trrs_jack_hole = None

    result.screw_hole_rims = None
    if rendered_screw_holes:
        result.screw_hole_rims = union_list([rsh.rim for rsh in rendered_screw_holes])

    case_clearances = union_list([rk.case_clearance for rk in rendered_keys])

    switch_rims = union_list([rk.switch_rim for rk in rendered_keys])

    keycap_clearances = union_list([rk.keycap_clearance for rk in rendered_keys])

    result.switch_holes = union_list([rk.switch_hole for rk in rendered_keys])

    for screw_hole in rendered_screw_holes:
        result.switch_holes = result.switch_holes.union(screw_hole.hole)

    switch_debug = None
    for rendered_key in rendered_keys:
        if rendered_key.debug:
            if switch_debug:
                switch_debug = switch_debug.union(rendered_key.debug)
            else:
                switch_debug = rendered_key.debug

    screw_hole_debug = None
    for rendered_screw_hole in rendered_screw_holes:
        if rendered_screw_hole.debug:
            if screw_hole_debug:
                screw_hole_debug = screw_hole_debug.union(rendered_screw_hole.debug)
            else:
                screw_hole_debug = rendered_screw_hole.debug

    if case_extras:
        result.case_extras = union_list(case_extras)

    if rendered_patches:
        result.patches = union_list(rendered_patches)

    if rendered_cuts:
        result.cuts = union_list(rendered_cuts)

    # Create case

    case = case_columns.clean()
    if result.case_extras:
        case = case.union(result.case_extras)
    if result.patches:
        case = case.union(result.patches)
    case = case.cut(case_clearances)
    if result.cuts:
        case = case.cut(result.cuts)
    case = case.union(switch_rims).clean()
    if result.screw_hole_rims:
        case = case.union(result.screw_hole_rims)
    case = case.cut(keycap_clearances).clean()

    result.case_before_fillet = case

    result.top_before_fillet = result.case_before_fillet.copyWorkplane(
        cq.Workplane("XY").workplane(offset=-case_config.case_thickness)
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

    if not debug:
        try:
            result.case_after_shell = result.case_after_fillet.shell(
                thickness=-case_config.case_thickness
            ).clean()

        except Exception:
            print(
                "The case shell step failed, which likely means your keyboard is not continuous or there are very "
                "sharp angles. To troubleshoot, pass in the result param and inspect result.case_after_fillet."
            )
            raise

        try:
            result.shell_cut = result.case_after_fillet.cut(result.case_after_shell)
        except Exception:
            print(
                "The case inner volume step failed, which likely means the shell step produced invalid results. To "
                "troubleshoot, pass in the result param and inspect result.case_after_shell."
            )
            raise
    else:
        result.case_after_shell = None
        result.shell_cut = None

    result.top = result.case_after_fillet.copyWorkplane(
        cq.Workplane("XY").workplane(offset=-case_config.case_thickness)
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

            connector_template = render_connector(case_config)
            connector_cutout_template = render_connector_cutout(case_config)
            case_connector_support_template = render_case_connector_support(case_config)

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
                            result.case_after_fillet, connector_location_x, highest_y=False
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

                        connector_location = LocationRotation(
                            x=connector_location_x,
                            y=connector_location_y,
                            z=-case_config.case_base_height,
                            rotate=connector_angle,
                        )

                        connector_cutout = position(connector_cutout_template, connector_location)
                        case_connector_support = position(
                            case_connector_support_template, connector_location
                        )

                        final_palm_rest = final_palm_rest.cut(connector_cutout)

                        # Add modifiers for the case
                        connector_cutouts.append(connector_cutout)
                        case_connector_supports.append(case_connector_support)

                        if render_standard_components:
                            connector = position(connector_template, connector_location)
                            standard_components.append(connector)

                result.palm_rests.append(final_palm_rest)

    result.bottom_before_fillet = result.case_with_rests_before_fillet.copyWorkplane(
        cq.Workplane("XY").workplane(offset=-case_config.case_thickness)
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

    result.top = result.top.cut(result.switch_holes).clean()

    # Debugs
    if switch_debug:
        result.debug = result.debug.union(switch_debug) if result.debug else switch_debug

    if screw_hole_debug:
        result.debug = result.debug.union(screw_hole_debug) if result.debug else screw_hole_debug

    if rendered_controller and rendered_controller.debug:
        result.debug = (
            result.debug.union(rendered_controller.debug)
            if result.debug
            else rendered_controller.debug
        )

    if rendered_trrs_jack and rendered_trrs_jack.debug:
        result.debug = (
            result.debug.union(rendered_trrs_jack.debug)
            if result.debug
            else rendered_trrs_jack.debug
        )

    if result.shell_cut:
        result.bottom = result.bottom.cut(result.shell_cut)

    if result.controller_hole:
        result.bottom = result.bottom.cut(result.controller_hole)

    if result.trrs_jack_hole:
        result.bottom = result.bottom.cut(result.trrs_jack_hole)

    for connector_cut in connector_cutouts:
        result.bottom = result.bottom.cut(connector_cut)

    for connector_support in case_connector_supports:
        result.bottom = result.bottom.union(connector_support)

    # Add back screw hole rims
    if result.screw_hole_rims:
        result.screw_hole_rims_bottom = result.screw_hole_rims.copyWorkplane(
            cq.Workplane("XY").workplane(offset=-case_config.case_thickness)
        ).split(keepBottom=True)

        result.bottom = result.bottom.union(result.screw_hole_rims_bottom)

    if result.controller_rail:
        result.bottom = result.bottom.union(result.controller_rail)

    if result.trrs_jack_rail:
        result.bottom = result.bottom.union(result.trrs_jack_rail)

    # This also contains screw holes
    result.bottom = result.bottom.cut(result.switch_holes).clean()

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

        # Remove keycap clearances and switch/screw holes from top
        if top_texts:
            top_text_union = top_texts[0]
            for top_text in top_texts[1:]:
                top_text_union = top_text_union.union(top_text)

            top_text_union = top_text_union.cut(keycap_clearances).cut(result.switch_holes).clean()

            result.top = result.top.union(top_text_union)
            
    if key_config.amoeba_royale:
        for post in rendered_keys:
            result.top = result.top.union(post.amoeba_royale_post)

    if render_standard_components:
        # Add switch holders
        switch_holder_template = render_switch_holder(
            config, orient_for_printing=False
        ).switch_holder
        if not key_config.north_facing:
            switch_holder_template = switch_holder_template.rotate((0, 0, 0), (0, 0, 1), 180)

        switch_holder_config = config.switch_holder_config

        for key in keys:
            switch_holder_lr = LocationRotation(
                x=key.x,
                y=key.y,
                z=key.z - case_config.case_thickness - switch_holder_config.holder_height,
                rotate=key.rotate,
                rotate_around=key.rotate_around,
            )
            standard_components.append(position(switch_holder_template, switch_holder_lr))

        # Add controller holder
        if controller:
            controller_config = config.controller_config

            controller_holder = render_controller_holder(controller_config).translate(
                (0, -case_config.case_thickness - controller_config.tolerance, 0)
            )

            controller_lr = LocationRotation(
                x=controller.x,
                y=controller.y,
                z=controller.z - case_config.case_base_height + case_config.case_thickness,
                rotate=controller.rotate,
                rotate_around=controller.rotate_around,
            )

            standard_components.append(position(controller_holder, controller_lr))

        # Add TRRS jack holder
        if trrs_jack:
            trrs_jack_config = config.trrs_jack_config

            trrs_jack_holder = render_trrs_jack_holder(trrs_jack_config).translate(
                (0, -case_config.case_thickness - trrs_jack_config.tolerance, 0)
            )

            trrs_jack_lr = LocationRotation(
                x=trrs_jack.x,
                y=trrs_jack.y,
                z=trrs_jack.z - case_config.case_base_height + case_config.case_thickness,
                rotate=trrs_jack.rotate,
                rotate_around=trrs_jack.rotate_around,
            )

            standard_components.append(position(trrs_jack_holder, trrs_jack_lr))

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


def export_case_to_step(result: RenderCaseResult):
    cq.exporters.export(result.top, "keyboard_top.step")
    cq.exporters.export(result.bottom, "keyboard_bottom.step")


def move_top(top):
    return top.translate((0, 200, 0))
