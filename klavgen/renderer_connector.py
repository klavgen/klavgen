import cadquery as cq

from .config import CaseConfig


def render_connector_cutout(case_config: CaseConfig):
    wp = cq.Workplane("XY").tag("base")

    # TODO: assumes switch_plate_gap_to_palm_rest is 0.5

    connector_cutout = (
        wp.box(6.2, 2.2, 5.2, centered=False)
        .workplaneFromTagged("base")
        .center(2, 2.2)
        .box(2.2, 4.5 - 0.2 + 0.2, 5, centered=False)
        .workplaneFromTagged("base")
        .center(0, 6.5 + 0.2)
        .box(6.2, 2.2, 5.2, centered=False)
        .translate((-3 - 0.1, -8.5 / 2 - 0.2, 0))
        .edges(">Z and (>X or <X) and |Y")
        .chamfer(2)
    )

    return connector_cutout


def render_connector(case_config: CaseConfig):
    wp = cq.Workplane("XY").tag("base")

    # TODO: assumes switch_plate_gap_to_palm_rest is 0.5

    connector = (
        wp.box(6, 2, 5, centered=False)
        .workplaneFromTagged("base")
        .center(2, 2)
        .box(2, 4.7, 5, centered=False)
        .workplaneFromTagged("base")
        .center(0, 6.7)
        .box(6, 2, 5, centered=False)
        .translate((-3, -8.5 / 2 - 0.1, 0))
        .edges(">Z and (>X or <X) and |Y")
        .chamfer(2)
    )

    return connector


def render_case_connector_support(case_config: CaseConfig):
    connector_cutout = render_connector_cutout(case_config)

    return (
        cq.Workplane("XY")
        .box(8, 5, 6, centered=(True, False, False))
        .translate((0, case_config.switch_plate_gap_to_palm_rest / 2, 0))
        .cut(connector_cutout)
    )


def export_connector_to_stl(connector):
    cq.exporters.export(connector, "connector.stl")


def export_connector_to_step(connector):
    cq.exporters.export(connector, "connector.step")
