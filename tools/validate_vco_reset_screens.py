"""Replay terminal equivalence and five preserved reset-screen receipts."""
import gzip,hashlib,json,re,subprocess,time
from pathlib import Path
import numpy as np
import voice_jfet_decomposed_probes as p
import voice_vco_rshunt as shunt
import vco1_circuit_reference as vco
from validate_loudness_board4_bank import source_identity

ROOT=vco.ROOT
ARCHIVES=('voice_jfet_decomposed01.json.gz','voice_jfet_decomposed02.json.gz',
          'voice_vco_rshunt01.json.gz','voice_vco_rshunt02.json.gz')


def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':')).encode()


def main():
    output=ROOT/'evidence/voice_reset_representation_validation.json'
    if output.exists():raise ValueError('preserve prior audit')
    start=time.perf_counter();sources={};records=[];payloads={};results={};cache={}
    reference_path=ROOT/'references-local/voice-circuit/port-behavioral01/fixed-contour-control-01-vco.txt'
    original=json.loads(gzip.decompress((ROOT/'evidence/voice_port_behavioral01.json.gz').read_bytes()))['cases']['fixed-contour-control']['iterations'][0]['vco_receipt']
    if vco.sha(reference_path)!=original['raw_export_sha256']:raise ValueError('positive control identity')
    reference=np.loadtxt(reference_path,skiprows=1,ndmin=2)
    for name in ARCHIVES:
        archive=ROOT/'evidence'/name;payload=gzip.decompress(archive.read_bytes());bank=json.loads(payload)
        if bank['passed'] or bank['coupling_admitted'] or canonical(bank['gates'])!=canonical(p.GATES):raise ValueError('rejected frozen scope/gates')
        if name.startswith('voice_vco_rshunt') and bank['selected'] is not None:raise ValueError('no regularizer selected')
        work=ROOT/'references-local/voice-circuit'/bank['bank']
        for label,case in bank['cases'].items():
            r=case['receipt']
            if canonical(vco.read(work/(label+'.json')))!=canonical(r):raise ValueError('private/public receipt identity')
            if r['source_sha256']!=r['source_sha256_after'] or r['executable_sha256']!=vco.EXPECTED_EXE_SHA or vco.sha(Path(r['command'][0]))!=vco.EXPECTED_EXE_SHA:
                raise ValueError('stable sources and frozen executable')
            for source,digest in r['source_sha256'].items():
                key=(r['git_commit'],source,digest)
                if key in cache:continue
                if source.startswith('references-local/'):
                    if source!='references-local/datasheets/ti_lm741_lm741.lib' or digest!='f58370983c8bd22bf6a59ddd05a1dd492f1a0ea60f673ffd460a356da5e693dc' or vco.sha(ROOT/source)!=digest:
                        raise ValueError('private TI model identity')
                    mode='identified-private-file'
                else:
                    blob=subprocess.check_output(['git','show',r['git_commit']+':'+source],cwd=ROOT)
                    mode=source_identity(source,digest,blob)
                sources[source]=mode;cache[key]=True
            for ext,key in (('cir','deck_sha256'),('log','log_sha256')):
                if vco.sha(work/(label+'.'+ext))!=r[key]:raise ValueError('artifact identity')
            rawpath=work/(label+'.txt');key='raw_export_sha256' if r['trajectory_complete'] else 'partial_export_sha256'
            if vco.sha(rawpath)!=r[key]:raise ValueError('export identity')
            raw=np.loadtxt(rawpath,skiprows=1,ndmin=2)
            vectors=p.bench.BENCH_VECTORS if label=='terminal-benchmark' else p.p.VCO_VECTORS
            clock=r['scenario']['board']['oscillator'];t=raw[:,0]
            if raw.shape[1]!=len(vectors)+1 or not np.isfinite(raw).all() or t[0]!=0 or np.any(np.diff(t)<=0):raise ValueError('finite export/clock')
            complete=r['trajectory_complete'];failure=None
            if complete:
                if len(raw)!=r['rows'] or abs(t[-1]-clock['duration_s'])>1e-14 or np.diff(t).max()>clock['max_step_s']*(1+1e-7):raise ValueError('complete trajectory gate')
                compressed=rawpath.with_suffix('.txt.gz')
                if hashlib.sha256(gzip.decompress(compressed.read_bytes())).hexdigest()!=r[key]:raise ValueError('compressed trajectory identity')
            else:
                log=(work/(label+'.log')).read_text(encoding='utf-8')
                found=re.search(r'doAnalyses: TRAN:  Timestep too small;[^\n]+',log)
                if not found or not r.get('error') or t[-1]>=clock['duration_s'] or float(t[-1])!=case['last_clock_s']:raise ValueError('preserved reset rejection')
                failure=found.group(0)
            if label=='terminal-benchmark':
                replay=p.bench.validate_benchmark(raw)
                if canonical(replay)!=canonical(case['measurements']) or not case['passed']:raise ValueError('terminal equivalence replay')
                results[bank['bank']]=replay
            elif complete:
                replay=p.contrast(raw,reference)
                if canonical(replay)!=canonical(case['contrast']) or replay['passed'] or case['passed']:raise ValueError('control rejection replay')
                results[bank['bank']]=replay
            records.append(dict(bank=bank['bank'],label=label,complete=complete,last_clock_s=float(t[-1]),
                                receipt_sha256=vco.sha(work/(label+'.json')),failure_report=failure))
        payloads[name]=dict(archive_sha256=vco.sha(archive),payload_sha256=hashlib.sha256(payload).hexdigest())
        print(bank['bank'],'replayed',flush=True)
    if len(records)!=5 or sum(x['complete'] for x in records)!=3:raise ValueError('bounded screen coverage')
    rejection=vco.read(ROOT/'evidence/voice_jfet_decomposed_adapter_rejection.json')
    if rejection['archive_sha256']!=payloads[ARCHIVES[0]]['archive_sha256'] or rejection['constant_control_measured'] or rejection['returned_bus_measured']:
        raise ValueError('unmeasured adapter rejection identity')
    failed=vco.read(ROOT/'evidence/voice_reset_test_rejection.json')
    snapshot=ROOT/'evidence/voice_reset_test_rejected_source.py'
    if vco.sha(snapshot)!=failed['source_sha256']['tests/test_vco_reset_screens.py']:raise ValueError('rejected test source snapshot')
    blob=subprocess.check_output(['git','show','b007a84:tools/voice_jfet_decomposed_probes.py'],cwd=ROOT)
    source_identity('tools/voice_jfet_decomposed_probes.py',failed['source_sha256']['tools/voice_jfet_decomposed_probes.py'],blob)
    documentary=vco.read(ROOT/'evidence/voice_reset_representation_sources.json')
    for item in documentary:
        if vco.sha(ROOT/item['path'])!=item['sha256']:raise ValueError('primary documentary source identity')
    unchanged=('evidence/vco1_laboratory_devices.json','evidence/vco1_ramp_graph.json','evidence/voice_board4_graph.json',
        'evidence/loudness_contour_graph.json','tools/vco1_circuit_reference.py','tools/voice_circuit_reference.py',
        'tools/loudness_voice_circuit.py','tools/loudness_board4_circuit.py')
    for name in unchanged:
        blob=subprocess.check_output(['git','show','c00c1c11c446898eabd02734b50c3a18e29e2826:'+name],cwd=ROOT)
        source_identity(name,vco.sha(ROOT/name),blob)
    report=dict(schema='rf-d/reset-representation-audit/v1',passed=True,coupling_admitted=False,regularizer_selected=None,
                new_solves=0,archives=payloads,records=records,replayed_measurements=results,source_byte_modes=sources,
                original_inputs_unchanged=unchanged,primary_source_manifest_sha256=vco.sha(ROOT/'evidence/voice_reset_representation_sources.json'),
                adapter_rejection_sha256=vco.sha(ROOT/'evidence/voice_jfet_decomposed_adapter_rejection.json'),
                failed_test_receipt_sha256=vco.sha(ROOT/'evidence/voice_reset_test_rejection.json'),
                failed_test_snapshot_sha256=vco.sha(snapshot),auditor_sha256=vco.sha(Path(__file__)),
                physical_fidelity=False,real_time=False,wall_s=time.perf_counter()-start)
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('audit passed; representation and regularization not admitted',flush=True)


if __name__=='__main__':main()
