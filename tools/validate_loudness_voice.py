"""Audit failed coupling screens and replay complete port pairs without solves."""
import gzip,hashlib,json,subprocess,time
from pathlib import Path
import numpy as np
import loudness_voice_probes as direct
import voice_port_relaxation as port
import vco1_circuit_reference as vco
from validate_loudness_board4_bank import source_identity

ROOT=vco.ROOT


def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':')).encode()


def main():
    output=ROOT/'evidence/loudness_voice_validation02.json'
    if output.exists():raise ValueError('preserve prior audit')
    start=time.perf_counter();checked={};source_modes={};summaries={};records=[]
    def audit_receipt(r,work,vectors):
        label=r['label'];path=work/(label+'.json')
        if canonical(vco.read(path))!=canonical(r):raise ValueError('archived/private receipt identity')
        if r['executable_sha256']!=vco.EXPECTED_EXE_SHA or vco.sha(Path(r['command'][0]))!=vco.EXPECTED_EXE_SHA:
            raise ValueError('executable identity')
        if r['source_sha256']!=r['source_sha256_after']:raise ValueError('source changed during solve')
        for name,digest in r['source_sha256'].items():
            key=(r['git_commit'],name,digest)
            if key in checked:continue
            if name.startswith('references-local/'):
                if name!='references-local/datasheets/ti_lm741_lm741.lib' or digest!='f58370983c8bd22bf6a59ddd05a1dd492f1a0ea60f673ffd460a356da5e693dc' or vco.sha(ROOT/name)!=digest:
                    raise ValueError('private model identity')
                mode='identified-private-file'
            else:
                blob=subprocess.check_output(['git','show',r['git_commit']+':'+name],cwd=ROOT)
                mode=source_identity(name,digest,blob)
            checked[key]=True;source_modes[name]=mode
        for ext,key in [('cir','deck_sha256'),('log','log_sha256')]:
            if vco.sha(work/(label+'.'+ext))!=r[key]:raise ValueError('private artifact identity')
        rawpath=work/(label+'.txt');raw=None
        if rawpath.exists():
            key='raw_export_sha256' if r['trajectory_complete'] else 'partial_export_sha256'
            if vco.sha(rawpath)!=r[key]:raise ValueError('export identity')
            raw=np.loadtxt(rawpath,skiprows=1,ndmin=2)
            if raw.shape[1]!=len(vectors)+1 or not np.isfinite(raw).all() or raw[0,0]!=0 or np.any(np.diff(raw[:,0])<=0):
                raise ValueError('export vectors, finiteness or clock')
        clock=r['scenario']['board']['oscillator']
        if r['trajectory_complete']:
            if raw is None or len(raw)!=r['rows'] or abs(raw[-1,0]-clock['duration_s'])>1e-14 or np.diff(raw[:,0]).max()>clock['max_step_s']*(1+1e-7):
                raise ValueError('complete export gate')
            if r.get('error'):raise ValueError('complete receipt with solver error')
        else:
            log=(work/(label+'.log')).read_text(encoding='utf-8')
            if 'Timestep too small' not in log or 'lab_e402-instance jq7_left' not in log or not r.get('error'):
                raise ValueError('expected preserved reset rejection')
            if raw is None or raw[-1,0]>=clock['duration_s']:raise ValueError('expected partial trajectory')
        records.append(dict(label=label,bank=work.name,complete=r['trajectory_complete'],
            receipt_sha256=vco.sha(path),last_clock_s=None if raw is None else float(raw[-1,0]),
            non_increasing_pwl_warning='non-increasing PWL' in (work/(label+'.log')).read_text(encoding='utf-8')))
        return raw

    archive=ROOT/'evidence/loudness_voice_screen01.json.gz';payload=gzip.decompress(archive.read_bytes());bank=json.loads(payload)
    if bank['passed'] or bank['gates']!=direct.GATES or set(bank['cases'])!=set(direct.scenes()):raise ValueError('direct rejection scope')
    work=ROOT/'references-local/voice-circuit'/bank['bank']
    for label,case in bank['cases'].items():
        raw=audit_receipt(case['receipt'],work,direct.scenes()[label].vectors)
        if not case.get('error') or case['last_clock_s']!=float(raw[-1,0]):raise ValueError('partial clock replay')
    summaries[archive.name]=dict(archive_sha256=vco.sha(archive),payload_sha256=hashlib.sha256(payload).hexdigest(),passed=False)

    pairs=[]
    archives=[ROOT/f'evidence/voice_port_relaxation{number:02d}.json.gz' for number in (1,2,3)]
    archives.append(ROOT/'evidence/voice_port_behavioral01.json.gz')
    for number,archive in enumerate(archives,start=1):
        payload=gzip.decompress(archive.read_bytes());bank=json.loads(payload)
        if bank['gates']!=port.GATES or bank['passed'] or set(bank['cases'])!={'fixed-contour-control'}:
            raise ValueError('bounded rejected control scope')
        work=ROOT/'references-local/voice-circuit'/bank['bank'];case=bank['cases']['fixed-contour-control']
        if case['passed'] or len(case['iterations'])>port.GATES['max_iterations']:raise ValueError('iteration budget or scope')
        for k in case['iterations']:
            raw={}
            for side in ('vco','board'):
                if side+'_receipt' not in k:continue
                r=k[side+'_receipt'];vectors=port.VCO_VECTORS if side=='vco' else port.BOARD_VECTORS
                raw[side]=audit_receipt(r,work,vectors)
            if 'closure' in k:
                replay=port.closure(raw['vco'],raw['board'],port.BOARD_VECTORS)
                if canonical(replay)!=canonical(k['closure']) or replay['passed']:raise ValueError('port defect replay')
                pairs.append(dict(bank=bank['bank'],iteration=k['iteration'],closure=replay))
        if number>=3:
            first=case['iterations'][0]['vco_receipt']
            blob=subprocess.check_output(['git','show',first['git_commit']+':tools/voice_port_probes.py'],cwd=ROOT)
            if hashlib.sha256(blob).hexdigest()!=bank['runner_sha256']:raise ValueError('frozen runner identity')
            if any(r['non_increasing_pwl_warning'] for r in records if r['bank']==bank['bank']):raise ValueError('terminal adapter still warns')
        summaries[archive.name]=dict(archive_sha256=vco.sha(archive),payload_sha256=hashlib.sha256(payload).hexdigest(),passed=False)
        print(bank['bank'],'audited',flush=True)
    immutable=['evidence/voice_board4_graph.json','evidence/loudness_contour_graph.json',
        'evidence/vco1_laboratory_devices.json','tools/vco1_circuit_reference.py',
        'tools/voice_circuit_reference.py','tools/filter_vca_circuit_reference.py','tools/loudness_board4_circuit.py']
    for name in immutable:
        old=subprocess.check_output(['git','show','5ce8b53203a0006cafd66edc4dd936703197bd38:'+name],cwd=ROOT)
        source_identity(name,vco.sha(ROOT/name),old)
    report=dict(schema='rf-d/loudness-voice-audit/v1',passed=True,coupling_admitted=False,
        new_solves=0,records=records,replayed_port_pairs=pairs,archives=summaries,
        source_byte_modes=source_modes,unchanged_electrical_inputs=immutable,
        physical_fidelity=False,real_time=False,auditor_sha256=vco.sha(Path(__file__)),wall_s=time.perf_counter()-start)
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('audit passed; coupling remains rejected;',len(records),'receipts',flush=True)


if __name__=='__main__':main()
