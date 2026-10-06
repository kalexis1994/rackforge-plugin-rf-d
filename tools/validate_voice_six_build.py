"""Exact two-anchor source diff and inherited build09 configuration."""
import difflib,json,subprocess
from pathlib import Path
import voice_six_build as build
import voice_union_refine_runner as prior
import validate_voice_full_note_matrix as previous
import vco1_circuit_reference as vco

ROOT=vco.ROOT

def validate():
    inherited=previous.build_identity()
    path=ROOT/'evidence/voice_six_build01.json';r=vco.read(path)
    if prior.canonical(r)!=prior.canonical(vco.read(build.WORK/'build.json')) or r['exit_code']!=0:raise ValueError('six compile receipt')
    if vco.sha(Path(build.__file__))!=r['helper_sha256'] or r['helper_sha256']!=r['helper_sha256_after'] or vco.sha(ROOT/build.PROTOCOL)!=r['protocol_sha256']:raise ValueError('frozen preparation')
    original=(build.PRIOR/'ngspice-46'/build.NAME).read_text(encoding='utf-8');changed=build.patched(original)
    if (build.TREE/build.NAME).read_bytes()!=changed.encode():raise ValueError('exact two-anchor six source')
    if r['patch']['diff']!=''.join(difflib.unified_diff(original.splitlines(True),changed.splitlines(True),n=2)):raise ValueError('declared diff')
    a=build.inventory(build.PRIOR/'ngspice-46');b=build.inventory(build.TREE)
    if set(a)!=set(b) or [n for n in a if a[n]!=b[n]]!=[build.NAME] or len(a)!=r['source_files']:raise ValueError('full source inventory')
    if prior.canonical(vco.read(build.WORK/'source-inventory.json'))!=prior.canonical(dict(before=a,after=b)) or vco.sha(build.WORK/'source-inventory.json')!=r['source_inventory_sha256']:raise ValueError('source inventory receipt')
    if r['patch']['before_sha256']!=a[build.NAME] or r['patch']['after_sha256']!=b[build.NAME]:raise ValueError('patch hashes')
    old=vco.read(build.PRIOR/'build.json');compiler=Path(r['compiler_path'])
    if vco.sha(build.PRIOR/'build.json')!=r['prior_build_sha256'] or r['compiler_sha256']!=old['compiler_sha256'] or r['compiler_sha256_after']!=r['compiler_sha256'] or vco.sha(compiler)!=r['compiler_sha256']:raise ValueError('compiler bytes')
    if r['cflags']!=old['cflags'] or r['ldflags']!=old['ldflags'] or r['corrections']!=6 or r['published_corrections']!=6 or r['shadow_corrections']!=0 or not r['numerical_algorithm_changed'] or r['observer_selection_changed'] or r['device_stamps_changed'] or r['state_update_changed']:raise ValueError('six numerical scope')
    if r['available_free_bytes']<r['copy_bytes']+r['estimated_exports_bytes']+r['margin_bytes'] or r['margin_bytes']!=2*1024**3:raise ValueError('preparation resources')
    for name,pair in r['relocated_generated_files'].items():
        p=build.PRIOR/name;q=build.WORK/name
        if vco.sha(p)!=pair['before_sha256'] or vco.sha(q)!=pair['after_sha256'] or q.read_bytes()!=p.read_bytes().replace(b'newton-build09',b'newton-build11'):raise ValueError('only generated path relocation')
    if vco.sha(build.WORK/'build.log')!=r['build_log_sha256'] or vco.sha(build.WORK/'bin/candidate.exe')!=r['executable_sha256']:raise ValueError('compiled bytes')
    if vco.sha(build.WORK/'baseline02/src/xspice/icm/spice2poly/spice2poly.cm')!=vco.sha(build.PRIOR/'baseline02/src/xspice/icm/spice2poly/spice2poly.cm'):raise ValueError('module inheritance')
    return dict(passed=True,build_sha256=vco.sha(path),inherited_build09=inherited,source_files=len(a),changed_source=build.NAME,
        compiler_sha256=r['compiler_sha256'],executable_sha256=r['executable_sha256'],published_corrections=6,
        numerical_algorithm_changed=True,device_stamps_changed=False,state_history_changed=False,
        new_spice_solves=0,new_compiler_runs=0,
        source_sha256={p.relative_to(ROOT).as_posix():vco.sha(p) for p in (Path(__file__),Path(build.__file__),Path(previous.__file__))})

def main():
    output=ROOT/'evidence/voice_six_build_validation01.json'
    if output.exists():raise ValueError('preserve build audit')
    r=validate();r['schema']='rf-d/active-six-build-validation/v1'
    output.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('six build audit:',r['source_files'],'source files; exact two-anchor diff',flush=True)

if __name__=='__main__':main()
