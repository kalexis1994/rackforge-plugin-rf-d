"""Build one explicitly enabled equivalent branch row; preserve the old tree."""
import json,shutil
from pathlib import Path
import voice_kcl_alias_instrument as prior
import vco1_circuit_reference as vco

ROOT=vco.ROOT
WORK=ROOT/'references-local/voice-circuit/newton-build05'
TREE=WORK/'ngspice-46'
DIR='src/spicelib/devices/ind/'


def replace_once(text,old,new):
    if text.count(old)!=1:raise ValueError('unique source anchor required')
    return text.replace(old,new,1)


def main():
    if WORK.exists():raise ValueError('preserve previous build')
    audit=vco.read(ROOT/'evidence/voice_kcl_observation02.json')
    if not audit['passed']:raise ValueError('prior KCL observation required')
    WORK.mkdir();shutil.copytree(prior.TREE,TREE)
    shutil.copytree(prior.WORK/'baseline02',WORK/'baseline02');moved={}
    for p in (WORK/'baseline02').rglob('*'):
        if p.is_file() and p.name in ('Makefile','config.status','libtool','makedefs','GNUmakefile'):
            b=p.read_bytes();a=b.replace(b'newton-build04',b'newton-build05')
            if a!=b:
                before=vco.sha(p);p.write_bytes(a)
                moved[p.relative_to(WORK).as_posix()]=dict(before_sha256=before,after_sha256=vco.sha(p))
    (WORK/'bin').mkdir();shutil.copy2(prior.WORK/'bin/observer.exe',WORK/'bin/prior.exe')
    module=WORK/'baseline02/src/xspice/icm/spice2poly/spice2poly.cm'
    if vco.sha(module)!=vco.sha(prior.WORK/'baseline02/src/xspice/icm/spice2poly/spice2poly.cm'):raise ValueError('module identity')
    (WORK/'init02').mkdir();(WORK/'init02/spinit').write_text('codemodel '+module.as_posix()+'\n',encoding='utf-8',newline='\n')
    patches={}
    def save(name,text):
        p=TREE/(DIR+name);before=vco.sha(p);p.write_text(text,encoding='utf-8',newline='\n')
        patches[DIR+name]=dict(before_sha256=before,after_sha256=vco.sha(p))
    p=TREE/(DIR+'inddefs.h');s=p.read_text(encoding='utf-8')
    marker='    unsigned INDindGiven'
    fields='''    /* RF-D laboratory-only equivalent row, explicitly enabled at setup. */
    int IND741Active, IND741Node16, IND741Node3, IND741Node49;
    double *IND741Conduct, *IND741GM;
    double *IND741Ptr16, *IND741Ptr3, *IND741Ptr49;
#ifdef KLU
    BindElement *IND741Binding16, *IND741Binding3, *IND741Binding49;
#endif

'''
    save('inddefs.h',replace_once(s,marker,fields+marker))
    p=TREE/(DIR+'indsetup.c');s=p.read_text(encoding='utf-8')
    s=replace_once(s,'#include "inddefs.h"','#include "inddefs.h"\n#include "../res/resdefs.h"\n#include "../vccs/vccsdefs.h"')
    marker='            TSTALLOC(INDibrIbrPtr,INDbrEq,INDbrEq);\n'
    addition='''
            here->IND741Active = 0;
            if (getenv("RF_D_741_REDUCE") && !strcmp(getenv("RF_D_741_REDUCE"),"1") && !strcmp(here->INDname,"l.xic3.l2")) {
                RESmodel *rm; RESinstance *ri, *found_r=NULL;
                VCCSmodel *gm; VCCSinstance *gi, *found_g=NULL;
                int rt=CKTtypelook("Resistor"), gt=CKTtypelook("VCCS");
                if (rt<0 || gt<0) return E_BADPARM;
                for (rm=(RESmodel *)ckt->CKThead[rt];rm;rm=RESnextModel(rm))
                    for (ri=RESinstances(rm);ri;ri=RESnextInstance(ri))
                        if (!strcmp(ri->RESname,"r.xic3.r13")) found_r=ri;
                for (gm=(VCCSmodel *)ckt->CKThead[gt];gm;gm=VCCSnextModel(gm))
                    for (gi=VCCSinstances(gm);gi;gi=VCCSnextInstance(gi))
                        if (!strcmp(gi->VCCSname,"g.xic3.g4")) found_g=gi;
                if (!found_r || !found_g || found_r->RESposNode!=here->INDnegNode ||
                    found_g->VCCSposNode!=here->INDposNode || found_g->VCCSnegNode!=found_r->RESnegNode) return E_BADPARM;
                here->IND741Node16=found_r->RESnegNode;
                here->IND741Node3=found_g->VCCScontPosNode;
                here->IND741Node49=found_g->VCCScontNegNode;
                here->IND741Conduct=&found_r->RESconduct;
                here->IND741GM=&found_g->VCCScoeff;
                TSTALLOC(IND741Ptr16,INDbrEq,IND741Node16);
                TSTALLOC(IND741Ptr3,INDbrEq,IND741Node3);
                TSTALLOC(IND741Ptr49,INDbrEq,IND741Node49);
                here->IND741Active=1;
                fprintf(stderr,"RF741REDUCE,setup,%s,%d,%d,%d,%d\\n",here->INDname,here->INDbrEq,here->IND741Node16,here->IND741Node3,here->IND741Node49);
            }
'''
    save('indsetup.c',replace_once(s,marker,marker+addition))
    p=TREE/(DIR+'indbindCSC.c');s=p.read_text(encoding='utf-8')
    for macro in ('CREATE_KLU_BINDING_TABLE','CONVERT_KLU_BINDING_TABLE_TO_COMPLEX','CONVERT_KLU_BINDING_TABLE_TO_REAL'):
        marker='            '+macro+'(INDibrIbrPtr, INDibrIbrBinding, INDbrEq, INDbrEq);\n'
        addition='            if (here->IND741Active) {\n'
        for node in ('16','3','49'):
            addition+='                '+macro+'(IND741Ptr'+node+', IND741Binding'+node+', INDbrEq, IND741Node'+node+');\n'
        addition+='            }\n'
        s=replace_once(s,marker,marker+addition)
    save('indbindCSC.c',s)
    p=TREE/(DIR+'indload.c');s=p.read_text(encoding='utf-8')
    s=replace_once(s,'            *(ckt->CKTrhs+here->INDbrEq) += veq;',
                     '            if (!here->IND741Active) *(ckt->CKTrhs+here->INDbrEq) += veq;')
    marker='''            *(here->INDibrPosPtr) +=  1;
            *(here->INDibrNegPtr) -=  1;
            *(here->INDibrIbrPtr) -=  req;'''
    replacement='''            if (here->IND741Active) {
                double g=*here->IND741Conduct, gm=*here->IND741GM, gain, scale;
                if (!(g>0) || !(gm>0) || !isfinite(g) || !isfinite(gm) || req<0) return E_BADPARM;
                gain=(req+1.0/g)*gm;
                scale=fmax(1.0,fabs(gain));
                if (!isfinite(gain) || !isfinite(scale)) return E_BADPARM;
                *(here->INDibrPosPtr) += 1.0/scale;
                *(here->IND741Ptr16) -= 1.0/scale;
                *(here->IND741Ptr3) += gain/scale;
                *(here->IND741Ptr49) -= gain/scale;
                *(ckt->CKTrhs+here->INDbrEq) += veq/scale;
            } else {
                *(here->INDibrPosPtr) +=  1;
                *(here->INDibrNegPtr) -=  1;
                *(here->INDibrIbrPtr) -=  req;
            }'''
    save('indload.c',replace_once(s,marker,replacement))
    report=dict(schema='rf-d/741-reduced-row-build/v1',previous_audit_sha256=vco.sha(ROOT/'evidence/voice_kcl_observation02.json'),
                patches=patches,relocated_generated_files=moved,patcher_sha256=vco.sha(Path(__file__)),
                numerical_branch_row_changed=True,physical_components_changed=False,state_update_changed=False,
                scale_policy='max(1,abs((req+1/gR)*gm))',enable_environment='RF_D_741_REDUCE=1')
    (WORK/'patch.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('equivalent row candidate copied; four source files changed; old state update retained',flush=True)


if __name__=='__main__':main()
