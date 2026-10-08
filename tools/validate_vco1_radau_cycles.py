"""Audit complete compressed cycles, stage/current roots and retained lineage."""
import base64,gzip,hashlib,json,re,subprocess,sys,tempfile
from decimal import Decimal,localcontext
from pathlib import Path
import numpy as np
import wave
import render_vco1_radau as listening
import vco1_radau_conformance as conformance
import vco1_radau_cycles_recovery as cycles
from validate_mixer_on_native import native_source_identity
ROOT=cycles.ROOT;sha=cycles.sha
OUT='evidence/voice_vco1_radau_cycles_tests01.json'
PREVIOUS='evidence/voice_vco1_radau_tests01.json'

def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def require(ok,msg):
    if not ok:raise ValueError(msg)
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'))

def codec_check():
    # Bitwise identity: no arithmetic on floats, including NaN payloads/subnormals.
    rng=np.random.default_rng(1065);a=rng.integers(0,2**64-1,size=(1025,cycles.trace.COLS),dtype=np.uint64)
    a[:8,0]=[0,2**63,1,2**63+1,0x7ff0000000000000,0xfff0000000000000,0x7ff8000000000106,15728640000]
    with tempfile.TemporaryDirectory(prefix='rf-d-radau-codec-') as directory:
        p=Path(directory)/'vectors.gz'
        with gzip.open(p,'wb') as f:
            for i in range(0,len(a),512):f.write(cycles.trace.encode_block(a[i:i+512].astype('<u8',copy=False).tobytes()))
        decoded=b''.join(b.tobytes() for b in cycles.trace.blocks(p))
        require(decoded==a.astype('<u8',copy=False).tobytes(),'codec arbitrary payload exact bytes')
        with gzip.open(p,'wb') as f:f.write(b'\x01\x00\x00\x00'+bytes(cycles.trace.COLS*8-1))
        try:list(cycles.trace.blocks(p))
        except ValueError:pass
        else:raise ValueError('codec accepted truncated block')
        try:cycles.trace.encode_block(b'x')
        except ValueError:pass
        else:raise ValueError('codec accepted partial row')
    return dict(rows=1025,columns=546,arbitrary_payload_exact=True,truncated_block_rejected=True,partial_row_rejected=True)

