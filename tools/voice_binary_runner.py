"""Same build11 and physical decks; dual short control or binary long export."""
import difflib,json,os,subprocess,time
from dataclasses import asdict
from pathlib import Path
import numpy as np
import voice_six_runner as six
import voice_six_build as build
import voice_full_note as note
import voice_native_raw as native
import vco1_circuit_reference as vco

ROOT=vco.ROOT;CONTROL=ROOT/'references-local/voice-circuit/native-export-control01'
LONG=ROOT/'references-local/voice-circuit/active-six-binary-long01'
PROTOCOL='docs/VOZ_NOTA_LARGA_EXPORT_BINARIO_PROTOCOLO.md'
WRITERS={'src/frontend/rawfile.c':'fa5d8625a5b4168d4f928af455f685a9a7edb0ef7999af2f18853e8bf5216840',
         'src/frontend/postcoms.c':'60bcc3b4bd6e2cc4203dc8bd4f3185b27d1376e321613ce89f6c84ee1887901c'}

def write(path,value):path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8',newline='\n')

def source(name):
    bankp=ROOT/'evidence/voice_six_short_runs01.json';auditp=ROOT/'evidence/voice_six_short_validation01.json'
    bank=vco.read(bankp);audit=vco.read(auditp)
    if not audit['passed'] or not audit['joint_admitted_locally'] or audit['bank_sha256']!=vco.sha(bankp):raise ValueError('audited six short bank required')
    for scope in (bank['wrapper_sha256'],audit['analysis_source_sha256']):
        for n,h in scope.items():
            if vco.sha(ROOT/n)!=h:raise ValueError('short measured helper changed')
    label='joint-'+name;r=bank['records'][label];p=six.WORK/(label+'.json')
    if six.canonical(r)!=six.canonical(vco.read(p)) or not r['trajectory_complete']:raise ValueError('complete short receipt required')
    for ext,key in (('cir','deck_sha256'),('txt','raw_export_sha256'),('log','log_sha256')):
        if vco.sha(p.with_suffix('.'+ext))!=r[key]:raise ValueError('short artifact identity')
    for n,h in r['current_source_sha256'].items():
        if vco.sha(ROOT/n)!=h:raise ValueError('physical source changed')
    if six.canonical(r['scenario'])!=six.canonical(asdict(note.short.scenes()[name])):raise ValueError('fixed short scene')
    for n,h in WRITERS.items():
        if vco.sha(build.TREE/n)!=h:raise ValueError('native writer source changed')
    return r,p

def patch(old,name,old_export,ascii_export,binary_export,long_mode=False):
    temporal=None;base=old
    if long_mode:base,temporal=note.patch(old,name,old_export,ascii_export)
    else:
        marker=('wrdata '+old_export+' ').encode()
        if old.count(marker)!=1:raise ValueError('unique original export anchor required')
        base=old.replace(marker,('wrdata '+ascii_export+' ').encode(),1)
    lines=[s for s in base.splitlines(True) if s.startswith(('wrdata '+ascii_export+' ').encode())]
    if len(lines)!=1:raise ValueError('unique full export line required')
    line=lines[0];vectors=' '.join(note.short.scenes()[name].vectors)
    expected=('wrdata '+ascii_export+' '+vectors+'\n').encode()
    if line!=expected:raise ValueError('exact frozen export vector order required')
    addition=('set filetype=binary\nwrite '+binary_export+' '+vectors+'\n').encode()
    replacement=addition if long_mode else line+addition
    result=base.replace(line,replacement,1)
    if result.replace(replacement,line,1)!=base:raise ValueError('reversible export-only patch required')
    return result,dict(temporal_patch=temporal,export_before=line.decode(),export_after=replacement.decode(),
        diff=''.join(difflib.unified_diff(old.decode().splitlines(True),result.decode().splitlines(True),n=0)),
        dual_export=not long_mode,electrical_changes=False)

def runtime():
    paths=[build.WORK/'init02/spinit',build.WORK/'baseline02/src/xspice/icm/spice2poly/spice2poly.cm',
        Path('C:/msys64/ucrt64/bin/libwinpthread-1.dll'),Path('C:/msys64/ucrt64/bin/libstdc++-6.dll'),Path('C:/msys64/ucrt64/bin/libgcc_s_seh-1.dll')]
    return {(p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT) else p.as_posix()):vco.sha(p) for p in paths}

def helper_hashes():
    paths=[Path(__file__),Path(native.__file__),Path(six.__file__),Path(build.__file__),Path(note.__file__),Path(vco.__file__),Path(note.short.__file__),Path(note.short.c.__file__)]
    return {p.relative_to(ROOT).as_posix():vco.sha(p) for p in paths}

