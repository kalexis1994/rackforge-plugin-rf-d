"""Preserve lineage and derive a lab caller for 18 charge sensitivities."""
import base64,json,subprocess
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require

def caller():
    old=(ROOT/'tools/joint_charge_seed_runner.rs').read_text(encoding='utf8')
    prefix=old[:old.index('fn run()->Result<(),String> {')]
    return prefix+'''fn record(label:&str,id:usize,k:usize,h:f64,z:Aug,iterations:usize,trials:usize,res:f64,corr:f64,forcing:f64) {
 println!("{label},{id},{k},{h:.17e},{iterations},{trials},{res:.17e},{corr:.17e},{forcing:.17e}");state(z.x);
 print!("CHAIN_CURRENTS");for k in 0..K {print!(",{:.17e},{:.17e}",z.i.high[k],z.i.low[k]);}println!();
}
fn run()->Result<(),String> {
 let(p,seed)=scene()?;
 let rows:Vec<Vec<f64>>=include_str!("../evidence/voice_joint_charge_seed_targets01.txt").lines().map(|line|line.split_whitespace().map(|x|x.parse().unwrap()).collect()).collect();
 if rows.len()!=2||rows.iter().any(|r|r.len()!=36) {return Err("target codec".into());}
 for id in 0..2 {
  let target=std::array::from_fn(|k|(rows[id][2*k],rows[id][2*k+1]));
  let(z,it,tr,res,corr,f)=condition(p,seed,target).map_err(|e|format!("base:{id}:{e:?}"))?;
  record("RESPONSE_BASE",id,0,0.,z,it,tr,res,corr,f);
  let(_,matrix,_)=system(p,z,target).map_err(|e|format!("matrix:{e:?}"))?;
  for k in 0..K {
   let mut rhs=[0.;M];rhs[200+k]=1.;
   let d=solve(matrix,rhs).map_err(|e|format!("response:{id}:{k}:{e:?}"))?;
   print!("RESPONSE_COLUMN,{id},{k}");for value in d {print!(",{value:.17e}");}println!();
  }
  for k in 0..K {for h in [0.001,0.0005] {for sign in [-1.,1.] {
   let mut t=target;t[k]=add(t[k].0,t[k].1,sign*h);
   let(q,it,tr,res,corr,f)=condition(p,z.x,t).map_err(|e|format!("perturb:{id}:{k}:{h}:{sign}:{e:?}"))?;
   record("RESPONSE_PERTURB",id,k,sign*h,q,it,tr,res,corr,f);
  }}}
 }
 Ok(())
}
fn main() {if let Err(e)=run() {eprintln!("FAILURE,{e}");std::process::exit(1);}}
'''

def main():
    previous='evidence/voice_joint_seed_cycles_tests01.json';q=json.loads((ROOT/previous).read_text());require(q['passed'],'previous release')
    for key in ['source_sha256','private_input_sha256']:
        for n,h in q[key].items():require(sha(ROOT/n)==h,'protected '+n)
    names=['README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md','.gitattributes']
    write('evidence/voice_joint_charge_response_before01.json',dict(schema='rf-d/joint-charge-response-before/v1',base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),previous_qa_sha256=sha(ROOT/previous),mutable_before_base64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in names}))
    p=ROOT/'tools/joint_charge_response_runner.rs';require(not p.exists(),'exclusive caller');p.write_text(caller(),encoding='utf8',newline='\n')
    p=ROOT/'.gitattributes';p.write_bytes(p.read_bytes()+b'\n/tools/joint_charge_response_runner.rs text eol=lf\n')
    print('CHARGE_RESPONSE_PREPARED',len(q['source_sha256']),len(q['private_input_sha256']),flush=True)

if __name__=='__main__':main()
