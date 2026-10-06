"""Read-only NI/KLU observer copied from the admitted original build04."""
import json, shutil
from pathlib import Path
import voice_kcl_alias_instrument as prior
import vco1_circuit_reference as vco

ROOT=vco.ROOT
WORK=ROOT/'references-local/voice-circuit/newton-build06'
TREE=WORK/'ngspice-46'

def once(text, marker, addition):
    if text.count(marker)!=1: raise ValueError('unique source anchor required')
    return text.replace(marker,addition,1)

def patched(ni, klu):
    ni=once(ni,'static int msgcount = 0;', '''static int msgcount = 0;
#ifdef KLU
/* Laboratory observer selection; never used by numerical calculations. */
int RFMatrixTrace = 0;
static void RFMatrixVector(CKTcircuit *ckt, const char *stage)
{
    unsigned int k;
    for (k=0; k<ckt->CKTmatrix->SMPkluMatrix->KLUmatrixN; k++) {
        unsigned int old=ckt->CKTmatrix->SMPkluMatrix->KLUmatrixNodeCollapsingNewToOld[k+1];
        CKTnode *node;
        if (!strcmp(stage,"before")) {
            for (node=ckt->CKTnodes; node && node->number!=(int)old; node=node->next) {}
            fprintf(stderr,"RFMATRIX,node,%u,%u,%d,%s,%.17g,%.17g\\n",k,old,
                node ? node->type : -1,node ? node->name : "MISSING",
                ckt->CKTrhs[old],ckt->CKTrhsOld[old]);
        } else {
            fprintf(stderr,"RFMATRIX,x,%u,%.17g\\n",k,ckt->CKTrhs[old]);
        }
    }
}
#endif''')
    marker='            if (ckt->CKTniState & NISHOULDREORDER) {'
    ni=once(ni,marker,'''#ifdef KLU
            RFMatrixTrace = getenv("RF_D_MATRIX_TRACE") &&
                !strcmp(getenv("RF_D_MATRIX_TRACE"),"1") && ckt->CKTkluMODE &&
                ckt->CKTtime>=0.0022773 && ckt->CKTtime<=0.0022775 &&
                ckt->CKTdelta<=1e-17 && (iterno==100 || iterno==101);
            if (RFMatrixTrace) {
                fprintf(stderr,"RFMATRIX,begin,%.17g,%.17g,%d,%d,%d,%u,%u,%.17g\\n",
                    ckt->CKTtime,ckt->CKTdelta,iterno,ckt->CKTorder,ckt->CKTmode,
                    ckt->CKTmatrix->SMPkluMatrix->KLUmatrixN,
                    ckt->CKTmatrix->SMPkluMatrix->KLUmatrixNZ,ckt->CKTdiagGmin);
                RFMatrixVector(ckt,"before");
            }
#endif
'''+marker)
    marker='            SMPsolve(ckt->CKTmatrix, ckt->CKTrhs, ckt->CKTrhsSpare);'
    ni=once(ni,marker,marker+'''
#ifdef KLU
            if (RFMatrixTrace) {
                RFMatrixVector(ckt,"after");
                fprintf(stderr,"RFMATRIX,end\\n");
            }
            RFMatrixTrace=0;
#endif''')
    marker='static void LoadGmin_CSC (double **diag, unsigned int n, double Gmin) ;'
    klu=once(klu,marker,'''extern int RFMatrixTrace;
static void RFMatrixEntries(SMPmatrix *Matrix, const char *stage)
{
    unsigned int c;
    int k;
    if (!RFMatrixTrace) return;
    fprintf(stderr,"RFMATRIX,factor,%s,%d,%.17g,%d\\n",stage,
        Matrix->SMPkluMatrix->KLUmatrixCommon->scale,
        Matrix->SMPkluMatrix->KLUmatrixCommon->tol,
        Matrix->SMPkluMatrix->KLUmatrixCommon->ordering);
    for (c=0;c<Matrix->SMPkluMatrix->KLUmatrixN;c++)
        for (k=Matrix->SMPkluMatrix->KLUmatrixAp[c];k<Matrix->SMPkluMatrix->KLUmatrixAp[c+1];k++)
            fprintf(stderr,"RFMATRIX,a,%d,%u,%.17g\\n",
                Matrix->SMPkluMatrix->KLUmatrixAi[k],c,Matrix->SMPkluMatrix->KLUmatrixAx[k]);
}
'''+marker)
    marker='        ret = klu_refactor (Matrix->SMPkluMatrix->KLUmatrixAp, Matrix->SMPkluMatrix->KLUmatrixAi, Matrix->SMPkluMatrix->KLUmatrixAx,'
    klu=once(klu,marker,'        RFMatrixEntries(Matrix,"refactor-after-gmin");\n'+marker)
    marker='        Matrix->SMPkluMatrix->KLUmatrixNumeric = klu_factor (Matrix->SMPkluMatrix->KLUmatrixAp, Matrix->SMPkluMatrix->KLUmatrixAi,\n                                                             Matrix->SMPkluMatrix->KLUmatrixAx, Matrix->SMPkluMatrix->KLUmatrixSymbolic,'
    klu=once(klu,marker,'        RFMatrixEntries(Matrix,"factor-after-gmin");\n'+marker)
    return ni,klu

