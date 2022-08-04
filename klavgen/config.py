from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class SwitchType(Enum):
    MX = 0
    CHOC = 1


@dataclass
class MXKeyConfig:
    # Switch hole
    switch_width: float = 14
    switch_depth: float = 14
    switch_hole_tolerance: float = 0.05

    # Orientation
    north_facing: float = False

    # Case tile
    case_tile_margin_add_back_tolerance: bool = True
    case_tile_margin: float = 8

    # Keycap
    keycap_width: float = 18
    keycap_depth: float = 18
    clearance_margin: float = 1

    # Need enough space for the socket holder lips
    switch_rim_width: float = 19
    switch_rim_depth: float = 19

    def __post_init__(self):
        self.switch_hole_width: float = self.switch_width - self.switch_hole_tolerance
        self.switch_hole_depth: float = self.switch_depth - self.switch_hole_tolerance

        if self.case_tile_margin_add_back_tolerance:
            self.case_tile_margin += self.switch_hole_tolerance / 2

        self.case_tile_width: float = self.switch_hole_width + self.case_tile_margin * 2
        self.case_tile_depth: float = self.switch_hole_depth + self.case_tile_margin * 2
        self.keycap_clearance_width = self.keycap_width + self.clearance_margin
        self.keycap_clearance_depth = self.keycap_depth + self.clearance_margin


@dataclass
class ChocKeyConfig(MXKeyConfig):
    # Switch hole
    switch_width: float = 13.8
    switch_depth: float = 13.8

    # Keycap
    keycap_width: float = 17.5
    keycap_depth: float = 16.5

    # Case tile
    case_tile_margin: float = 8.1  # Bump up to produce same outlines as MX


@dataclass
class CaseConfig:
    switch_type: SwitchType = SwitchType.MX
    use_switch_holders: bool = True

    case_thickness: float = 2  # 2.4

    # Total height, including top and bottom thickness
    # MX: 11 = 5 switch holder (incl top thickness of 2) + 0.2 buffer + 1 socket bumps + 1.8 socket + 1 socket base +
    #   2 bottom thickness
    # Choc: 9 = 2.4 switch holder/top thickness (incl buffer of 0.2) + 4.2 usbc socket (disregard 1.2 socket bumps + 1.8 socket) +
    #   + 2.4 bottom thickness
    case_base_height: float = 11  # 9

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
class SocketConfig:
    socket_height: float = field(init=False)
    socket_total_depth: float = field(init=False)

    socket_bump_1_x_from_center: float = field(init=False)
    socket_bump_1_y_from_center: float = field(init=False)
    socket_bump_2_x_from_center: float = field(init=False)
    socket_bump_2_y_from_center: float = field(init=False)

    socket_locking_lip_start_x: float = field(init=False)
    socket_locking_lip_start_y: float = field(init=False)
    socket_locking_lip_width: float = field(init=False)

    socket_left_end_x: float = field(init=False)
    socket_right_end_x: float = field(init=False)

    solder_pin_width: float = field(init=False)


@dataclass
class KailhMXSocketConfig(SocketConfig):
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

    # Switch pin bumps
    socket_bump_radius: float = 1.6

    socket_bump_1_x: float = 2.6
    socket_bump_1_y: float = 1.8

    socket_bump_2_x: float = 8.95
    socket_bump_2_y: float = 4.3

    # Offsets from center
    socket_center_x_offset: float = -5.3
    socket_center_y_offset: float = -7

    def __post_init__(self):
        # Kailh socket outline, including solder pins
        self.socket_total_depth: float = (
            self.large_radius
            + self.right_flat_depth_in_front_of_solder_pin
            + self.right_flat_depth_solder_pin
            + self.right_flat_depth_behind_solder_pin
        )
        self.socket_thin_part_depth: float = self.socket_total_depth - self.small_radius

        self.left_flat_depth_solder_pin: float = (
            self.socket_thin_part_depth
            - self.left_flat_depth_in_front_of_solder_pin
            - self.left_flat_depth_behind_solder_pin
        )

        self.back_flat_width: float = (
            self.front_flat_width
            + self.large_radius
            - self.back_right_flat_width
            - self.small_radius
        )
        self.socket_total_width: float = self.front_flat_width + self.large_radius

        # Final switch pin bump coordinates
        self.socket_bump_1_x_from_center: float = self.socket_bump_1_x + self.socket_center_x_offset
        self.socket_bump_1_y_from_center: float = self.socket_bump_1_y + self.socket_center_y_offset
        self.socket_bump_2_x_from_center: float = self.socket_bump_2_x + self.socket_center_x_offset
        self.socket_bump_2_y_from_center: float = self.socket_bump_2_y + self.socket_center_y_offset

        # Final bounding box
        self.socket_left_end_x: float = (
            self.socket_center_x_offset  # start X is just the offset, since we start sketching from X = 0
        )
        self.socket_right_end_x: float = self.socket_total_width + self.socket_center_x_offset

        self.socket_front_end_y: float = (
            self.socket_center_y_offset  # start Y is just the offset, since we start sketching from Y = 0
        )

        self.socket_back_right_end_y: float = self.socket_total_depth + self.socket_center_y_offset

        self.socket_locking_lip_start_y: float = (
            self.socket_thin_part_depth + self.socket_center_y_offset
        )
        self.socket_locking_lip_start_x: float = self.socket_left_end_x
        self.socket_locking_lip_width: float = self.back_flat_width


