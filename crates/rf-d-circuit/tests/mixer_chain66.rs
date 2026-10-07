use rf_d_circuit::{circuit66, mixer_chain66 as joint, mixer_on::OnMixer, SolverBudget};
#[allow(dead_code)]
#[path="support/mixer_chain_lab.rs"]
mod lab;
fn rows()->Vec<Vec<f64>> {
    include_str!("../../../evidence/voice_mixer_chain_vectors01.txt").lines()
        .map(|line|line.split_whitespace().map(|x|x.parse().unwrap()).collect()).collect()
}
fn near(a:f64,b:f64,t:f64) {assert!(a.is_finite() && b.is_finite() && (a-b).abs()<t,"{a:.17e} vs {b:.17e} tol {t:.3e}");}
fn mixer(row:&[f64])->OnMixer {
    let mask=row[1] as usize;
    OnMixer::new(std::array::from_fn(|i|mask&(1<<i)!=0),std::array::from_fn(|i|row[2+i])).unwrap()
}

#[test]
fn full_nodal_oracle_matches_loaded_chain_and_all_memories() {
    let rows=rows();assert_eq!(rows.len(),64);
    let (base,c,h)=lab::lab_parameters();let mut worst_v=0.0_f64;let mut worst_i=0.0_f64;
    for case in rows.chunks(16) {
        let mut p=base;p.r61_ohm=case[0][0];let mut b=lab::controlled_boundary(0,true);b.bus_v=0.;b.recovery.vca.second.output.output.dt_s=case[0][6];
        let m=mixer(&case[0]);let mut state=joint::initial_state(m,[0.;5],p,c,h,b,lab::SEED).unwrap();
        for i in 0..66 {near(state.node_v[i],case[0][12+i],1e-6);}
        for row in case {
            assert_eq!(row.len(),187);let old=state;
            let result=joint::step(&mut state,m,row[7..12].try_into().unwrap(),p,c,h,b,SolverBudget::default()).unwrap();
            for i in 0..66 {let error=(state.node_v[i]-row[96+i]).abs();worst_v=worst_v.max(error);near(state.node_v[i],row[96+i],1e-6);}
            near(result.mixer.bus_v,row[162],1e-6);
            for i in 0..17 {near(state.capacitor_v[i],row[163+i],1e-6);}
            near(state.c10_capacitor_v,row[180],1e-6);
            for i in 0..6 {near(result.mixer.current_a[i],row[181+i],1e-9);worst_i=worst_i.max((result.mixer.current_a[i]-row[181+i]).abs());}
            near(result.chain.output.j7_v,state.node_v[61],1e-15);
            let low=1.0/(1.0/1000.0+1.0/100000.0);
            let wiper=1.0/(1.0/2500.0+1.0/10000.0+1.0/(33000.0+low));
            let hi=row[96+47]*wiper/(3500.0+wiper);
            near(result.chain.output.j4_hi_v,hi,1e-6);
            near(result.chain.output.j5_lo_v,hi*low/(33000.0+low),1e-6);
            assert!(result.chain.output.max_ladder_kcl_residual_a<1e-11);
            assert!(result.correction_v<1e-8);
            near(result.mixer.current_a[5],10e-6/b.recovery.vca.second.output.output.dt_s*(state.capacitor_v[5]-old.capacitor_v[5]),1e-13);
        }
    }
    println!("CHAIN_ORACLE,cases=4,steps=64,max_node_v={worst_v:.17e},max_current_a={worst_i:.17e}");
}

#[test]
fn all_coupled_jacobian_columns_match_fixed_history_differences() {
    let rows=rows();let(base,c,h)=lab::lab_parameters();
    for case in rows.chunks(16) {
        let row=&case[3];let mut p=base;p.r61_ohm=row[0];let mut b=lab::controlled_boundary(0,true);b.bus_v=0.;b.recovery.vca.second.output.output.dt_s=row[6];
        let old=circuit66::State {node_v:row[12..78].try_into().unwrap(),previous_node_v:row[12..78].try_into().unwrap(),
            capacitor_v:row[78..95].try_into().unwrap(),c10_capacitor_v:row[95]};
        let m=mixer(row);let source=row[7..12].try_into().unwrap();let x:[f64;66]=row[96..162].try_into().unwrap();
        let (_,j,_)=joint::linearize(&old,m,source,p,c,h,b,&x).unwrap();
        for column in 0..66 {
            let mut plus=x;let mut minus=x;plus[column]+=1e-6;minus[column]-=1e-6;
            let (rp,_,_)=joint::linearize(&old,m,source,p,c,h,b,&plus).unwrap();
            let (rm,_,_)=joint::linearize(&old,m,source,p,c,h,b,&minus).unwrap();
            for i in 0..66 {let fd=(rp[i]-rm[i])/2e-6;near(j[i][column],fd,1e-8+2e-5*fd.abs());}
        }
    }
}

#[test]
fn failed_coupled_solve_preserves_incoming_state() {
    let(p,c,h)=lab::lab_parameters();let b=lab::controlled_boundary(0,true);let m=OnMixer::new([true;5],[0.5;4]).unwrap();
    let mut state=joint::initial_state(m,[0.;5],p,c,h,b,lab::SEED).unwrap();let old=state;
    assert!(joint::step(&mut state,m,[1.;5],p,c,h,b,SolverBudget{iterations:1,line_search_halvings:1}).is_err());
    assert_eq!(state,old);
    for bad in [0.,1e-8,0.002,f64::NAN] {
        let mut invalid=b;invalid.recovery.vca.second.output.output.dt_s=bad;
        assert!(joint::step(&mut state,m,[0.;5],p,c,h,invalid,SolverBudget::default()).is_err());assert_eq!(state,old);
    }
}
