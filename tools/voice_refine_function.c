/* Included by the preparation helper inside NIiter's KLU section. */
static int RFLinearSolve(CKTcircuit *ckt)
{
    SMPmatrix *m=ckt->CKTmatrix;
    unsigned int n,nz,nrhs,c,k,old;
    int step,ok=0,trace=RFMatrixTrace;
    double *a=NULL,*b=NULL,*rhs=NULL,*spare=NULL;
    RFDD *x=NULL,*r=NULL,p;
    static int announced=0;
    if (!getenv("RF_D_LINEAR_REFINE") || strcmp(getenv("RF_D_LINEAR_REFINE"),"1")) {
        SMPsolve(m,ckt->CKTrhs,ckt->CKTrhsSpare);return OK;
    }
    if (!ckt->CKTkluMODE || m->SMPkluMatrix->KLUmatrixIsComplex)goto failed;
    n=m->SMPkluMatrix->KLUmatrixN;nz=m->SMPkluMatrix->KLUmatrixNZ;
    nrhs=m->SMPkluMatrix->KLUmatrixNrhs;
    if (!n || !nz || nrhs<=n || m->SMPkluMatrix->KLUmatrixAp[n]!=(int)nz)goto failed;
    a=malloc(nz*sizeof(double));b=malloc(n*sizeof(double));
    x=calloc(n,sizeof(RFDD));r=calloc(n,sizeof(RFDD));
    rhs=calloc(nrhs+1,sizeof(double));spare=calloc(nrhs+1,sizeof(double));
    if (!a || !b || !x || !r || !rhs || !spare)goto failed;
    memcpy(a,m->SMPkluMatrix->KLUmatrixAx,nz*sizeof(double));
    for (c=0;c<n;c++) {
        old=m->SMPkluMatrix->KLUmatrixNodeCollapsingNewToOld[c+1];
        if (!old || old>=nrhs)goto failed;
        b[c]=ckt->CKTrhs[old];if (!rf_operand(b[c]))goto failed;
    }
    if (!announced) {
        fprintf(stderr,"RFREFINE,active,three-corrections,pair-fma,all-real-NI\\n");announced=1;
    }
    SMPsolve(m,ckt->CKTrhs,ckt->CKTrhsSpare);
    for(c=0;c<n;c++) {
        old=m->SMPkluMatrix->KLUmatrixNodeCollapsingNewToOld[c+1];x[c].hi=ckt->CKTrhs[old];
        if (!rf_operand(x[c].hi))goto failed;
        if (trace)fprintf(stderr,"RFREFINE,original,%u,%.17g\\n",c,x[c].hi);
    }
    for(step=0;step<3;step++) {
        memset(rhs,0,(nrhs+1)*sizeof(double));
        for(c=0;c<n;c++) {r[c].hi=b[c];r[c].lo=0;}
        for(c=0;c<n;c++) {
            for(k=m->SMPkluMatrix->KLUmatrixAp[c];k<(unsigned int)m->SMPkluMatrix->KLUmatrixAp[c+1];k++) {
                int row=m->SMPkluMatrix->KLUmatrixAi[k];
                if(row<0 || row>=(int)n || !rf_ax(-a[k],x[c],&p))goto failed;
                r[row]=rf_add(r[row],p);if(!rf_good(r[row]))goto failed;
            }
        }
        for(c=0;c<n;c++) {
            old=m->SMPkluMatrix->KLUmatrixNodeCollapsingNewToOld[c+1];
            rhs[old]=r[c].hi+r[c].lo;if(!isfinite(rhs[old]))goto failed;
            if(trace)fprintf(stderr,"RFREFINE,r,%d,%u,%.17g,%.17g\\n",step,c,r[c].hi,r[c].lo);
        }
        SMPsolve(m,rhs,spare);
        for(c=0;c<n;c++) {
            double dx;old=m->SMPkluMatrix->KLUmatrixNodeCollapsingNewToOld[c+1];dx=rhs[old];
            if(!isfinite(dx))goto failed;
            p.hi=dx;p.lo=0;x[c]=rf_add(x[c],p);if(!rf_good(x[c]))goto failed;
            if(trace)fprintf(stderr,"RFREFINE,correction,%d,%u,%.17g,%.17g,%.17g\\n",step,c,dx,x[c].hi,x[c].lo);
        }
    }
    if(memcmp(a,m->SMPkluMatrix->KLUmatrixAx,nz*sizeof(double)))goto failed;
    for(c=0;c<n;c++) {
        old=m->SMPkluMatrix->KLUmatrixNodeCollapsingNewToOld[c+1];
        ckt->CKTrhs[old]=x[c].hi+x[c].lo;
        if(!isfinite(ckt->CKTrhs[old]))goto failed;
    }
    ok=1;
failed:
    free(a);free(b);free(x);free(r);free(rhs);free(spare);
    if(!ok)fprintf(stderr,"RFREFINE,error,dimension-domain-finiteness-or-matrix-change\\n");
    return ok ? OK : E_BADPARM;
}