@dataclass
class KailhChocSocketConfig(SocketConfig):
    back_left_width: float = 5
    front_right_width: float = 4.75
    left_depth: float = 4.65
    right_depth: float = 4.65
    socket_total_depth: float = 6.85
    total_width: float = 9.55

    socket_height: float = 1.8

    pins_inset_depth: float = 1
    solder_pin_width: float = 1.9
    pin_top_clearance_height: float = 0.4

    bump_x_distance: float = 5
    bump_y_distance: float = -2.2

    socket_bump_radius: float = 1.6
    socket_bump_height: float = 1.25

    socket_bump_1_x: float = 2.4

    front_right_corner_protrusion_width: float = 0.5

    # Offsets from center
    socket_bump_1_center_x_offset: float = -5
    socket_bump_1_center_y_offset: float = -3.8

    def __post_init__(self):

        self.left_y_offset: float = self.socket_total_depth - self.left_depth
        self.right_y_space_behind: float = self.socket_total_depth - self.right_depth

        self.socket_bump_1_y: float = self.left_y_offset + self.left_depth / 2

        self.socket_bump_2_x: float = self.socket_bump_1_x + self.bump_x_distance
        self.socket_bump_2_y: float = self.socket_bump_1_y + self.bump_y_distance

        # Offsets from center
        self.socket_center_x_offset: float = (
            -self.socket_bump_1_x + self.socket_bump_1_center_x_offset
        )
        self.socket_center_y_offset: float = (
            -self.socket_bump_1_y + self.socket_bump_1_center_y_offset
        )

        # Final switch pin bump coordinates
        self.socket_bump_1_x_from_center: float = self.socket_bump_1_x + self.socket_center_x_offset
        self.socket_bump_1_y_from_center: float = self.socket_bump_1_y + self.socket_center_y_offset
        self.socket_bump_2_x_from_center: float = self.socket_bump_2_x + self.socket_center_x_offset
        self.socket_bump_2_y_from_center: float = self.socket_bump_2_y + self.socket_center_y_offset

        self.socket_left_end_x: float = self.socket_center_x_offset
        self.socket_right_end_x: float = self.total_width + self.socket_center_x_offset

        self.socket_front_end_y: float = (
            self.socket_center_y_offset  # start Y is just the offset, since we start sketching from Y = 0
        )

        self.socket_locking_lip_start_y: float = self.right_depth + self.socket_center_y_offset
        self.socket_locking_lip_start_x: float = (
            self.back_left_width + self.left_y_offset + self.socket_center_x_offset
        )
        self.socket_locking_lip_width: float = (
            self.total_width - self.back_left_width - self.left_y_offset
        )


