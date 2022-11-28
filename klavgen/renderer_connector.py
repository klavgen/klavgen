from typing import Any

import cadquery as cq

from .config import Config
from .utils import grow_yz


def render_connector(config: Config = Config()):
    conn_config = config.connector_config
    wp = cq.Workplane("XY")

    # Render back half, then mirror

    # Center console
    center_console_depth = (
        config.case_config.switch_plate_gap_to_palm_rest / 2
        + config.case_config.case_thickness
        + conn_config.horizontal_tolerance
    )
    connector = wp.box(
        conn_config.center_console_width, center_console_depth, conn_config.height, centered=grow_yz
    )

    # End tab
    end_tab = wp.center(0, center_console_depth).box(
        conn_config.end_tab_side_width * 2 + conn_config.center_console_width,
        conn_config.end_tab_depth,
        conn_config.height,
        centered=grow_yz,
    )
    end_tab = end_tab.edges(">Z and |Y").chamfer(conn_config.chamfer)
    connector = connector.union(end_tab)

    # Mirror
    connector_front = connector.mirror(mirrorPlane="XZ")
    connector = connector.union(connector_front)

    return connector


def render_connector_cutout(config: Config = Config()):
    conn_config = config.connector_config
    wp = cq.Workplane("XY")

    # Render back half, then mirror

    # Center console
    center_console_depth = (
        config.case_config.switch_plate_gap_to_palm_rest / 2 + config.case_config.case_thickness
    )
    connector_cutout = wp.box(
        conn_config.center_console_width + 2 * conn_config.horizontal_tolerance,
        center_console_depth,
        conn_config.height + conn_config.vertical_tolerance,
        centered=grow_yz,
    )

    # End tab
    end_tab = wp.center(0, center_console_depth).box(
        conn_config.end_tab_side_width * 2
        + conn_config.center_console_width
        + 2 * conn_config.horizontal_tolerance,
        conn_config.end_tab_depth + 2 * conn_config.horizontal_tolerance,
        conn_config.height + conn_config.vertical_tolerance,
        centered=grow_yz,
    )
    end_tab = end_tab.edges(">Z and |Y").chamfer(conn_config.chamfer)
    connector_cutout = connector_cutout.union(end_tab)

    # Mirror
    connector_front = connector_cutout.mirror(mirrorPlane="XZ")
    connector_cutout = connector_cutout.union(connector_front)

    return connector_cutout


def render_case_connector_support(config: Config = Config()) -> (Any, Any):
    connector_cutout = render_connector_cutout(config)
    conn_config = config.connector_config

    cutout_width = (
        conn_config.end_tab_side_width * 2
        + conn_config.center_console_width
        + 2 * conn_config.horizontal_tolerance
        + 2 * conn_config.tab_support_wall_size
    )
    cutout_depth = (
        config.case_config.case_thickness
        + conn_config.end_tab_depth
        + 2 * conn_config.horizontal_tolerance
        + conn_config.tab_support_wall_size
    )
    cutout_height = (
        conn_config.height + conn_config.vertical_tolerance + conn_config.tab_support_wall_size
    )

    wp = cq.Workplane("XY").center(0, config.case_config.switch_plate_gap_to_palm_rest / 2)

    support = wp.box(
        cutout_width,
        cutout_depth,
        cutout_height,
        centered=grow_yz,
    ).cut(connector_cutout)

    inner_clearance = wp.box(
        cutout_width + config.case_config.inner_volume_clearance * 2,
        cutout_depth + config.case_config.inner_volume_clearance,
        config.case_config.case_base_height,
        centered=grow_yz,
    )

    return support, inner_clearance


def export_connector_to_stl(connector):
    cq.exporters.export(connector, "connector.stl")


def export_connector_to_step(connector):
    cq.exporters.export(connector, "connector.step")
