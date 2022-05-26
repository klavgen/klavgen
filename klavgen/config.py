from dataclasses import dataclass
from typing import Optional


@dataclass
class CaseConfig:
    case_thickness: float = 2

    # Total height, including top and bottom thickness
    # 11 = 5.2 switch holder (incl top thickness of 2) + 1 socket bumps + 1.8 socket + 1 socket base + 2 bottom
    # thickness
    case_base_height: float = 11

    # Global clearance height
    clearance_height: float = 100

    switch_plate_gap_to_palm_rest: float = 0.5
    side_fillet: Optional[float] = None
    switch_plate_top_fillet: Optional[float] = 0.5
    palm_rests_top_fillet: Optional[float] = None

    detachable_palm_rests: bool = True

    def __post_init__(self):
        self.case_inner_height = self.case_base_height - 2 * self.case_thickness


@dataclass
class ScrewHoleConfig:
    screw_rim_radius: float = 3.5  # Want 2 mm wall around it = 7mm diameter = 3.5mm radius
    screw_hole_body_radius: float = 1.5  # M3 = 3mm diameter = 1.5mm radius
    screw_hole_plate_radius: float = (
        1.7  # On the plate we want some room so we don't touch the screw = 1.7mm
    )
    screw_head_radius: float = (
        3  # Head is 5.5 mm, want 0.25 buffer from each side = 6mm diameter = 3mm radius
    )

    screw_insert_hole_width: float = 1.7  # 3.4 mm radius
    screw_insert_depth: float = 6


@dataclass
class KailhSocketConfig:
    # Kailh socket heights
    socket_height: float = 1.8
    socket_bump_height: float = 1

    pin_top_clearance_height: float = 0.4

    # Kailh socket outline, including solder pins
    front_flat_width: float = 9.50

    right_flat_depth_in_front_of_solder_pin: float = 0.9
    right_flat_depth_solder_pin: float = 2.6
    right_flat_depth_behind_solder_pin: float = 0.5

    left_flat_depth_in_front_of_solder_pin: float = 0.4
    left_flat_depth_behind_solder_pin: float = 1.2

    back_right_flat_width: float = 4.00

    large_radius: float = 2
    small_radius: float = 1.8

    solder_pin_width: float = 4.00

    socket_total_depth: float = (
        large_radius
        + right_flat_depth_in_front_of_solder_pin
        + right_flat_depth_solder_pin
        + right_flat_depth_behind_solder_pin
    )
    socket_thin_part_depth: float = socket_total_depth - small_radius

    left_flat_depth_solder_pin: float = (
        socket_thin_part_depth
        - left_flat_depth_in_front_of_solder_pin
        - left_flat_depth_behind_solder_pin
    )

    back_flat_width: float = front_flat_width + large_radius - back_right_flat_width - small_radius
    socket_total_width: float = front_flat_width + large_radius

    # Switch pin bumps
    socket_bump_radius: float = 1.6

    socket_bump_1_x: float = 2.6
    socket_bump_1_y: float = 1.8

    socket_bump_2_x: float = 8.95
    socket_bump_2_y: float = 4.3

    # Offsets from center
    socket_center_x_offset: float = -5.3
    socket_center_y_offset: float = -7

    # Final switch pin bump coordinates
    socket_bump_1_x_from_center: float = socket_bump_1_x + socket_center_x_offset
    socket_bump_1_y_from_center: float = socket_bump_1_y + socket_center_y_offset
    socket_bump_2_x_from_center: float = socket_bump_2_x + socket_center_x_offset
    socket_bump_2_y_from_center: float = socket_bump_2_y + socket_center_y_offset

    # Final bounding box
    socket_left_end_x = (
        socket_center_x_offset  # start X is just the offset, since we start sketching from X = 0
    )
    socket_right_end_x = socket_total_width + socket_center_x_offset

    socket_front_end_y: float = (
        socket_center_y_offset  # start Y is just the offset, since we start sketching from Y = 0
    )

    socket_back_left_end_y: float = socket_thin_part_depth + socket_center_y_offset
    socket_back_right_end_y: float = socket_total_depth + socket_center_y_offset


