"""Admit nominal NJF kernel, replay oracles/exports and retain prior identity."""
import base64,hashlib,json,math,re,subprocess
from pathlib import Path
from decimal import localcontext
import vco_jfet_vectors as oracle
import vco_jfet_spice as spice_tool
from validate_mixer_on_native import native_source_identity
ROOT=oracle.ROOT;sha=oracle.sha;OUTPUT=ROOT/'evidence/voice_vco_jfet_tests01.json'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'))
def main():
 if OUTPUT.exists():raise ValueError('preserve release')
 qp=ROOT/'evidence/voice_vco_bjt_tests02.json';q=read(qp)
 vp=ROOT/'evidence/voice_vco_jfet_vectors01.json';v=read(vp)
 ap=ROOT/'evidence/voice_vco_jfet_native01.json';a=read(ap)
 sp=ROOT/'evidence/voice_vco_jfet_documentation01.json';snapshot=read(sp)
 xp=ROOT/'evidence/voice_vco_jfet_spice01.json';x=read(xp)
 if not all(r['passed'] for r in (q,v,a,x)) or q['covered_test_count']!=201:raise ValueError('inherited/new admission')
 if snapshot['previous_qa_sha256']!=sha(qp) or set(snapshot['previous_bytes_base64'])!=set(oracle.DOCS):raise ValueError('documentation lineage')
 for n,b in snapshot['previous_bytes_base64'].items():
  if hashlib.sha256(base64.b64decode(b,validate=True)).hexdigest()!=q['source_sha256'][n]:raise ValueError('exact historical document')
 for n,h in q['source_sha256'].items():
  if n in oracle.DOCS:continue
  if n in (oracle.LIB,'.gitattributes'):
   old=subprocess.check_output(['git','show',oracle.BASE+':'+n],cwd=ROOT);native_source_identity(n,h,old)
   if (ROOT/n).read_bytes()!=old+(oracle.EXPORT if n==oracle.LIB else oracle.ATTRS):raise ValueError('only additive exports/policies')
  elif sha(ROOT/n)!=h:raise ValueError('inherited input changed '+n)
 for receipt in (v,a,x):
  if receipt['source_sha256']!=receipt['source_sha256_after'] or receipt['private_input_sha256']!=receipt['private_input_sha256_after']:raise ValueError('measured source changed')
  for n,h in receipt['source_sha256'].items():
   expected=q['source_sha256'][n] if n in oracle.DOCS else sha(ROOT/n)
   if h!=expected:raise ValueError('measured source no longer bound '+n)
  for n,h in receipt['private_input_sha256'].items():
   if sha(ROOT/n)!=h:raise ValueError('primary device source changed '+n)
 cards=read(ROOT/'evidence/vco1_laboratory_devices.json')
 if cards['jfet']!=oracle.CARD or cards['temperature_c']!=25 or v['card']!=oracle.CARD:raise ValueError('exact source card')
 if (v['rows'],v['columns'],v['decimal_precision'],v['input_conversion'],v['native_seeds_used'],v['thermal_voltage_v'])!=(2028,48,100,'Decimal.from_float',False,oracle.VT):raise ValueError('oracle definitions')
 pins={n:sha(ROOT/n) for n in v['source_sha256']};rows,text,neighbors=oracle.fixtures()
 if canonical(rows)!=canonical(v['cases']) or canonical(neighbors)!=canonical(v['neighbors']) or len(neighbors)!=20:raise ValueError('independent Decimal replay')
 tp=ROOT/'evidence/voice_vco_jfet_vectors01.txt';np=ROOT/'evidence/voice_vco_jfet_neighbors01.txt'
 if tp.read_bytes()!=text.encode() or sha(tp)!=v['text_sha256'] or np.read_bytes()!=oracle.table(neighbors).encode() or sha(np)!=v['neighbor_text_sha256']:raise ValueError('exact numerical fixtures')
 if pins!={n:sha(ROOT/n) for n in pins}:raise ValueError('oracle changed during replay')
 if (x['rows'],x['columns'],x['new_spice_processes'])!=(12,28,12) or len(x['cases'])!=12 or x['unchanged_replays']:raise ValueError('complete fresh independent probes')
 if canonical(x['gates'])!=canonical(spice_tool.GATES):raise ValueError('frozen SPICE gates')
 if x['executable_sha256']!=q['official_executable_sha256'] or x['executable_sha256_after']!=q['official_executable_sha256']:raise ValueError('official executable identity')
 if not x['resource_passed'] or x['estimated_export_bytes']!=8*1024**2 or x['margin_bytes']!=2*1024**3 or x['available_free_bytes']<x['estimated_export_bytes']+x['margin_bytes']:raise ValueError('SPICE resource admission')
 expected_nodes=[[.17-gd,.17,.17-gs] for gs,gd in spice_tool.BIAS];spice_rows=[]
 flat=lambda m:[v for row in m for v in row]
 for index,c in enumerate(x['cases']):
  if not c['passed'] or c['exit_code'] or c['terminal_v']!=expected_nodes[index]:raise ValueError('independent point identity')
  case=ROOT/f'references-local/vco-jfet-spice01/case{index:02d}'
  if sha(case/'probe.cir')!=c['deck_sha256'] or (case/'probe.log').read_text(encoding='utf8')!=c['stdout']+c['stderr']:raise ValueError('original deck/log')
  measured=spice_tool.measure(case,c['stdout'],c['terminal_v'])
  if any(canonical(value)!=canonical(c[n]) for n,value in measured.items()):raise ValueError('original complete SPICE export replay')
  if len(c['checks'])!=4 or not all(g['passed'] and 0<=g['max_gate_ratio']<=1 for g in c['checks']):raise ValueError('independent point gates')
  spice_rows.append([*c['terminal_v'],*c['ngspice_junction_charge_c'],*c['ngspice_junction_cap_f'],*c['ngspice_current_a'],*flat(c['admittance_real_s']),*flat(c['admittance_imag_s'])])
 xt=ROOT/'evidence/voice_vco_jfet_spice01.txt'
 if xt.read_bytes()!=oracle.table(spice_rows).encode() or sha(xt)!=x['text_sha256']:raise ValueError('exact SPICE native fixture')
 compiler=a['compiler']
 if sha(Path(compiler['path']))!=compiler['sha256'] or a['compiler_sha256_after']!=compiler['sha256']:raise ValueError('compiler identity')
 if not a['resource_passed'] or a['estimated_build_bytes']!=64*1024**2 or a['margin_bytes']!=2*1024**3 or a['available_free_bytes']<a['estimated_build_bytes']+a['margin_bytes']:raise ValueError('production resource admission')
 if a['unchanged_replays'] or any(c['exit_code'] for c in a['commands']) or [c['kind'] for c in a['commands']]!=['compile','compile','test','compile','test']:raise ValueError('captured production commands')
 tests='\n'.join(c['stdout'] for c in a['commands'] if c['kind']=='test')
 if re.findall(r'test result: ok\. (\d+) passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;',tests)!=['3','1'] or tests.count('VCO_JFET_ALLOCATION,stamps=10000,allocations=0')!=1:raise ValueError('four tests and isolated heap result')
 match=re.search(r'VCO_JFET_ORACLE,rows=2028,spice=12,max_i_a=([^,\s]+),max_q_c=([^,\s]+),max_j_s=([^,\s]+),max_c_f=([^,\s]+),max_delta_c=([^,\s]+),max_spice_y_s=([^,\s]+)',tests)
 if not match:raise ValueError('captured numerical maxima')
 maxima=dict(zip(('i_a','q_c','j_s','c_f','delta_c','spice_y_s'),map(float,match.groups())))
 if any(not math.isfinite(v) or v<0 for v in maxima.values()):raise ValueError('finite measured maxima')
 private=dict(q['private_input_sha256']);private.update(v['private_input_sha256'])
 if len(a['outputs'])!=3 or len(x['outputs'])!=96:raise ValueError('retained library/tests and full SPICE exports')
 for receipt,folder in ((a,'vco-jfet-native01'),(x,'vco-jfet-spice01')):
  for item in receipt['outputs']:
   path=ROOT/item['path']
   if not path.resolve().is_relative_to((ROOT/'references-local'/folder).resolve()) or path.stat().st_size!=item['bytes'] or sha(path)!=item['sha256']:raise ValueError('preserved private output')
   private[item['path']]=item['sha256']
 for n,h in private.items():
  if sha(ROOT/n)!=h:raise ValueError('private inherited input changed '+n)
 if sha(ROOT/q['previous_audio']['path'])!=q['previous_audio']['sha256'] or sha(ROOT/'references-local/ngspice46/runtime/Spice64/bin/ngspice_con.exe')!=q['official_executable_sha256']:raise ValueError('old audio/executable unchanged')
 staged=subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=ROOT).decode().split('\0')
 names=sorted(set(q['source_sha256'])|{qp.relative_to(ROOT).as_posix()}|{n for n in staged if n and ROOT/n!=OUTPUT})
 sources={n:sha(ROOT/n) for n in names}
 for n,h in sources.items():native_source_identity(n,h,subprocess.check_output(['git','show',':'+n],cwd=ROOT))
 local=[]
 for n in (*oracle.DOCS,'docs/VCO_JFET_NOMINAL_PROTOCOLO.md','docs/VCO_JFET_NOMINAL_RESULTADOS.md'):
  path=ROOT/n
  for link in re.findall(r'\]\(([^)]+)\)',path.read_text(encoding='utf8')):
   if link.startswith(('http:','https:','#')):continue
   target=(path.parent/link.split('#')[0]).resolve()
   if not target.exists() and target!=OUTPUT.resolve():raise ValueError('missing local publication link '+link)
   local.append(target.relative_to(ROOT).as_posix())
 after={n:sha(ROOT/n) for n in names}
 if sources!=after:raise ValueError('publication changed')
 OUTPUT.write_text(json.dumps(dict(schema='rf-d/vco-jfet-release/v1',passed=True,base_commit=oracle.BASE,previous_qa_sha256=sha(qp),source_sha256=sources,source_sha256_after=after,private_input_sha256=private,documentation_snapshot_sha256=sha(sp),oracle_sha256=sha(vp),production_sha256=sha(ap),spice_sha256=sha(xp),numerical_maxima=maxima,vector_count=2028,neighbor_count=20,spice_case_count=12,covered_test_count=205,inherited_test_count=201,native_test_count=4,inherited_tests_reexecuted=False,old_native_algorithms_unchanged=True,jfet_nominal_half_admitted=True,temperature_c=25,tnom_c=25,other_temperatures_admitted=False,dual_common_source_integration_admitted=False,physical_capacitances_not_swapped=True,ac_charge_storage_semantics_explicit=True,native_vco_admitted=False,checked_local_targets=sorted(set(local)),previous_audio=q['previous_audio'],official_executable_sha256=q['official_executable_sha256'],new_spice_processes=12,new_audio=False,long_note_admitted_locally=False,physical_fidelity=False,real_time=False),indent=2)+'\n',encoding='utf8',newline='\n')
 print('JFET release: 205 covered, 4 executed + 201 inherited;',len(sources),'inputs;',len(private),'private inputs',flush=True)
if __name__=='__main__':main()
