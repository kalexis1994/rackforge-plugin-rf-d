use crate::{incidence::{BitRow, Row, Tangent}, StepError};

pub fn guard() {
    let mut reference = Tangent::new();
    let mut candidate = Tangent::new();
    let make_bits = |(i, dc, mass): (usize, f64, f64)| (i, dc.to_bits(), mass.to_bits());
    for a in 0..117 {
        let mut normal = Row::new();
        let mut bits = BitRow::new();
        // Add columns in reverse and keep one signed zero next to nonzero mass.
        for k in (0..35).rev() {
            let dc = if k == 17 { -0. } else { k as f64 + 1. };
            normal.set(k, dc, 0.25).unwrap();
            bits.set(k, dc, 0.25).unwrap();
        }
        reference.push_row(a, &mut normal).unwrap();
        candidate.push_bits(a, &bits).unwrap();
        assert!(reference.entries(a).map(make_bits).eq(candidate.entries(a).map(make_bits)));
    }
    let mut normal = Row::new();
    let mut bits = BitRow::new();
    for k in [117, 116] {
        normal.add(k, 1., 0.125).unwrap();
        bits.add(k, 1., 0.125).unwrap();
    }
    assert_eq!(reference.push_row(117, &mut normal), Err(StepError::InvalidInput));
    assert_eq!(candidate.push_bits(117, &bits), Err(StepError::InvalidInput));
    normal.add(116, -1., -0.125).unwrap();
    bits.add(116, -1., -0.125).unwrap();
    reference.push_row(117, &mut normal).unwrap();
    candidate.push_bits(117, &bits).unwrap();
    assert!(reference.entries(117).map(make_bits).eq(candidate.entries(117).map(make_bits)));
    assert!(reference.complete() && candidate.complete());
    println!("BITROW_GUARD,4096,1,1");
}
