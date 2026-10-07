use rf_d_circuit::mixer_on::{Error, OnMixer, SOURCE_NAMES};
use serde_json::Value;

fn fixture() -> Value {
    serde_json::from_str(include_str!(
        "../../../evidence/voice_mixer_on_vectors01.json"
    ))
    .unwrap()
}
fn array<const N: usize>(v: &Value) -> [f64; N] {
    std::array::from_fn(|i| v[i].as_f64().unwrap())
}
fn model(v: &Value) -> OnMixer {
    OnMixer::new(
        std::array::from_fn(|i| v["included_on"][i].as_bool().unwrap()),
        array(&v["alpha"]),
    )
    .unwrap()
}
fn near(a: f64, b: f64, tolerance: f64, label: &str) {
    assert!(
        a.is_finite() && b.is_finite() && (a - b).abs() <= tolerance,
        "{label}: {a:.17e} vs {b:.17e}, delta {:.4e}",
        (a - b).abs()
    );
}

#[test]
fn full_port_and_loaded_bus_match_independent_resistor_nodes() {
    let f = fixture();
    assert_eq!(f["case_count"], 279);
    assert_eq!(f["precision_digits"], 80);
    assert_eq!(f["source_names"], serde_json::json!(SOURCE_NAMES));
    assert_eq!(f["legacy_bus_comparison_passed"], true);
    let mut maximum_voltage: f64 = 0.0;
    let mut maximum_current: f64 = 0.0;
    let mut maximum_y: f64 = 0.0;
    for case in f["cases"].as_array().unwrap() {
        let m = model(case);
        let y = m.admittance_s();
        for i in 0..6 {
            for j in 0..6 {
                let expected = case["admittance_s"][i][j].as_f64().unwrap();
                near(y[i][j], expected, 1e-15, "admittance S");
                maximum_y = maximum_y.max((y[i][j] - expected).abs());
            }
        }
        let terminal = array::<6>(&case["terminal_v"]);
        let port = m.evaluate(terminal).unwrap();
        for i in 0..6 {
            near(
                port.current_a[i],
                case["current_a"][i].as_f64().unwrap(),
                1e-14,
                "port A",
            );
        }
        near(
            port.dissipated_power_w,
            case["dissipated_power_w"].as_f64().unwrap(),
            1e-13,
            "power W",
        );
        let source = std::array::from_fn(|i| terminal[i]);
        let solved = m
            .solve_imposed_current(source, case["board_current_a"].as_f64().unwrap())
            .unwrap();
        let expected = case["bus_v"].as_f64().unwrap();
        near(solved.bus_v, expected, 1e-10, "bus V");
        maximum_voltage = maximum_voltage.max((solved.bus_v - expected).abs());
        near(solved.kcl_residual_a, 0.0, 1e-14, "KCL A");
        near(
            solved.d_bus_d_board_current_ohm,
            case["d_bus_d_board_current_ohm"].as_f64().unwrap(),
            1e-9,
            "dV/dI ohm",
        );
        for i in 0..6 {
            let e = case["solved_current_a"][i].as_f64().unwrap();
            near(solved.port.current_a[i], e, 1e-14, "loaded port A");
            maximum_current = maximum_current.max((solved.port.current_a[i] - e).abs());
        }
        for i in 0..5 {
            near(
                solved.d_bus_d_source[i],
                case["d_bus_d_source"][i].as_f64().unwrap(),
                1e-10,
                "dV/dV",
            );
            near(
                solved.d_source_current_d_board_current[i],
                case["d_source_current_d_board_current"][i]
                    .as_f64()
                    .unwrap(),
                1e-12,
                "dI/dI",
            );
            for j in 0..5 {
                near(
                    solved.d_source_current_d_source_s[i][j],
                    case["d_source_current_d_source_s"][i][j].as_f64().unwrap(),
                    1e-15,
                    "reduced S",
                );
            }
        }
    }
    println!("MIXER_ORACLE,cases=279,max_voltage_v={maximum_voltage:.17e},max_current_a={maximum_current:.17e},max_admittance_s={maximum_y:.17e}");
}

#[test]
fn analytical_loaded_port_tangents_match_finite_differences() {
    let f = fixture();
    for case in f["cases"].as_array().unwrap().iter().step_by(11) {
        let m = model(case);
        let v = array::<6>(&case["terminal_v"]);
        let source = std::array::from_fn(|i| v[i]);
        let board = case["board_current_a"].as_f64().unwrap();
        let base = m.solve_imposed_current(source, board).unwrap();
        for j in 0..6 {
            let h = if j == 5 { 1e-7 } else { 1e-4 };
            let mut plus = source;
            let mut minus = source;
            if j < 5 {
                plus[j] += h;
                minus[j] -= h;
            }
            let p = m
                .solve_imposed_current(plus, board + if j == 5 { h } else { 0.0 })
                .unwrap();
            let n = m
                .solve_imposed_current(minus, board - if j == 5 { h } else { 0.0 })
                .unwrap();
            let dv = (p.bus_v - n.bus_v) / (2.0 * h);
            // These FD limits account for subtracting binary64 observations;
            // exact derivative admission above uses the independent nodal oracle.
            near(
                dv,
                if j == 5 {
                    base.d_bus_d_board_current_ohm
                } else {
                    base.d_bus_d_source[j]
                },
                if j == 5 { 1e-7 } else { 1e-10 },
                "FD bus",
            );
            for i in 0..5 {
                let di = (p.port.current_a[i] - n.port.current_a[i]) / (2.0 * h);
                near(
                    di,
                    if j == 5 {
                        base.d_source_current_d_board_current[i]
                    } else {
                        base.d_source_current_d_source_s[i][j]
                    },
                    if j == 5 { 1e-12 } else { 1e-14 },
                    "FD source current",
                );
            }
        }
    }
}

