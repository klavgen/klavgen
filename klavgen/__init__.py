from . import (
    classes,
    config,
    constants,
    keyboard,
    kle,
    renderer_case,
    renderer_connector,
    renderer_controller,
    renderer_kailh_mx_socket,
    renderer_kailh_choc_socket,
    renderer_key,
    renderer_switch_holder,
    renderer_trrs_jack,
)

import importlib

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

# Classes
from .classes import (
    Key,
    ScrewHole,
    Controller,
    Patch,
    Cut,
    Text,
    Controller,
    TrrsJack,
    PalmRest,
)

# Config
from .config import (
    SwitchType,
    CaseConfig,
    Config,
    ControllerConfig,
    KailhMXSocketConfig,
    MXKeyConfig,
    ChocKeyConfig,
    MXSwitchHolderConfig,
    ChocSwitchHolderConfig,
    TrrsJackConfig,
)

# Constants
from .constants import (
    MX_KEYCAP_1U_WIDTH,
    MX_KEYCAP_1_5U_WIDTH,
    MX_KEYCAP_1U_DEPTH,
    MX_KEY_X_SPACING,
    MX_KEY_Y_SPACING,
    CHOC_KEYCAP_1U_WIDTH,
    CHOC_KEYCAP_1U_DEPTH,
    CHOC_KEY_X_SPACING,
    CHOC_KEY_Y_SPACING,
)

# Methods
from .keyboard import render_and_save_keyboard
from .kle import generate_keys_from_kle_json
from .renderer_case import (
    RenderCaseResult,
    render_case,
    move_top,
    export_case_to_stl,
    export_case_to_step,
)
from .renderer_switch_holder import (
    render_switch_holder,
    render_choc_switch_holder,
    render_mx_switch_holder,
    export_switch_holder_to_stl,
    export_switch_holder_to_step,
)
from .renderer_controller import (
    render_controller_holder,
    export_controller_holder_to_stl,
    export_controller_holder_to_step,
)
from .renderer_trrs_jack import (
    render_trrs_jack_holder,
    export_trrs_jack_holder_to_stl,
    export_trrs_jack_holder_to_step,
)
from .renderer_kailh_mx_socket import draw_mx_socket
from .renderer_kailh_choc_socket import draw_choc_socket
from .renderer_connector import (
    render_connector,
    export_connector_to_stl,
    export_connector_to_step,
)
