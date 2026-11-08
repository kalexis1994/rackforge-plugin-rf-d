use crate::{incidence::{Row, Tangent}, original_solver, solver, voice::{Accepted, B, M, N}, StepError};

fn matrix(trial: &mut solver::Workspace, reference: &mut original_solver::Workspace,
          tangents: [&Tangent; 2], weights: [[f64; 2]; 2]) -> Result<(), StepError> {
    let a = trial.coefficients(tangents.map(|tangent| solver::Stage { tangent }), weights)?;
    let b = reference.coefficients(tangents.map(|tangent| original_solver::Stage { tangent }), weights)?;
    for (x, y) in a.iter().zip(b.iter()) {
        assert!(x.iter().zip(y.iter()).all(|(x, y)| x.to_bits() == y.to_bits()));
    }
    Ok(())
}

pub fn accepted(step: &Accepted) {
    matrix(&mut solver::Workspace::new(), &mut original_solver::Workspace::new(),
           step.stages.chain.each_ref().map(|s| &s.tangent), B).unwrap();
    println!("MATRIX,{}", M * M);
}

fn tangent(stage: usize, crowded: bool, huge: bool) -> Tangent {
    let mut t = Tangent::new();
    for a in 0..N {
        let mut row = Row::new();
        let (first, end) = if a < 54 { (0, 54) } else if a < 56 { (54, 56) } else { (56, N) };
        if crowded {
            for b in first..(first + 24).min(end) {
                row.set(b, 1., 0.).unwrap();
            }
        } else {
            row.set(a, 4., if a == 0 { 0. } else if a == 1 && huge { f64::MAX } else { 0.125 }).unwrap();
            if a < 54 || a >= 56 {
                let b = if a == first { first + 1 } else { first };
                if stage == 0 && a == 0 {
                    // Diagonal coefficient cancels exactly while its cross-stage term survives.
                    row.set(b, -0.1875, 0.125).unwrap();
                } else if (a + stage) % 2 == 0 {
                    row.set(b, 0.03125, if stage == 1 { 0. } else { 0.015625 }).unwrap();
                }
            }
        }
        t.push_row(a, &mut row).unwrap();
    }
    t
}

pub fn guards() {
    let mut a = solver::Workspace::new();
    let mut b = original_solver::Workspace::new();
    let stages = [tangent(0, false, false), tangent(1, false, false)];
    let crowded = tangent(0, true, false);
    let huge = tangent(0, false, true);
    let good = [&stages[0], &stages[1]];
    let rhs = std::array::from_fn(|i| (i as f64 - 80.) * 1e-9);
    for (inputs, weights, fails) in [
        (good, B, false),
        ([&crowded; 2], B, true),
        (good, B, false),
        ([&huge, &stages[1]], B, true),
        (good, B, false),
    ] {
        let left = a.solve(inputs.map(|tangent| solver::Stage { tangent }), weights, rhs);
        let right = b.solve(inputs.map(|tangent| original_solver::Stage { tangent }), weights, rhs);
        if fails {
            assert_eq!(left.as_ref().err(), Some(&StepError::InvalidInput));
        } else {
            assert!(left.is_ok());
        }
        assert_eq!(left.map(|d| d.map(f64::to_bits)), right.map(|d| d.map(f64::to_bits)));
    }
    matrix(&mut a, &mut b, good, B).unwrap();
    println!("SCATTER_GUARD,3,2,1");
}
