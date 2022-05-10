from klavgen import *

config = Config()

keys = [Key(x=0, y=0)]

screw_holes = [
    ScrewHole(x=13, y=13),
    ScrewHole(x=13, y=-13),
    ScrewHole(x=-13, y=-13),
]

palm_rests = [
    PalmRest(
        points=[(13, -5), (13, -30), (-13, -30), (-13, -5)],
        height=config.case_config.case_base_height + 2,
        connector_locations_x=[0],
    ),
]

case_result = render_case(keys=keys, palm_rests=palm_rests, screw_holes=screw_holes, config=config)
