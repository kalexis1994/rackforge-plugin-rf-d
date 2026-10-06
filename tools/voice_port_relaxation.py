"""Offline waveform relaxation at the physical R45 mixer resistor.

Each iteration solves both histories from DC; only port closure may admit
the pair. Temporary PWL boundaries are not an independent audio fixture.
"""
from dataclasses import asdict
import hashlib
from pathlib import Path
import numpy as np
import filter_vca_circuit_reference as f
import loudness_board4_circuit as envelope
import loudness_voice_circuit as coupled
import vco1_circuit_reference as vco
import voice_circuit_reference as voice

ROOT=vco.ROOT
GATES=dict(pwl_v=1e-6,port_v=10e-6,port_a=1e-9,max_iterations=10,
           trace_v=.005,frequency_cents=1,charge_c=.1e-9)
VCO_VECTORS=['v(ramp_c1)','v(schmitt_drive)','v(saw_output_9b)',
             'v(r6_wiper)','v(mix_bus_board4_pin4)','i(vmixer)']
BOARD_VECTORS=['v(mix_bus_board4_pin4)','v(f4_recover_collector)',
               'v(f4_main_output)','v(f4_q17_collector)','v(f4_c2_right)',
               'v(f4_headphone_input)','i(vport)']


def resistance():
    return next(p['value_ohm'] for p in vco.read(vco.PANEL)['parts'] if p['ref']=='R45_PANEL')


def waveform(t,x):
    t=np.asarray(t,dtype=float);x=np.asarray(x,dtype=float)
    if t.ndim!=1 or x.shape!=t.shape or len(t)<2 or not np.isfinite(t).all() or not np.isfinite(x).all():
        raise ValueError('finite one-dimensional port history required')
    if t[0]!=0 or np.any(np.diff(t)<=0):raise ValueError('port history must start at zero and grow strictly')
    return t,x


def simplify(t,x,tolerance=GATES['pwl_v']):
    """RDP with an error bound against every vertex of the input polyline.

    On the union of input/output knots both are linear between vertices,
    so the checked bound covers the represented polylines, not an unknown
    continuous circuit solution between ngspice samples.
    """
    t,x=waveform(t,x)
    if not np.isfinite(tolerance) or tolerance<=0:raise ValueError('positive finite approximation bound')
    keep={0,len(t)-1};pending=[(0,len(t)-1)]
    while pending:
        a,b=pending.pop()
        if b<=a+1:continue
        line=x[a]+(x[b]-x[a])*(t[a+1:b]-t[a])/(t[b]-t[a])
        errors=np.abs(x[a+1:b]-line);k=a+1+int(np.argmax(errors))
        if errors[k-a-1]>tolerance:
            keep.add(k);pending.extend(((a,k),(k,b)))
    indices=np.array(sorted(keep));tt,xx=t[indices],x[indices]
    error=float(np.max(np.abs(x-np.interp(t,tt,xx))))
    if error>tolerance*(1+1e-8):raise ValueError('port approximation rejected')
    digest=hashlib.sha256(np.column_stack((tt,xx)).astype('<f8').tobytes()).hexdigest()
    return tt,xx,dict(input_knots=len(t),retained_knots=len(tt),max_error_v=error,knots_sha256=digest)


def pwl(name,node,t,x):
    t,x=waveform(t,x)
    return f'{name} {node} 0 PWL(\n'+''.join(f'+ {a:.17g} {b:.17g}\n' for a,b in zip(t,x))+'+)'


def board_vectors(with_contour):
    return BOARD_VECTORS+(envelope.EXTRA if with_contour else [])