@dataclass
class MXSwitchHolderConfig:
    case_config: CaseConfig = CaseConfig()
    key_config: MXKeyConfig = MXKeyConfig()
    kailh_socket_config: KailhMXSocketConfig = KailhMXSocketConfig()

    # Switch hole
    switch_bottom_height: float = 5
    switch_bottom_buffer_height: float = 0.2

    # Plate holes for holder lips
    holder_plate_gap: float = 0.1

    plate_side_hole_width: float = 1.8
    plate_side_hole_depth: float = 7

    plate_front_hole_width: float = 6
    plate_front_hole_depth: float = 1.1

    # Side wall thicknesses (front is calculated)
    holder_side_bottom_wall_width: float = 2.3

    # Y cutoffs
    cutoff_base_y_behind_socket_lip: float = 0.2
    cutoff_y: float = 8.2

    # Socket supports
    socket_base_height: float = 1

    # Front cutout to ease removal
    has_front_cutout_for_removal: bool = True
    front_removal_cutout_width: float = 3

    # Holes for switch metal pins to extend in base
    switch_metal_pin_base_hole_radius: float = 1

    # Front wire supports
    front_wire_supports_depth: float = 1.2

    # Side angled cutouts
    bottom_angled_cutout_left_end_top_y: float = 0.5
    bottom_angled_cutout_left_socket_top_y: float = 0.5
    bottom_angled_cutout_right_socket_top_y: float = 2.8
    bottom_angled_cutout_right_end_top_y: float = 2.8

    # Lip to prevent socket from sliding out
    socket_lip_depth: float = 0.4
    socket_lip_height: float = 0.2

    # Reverse position of diode and col wire:
    # * False = diode on left, col wire on right when looking from the front wall
    # * True = diode on right, col wire on left
    reverse_diode_and_col_wire: bool = False

    #
    # Front wire holes
    #

    # Diode wire front hole
    diode_wire_front_hole_distance_from_socket: float = 0.6
    diode_wire_front_hole_width: float = 0.9

    # Col wire front wrapping post (=hole in the front wall)
    col_wire_front_hole_distance_from_socket: float = 0.075
    col_wire_front_hole_narrow_width: float = 1
    col_wire_front_hole_narrow_height: float = 1
    col_wire_front_hole_wide_width: float = 1.5

    #
    # Top lips
    #

    # Top lips
    holder_lips_start_below_case_top: float = 0.2
    holder_lips_chamfer_top: float = 0.7

    # Top side lips
    holder_side_lips_width: float = 0.9
    holder_side_lips_base_width: float = 1
    holder_side_lips_top_width: float = 0.6

    # Top front lip
    holder_front_lip_side_plate_gap: float = 0.2
    holder_front_lip_height: float = 1.8

    #
    # Base holes for switch plastic pins
    #

    switch_center_pin_y: float = 0
    switch_center_pin_radius: float = 2.2

    switch_side_pin_distance: float = 5
    switch_side_pin_y: float = 0
    switch_side_pin_radius: float = 1.1

    #
    # Back wrapping posts and col/row separator
    #

    # Row wire back wrapping posts
    has_row_wire_wrappers: bool = True
    has_left_row_wire_wrapper: bool = True

    back_wrappers_and_separator_depth: float = 1.6

    row_wire_wrappers_offset_from_plate: float = 1.4
    row_wire_wrappers_base_height: float = 1
    row_wire_wrappers_tip_height: float = 2
    row_wire_wrapper_extra_width: float = 0

    # Col and row wires separator
    col_row_separator_z: float = 2
    col_row_separator_height: float = 1

    # Col wire back wrapping post
    col_wire_wrapper_back_head_height: float = 1
    col_wire_wrapper_back_head_extra_depth: float = 0.6

    col_wire_wrapper_back_neck_height: float = 1
    col_wire_wrapper_neck_width: float = 1
    col_wire_wrapper_neck_inner_margin: float = 0.85
    col_wire_wrapper_neck_outer_margin: float = 0.85

    col_wire_wrapper_back_neck_back_cutout_depth: float = 0.4

    #
    # Diode holder
    #

    # Diode hole location
    diode_center_x_from_side_end: float = 2.6
    diode_center_y_in_front_of_back_wall: float = 3.1
    diode_rotation: float = -45

    # Diode size
    diode_depth: float = 4
    diode_diameter: float = 2.1

    # Diode hole lips
    diode_bottom_lips_z_offset: float = 0.8
    diode_bottom_lips_width: float = 0.32
    diode_bottom_lips_height: float = 1
    diode_top_lips_size: float = 0.65

    # Diode wire cutout
    diode_wire_diameter: float = 0.55

    # Diode wire front triangular cutout
    has_diode_wire_triangular_cutout: bool = True
    diode_wire_triangular_cutout_width_depth: float = 1.5

    # Diode back wall
    has_diode_back_wall_cutout: bool = True
    diode_back_wall_top_cut_half_width: bool = True
    diode_back_wall_depth: float = 1
    diode_back_wall_cutout_width: float = 6

    #
    # Back side cuts
    #

    back_side_cut_start_behind_lips: float = 1
    back_side_cut_left_width: float = 1
    back_side_cut_right_width: float = 1

    def __post_init__(self):
        self.holder_front_wall_depth: float = self.plate_front_hole_depth - self.holder_plate_gap

        self.holder_width: float = (
            self.key_config.switch_hole_width + 2 * self.holder_side_bottom_wall_width
        )
        self.holder_depth: float = (
            self.key_config.switch_hole_depth + 2 * self.holder_front_wall_depth
        )

        self.holder_bottom_height: float = (
            self.socket_base_height
            + self.kailh_socket_config.socket_height
            + self.kailh_socket_config.socket_bump_height
        )
        self.holder_height: float = (
            self.holder_bottom_height
            + self.switch_bottom_buffer_height
            + self.switch_bottom_height
            - self.case_config.case_thickness
        )

        self.holder_height_to_socket_pin_top: float = (
            self.socket_base_height
            + self.kailh_socket_config.socket_height
            + self.kailh_socket_config.pin_top_clearance_height
        )

        self.cutoff_y_before_back_wrappers_and_separator = (
            self.cutoff_y - self.back_wrappers_and_separator_depth
        )

        self.switch_hole_min_height: float = self.holder_height + self.case_config.case_thickness

        self.plate_front_hole_start_y: float = (
            -self.key_config.switch_hole_depth / 2 - self.plate_front_hole_depth
        )

        self.cutoff_base_y: float = (
            self.kailh_socket_config.socket_locking_lip_start_y
            + self.socket_lip_depth
            + self.cutoff_base_y_behind_socket_lip
        )

        # Holder top walls
        self.holder_side_top_wall_width: float = self.plate_side_hole_width - self.holder_plate_gap
        self.holder_side_top_wall_x_offset: float = (
            self.holder_side_bottom_wall_width - self.holder_side_top_wall_width
        )

        self.holder_lips_depth: float = self.plate_side_hole_depth - self.holder_plate_gap

        self.holder_side_lips_top_lip_height: float = (
            self.holder_side_lips_width
            + self.holder_side_lips_base_width
            - self.holder_side_lips_top_width
        )

        self.holder_front_lock_bump_width = (
            self.plate_front_hole_width - 2 * self.holder_front_lip_side_plate_gap
        )

        self.holder_total_height: float = (
            self.holder_height
            + self.case_config.case_thickness
            - self.holder_lips_start_below_case_top
            + self.holder_side_lips_width
            + self.holder_side_lips_top_lip_height
        )

        self.col_wire_wrapper_head_width = (
            self.col_wire_wrapper_neck_inner_margin
            + self.col_wire_wrapper_neck_width
            + self.col_wire_wrapper_neck_outer_margin
        )

        self.diode_center_y = (
            self.cutoff_y_before_back_wrappers_and_separator
            - self.diode_center_y_in_front_of_back_wall
        )

    def reset_dependencies(
        self,
        case_config: CaseConfig,
        key_config: MXKeyConfig,
        kailh_socket_config: KailhMXSocketConfig,
    ):
        self.case_config = case_config
        self.key_config = key_config
        self.kailh_socket_config = kailh_socket_config
        self.__post_init__()


