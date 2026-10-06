"""Resolve a formal subcircuit pin through the frozen instance before observing it."""
import json,shutil
from pathlib import Path
import voice_kcl_instrument as rejected
import voice_inductor_instrument as admitted
import voice_newton_probe as runner
import vco1_circuit_reference as vco

ROOT=vco.ROOT
WORK=ROOT/'references-local/voice-circuit/newton-build04'
TREE=WORK/'ngspice-46'


def resolve_pin_alias(text,formal_pin):
    pins=('1','2','99','50','28')
    if formal_pin not in pins:raise ValueError('unknown formal pin')
    rows=[s.split() for s in text.splitlines() if s.split() and s.split()[0].upper()=='XIC3']
    if len(rows)!=1 or len(rows[0])!=7 or rows[0][-1].upper()!='LM741':raise ValueError('unique frozen LM741 instance required')
    return rows[0][1+pins.index(formal_pin)].lower()


def main():
    if WORK.exists():raise ValueError('preserve previous build')
    failed=vco.read(ROOT/'evidence/voice_kcl_observation_rejection01.json')
    if failed['passed'] or failed['gate']!='selected node observation completeness':raise ValueError('rejected observation required')
    aliases={}
    for kind in ('constant','returned'):
        deck,_,_=runner.original(kind)
        aliases[kind]=dict(deck_sha256=vco.sha(deck),external_node=resolve_pin_alias(deck.read_text(encoding='utf-8'),'1'))
    if aliases['constant']['external_node']!=aliases['returned']['external_node']:raise ValueError('same pin boundary required')
    WORK.mkdir();shutil.copytree(rejected.TREE,TREE)
    shutil.copytree(rejected.WORK/'baseline02',WORK/'baseline02');moved={}
    for p in (WORK/'baseline02').rglob('*'):
        if p.is_file() and p.name in ('Makefile','config.status','libtool','makedefs','GNUmakefile'):
            b=p.read_bytes();a=b.replace(b'newton-build03',b'newton-build04')
            if a!=b:
                before=vco.sha(p);p.write_bytes(a)
                moved[p.relative_to(WORK).as_posix()]=dict(before_sha256=before,after_sha256=vco.sha(p))
    (WORK/'bin').mkdir();shutil.copy2(rejected.WORK/'bin/observer.exe',WORK/'bin/prior.exe')
    module=WORK/'baseline02/src/xspice/icm/spice2poly/spice2poly.cm'
    if vco.sha(module)!=vco.sha(rejected.WORK/'baseline02/src/xspice/icm/spice2poly/spice2poly.cm'):raise ValueError('copied module identity')
    (WORK/'init02').mkdir();(WORK/'init02/spinit').write_text('codemodel '+module.as_posix()+'\n',encoding='utf-8',newline='\n')
    p=TREE/rejected.NI;before=vco.sha(p);text=p.read_text(encoding='utf-8');marker='"xic3.1"'
    if text.count(marker)!=1:raise ValueError('unique rejected lookup required')
    p.write_text(text.replace(marker,'"'+aliases['constant']['external_node']+'"',1),encoding='utf-8',newline='\n')
    report=dict(schema='rf-d/kcl-pin-alias-build/v1',previous_audit_sha256=vco.sha(ROOT/'evidence/voice_inductor_observation01.json'),
                rejected_observation_sha256=vco.sha(ROOT/'evidence/voice_kcl_observation_rejection01.json'),
                patches={rejected.NI:dict(before_sha256=before,after_sha256=vco.sha(p))},
                relocated_generated_files=moved,pin_aliases=aliases,circuit_equations_changed=False,
                patcher_path=Path(__file__).relative_to(ROOT).as_posix(),patcher_sha256=vco.sha(Path(__file__)))
    (WORK/'patch.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('external pin resolved from both frozen decks; lookup-only correction',flush=True)


if __name__=='__main__':main()
