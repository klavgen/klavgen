import cadquery as cq

from .classes import Patch
from .config import CaseConfig


def render_patch(patch: Patch, case_config: CaseConfig = CaseConfig()):
    base_wp = cq.Workplane("XY").workplane(offset=-case_config.case_base_height)

    patch_body = base_wp.polyline(patch.points).close().extrude(patch.height)

    return patch_body
