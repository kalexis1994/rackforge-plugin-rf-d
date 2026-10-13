"""Inspect exact stored Jacobian support for the next downstream partition."""
import json,struct
from prepare_vco1_portable import ROOT,sha,write
from prepare_dynamic_schur import maps
from joint_cycles_analysis import require

def main():
    receipt='evidence/voice_schur_refined_contourbank01.json';bank=json.loads((ROOT/receipt).read_text(encoding='utf8'));require(bank['passed'],'current bank')
    name='references-local/schur-refined-contourbank01/linear.bin';require(sha(ROOT/name)==next(x['sha256'] for x in bank['outputs'] if x['path']==name),'observed bank identity')
    inside=[k+stage*229 for stage in range(2) for k in range(133,200) if k!=165];ports=[12,165,241,394];allowed=set(inside+ports);owned=set(inside)
    # Existing opamp/contour interiors remain distinct. Loudness stays exterior
    # so neither reduced block silently removes the other block's port.
    contour=set(range(200,229))|set(range(429,458));external=[k for k in maps()[2] if k not in contour and k not in owned]
    require(len(inside)==132 and len(external)==140 and set(ports)<=set(external),'proposed full-state partition')
    raw=(ROOT/name).read_bytes();require(raw[:8]==b'RFSCLR01','trace magic');p=8;matrices=0;incoming=outgoing=stage_cross=0;seen=set();violations=[]
    while p<len(raw):
        nnz=struct.unpack_from('<I',raw,p)[0];p+=4
        for _ in range(nnz):
            i,k,a=struct.unpack_from('<HHd',raw,p);p+=12;require(i<458 and k<458 and a!=0,'stored support')
            if i in owned and k not in allowed or k in owned and i not in allowed:violations.append([matrices,i,k])
            if i in owned and k in ports:incoming+=1;seen.add(k)
            if k in owned and i in ports:outgoing+=1;seen.add(i)
            if i in owned and k in owned and i//229!=k//229:stage_cross+=1
        p+=1832*8;matrices+=1
    require(p==len(raw) and matrices==396,'complete bank support inspection')
    write('evidence/voice_schur_chain_frontier01.json',dict(passed=not violations,source_sha256={n:sha(ROOT/n) for n in ['tools/inspect_schur_chain_frontier.py','crates/rf-d-circuit/src/joint_voice.rs',receipt]},private_used_sha256={name:sha(ROOT/name)},matrices=matrices,proposed_interiors=inside,proposed_ports=ports,ports_observed=sorted(seen),remaining_exterior=external,incoming_nonzero_observations=incoming,outgoing_nonzero_observations=outgoing,internal_cross_stage_nonzero_observations=stage_cross,foreign_couplings=violations,new_solves=0,interior_invertibility_measured=False,cost_measured=False,partition_admitted=False,physical_fidelity=False,real_time=False))
    print('CHAIN_FRONTIER',matrices,len(inside),len(external),'foreign',len(violations))
if __name__=='__main__':main()
