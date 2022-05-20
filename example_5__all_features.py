import cadquery as cq

from klavgen import *

config = Config(case_config=CaseConfig(side_fillet=1, palm_rests_top_fillet=2))

keys = [  # By columns from bottom left
    Key(x=0, y=0),
    Key(x=0, y=19),
    Key(x=19, y=0),
    Key(x=19, y=19),
]

controller = Controller(x=47.5, y=34)

trrs_jack = TrrsJack(x=68, y=34)

screw_holes = [  # Clockwise from top left
    ScrewHole(x=-11.4, y=30.4),
    ScrewHole(x=30.5, y=30.4),
    ScrewHole(x=78.4, y=30.4),
    ScrewHole(x=78.4, y=9.5),
    ScrewHole(x=30.5, y=-15),
    ScrewHole(x=-11.5, y=-15),
]

patches = [
    Patch(
        points=[
            (-15, 34),
            (82, 34),
            (82, 7),
            (57.5, -15),
            (30.5, -15),
            (9.5, -18),
            (-15, -15),
        ],
        height=config.case_config.case_base_height,
    )
]

cuts = [
    Cut(
        points=[(57.5, -15), (82, 7), (82, -15)],
        height=config.case_config.case_base_height,
    )
]

case_extras = [
    (
        cq.Workplane("XY")
        .workplane(offset=-config.case_config.case_base_height)
        .center(69.75, -4)
        .circle(5)
        .extrude(config.case_config.case_base_height)
    )
]

palm_rests = [
    PalmRest(
        points=[(-15, 0), (34, 0), (34, -35), (-15, -35)],
        height=config.case_config.case_base_height + 10,
        connector_locations_x=[0, 20],
    ),
]

texts = [
    Text(x=45, y=-8.5, text="Plate", font_size=6, extrude=0.4),
    Text(x=10, y=-26, z=10, text="Palm rest", font_size=6, extrude=0.4),
]

keyboard_result = render_and_save_keyboard(
    keys=keys,
    screw_holes=screw_holes,
    controller=controller,
    trrs_jack=trrs_jack,
    patches=patches,
    cuts=cuts,
    case_extras=case_extras,
    palm_rests=palm_rests,
    texts=texts,
    debug=False,
    config=config,
)

print("Done")