def run(name='nominal500',long_mode=False):
    if long_mode:
        a=ROOT/'evidence/voice_native_control_validation01.json';c=ROOT/'evidence/voice_native_control01.json'
        proof=vco.read(a)
        if not proof['passed'] or not proof['control_admitted'] or proof['control_sha256']!=vco.sha(c):raise ValueError('admitted native control audit required')
    work=LONG if long_mode else CONTROL;work.mkdir(parents=True,exist_ok=True)
    paths={ext:work/(name+'.'+ext) for ext in ('cir','txt','raw','log','json')}
    if any(p.exists() for p in paths.values()):raise ValueError('preserve native run')
    old,receipt=source(name);compiled,exe=six.candidate()
    deck,changes=patch(receipt.with_suffix('.cir').read_bytes(),name,receipt.with_suffix('.txt').as_posix(),paths['txt'].as_posix(),paths['raw'].as_posix(),long_mode)
    paths['cir'].write_bytes(deck);s=note.scenes()[name] if long_mode else note.short.scenes()[name]
    env=os.environ.copy()
    for flag in six.FLAGS:env.pop(flag,None)
    env['RF_D_LINEAR_REFINE']='1';env['PATH']='C:/msys64/ucrt64/bin;'+env['PATH'];env['SPICE_SCRIPTS']=(build.WORK/'init02').as_posix()
    budget=7200 if long_mode else 900
    before=helper_hashes();physical=old['current_source_sha256'];libraries=runtime()
    compiled_sources={n:vco.sha(build.TREE/n) for n in (build.NAME,*WRITERS)}
    r=dict(schema='rf-d/native-export-run/v1',scene=name,long_mode=long_mode,scenario=asdict(s),vectors=list(s.vectors),patch=changes,
        short_receipt_path=receipt.relative_to(ROOT).as_posix(),short_receipt_sha256=vco.sha(receipt),
        short_bank_sha256=vco.sha(ROOT/'evidence/voice_six_short_runs01.json'),short_audit_sha256=vco.sha(ROOT/'evidence/voice_six_short_validation01.json'),
        original_deck_sha256=vco.sha(receipt.with_suffix('.cir')),current_source_sha256=physical,helper_sha256=before,runtime_sha256=libraries,
        compiled_source_sha256=compiled_sources,executable_path=exe.relative_to(ROOT).as_posix(),executable_sha256=vco.sha(exe),
        build_sha256=vco.sha(build.WORK/'build.json'),protocol_sha256=vco.sha(ROOT/PROTOCOL),deck_sha256=vco.sha(paths['cir']),
        command=[str(exe),'-n','-b',str(paths['cir'])],controlled_environment={f:env.get(f) for f in six.FLAGS},
        published_corrections=6,wall_limit_s=budget,process_started=False,trajectory_complete=False,
        git_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),physical_fidelity=False,real_time=False,new_audio=False)
    if long_mode:r['control_audit_sha256']=vco.sha(a)
    start=time.perf_counter()
    try:
        with paths['log'].open('wb') as stream:
            process=subprocess.Popen(r['command'],cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
            r['process_started']=True
            try:r['exit_code']=process.wait(timeout=budget)
            except subprocess.TimeoutExpired:process.kill();r.update(timeout=True,exit_code=process.wait())
    except OSError as e:r['launch_error']=str(e)
    finally:
        r.update(wall_s=time.perf_counter()-start,helper_sha256_after=helper_hashes(),runtime_sha256_after=runtime(),
            current_source_sha256_after={n:vco.sha(ROOT/n) for n in physical},compiled_source_sha256_after={n:vco.sha(build.TREE/n) for n in compiled_sources},
            executable_sha256_after=vco.sha(exe),log_sha256=vco.sha(paths['log']))
        r.update(six.log_status(paths['log'].read_text(encoding='utf-8',errors='replace'),True))
        for ext in ('txt','raw'):
            if paths[ext].exists():r[ext+'_sha256']=vco.sha(paths[ext]);r[ext+'_bytes']=paths[ext].stat().st_size
        try:
            raw,layout=native.read(paths['raw'],s.vectors);r['native_layout']=layout
            r.update(six.clock_info(raw,s.vectors,s.oscillator.duration_s,s.oscillator.max_step_s))
        except Exception as e:r['export_error']=str(e)
        r['trajectory_complete']=bool(r.get('endpoint_complete') and r.get('max_step_passed') and r['activation_gate_passed'] and not r.get('timeout') and not r.get('launch_error') and r.get('exit_code')==0)
        if before!=r['helper_sha256_after'] or physical!=r['current_source_sha256_after'] or libraries!=r['runtime_sha256_after'] or compiled_sources!=r['compiled_source_sha256_after'] or r['executable_sha256']!=r['executable_sha256_after']:raise ValueError('native solve inputs changed')
        write(paths['json'],r)
    print(name,'native complete:',r['trajectory_complete'],'last:',r.get('last_clock_s'),'wall:',round(r['wall_s'],2),flush=True)
    return r
