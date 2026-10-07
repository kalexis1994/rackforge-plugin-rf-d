use rf_d_circuit::{circuit66,mixer_chain_port::solve_input_port,mixer_on::OnMixer,SolverBudget};
#[allow(dead_code)]
#[path="support/mixer_chain_lab.rs"]mod lab;
fn near(a:f64,b:f64,t:f64) {assert!(a.is_finite() && b.is_finite() && (a-b).abs()<t,"{a:.17e} vs {b:.17e} tolerance {t:.3e}");}
fn rows()->Vec<Vec<f64>> {
    include_str!("../../../evidence/voice_mixer_chain_port_vectors01.txt").lines()
        .map(|line|line.split_whitespace().map(|x|x.parse().unwrap()).collect()).collect()
}

#[test]
fn loaded_source_tangents_match_uneliminated_nodal_roots() {
    let(base,c,h)=lab::lab_parameters();let mut worst_y=0.0_f64;let mut worst_dx=0.0_f64;
    for row in rows() {
        assert_eq!(row.len(),528);let mut p=base;p.r61_ohm=row[0];let mask=row[1] as usize;
        let mixer=OnMixer::new(std::array::from_fn(|i|mask&(1<<i)!=0),std::array::from_fn(|i|row[2+i])).unwrap();
        let mut b=lab::controlled_boundary(0,true);b.recovery.vca.second.output.output.dt_s=row[6];
        let old=circuit66::State{node_v:row[12..78].try_into().unwrap(),previous_node_v:row[12..78].try_into().unwrap(),
            capacitor_v:row[78..95].try_into().unwrap(),c10_capacitor_v:row[95]};
        let saved=old;let source=row[7..12].try_into().unwrap();
        let port=solve_input_port(&old,mixer,source,p,c,h,b,SolverBudget::default()).unwrap();assert_eq!(old,saved);
        for i in 0..66 {near(port.next_state.node_v[i],row[96+i],1e-6);}
        near(port.result.mixer.bus_v,row[162],1e-6);
        for i in 0..5 {
            near(port.current_a[i],row[163+i],1e-9);
            for j in 0..5 {
                let expected=row[168+i*5+j];let error=(port.admittance_s[i][j]-expected).abs();worst_y=worst_y.max(error);
                near(port.admittance_s[i][j],expected,1e-8+1e-3*expected.abs());
            }
        }
        for i in 0..66 {for j in 0..5 {let expected=row[193+i*5+j];worst_dx=worst_dx.max((port.node_gradient_v_per_v[i][j]-expected).abs());
            near(port.node_gradient_v_per_v[i][j],expected,1e-6+1e-3*expected.abs());}}
        for j in 0..5 {near(port.bus_gradient_v_per_v[j],row[523+j],1e-6+1e-3*row[523+j].abs());}
        let repeat=solve_input_port(&old,mixer,source,p,c,h,b,SolverBudget::default()).unwrap();
        assert_eq!(repeat.next_state,port.next_state);assert_eq!(repeat.current_a,port.current_a);assert_eq!(old,saved);
    }
    println!("LOADED_PORT,cases=4,max_admittance_delta_s={worst_y:.17e},max_node_gradient_delta={worst_dx:.17e}");
}

#[test]
fn omitted_sources_and_rejection_preserve_incoming_history() {
    let(p,c,h)=lab::lab_parameters();let b=lab::controlled_boundary(0,true);
    let m=OnMixer::new([true,false,false,false,false],[0.5;4]).unwrap();
    let old=rf_d_circuit::mixer_chain66::initial_state(m,[0.;5],p,c,h,b,lab::SEED).unwrap();let saved=old;
    let port=solve_input_port(&old,m,[0.01;5],p,c,h,b,SolverBudget::default()).unwrap();
    for j in 1..5 {
        assert_eq!(port.current_a[j],0.0);
        for i in 0..5 {assert_eq!(port.admittance_s[i][j],0.0);assert_eq!(port.admittance_s[j][i],0.0);}
        for i in 0..66 {assert_eq!(port.node_gradient_v_per_v[i][j],0.0);}
        assert_eq!(port.bus_gradient_v_per_v[j],0.0);
    }
    assert!(solve_input_port(&old,m,[1.;5],p,c,h,b,SolverBudget{iterations:1,line_search_halvings:1}).is_err());
    assert_eq!(old,saved);
}