@dataclass
class SwitchHolderConfig:
    case_config: CaseConfig = CaseConfig()
    kailh_socket_config: KailhSocketConfig = KailhSocketConfig()

    # Switch hole
    switch_hole_tolerance: float = 0.05

    switch_hole_width: float = 14 - switch_hole_tolerance
    switch_hole_depth: float = 14 - switch_hole_tolerance

    # Front hole
    plate_front_hole_depth: float = 1.1
    plate_front_hole_width: float = 6

    # Holder

    switch_bottom_height: float = 3.2

    holder_plate_gap: float = 0.1

    holder_side_bottom_wall_width: float = 2.3
    holder_front_back_wall_depth: float = plate_front_hole_depth - holder_plate_gap

    socket_base_height: float = 1

    holder_width: float = switch_hole_width + 2 * holder_side_bottom_wall_width
    holder_depth: float = switch_hole_depth + 2 * holder_front_back_wall_depth
    holder_bottom_height: float = (
        socket_base_height
        + kailh_socket_config.socket_height
        + kailh_socket_config.socket_bump_height
    )
    holder_height: float = holder_bottom_height + switch_bottom_height

    holder_height_to_pin_top: float = (
        socket_base_height
        + kailh_socket_config.socket_height
        + kailh_socket_config.pin_top_clearance_height
    )

    switch_hole_min_height: float = holder_height + case_config.case_thickness

    # Socket lips to prevent it from sliding out
    socket_lip_width: float = 0.4
    socket_lip_height: float = 0.2

    # Y cutoffs
    cutoff_y_behind_socket: float = 0.5

    cutoff_front_base_y: float = kailh_socket_config.socket_back_left_end_y + cutoff_y_behind_socket

    cutoff_y: float = 8.2

    cutoff_back_bottom_y: float = 8.2

    # Plate holes

    # Side holes
    plate_side_hole_width: float = 1.8
    plate_right_side_hole_depth: float = 7
    plate_left_side_hole_depth: float = 7

    plate_front_hole_start_y: float = -switch_hole_depth / 2 - plate_front_hole_depth

    # Holder top walls
    holder_side_top_wall_width: float = plate_side_hole_width - holder_plate_gap
    holder_side_top_wall_x_offset: float = (
        holder_side_bottom_wall_width - holder_side_top_wall_width
    )

    # Switch plastic pin holes
    switch_hole_1_x: float = -5
    switch_hole_1_y: float = 0
    switch_hole_1_radius: float = 1.1  # 0.875

    switch_hole_2_x: float = 0
    switch_hole_2_y: float = 0
    switch_hole_2_radius: float = 2.2  # 2.1

    switch_hole_3_x: float = 5
    switch_hole_3_y: float = 0
    switch_hole_3_radius: float = 1.1  # 0.875

    # Front cutout to ease removal
    front_removal_cutout_width: float = 3

    # Bottom cutout for wires and diode
    base_cutout_width_within_socket_body: float = 1.7

    # Switch metal pins extension holes in base
    switch_metal_pin_base_hole_radius: float = 1

    # Top brackets/lips
    holder_lips_start_below_case_top: float = 0.2
    holder_lips_chamfer_top: float = 0.7

    # Top side lips
    holder_side_lips_width: float = 0.9
    holder_side_lips_base_width: float = 1
    holder_side_lips_top_width: float = 0.6

    holder_left_lips_depth: float = plate_left_side_hole_depth - holder_plate_gap
    holder_right_lips_depth: float = plate_right_side_hole_depth - holder_plate_gap

    holder_side_lips_top_lip_height: float = (
        holder_side_lips_width + holder_side_lips_base_width - holder_side_lips_top_width
    )

    # Top front bump

    holder_front_lock_bump_side_plate_gap: float = 0.2
    holder_front_lock_bump_width = (
        plate_front_hole_width - 2 * holder_front_lock_bump_side_plate_gap
    )
    holder_front_lock_bump_height = 1.8

    holder_total_height: float = (
        holder_height
        + case_config.case_thickness
        - holder_lips_start_below_case_top
        + holder_side_lips_width
        + holder_side_lips_top_lip_height
    )

    # Side profiles

    left_profile_bottom_start_y = 3.7
    right_profile_bottom_start_y = 6

    front_wire_supports_depth = 1.2

    # Row wire cutout

    row_wire_cutout_depth = 1.6  # 1.2

    # Diode & wire

    diode_depth = 4
    diode_diameter = 2.1
    diode_wire_diameter = 0.55

    diode_center_from_left_end = 3.6
    diode_center_y = 3.5

    # Diode back cutout

    diode_back_wall_depth = 1
    diode_back_cutout_width = 6

    # Diode wire front support

    diode_wire_front_support_x_gap = 1.5
    diode_wire_front_support_cutout_z_offset = 1.6
    diode_wire_front_support_cutout_height = 0.5

    # Diode wire front triangular cutout

    diode_wire_front_triangular_cutout_edge = 1.5

    # Diode lips

    diode_bottom_lips_z_offset = 0.8
    diode_bottom_lips_width = 0.32
    diode_bottom_lips_height = 1
    diode_top_lips_size = 0.65

    # Col wire cutout

    col_wire_cutout_width = 0.9
    col_wire_cutout_height = 1.5
    col_wire_lips_width = 0.15
    col_wire_lips_height = 0.3

    col_wire_cutout_offset_from_right_end = 0.8
    col_wire_lips_offset_from_cutout_top = 0.6
    col_wire_support_width_on_left = 1

    # Vertical cut

    vertical_cut_left_hole_start_y_offset = 0.001

    # Back side cuts

    back_side_cut_start_behind_lips = 1
    back_side_cut_left = 1
    back_side_cut_right = 1


