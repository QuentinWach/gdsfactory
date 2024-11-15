# See: https://quentinwach.com/blog/2024/02/15/dubins-paths-for-waveguide-routing.html
# A minimal implementation of Dubins paths for waveguide routing
# adapted for gdsFactory by Quentin Wach.
import math as m

import numpy as np

import gdsfactory as gf
from gdsfactory.component import Component
from gdsfactory.typings import CrossSectionSpec


def route_dubin(xs: CrossSectionSpec, port1, port2) -> Component:
    """Route between ports using Dubins paths with radius from cross-section."""
    # Get start position and orientation
    x1, y1 = port1.center
    angle1 = float(port1.orientation)
    START = (x1 / 1000, y1 / 1000, angle1)  # Convert to um

    # Get end position and orientation
    x2, y2 = port2.center
    angle2 = float(port2.orientation)
    angle2 = (angle2 + 180) % 360  # Adjust for input connection
    END = (x2 / 1000, y2 / 1000, angle2)  # Convert to um

    # Find the Dubin's path between ports using radius from cross-section
    path = dubins_path(xs, start=START, end=END)  # Convert radius to um

    return gds_solution(xs, port1, port2, solution=path)


#########################################################################
# Main
#########################################################################


def general_planner(planner, alpha, beta, d):
    """Finds the optimal path between two points using various planning methods."""
    sa = m.sin(alpha)
    sb = m.sin(beta)
    ca = m.cos(alpha)
    cb = m.cos(beta)
    c_ab = m.cos(alpha - beta)
    mode = list(planner)

    planner_uc = planner.upper()

    if planner_uc == "LSL":
        tmp0 = d + sa - sb
        p_squared = 2 + (d * d) - (2 * c_ab) + (2 * d * (sa - sb))
        if p_squared < 0:
            return None
        tmp1 = m.atan2((cb - ca), tmp0)
        t = mod_to_pi(-alpha + tmp1)
        p = m.sqrt(p_squared)
        q = mod_to_pi(beta - tmp1)

    elif planner_uc == "RSR":
        tmp0 = d - sa + sb
        p_squared = 2 + (d * d) - (2 * c_ab) + (2 * d * (sb - sa))
        if p_squared < 0:
            return None
        tmp1 = m.atan2((ca - cb), tmp0)
        t = mod_to_pi(alpha - tmp1)
        p = m.sqrt(p_squared)
        q = mod_to_pi(-beta + tmp1)

    elif planner_uc == "LSR":
        p_squared = -2 + (d * d) + (2 * c_ab) + (2 * d * (sa + sb))
        if p_squared < 0:
            return None
        p = m.sqrt(p_squared)
        tmp2 = m.atan2((-ca - cb), (d + sa + sb)) - m.atan2(-2.0, p)
        t = mod_to_pi(-alpha + tmp2)
        q = mod_to_pi(-mod_to_pi(beta) + tmp2)

    elif planner_uc == "RSL":
        p_squared = (d * d) - 2 + (2 * c_ab) - (2 * d * (sa + sb))
        if p_squared < 0:
            return None
        p = m.sqrt(p_squared)
        tmp2 = m.atan2((ca + cb), (d - sa - sb)) - m.atan2(2.0, p)
        t = mod_to_pi(alpha - tmp2)
        q = mod_to_pi(beta - tmp2)

    elif planner_uc == "RLR":
        tmp_rlr = (6.0 - d * d + 2.0 * c_ab + 2.0 * d * (sa - sb)) / 8.0
        if abs(tmp_rlr) > 1.0:
            return None

        p = mod_to_pi(2 * m.pi - m.acos(tmp_rlr))
        t = mod_to_pi(alpha - m.atan2(ca - cb, d - sa + sb) + mod_to_pi(p / 2.0))
        q = mod_to_pi(alpha - beta - t + mod_to_pi(p))

    elif planner_uc == "LRL":
        tmp_lrl = (6.0 - d * d + 2 * c_ab + 2 * d * (-sa + sb)) / 8.0
        if abs(tmp_lrl) > 1:
            return None
        p = mod_to_pi(2 * m.pi - m.acos(tmp_lrl))
        t = mod_to_pi(-alpha - m.atan2(ca - cb, d + sa - sb) + p / 2.0)
        q = mod_to_pi(mod_to_pi(beta) - alpha - t + mod_to_pi(p))

    else:
        print("bad planner:", planner)

    path = [t, p, q]

    for i in [0, 2]:
        if planner[i].islower():
            path[i] = (2 * m.pi) - path[i]

    cost = sum(map(abs, path))

    return (path, mode, cost)


