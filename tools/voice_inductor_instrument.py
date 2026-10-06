"""Extend the immutable local Newton build with L2 observation only."""
import json,shutil,urllib.request
from pathlib import Path
import voice_newton_instrument as old
import vco1_circuit_reference as vco

ROOT=vco.ROOT
WORK=ROOT/'references-local/voice-circuit/newton-build02'
TREE=WORK/'ngspice-46'
REV='ebdaf58ec76a06ffaac7e0f138360dd1cf5ee4b6'
IND='src/spicelib/devices/ind/indload.c'
NI='src/maths/ni/niiter.c'
TARGET='l.xic3.l2'


def main():
    if WORK.exists():raise ValueError('preserve previous build')
    prior=vco.read(ROOT/'evidence/voice_newton_observation01.json')
    if not prior['passed']:raise ValueError('previous observation required')
    WORK.mkdir()
    shutil.copytree(old.TREE,TREE)
    shutil.copytree(old.WORK/'baseline02',WORK/'baseline02')
    # Generated build paths are relocated; source and circuit equations are preserved.
    moved={}
    for p in (WORK/'baseline02').rglob('*'):
        if p.is_file() and p.name in ('Makefile','config.status','libtool','makedefs','GNUmakefile'):
            b=p.read_bytes();a=b.replace(b'newton-build01',b'newton-build02')
            if a!=b:
                before=vco.sha(p);p.write_bytes(a);moved[p.relative_to(WORK).as_posix()]=dict(before_sha256=before,after_sha256=vco.sha(p))
    (WORK/'bin').mkdir();shutil.copy2(old.WORK/'bin/instrumented.exe',WORK/'bin/prior.exe')
    (WORK/'init02').mkdir();module=WORK/'baseline02/src/xspice/icm/spice2poly/spice2poly.cm'
    if vco.sha(module)!=vco.sha(old.WORK/'baseline02/src/xspice/icm/spice2poly/spice2poly.cm'):raise ValueError('copied module identity')
    (WORK/'init02/spinit').write_text('codemodel '+module.as_posix()+'\n',encoding='utf-8',newline='\n')
    sources={}
    for name in (IND,'src/maths/ni/niinteg.c','src/spicelib/devices/ind/inddefs.h'):
        url='https://raw.githubusercontent.com/imr/ngspice/'+REV+'/'+name
        data=urllib.request.urlopen(url,timeout=30).read()
        if data!=(TREE/name).read_bytes():raise ValueError('primary source identity: '+name)
        sources[name]=dict(url=url,sha256=vco.sha(TREE/name))
    ind=TREE/IND;text=ind.read_text(encoding='utf-8');before=vco.sha(ind)
    marker='            *(ckt->CKTrhs+here->INDbrEq) += veq;\n'
    addition='''
            /* RF-D read-only history and actual affine stamp. */
            if ('''+old.GUARD+''' && !strcmp(here->INDname,"l.xic3.l2")) {
                fprintf(stderr,"RFLTRACE,load,%.17g,%.17g,%s,%d,%d,%d,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g\\n",
                    ckt->CKTtime,ckt->CKTdelta,here->INDname,ckt->CKTorder,ckt->CKTmode,here->INDbrEq,
                    here->INDinduct/here->INDm,ckt->CKTstate0[here->INDflux],
                    ckt->CKTstate1[here->INDflux],ckt->CKTstate2[here->INDflux],
                    ckt->CKTag[0],ckt->CKTag[1],ckt->CKTag[2],ckt->CKTstate0[here->INDvolt],
                    req,veq,ckt->CKTrhsOld[here->INDbrEq],
                    ckt->CKTrhsOld[here->INDposNode],ckt->CKTrhsOld[here->INDnegNode]);
            }
'''
    ind.write_text(old.insert(text,marker,addition),encoding='utf-8',newline='\n')
    patches={IND:dict(before_sha256=before,after_sha256=vco.sha(ind))}
    ni=TREE/NI;before=vco.sha(ni);text=ni.read_text(encoding='utf-8')
    marker='                    rf_name,rf_ratio,rf_old,rf_new,rf_tol);\n'
    addition='''
                {
                    int rf_br=-1, rf_pos=-1, rf_neg=-1;
                    for (rf_node=ckt->CKTnodes->next; rf_node; rf_node=rf_node->next) {
                        const char *name=CKTnodName(ckt,rf_node->number);
                        if (!strcmp(name,"l.xic3.l2#branch")) rf_br=rf_node->number;
                        if (!strcmp(name,"xic3.98")) rf_pos=rf_node->number;
                        if (!strcmp(name,"xic3.17")) rf_neg=rf_node->number;
                    }
                    if (rf_br<0 || rf_pos<0 || rf_neg<0)
                        fprintf(stderr,"RFLTRACE,invalid,%.17g,%.17g\\n",ckt->CKTtime,ckt->CKTdelta);
                    else
                        fprintf(stderr,"RFLTRACE,solve,%.17g,%.17g,%d,%d,%.17g,%.17g,%.17g,%.17g\\n",
                            ckt->CKTtime,ckt->CKTdelta,iterno,rf_br,
                            ckt->CKTrhsOld[rf_br],ckt->CKTrhs[rf_br],
                            ckt->CKTrhs[rf_pos],ckt->CKTrhs[rf_neg]);
                }
'''
    ni.write_text(old.insert(text,marker,addition),encoding='utf-8',newline='\n')
    patches[NI]=dict(before_sha256=before,after_sha256=vco.sha(ni))
    report=dict(schema='rf-d/inductor-observer-build/v1',previous_audit_sha256=vco.sha(ROOT/'evidence/voice_newton_observation01.json'),
                primary_sources=sources,patches=patches,relocated_generated_files=moved,
                circuit_equations_changed=False,patcher_sha256=vco.sha(Path(__file__)))
    (WORK/'patch.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('separate build copied; two read-only insertions; prior tree preserved',flush=True)


if __name__=='__main__':main()
