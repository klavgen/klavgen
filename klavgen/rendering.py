from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import cadquery as cq

from .config import Config


class RenderingPipelineStage(Enum):
    CASE_SOLID = 0
    TOP_CUTOUTS = 1
    BOTTOM_AFTER_SHELL_ADDITIONS = 2
    BOTTOM_CUTOUTS = 3
    INNER_CLEARANCES = 4
    DEBUG = 5


@dataclass
class Renderable:
    render_func_name: str = ""
    name: str = ""


@dataclass
class RenderedItem:
    shape: cq.Workplane
    pipeline_stage: RenderingPipelineStage


@dataclass
class SeparateComponentRender:
    name: str
    render_func: Callable[[], cq.Workplane]
    render_in_place_func: Callable[[], cq.Workplane]


@dataclass
class RenderResult:
    name: str
    items: List[RenderedItem]
    separate_components: Optional[List[SeparateComponentRender]] = None


RendererFunc = Callable[[Any, Config], RenderResult]


class Renderers:
    def __init__(self):
        self.renderers: Dict[str, RendererFunc] = {}

    def set_renderer(self, name: str, render_func: RendererFunc):
        self.renderers[name] = render_func

    def get_renderer(self, name) -> RendererFunc:
        return self.renderers.get(name)


RENDERERS = Renderers()
