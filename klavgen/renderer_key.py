from typing import Optional

import cadquery as cq

from .classes import Key, RenderedKey, RenderedKeyTemplates
from .config import CaseConfig, Config, MXKeyConfig, SwitchType
from .renderer_switch_holder import render_switch_holder, render_switch_hole
from .utils import create_workplane, grow_z, position


def render_case_clearance(config: MXKeyConfig, case_config: CaseConfig):
    return cq.Workplane("XY").box(
        config.case_tile_width,
        config.case_tile_depth,
        case_config.clearance_height,
        centered=grow_z,
    )


def render_keycap_clearance(config: MXKeyConfig, case_config: CaseConfig):
    return cq.Workplane("XY").box(
        config.keycap_clearance_width,
        config.keycap_clearance_depth,
        case_config.clearance_height,
        centered=grow_z,
    )


def render_key_templates(config: Config) -> RenderedKeyTemplates:
    case_config = config.case_config
    switch_holder_config = config.get_switch_holder_config()
    key_config = config.get_key_config()

    fused_switch_holder = None
    fused_switch_holder_clearance = None
    # fused_switch_holder_mirrored = None
    # fused_switch_holder_clearance_mirrored = None
    if case_config.use_switch_holders and case_config.switch_type == SwitchType.CHOC:
        switch_holder_result = render_switch_holder(config)

        fused_switch_holder = switch_holder_result.switch_holder
        fused_switch_holder_clearance = switch_holder_result.switch_holder_clearance

        if config.case_config.mirrored:
            # We need to keep the switch holders in the same orientation, so we mirror here, so that after the whole
            # case is mirrored they return to normal
            fused_switch_holder = fused_switch_holder.mirror(mirrorPlane="YZ")
            fused_switch_holder_clearance = fused_switch_holder_clearance.mirror(mirrorPlane="YZ")

    return RenderedKeyTemplates(
        switch_hole=render_switch_hole(case_config, switch_holder_config),
        case_clearance=render_case_clearance(key_config, case_config),
        keycap_clearance=render_keycap_clearance(key_config, case_config),
        fused_switch_holder=fused_switch_holder,
        fused_switch_holder_clearance=fused_switch_holder_clearance,
    )


def render_key(
    key: Key,
    templates: RenderedKeyTemplates,
    case_config: CaseConfig,
    config: MXKeyConfig,
) -> RenderedKey:
    base_wp = create_workplane(key)

    if (
        key.case_tile_margin_back is None
        and key.case_tile_margin_right is None
        and key.case_tile_margin_front is None
        and key.case_tile_margin_left is None
    ):
        # Use defaults

        # Case column (full-height)
        case_column = base_wp.workplane(offset=-key.z - case_config.case_base_height).box(
            config.case_tile_width,
            config.case_tile_depth,
            key.z + case_config.case_base_height,
            centered=grow_z,
        )

        # Case column clearance - bring keyboard to lowest level by cutting higher columns
        case_clearance = position(templates.case_clearance, key)
    else:
        # Use custom case tile margins

        case_tile_margin_back = (
            key.case_tile_margin_back
            if key.case_tile_margin_back is not None
            else config.case_tile_margin
        )
        case_tile_margin_right = (
            key.case_tile_margin_right
            if key.case_tile_margin_right is not None
            else config.case_tile_margin
        )
        case_tile_margin_front = (
            key.case_tile_margin_front
            if key.case_tile_margin_front is not None
            else config.case_tile_margin
        )
        case_tile_margin_left = (
            key.case_tile_margin_left
            if key.case_tile_margin_left is not None
            else config.case_tile_margin
        )

        case_tile_start_x = -case_tile_margin_left - config.switch_hole_width / 2
        case_tile_start_y = -case_tile_margin_front - config.switch_hole_depth / 2
        case_tile_width = case_tile_margin_left + config.switch_hole_width + case_tile_margin_right
        case_tile_depth = case_tile_margin_front + config.switch_hole_depth + case_tile_margin_back

        case_tile_wp = base_wp.center(case_tile_start_x, case_tile_start_y)

        # Case column (full-height)
        case_column = case_tile_wp.workplane(offset=-key.z - case_config.case_base_height).box(
            case_tile_width,
            case_tile_depth,
            key.z + case_config.case_base_height,
            centered=False,
        )

        # Case column clearance - bring keyboard to lowest level by cutting higher columns
        case_clearance = case_tile_wp.box(
            case_tile_width,
            case_tile_depth,
            case_config.clearance_height,
            centered=False,
        )

    # Switch support rim that overrides column clearance so there is something to support a switch
    # that's within the case column clearance area
    switch_rim = base_wp.workplane(offset=-key.z - case_config.case_base_height).box(
        config.switch_rim_width,
        config.switch_rim_depth,
        key.z + case_config.case_base_height,
        centered=grow_z,
    )

    # Vertical clearance for the keycap above the switch. Cuts into the switch rim of switches
    # that are unrealistically close
    keycap_clearance = position(templates.keycap_clearance, key)

    # The hole for the switch and holder
    switch_hole = templates.switch_hole
    if not config.north_facing:
        switch_hole = switch_hole.rotate((0, 0, 0), (0, 0, 1), 180)
    switch_hole = position(switch_hole, key)

    # Fused switch holder
    fused_switch_holder = templates.fused_switch_holder
    if fused_switch_holder:
        if not config.north_facing:
            fused_switch_holder = fused_switch_holder.rotate((0, 0, 0), (0, 0, 1), 180)

        fused_switch_holder = position(fused_switch_holder, key)

    fused_switch_holder_clearance = templates.fused_switch_holder_clearance
    if fused_switch_holder_clearance:
        if not config.north_facing:
            fused_switch_holder_clearance = fused_switch_holder_clearance.rotate(
                (0, 0, 0), (0, 0, 1), 180
            )

        fused_switch_holder_clearance = position(fused_switch_holder_clearance, key)

    # Debug: keycap outline in the air
    keycap_width = key.keycap_width or config.keycap_width
    keycap_depth = key.keycap_depth or config.keycap_depth
    debug = (
        base_wp.workplane(offset=5)
        .rect(keycap_width, keycap_depth)
        .rect(keycap_width - 1, keycap_depth - 1)
        .extrude(1)
    )

    return RenderedKey(
        case_column=case_column,
        case_clearance=case_clearance,
        switch_rim=switch_rim,
        keycap_clearance=keycap_clearance,
        switch_hole=switch_hole,
        fused_switch_holder=fused_switch_holder,
        fused_switch_holder_clearance=fused_switch_holder_clearance,
        debug=debug,
    )