def dubins_path_length(start, end, xs):
    """Calculate the length of a Dubins path."""
    (sx, sy, syaw) = start
    (ex, ey, eyaw) = end
    # convert the degree angle inputs to radians
    syaw = m.radians(syaw)
    eyaw = m.radians(eyaw)

    c = xs.radius

    ex = ex - sx
    ey = ey - sy

    lex = m.cos(syaw) * ex + m.sin(syaw) * ey
    ley = -m.sin(syaw) * ex + m.cos(syaw) * ey
    leyaw = eyaw - syaw
    D = m.sqrt(lex**2.0 + ley**2.0)
    return D


def dubins_path(xs, start, end):
    """Finds the Dubins path between two points."""
    (sx, sy, syaw) = start  # Coordinates already in um
    (ex, ey, eyaw) = end  # Coordinates already in um

    # Convert angles to radians
    syaw = m.radians(syaw)
    eyaw = m.radians(eyaw)

    # Use radius in um
    c = xs.radius  # Already converted to um

    # Calculate relative end position
    ex = ex - sx
    ey = ey - sy

    # Transform to local coordinates
    lex = m.cos(syaw) * ex + m.sin(syaw) * ey
    ley = -m.sin(syaw) * ex + m.cos(syaw) * ey
    leyaw = eyaw - syaw

    # Calculate normalized distance
    D = m.sqrt(lex**2.0 + ley**2.0)
    d = D / c  # Normalize by radius

    print("D (um):", D)

    # Calculate angles for path planning
    theta = mod_to_pi(m.atan2(ley, lex))
    alpha = mod_to_pi(-theta)
    beta = mod_to_pi(leyaw - theta)

    # Find best path
    planners = ["LSL", "RSR", "LSR", "RSL", "RLR", "LRL"]
    bcost = float("inf")
    bt, bp, bq, bmode = None, None, None, None

    for planner in planners:
        solution = general_planner(planner, alpha, beta, d)
        if solution is None:
            continue
        (path, mode, cost) = solution
        (t, p, q) = path
        if bcost > cost:
            bt, bp, bq, bmode = t, p, q, mode
            bcost = cost

    print(f"Best mode: {bmode}")
    # Return path segments with lengths in um
    return list(zip(bmode, [bt * c, bp * c, bq * c], [c] * 3))


#########################################################################
# Helpers
#########################################################################


def mod_to_pi(angle):
    """Normalizes an angle to the range [0, 2*pi)."""
    return angle - 2.0 * m.pi * m.floor(angle / 2.0 / m.pi)


def pi_to_pi(angle):
    """Constrains an angle to the range [-pi, pi]."""
    while angle >= m.pi:
        angle = angle - 2.0 * m.pi
    while angle <= -m.pi:
        angle = angle + 2.0 * m.pi
    return angle


def linear(START, END, STEPS):
    """Creates a list of points on lines between a given start point and end point.
    start/end: [x, y, angle], the start/end point with given jaw angle.
    """
    x = []
    y = []
    Dx = END[0] - START[0]
    Dy = END[1] - START[1]
    dx = Dx / STEPS
    dy = Dy / STEPS
    for step in range(0, STEPS + 1):
        x.append(step * dx + START[0])
        y.append(step * dy + START[1])
    return x, y


def arrow_orientation(ANGLE):
    """Returns x, y setoffs for a given angle to orient the arrows
    marking the yaw of the start and end points.
    """
    alpha_x = m.cos(m.radians(ANGLE))
    alpha_y = m.sin(m.radians(ANGLE))
    return alpha_x, alpha_y


# generate a Nazca cell for a given Dubin's path solution
def gds_solution(xs: CrossSectionSpec, port1, port2, solution) -> Component:
    """Creates GDS component with Dubins path."""
    c = Component(
        name="dubins_path_" + str(np.random.randint(1000000)) + str(port1.name)
    )
    current_position = port1

    for mode, length, radius in solution:
        if mode == "L":
            # Length and radius are in um, convert to nm for gdsfactory
            arc_angle = 180 * length / (m.pi * radius)
            bend = c << gf.components.bend_circular(angle=arc_angle, cross_section=xs)
            bend.connect("o1", destination=current_position)
            current_position = bend.ports["o2"]

        elif mode == "R":
            arc_angle = -(180 * length / (m.pi * radius))
            bend = c << gf.components.bend_circular(angle=arc_angle, cross_section=xs)
            bend.connect("o1", destination=current_position)
            current_position = bend.ports["o2"]

        elif mode == "S":
            straight = c << gf.components.straight(length=length, cross_section=xs)
            straight.connect("o1", destination=current_position)
            current_position = straight.ports["o2"]

        else:
            raise ValueError(f"Invalid mode: {mode}")

    return c
