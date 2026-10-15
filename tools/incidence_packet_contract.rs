pub use rf_d_circuit::{StepError,junction_charge};
#[path="../crates/rf-d-circuit/src/active_nominal_voice.rs"]mod selected;
#[path="../crates/rf-d-circuit/src/direct_hybrid_voice.rs"]mod previous;
use selected::incidence::{Tangent,Row,N};
fn finish(row:Row)->Tangent{let mut t=Tangent::new();let mut row=row;t.push_row(0,&mut row).unwrap();for a in 1..N{t.push_row(a,&mut Row::new()).unwrap();}t}
fn main(){
    let mut row=Row::new();row.set(117,1.,0.).unwrap();row.set(7,2.,4.).unwrap();row.set(7,8.,16.).unwrap();row.set(0,32.,64.).unwrap();row.add(7,2.,4.).unwrap();
    let mut t=finish(row);assert_eq!(t.entries(0).collect::<Vec<_>>(),vec![(0,32.,64.),(7,10.,20.),(117,1.,0.)]);
    t.add(0,50,4.,8.).unwrap();t.add(0,1,16.,32.).unwrap();t.add(0,50,2.,4.).unwrap();
    assert_eq!(t.entries(0).collect::<Vec<_>>(),vec![(0,32.,64.),(1,16.,32.),(7,10.,20.),(50,6.,12.),(117,1.,0.)]);
    t.add(0,50,-6.,-12.).unwrap();assert_eq!(t.entries(0).map(|(k,_,_)|k).collect::<Vec<_>>(),vec![0,1,7,117]);
    assert!((1..N).all(|a|t.entries(a).count()==0));
    t.add(N-1,118-1,1.,2.).unwrap();t.add(54,55,3.,4.).unwrap();t.add(54,54,5.,6.).unwrap();
    assert_eq!(t.entries(54).collect::<Vec<_>>(),vec![(54,5.,6.),(55,3.,4.)]);assert_eq!(t.entries(N-1).collect::<Vec<_>>(),vec![(N-1,1.,2.)]);
    let mut row=Row::new();row.add(4,1.,2.).unwrap();row.add(4,-1.,-2.).unwrap();let t=finish(row);assert_eq!(t.entries(0).count(),0);
    let old=std::mem::size_of::<previous::Parts>();let new=std::mem::size_of::<selected::Parts>();assert!(new<old);
    println!("PACKET,7,{old},{new},{}",std::mem::size_of::<Tangent>());
}