@dataclass
class KeyConfig:
    switch_holder_config: SwitchHolderConfig = SwitchHolderConfig()

    # Orientation
    north_facing: float = False

    # Case tile
    case_tile_margin_add_back_tolerance: bool = True
    case_tile_margin: float = 8

    # Keycap
    keycap_width: float = 19
    keycap_depth: float = 19

    # Need enough space for the socket holder lips
    switch_rim_width: float = 19
    switch_rim_depth: float = 19

    # Amoeba royale screw post
    amoeba_royale: bool = False
    amoeba_plot_height: float = 2.2
    amoeba_hole_diameter: float = 1.8
    amoeba_plot_diameter: float = 2.5
    
    def __post_init__(self):
        if self.case_tile_margin_add_back_tolerance:
            self.case_tile_margin += self.switch_holder_config.switch_hole_tolerance / 2

        self.case_tile_width: float = (
            self.switch_holder_config.switch_hole_width + self.case_tile_margin * 2
        )
        self.case_tile_depth: float = (
            self.switch_holder_config.switch_hole_depth + self.case_tile_margin * 2
        )


@dataclass
class SideHolderConfig:
    item_width: float
    side_supports_width: float
    rail_width: float

    item_depth: float
    front_support_depth: float
    back_support_depth: float

    holder_height: float

    case_hole_width: float

    item_width_tolerance: float = 0.1
    item_depth_tolerance: float = 0.1

    case_tile_margin: float = 7

    case_hole_start_from_case_bottom: float = 0.0
    case_hole_depth_in_front_of_wall: float = 1.4
    case_hole_clearance_depth: float = 10.0

    rail_wall_width: float = 0.8
    rail_wall_depth: float = 1.6

    rail_width_inset: float = 0.2

    rail_latch_depth: float = 0.2
    rail_latch_hole_depth: float = 0.3
    rail_latch_base_height: float = 1.6
    rail_latch_base_width: float = 1.2

    rail_latch_tip_height: float = 0.8

    rail_latch_offset_from_side: float = 0.4

    tolerance: float = 0.15

    def __post_init__(self):
        self.width = (
            self.item_width
            + 2 * self.item_width_tolerance
            + 2 * self.side_supports_width
            + 2 * self.rail_width
        )
        self.depth = (
            self.item_depth
            + 2 * self.item_depth_tolerance
            + self.front_support_depth
            + self.back_support_depth
        )
        self.holder_rail_width = self.rail_width - self.rail_width_inset
        self.rail_latch_tip_width = self.rail_latch_base_width - 2 * self.rail_latch_depth
        self.rail_latch_offset_from_bottom: float = (
            self.holder_height / 2 - self.rail_latch_base_height / 2
        )


@dataclass
class ControllerConfig(SideHolderConfig):
    item_width: float = 18

    side_supports_width: float = 1
    rail_width: float = 2

    item_depth: float = 33
    front_support_depth: float = 1.4
    back_support_depth: float = 1.4

    case_hole_width: float = 18

    holder_height: float = 4.7


@dataclass
class TrrsJackConfig(SideHolderConfig):
    item_width: float = 6

    side_supports_width: float = 1
    rail_width: float = 2

    item_depth: float = 12
    front_support_depth: float = 1.4
    back_support_depth: float = 2

    case_hole_width: float = 10

    holder_height: float = 7

    holder_hole_width: float = 5.3
    holder_right_bracket_depth: float = 9.5
    holder_left_front_bracket_depth: float = 2
    holder_left_bracket_gap: float = 5
    holder_left_back_bracket_depth: float = 2
    holder_bracket_lip_height: float = 1
    holder_bracket_lip_protrusion: float = 0.3
    holder_bracket_lip_start_before_top: float = 0.2
    holder_back_hole_depth: float = 1.0
    holder_back_hole_radius: float = 2


@dataclass
class Config:
    case_config: CaseConfig = CaseConfig()

    screw_hole_config: ScrewHoleConfig = ScrewHoleConfig()
    kailh_socket_config: KailhSocketConfig = KailhSocketConfig()
    # TODO: fix overriding
    switch_holder_config: SwitchHolderConfig = SwitchHolderConfig(
        case_config=case_config, kailh_socket_config=kailh_socket_config
    )
    key_config: KeyConfig = KeyConfig(switch_holder_config=switch_holder_config)
    controller_config: ControllerConfig = ControllerConfig()
    trrs_jack_config: TrrsJackConfig = TrrsJackConfig()