def factory(s,side,t,x,with_contour):
    s.validate();t,x,approx=simplify(t,x)
    duration=s.oscillator.duration_s
    if abs(t[-1]-duration)>1e-14:raise ValueError('complete port horizon required')
    # ngspice's final export can round a complete horizon by one ULP.
    # Preserve that interval explicitly in metadata; no partial trace promotion.
    terminal_rounding_s=float(duration-t[-1])
    if terminal_rounding_s>0:t=np.r_[t,duration];x=np.r_[x,x[-1]]
    elif terminal_rounding_s<0:
        end=float(np.interp(duration,t,x));mask=t<duration
        t=np.r_[t[mask],duration];x=np.r_[x[mask],end]
    vectors=VCO_VECTORS if side=='vco' else board_vectors(with_contour)
    if side not in ('vco','board'):raise ValueError('known side required')
    def generate(_scenario,export):
        if _scenario!=s:raise ValueError('frozen scenario required')
        if side=='vco':
            text,meta=vco.netlist(s.oscillator,export);old=vco.VECTORS
            lines=text.splitlines()
            if sum(l.startswith('Vmixer ') for l in lines)!=1:raise ValueError('exactly one mixer boundary')
            text='\n'.join(pwl('Vmixer','MIX_BUS_BOARD4_PIN4',t,x) if l.startswith('Vmixer ') else l for l in lines)+'\n'
            text=text.replace('.options ','.options klu bypass=0 itl4=100 ',1)
        else:
            if with_contour:
                e=s.contour_scenario();text,meta=envelope.netlist(e,export);old=e.vectors
            else:
                text,meta=f.netlist(f.Scenario(board=s.board),export);old=f.VECTORS
            lines=text.splitlines()
            if sum(l.startswith('Vfixture ') for l in lines)!=1 or sum(l.startswith('Rfixture ') for l in lines)!=1:
                raise ValueError('fixture boundary count')
            text='\n'.join(l for l in lines if not l.startswith(('Vfixture ','Rfixture ')))+'\n'
            port=pwl('Vport','PORT_R6_WIPER',t,x)+f'\nR45_PANEL PORT_R6_WIPER MIX_BUS_BOARD4_PIN4 {resistance():.17g}\n'
            text=text.replace('.options ',port+'.options ',1)
        text=text.replace('.save '+' '.join(old),'.save '+' '.join(vectors))
        text=text.replace(' '.join(old)+'\nquit',' '.join(vectors)+'\nquit')
        meta.update(schema='rf-d/voice-port-netlist/v1',scenario=asdict(s),side=side,
            contour_circuit=with_contour,port_resistance_ohm=resistance(),port_approximation=approx,
            iteration_boundary=True,port_closed=False,physical_fidelity=False,real_time=False,
            terminal_rounding_s=terminal_rounding_s)
        for path in (vco.PANEL,Path(__file__),Path(coupled.__file__)):
            meta['source_sha256'][path.relative_to(ROOT).as_posix()]=vco.sha(path)
        return text,meta
    return generate,vectors


def closure(vraw,braw,bvectors):
    vt=vraw[:,0];bt=braw[:,0]
    waveform(vt,vraw[:,1]);waveform(bt,braw[:,1])
    if abs(vt[-1]-bt[-1])>1e-14 or not np.isfinite(vraw).all() or not np.isfinite(braw).all():
        raise ValueError('common complete finite port horizon')
    t=np.union1d(vt,bt);t=t[t<=min(vt[-1],bt[-1])]
    v=lambda n:np.interp(t,vt,vraw[:,VCO_VECTORS.index(n)+1])
    b=lambda n:np.interp(t,bt,braw[:,bvectors.index(n)+1])
    # Both histories keep R45. The source current is opposite at its ends.
    dv=v('v(mix_bus_board4_pin4)')-b('v(mix_bus_board4_pin4)')
    di=v('i(vmixer)')+b('i(vport)')
    rv=(v('v(r6_wiper)')-v('v(mix_bus_board4_pin4)'))/resistance()-v('i(vmixer)')
    voltage=float(np.max(np.abs(dv)));current=float(np.max(np.abs(di)))
    algebra=float(np.max(np.abs(rv)))
    return dict(union_knots=len(t),max_voltage_defect_v=voltage,max_current_defect_a=current,
        vco_resistor_current_defect_a=algebra,
        passed=voltage<=GATES['port_v'] and current<=GATES['port_a'] and algebra<=GATES['port_a'])


def assemble(vraw,braw,bvectors,s):
    """Observation adapter; does not initialize or reset any electrical state."""
    t=braw[:,0];cols=[]
    for n in s.vectors:
        if n in VCO_VECTORS:cols.append(np.interp(t,vraw[:,0],vraw[:,VCO_VECTORS.index(n)+1]))
        elif n in bvectors:cols.append(braw[:,bvectors.index(n)+1])
        else:raise ValueError('missing coupled observation: '+n)
    return np.column_stack((t,*cols))
