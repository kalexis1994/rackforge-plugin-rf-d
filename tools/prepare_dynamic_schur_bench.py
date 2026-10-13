"""Build a paired benchmark; preserve new roots for the independent full graph."""
from prepare_vco1_portable import ROOT
from joint_cycles_analysis import require
MAIN='''fn compare(a:&(Vec<u64>,usize,usize),b:&(Vec<u64>,usize,usize))->f64{
 let mut worst=0_f64;for block in 0..4{for k in 0..229{let q=block*458;let ah=f64::from_bits(a.0[q+k]);let al=f64::from_bits(a.0[q+k+229]);let bh=f64::from_bits(b.0[q+k]);let bl=f64::from_bits(b.0[q+k+229]);let diff=(ah-bh)+(al-bl);let ratio=diff.abs()/if(98..133).contains(&k){2e-9}else{2e-6};worst=worst.max(ratio);}}
 assert!(worst<=1.,"full candidate/increment gate {worst}");assert!(f64::from_bits(b.0[1832])<=1.&&f64::from_bits(b.0[1833])<=1.,"original Newton gates");worst
}
fn save(w:&mut impl std::io::Write,c:&Case,q:&(Vec<u64>,usize,usize)){
 writeln!(w,"SCENE,{},{}",c.on as u32,c.phase).unwrap();writeln!(w,"JOINT_ROOT,0,{:.17e},{:.17e},{:.17e}",c.h,f64::from_bits(q.0[1832]),f64::from_bits(q.0[1833])).unwrap();write!(w,"JOINT_STATE").unwrap();for v in c.states[0]{write!(w,",{v:.17e}").unwrap();}writeln!(w).unwrap();for block in 0..4{write!(w,"JOINT_STATE").unwrap();for &v in &q.0[block*458..(block+1)*458]{write!(w,",{:.17e}",f64::from_bits(v)).unwrap();}writeln!(w).unwrap();}
}
fn main(){
 let args:Vec<_>=std::env::args().collect();let cs=cases(&args[1]);assert_eq!(cs.len(),84);let mut expected=Vec::new();let mut file=std::fs::File::create(&args[2]).unwrap();
 for(i,c)in cs.iter().enumerate(){let a=run_reference(c);assert_eq!(a.0,stored(c),"reference stored bits");let b=run_reuse(c);let error=compare(&a,&b);save(&mut file,c,&b);println!("CASE,{i},{},{},{:.17e},{},{},{},{},{error:.17e}",c.on as u32,c.phase,c.h,a.1,a.2,b.1,b.2);expected.push(a);}
 for round in 0..5{let reference=|cs:&[Case]|{let t=Instant::now();for(c,e)in cs.iter().zip(&expected){assert_eq!(&run_reference(c),e);}t.elapsed().as_nanos()};let reduced=|cs:&[Case]|{let t=Instant::now();for(c,e)in cs.iter().zip(&expected){compare(e,&run_reuse(c));}t.elapsed().as_nanos()};let(a,b)=if round%2==0{(reference(&cs),reduced(&cs))}else{let b=reduced(&cs);(reference(&cs),b)};println!("ROUND,{round},{a},{b}");}
 println!("PASSED,84,5,reconstructed_candidate_gates");
}
'''
def main():
 s=(ROOT/'tools/lu_extent_bench.rs').read_text(encoding='utf8').split('fn main(){')[0];s=s.replace('../references-local/lu-extent-inputs01/reference_profile.rs','joint_lu_extent_kernel.rs').replace('../references-local/lu-extent-inputs01/reuse_profile.rs','joint_dynamic_schur_kernel.rs');s+=MAIN;p=ROOT/'tools/dynamic_schur_bench.rs';require(not p.exists(),'exclusive benchmark source');p.write_text(s,encoding='utf8',newline='\n')
if __name__=='__main__':main()
