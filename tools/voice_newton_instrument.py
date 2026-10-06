"""Read-only solver observations; patch only the SHA-pinned private ngspice tree."""
import hashlib,json
from pathlib import Path
import vco1_circuit_reference as vco

ROOT=vco.ROOT
WORK=ROOT/'references-local/voice-circuit/newton-build01'
TREE=WORK/'ngspice-46'
WINDOW=(.0022773,.0022775)
GUARD='getenv("RF_D_TRACE") && ckt->CKTtime >= 0.0022773 && ckt->CKTtime <= 0.0022775'


def insert(text,marker,addition):
    if text.count(marker)!=1:raise ValueError('instrumentation anchor must be unique')
    return text.replace(marker,marker+addition,1)


def patch(name,text):
    if name.endswith('/niiter.c'):
        marker='            ckt->CKTrhsOld[0] = 0;\n'
        return insert(text,marker,'''
            /* RF-D observation only: never write circuit state or matrix. */
            if ('''+GUARD+''') {
                CKTnode *rf_node;
                const char *rf_name = "none";
                double rf_ratio = 0, rf_old = 0, rf_new = 0, rf_tol = 0;
                for (rf_node = ckt->CKTnodes->next; rf_node; rf_node = rf_node->next) {
                    double a = ckt->CKTrhsOld[rf_node->number];
                    double b = ckt->CKTrhs[rf_node->number];
                    double tol = ckt->CKTreltol * MAX(fabs(a),fabs(b)) +
                        (rf_node->type == SP_VOLTAGE ? ckt->CKTvoltTol : ckt->CKTabstol);
                    double ratio = fabs(b-a)/tol;
                    if (!isfinite(a) || !isfinite(b) || !isfinite(ratio))
                        fprintf(stderr,"RFTRACE,invalid,%.17g,%.17g,%s\\n",
                            ckt->CKTtime,ckt->CKTdelta,CKTnodName(ckt,rf_node->number));
                    if (ratio > rf_ratio) {
                        rf_ratio = ratio; rf_old = a; rf_new = b; rf_tol = tol;
                        rf_name = CKTnodName(ckt,rf_node->number);
                    }
                }
                fprintf(stderr,"RFTRACE,iteration,%.17g,%.17g,%d,%d,%d,%s,%.17g,%.17g,%.17g,%.17g\\n",
                    ckt->CKTtime,ckt->CKTdelta,iterno,ckt->CKTmode,ckt->CKTnoncon,
                    rf_name,rf_ratio,rf_old,rf_new,rf_tol);
            }
''')
    if name.endswith('/jfetload.c'):
        marker='                    ckt->CKTnoncon++;\n'
        return insert(text,marker,'''
                    if ('''+GUARD+''') {
                        fprintf(stderr,"RFTRACE,jfet,%.17g,%.17g,%s,%d,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g\\n",
                            ckt->CKTtime,ckt->CKTdelta,here->JFETname,icheck,
                            cghat,cg,ckt->CKTreltol*MAX(fabs(cghat),fabs(cg))+ckt->CKTabstol,
                            cdhat,cd,ckt->CKTreltol*MAX(fabs(cdhat),fabs(cd))+ckt->CKTabstol,
                            vgs,vgd);
                    }
''')
    if name.endswith('/niconv.c'):
        # Both return sites are intentional. Observe the actual first rejected node.
        marker='                ckt->CKTtroubleNode = i;\n'
        if text.count(marker)!=2:raise ValueError('two nodal convergence sites required')
        return text.replace(marker,'''
                if ('''+GUARD+''')
                    fprintf(stderr,"RFTRACE,node,%.17g,%.17g,%s,%.17g,%.17g,%.17g\\n",
                        ckt->CKTtime,ckt->CKTdelta,CKTnodName(ckt,i),old,new,tol);
'''+marker)
    if name.endswith('/dctran.c'):
        text=insert(text,'        converged = NIiter(ckt,ckt->CKTtranMaxIter);\n','''
        if ('''+GUARD+''')
            fprintf(stderr,"RFTRACE,step,%.17g,%.17g,%d,%d\\n",
                ckt->CKTtime,ckt->CKTdelta,converged,ckt->CKTorder);
''')
        return insert(text,'            error = CKTtrunc(ckt,&newdelta);\n','''
            if ('''+GUARD+''')
                fprintf(stderr,"RFTRACE,trunc,%.17g,%.17g,%.17g,%d\\n",
                    ckt->CKTtime,ckt->CKTdelta,newdelta,error);
''')
    raise ValueError('unrecognized source')


def main():
    output=WORK/'patch.json'
    if output.exists():raise ValueError('preserve instrumentation identity')
    identities=vco.read(WORK/'source-identity.json');report={}
    for name,identity in identities.items():
        path=TREE/name
        if vco.sha(path)!=identity['sha256']:raise ValueError('source identity: '+name)
        text=path.read_text(encoding='utf-8');changed=patch(name,text)
        path.write_text(changed,encoding='utf-8',newline='\n')
        report[name]=dict(before_sha256=identity['sha256'],after_sha256=vco.sha(path),url=identity['url'])
    output.write_text(json.dumps(dict(sources=report,patcher_sha256=vco.sha(Path(__file__)),window_s=WINDOW,
                                   circuit_equations_changed=False),indent=2)+'\n',encoding='utf-8',newline='\n')
    print('four source files instrumented; numerical statements unchanged')


if __name__=='__main__':main()
