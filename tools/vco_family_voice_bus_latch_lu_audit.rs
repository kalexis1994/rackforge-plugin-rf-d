use crate::{incidence::{Row, Tangent}, original_solver, solver, StepError};
use crate::voice::{B, M, N};

#[path = "OLD_LATCH_PATH"]
mod old;
#[path = "NEW_LATCH_PATH"]
mod new;

pub fn junction() {
    let values: [f64; 6] = [-0.7, -0.0, 0.25, 0.28, 0.30, 0.6];
    let mut valid = 0;
    for (old_law, new_law, tau, splice) in [
        (old::BE, new::BE, 1e-9, 0.4 * 0.75),
        (old::BC, new::BC, 3e-9, 0.4 * 0.7),
    ] {
        let splice: f64 = splice;
        let bits = splice.to_bits();
        for a in values.into_iter().chain([f64::from_bits(bits - 1), splice, f64::from_bits(bits + 1)]) {
            for b in values.into_iter().chain([f64::from_bits(bits - 1), splice, f64::from_bits(bits + 1)]) {
                let from = (a, -1e-18);
                let to = (b, 1e-18);
                let left = old::junction(old_law, tau, from, to).unwrap();
                let right = new::junction(new_law, tau, from, to).unwrap();
                assert_eq!((left.0.to_bits(), left.1.to_bits()), (right.0.to_bits(), right.1.to_bits()));
                valid += 1;
            }
        }
    }
    for (from, to, tau) in [
        ((1.4, 0.), (0.1, 0.), 1e-9),
        ((0.1, 0.), (1.4, 0.), 1e-9),
        ((f64::NAN, 0.), (0.1, 0.), 1e-9),
        ((0.1, 0.), (-41., 0.), 1e-9),
        ((0.1, f64::INFINITY), (0.1, 0.), 1e-9),
        ((0.1, 0.), (0.1, 0.), -1e-9),
    ] {
        let reference = old::junction(old::BE, tau, from, to);
        let candidate = new::junction(new::BE, tau, from, to);
        assert_eq!(reference, Err(StepError::ExponentialDomain));
        assert_eq!(reference, candidate);
    }
    println!("JUNCTION_GUARD,{valid},6");
}

pub fn active() {
    let mut candidate = solver::Workspace::new();
    let mut reference = original_solver::Workspace::new();
    for lead in [0., 1e-6] {
        let mut matrix = Tangent::new();
        for i in 0..N {
            let mut row = Row::new();
            match i {
                0 => {
                    row.set(0, lead, 0.).unwrap();
                    row.set(1, 4., 0.).unwrap();
                    row.set(54, -0.5, 0.).unwrap();
                }
                1 => {
                    row.set(0, 3., 0.).unwrap();
                    row.set(1, -1., 0.).unwrap();
                    row.set(2, -0.75, 0.).unwrap();
                }
                2 => {
                    row.set(0, 0.25, 0.).unwrap();
                    row.set(2, 1., 0.03125).unwrap();
                }
                _ => row.set(i, 2., 0.03125).unwrap(),
            }
            matrix.push_row(i, &mut row).unwrap();
        }
        for rhs in [
            std::array::from_fn(|i| (i as f64 - 17.) * 1e-9),
            std::array::from_fn(|i| if i % 2 == 0 { -0. } else { 0. }),
        ] {
            let trial: [f64; M] = candidate.solve([solver::Stage { tangent: &matrix }; 2], B, rhs).unwrap();
            let exact = reference.solve([original_solver::Stage { tangent: &matrix }; 2], B, rhs).unwrap();
            assert_eq!(trial.map(f64::to_bits), exact.map(f64::to_bits));
        }
    }
    println!("ACTIVE_GUARD,4");
}