#[test]
fn reciprocal_stamp_and_physical_power_are_passive() {
    let f = fixture();
    for case in f["cases"].as_array().unwrap() {
        let m = model(case);
        let y = m.admittance_s();
        for i in 0..6 {
            for j in 0..6 {
                near(y[i][j], y[j][i], 1e-15, "reciprocity");
            }
        }
        for mask in 0..64 {
            let v = std::array::from_fn(|i| if mask & (1 << i) == 0 { -5.0 } else { 5.0 });
            let p = m.evaluate(v).unwrap();
            let terminal_power: f64 = v.iter().zip(p.current_a).map(|(v, i)| v * i).sum();
            assert!(p.dissipated_power_w >= 0.0);
            near(
                terminal_power,
                p.dissipated_power_w,
                1e-13,
                "terminal power",
            );
        }
    }
}

#[test]
fn exact_contacts_preserve_loads_and_documentary_weights() {
    let m = OnMixer::new([true, false, false, false, false], [0.0; 4]).unwrap();
    let p = m
        .solve_imposed_current([2.0, 0.0, 0.0, 0.0, 0.0], 1e-6)
        .unwrap();
    near(p.bus_v, -0.033, 1e-15, "grounded wiper");
    near(
        p.port.current_a[0],
        2.0 / 25_000.0,
        1e-18,
        "source track load",
    );
    near(p.d_bus_d_source[0], 0.0, 0.0, "zero drive");
    near(
        p.d_bus_d_board_current_ohm,
        -33_000.0,
        1e-9,
        "bus still loaded",
    );
    let all = OnMixer::new([true; 5], [1.0; 4])
        .unwrap()
        .solve_imposed_current([1.0, 2.0, 3.0, 4.0, 5.0], 0.0)
        .unwrap();
    near(all.bus_v, 23.0 / 7.0, 1e-14, "documentary full level");
    for i in 0..5 {
        near(
            all.d_bus_d_source[i],
            if i == 3 { 3.0 / 7.0 } else { 1.0 / 7.0 },
            1e-15,
            "series weights",
        );
    }
    let ext = OnMixer::new([false, false, false, false, true], [0.0; 4])
        .unwrap()
        .solve_imposed_current([0.0, 0.0, 0.0, 0.0, 3.2], 1e-3)
        .unwrap();
    near(
        ext.port.current_a[4],
        1e-3,
        1e-17,
        "EXT source supplies board",
    );
}

#[test]
fn representable_contact_neighborhoods_remain_finite() {
    for alpha in [f64::from_bits(1), 1e-300, 1e-15, 1.0 - f64::EPSILON, 1.0] {
        let m = OnMixer::new([true; 5], [alpha; 4]).unwrap();
        let p = m
            .solve_imposed_current([2.0, -2.0, 1.0, -1.0, 0.5], 3e-6)
            .unwrap();
        assert!(p.bus_v.is_finite());
        assert!(p.port.current_a.iter().all(|v| v.is_finite()));
        near(p.kcl_residual_a, 0.0, 1e-14, "endpoint KCL");
    }
}

#[test]
fn omitted_subgraph_has_zero_stamp_and_floating_bus() {
    let m = OnMixer::new([false; 5], [0.5; 4]).unwrap();
    assert_eq!(m.admittance_s(), [[0.0; 6]; 6]);
    assert_eq!(m.evaluate([2.0; 6]).unwrap().current_a, [0.0; 6]);
    assert_eq!(
        m.solve_imposed_current([2.0; 5], 0.0).unwrap_err(),
        Error::FloatingBus
    );
}

#[test]
fn invalid_or_overflowing_inputs_are_rejected_without_clamping() {
    for alpha in [f64::NAN, f64::INFINITY, -0.1, 1.1] {
        assert_eq!(
            OnMixer::new([true; 5], [alpha; 4]).unwrap_err(),
            Error::InvalidInput
        );
    }
    let m = OnMixer::new([true; 5], [0.5; 4]).unwrap();
    assert_eq!(m.evaluate([f64::NAN; 6]).unwrap_err(), Error::InvalidInput);
    assert_eq!(
        m.solve_imposed_current([0.0; 5], f64::INFINITY)
            .unwrap_err(),
        Error::InvalidInput
    );
    assert_eq!(
        m.evaluate([f64::MAX; 6]).unwrap_err(),
        Error::ArithmeticDomain
    );
    assert_eq!(
        m.solve_imposed_current([0.0; 5], f64::MAX).unwrap_err(),
        Error::ArithmeticDomain
    );
}
