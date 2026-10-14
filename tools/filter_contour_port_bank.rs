pub use rf_d_circuit::StepError;
#[path = "../crates/rf-d-circuit/src/filter_contour_port.rs"]
mod port;
use port::*;
fn values(x: impl IntoIterator<Item = f64>) {
    for v in x {
        print!(",{v:.17e}");
    }
}
fn response(r: &Response) {
    values(r.next_state.node_v);
    values(r.port_current);
    values(r.port_jacobian.into_iter().flatten());
}
fn main() {
    let high = if std::env::args().any(|s| s == "--local") {
        0.851
    } else {
        3.0
    };
    for a in [0., 0.5, 1.] {
        for timing in [0., 0.85, 3., 6., 9.3] {
            for reset in [0.01, 0.7] {
                for cutoff in [0.5, 1.] {
                    let p = Parameters {
                        amount: a,
                        cutoff,
                        ..Parameters::default()
                    };
                    let b = boundary(timing, reset, 1.4, p);
                    let r = dc(p, b).expect("DC root");
                    assert!(r.residual_a <= 1e-11 && r.correction_v <= 1e-8);
                    print!("DC");
                    values([a, timing, reset, cutoff]);
                    response(&r);
                    let s = linearize(p, b, r.next_state.node_v, None).unwrap();
                    values(s.residual);
                    values(s.jacobian.into_iter().flatten());
                    values(s.node_port.into_iter().flatten());
                    values(s.port_node.into_iter().flatten());
                    values(s.port_port.into_iter().flatten());
                    println!();
                }
            }
        }
    }
    for c11 in [0., 47e-12] {
        for dt in [8e-6_f64, 4e-6_f64] {
            let p = Parameters {
                c11_f: c11,
                ..Parameters::default()
            };
            let mut s = dc(p, boundary(0.85, 0.01, 1.4, p)).unwrap().next_state;
            let mut replay = s;
            let steps = (128e-6 / dt).round() as usize;
            let mut ledger = [0.; 2];
            print!("START");
            values([c11, dt]);
            values(s.node_v);
            values(s.capacitor_v);
            println!();
            for k in 1..=steps {
                let clock = k * (dt * 1e9).round() as usize;
                let key = if clock <= 32000 || clock > 96000 {
                    0.85
                } else {
                    high
                };
                let b = boundary(key, 0.01, 1.4, p);
                let old = s;
                let candidate = provisional(&s, p, b, dt, 64).unwrap();
                assert_eq!(s, old);
                let r = step(&mut s, p, b, dt, 64).unwrap();
                let rr = step(&mut replay, p, b, dt, 64).unwrap();
                assert_eq!(s, replay);
                assert_eq!(
                    r.port_current.map(f64::to_bits),
                    rr.port_current.map(f64::to_bits)
                );
                assert_eq!(
                    r.port_jacobian.map(|row| row.map(f64::to_bits)),
                    rr.port_jacobian.map(|row| row.map(f64::to_bits))
                );
                assert_eq!(candidate.next_state, s);
                let q = [
                    c11 * (s.capacitor_v[0] - old.capacitor_v[0]),
                    100e-12 * (s.capacitor_v[1] - old.capacitor_v[1]),
                ];
                for i in 0..2 {
                    ledger[i] += q[i];
                }
                print!("STEP");
                values([c11, dt, k as f64, key]);
                response(&r);
                values(q);
                values([r.residual_a, r.correction_v]);
                let stamp = linearize(p, b, s.node_v, Some((old.capacitor_v, dt))).unwrap();
                values(stamp.jacobian.into_iter().flatten());
                values(stamp.node_port.into_iter().flatten());
                values(stamp.port_node.into_iter().flatten());
                values(stamp.port_port.into_iter().flatten());
                println!();
            }
            print!("LEDGER");
            values([c11, dt]);
            values(ledger);
            println!();
            for invalid in 0..6 {
                let mut test = s;
                let mut pp = p;
                let mut bb = boundary(0.85, 0.01, 1.4, p);
                let mut h = dt;
                let mut budget = 64;
                match invalid {
                    0 => pp.amount = f64::NAN,
                    1 => test.capacitor_v[0] = f64::NAN,
                    2 => h = 0.,
                    3 => budget = 0,
                    4 => bb[0] = 1e300,
                    _ => pp.c11_f = if c11 == 0. { 47e-12 } else { 0. },
                }
                let saved = test;
                assert!(step(&mut test, pp, bb, h, budget).is_err());
                assert!(
                    test.c11_f.to_bits() == saved.c11_f.to_bits()
                        && test.node_v.map(f64::to_bits) == saved.node_v.map(f64::to_bits)
                        && test.capacitor_v.map(f64::to_bits)
                            == saved.capacitor_v.map(f64::to_bits)
                );
            }
        }
    }
    println!("PASSED,60,96,24");
}
