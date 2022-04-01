import cadquery as cq
from .classes import PalmRest
from .config import CaseConfig


def render_palm_rest(palm_rest: PalmRest, case_config: CaseConfig = CaseConfig()):
    base_wp = cq.Workplane("XY").workplane(offset=-case_config.case_base_height)

    palm_rest_body = base_wp.polyline(palm_rest.points).close().extrude(palm_rest.height)

    return palm_rest_body
