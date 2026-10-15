"""Use original Amount rows on the long trajectory; adapt parser and row labels only."""
import json,time,traceback,sys
from decimal import localcontext
from pathlib import Path
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources
from check_long_note_aa import arrays
import audit_chain_startup as original
def audit(native):
    original.parse=lambda raw:arrays(raw)[0]
    with localcontext() as ctx:ctx.prec=100;result=original.audit(native)
    assert len(result['profiles'])==2 and all(p['pairs']==24 and p['original_rows']==5712 for p in result['profiles'])
    result['dynamic_rows']=sum(p['original_rows'] for p in result['profiles']);result['original_rows']=result['dc_rows']+result['dynamic_rows']
    assert result['dynamic_rows']==11424 and result['original_rows']==11662
    return result
def main():
    native='evidence/long_note_aa_native01.json';sources=Sources(original.OWN+['tools/audit_long_note_aa.py','tools/check_long_note_aa.py','docs/LONG_NOTE_AA_AUDITORIA.md'])
    r=dict(passed=False,**sources.fields(),native=native,native_sha256=sha(ROOT/native),real_time=False,physical_fidelity=False);clock=time.monotonic()
    private=json.loads((ROOT/'evidence/j7_readout_tests01.json').read_text())['private_input_sha256'];used={};busy=False
    def opened(event,args):
        nonlocal busy
        if event!='open' or busy or not isinstance(args[0],str):return
        try:name=Path(args[0]).resolve().relative_to(ROOT).as_posix()
        except ValueError:return
        if name in private and name not in used:
            busy=True
            try:h=sha(ROOT/name);assert h==private[name],name;used[name]=h
            finally:busy=False
    sys.addaudithook(opened)
    try:r.update(audit(native));r['passed']=True
    except Exception:
        r['failure']=traceback.format_exc()
        try:audit(native);r['unchanged_replay']='unexpected pass'
        except Exception:r['unchanged_replay']=traceback.format_exc()
    sources.unchanged();r['used_private_sha256']=used;r['wall_s']=time.monotonic()-clock;k=1
    while(ROOT/f'evidence/long_note_aa_audit{k:02d}.json').exists():k+=1
    write(ROOT/f'evidence/long_note_aa_audit{k:02d}.json',r);print('LONG_NOTE_AA_ORIGINAL',r['passed'],r.get('original_rows'),r.get('profiles'),r.get('failure',''),flush=True)
    if not r['passed']:raise SystemExit(1)
if __name__=='__main__':main()
