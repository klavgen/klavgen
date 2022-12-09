from dataclasses import dataclass
from typing import List, Optional, Tuple

import cadquery as cq

from .rendering import Renderable


@dataclass
class LocationOrientation:
    x: float
    y: float
    z: float = 0.0
    rotate: float = 0.0  # CCW
    rotate_around: Optional[Tuple[float, float]] = None


@dataclass
class Key(LocationOrientation):
    keycap_width: Optional[float] = None
    keycap_depth: Optional[float] = None
    case_tile_margin_back: Optional[float] = None
    case_tile_margin_right: Optional[float] = None
    case_tile_margin_front: Optional[float] = None
    case_tile_margin_left: Optional[float] = None


@dataclass
class RenderedKey:
    case_column: cq.Workplane
    case_clearance: cq.Workplane
    switch_rim: cq.Workplane
    keycap_clearance: cq.Workplane
    switch_hole: cq.Workplane
    fused_switch_holder: cq.Workplane
    fused_switch_holder_clearance: cq.Workplane
    fused_switch_holder_mirrored: cq.Workplane
    fused_switch_holder_clearance_mirrored: cq.Workplane
    debug: cq.Workplane


@dataclass
class RenderedKeyTemplates:
    switch_hole: cq.Workplane
    case_clearance: cq.Workplane
    keycap_clearance: cq.Workplane
    fused_switch_holder: cq.Workplane
    fused_switch_holder_clearance: cq.Workplane
    fused_switch_holder_mirrored: cq.Workplane
    fused_switch_holder_clearance_mirrored: cq.Workplane


@dataclass
class ScrewHole(Renderable, LocationOrientation):
    name = "screw_hole"
    render_func_name: str = "screw_hole"


@dataclass
class RenderedScrewHole:
    rim: cq.Workplane
    rim_bottom: cq.Workplane
    rim_inner_clearance: cq.Workplane
    hole: cq.Workplane
    debug: cq.Workplane


@dataclass
class Patch:
    points: List[Tuple[float, float]]
    height: float


@dataclass
class Cut:
    points: List[Tuple[float, float]]
    height: float


@dataclass
class Text(LocationOrientation):
    text: str = ""
    font_size: float = 6
    extrude: float = 0.4


@dataclass
class RenderedSideHolder:
    case_column: cq.Workplane
    rail: cq.Workplane
    inner_clearance: cq.Workplane
    hole: cq.Workplane
    debug: cq.Workplane


@dataclass
class Controller(Renderable, LocationOrientation):
    name = "controller"
    render_func_name: str = "controller"


@dataclass
class TRRSJack(Renderable, LocationOrientation):
    name = "trrs_jack"
    render_func_name: str = "trrs_jack"


@dataclass
class USBCJack(Renderable, LocationOrientation):
    name = "usbc_jack"
    render_func_name: str = "usbc_jack"


@dataclass
class PalmRest:
    points: List[Tuple[float, float]]
    height: float
    connector_locations_x: Optional[List[float]] = None


@dataclass
class RenderedSwitchHolder:
    switch_holder: cq.Workplane
    switch_holder_clearance: Optional[cq.Workplane]
    socket: cq.Workplane
