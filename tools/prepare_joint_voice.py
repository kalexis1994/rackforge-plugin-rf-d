"""Preserve admitted inputs before the joint BUS block; additive fine helper."""
import base64,json,subprocess
from prepare_vco1_portable import ROOT,sha,write

def main():
    previous='evidence/voice_chain_charge_tests01.json'
    old=json.loads((ROOT/previous).read_text())
    for group in ['source_sha256','private_input_sha256']:
        for n,h in old[group].items():assert sha(ROOT/n)==h,n
    mutable=['README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md','crates/rf-d-circuit/src/lib.rs']
    write('evidence/voice_joint_before01.json',dict(schema='rf-d/joint-before/v1',
        base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        previous_qa_sha256=sha(ROOT/previous),
        mutable_before_base64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in mutable}))
    source=(ROOT/'crates/rf-d-circuit/src/vco1_radau_fine.rs').read_text()
    # Keep physical laws identical. Change only increment representation and API.
    source=source.replace('fn cap(s:&mut Stamp,d:&[f64;N]', 'fn cap(s:&mut Stamp,d:State')
    source=source.replace('let i=g*(value(d,a)-value(d,b));',
        'let(h,l)=add_pair(value(&d.high,a),value(&d.low,a),-value(&d.high,b));let(h,l)=add_pair(h,l,-value(&d.low,b));let i=g*(h+l);')
    source=source.replace('pub fn linearize(previous:State,delta:[f64;N],c:Controls,dt:f64)->Result<Stamp,vco1_stamp::Error> {',
        'pub fn linearize(previous:State,delta:[f64;N],c:Controls,dt:f64)->Result<Stamp,vco1_stamp::Error> {\n linearize_compensated(previous,State::from_nodes(delta),c,dt)\n}\n'
        'pub fn linearize_compensated(previous:State,delta:State,c:Controls,dt:f64)->Result<Stamp,vco1_stamp::Error> {')
    source=source.replace('delta.iter().any(|v|!v.is_finite())',
        'delta.high.iter().chain(delta.low.iter()).any(|v|!v.is_finite())||!(0..N).all(|k|two_sum(delta.high[k],delta.low[k])==(delta.high[k],delta.low[k]))')
    source=source.replace('previous.advanced(delta);','previous.advanced(delta.high).advanced(delta.low);')
    source=source.replace('cap(&mut s,&delta,','cap(&mut s,delta,')
    source=source.replace('l/dt*delta[row]', 'l/dt*(delta.high[row]+delta.low[row])')
    target=ROOT/'crates/rf-d-circuit/src/joint_vco_fine.rs';assert not target.exists()
    target.write_text(source,encoding='utf8',newline='\n')
    print('JOINT_BEFORE',len(old['source_sha256']),len(old['private_input_sha256']))
if __name__=='__main__':main()
