from dataclasses import dataclass
from typing import Dict, List, Optional

import cadquery as cq

from .classes import Cut, Key, PalmRest, Patch, RenderedSwitchHolder, Text
from .config import Config, SwitchType
from .renderer_case import RenderCaseResult, export_case_to_step, export_case_to_stl, render_case
from .renderer_connector import export_connector_to_step, export_connector_to_stl, render_connector
from .renderer_switch_holder import (
    export_switch_holder_to_step,
    export_switch_holder_to_stl,
    render_switch_holder,
)
from .rendering import Renderable


@dataclass
class RenderKeyboardResult:
    case_result: RenderCaseResult
    top: cq.Workplane
    bottom: cq.Workplane
    switch_holder: Optional[cq.Workplane]
    connector: Optional[cq.Workplane]
    separate_components: Dict[str, cq.Workplane]


def render_and_save_keyboard(
    keys: List[Key],
    components: Optional[List[Renderable]] = None,
    case_extras: Optional[List[cq.Workplane]] = None,
    patches: Optional[List[Patch]] = None,
    cuts: Optional[List[Cut]] = None,
    palm_rests: Optional[List[PalmRest]] = None,
    texts: Optional[List[Text]] = None,
    debug: bool = False,
    render_standard_components: bool = False,
    result: Optional[RenderCaseResult] = None,
    config: Optional[Config] = None,
) -> RenderKeyboardResult:
    """
    The core method that renders and saves as STL files all keyboard components.

    :param keys: A list of Key objects defining the key positions. Required.
    :param components: A list of components to add to the keyboard
    :param patches: A list of Patch objects that add volume to the case. Optional.
    :param cuts: A list of Cut objects that remove volume from the case. Optional.
    :param case_extras: A list of CadQuery objects to be added to the case. Can be used for custom outlines. Optional.
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
    :return: A RenderKeyboardResult object with all components of the keyboard
    """
    if not config:
        config = Config()

    case_result = render_case(
        keys=keys,
        components=components,
        patches=patches,
        cuts=cuts,
        case_extras=case_extras,
        palm_rests=palm_rests,
        texts=texts,
        debug=debug,
        render_standard_components=render_standard_components,
        result=result,
        config=config,
    )

    return export_keyboard_to_stl(case_result)


@dataclass
class KeyboardComponents:
    switch_holder_result: Optional[RenderedSwitchHolder]
    connector: Optional[cq.Workplane]
    components: Dict[str, cq.Workplane]


def _render_keyboard_separate_components(case_result: RenderCaseResult) -> KeyboardComponents:
    config = case_result.config

    switch_holder_result = None
    if config.case_config.use_switch_holders and config.case_config.switch_type == SwitchType.MX:
        switch_holder_result = render_switch_holder(config)

    connector = None
    if case_result.palm_rests:
        connector = render_connector(config)

    rendered_components = {}
    if case_result.separate_components:
        for separate_component in case_result.separate_components:
            rendered_component = separate_component.render_func()
            rendered_components[separate_component.name] = rendered_component

    return KeyboardComponents(
        switch_holder_result=switch_holder_result,
        connector=connector,
        components=rendered_components,
    )


def export_keyboard_to_stl(case_result: RenderCaseResult) -> RenderKeyboardResult:
    components = _render_keyboard_separate_components(case_result)

    export_case_to_stl(case_result)

    switch_holder = None
    if components.switch_holder_result:
        switch_holder = components.switch_holder_result.switch_holder
        export_switch_holder_to_stl(components.switch_holder_result)

    if components.connector:
        export_connector_to_stl(components.connector)

    for name, result in components.components.items():
        cq.exporters.export(result, f"{name}.stl")

    return RenderKeyboardResult(
        case_result=case_result,
        top=case_result.top,
        bottom=case_result.bottom,
        switch_holder=switch_holder,
        connector=components.connector,
        separate_components=components.components,
    )


def export_keyboard_to_step(case_result: RenderCaseResult) -> RenderKeyboardResult:
    components = _render_keyboard_separate_components(case_result)

    export_case_to_step(case_result)

    switch_holder = None
    if components.switch_holder_result:
        switch_holder = components.switch_holder_result.switch_holder
        export_switch_holder_to_step(components.switch_holder_result)

    if components.connector:
        export_connector_to_step(components.connector)

    for name, result in components.components.items():
        cq.exporters.export(result, f"{name}.step")

    return RenderKeyboardResult(
        case_result=case_result,
        top=case_result.top,
        bottom=case_result.bottom,
        switch_holder=switch_holder,
        connector=components.connector,
        separate_components=components.components,
    )
