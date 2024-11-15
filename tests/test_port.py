from __future__ import annotations

import pytest
from pytest_regressions.data_regression import DataRegressionFixture

import gdsfactory as gf


def test_get_ports_sort_clockwise() -> None:
    """Test that the ports are sorted clockwise.

    .. code::

            3   4
            |___|_
        2 -|      |- 5
           |      |
        1 -|______|- 6
            |   |
            8   7
    """
    c = gf.Component()
    nxn = gf.components.nxn(west=2, north=2, east=2, south=2)
    ref = c << nxn
    p = gf.port.get_ports_list(ref, sort_ports=True, clockwise=True)
    p1 = p[0]
    p8 = p[-1]

    assert p1.name == "o1", p1.name
    assert p1.orientation == 180, p1.orientation
    assert p8.name == "o8", p8.name
    assert p8.orientation == 270, p8.orientation


def test_get_ports_sort_counter_clockwise() -> None:
    """Test that the ports are sorted counter clockwise.

    .. code::

            4   3
            |___|_
        5 -|      |- 2
           |      |
        6 -|______|- 1
            |   |
            7   8

    """
    c = gf.Component()
    nxn = gf.components.nxn(west=2, north=2, east=2, south=2)
    ref = c << nxn
    p = gf.port.get_ports_list(ref, sort_ports=True, clockwise=False)
    p1 = p[0]
    p8 = p[-1]
    assert p1.name == "o6", p1.name
    assert p1.orientation == 0, p1.orientation
    assert p8.name == "o7", p8.name
    assert p8.orientation == 270, p8.orientation


@pytest.mark.parametrize("port_type", ["electrical", "optical", "placement"])
def test_rename_ports(port_type, data_regression: DataRegressionFixture):
    c = gf.components.nxn(port_type=port_type)
    data_regression.check(c.to_dict())


def test_port() -> None:
    p = gf.Port(name="foo", orientation=359, center=(0, 0), width=5, layer=(1, 1))
    assert p.orientation == 359
