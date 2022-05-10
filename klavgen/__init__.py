from . import (
    classes,
    config,
    keyboard,
    kle,
    renderer_case,
    renderer_connector,
    renderer_controller,
    renderer_kailh_socket,
    renderer_key,
    renderer_switch_holder,
    renderer_trrs_jack,
)

import importlib

importlib.reload(classes)
importlib.reload(config)
importlib.reload(keyboard)
importlib.reload(kle)
importlib.reload(renderer_case)
importlib.reload(renderer_connector)
importlib.reload(renderer_controller)
importlib.reload(renderer_kailh_socket)
importlib.reload(renderer_key)
importlib.reload(renderer_switch_holder)
importlib.reload(renderer_trrs_jack)

# Classes
from .classes import Key, ScrewHole, Controller, Patch, Cut, Text, Controller, TrrsJack, PalmRest

# Config
from .config import (
    CaseConfig,
    Config,
    ControllerConfig,
    KailhSocketConfig,
    KeyConfig,
    SwitchHolderConfig,
    TrrsJackConfig,
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
from .renderer_kailh_socket import draw_socket
from .renderer_connector import render_connector, export_connector_to_stl, export_connector_to_step
