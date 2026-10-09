"""Analyze admitted records; join only exact checkpoint continuation seams."""
import argparse,json,re,traceback
from pathlib import Path
from decimal import Decimal,localcontext
import numpy as np
from prepare_vco1_portable import ROOT,sha
from joint_cycles_analysis import trace,checkpoint,checkpoints,reset_measurements,compare,require,ANCHOR,GOAL,TICK
def summary(text):
    match=re.search(r'^SUMMARY,(.+)$',text,re.M);require(match is not None,'native summary')
    return {k:float(v) for k,v in (part.split('=') for part in match[1].split(','))}
def records(native,extension=None):
    groups={65536:[],32768:[]}
    for p in native['profiles']:groups[p['maximum_half_ticks']].append(p)
    if extension:
        for p in extension['profiles']:groups[p['maximum_half_ticks']].append(p)
    return groups
def analyze(native,extension=None):
    groups=records(native,extension);result=[];anchors=[];paths=set()
    for maximum,parts in groups.items():
        require(parts,'profile present');pieces=[];cps=[];charge=Decimal(0);absolute=Decimal(0);restores=0;previous=None;intervals=0
        with localcontext() as ctx:
            ctx.prec=100
            for part in parts:
                directory=Path(part['command'][3]);require(directory.is_relative_to(ROOT/'references-local'),'local measured directory')
                paths.update((directory/n).relative_to(ROOT).as_posix() for n in ['trace.bin','checkpoints.bin','final.ckp','selected.txt','stderr.txt'])
                points=checkpoints(directory/'checkpoints.bin');start=points[0]
                if previous:require(start==previous,'exact typed continuation seam')
                else:require(start['ticks']==0,'conditioned initial clock')
                rows=trace(directory/'trace.bin',start_ticks=start['ticks']);last=checkpoint((directory/'final.ckp').read_bytes())
                require(int(rows[-1]['ticks'])==last['ticks'],'final checkpoint agrees with trace')
                info=summary(part['stderr']);require(int(info['intervals'])*2==len(rows) and int(info['ticks'])==last['ticks'],'native ledger length')
                require(start['maximum']==maximum and last['maximum']==maximum,'profile metadata')
                intervals+=int(info['intervals']);restores+=int(info['restore_replays']);charge+=Decimal.from_float(info['charge']);absolute+=Decimal.from_float(info['absolute']);previous=last;pieces.append(rows)
                for q in points:
                    if q['ticks']%ANCHOR==0:
                        if cps and q['ticks']==cps[-1]['ticks']:require(q==cps[-1],'duplicate anchor identity')
                        else:cps.append(q)
            require(previous['ticks']==GOAL,'complete requested coverage')
            rows=np.concatenate(pieces);require(len(rows)%2==0 and np.all(np.diff(rows['ticks'])>0),'continuous segment timeline')
            require([q['ticks'] for q in cps]==[k*ANCHOR for k in range(22)],'all shared anchors')
            require(restores==2,'two exact byte-restore continuations')
            initial=cps[0];end=cps[-1];delta=Decimal.from_float(end['high'][43])+Decimal.from_float(end['low'][43])-Decimal.from_float(initial['high'][43])-Decimal.from_float(initial['low'][43])
            balance=abs(charge+Decimal.from_float(1e-8)*delta)/absolute;require(balance<=Decimal('.002'),'C1 integrated charge gate')
            measured=reset_measurements(rows)
            result.append(dict(maximum_half_ticks=maximum,intervals=intervals,endpoints=len(rows),segments=len(parts),restore_replays=restores,max_lte=float(np.max(rows['lte'])),min_half_ticks=int(np.min(rows['half_ticks'])),max_bus_kcl_a=float(np.max(np.abs(rows['bus_kcl']))),max_c1_kcl_a=float(np.max(np.abs(rows['c1_kcl']))),integrated_charge_relative=str(balance),final_ticks=int(rows[-1]['ticks']),measurements=measured))
            anchors.append(cps)
    points=compare(*anchors);frequency=1200*abs(np.log2(result[0]['measurements']['frequency_hz']/result[1]['measurements']['frequency_hz']));require(frequency<=1,'frequency refinement cent')
    extremes={n:max(abs(result[0]['measurements']['extrema'][n][edge]-result[1]['measurements']['extrema'][n][edge]) for edge in ['min_v','max_v']) for n in ['saw','tri','pulse','bus','j7']}
    require(max(extremes.values())<=.005,'wave extrema refinement')
    return dict(profiles=result,shared_clock_points=points,frequency_refinement_cents=float(frequency),extrema_refinement_v=extremes,input_sha256={n:sha(ROOT/n) for n in sorted(paths)})
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,required=True);parser.add_argument('--extension');a=parser.parse_args()
    out=ROOT/f'evidence/voice_joint_cycles_analysis{a.attempt:02d}.json';require(not out.exists(),'new receipt')
    native='evidence/voice_joint_cycles_native01.json';source=[native,'tools/analyze_joint_cycles.py','tools/joint_cycles_analysis.py','docs/VOZ_PRIMER_CICLO_PROTOCOLO.md']
    if a.extension:source.append(a.extension)
    before={n:sha(ROOT/n) for n in source};report=dict(schema='rf-d/joint-cycles-analysis/v1',passed=False,source_sha256=before)
    data=json.loads((ROOT/native).read_text());extension=json.loads((ROOT/a.extension).read_text()) if a.extension else None
    try:report.update(analyze(data,extension));report['passed']=True
    except Exception:
        report['failure']=traceback.format_exc();report['failed_source_text']={n:(ROOT/n).read_text() for n in source if n.endswith('.py')}
        try:analyze(data,extension);report['replay']='unexpected pass'
        except Exception:report['replay']=traceback.format_exc()
    report['source_sha256_after']={n:sha(ROOT/n) for n in source};require(before==report['source_sha256_after'],'unchanged analysis sources')
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n');print('CYCLES_ANALYSIS',report['passed'],report.get('failure',''),report.get('frequency_refinement_cents'),report.get('extrema_refinement_v'))
if __name__=='__main__':main()