@dataclass
class ChocSwitchHolderConfig(MXSwitchHolderConfig):
    key_config: ChocKeyConfig = ChocKeyConfig()
    kailh_socket_config: KailhChocSocketConfig = KailhChocSocketConfig()

    switch_bottom_height: float = 2.2

    has_front_cutout_for_removal: bool = False
    has_left_row_wire_wrapper: bool = False
    reverse_diode_and_col_wire: bool = True

    row_wire_wrappers_offset_from_plate: float = 1.4

    cutoff_y: float = 7.8
    plate_front_hole_depth: float = 1.9

    # Side angled cutouts
    bottom_angled_cutout_left_end_top_y: float = 0.5
    bottom_angled_cutout_right_socket_top_y: float = 2.4
    bottom_angled_cutout_right_end_top_y: float = 2.4

    #
    # Base holes for switch plastic pins
    #

    switch_center_pin_y: float = 0
    switch_center_pin_radius: float = 2.7

    switch_side_pin_distance: float = 5.5
    switch_side_pin_y: float = 0
    switch_side_pin_radius: float = 1.1

    #
    # Front wire holes
    #

    # Diode wire front hole
    diode_wire_front_hole_distance_from_socket: float = 1

    # Col wire front wrapping post (=hole in the front wall)
    col_wire_front_hole_narrow_width: float = 2
    col_wire_front_hole_wide_width: float = 2

    #
    # Back wrapping posts and col/row separator
    #

    # Row wire back wrapping posts
    row_wire_wrapper_extra_width: float = 0.8

    #
    # Diode holder
    #

    # Diode hole location
    diode_center_x_from_side_end: float = 4
    diode_center_y_in_front_of_back_wall: float = 2.4
    diode_rotation: float = 0

    # Diode wire front triangular cutout
    has_diode_wire_triangular_cutout: bool = False

    # Diode back wall
    has_diode_back_wall_cutout: bool = False
    diode_back_wall_top_cut_half_width: bool = False

    #
    # Back side cuts
    #

    back_side_cut_left_width: float = 0.5
    back_side_cut_right_width: float = 1.5

    def reset_dependencies(
        self,
        case_config: CaseConfig,
        key_config: ChocKeyConfig,
        kailh_socket_config: KailhChocSocketConfig,
    ):
        self.case_config = case_config
        self.key_config = key_config
        self.kailh_socket_config = kailh_socket_config
        self.__post_init__()


