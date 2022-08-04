import cadquery as cq

from .classes import LocationOrientation, USBCJack
from .config import Config, SideHolderConfig, USBCJackConfig
from .renderer_side_holder import render_side_holder
from .rendering import (
    RENDERERS,
    RenderedItem,
    RenderingPipelineStage,
    RenderResult,
    SeparateComponentRender,
)
from .utils import grow_yz, position


def render_usbc_jack(usbc_jack: USBCJack, config: Config) -> RenderResult:
    result = render_side_holder(usbc_jack, config.usbc_jack_config, config.case_config)

    def render_in_place():
        usbc_jack_holder = render_usbc_jack_holder(config.usbc_jack_config).translate(
            (0, config.case_config.case_thickness + config.usbc_jack_config.tolerance, 0)
        )

        usbc_jack_lr = LocationOrientation(
            x=usbc_jack.x,
            y=usbc_jack.y,
            z=usbc_jack.z - config.case_config.case_base_height + config.case_config.case_thickness,
            rotate=usbc_jack.rotate,
            rotate_around=usbc_jack.rotate_around,
        )

        return position(usbc_jack_holder, usbc_jack_lr)

    return RenderResult(
        name=usbc_jack.name or "usbc_jack",
        items=[
            RenderedItem(result.case_column, pipeline_stage=RenderingPipelineStage.CASE_SOLID),
            RenderedItem(result.rail, pipeline_stage=RenderingPipelineStage.AFTER_SHELL_ADDITIONS),
            RenderedItem(result.hole, pipeline_stage=RenderingPipelineStage.BOTTOM_CUTS),
            RenderedItem(result.debug, pipeline_stage=RenderingPipelineStage.DEBUG),
        ],
        separate_components=[
            SeparateComponentRender(
                name="usbc_jack",
                render_func=lambda: render_usbc_jack_holder(config.usbc_jack_config),
                render_in_place_func=render_in_place,
            )
        ],
    )


RENDERERS.set_renderer("usbc_jack", render_usbc_jack)


def render_side_mount(config: SideHolderConfig):
    wp = cq.Workplane("XY")
    wp_mid_xy = wp.center(config.width / 2, 0)

    # Mount
    mount = wp.box(config.width, config.front_support_depth, config.holder_height, centered=False)

    # Mount hole
    front_hole = wp_mid_xy.workplane(offset=config.holder_hole_start_z).box(
        config.holder_hole_width,
        config.front_support_depth,
        config.holder_height,
        centered=grow_yz,
    )
    mount = mount.cut(front_hole)

    return mount


def render_lip(
    wp,
    end_x: float,
    sloped_height: float,
    length: float,
    straight_height: float = 0,
):
    lip = wp.lineTo(0, straight_height + sloped_height)

    if straight_height != 0:
        lip = lip.lineTo(end_x, straight_height)

    lip = lip.lineTo(end_x, 0).close().extrude(length)

    return lip


def render_usbc_jack_holder(config: USBCJackConfig = USBCJackConfig()):
    wp = cq.Workplane("XY")
    wp_xz = cq.Workplane("XZ")

    holder = render_side_mount(config)
    holder = holder.translate((-config.width / 2, 0, 0))

    # Overall bounding box

    bounding_box = wp.box(
        config.base_width,
        config.metal_part_depth + config.stopper_depth,
        config.holder_hole_start_z + config.item_height,
        centered=grow_yz,
    )
    holder = holder.union(bounding_box)

    # Socket

    socket = wp.workplane(offset=config.holder_hole_start_z).box(
        config.item_width,
        config.metal_part_depth + config.stopper_depth,
        config.item_height,
        centered=grow_yz,
    )
    holder = holder.cut(socket)

    # Back lips

    back_lips_width = 0.7
    back_lips_straight_depth = 0.65
    back_lips_sloped_depth = 0.65

    wp_back_lips = wp.workplane(offset=config.holder_hole_start_z).center(
        0, config.metal_part_depth + config.stopper_depth
    )
    back_left_lip = render_lip(
        wp_back_lips.center(-config.item_width / 2, 0),
        end_x=back_lips_width,
        sloped_height=-back_lips_sloped_depth,
        length=config.item_height,
        straight_height=-back_lips_straight_depth,
    )
    holder = holder.union(back_left_lip)

    back_right_lip = render_lip(
        wp_back_lips.center(config.item_width / 2, 0),
        end_x=-back_lips_width,
        sloped_height=-back_lips_sloped_depth,
        length=config.item_height,
        straight_height=-back_lips_straight_depth,
    )
    holder = holder.union(back_right_lip)

    # Top lips

    top_lips_width = 0.6
    top_lips_sloped_height = 0.7
    top_lips_straight_height = 0.35

    wp_top_lips = wp_xz.center(0, (config.holder_hole_start_z + config.item_height))

    top_left_lip = render_lip(
        wp_top_lips.center(-config.item_width / 2, 0),
        end_x=top_lips_width,
        sloped_height=-top_lips_sloped_height,
        length=-(config.metal_part_depth + config.stopper_depth),
        straight_height=-top_lips_straight_height,
    )
    holder = holder.union(top_left_lip)

    top_right_lip = render_lip(
        wp_top_lips.center(config.item_width / 2, 0),
        end_x=-top_lips_width,
        sloped_height=-top_lips_sloped_height,
        length=-(config.metal_part_depth + config.stopper_depth),
        straight_height=-top_lips_straight_height,
    )
    holder = holder.union(top_right_lip)

    # Socket end used for debugging
    # socket_end = (
    #     wp_xz.center(
    #         -config.item_width / 2 + config.item_height / 2,
    #         config.holder_hole_start_z + config.item_height / 2
    #     )
    #     .circle(config.item_height / 2)
    #     .extrude(5)
    # )
    # holder = holder.union(socket_end)

    # Rotate 180 degrees to orient so USB port is on the back
    holder = holder.rotate((0, 0, 0), (0, 0, 1), 180)

    return holder


def export_usbc_jack_holder_to_stl(usbc_jack_holder):
    cq.exporters.export(usbc_jack_holder, "usbc_jack_holder.stl")


def export_usbc_jack_holder_to_step(usbc_jack_holder):
    cq.exporters.export(usbc_jack_holder, "usbc_jack_holder.step")
