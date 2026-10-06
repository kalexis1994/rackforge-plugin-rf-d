"""Same port polyline as a B expression, with a zero-volt current probe."""
from pathlib import Path
import voice_port_relaxation as p
import voice_port_probes as probes
import vco1_circuit_reference as vco


def factory(s,side,t,x,with_contour):
    original,vectors=p.factory(s,side,t,x,with_contour)
    def generate(scene,export):
        deck,meta=original(scene,export)
        if side=='vco':
            start=deck.index('Vmixer MIX_BUS_BOARD4_PIN4 0 PWL(\n')
            stop=deck.index('+)\n',start)+3
            lines=deck[start:stop].splitlines()[1:-1]
            points=[line[2:].split() for line in lines]
            expression='Bmixer MIXER_DRIVE 0 V=pwl(time,\n'
            expression+=''.join('+ '+a+', '+b+(',\n' if k<len(points)-1 else ')\n') for k,(a,b) in enumerate(points))
            expression+='Vmixer MIX_BUS_BOARD4_PIN4 MIXER_DRIVE 0\n'
            deck=deck[:start]+expression+deck[stop:]
        meta['port_source_form']='behavioral-pwl-with-zero-volt-current-probe' if side=='vco' else 'independent-pwl'
        for path in (Path(__file__),Path(probes.__file__)):
            meta['source_sha256'][path.relative_to(p.ROOT).as_posix()]=vco.sha(path)
        return deck,meta
    return generate,vectors


if __name__=='__main__':probes.main('port-behavioral01',factory)