@dataclass
class SideHolderConfig:
    item_width: float

    item_depth: float
    back_support_depth: float

    holder_height: float

    holder_hole_width: float
    case_hole_width: float

    holder_hole_start_z: float

    front_support_depth: float = 1.4

    side_supports_width: float = 1
    rail_width: float = 2

    # item_width_tolerance: float = 0.1
    # item_depth_tolerance: float = 0.1

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
        self.base_width = self.item_width + 2 * self.side_supports_width
        self.width = self.base_width + 2 * self.rail_width
        self.depth = self.item_depth + self.front_support_depth + self.back_support_depth
        self.holder_rail_width = self.rail_width - self.rail_width_inset
        self.rail_latch_tip_width = self.rail_latch_base_width - 2 * self.rail_latch_depth
        self.rail_latch_offset_from_bottom: float = (
            self.holder_height / 2 - self.rail_latch_base_height / 2
        )


@dataclass
class ControllerConfig(SideHolderConfig):
    item_width: float = 18

    item_depth: float = 33
    back_support_depth: float = 1.4

    holder_hole_width: float = 8.8
    holder_hole_start_z: float = 1.6

    case_hole_width: float = 18

    holder_height: float = 4.7


@dataclass
class TrrsJackConfig(SideHolderConfig):
    item_width: float = 6

    item_depth: float = 12
    back_support_depth: float = 2

    holder_hole_width: float = 5.3
    holder_hole_start_z: float = 0

    case_hole_width: float = 10

    holder_height: float = 7

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
class USBCJackConfig(SideHolderConfig):
    item_width: float = 9

    item_depth: float = 14.5
    back_support_depth: float = 1

    holder_hole_width: float = 9
    holder_hole_start_z: float = 1

    case_hole_width: float = 9

    holder_height: float = 4.2

    item_height: float = 3.2

    metal_part_depth: float = 7

    stopper_depth: float = 1.2
    # stopper_width: float = 0.8

    top_lip_width: float = 0.3
    top_lip_height: float = 0.5


@dataclass
class Config:
    case_config: CaseConfig = CaseConfig()

    mx_key_config: MXKeyConfig = MXKeyConfig()
    choc_key_config: ChocKeyConfig = ChocKeyConfig()

    screw_hole_config: ScrewHoleConfig = ScrewHoleConfig()

    kailh_mx_socket_config: KailhMXSocketConfig = KailhMXSocketConfig()
    kailh_choc_socket_config: KailhChocSocketConfig = KailhChocSocketConfig()

    switch_holder_mx_config: MXSwitchHolderConfig = MXSwitchHolderConfig()
    switch_holder_choc_config: ChocSwitchHolderConfig = ChocSwitchHolderConfig()

    controller_config: ControllerConfig = ControllerConfig()
    trrs_jack_config: TrrsJackConfig = TrrsJackConfig()
    usbc_jack_config: USBCJackConfig = USBCJackConfig()

    def __post_init__(self):
        self.switch_holder_mx_config.reset_dependencies(
            self.case_config, self.mx_key_config, self.kailh_mx_socket_config
        )
        self.switch_holder_choc_config.reset_dependencies(
            self.case_config, self.choc_key_config, self.kailh_choc_socket_config
        )

    def get_switch_holder_config(self) -> MXSwitchHolderConfig:
        return (
            self.switch_holder_mx_config
            if self.case_config.switch_type == SwitchType.MX
            else self.switch_holder_choc_config
        )

    def get_key_config(self) -> MXKeyConfig:
        return (
            self.mx_key_config
            if self.case_config.switch_type == SwitchType.MX
            else self.choc_key_config
        )
