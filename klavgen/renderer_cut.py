import cadquery as cq

from .classes import Cut
from .config import CaseConfig


def render_cut(cut: Cut, case_config: CaseConfig):
    base_wp = cq.Workplane("XY").workplane(offset=-case_config.case_base_height)

    cut_body = base_wp.polyline(cut.points).close().extrude(cut.height)

    return cut_body
