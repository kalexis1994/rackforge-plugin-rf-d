use std::alloc::{GlobalAlloc, Layout, System};
use std::sync::atomic::{AtomicUsize, Ordering};

use rf_d_circuit::ladder_recovery_output::{
    initial_state as initial_ladder_state, step as step_ladder, Boundary as LadderBoundary,
    Parameters as LadderParameters,
};
use rf_d_circuit::output::{
    initial_output_state, solve_output_boundary, solve_output_input_port, OutputBoundary,
};
use rf_d_circuit::output_conversion::{
    initial_coupled_state, solve_coupled_step, solve_dc as solve_conversion_dc,
    Boundary as ConversionBoundary, CoupledBoundary, DiodeParameters,
    Parameters as ConversionParameters,
};
use rf_d_circuit::output_conversion_c4::{
    initial_state as initial_c4_state, solve_input_port as solve_c4_input_port, step as step_c4,
    BoundaryC4,
};
use rf_d_circuit::panel::{initial_panel_state, solve_panel_boundary, PanelBoundary};
use rf_d_circuit::recovery_vca_output::{
    initial_state as initial_recovery_vca_state, solve_input_port as solve_recovery_input_port,
    step as step_recovery_vca, Boundary as RecoveryBoundary,
};
use rf_d_circuit::vca1_output::{
    initial_state as initial_vca1_output_state, solve_input_port as solve_vca1_input_port,
    step as step_vca1_output, Boundary as Vca1Boundary,
};
use rf_d_circuit::vca2_output::{
    initial_state as initial_vca2_output_state, solve_input_port as solve_vca2_output_input_port,
    step as step_vca2_output, Boundary as Vca2Boundary, Parameters as Vca2Parameters,
};
use rf_d_circuit::{initial_state, solve_input_port, step, Parameters, SolverBudget};

struct CountingAllocator;
static ALLOCATIONS: AtomicUsize = AtomicUsize::new(0);

// The test binary has one test, so the counter isolates this processing loop.
unsafe impl GlobalAlloc for CountingAllocator {
    unsafe fn alloc(&self, layout: Layout) -> *mut u8 {
        ALLOCATIONS.fetch_add(1, Ordering::Relaxed);
        unsafe { System.alloc(layout) }
    }

    unsafe fn alloc_zeroed(&self, layout: Layout) -> *mut u8 {
        ALLOCATIONS.fetch_add(1, Ordering::Relaxed);
        unsafe { System.alloc_zeroed(layout) }
    }

    unsafe fn realloc(&self, ptr: *mut u8, layout: Layout, new_size: usize) -> *mut u8 {
        ALLOCATIONS.fetch_add(1, Ordering::Relaxed);
        unsafe { System.realloc(ptr, layout, new_size) }
    }

    unsafe fn dealloc(&self, ptr: *mut u8, layout: Layout) {
        unsafe { System.dealloc(ptr, layout) }
    }
}

#[global_allocator]
static ALLOCATOR: CountingAllocator = CountingAllocator;

