"""Derive a compensated residual-only audio path for line-search trials."""
def once(s,a,b):
    assert s.count(a)==1,a[:100]
    return s.replace(a,b)
def transform(audio,chain,graph,voice):
    audio=audio.replace("struct Stamp<'a> {", "struct Stamp<'a,const FULL:bool> {")
    audio=once(audio,"    x: &'a [f64; N],","    x: &'a [f64; N],\n    low: &'a [f64;N],")
    audio=once(audio,"impl<'a> Stamp<'a> {", "impl<'a,const FULL:bool> Stamp<'a,FULL> {")
    audio=once(audio,'    fn branch(&mut self, left: Terminal, right: Terminal, current: f64, g: f64) {', '''    fn low(&self,t:Terminal)->f64{match t{Node(k)=>self.low[k],Fixed(_)=>0.}}
    fn branch(&mut self, left: Terminal, right: Terminal, current: f64, g: f64) {
        let current=if FULL{current}else{current+g*(self.low(left)-self.low(right))};''')
    old='''                for (other, slope) in [(left, g), (right, -g)] {
                    if let Node(k) = other {
                        self.j[POSITION[i]][POSITION[k]] += sign * slope;
                    }
                }'''
    audio=once(audio,old,'                if FULL {\n'+old+'\n                }')
    old='''                for col in 0..3 {
                    if let Node(k) = terminals[col] {
                        self.j[POSITION[i]][POSITION[k]] += slopes[row][col];
                    }
                }'''
    audio=once(audio,old,'''                if FULL {
'''+old+'''
                }else{let mut v=0.;for col in 0..3{v+=slopes[row][col]*self.low(terminals[col]);}self.r[i]+=v;}
''')
    audio=once(audio,'fn evaluate(\n    x: &[f64; N],','fn evaluate<const FULL:bool>(\n    x: &[f64; N],\n    low: &[f64;N],')
    audio=once(audio,'    let mut s = Stamp {\n        x,','    let mut s = Stamp::<FULL> {\n        x,low,')
    audio=once(audio,'        s.r[49] = r21_constraint(x, ob.r21_lower_ohm);','        s.r[49] = r21_constraint(x, ob.r21_lower_ohm);\n        if !FULL{s.r[49]+=if ob.r21_lower_ohm==5000.{low[49]-low[48]}else{low[49]};}')
    audio=once(audio,'    if s.r\n        .iter()\n        .chain(s.j.iter().flatten())\n        .any(|v| !v.is_finite())','    if s.r.iter().any(|v|!v.is_finite()) || (FULL && s.j.iter().flatten().any(|v|!v.is_finite()))')
    audio=once(audio,'pub fn linearize(self,x:&[f64;N])','pub fn linearize<const FULL:bool>(self,x:&[f64;N],low:&[f64;N])')
    audio=once(audio,'let(r,j)=evaluate(x,self.p,','let(r,j)=evaluate::<FULL>(x,low,self.p,')
    chain=once(chain,' linearize_compensated(p,sources,old,State::from_nodes(delta),h)',' linearize_compensated::<true>(p,sources,old,State::from_nodes(delta),h)')
    chain=once(chain,'pub fn linearize_compensated(', 'pub fn linearize_compensated<const FULL:bool>(')
    chain=once(chain,'let(r,j)=p.audio.linearize(&x)?;','let low=std::array::from_fn(|k|now.low[k]);let(r,j)=p.audio.linearize::<FULL>(&x,&low)?;')
    chain=once(chain,'for a in 0..66 {jac[a][..66].copy_from_slice(&j[a]);}','if FULL{for a in 0..66 {jac[a][..66].copy_from_slice(&j[a]);}}')
    chain=once(chain,'for a in 0..N {dc[a]+=(0..N).map(|b|jac[a][b]*now.low[b]).sum::<f64>();}', 'for a in 0..N {if FULL||a==22||a==C10_LEFT||a==BUS{dc[a]+=(0..N).map(|b|jac[a][b]*now.low[b]).sum::<f64>();}}')
    chain=once(chain,'q[r]+=sign*i;for (col,slope) in [(a,g),(b,-g)] {if col!=GROUND {mass[r][col]+=sign*slope;}}','q[r]+=sign*i;if FULL{for (col,slope) in [(a,g),(b,-g)] {if col!=GROUND {mass[r][col]+=sign*slope;}}}')
    graph=once(graph,'pub fn parts(', 'pub fn parts<const FULL:bool>(')
    graph=once(graph,'chain_charge::linearize_compensated(', 'chain_charge::linearize_compensated::<FULL>(')
    graph=once(graph,'for b in 0..56{let g=', 'if FULL{for b in 0..56{let g=')
    graph=once(graph,'s.mass[a][b]=m;}}','s.mass[a][b]=m;}}}')
    graph=once(graph,'for b in 0..68 {let j=', 'if FULL{for b in 0..68 {let j=')
    graph=once(graph,'!s.mass[i][j].is_finite(){return Err(StepError::ExponentialDomain);}}}', '!s.mass[i][j].is_finite(){return Err(StepError::ExponentialDomain);}}}}')
    graph=once(graph,'{parts(p,x,', '{parts::<true>(p,x,')
    voice=once(voice,'pub fn parts(', 'pub fn parts<const FULL:bool>(')
    voice=once(voice,'graph::parts(', 'graph::parts::<FULL>(')
    voice=once(voice,'    s.j[116][116]+=y;', '    if FULL{s.j[116][116]+=y;}')
    voice=voice.replace('parts(p,old,','parts::<true>(p,old,')
    marker='    for iteration in 1..=budget {'
    extra='''    let evaluate_residual = |d:[State;2]|->Result<[f64;M],StepError>{
        let s=[parts::<false>(p,old,d[0],c,h,p.time+h/3.)?,parts::<false>(p,old,d[1],c,h,p.time+h)?];Ok(residual(&s))
    };
'''
    voice=once(voice,marker,extra+marker)
    a=voice.index('            if let Ok(ss) = evaluate(trial) {');b=voice.index('        if !found {',a)
    voice=voice[:a]+'''            let merit=if norm<=1e-12{
                if let Ok(ss)=evaluate(trial){let rr=residual(&ss);let weak=max(rr)<=1e-12&&max(gaussian(w,&jacobian(&ss),rr.map(|v|-v))?)<corr;Some((max(rr),weak))}else{None}
            }else{evaluate_residual(trial).ok().map(|rr|(max(rr),false))};
            if let Some((next,weak))=merit{if next<norm||weak{d=trial;found=true;break;}}
        }
'''+voice[b:]
    audio=once(audio,'fn evaluate<const FULL:bool>(', '#[inline(always)]\nfn evaluate<const FULL:bool>(')
    audio=once(audio,' pub fn linearize<const FULL:bool>(', ' #[inline(always)]\n pub fn linearize<const FULL:bool>(')
    chain=once(chain,'pub fn linearize_compensated<const FULL:bool>(', '#[inline(always)]\npub fn linearize_compensated<const FULL:bool>(')
    graph=once(graph,'pub fn parts<const FULL:bool>(', '#[inline(always)]\npub fn parts<const FULL:bool>(')
    voice=once(voice,'pub fn parts<const FULL:bool>(', '#[inline(always)]\npub fn parts<const FULL:bool>(')
    voice=once(voice,'fn max<const S:usize>', '''pub fn residual_parts(p:Parameters,old:State,delta:State,c:Controls,h:f64,t:f64)->Result<([f64;N],[f64;N]),StepError>{
    let s=parts::<false>(p,old,delta,c,h,t)?;Ok((s.dc,s.dq))
}
fn max<const S:usize>''')
    voice=once(voice,'let s=[parts::<false>(p,old,d[0],c,h,p.time+h/3.)?,parts::<false>(p,old,d[1],c,h,p.time+h)?];Ok(residual(&s))', '''let(a,qa)=residual_parts(p,old,d[0],c,h,p.time+h/3.)?;let(b,qb)=residual_parts(p,old,d[1],c,h,p.time+h)?;
        let mut r=[0.;M];for k in 0..N{r[k]=a[k]+B[0][0]*qa[k]+B[0][1]*qb[k];r[N+k]=b[k]+B[1][0]*qa[k]+B[1][1]*qb[k];}Ok(r)''')
    return audio,chain,graph,voice
