"""Descending numerical shunt screen; original JFET and 741 cards unchanged."""
from dataclasses import asdict
import copy,gzip,json
from pathlib import Path
import numpy as np
import loudness_voice_circuit as coupled
import voice_jfet_decomposed_probes as checks
import voice_port_relaxation as port
import voice_circuit_reference as voice
import vco1_circuit_reference as vco

ROOT=vco.ROOT
CANDIDATES=(1e9,1e10,1e11)
REFINED=(1e13,1e14,1e15)
LABELS=dict(constant='fixed-contour-control-01-vco',returned='fixed-contour-control-03-vco')


def factory(label,resistance):
    if resistance not in CANDIDATES+REFINED:raise ValueError('frozen numerical regularization series required')
    bank=json.loads(gzip.decompress((ROOT/'evidence/voice_port_behavioral01.json.gz').read_bytes()))
    original=next(k['vco_receipt'] for k in bank['cases']['fixed-contour-control']['iterations'] if k['vco_receipt']['label']==LABELS[label])
    work=ROOT/'references-local/voice-circuit'/bank['bank'];deck_path=work/(original['label']+'.cir')
    if vco.sha(deck_path)!=original['deck_sha256']:raise ValueError('frozen reproduction deck identity')
    def generate(s,export):
        if asdict(s)!=original['scenario']:raise ValueError('frozen reproduction scenario')
        text=deck_path.read_text(encoding='utf-8');marker='wrdata '+(work/(original['label']+'.txt')).as_posix()+' '
        if text.count(marker)!=1 or text.count('.options ')!=1 or 'rshunt=' in text or " Q='" in text:
            raise ValueError('supported original deck and no behavioral charge state')
        text=text.replace(marker,'wrdata '+export.as_posix()+' ',1)
        text=text.replace('.options ',f'.options rshunt={resistance:.17g} ',1)
        for name,digest in original['source_sha256'].items():
            if vco.sha(ROOT/name)!=digest:raise ValueError('historical input changed: '+name)
        meta=dict(scenario=asdict(s),source_sha256=copy.deepcopy(original['source_sha256']),
                  reproduced_label=original['label'],reproduced_commit=original['git_commit'],
                  reproduced_deck_sha256=original['deck_sha256'],rshunt_ohm=resistance,
                  per_node_extra_conductance_s=1/resistance,diagnostic_only=True,
                  added_shunts_are_physical_components=False,exact_original_equations=False)
        for helper in (Path(__file__),Path(checks.__file__)):
            meta['source_sha256'][helper.relative_to(ROOT).as_posix()]=vco.sha(helper)
        return text,meta
    return generate,original


def main(candidates=CANDIDATES,bank_name='vco-rshunt01'):
    if candidates not in (CANDIDATES,REFINED):raise ValueError('one complete frozen series required')
    work=ROOT/'references-local/voice-circuit'/bank_name
    output=ROOT/'evidence'/('voice_'+bank_name.replace('-','_')+'.json.gz')
    if work.exists() or output.exists():raise ValueError('preserve previous screen')
    exe=ROOT/'references-local/ngspice46/runtime/Spice64/bin/ngspice_con.exe';s=coupled.Scenario()
    report=dict(schema='rf-d/vco-rshunt-screen/v1',bank=work.name,candidates_ohm=candidates,
                gates=checks.GATES,cases={},comparisons={},passed=False,selected=None,
                physical_fidelity=False,real_time=False,coupling_admitted=False)
    def save():output.write_bytes(gzip.compress((json.dumps(report,indent=2)+'\n').encode(),mtime=0))
    reference_path=ROOT/'references-local/voice-circuit/port-behavioral01/fixed-contour-control-01-vco.txt'
    _,old=factory('constant',candidates[0])
    if vco.sha(reference_path)!=old['raw_export_sha256']:raise ValueError('positive reference export identity')
    reference=np.loadtxt(reference_path,skiprows=1,ndmin=2);kept={}
    for resistance in candidates:
        key=f'{resistance:.0e}'.replace('+','')
        for kind in ('constant','returned'):
            label=kind+'-'+key
            try:
                fn,_=factory(kind,resistance)
                raw,r=voice.run(s,label,work,exe,netlist_factory=fn,vectors=port.VCO_VECTORS,timeout=120)
                case=dict(receipt=r,passed=True);report['cases'][label]=case
                if r['source_sha256']!=r['source_sha256_after']:raise ValueError('source changed')
                if kind=='constant':
                    case['contrast']=checks.contrast(raw,reference)
                    if not case['contrast']['passed']:raise ValueError('original control contrast rejected')
                else:kept[key]=raw
                save();print(label,'passed',round(r['wall_s'],2),flush=True)
            except Exception as e:
                path=work/(label+'.json');case=report['cases'].setdefault(label,dict(receipt=vco.read(path) if path.exists() else None))
                case.update(passed=False,error=str(e));report['validation_error']=label+' rejected; descending series stopped'
                if (work/(label+'.txt')).exists():case['last_clock_s']=float(np.loadtxt(work/(label+'.txt'),skiprows=1,ndmin=2)[-1,0])
                save();print(label,'rejected',str(e),flush=True);return
    try:
        keys=list(kept)
        for a,b in zip(keys,keys[1:]):
            report['comparisons'][a+'--'+b]=checks.contrast(kept[a],kept[b])
            if not report['comparisons'][a+'--'+b]['passed']:raise ValueError('descending regularization contrast rejected')
        report['passed']=True
    except Exception as e:report['validation_error']=str(e)
    save();print('isolated regularization screen',report['passed'],flush=True)


if __name__=='__main__':main()
