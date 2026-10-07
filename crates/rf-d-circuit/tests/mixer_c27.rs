// Direct rustc target also compiles the exact production modules.
#[path = "../src/mixer_on.rs"]
mod mixer_on;
#[path = "../src/mixer_c27.rs"]
mod mixer_c27;
use mixer_on::{Error, OnMixer};
use mixer_c27::C27OnPort;

fn near(a: f64, b: f64, tol: f64) {
    assert!(a.is_finite() && b.is_finite() && (a-b).abs() <= tol,
        "{a:.17e} vs {b:.17e}, error {:.17e}, tolerance {tol:.3e}", (a-b).abs());
}

#[test]
fn c27_ports_match_full_resistor_and_history_nodes() {
    let text=include_str!("../../../evidence/voice_mixer_c27_vectors01.txt");
    let mut maxima=[0.0_f64;3];
    let mut count=0;
    for line in text.lines() {
        let x: Vec<f64>=line.split_whitespace().map(|s| s.parse().unwrap()).collect();
        assert_eq!(x.len(),58);
        let mask=x[0] as usize;
        let mixer=OnMixer::new(std::array::from_fn(|i| mask&(1<<i)!=0),std::array::from_fn(|i| x[1+i])).unwrap();
        let p=C27OnPort::new(mixer).unwrap();
        let result=p.evaluate(std::array::from_fn(|i| x[5+i]),x[10],x[11],x[12]).unwrap();
        for (a,b) in [(result.bus_v,x[13]),(result.capacitor_delta_v,x[56]),(result.next_capacitor_v,x[57])] {
            near(a,b,1e-10);maxima[0]=maxima[0].max((a-b).abs());
        }
        near(result.bus_kcl_residual_a,0.0,1e-13);
        for i in 0..6 {
            near(result.current_a[i],x[14+i],1e-13);
            maxima[1]=maxima[1].max((result.current_a[i]-x[14+i]).abs());
            for j in 0..6 {
                let expected=x[20+i*6+j];
                near(result.jacobian_s[i][j],expected,1e-12);
                maxima[2]=maxima[2].max((result.jacobian_s[i][j]-expected).abs());
            }
        }
        count+=1;
    }
    assert_eq!(count,837);
    println!("C27_ORACLE,cases={count},max_voltage_v={:.17e},max_current_a={:.17e},max_admittance_s={:.17e}",maxima[0],maxima[1],maxima[2]);
}

#[test]
fn coupled_jacobian_matches_finite_difference_and_is_passive() {
    for alpha in [0.0,1e-9,0.3,1.0-1e-9,1.0] {
        let p=C27OnPort::new(OnMixer::new([true;5],[alpha;4]).unwrap()).unwrap();
        for dt in [0.5e-6,20e-6,1e-3] {
            let v=[1.0,-0.7,0.3,0.2,0.5,-0.8];
            let r=p.evaluate(v[..5].try_into().unwrap(),v[5],0.4,dt).unwrap();
            for j in 0..6 {
                let mut plus=v;let mut minus=v;plus[j]+=1e-5;minus[j]-=1e-5;
                let a=p.evaluate(plus[..5].try_into().unwrap(),plus[5],0.4,dt).unwrap();
                let b=p.evaluate(minus[..5].try_into().unwrap(),minus[5],0.4,dt).unwrap();
                for i in 0..6 {
                    let fd=(a.current_a[i]-b.current_a[i])/2e-5;
                    near(fd,r.jacobian_s[i][j],1e-13+1e-7*fd.abs());
                    near(r.jacobian_s[i][j],r.jacobian_s[j][i],1e-15);
                }
            }
            for signs in 0..64 {
                let v: [f64;6]=std::array::from_fn(|i| if signs&(1<<i)==0 {-1.0} else {1.0});
                let mut power=0.0;
                for i in 0..6 { for j in 0..6 { power+=v[i]*r.jacobian_s[i][j]*v[j]; } }
                assert!(power>=-1e-14);
            }
        }
    }
}

#[test]
fn repeated_trials_freeze_charge_and_accepted_steps_conserve_energy() {
    let p=C27OnPort::new(OnMixer::new([true;5],[0.2,0.5,0.8,1.0]).unwrap()).unwrap();
    let source=[1.0,-0.3,0.7,-0.2,0.4];
    let mut history=0.6;
    let dt=20e-6;
    for step in 0..64 {
        let base=(step as f64*0.13).sin()*0.7;
        let result=p.evaluate(source,base,history,dt).unwrap();
        for _ in 0..20 {
            let trial=p.evaluate(source,base,history,dt).unwrap();
            assert_eq!(trial.next_capacitor_v.to_bits(),result.next_capacitor_v.to_bits());
            assert_eq!(trial.current_a[5].to_bits(),result.current_a[5].to_bits());
        }
        let dv=result.capacitor_delta_v;
        near(base-result.bus_v,result.next_capacitor_v,1e-14);
        near(10e-6/dt*dv,result.current_a[5],1e-15);
        let energy_delta=0.5*10e-6*dv*(2.0*history+dv);
        let euler_dissipation=0.5*10e-6*dv*dv;
        assert!(euler_dissipation>=0.0);
        let terminal_work=dt*(result.current_a[5]*base+(0..5).map(|i|result.current_a[i]*source[i]).sum::<f64>());
        near(terminal_work,result.mixer_dissipated_power_w*dt+energy_delta+euler_dissipation,1e-17);
        history=result.next_capacitor_v;
    }
}

#[test]
fn invalid_inputs_and_empty_network_are_rejected() {
    assert!(matches!(C27OnPort::new(OnMixer::new([false;5],[0.5;4]).unwrap()),Err(Error::FloatingBus)));
    let p=C27OnPort::new(OnMixer::new([true;5],[0.5;4]).unwrap()).unwrap();
    for dt in [0.0,-1.0,f64::NAN,f64::INFINITY] {
        assert!(matches!(p.evaluate([0.0;5],0.0,0.0,dt),Err(Error::InvalidInput)));
    }
    for bad in [f64::NAN,f64::INFINITY,f64::NEG_INFINITY] {
        assert!(p.evaluate([bad;5],0.0,0.0,1e-5).is_err());
        assert!(p.evaluate([0.0;5],bad,0.0,1e-5).is_err());
        assert!(p.evaluate([0.0;5],0.0,bad,1e-5).is_err());
    }
    assert!(matches!(p.evaluate([0.0;5],0.0,0.0,f64::from_bits(1)),Err(Error::ArithmeticDomain)));
    assert!(p.evaluate([1e308;5],-1e308,1e308,1e-5).is_err());
}
