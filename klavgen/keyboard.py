from dataclasses import dataclass
from typing import List, Optional, Any

from .renderer_switch_holder import (
    render_mx_switch_holder,
    render_choc_switch_holder,
    export_switch_holder_to_stl,
)
from .renderer_connector import render_connector, export_connector_to_stl
from .renderer_controller import (
    render_controller_holder,
    export_controller_holder_to_stl,
)
from .renderer_trrs_jack import render_trrs_jack_holder, export_trrs_jack_holder_to_stl
from .renderer_case import RenderCaseResult, render_case, export_case_to_stl
from .config import Config, SwitchType
from .classes import Key, ScrewHole, Controller, TrrsJack, Patch, Cut, PalmRest, Text


@dataclass
class RenderKeyboardResult:
    case_result: RenderCaseResult
    top: Any
    bottom: Any
    switch_holder: Any
    connector: Optional[Any] = None
    controller_holder: Optional[Any] = None
    trrs_jack_holder: Optional[Any] = None
    palm_rests: Optional[List[Any]] = None


def render_and_save_keyboard(
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
    config: Optional[Config] = None,
) -> RenderKeyboardResult:
    """
    The core method that renders and saves as STL files all keyboard components.

    :param keys: A list of Key objects defining the key positions. Required.
    :param screw_holes: A list of ScrewHole objects defining the screw hole positions. Optional.
    :param controller: A Controller object defining where the controller back center is. Optional.
    :param trrs_jack: A TrrsJack object defining where the TRRS jack back center is. Optional.
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
        screw_holes=screw_holes,
        controller=controller,
        trrs_jack=trrs_jack,
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
    switch_holder_result = (
        render_mx_switch_holder(config)
        if config.case_config.switch_type == SwitchType.MX
        else render_choc_switch_holder(config)
    )

    export_case_to_stl(case_result)
    export_switch_holder_to_stl(switch_holder_result)

    controller_holder = None
    if controller:
        controller_holder = render_controller_holder(config.controller_config)
        export_controller_holder_to_stl(controller_holder)

    trrs_jack_holder = None
    if trrs_jack:
        trrs_jack_holder = render_trrs_jack_holder(config.trrs_jack_config)
        export_trrs_jack_holder_to_stl(trrs_jack_holder)

    palm_rests = None
    connector = None
    if case_result.palm_rests:
        connector = render_connector(config.case_config)
        palm_rests = case_result.palm_rests

        export_connector_to_stl(connector)

    return RenderKeyboardResult(
        case_result=case_result,
        top=case_result.top,
        bottom=case_result.bottom,
        switch_holder=switch_holder_result.switch_holder,
        connector=connector,
        controller_holder=controller_holder,
        trrs_jack_holder=trrs_jack_holder,
        palm_rests=palm_rests,
    )
