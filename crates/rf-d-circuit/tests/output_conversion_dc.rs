use rf_d_circuit::output_conversion::{
    solve_dc, Boundary, DiodeParameters, Parameters, NODE_NAMES,
};
use serde_json::Value;

fn n(v: &Value) -> f64 {
    v.as_f64().unwrap()
}

#[test]
fn six_node_conversion_matches_independent_python_dc() {
    let fixture: Value = serde_json::from_str(include_str!(
        "../../../evidence/output_conversion_dc_vectors.json"
    ))
    .unwrap();
    assert_eq!(fixture["schema"], "rf-d/output-conversion-dc-vectors/v1");
    for (i, name) in NODE_NAMES.iter().enumerate() {
        assert_eq!(&fixture["node_order"][i], name);
    }
    for case in fixture["cases"].as_array().unwrap() {
        let params = &case["parameters"];
        let diode = if params["diode_model"].is_null() {
            None
        } else {
            Some(DiodeParameters {
                is_a: n(&params["diode_model"]["is_a"]),
                ideality: n(&params["diode_model"]["ideality"]),
            })
        };
        let p = Parameters {
            transistor_is_a: n(&params["is_a"]),
            beta_forward: n(&params["beta_forward"]),
            beta_reverse: n(&params["beta_reverse"]),
            temperature_k: n(&params["temperature_k"]),
            diode,
        };
        let boundary = &case["boundary"];
        let b = Boundary {
            q1_base_v: n(&boundary["q1_base_v"]),
            q12_base_v: n(&boundary["q12_base_v"]),
            q17_base_v: n(&boundary["q17_base_v"]),
            plus_v: n(&boundary["plus_v"]),
        };
        let result = solve_dc(p, b).unwrap_or_else(|e| panic!("{}: {e:?}", case["id"]));
        assert!(result.max_kcl_residual_a < 1e-12);
        for (i, actual) in result.state.node_v.iter().enumerate() {
            let expected = n(&case["node_v"][i]);
            assert!(
                (actual - expected).abs() < 1e-8,
                "{} node {}: {actual} vs {expected}",
                case["id"],
                NODE_NAMES[i]
            );
        }
    }
}
