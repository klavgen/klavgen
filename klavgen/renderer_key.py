import cadquery as cq

from .classes import Key, RenderedKey, RenderedKeyTemplates
from .config import CaseConfig, MXKeyConfig, MXSwitchHolderConfig
from .renderer_switch_holder import render_switch_hole
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


def render_key_templates(
    case_config: CaseConfig, config: MXSwitchHolderConfig
) -> RenderedKeyTemplates:
    return RenderedKeyTemplates(
        switch_hole=render_switch_hole(case_config, config),
        case_clearance=render_case_clearance(config.key_config, case_config),
        keycap_clearance=render_keycap_clearance(config.key_config, case_config),
    )


def render_key(
    key: Key,
    templates: RenderedKeyTemplates,
    case_config: CaseConfig,
    config: MXKeyConfig,
) -> RenderedKey:
    base_wp = create_workplane(key)

    # Case column (full-height)
    case_column = base_wp.workplane(offset=-key.z - case_config.case_base_height).box(
        config.case_tile_width,
        config.case_tile_depth,
        key.z + case_config.case_base_height,
        centered=grow_z,
    )

    # Case column clearance - bring keyboard to lowest level by cutting higher columns
    case_clearance = position(templates.case_clearance, key)

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

    # The whole for the switch assembly
    switch_hole = templates.switch_hole
    if not config.north_facing:
        switch_hole = switch_hole.rotate((0, 0, 0), (0, 0, 1), 180)
    switch_hole = position(switch_hole, key)

    # Debug: keycap outline in the air
    keycap_width = key.keycap_width or config.keycap_width
    keycap_depth = key.keycap_depth or config.keycap_depth
    debug = (
        base_wp.workplane(offset=5)
        .rect(keycap_width, keycap_depth)
        .rect(keycap_width - 1, keycap_depth - 1)
        .extrude(1)
    )

    if config.amoeba_royale:
        amoeba_royale_post= (base_wp.workplane(offset=-case_config.case_thickness)
            .center(9.5,1.16)
            .circle(config.amoeba_plot_diameter)
            .extrude(-config.amoeba_plot_height)
            .hole(config.amoeba_hole_diameter)
        )
        
        amoeba_royale_post= amoeba_royale_post.union(
            base_wp.workplane(offset=-case_config.case_thickness)
            .center(-9.5,1.16)
            .circle(config.amoeba_plot_diameter)
            .extrude(-config.amoeba_plot_height)
            .hole(config.amoeba_hole_diameter)
        )
    
    return RenderedKey(
        case_column=case_column,
        case_clearance=case_clearance,
        switch_rim=switch_rim,
        keycap_clearance=keycap_clearance,
        switch_hole=switch_hole,
        amoeba_royale_post=amoeba_royale_post,
        debug=debug,
    )
