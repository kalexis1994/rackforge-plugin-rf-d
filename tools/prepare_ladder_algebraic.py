"""Isolate admitted ladder laws and snapshot the unchanged parent admission."""
import base64,subprocess
from prepare_dual_chain import ROOT,sha,write
from prepare_hybrid_stamp import once
def derive():
    source=(ROOT/'crates/rf-d-circuit/src/prepared_audio_stamp.rs').read_text(encoding='utf8')
    s=source[source.index('const N: usize = 66;'):source.index('const R20_OHM:')].replace('const N: usize = 66;','const N: usize = 16;')
    s=once(s,'    j: [[f64; N]; N],','    j: [[f64; N]; N],\n    fixed:[f64;2],fixed_j:[[f64;N];2],')
    marker='''                }
            }
        }
    }
    fn resistor'''
    s=once(s,marker,'''                }
            }else if let Fixed(v)=terminal{
                let k=if v==0.{0}else{1};self.fixed[k]+=sign*current;
                for(other,slope)in[(left,g),(right,-g)]{if let Node(col)=other{self.fixed_j[k][col]+=sign*slope;}}
            }
        }
    }
    fn resistor''')
    marker='''                let mut v=0.;for col in 0..3{v+=slopes[row][col]*self.low(terminals[col]);}self.r[i]+=v;

            }
'''
    s=once(s,marker,'''                let mut v=0.;for col in 0..3{v+=slopes[row][col]*self.low(terminals[col]);}self.r[i]+=v;
            }else if let Fixed(v)=terminals[row]{
                let k=if v==0.{0}else{1};self.fixed[k]+=polarity*[ib,ic,-ib-ic][row];
                let mut low=0.;for col in 0..3{low+=slopes[row][col]*self.low(terminals[col]);if let Node(a)=terminals[col]{self.fixed_j[k][a]+=slopes[row][col];}}self.fixed[k]+=low;
            }
''')
    body=source[source.index('    let mut s = Stamp::<FULL> {'):source.index('    // Recovery Q8/Q6/Q7/Q5.')]
    body=once(body,'        j: [[0.0; N]; N],','        j: [[0.0; N]; N],fixed:[0.;2],fixed_j:[[0.;N];2],')
    a=body.index('    let vb = ');b=body.index('    // Ladder,',a);body=body[:a]+body[b:]
    out='''//! Isolated original ladder laws; LADDER_ALGEBRAICO_PROTOCOLO.
use rf_d_circuit::{vca2_output::Parameters as Bjt,StepError};
pub use rf_d_circuit::cutoff_ladder_output::Parameters;
'''+s+'''pub struct Linear{pub dc:[f64;N],pub j:[[f64;N];N],pub fixed:[f64;2],pub fixed_j:[[f64;N];2]}
pub fn linearize(p:Parameters,x:&[f64;N],low:&[f64;N])->Result<Linear,StepError>{
 if x.iter().chain(low.iter()).any(|v|!v.is_finite()){return Err(StepError::InvalidInput);}
'''+body.replace('Stamp::<FULL>','Stamp::<true>')+'''
 if s.r.iter().chain(s.j.iter().flatten()).chain(s.fixed.iter()).chain(s.fixed_j.iter().flatten()).any(|v|!v.is_finite()){return Err(StepError::ExponentialDomain);}
 Ok(Linear{dc:s.r,j:s.j,fixed:s.fixed,fixed_j:s.fixed_j})
}
'''
    return {'crates/rf-d-circuit/src/ladder_algebraic_stamp.rs':out}
def main():
    before=ROOT/'evidence/ladder_algebraic_before01.json';assert not before.exists();sources=derive();assert not any((ROOT/n).exists() for n in sources)
    previous='evidence/hybrid_compact_tests01.json'
    mutable=['.gitattributes','README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md','docs/LADDER_REDUCCION_ALGEBRAICA_PLAN.md']
    write(before,dict(base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),previous_qa=previous,previous_qa_sha256=sha(ROOT/previous),mutable_original_b64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in mutable}))
    for n,s in sources.items():(ROOT/n).write_text(s,encoding='utf8',newline='\n')
if __name__=='__main__':main()
