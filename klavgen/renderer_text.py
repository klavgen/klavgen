import cadquery as cq

from .classes import Text
from .utils import position


def render_text(text: Text):
    base_wp = cq.Workplane("XY")

    text_body = base_wp.text(txt=text.text, fontsize=text.font_size, distance=text.extrude)

    text_body = position(text_body, text)

    return text_body
