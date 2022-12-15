import functools
from collections.abc import Iterable
from typing import Any, List, Union

import cadquery as cq

from .classes import LocationOrientation


def highest_from_workplane(workplane):
    return cq.selectors.DirectionMinMaxSelector(workplane.plane.zDir, True)


def position(wp, lr: LocationOrientation):
    """
    Move an object stack (=workplane) to the given relative location and Z-rotation
    :param wp: workplane to move
    :param lr: location/rotation to move to (all relative)
    :return: moved workplane
    """
    wp = wp.translate((lr.x, lr.y, lr.z))

    if lr.rotate:
        rx = lr.rotate_around[0] if lr.rotate_around else lr.x
        ry = lr.rotate_around[1] if lr.rotate_around else lr.y
        wp = wp.rotate((rx, ry, 0), (rx, ry, 1), lr.rotate)

    return wp


def create_workplane(lr: LocationOrientation):
    """
    Create a workplane parallel to XY at the given global location and Z-rotation
    :param lr: location and rotation
    :return: new workplane parallel to XY
    """
    # This is an optimization where we first center on either the final position (if no rotate_around or rotate is 0)
    # or on rotate_around
    rx = lr.rotate_around[0] if lr.rotate_around and lr.rotate != 0 else lr.x
    ry = lr.rotate_around[1] if lr.rotate_around and lr.rotate != 0 else lr.y
    wp = cq.Workplane("XY").workplane(offset=lr.z).center(rx, ry)

    if lr.rotate:
        # If rotating, now first rotate, and then re-center workplane with local coordinates. If there is no
        # rotate_around, the re-center has no effect (since rx = key.x), however if there is one,
        # the effect is as if rotating around the points in rotate_around
        # Using separate center() call because offset in transformed() seems to use global coordinates
        # contrary to the documentation
        wp = wp.transformed(rotate=(0, 0, lr.rotate)).center(lr.x - rx, lr.y - ry)

    return wp


grow_z = (True, True, False)

grow_yz = (True, False, False)


def _cq_union_reductor(a, b):
    if a is not None and b is not None:
        return a.union(b)

    if a is not None:
        return a

    if b is not None:
        return b

    return None


def union_list(*objects: Union[cq.Workplane, List[cq.Workplane]]):
    if objects:
        flat_objects = []
        for obj in objects:
            if isinstance(obj, Iterable):
                flat_objects.extend(obj)
            else:
                flat_objects.append(obj)

        if flat_objects:
            return functools.reduce(_cq_union_reductor, flat_objects)
        else:
            return None
    else:
        return None
