from pp.components.bend_circular import bend_circular
from pp.components.coupler_ring import coupler_ring
from pp.components.waveguide import waveguide
from pp.drc import assert_on_2nm_grid
from pp.component import Component
from pp.config import call_if_func
from pp.name import autoname


@autoname
def ring_single(
    wg_width=0.5,
    gap=0.2,
    length_x=4,
    bend_radius=5,
    length_y=2,
    coupler=coupler_ring,
    waveguide=waveguide,
    bend=bend_circular,
):
    """ single bus ring made of two couplers (ct: top, cb: bottom)
    connected with two vertical waveguides (wyl: left, wyr: right)

    .. code::

          bl-wt-br
          |      |
          wl     wr length_y
          |      |
         --==cb==-- gap

          length_x
    """
    assert_on_2nm_grid(gap)

    coupler = call_if_func(
        coupler, gap=gap, wg_width=wg_width, bend_radius=bend_radius, length_x=length_x
    )
    waveguide_side = call_if_func(waveguide, width=wg_width, length=length_y)
    waveguide_top = call_if_func(waveguide, width=wg_width, length=length_x)
    bend = call_if_func(bend, width=wg_width, radius=bend_radius)

    c = Component()
    cb = c << coupler
    wl = c << waveguide_side
    wr = c << waveguide_side
    bl = c << bend
    br = c << bend
    wt = c << waveguide_top

    wl.connect(port="E0", destination=cb.ports["N0"])
    bl.connect(port="N0", destination=wl.ports["W0"])

    wt.connect(port="W0", destination=bl.ports["W0"])
    br.connect(port="N0", destination=wt.ports["E0"])
    wr.connect(port="W0", destination=br.ports["W0"])
    c.add_port("E0", port=cb.ports["E0"])
    c.add_port("W0", port=cb.ports["W0"])
    return c


if __name__ == "__main__":
    import pp

    c = ring_single(with_pins=True)
    pp.show(c)
