"""Avoid full Radau assembly during line-search residual-only candidates."""
from prepare_dual_chain import ROOT
def transform(source):
    a=source.index('    let system = |d: [State; 2]|')
    b=source.index('    for iteration in 1..=budget {',a)
    source=source[:a]+'''    let evaluate = |d:[State;2]|->Result<[Parts;2],StepError>{
        Ok([parts(p,old,d[0],c,h,p.time+h/3.)?,parts(p,old,d[1],c,h,p.time+h)?])
    };
    let residual = |s:&[Parts;2]|->[f64;M]{std::array::from_fn(|k|{
        let a=k%N;let i=k/N;s[i].dc[a]+B[i][0]*s[0].dq[a]+B[i][1]*s[1].dq[a]
    })};
    let jacobian = |s:&[Parts;2]|->[[f64;M];M]{std::array::from_fn(|k|std::array::from_fn(|l|{
        let i=k/N;let a=k%N;let jj=l/N;let b=l%N;
        B[i][jj]*s[jj].mass[a][b]+if i==jj{s[i].j[a][b]}else{0.}
    }))};
    let system = |d:[State;2]|->Result<([f64;M],[[f64;M];M],[State;2]),StepError>{
        let s=evaluate(d)?;Ok((residual(&s),jacobian(&s),[s[0].now,s[1].now]))
    };
'''+source[b:]
    source=source.replace('a:[[f64;M];M],r:[f64;M]', 'a:&[[f64;M];M],r:[f64;M]')
    source=source.replace('gaussian(w,j,', 'gaussian(w,&j,')
    old='''if let Ok((rr, jj, _)) = system(trial) {
                let weak = norm <= 1e-12 && max(rr) <= 1e-12
                    && max(gaussian(w,jj, rr.map(|v| -v))?) < corr;'''
    new='''if let Ok(ss) = evaluate(trial) {
                let rr=residual(&ss);
                let weak = norm <= 1e-12 && max(rr) <= 1e-12
                    && max(gaussian(w,&jacobian(&ss), rr.map(|v| -v))?) < corr;'''
    assert source.count(old)==1;return source.replace(old,new)
if __name__=='__main__':
    path=ROOT/'crates/rf-d-circuit/src/hybrid_schur_voice.rs'
    path.write_text(transform(path.read_text(encoding='utf8')),encoding='utf8',newline='\n')
