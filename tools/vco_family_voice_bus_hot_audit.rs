use crate::{family::Family, graph, original_graph, original_solver, original_voice, parameters, solver, voice};
use voice::{Accepted, Controls, Parameters, State, B, M, N};

pub fn compare(
    family: &Family, p: Parameters, old: State, phase: f64, controls: Controls, h: f64,
    accepted: &Accepted,
) -> Result<(), String> {
    let mut original_p = original_graph::Parameters::new(parameters()).map_err(|e| format!("{e:?}"))?;
    original_p.time = p.time;
    let state = |s: State| original_graph::State { high: s.high, low: s.low, optional: s.optional };
    let control = original_graph::Controls { key: controls.key, optional: controls.optional, short: controls.short };
    let original = original_voice::stages::<true>(
        family, original_p, state(old), phase, accepted.delta.map(state), control, h,
    ).map_err(|e| format!("{e:?}"))?;
    let trial = &accepted.stages;
    let bits = |(col, dc, dq): (usize, f64, f64)| (col, dc.to_bits(), dq.to_bits());
    let mut entries = 0;
    assert_eq!(trial.phase.map(f64::to_bits), original.phase.map(f64::to_bits));
    for (a, b) in trial.chain.iter().zip(original.chain.iter()) {
        assert_eq!(a.now.high.map(f64::to_bits), b.now.high.map(f64::to_bits));
        assert_eq!(a.now.low.map(f64::to_bits), b.now.low.map(f64::to_bits));
        assert_eq!(a.dc.map(f64::to_bits), b.dc.map(f64::to_bits));
        assert_eq!(a.dq.map(f64::to_bits), b.dq.map(f64::to_bits));
        for row in 0..N {
            assert!(a.tangent.entries(row).map(bits).eq(b.tangent.entries(row).map(bits)), "row {row}");
            entries += a.tangent.entries(row).count();
        }
    }
    let original_stages = original.chain.each_ref().map(|stage| original_solver::Stage { tangent: &stage.tangent });
    let trial_stages = trial.chain.each_ref().map(|stage: &graph::Parts| solver::Stage { tangent: &stage.tangent });
    let mut work = solver::Workspace::new();
    let mut reference = original_solver::Workspace::new();
    // Solve the observed Newton RHS and independent directions at both returns.
    for rhs in [
        voice::residual(trial).map(|value| -value),
        std::array::from_fn(|i| if i == 54 || i == N + 54 { 1e-9 } else { 0. }),
        std::array::from_fn(|i| if i == 55 || i == N + 55 { 1e-9 } else { 0. }),
    ] {
        let a: [f64; M] = work.solve(trial_stages, B, rhs).map_err(|e| format!("{e:?}"))?;
        let b = reference.solve(original_stages, B, rhs).map_err(|e| format!("{e:?}"))?;
        assert_eq!(a.map(f64::to_bits), b.map(f64::to_bits));
    }
    let a = work.statistics;
    let b = reference.statistics;
    assert_eq!((a.solves, a.refinements, a.max_nonzeros), (b.solves, b.refinements, b.max_nonzeros));
    assert_eq!(a.max_initial_backward.to_bits(), b.max_initial_backward.to_bits());
    assert_eq!(a.max_final_backward.to_bits(), b.max_final_backward.to_bits());
    println!("HOT_AUDIT,{entries},{},{:.17e}", a.solves, a.max_final_backward);
    Ok(())
}
