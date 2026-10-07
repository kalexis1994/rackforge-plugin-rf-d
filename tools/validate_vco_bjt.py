"""Publish bounded depletion-charge admission with exact inherited identity."""
import base64,hashlib,json,math,re,subprocess
from pathlib import Path
import vco_bjt_vectors as oracle
from validate_mixer_on_native import native_source_identity
ROOT=oracle.ROOT;sha=oracle.sha
OUTPUT=ROOT/'evidence/voice_vco_bjt_tests01.json'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def main():
 if OUTPUT.exists():raise ValueError('preserve release')
 qp=ROOT/'evidence/voice_junction_charge_tests01.json';q=read(qp)
 vp=ROOT/'evidence/voice_vco_bjt_vectors01.json';v=read(vp)
 ap=ROOT/'evidence/voice_vco_bjt_native01.json';a=read(ap)
 sp=ROOT/'evidence/voice_vco_bjt_documentation01.json';snapshot=read(sp)
 if not all(x['passed'] for x in (q,v,a)) or q['covered_test_count']!=197:raise ValueError('inherited/production admission')
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
 cards=read(ROOT/'evidence/vco1_laboratory_devices.json');b=cards['bjt']
 expected={'IS':1e-14,'BF':100,'BR':5,'VAF':0,'IKF':0,'CJE':7e-12,'VJE':.75,'MJE':.5,'CJC':3e-12,'VJC':.7,'MJC':.33,'FC':.4,'TF':1e-9,'TR':3e-9,'TNOM':25}
 if b!=expected or cards['temperature_c']!=25:raise ValueError('exact nominal source card')
 if (v['rows'],v['columns'],v['decimal_precision'],v['input_conversion'],v['native_seeds_used'],v['thermal_voltage_v'])!=(1536,74,100,'Decimal.from_float',False,oracle.VT):raise ValueError('oracle definition')
 pins={n:sha(ROOT/n) for n in v['source_sha256']};rows,text,neighbors=oracle.fixtures()
 canonical=lambda value:json.dumps(value,sort_keys=True,separators=(',',':'))
 if canonical(rows)!=canonical(v['cases']) or canonical(neighbors)!=canonical(v['neighbors']) or len(neighbors)!=20:raise ValueError('independent oracle replay')
 if text.encode()!=(ROOT/'evidence/voice_vco_bjt_vectors01.txt').read_bytes() or sha(ROOT/'evidence/voice_vco_bjt_vectors01.txt')!=v['text_sha256']:raise ValueError('oracle text')
 nt=ROOT/'evidence/voice_vco_bjt_neighbors01.txt';neighbor_text='\n'.join(' '.join(format(x,'.17e') for x in row) for row in neighbors)+'\n'
 if neighbor_text.encode()!=nt.read_bytes() or sha(nt)!=v['neighbor_text_sha256']:raise ValueError('neighbor table replay')
 if pins!={n:sha(ROOT/n) for n in pins}:raise ValueError('oracle changed during replay')
 for receipt in (v,a):
  if 'private_input_sha256_after' in receipt and receipt['private_input_sha256_after']!=receipt['private_input_sha256']:raise ValueError('private device source changed during run')
  for n,h in receipt['private_input_sha256'].items():
   if sha(ROOT/n)!=h:raise ValueError('primary device source changed '+n)
 spice=read(ROOT/'evidence/voice_vco_bjt_spice02.json');failed=read(ROOT/'evidence/voice_vco_bjt_spice01.json')
 for receipt in (spice,failed):
  if receipt['source_sha256']!=receipt['source_sha256_after'] or receipt['private_input_sha256']!=receipt['private_input_sha256_after']:raise ValueError('SPICE inputs changed during attempt')
  for n,h in receipt['source_sha256'].items():
   expected_hash=q['source_sha256'][n] if n in oracle.DOCS else sha(ROOT/n)
   if h!=expected_hash:raise ValueError('bound SPICE source changed '+n)
  for n,h in receipt['private_input_sha256'].items():
   if sha(ROOT/n)!=h:raise ValueError('private SPICE input')
  if receipt['executable_sha256']!=q['official_executable_sha256'] or receipt['executable_sha256_after']!=q['official_executable_sha256']:raise ValueError('SPICE executable identity')
  if not receipt['resource_passed'] or receipt['estimated_export_bytes']!=8*1024**2 or receipt['margin_bytes']!=2*1024**3 or receipt['available_free_bytes']<receipt['estimated_export_bytes']+receipt['margin_bytes']:raise ValueError('SPICE resources')
 if failed['passed'] or failed['error']!='finite complete table' or len(failed['cases'])!=1 or len(failed['unchanged_replays'])!=1:raise ValueError('preserved failed export and unchanged replay')
 fc=failed['cases'][0];replay=failed['unchanged_replays'][0]
 if replay['command']!=fc['command'] or replay['exit_code']!=fc['exit_code'] or replay['deck_sha256_after']!=fc['deck_sha256'] or replay['source_sha256']!=failed['source_sha256']:raise ValueError('exact original replay')
 for n,b64 in fc['failed_original_bytes_base64'].items():
  original=base64.b64decode(b64,validate=True)
  if original!=(ROOT/'references-local/vco-bjt-spice01/case00'/n).read_bytes():raise ValueError('unchanged replay reproduces original bytes '+n)
 for n,source in fc['failed_source_text'].items():
  original=base64.b64decode(snapshot['previous_bytes_base64'][n],validate=True).decode('utf8') if n in oracle.DOCS else (ROOT/n).read_text(encoding='utf8')
  if source!=original:raise ValueError('failure source snapshot')
 if not spice['passed'] or spice['unchanged_replays'] or (spice['rows'],spice['columns'],spice['new_spice_processes'])!=(12,45,12) or len(spice['cases'])!=12:raise ValueError('complete independent SPICE')
 expected_gates={'i':[2e-14,1e-7],'q':[1e-20,1e-7],'c':[1e-19,1e-7],'y':[2e-12,1e-7]}
 if spice['gates']!=expected_gates or failed['gates']!=expected_gates:raise ValueError('unchanged independent gates')
 flat=lambda m:[x for row in m for x in row]
 spice_rows=[]
 for c in spice['cases']:
  if not c['passed'] or c['exit_code'] or len(c['checks'])!=4 or not all(x['passed'] and 0<=x['max_gate_ratio']<=1 for x in c['checks']):raise ValueError('independent point gates')
  spice_rows.append([c['polarity'],*c['terminal_v'],*c['ngspice_oriented_charge_c'],*c['ngspice_junction_cap_f'],*c['ngspice_current_a'],*flat(c['admittance_real_s']),*flat(c['admittance_imag_s'])])
 st=ROOT/'evidence/voice_vco_bjt_spice02.txt';spice_text='\n'.join(' '.join(format(x,'.17e') for x in row) for row in spice_rows)+'\n'
 if st.read_bytes()!=spice_text.encode() or sha(st)!=spice['text_sha256']:raise ValueError('SPICE test table exact')
 import vco_bjt_ac_audit
 audit=read(ROOT/'evidence/voice_vco_bjt_ac_audit01.json')
 if canonical(audit)!=canonical(vco_bjt_ac_audit.audit()):raise ValueError('retained AC discrepancy replay')
 compiler=a['compiler']
 if sha(Path(compiler['path']))!=compiler['sha256'] or a['compiler_sha256_after']!=compiler['sha256']:raise ValueError('compiler identity')
 if not a['resource_passed'] or a['available_free_bytes']<a['estimated_build_bytes']+a['margin_bytes'] or a['estimated_build_bytes']!=64*1024**2 or a['margin_bytes']!=2*1024**3:raise ValueError('resource admission')
 if a['unchanged_replays'] or any(c['exit_code'] for c in a['commands']) or [c['kind'] for c in a['commands']]!=['compile','compile','test','compile','test']:raise ValueError('successful captured commands')
 tests='\n'.join(c['stdout'] for c in a['commands'] if c['kind']=='test')
 if re.findall(r'test result: ok\. (\d+) passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;',tests)!=['3','1']:raise ValueError('four production tests')
 if tests.count('VCO_BJT_ALLOCATION,stamps=10000,allocations=0')!=1:raise ValueError('isolated heap result')
 match=re.search(r'VCO_BJT_ORACLE,rows=1536,spice=12,max_i_a=([^,\s]+),max_q_c=([^,\s]+),max_j_s=([^,\s]+),max_c_f=([^,\s]+),max_delta_c=([^,\s]+),max_spice_y_s=([^,\s]+)',tests)
 if not match:raise ValueError('captured numerical maxima')
 maxima=dict(zip(('i_a','q_c','j_s','c_f','delta_c','spice_y_s'),map(float,match.groups())))
 if any(not math.isfinite(x) or x<0 for x in maxima.values()):raise ValueError('finite maxima')
 private=dict(q['private_input_sha256'])
 if len(a['outputs'])!=3:raise ValueError('library and two test binaries')
 for item in a['outputs']:
  path=ROOT/item['path']
  if not path.resolve().is_relative_to((ROOT/'references-local/vco-bjt-native01').resolve()) or path.stat().st_size!=item['bytes'] or sha(path)!=item['sha256']:raise ValueError('retained production binary')
  private[item['path']]=item['sha256']
 for receipt in (v,a,spice,failed):
  private.update(receipt.get('private_input_sha256',{}))
 for receipt in (spice,failed):
  for item in receipt['outputs']:
   path=ROOT/item['path']
   if not path.resolve().is_relative_to((ROOT/'references-local').resolve()) or path.stat().st_size!=item['bytes'] or sha(path)!=item['sha256']:raise ValueError('preserved SPICE output')
   private[item['path']]=item['sha256']
 private.update({n:h for n,h in audit['source_sha256'].items() if n.startswith('references-local/')})
 for n,h in private.items():
  if sha(ROOT/n)!=h:raise ValueError('private input changed '+n)
 if sha(ROOT/q['previous_audio']['path'])!=q['previous_audio']['sha256'] or sha(ROOT/'references-local/ngspice46/runtime/Spice64/bin/ngspice_con.exe')!=q['official_executable_sha256']:raise ValueError('old audio/official executable')
 staged=subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=ROOT).decode().split('\0')
 names=sorted(set(q['source_sha256'])|{qp.relative_to(ROOT).as_posix()}|{n for n in staged if n and ROOT/n!=OUTPUT})
 sources={n:sha(ROOT/n) for n in names}
 for n,h in sources.items():native_source_identity(n,h,subprocess.check_output(['git','show',':'+n],cwd=ROOT))
 local=[]
 for n in (*oracle.DOCS,'docs/VCO_BJT_NOMINAL_PROTOCOLO.md','docs/VCO_BJT_NOMINAL_RESULTADOS.md'):
  path=ROOT/n
  for link in re.findall(r'\]\(([^)]+)\)',path.read_text(encoding='utf8')):
   if link.startswith(('http:','https:','#')):continue
   target=(path.parent/link.split('#')[0]).resolve()
   if not target.exists() and target!=OUTPUT.resolve():raise ValueError('missing publication link '+link)
   local.append(target.relative_to(ROOT).as_posix())
 after={n:sha(ROOT/n) for n in names}
 if sources!=after:raise ValueError('publication changed')
 OUTPUT.write_text(json.dumps(dict(schema='rf-d/vco-bjt-release/v1',passed=True,base_commit=oracle.BASE,previous_qa_sha256=sha(qp),source_sha256=sources,source_sha256_after=after,private_input_sha256=private,documentation_snapshot_sha256=sha(sp),oracle_sha256=sha(vp),production_sha256=sha(ap),numerical_maxima=maxima,vector_count=1536,neighbor_count=20,spice_case_count=12,covered_test_count=201,inherited_test_count=197,native_test_count=4,inherited_tests_reexecuted=False,old_native_algorithms_unchanged=True,bjt_nominal_transport_diffusion_implemented=True,temperature_c=25,tnom_c=25,other_temperatures_admitted=False,substrate_explicit=True,ac_dc_gmin_discrepancy_retained=True,native_vco_admitted=False,checked_local_targets=sorted(set(local)),previous_audio=q['previous_audio'],official_executable_sha256=q['official_executable_sha256'],new_spice_processes=14,new_audio=False,failed_export_replayed_unchanged=True,long_note_admitted_locally=False,physical_fidelity=False,real_time=False),indent=2)+'\n',encoding='utf8',newline='\n')
 print('BJT release: 201 covered, 4 executed + 197 inherited;',len(sources),'inputs;',len(private),'private inputs')
if __name__=='__main__':main()
