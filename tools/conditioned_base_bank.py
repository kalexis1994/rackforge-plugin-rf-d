"""Decode the frozen complete base and all four old C27 histories."""
import json
from prepare_vco1_portable import ROOT,sha
from check_history_propagation import Reader
from joint_cycles_analysis import require

PATH='references-local/conditioned-return01/return.bin'

def bank():
    qa=json.loads((ROOT/'evidence/voice_conditioned_return_utf8_tests01.json').read_text(encoding='utf8'))
    require(qa['passed'] and sha(ROOT/PATH)==qa['private_input_sha256'][PATH],'protected base')
    r=Reader(ROOT/PATH);require(r.bytes(8)==b'RFJCRO01' and r.integer('I')==42544,'base codec')
    root=r.floats(441);basis=r.floats(3924).reshape(218,18);samples={};schedule=[]
    for step in range(42544):
        require(r.integer('I')==step,'base order');ticks=r.integer('Q');half=r.integer('I');obs=r.floats(7);schedule.append((ticks,half,obs))
        if r.bytes(1)[0]:samples[step]=(r.floats(2000).reshape(5,400),r.floats(3600).reshape(200,18),r.floats(7200).reshape(400,18))
    gain=r.floats(18);epsilon=r.floats(18);events=[]
    for _ in range(2):events.append(dict(alpha=float(r.floats(1)[0]),state=r.floats(400),dalpha=r.floats(18),dt=r.floats(18),response=r.floats(3600).reshape(200,18)))
    period=float(r.floats(1)[0]);drift=r.floats(200);dt=r.floats(18);dd=r.floats(3600).reshape(200,18)
    for scale in [1.,.5]:
        for sign in [1.,-1.]:
            meta=r.floats(3);require(meta[0]==scale and meta[1]==sign,'old own order');r.floats(441);r.floats(1600)
            for _ in range(2):r.floats(1);r.floats(400)
            r.floats(1)
    r.end()
    return dict(root=root,basis=basis,samples=samples,schedule=schedule,gain=gain,epsilon=epsilon,events=events,period=period,drift=drift,dt=dt,dd=dd,path=PATH)
