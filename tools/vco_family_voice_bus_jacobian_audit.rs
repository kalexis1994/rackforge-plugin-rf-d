use crate::{graph, incidence::{Row, Tangent}, original_graph, original_solver, solver, voice, StepError};
use voice::{Accepted, Controls, Parameters, State, B, M, N};

pub fn contact(old: State, controls: Controls, h: f64, q: &Accepted) -> Result<(), String> {
    let state = |s: State| original_graph::State { high: s.high, low: s.low, optional: s.optional };
    let c = original_graph::Controls { key: controls.key, short: controls.short, optional: controls.optional };
    let bits = |(k, g, m): (usize, f64, f64)| (k, g.to_bits(), m.to_bits());
    for position in [0., 2500., 5000.] {
        let mut params = crate::parameters();
        params.boundary.recovery.vca.second.output.output.r21_lower_ohm = position;
        let current = Parameters::new(params).map_err(|e| format!("{e:?}"))?;
        let original = original_graph::Parameters::new(params).map_err(|e| format!("{e:?}"))?;
        for delta in q.delta {
            let a = graph::parts::<true>(current, old, delta, controls, h, 0.).map_err(|e| format!("{e:?}"))?;
            let b = original_graph::parts::<true>(original, state(old), state(delta), c, h, 0.)
                .map_err(|e| format!("{e:?}"))?;
            assert_eq!(a.dc.map(f64::to_bits), b.dc.map(f64::to_bits));
            assert_eq!(a.dq.map(f64::to_bits), b.dq.map(f64::to_bits));
            for row in 0..N {
                assert!(a.tangent.entries(row).map(bits).eq(b.tangent.entries(row).map(bits)), "R21 {position} row {row}");
            }
        }
    }
    println!("CONTACT,6");
    Ok(())
}

fn fixture(singular: bool) -> Tangent {
    let mut tangent = Tangent::new();
    for k in 0..N {
        let mut row = Row::new();
        match k {
            0 => {
                row.set(k, 1e-6, 0.).unwrap();
                row.set(1, 4., 0.).unwrap();
                row.set(54, 0.25, 0.).unwrap();
            }
            1 => {
                row.set(0, 3., 0.).unwrap();
                row.set(k, -1., 0.).unwrap();
            }
            54 => {
                row.set(0, 0.125, 0.).unwrap();
                row.set(k, 2., 0.0625).unwrap();
                row.set(56, -0.25, 0.).unwrap();
            }
            56 => {
                row.set(54, 0.25, 0.).unwrap();
                row.set(k, 2., 0.125).unwrap();
            }
            117 => row.set(k, if singular { 0. } else { 0.5 }, 0.).unwrap(),
            _ => row.set(k, 2., 0.03125).unwrap(),
        }
        tangent.push_row(k, &mut row).unwrap();
    }
    tangent
}

pub fn linear() {
    let normal = fixture(false);
    let singular = fixture(true);
    let normal_rhs = std::array::from_fn(|i| (i as f64 - 80.) * 1e-9);
    let mut overflow = [0.; M];
    overflow[M - 1] = f64::MAX;
    let signed_zero = std::array::from_fn(|i| if i % 2 == 0 { -0. } else { 0. });
    let mut candidate = solver::Workspace::new();
    let mut reference = original_solver::Workspace::new();
    let cases = [
        (&normal, normal_rhs, None),
        (&normal, signed_zero, None),
        (&normal, overflow, Some(StepError::SingularJacobian)),
        (&normal, normal_rhs, None),
        (&singular, normal_rhs, Some(StepError::SingularJacobian)),
        (&normal, normal_rhs, None),
    ];
    for (matrix, rhs, error) in cases {
        let a = candidate.solve([solver::Stage { tangent: matrix }; 2], B, rhs);
        let b = reference.solve([original_solver::Stage { tangent: matrix }; 2], B, rhs);
        assert_eq!(a.as_ref().err(), error.as_ref());
        assert_eq!(a.map(|x| x.map(f64::to_bits)), b.map(|x| x.map(f64::to_bits)));
    }
    println!("LINEAR_GUARD,4,2");
}