def audit():
    old=read(PREVIOUS);snapshot=read('evidence/voice_vco1_radau_cycles_documentation01.json');repair=read('evidence/voice_vco1_radau_cycles_repair01.json');failed=read(repair['failure_receipt']);interrupted=read('evidence/voice_vco1_radau_cycles02.json');resource=read('evidence/voice_vco1_radau_cycles_resource01.json');extension=read('evidence/voice_vco1_radau_cycles_extension01.json');rejected=read('evidence/voice_vco1_radau_cycles03.json');probe=read('evidence/voice_vco1_radau_newton01.json');bank=read('evidence/voice_vco1_radau_cycles04.json')
    prev={n:base64.b64decode(v) for n,v in snapshot['previous_bytes_base64'].items()};original={n:base64.b64decode(v) for n,v in repair['original_bytes_base64'].items()}
    require(old['passed'] and sha(ROOT/PREVIOUS)==snapshot['previous_qa_sha256'],'prior release identity')
    for n,h in old['source_sha256'].items():require(hashlib.sha256(prev[n] if n in prev else (ROOT/n).read_bytes()).hexdigest()==h,'protected source '+n)
    require(sha(ROOT/repair['failure_receipt'])==repair['failure_sha256'] and not failed['passed'] and len(failed['commands'])==1 and len(failed['unchanged_replays'])==1 and not failed['profiles'],'compile original/replay only')
    require(all(x['exit_code']!=0 and 'float literals must have an integer part' in x['stderr'] for x in failed['commands']+failed['unchanged_replays']),'compile failure cause')
    require((ROOT/'tools/vco1_radau_cycles_runner.rs').read_bytes()==original['tools/vco1_radau_cycles_runner.rs'].replace(b'(.03/TICK)',b'(0.03/TICK)'),'only literal repair')
    require((ROOT/'tools/vco1_radau_cycles.py').read_bytes()==original['tools/vco1_radau_cycles.py'].replace(b'voice_vco1_radau_cycles01.json',b'voice_vco1_radau_cycles02.json').replace(b'vco1-radau-cycles01',b'vco1-radau-cycles02'),'only fresh receipt/work repair')
    private=dict(old['private_input_sha256'])
    require(not interrupted['passed'] and interrupted['error']=="ValueError('partial native row')" and len(interrupted['commands'])==1 and interrupted['commands'][0]['exit_code']==0 and not interrupted['profiles'],'administrative interruption and adapter tail rejection')
    require(sha(ROOT/'evidence/voice_vco1_radau_cycles02.json')==resource['original_receipt_sha256']==extension['original_bank_sha256'] and not resource['native_replay_dispatched'] and not resource['unencoded_partial_tail_recoverable'] and not resource['physics_changed'] and not resource['gates_changed'],'resource provenance/tail limitation')
    for n,v in extension['original_bytes_base64'].items():require((ROOT/n).read_bytes()==base64.b64decode(v),'measured interrupted source retained')
    for record in (failed,interrupted,rejected,probe,bank):
        require(record['source_sha256']==record['source_sha256_after'] and record['private_input_sha256']==record['private_input_sha256_after'],'campaign source identity')
        for n,h in record['source_sha256'].items():
            b=original[n] if record is failed and n in original else prev[n] if n in prev else (ROOT/n).read_bytes()
            require(hashlib.sha256(b).hexdigest()==h,'recoverable campaign source '+n)
        private.update(record['private_input_sha256'])
        for v in record['outputs']:require(sha(ROOT/v['path'])==v['sha256'] and (ROOT/v['path']).stat().st_size==v['bytes'],'retained native output');private[v['path']]=v['sha256']
    require(bank['passed'] and bank['resource_passed'] and bank['gates']==cycles.GATES and not bank['unchanged_replays'] and len(bank['profiles'])==2 and all(c['exit_code']==0 and not c['resource_rejection'] for c in bank['commands']),'complete bank and commands')
    require(sha(Path(bank['compiler']['path']))==bank['compiler']['sha256'] and bank['lab_stack_bytes']==8388608 and bank['process_budget_s']==2400 and bank['reserve_bytes']==1024**3,'compiler/resources')
    require('opt-level=2' in bank['commands'][0]['command'] and 'link-arg=-Wl,--stack,8388608' in bank['commands'][0]['command'],'measured build flags')
    require(not rejected['passed'] and rejected['profiles'][0]['complete'] and not rejected['profiles'][1]['complete'] and 'nonlinear:LineSearch' in rejected['commands'][-1]['stderr'] and rejected['commands'][-1]['exit_code']!=0 and not rejected['commands'][-1]['resource_rejection'],'original nonlinear125 rejection retained')
    require(bank['inherited_250_profile'] and bank['inherited_250_receipt_sha256']==sha(ROOT/'evidence/voice_vco1_radau_cycles03.json') and canonical(bank['profiles'][0])==canonical(rejected['profiles'][0]),'completed250 inherited without rerun')
    adapters=read('evidence/voice_vco1_radau_adapters_snapshot01.json')
    for n,v in adapters['previous_bytes_base64'].items():
        b=base64.b64decode(v);expected=b.replace(b'voice_vco1_radau_cycles03.json',b'voice_vco1_radau_cycles04.json') if n.startswith('tools/') else b
        require((ROOT/n).read_bytes()==expected,'planned adapter bank target only')
    original_kernel=(ROOT/'tools/vco1_radau_kernel.rs').read_bytes();residual_kernel=original_kernel.replace(b'next<ratio*(1.-1e-4*alpha)',b'merit(&t.residual)<norm*(1.-1e-4*alpha)')
    require((ROOT/'tools/vco1_radau_residual_kernel.rs').read_bytes()==residual_kernel,'only line-search merit changed')
    diagnostic_stage_comparisons=0;diagnostic_identities=0;diagnostic_stages=0;diagnostic_points={};all_points={}
    require(probe['passed'] and probe['elapsed_ticks']==6381419552 and probe['original_rows']==109373 and len(probe['methods'])==3 and len(probe['independent'])==3 and not probe['production_kernel_changed'],'local root probe admission')
    with localcontext() as ctx:
        ctx.prec=100;inv=cycles.ports.ref.circuit.inventory(cycles.ports.ref.circuit.scenario(cycles.ports.C));history=cycles.ports.packed(probe['previous_high'],probe['previous_low'])
        for method in probe['methods']:
            commands=method['commands'];require(len(commands)==3 and all(c['exit_code']==0 for c in commands) and commands[1]['stdout']==commands[2]['stdout'] and commands[1]['stderr']==commands[2]['stderr'],'unchanged local replay')
            folder=ROOT/'references-local/vco1-radau-newton01'/method['method'];actual=(folder/'radau.rs').read_bytes()
            expected=original_kernel if method['method']=='original' else residual_kernel if method['method']=='residual' else original_kernel.replace(b'let ratio=correction(&d);',b'let ratio=correction(&d);eprintln!("NEWTON,iteration={iteration},norm={norm:.17e},correction={ratio:.17e}");').replace(b'let next=correction(&dd);',b'let next=correction(&dd);eprintln!("TRIAL,power={power},norm={:.17e},correction={next:.17e}",merit(&t.residual));')
            require(actual==expected and sha(folder/'radau.rs')==method['kernel_sha256'],'diagnostic kernel exact bytes')
            parsed={};rejects=[]
            for line in commands[1]['stdout'].splitlines():
                w=line.split(',')
                if w[0]=='REJECT':rejects.append(dict(label=w[1],error=w[2]))
                elif w[0]=='ROOT':parsed.setdefault(w[1],{})[w[2]]=dict(high=list(map(float,w[5:139])),low=list(map(float,w[139:])),residual_ratio=float(w[3]),correction_ratio=float(w[4]))
            require(canonical(parsed)==canonical(method['roots']) and rejects==method['rejections'],'diagnostic root provenance')
        for item,ticks in zip(probe['independent'],(8,16,32)):
            require(item['full_ticks']==ticks and item['local_error_admitted'],'local grid gates');steps=item['steps'];checked=[]
            for label in ('full','mid','end'):
                step=steps[label];oldstep=list(map(Decimal,steps['mid']['roots']['endpoint']['independent_decimal'])) if label=='end' else history
                require(step['previous_decimal']==list(map(str,oldstep)) and step['dt_s']==ticks*cycles.TICK/(1 if label=='full' else 2),'independent diagnostic history/time')
                key=canonical(dict(previous=list(map(str,oldstep)),dt_s=step['dt_s']));value=canonical({p:step['roots'][p]['independent_decimal'] for p in ('stage','endpoint')})
                if key in diagnostic_points:require(diagnostic_points[key]==value,'identical repeated discrete problem roots')
                diagnostic_points[key]=value;all_points[key]=value
                for method in probe['methods']:
                    native=method['roots'].get(f'{ticks}/{label}')
                    if native:
                        pair={part:dict(step['roots'][part],native=native[part]) for part in ('stage','endpoint')};rows=cycles.ports.check(pair,oldstep,step['dt_s'],inv);checked.append(dict(method=method['method'],label=label,ports=rows));diagnostic_stage_comparisons+=2;diagnostic_identities+=4
                diagnostic_stages+=2
            full=list(map(Decimal,steps['full']['roots']['endpoint']['independent_decimal']));end=list(map(Decimal,steps['end']['roots']['endpoint']['independent_decimal']));error=max(abs(a-b)/Decimal.from_float(2e-6 if k<98 else 2e-9) for k,(a,b) in enumerate(zip(full,end)))
            require(str(error)==item['independent_error_ratio'] and error<=1 and canonical(checked)==canonical(item['native_comparisons']),'same discrete roots and local error')
    require(diagnostic_stages==18 and diagnostic_stage_comparisons==42 and diagnostic_identities==84 and 2*len(diagnostic_points)==14,'diagnostic counts and unique equation problems')
    for n in ('fine.rs','linear.rs','vco1_stamp_data.rs'):
        require(sha(ROOT/'references-local/vco1-radau-cycles04'/n)==sha(ROOT/'references-local/vco1-reset-grid02'/n),'unchanged physical/linear modules')
    require(sha(ROOT/'references-local/vco1-radau-cycles04/radau.rs')==sha(ROOT/'tools/vco1_radau_residual_kernel.rs') and sha(ROOT/'references-local/vco1-radau-cycles04/runner.rs')==sha(ROOT/'tools/vco1_radau_cycles_resume_runner.rs'),'measured kernel/runner')
    roots=0;currents=0;inv=cycles.ports.ref.circuit.inventory(cycles.ports.ref.circuit.scenario(cycles.ports.C))
    with localcontext() as ctx:
        ctx.prec=100
        for profile,maximum,command in zip(bank['profiles'],(131072,65536),(rejected['commands'][1],bank['commands'][1])):
            require(profile['complete'] and profile['maximum_accepted_half_ticks']==maximum,'two nominal fine profiles')
            entries=[dict(path=ROOT/e['path'],skip_rows=e['skip_rows'],take_rows=e['take_rows']) for e in profile['segments']]
            coverage,first,selected,m=cycles.joined.summary(entries,maximum)
            digest=hashlib.sha256();size=0;rows=0;echo=None;nextrow=None
            for block in cycles.trace.blocks(ROOT/profile['export']['path']):
                digest.update(block.tobytes());size+=block.nbytes;rows+=len(block)
                if echo is None:echo=block[0].copy();nextrow=block[1].copy() if len(block)>1 else None
            require(digest.hexdigest()==command['native_stream_sha256'] and size==command['native_stream_bytes'] and canonical(dict(uncompressed_sha256=digest.hexdigest(),uncompressed_bytes=size,rows=rows))==canonical(profile['new_native_stream']),'all new native stdout bytes verified')
            if maximum in (131072,65536):
                prefix=(rejected if maximum==131072 else bank)['preserved_prefix'];original_rows=0;tail=[]
                for block in cycles.trace.blocks(ROOT/prefix['path']):original_rows+=len(block);tail.extend(block[-2:].copy());tail=tail[-2:]
                take=original_rows if original_rows%2 else original_rows-1;oldrow=tail[-1] if take==original_rows else tail[-2];extra=tail[-1] if take<original_rows else None
                half=int(oldrow[1]);proposal=min(4*half,2*maximum) if oldrow[4]<=.25 else 2*half
                require(take==prefix['take_rows'] and original_rows==prefix['original_rows'] and (maximum!=131072 or original_rows==resource['surviving_rows']) and oldrow[0]==prefix['last_clock_ticks'] and proposal==prefix['proposal_ticks'],'complete pair checkpoint clock/controller')
                require(sha(ROOT/prefix['path'])==prefix['sha256'] and (maximum!=131072 or prefix['sha256']==resource['original_export_sha256']) and sha(ROOT/prefix['checkpoint_path'])==prefix['checkpoint_sha256'],'checkpoint source bytes')
                packed=list(map(float,(ROOT/prefix['checkpoint_path']).read_text().split()));require(np.array_equal(oldrow[6:274],packed) and np.array_equal(echo[6:274],packed) and echo[0]==oldrow[0] and profile['checkpoint_echo_verified'],'echo full state/low')
                require(extra is None or nextrow is not None and extra.tobytes()==nextrow.tobytes(),'extra surviving endpoint exact byte overlap')
                require(profile['overlap_additional_row_byte_equal'] and profile['segments'][0]['skip_rows']==0 and profile['segments'][0]['take_rows']==take and profile['segments'][1]['skip_rows']==1,'logical splice echo excluded')
            require(canonical(coverage)==canonical(profile['coverage']) and canonical(m)==canonical(profile['measurements']),'full trace measurements rederived')
            require(abs(coverage['elapsed_s']-.03)<1e-17,'complete logical duration')
            own=profile['startup_identity'];startup=read(own['path']);nominal=next(x for x in startup['cases'] if x['profile']==0 and x['scene']==0)
            require(startup['passed'] and sha(ROOT/own['path'])==own['sha256'] and np.array_equal(first[6:140],nominal['native_root']) and np.array_equal(first[6:140],own['initial_high']) and np.array_equal(first[140:274],own['initial_low']),'same own root with protected independent contrast')
            require(sorted(selected)==[i['row_index'] for i in profile['actual_intervals']],'selected actual intervals')
            for item in profile['actual_intervals']:
                previous,now=selected[item['row_index']];h=float(now[1]*cycles.TICK);history=cycles.ports.packed(previous[6:140],previous[140:274]);pair=item['roots']
                require(h==item['dt_s'] and item['previous_high']==previous[6:140].tolist() and item['previous_low']==previous[140:274].tolist(),'actual incoming state')
                for part,col in (('stage',274),('endpoint',6)):
                    n=pair[part]['native'];require(n['high']==now[col:col+134].tolist() and n['low']==now[col+134:col+268].tolist() and n['residual_ratio']==now[2] and n['correction_ratio']==now[3],'actual native stage')
                checked=cycles.ports.check(pair,history,h,inv);require(canonical(checked)==canonical(item['ports']),'independent retained root reevaluation')
                key=canonical(dict(previous=list(map(str,history)),dt_s=h));value=canonical({p:pair[p]['independent_decimal'] for p in ('stage','endpoint')})
                if key in all_points:require(all_points[key]==value,'repeated actual equation roots identical')
                all_points[key]=value
                stages=[list(map(Decimal,pair[p]['independent_decimal'])) for p in ('stage','endpoint')];cur=cycles.terminal_currents(stages,history,h);errors=[abs(v-Decimal.from_float(float(w))) for v,w in zip(cur,now[542:545])]
                panel=(stages[1][46]-stages[1][39])/Decimal.from_float(12500.);panelerror=abs(panel-Decimal.from_float(float(now[545])))
                require(list(map(str,cur))==item['independent_currents_a'] and now[542:546].tolist()==item['native_currents_a'] and str(max(errors))==item['max_current_error_a'] and str(panelerror)==item['panel_error_a'] and max(errors)<=Decimal.from_float(2e-10) and panelerror<=Decimal.from_float(2e-10),'Radau current formula/independent terminals')
                roots+=2;currents+=4
            require(m['period_spread_relative']<=cycles.GATES['period_spread_relative'] and m['cycle_charge_check']['relative_imbalance']<=cycles.GATES['cycle_charge_relative'],'fixed periodicity/current gates')
    comparison=cycles.comparison(*[p['measurements'] for p in bank['profiles']]);require(canonical(comparison)==canonical(bank['comparison']) and comparison['frequency_error_cents']<=cycles.GATES['frequency_refinement_cents'] and max(comparison['output_extrema_error_v'].values())<=cycles.GATES['output_extrema_refinement_v'],'fine refinement')
    expected=(ROOT/'tools/vco1_radau_cycles_runner.rs').read_text().replace('let mut old=State::from_nodes(initial.nodes);let mut elapsed=0_u64;', '''let mut old=State::from_nodes(initial.nodes);let mut elapsed=0_u64;
 if args.len()==5 {let content=std::fs::read_to_string(&args[2])?;let a:Vec<f64>=content.split_whitespace().map(str::parse).collect::<Result<_,_>>()?;if a.len()!=2*N {return Err("checkpoint shape".into());}old=State{high:a[..N].try_into()?,low:a[N..].try_into()?};elapsed=args[3].parse()?;eprintln!("RESUME,ticks={elapsed}");}else if args.len()!=2 {return Err("arguments".into());}
''').replace('let mut proposal=2*maximum;', 'let mut proposal=if args.len()==5 {args[4].parse()?} else {2*maximum};if proposal<8||proposal>2*maximum||!proposal.is_power_of_two()||elapsed>=limit {return Err("checkpoint clock/proposal".into());}').replace('for v in [0.;6].into_iter()', 'for v in [elapsed as f64,0.,0.,0.,0.,0.].into_iter()')
    require(expected==(ROOT/'tools/vco1_radau_cycles_resume_runner.rs').read_text(),'only state/clock/controller checkpoint adapter added')
    require((ROOT/'.gitattributes').read_bytes()==prev['.gitattributes']+b'/tools/vco1_radau_cycles_runner.rs text eol=lf\n/tools/vco1_radau_cycles_resume_runner.rs text eol=lf\n/tools/vco1_radau_failure_runner.rs text eol=lf\n/tools/vco1_radau_residual_kernel.rs text eol=lf\n','explicit new Rust LF policy only')
    c=read('evidence/voice_vco1_radau_conformance01.json')
    require(c['passed'] and c['source_sha256']==c['source_sha256_after'] and c['gates']==cycles.GATES and c['new_spice_processes']==0 and c['new_native_trajectories']==0 and not c['new_audio'],'archived method conformance receipt')
    for n,h in c['source_sha256'].items():require(sha(ROOT/n)==h,'conformance source '+n)
    archived=json.load(gzip.open(ROOT/'evidence/vco1_circuit_convergence_v1.json.gz','rt'))
    require(canonical(conformance.calculate(bank,archived,read('evidence/vco1_circuit_validation.json')))==canonical(c['comparisons']),'four method observables comparisons independently rederived')
    audio=read('evidence/voice_vco1_radau_listening01.json')
    require(audio['passed'] and audio['source_sha256']==audio['source_sha256_after'] and audio['simulated_circuit_s']==.03 and audio['periodic_cycle_repeated'] and not audio['full_duration_circuit_render'] and not audio['full_voice'] and not audio['physical_fidelity'] and not audio['real_time'] and audio['new_native_trajectories']==audio['new_spice_processes']==0,'scoped native listening')
    for n,h in audio['source_sha256'].items():require(sha(ROOT/n)==h,'listening source '+n)
    profile=bank['profiles'][1];phase,voltage,window=listening.signals(profile);frequency=1/(window[1]-window[0]);rate=48000;harmonics=int(np.floor(.45*rate/frequency));parts=[]
    require(audio['source_logical_sha256']==profile['coverage']['uncompressed_sha256'] and audio['source_segments']==profile['segments'] and audio['window_s']==list(window) and audio['knots']==len(phase) and audio['frequency_hz']==frequency and audio['sample_rate_hz']==rate and audio['harmonics']==harmonics and audio['volts_per_full_scale']==8. and audio['fade_s']==.01,'audio actual cycle/scale')
    for i,name in enumerate(('sierra','triangulo','pulso')):
        c=listening.coefficients(phase,voltage[:,i],harmonics);signal=listening.synthesize(c,frequency,rate);parts.append(signal);f=audio['files'][name];path=ROOT/f['path']
        require(canonical([[float(v.real),float(v.imag)] for v in c])==canonical(audio['coefficients'][name]) and float(c[0].real)==audio['removed_dc_v'][name] and float(np.max(np.abs(signal)))==f['peak'] and f['peak']<1 and float(np.sqrt(np.mean(signal**2)))==f['rms'],'audio coefficients/DC/peak')
        with wave.open(str(path),'rb') as w:require(w.getnchannels()==1 and w.getsampwidth()==2 and w.getframerate()==rate and w.getnframes()==len(signal)==f['frames'] and w.readframes(w.getnframes())==np.rint(signal*32767).astype('<i2').tobytes(),'WAV exact regenerated PCM')
    montage=np.concatenate([parts[0],np.zeros(int(.15*rate)),parts[1],np.zeros(int(.15*rate)),parts[2]]);f=audio['files']['montaje']
    with wave.open(str(ROOT/f['path']),'rb') as w:require(w.getnchannels()==1 and w.getsampwidth()==2 and w.getframerate()==rate and w.getnframes()==len(montage)==f['frames'] and w.readframes(w.getnframes())==np.rint(montage*32767).astype('<i2').tobytes() and f['duration_s']==2.55,'montage payload/duration')
    for f in audio['files'].values():require(sha(ROOT/f['path'])==f['sha256'] and (ROOT/f['path']).stat().st_size==f['bytes'],'private audio hash');private[f['path']]=f['sha256']
    codec=codec_check()
    for n,h in private.items():require(sha(ROOT/n)==h,'protected private input '+n)
    staged=subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=ROOT).decode().split('\0');names=sorted(set(old['source_sha256'])|{PREVIOUS}|{n for n in staged if n and n!=OUT});sources={n:sha(ROOT/n) for n in names}
    for n,h in sources.items():native_source_identity(n,h,subprocess.check_output(['git','show',':'+n],cwd=ROOT))
    for n in ('README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md','docs/VCO1_RADAU_CICLOS_PROTOCOLO.md','docs/VCO1_RADAU_CICLOS_EXTENSION_PROTOCOLO.md','docs/VCO1_RADAU_CICLOS_RESULTADOS.md'):
        p=ROOT/n
        for link in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf8')):
            if link.startswith(('http:','https:','#')):continue
            target=(p.parent/link.split('#')[0]).resolve();require(target==ROOT/OUT or target.exists(),'documentation target '+link)
    return dict(schema='rf-d/radau-own-started-cycles-release/v1',passed=True,base_commit='4efd8b88bb3f150388d75e9861ab07e6d9df4ca3',previous_qa_sha256=sha(ROOT/PREVIOUS),source_sha256=sources,source_sha256_after=sources,private_input_sha256=private,covered_test_count=235,inherited_test_count=235,native_test_count=0,inherited_tests_reexecuted=False,independent_stage_root_comparisons=roots,publication_stage_roots_reevaluated=roots,common_mode_identities=roots*2,diagnostic_independent_stage_roots=diagnostic_stages,diagnostic_native_stage_comparisons=diagnostic_stage_comparisons,diagnostic_port_identities=diagnostic_identities,diagnostic_counts_include_instrumented_repetitions=True,replay_native_roots_not_double_counted=True,diagnostic_unique_stage_roots=2*len(diagnostic_points),all_unique_stage_roots=2*len(all_points),terminal_current_comparisons=currents,codec=codec,own_started_radau_admitted=True,native_full_period_admitted=True,native_frequency_refinement_admitted=True,production_kernel_changed=False,new_spice_processes=0,new_audio=True,new_audio_scope="Native nominal VCO cycle repeated; no filter/VCA or full-duration circuit render",physical_fidelity=False,real_time=False,new_method_heap_measured=False,lab_stack_bytes=8388608,c4_pf=10,calibrated_transient_admitted=False,active_mixer_admitted=False,archived_spice_observable_conformance=True,archived_method_comparisons=4,previous_audio=old['previous_audio'],native_listening=audio['files'],official_executable_sha256=old['official_executable_sha256'],long_note_admitted_locally=False)

def main():
    out=ROOT/OUT;require(not out.exists(),'preserve QA attempt');r=dict(schema='rf-d/radau-own-started-cycles-release/v1',passed=False)
    out.write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n')
    try:r=audit()
    except Exception as e:r['error']=repr(e)
    out.write_text(json.dumps(r,indent=2)+'\n',encoding='utf8',newline='\n')
    print('Radau cycle release',r['passed'],r.get('error',''),len(r.get('source_sha256',{})),len(r.get('private_input_sha256',{})),flush=True)
    if not r['passed']:sys.exit(1)

if __name__=='__main__':main()