#[test]
fn dc_initialization_and_audio_steps_do_not_allocate() {
    let p = Parameters {
        transistor_is_a: 1e-14,
        beta_forward: 160.0,
        beta_reverse: 5.0,
        temperature_k: 300.0,
        diode_is_a: 1.446_588_643_457_551_9e-9,
        diode_ideality: 1.5,
    };
    let before = ALLOCATIONS.load(Ordering::Relaxed);
    solve_conversion_dc(
        ConversionParameters {
            transistor_is_a: 1e-14,
            beta_forward: 100.0,
            beta_reverse: 5.0,
            temperature_k: 298.15,
            diode: None,
        },
        ConversionBoundary {
            q1_base_v: 8.3,
            q12_base_v: 7.75,
            q17_base_v: 7.75,
            plus_v: 10.0,
        },
    )
    .expect("board-4 conversion DC");
    let mut state = initial_state(p).expect("DC initialization");
    for i in 0..1000 {
        let input = if i % 200 < 100 { 0.5 } else { -0.5 };
        step(
            &mut state,
            p,
            input,
            1.0 / 48000.0,
            Some(32.0),
            Some(32.0),
            SolverBudget::default(),
        )
        .expect("bounded board-3 step");
    }
    for i in 0..100 {
        let input = if i % 20 < 10 { 0.25 } else { -0.25 };
        state = solve_input_port(
            &state,
            p,
            input,
            1.0 / 48000.0,
            Some(32.0),
            Some(32.0),
            SolverBudget::default(),
        )
        .expect("dynamic C19 port")
        .next_state;
    }
    let mut panel = initial_panel_state(p).expect("panel DC initialization");
    for i in 0..100 {
        let source = if i % 20 < 10 { 0.1 } else { -0.1 };
        solve_panel_boundary(
            &mut panel,
            p,
            PanelBoundary {
                c2_right_v: source,
                r21_lower_ohm: 2000.0,
                dt_s: 1.0 / 48000.0,
                tip_load_ohm: Some(32.0),
                ring_load_ohm: Some(32.0),
            },
            SolverBudget::default(),
        )
        .expect("panel and board-3 step");
    }
    let mut output = initial_output_state(p, 5.0).expect("output DC initialization");
    for i in 0..100 {
        let q17 = if i % 20 < 10 { 5.1 } else { 4.9 };
        solve_output_boundary(
            &mut output,
            p,
            OutputBoundary {
                q17_collector_v: q17,
                r20_lower_ohm: 2500.0,
                hi_load_ohm: 10000.0,
                lo_load_ohm: 100000.0,
                sw18_on: i % 40 < 20,
                r21_lower_ohm: 2000.0,
                tip_load_ohm: Some(32.0),
                ring_load_ohm: Some(32.0),
                dt_s: 1.0 / 48000.0,
            },
            SolverBudget::default(),
        )
        .expect("C2, main panel and headphone step");
    }
    for i in 0..100 {
        let q17 = if i % 20 < 10 { 5.1 } else { 4.9 };
        output = solve_output_input_port(
            &output,
            p,
            OutputBoundary {
                q17_collector_v: q17,
                r20_lower_ohm: 2500.0,
                hi_load_ohm: 10000.0,
                lo_load_ohm: 100000.0,
                sw18_on: true,
                r21_lower_ohm: 2000.0,
                tip_load_ohm: Some(32.0),
                ring_load_ohm: Some(32.0),
                dt_s: 1.0 / 48000.0,
            },
            SolverBudget::default(),
        )
        .expect("Q17 C2 dynamic port")
        .next_state;
    }
    let conversion = ConversionParameters {
        transistor_is_a: 1e-14,
        beta_forward: 100.0,
        beta_reverse: 5.0,
        temperature_k: 300.0,
        diode: Some(DiodeParameters {
            is_a: p.diode_is_a,
            ideality: p.diode_ideality,
        }),
    };
    let base = ConversionBoundary {
        q1_base_v: 8.3,
        q12_base_v: 7.75,
        q17_base_v: 7.75,
        plus_v: 10.0,
    };
    let mut coupled = initial_coupled_state(conversion, base, p).expect("joint DC state");
    for i in 0..100 {
        let mut imposed = base;
        imposed.q17_base_v += if i % 20 < 10 { 0.018 } else { -0.018 };
        solve_coupled_step(
            &mut coupled,
            conversion,
            p,
            CoupledBoundary {
                conversion: imposed,
                output: OutputBoundary {
                    q17_collector_v: 0.0,
                    r20_lower_ohm: 2500.0,
                    hi_load_ohm: 10000.0,
                    lo_load_ohm: 100000.0,
                    sw18_on: i % 40 < 20,
                    r21_lower_ohm: 2000.0,
                    tip_load_ohm: Some(32.0),
                    ring_load_ohm: Some(32.0),
                    dt_s: 1.0 / 48000.0,
                },
            },
            SolverBudget::default(),
        )
        .expect("atomic board4/C2/panel/board3 step");
    }
    let mut c4 = initial_c4_state(
        conversion,
        p,
        BoundaryC4 {
            second_balance_wiper_v: 6.2,
            q12_base_v: 7.75,
            q17_base_v: 7.75,
            plus_v: 10.0,
            output: OutputBoundary {
                q17_collector_v: 0.0,
                r20_lower_ohm: 2500.0,
                hi_load_ohm: 10000.0,
                lo_load_ohm: 100000.0,
                sw18_on: true,
                r21_lower_ohm: 2000.0,
                tip_load_ohm: Some(32.0),
                ring_load_ohm: Some(32.0),
                dt_s: 1.0 / 48000.0,
            },
        },
    )
    .expect("C4 and output DC state");
    for i in 0..100 {
        step_c4(
            &mut c4,
            conversion,
            p,
            BoundaryC4 {
                second_balance_wiper_v: if i % 20 < 10 { 6.2 } else { 6.23 },
                q12_base_v: 7.75,
                q17_base_v: 7.75 + if i % 20 < 10 { 0.018 } else { -0.018 },
                plus_v: 10.0,
                output: OutputBoundary {
                    q17_collector_v: 0.0,
                    r20_lower_ohm: 2500.0,
                    hi_load_ohm: 10000.0,
                    lo_load_ohm: 100000.0,
                    sw18_on: i % 40 < 20,
                    r21_lower_ohm: 2000.0,
                    tip_load_ohm: Some(32.0),
                    ring_load_ohm: Some(32.0),
                    dt_s: 1.0 / 48000.0,
                },
            },
            SolverBudget::default(),
        )
        .expect("atomic C4 and complete output step");
    }
    for i in 0..20 {
        c4 = solve_c4_input_port(
            &c4,
            conversion,
            p,
            BoundaryC4 {
                second_balance_wiper_v: 6.2,
                q12_base_v: 7.75,
                q17_base_v: 7.75 + if i % 10 < 5 { 0.01 } else { -0.01 },
                plus_v: 10.0,
                output: OutputBoundary {
                    q17_collector_v: 0.0,
                    r20_lower_ohm: 2500.0,
                    hi_load_ohm: 10000.0,
                    lo_load_ohm: 100000.0,
                    sw18_on: true,
                    r21_lower_ohm: 2000.0,
                    tip_load_ohm: Some(32.0),
                    ring_load_ohm: Some(32.0),
                    dt_s: 1.0 / 48000.0,
                },
            },
            SolverBudget::default(),
        )
        .expect("second VCA three-port")
        .next_state;
    }
    let vca2 = Vca2Parameters {
        transistor_is_a: 1e-14,
        beta_forward: 100.0,
        beta_reverse: 5.0,
        temperature_k: 298.15,
    };
    let vca2_base = Vca2Boundary {
        q14_base_v: 6.049_215_054_864_024,
        q13_base_v: 6.048_795_653_323_937,
        q21_base_v: 2.0,
        first_balance_wiper_v: 6.061_605_244_408_402,
        second_balance_left_ohm: 50.0,
        minus_v: -10.0,
        output: BoundaryC4 {
            second_balance_wiper_v: 0.0,
            q12_base_v: 0.0,
            q17_base_v: 0.0,
            plus_v: 10.0,
            output: OutputBoundary {
                q17_collector_v: 0.0,
                r20_lower_ohm: 2500.0,
                hi_load_ohm: 10000.0,
                lo_load_ohm: 100000.0,
                sw18_on: true,
                r21_lower_ohm: 2000.0,
                tip_load_ohm: Some(32.0),
                ring_load_ohm: Some(32.0),
                dt_s: 1.0 / 48000.0,
            },
        },
    };
    let mut vca2_output =
        initial_vca2_output_state(vca2, conversion, p, vca2_base).expect("VCA2 to J7 DC state");
    for i in 0..100 {
        let mut b = vca2_base;
        b.q14_base_v += if i % 20 < 10 { 0.005 } else { -0.005 };
        b.q13_base_v -= if i % 20 < 10 { 0.005 } else { -0.005 };
        b.output.output.sw18_on = i % 40 < 20;
        step_vca2_output(
            &mut vca2_output,
            vca2,
            conversion,
            p,
            b,
            SolverBudget::default(),
        )
        .expect("VCA2 to J7 step");
    }
    for i in 0..20 {
        let mut b = vca2_base;
        b.q14_base_v += if i % 10 < 5 { 0.003 } else { -0.003 };
        vca2_output = solve_vca2_output_input_port(
            &vca2_output,
            vca2,
            conversion,
            p,
            b,
            SolverBudget::default(),
        )
        .expect("four-port toward first VCA")
        .next_state;
    }
    let vca1_boundary = Vca1Boundary {
        recover_collector_v: 5.0,
        loudness_v: 2.0,
        first_balance_left_ohm: 12.5,
        second: Vca2Boundary {
            q14_base_v: 0.0,
            q13_base_v: 0.0,
            first_balance_wiper_v: 0.0,
            ..vca2_base
        },
    };
    let mut vca1 = initial_vca1_output_state(vca2, conversion, p, vca1_boundary)
        .expect("first VCA to J7 DC state");
    for i in 0..100 {
        let mut b = vca1_boundary;
        b.recover_collector_v += if i % 20 < 10 { 0.03 } else { -0.03 };
        b.second.output.output.sw18_on = i % 40 < 20;
        step_vca1_output(&mut vca1, vca2, conversion, p, b, SolverBudget::default())
            .expect("first VCA to J7 step");
    }
    for i in 0..20 {
        let mut b = vca1_boundary;
        b.recover_collector_v += if i % 10 < 5 { 0.01 } else { -0.01 };
        vca1 = solve_vca1_input_port(&vca1, vca2, conversion, p, b, SolverBudget::default())
            .expect("R2/C6 port toward filter recovery")
            .next_state;
    }
    let recovery_boundary = RecoveryBoundary {
        ladder_left_v: 0.0,
        ladder_right_v: 0.0,
        vca: vca1_boundary,
    };
    let mut recovery = initial_recovery_vca_state(vca2, conversion, p, recovery_boundary)
        .expect("recovery through J7 DC state");
    for i in 0..100 {
        let mut b = recovery_boundary;
        b.ladder_left_v = if i % 20 < 10 { 0.02 } else { -0.02 };
        b.ladder_right_v = -b.ladder_left_v;
        b.vca.second.output.output.sw18_on = i % 40 < 20;
        step_recovery_vca(
            &mut recovery,
            vca2,
            conversion,
            p,
            b,
            SolverBudget::default(),
        )
        .expect("recovery through J7 step");
    }
    for i in 0..20 {
        let mut b = recovery_boundary;
        b.ladder_left_v = if i % 10 < 5 { 0.01 } else { -0.01 };
        b.ladder_right_v = -b.ladder_left_v;
        recovery =
            solve_recovery_input_port(&recovery, vca2, conversion, p, b, SolverBudget::default())
                .expect("C5/C1 two-port toward ladder")
                .next_state;
    }
    let ladder_parameters = LadderParameters {
        transistor: vca2,
        tail_current_a: 6.824_898_505_905_974e-6,
        r61_ohm: 200.0,
        r30_ohm: 830.0,
    };
    let ladder_seed = [
        7.8431017460109675,
        6.372499040594479,
        4.9019061730679665,
        3.43132324181033,
        1.9607503461842566,
        1.4561733893906676,
        1.9607344627142946,
        1.9607223099167141,
        2.9270178181494293,
        4.397856399069791,
        5.868704916259031,
        7.339563271338244,
        2.927029970947009,
        4.397868551867372,
        5.868717069056611,
        7.339575424135825,
    ];
    let mut ladder = initial_ladder_state(
        ladder_parameters,
        conversion,
        p,
        LadderBoundary {
            bus_v: 0.0,
            recovery: recovery_boundary,
        },
        ladder_seed,
    )
    .expect("ladder through J7 DC state");
    for i in 0..40 {
        let bus_v = if i % 20 < 10 { 0.001 } else { -0.001 };
        step_ladder(
            &mut ladder,
            ladder_parameters,
            conversion,
            p,
            LadderBoundary {
                bus_v,
                recovery: recovery_boundary,
            },
            SolverBudget::default(),
        )
        .expect("ladder through J7 step");
    }
    let after = ALLOCATIONS.load(Ordering::Relaxed);
    assert_eq!(after - before, 0, "processing allocated heap memory");
}
