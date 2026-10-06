"""Resume the verified unpatched copy after the preserved insertion preflight rejection."""
import json,shutil,urllib.request
from pathlib import Path
import voice_inductor_instrument as previous
import voice_newton_instrument as original
import vco1_circuit_reference as vco

ROOT=vco.ROOT
WORK=ROOT/'references-local/voice-circuit/newton-build03'
TREE=WORK/'ngspice-46'
NI='src/maths/ni/niiter.c'
RES='src/spicelib/devices/res/resload.c'
VCCS='src/spicelib/devices/vccs/vccsload.c'


def main():
    audit=vco.read(ROOT/'evidence/voice_inductor_observation01.json')
    if not audit['passed']:raise ValueError('prior observation scope')
    rejection=vco.read(ROOT/'evidence/voice_kcl_preparation_rejection01.json')
    if vco.sha(ROOT/rejection['source_path'])!=rejection['source_sha256'] or vco.sha(ROOT/rejection['frozen_source_path'])!=rejection['source_sha256']:raise ValueError('preserved failed source')
    expected={p.relative_to(previous.TREE).as_posix():vco.sha(p) for p in previous.TREE.rglob('*') if p.is_file()}
    actual={p.relative_to(TREE).as_posix():vco.sha(p) for p in TREE.rglob('*') if p.is_file()}
    if expected!=actual:raise ValueError('retry requires exact unpatched source copy')
    moved={}
    for p in (previous.WORK/'baseline02').rglob('*'):
        if p.is_file() and p.name in ('Makefile','config.status','libtool','makedefs','GNUmakefile'):
            b=p.read_bytes();a=b.replace(b'newton-build02',b'newton-build03');target=WORK/'baseline02'/p.relative_to(previous.WORK/'baseline02')
            import hashlib
            if target.read_bytes()!=a:raise ValueError('relocated generated build identity')
            if a!=b:moved[target.relative_to(WORK).as_posix()]=dict(before_sha256=vco.sha(p),after_sha256=vco.sha(target))
    module=WORK/'baseline02/src/xspice/icm/spice2poly/spice2poly.cm'
    if vco.sha(module)!=vco.sha(previous.WORK/'baseline02/src/xspice/icm/spice2poly/spice2poly.cm'):raise ValueError('module identity')
    if vco.sha(WORK/'bin/prior.exe')!=vco.sha(previous.WORK/'bin/observer.exe'):raise ValueError('prior executable identity')
    if (WORK/'init02/spinit').read_text(encoding='utf-8')!='codemodel '+module.as_posix()+'\n':raise ValueError('initialization identity')
    sources={}
    for name in (RES,VCCS,'src/xspice/icm/spice2poly/icm_spice2poly/ifspec.ifs',
                 'src/xspice/icm/spice2poly/icm_spice2poly/cfunc.mod'):
        url='https://raw.githubusercontent.com/imr/ngspice/'+previous.REV+'/'+name
        if urllib.request.urlopen(url,timeout=30).read()!=(TREE/name).read_bytes():raise ValueError('primary source identity: '+name)
        sources[name]=dict(url=url,sha256=vco.sha(TREE/name))
    patches={}
    for name,field,marker in ((RES,'RESconduct','            *(here->RESnegPosPtr) -= here->RESconduct;\n'),
                              (VCCS,'VCCScoeff','            *(here->VCCSnegContNegPtr) += here->VCCScoeff ;\n')):
        p=TREE/name;before=vco.sha(p);s=p.read_text(encoding='utf-8')
        target='r.xic3.r13' if name==RES else 'g.xic3.g4'
        device='RESname' if name==RES else 'VCCSname'
        kind='res' if name==RES else 'gm'
        addition='''
            /* RF-D read-only actual stamp coefficient. */
            if ('''+original.GUARD+''' && !strcmp(here->'''+device+''',"'''+target+'''"))
                fprintf(stderr,"RFKTRACE,'''+kind+''',%.17g,%.17g,%s,%.17g\\n",
                    ckt->CKTtime,ckt->CKTdelta,here->'''+device+''',here->'''+field+''');
'''
        if s.count(marker)!=1:raise ValueError('stamp insertion anchor')
        p.write_text(s.replace(marker,marker+addition,1),encoding='utf-8',newline='\n')
        patches[name]=dict(before_sha256=before,after_sha256=vco.sha(p))
    p=TREE/NI;before=vco.sha(p);s=p.read_text(encoding='utf-8')
    marker='                            ckt->CKTrhs[rf_pos],ckt->CKTrhs[rf_neg]);\n'
    addition='''
                    {
                        int rf_ids[5]={-1,-1,-1,-1,-1}, rf_j;
                        const char *rf_names[5]={"xic3.16","xic3.3","xic3.49","xic3.7","xic3.1"};
                        for (rf_node=ckt->CKTnodes->next;rf_node;rf_node=rf_node->next)
                            for (rf_j=0;rf_j<5;rf_j++)
                                if (!strcmp(CKTnodName(ckt,rf_node->number),rf_names[rf_j])) rf_ids[rf_j]=rf_node->number;
                        if (rf_br<0 || rf_pos<0 || rf_neg<0 || rf_ids[0]<0 || rf_ids[1]<0 || rf_ids[2]<0 || rf_ids[3]<0 || rf_ids[4]<0)
                            fprintf(stderr,"RFKTRACE,invalid,%.17g,%.17g\\n",ckt->CKTtime,ckt->CKTdelta);
                        else {
                            fprintf(stderr,"RFKTRACE,solve,%.17g,%.17g,%d,%d,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g",
                                ckt->CKTtime,ckt->CKTdelta,iterno,rf_br,
                                ckt->CKTrhsOld[rf_br],ckt->CKTrhs[rf_br],
                                ckt->CKTrhsOld[rf_pos],ckt->CKTrhs[rf_pos],
                                ckt->CKTrhsOld[rf_neg],ckt->CKTrhs[rf_neg]);
                            for (rf_j=0;rf_j<5;rf_j++) fprintf(stderr,",%.17g,%.17g",ckt->CKTrhsOld[rf_ids[rf_j]],ckt->CKTrhs[rf_ids[rf_j]]);
                            fprintf(stderr,"\\n");
                        }
                    }
'''
    p.write_text(original.insert(s,marker,addition),encoding='utf-8',newline='\n')
    patches[NI]=dict(before_sha256=before,after_sha256=vco.sha(p))
    report=dict(schema='rf-d/kcl-observer-build/v1',previous_audit_sha256=vco.sha(ROOT/'evidence/voice_inductor_observation01.json'),
                primary_sources=sources,patches=patches,relocated_generated_files=moved,
                preparation_rejection_sha256=vco.sha(ROOT/'evidence/voice_kcl_preparation_rejection01.json'),
                circuit_equations_changed=False,patcher_path=Path(__file__).relative_to(ROOT).as_posix(),patcher_sha256=vco.sha(Path(__file__)))
    (WORK/'patch.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('separate KCL observer build; prior source and binary preserved',flush=True)


if __name__=='__main__':main()
