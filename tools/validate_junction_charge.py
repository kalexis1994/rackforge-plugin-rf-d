"""Publish bounded depletion-charge admission with exact inherited identity."""
import base64,hashlib,json,math,re,subprocess
from pathlib import Path
import junction_charge_vectors as oracle
from validate_mixer_on_native import native_source_identity
ROOT=oracle.ROOT;sha=oracle.sha
OUTPUT=ROOT/'evidence/voice_junction_charge_tests01.json'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def main():
 if OUTPUT.exists():raise ValueError('preserve release')
 qp=ROOT/'evidence/voice_mixer_direct_tests01.json';q=read(qp)
 vp=ROOT/'evidence/voice_junction_charge_vectors01.json';v=read(vp)
 ap=ROOT/'evidence/voice_junction_charge_native01.json';a=read(ap)
 sp=ROOT/'evidence/voice_junction_charge_documentation01.json';snapshot=read(sp)
 if not all(x['passed'] for x in (q,v,a)) or q['covered_test_count']!=193:raise ValueError('inherited/production admission')
 if snapshot['previous_qa_sha256']!=sha(qp) or set(snapshot['previous_bytes_base64'])!=set(oracle.DOCS):raise ValueError('documentation lineage')
 for n,b in snapshot['previous_bytes_base64'].items():
  if hashlib.sha256(base64.b64decode(b,validate=True)).hexdigest()!=q['source_sha256'][n]:raise ValueError('exact historical document')
 for n,h in q['source_sha256'].items():
  if n in oracle.DOCS:continue
  if n in (oracle.LIB,'.gitattributes'):
   old=subprocess.check_output(['git','show',oracle.BASE+':'+n],cwd=ROOT)
   native_source_identity(n,h,old)
   if (ROOT/n).read_bytes()!=old+(oracle.EXPORT if n==oracle.LIB else oracle.ATTRS):raise ValueError('only additive exports/policies')
  elif sha(ROOT/n)!=h:raise ValueError('inherited input changed '+n)
 for receipt in (v,a):
  if receipt['source_sha256']!=receipt['source_sha256_after']:raise ValueError('measured source changed')
  for n,h in receipt['source_sha256'].items():
   if n in oracle.DOCS:
    if h!=q['source_sha256'][n]:raise ValueError('measured historical document')
   elif sha(ROOT/n)!=h:raise ValueError('measured input changed '+n)
 cards=read(ROOT/'evidence/vco1_laboratory_devices.json');b=cards['bjt'];j=cards['jfet']
 expected=((b['CJE'],b['VJE'],b['MJE'],b['FC']),(b['CJC'],b['VJC'],b['MJC'],b['FC']),(j['CGS'],j['PB'],.5,j['FC']),(j['CGD'],j['PB'],.5,j['FC']))
 if oracle.CARDS!=expected or cards['temperature_c']!=25 or b['TNOM']!=25 or j['TNOM']!=25:raise ValueError('nominal source cards')
 if (v['rows'],v['columns'],v['decimal_precision'],v['input_conversion'],v['native_seeds_used'])!=(1280,14,100,'Decimal.from_float',False):raise ValueError('oracle definition')
 pins={n:sha(ROOT/n) for n in v['source_sha256']};rows,text=oracle.fixtures()
 if rows!=v['cases'] or text.encode()!=(ROOT/'evidence/voice_junction_charge_vectors01.txt').read_bytes() or sha(ROOT/'evidence/voice_junction_charge_vectors01.txt')!=v['text_sha256']:raise ValueError('exact independent oracle replay')
 if pins!={n:sha(ROOT/n) for n in pins}:raise ValueError('oracle changed during replay')
 compiler=a['compiler']
 if sha(Path(compiler['path']))!=compiler['sha256'] or a['compiler_sha256_after']!=compiler['sha256']:raise ValueError('compiler identity')
 if not a['resource_passed'] or a['available_free_bytes']<a['estimated_build_bytes']+a['margin_bytes'] or a['estimated_build_bytes']!=64*1024**2 or a['margin_bytes']!=2*1024**3:raise ValueError('resource admission')
 if a['unchanged_replays'] or any(c['exit_code'] for c in a['commands']) or [c['kind'] for c in a['commands']]!=['compile','compile','test','compile','test']:raise ValueError('successful captured commands')
 tests='\n'.join(c['stdout'] for c in a['commands'] if c['kind']=='test')
 if re.findall(r'test result: ok\. (\d+) passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;',tests)!=['3','1']:raise ValueError('four production tests')
 if tests.count('JUNCTION_ALLOCATION,companions=10000,allocations=0')!=1:raise ValueError('isolated heap result')
 match=re.search(r'JUNCTION_ORACLE,rows=1280,max_q_c=([^,\s]+),max_c_f=([^,\s]+),max_delta_c=([^,\s]+),max_i_a=([^,\s]+),max_g_s=([^,\s]+)',tests)
 if not match:raise ValueError('captured numerical maxima')
 maxima=dict(zip(('q_c','c_f','delta_c','i_a','g_s'),map(float,match.groups())))
 if any(not math.isfinite(x) or x<0 for x in maxima.values()):raise ValueError('finite maxima')
 private=dict(q['private_input_sha256'])
 if len(a['outputs'])!=3:raise ValueError('library and two test binaries')
 for item in a['outputs']:
  path=ROOT/item['path']
  if not path.resolve().is_relative_to((ROOT/'references-local/junction-charge-native01').resolve()) or path.stat().st_size!=item['bytes'] or sha(path)!=item['sha256']:raise ValueError('retained production binary')
  private[item['path']]=item['sha256']
 # Local primary-source audit. Original files are never vendored into public Git.
 for name in ('jfetload.c','jfettemp.c','jfetset.c'):
  n='references-local/voice-circuit/newton-build11/ngspice-46/src/spicelib/devices/jfet/'+name
  private[n]=sha(ROOT/n)
 for n,h in private.items():
  if sha(ROOT/n)!=h:raise ValueError('private input changed '+n)
 if sha(ROOT/q['previous_audio']['path'])!=q['previous_audio']['sha256'] or sha(ROOT/'references-local/ngspice46/runtime/Spice64/bin/ngspice_con.exe')!=q['official_executable_sha256']:raise ValueError('old audio/official executable')
 staged=subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=ROOT).decode().split('\0')
 names=sorted(set(q['source_sha256'])|{qp.relative_to(ROOT).as_posix()}|{n for n in staged if n and ROOT/n!=OUTPUT})
 sources={n:sha(ROOT/n) for n in names}
 for n,h in sources.items():native_source_identity(n,h,subprocess.check_output(['git','show',':'+n],cwd=ROOT))
 local=[]
 for n in (*oracle.DOCS,'docs/VCO_CARGA_JUNTURA_PROTOCOLO.md','docs/VCO_CARGA_JUNTURA_RESULTADOS.md'):
  path=ROOT/n
  for link in re.findall(r'\]\(([^)]+)\)',path.read_text(encoding='utf8')):
   if link.startswith(('http:','https:','#')):continue
   target=(path.parent/link.split('#')[0]).resolve()
   if not target.exists() and target!=OUTPUT.resolve():raise ValueError('missing publication link '+link)
   local.append(target.relative_to(ROOT).as_posix())
 after={n:sha(ROOT/n) for n in names}
 if sources!=after:raise ValueError('publication changed')
 OUTPUT.write_text(json.dumps(dict(schema='rf-d/junction-charge-release/v1',passed=True,base_commit=oracle.BASE,previous_qa_sha256=sha(qp),source_sha256=sources,source_sha256_after=after,private_input_sha256=private,documentation_snapshot_sha256=sha(sp),oracle_sha256=sha(vp),production_sha256=sha(ap),numerical_maxima=maxima,vector_count=1280,covered_test_count=197,inherited_test_count=193,native_test_count=4,inherited_tests_reexecuted=False,old_native_algorithms_unchanged=True,depletion_charge_only=True,transport_diffusion_implemented=False,temperature_binding_implemented=False,native_vco_admitted=False,checked_local_targets=sorted(set(local)),previous_audio=q['previous_audio'],official_executable_sha256=q['official_executable_sha256'],new_spice_solves=0,new_audio=False,long_note_admitted_locally=False,physical_fidelity=False,real_time=False),indent=2)+'\n',encoding='utf8',newline='\n')
 print('junction release: 197 covered, 4 executed + 193 inherited;',len(sources),'inputs;',len(private),'private inputs')
if __name__=='__main__':main()
