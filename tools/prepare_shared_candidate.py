"""Compute/validate the full provisional HIGH/LOW state once per stage."""
from refine_hybrid_stamp import once
def transform(chain,contour,graph):
    a=chain.index('pub fn linearize(');b=chain.index('pub fn linearize_compensated<',a);chain=chain[:a]+chain[b:]
    chain=once(chain,'pub fn linearize_compensated<const FULL:bool>', 'pub fn linearize_prevalidated<const FULL:bool>')
    chain=once(chain,'delta:State,h:f64)->Result<Parts,StepError>', 'delta:State,h:f64,now:State)->Result<Parts,StepError>')
    a=chain.index(' if !h.is_finite()',chain.index('pub fn linearize_prevalidated'));b=chain.index(' let x:[f64;66]',a)
    chain=chain[:a]+''' // State/LOW canonicality belongs to the checked full-graph boundary.
 if !h.is_finite()||!(MIN_DT_S..=1e-3).contains(&h){return Err(StepError::InvalidInput);}
'''+chain[b:]
    contour=once(contour,'h: f64) -> Result<Parts<FULL>, StepError>', 'h: f64, now:State) -> Result<Parts<FULL>, StepError>')
    a=contour.index('    if !old.valid()',contour.index('pub fn parts<'));b=contour.index('    let mut s = dc(now, c)?;',a)
    contour=contour[:a]+'''    // old/delta/now were checked in the full 118-node stage boundary.
    if !h.is_finite()||h<=0.{return Err(StepError::InvalidInput);}
'''+contour[b:]
    contour=once(contour,'if !x.valid() || c.optional != x.optional ||', 'if c.optional != x.optional ||')
    old='''    let mut audio=chain_charge::linearize_compensated::<FULL>(p.chain,sources(t),old.chain(),delta.chain(),h)?;
    let dual=contour::parts::<FULL>(old.contour(),delta.contour(),c,h)?;
    let now=old.advanced(delta.high).advanced(delta.low);'''
    new='''    let now=old.advanced(delta.high).advanced(delta.low);
    if !now.valid(){return Err(StepError::InvalidInput);}
    let audio=chain_charge::linearize_prevalidated::<FULL>(p.chain,sources(t),old.chain(),delta.chain(),h,now.chain())?;
    let dual=contour::parts::<FULL>(old.contour(),delta.contour(),c,h,now.contour())?;'''
    graph=once(graph,old,new)
    return chain,contour,graph