def main():
    if WORK.exists(): raise ValueError('preserve previous build')
    paths=('src/maths/ni/niiter.c','src/maths/KLU/klusmp.c')
    originals=[(prior.TREE/p).read_text(encoding='utf-8') for p in paths]
    changes=patched(*originals) # Preflight all anchors before copying or patching.
    WORK.mkdir();shutil.copytree(prior.TREE,TREE)
    shutil.copytree(prior.WORK/'baseline02',WORK/'baseline02');moved={}
    for p in (WORK/'baseline02').rglob('*'):
        if p.is_file() and p.name in ('Makefile','config.status','libtool','makedefs','GNUmakefile'):
            b=p.read_bytes();a=b.replace(b'newton-build04',b'newton-build06')
            if a!=b:
                before=vco.sha(p);p.write_bytes(a)
                moved[p.relative_to(WORK).as_posix()]=dict(before_sha256=before,after_sha256=vco.sha(p))
    (WORK/'bin').mkdir();shutil.copy2(prior.WORK/'bin/observer.exe',WORK/'bin/prior.exe')
    module=WORK/'baseline02/src/xspice/icm/spice2poly/spice2poly.cm'
    if vco.sha(module)!=vco.sha(prior.WORK/'baseline02/src/xspice/icm/spice2poly/spice2poly.cm'): raise ValueError('module identity')
    (WORK/'init02').mkdir();(WORK/'init02/spinit').write_text('codemodel '+module.as_posix()+'\n',encoding='utf-8',newline='\n')
    patches={}
    for name,s in zip(paths,changes):
        p=TREE/name;before=vco.sha(p);p.write_text(s,encoding='utf-8',newline='\n')
        patches[name]=dict(before_sha256=before,after_sha256=vco.sha(p))
    report=dict(schema='rf-d/newton-matrix-build/v1',previous_audit_sha256=vco.sha(ROOT/'evidence/voice_kcl_observation02.json'),
        rejected_candidate_sha256=vco.sha(ROOT/'evidence/voice_741_row_validation01.json'),patches=patches,
        relocated_generated_files=moved,patcher_sha256=vco.sha(Path(__file__)),
        protocol_sha256=vco.sha(ROOT/'docs/NEWTON_MATRIZ_COMPLETA_PROTOCOLO.md'),
        circuit_equations_changed=False,solver_tolerances_changed=False,
        selection='iterno 100/101; h<=1e-17; 2.2773-2.2775ms; RF_D_MATRIX_TRACE=1',
        capture='CSC immediately before klu_factor/klu_refactor, after LoadGmin_CSC; full mapped RHS/xOld before SMPsolve; x after')
    (WORK/'patch.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('original build04 copied; NI/KLU read-only observer prepared',flush=True)

if __name__=='__main__': main()
