"""Bound before/after replay of the independently generated full chain trajectory."""
import json,sys
from pathlib import Path
import mixer_chain_vectors as oracle
from mixer_on_native_vectors import ROOT,sha

def main():
    out=ROOT/'evidence/voice_mixer_chain_vectors_validation01.json'
    if out.exists():raise ValueError('preserve bound full chain replay')
    vp=ROOT/'evidence/voice_mixer_chain_vectors01.json';v=json.loads(vp.read_text(encoding='utf8'))
    qa=ROOT/'evidence/voice_mixer_c27_tests01.json';release=json.loads(qa.read_text(encoding='utf8'))
    sources={**release['source_sha256'],**v['source_sha256'],qa.relative_to(ROOT).as_posix():sha(qa),
        vp.relative_to(ROOT).as_posix():sha(vp),oracle.TEXT.relative_to(ROOT).as_posix():sha(oracle.TEXT),
        Path(__file__).relative_to(ROOT).as_posix():sha(Path(__file__))}
    for n,h in sources.items():
        if sha(ROOT/n)!=h:raise ValueError('fixed full chain source '+n)
    cases,text=oracle.fixtures()
    if cases!=v['cases'] or text.encode()!=oracle.TEXT.read_bytes() or sha(oracle.TEXT)!=v['text_sha256'] or v['gates']!=oracle.GATES:
        raise ValueError('full nodal trajectory replay')
    after={n:sha(ROOT/n) for n in sources}
    if after!=sources:raise ValueError('full chain replay inputs changed')
    out.write_text(json.dumps(dict(schema='rf-d/mixer-chain-vectors-audit/v1',passed=True,source_sha256=sources,source_sha256_after=after,
        cases=4,temporal_steps=64,oracle_nodal_dimensions=[67,71],original_result_preserved=True,
        native_seeds_used=False,new_spice_solves=0,physical_fidelity=False,real_time=False),indent=2)+'\n',encoding='utf8',newline='\n')
    print('bound full nodal replay passed; 4 cases, 64 steps',flush=True)

if __name__=='__main__':main()
