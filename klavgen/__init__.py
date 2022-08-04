import importlib

from . import (
    classes,
    config,
    constants,
    keyboard,
    kle,
    renderer_case,
    renderer_connector,
    renderer_controller,
    renderer_kailh_choc_socket,
    renderer_kailh_mx_socket,
    renderer_key,
    renderer_switch_holder,
    renderer_trrs_jack,
    renderer_usbc_jack,
    rendering,
)

importlib.reload(rendering)
importlib.reload(classes)
importlib.reload(config)
importlib.reload(constants)
importlib.reload(keyboard)
importlib.reload(kle)
importlib.reload(renderer_case)
importlib.reload(renderer_connector)
importlib.reload(renderer_controller)
importlib.reload(renderer_kailh_mx_socket)
importlib.reload(renderer_kailh_choc_socket)
importlib.reload(renderer_key)
importlib.reload(renderer_switch_holder)
importlib.reload(renderer_trrs_jack)
importlib.reload(renderer_usbc_jack)


# Classes
from .classes import (
    Controller,
    Cut,
    Key,
    PalmRest,
    Patch,
    Renderable,
    ScrewHole,
    Text,
    TrrsJack,
    USBCJack,
)

# Config
from .config import (
    CaseConfig,
    ChocKeyConfig,
    ChocSwitchHolderConfig,
    Config,
    ControllerConfig,
    KailhMXSocketConfig,
    MXKeyConfig,
    MXSwitchHolderConfig,
    SwitchType,
    TrrsJackConfig,
    USBCJackConfig,
)

# Constants
from .constants import (
    CHOC_KEY_X_SPACING,
    CHOC_KEY_Y_SPACING,
    CHOC_KEYCAP_1U_DEPTH,
    CHOC_KEYCAP_1U_WIDTH,
    MX_KEY_X_SPACING,
    MX_KEY_Y_SPACING,
    MX_KEYCAP_1_5U_WIDTH,
    MX_KEYCAP_1U_DEPTH,
    MX_KEYCAP_1U_WIDTH,
)

# Methods
from .keyboard import render_and_save_keyboard
from .kle import generate_keys_from_kle_json
from .renderer_case import (
    RenderCaseResult,
    export_case_to_step,
    export_case_to_stl,
    move_top,
    render_case,
)
from .renderer_connector import export_connector_to_step, export_connector_to_stl, render_connector
from .renderer_controller import (
    export_controller_holder_to_step,
    export_controller_holder_to_stl,
    render_controller_holder,
)
from .renderer_kailh_choc_socket import draw_choc_socket
from .renderer_kailh_mx_socket import draw_mx_socket
from .renderer_switch_holder import (
    export_switch_holder_to_step,
    export_switch_holder_to_stl,
    render_choc_switch_holder,
    render_mx_switch_holder,
    render_switch_holder,
)
from .renderer_trrs_jack import (
    export_trrs_jack_holder_to_step,
    export_trrs_jack_holder_to_stl,
    render_trrs_jack_holder,
)
from .renderer_usbc_jack import (
    export_usbc_jack_holder_to_step,
    export_usbc_jack_holder_to_stl,
    render_usbc_jack_holder,
)
