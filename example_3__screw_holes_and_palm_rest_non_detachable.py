from klavgen import *

config = Config(case_config=CaseConfig(detachable_palm_rests=False))

keys = [Key(x=0, y=0)]

components = [
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

case_result = render_case(keys=keys, components=components, palm_rests=palm_rests, config=config)
