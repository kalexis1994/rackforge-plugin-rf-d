pub use rf_d_circuit::{junction_charge, StepError};
#[path = "../crates/rf-d-circuit/src/dual_contour_checkpoint.rs"]
mod codec;
#[path = "../crates/rf-d-circuit/src/dual_contour.rs"]
pub mod dual_contour;
use codec::*;
use dual_contour::*;
fn bits(s: State) -> Vec<u64> {
    s.high
        .into_iter()
        .chain(s.low)
        .map(f64::to_bits)
        .chain([s.optional as u64])
        .collect()
}
fn main() {
    let raw = std::fs::read(std::env::args().nth(1).unwrap()).unwrap();
    assert!(raw.len() % SIZE == 0);
    let mut count = 0;
    let mut rejected = 0;
    for b in raw.chunks_exact(SIZE) {
        let optional = b[24] & 1 != 0;
        let q = Checkpoint::decode(b, optional).unwrap();
        assert_eq!(q.encode().as_slice(), b);
        let mut a = q.state;
        let mut restored = Checkpoint::decode(&q.encode(), optional).unwrap().state;
        let aa = advance(
            &mut a,
            q.controls,
            q.proposal as f64 * 1e-6 / TICKS_PER_US as f64,
        )
        .unwrap();
        let rr = advance(
            &mut restored,
            q.controls,
            q.proposal as f64 * 1e-6 / TICKS_PER_US as f64,
        )
        .unwrap();
        assert_eq!(bits(a), bits(restored));
        assert_eq!(aa.error.to_bits(), rr.error.to_bits());
        assert_eq!(aa.h.to_bits(), rr.h.to_bits());
        for (a, b) in aa
            .fine
            .iter()
            .chain([&aa.coarse])
            .zip(rr.fine.iter().chain([&rr.coarse]))
        {
            assert_eq!(a.residual_a.to_bits(), b.residual_a.to_bits());
            assert_eq!(a.correction_v.to_bits(), b.correction_v.to_bits());
            for (x, y) in a
                .delta
                .into_iter()
                .chain(a.stages)
                .zip(b.delta.into_iter().chain(b.stages))
            {
                assert_eq!(bits(x), bits(y));
            }
        }
        for kind in 0..8 {
            let mut bad = q.encode();
            match kind {
                0 => bad[0] ^= 1,
                1 => bad[28] = 1,
                2 => bad[32..40].copy_from_slice(&f64::NAN.to_le_bytes()),
                3 => bad[40 + 38 * 8..48 + 38 * 8].copy_from_slice(&f64::NAN.to_le_bytes()),
                4 => bad[40 + (54 + 38) * 8..48 + (54 + 38) * 8]
                    .copy_from_slice(&1_f64.to_le_bytes()),
                5 => bad[24] ^= 1,
                6 => bad[16..24].fill(0),
                _ => bad[8..16].copy_from_slice(&(36000 * TICKS_PER_US + 2).to_le_bytes()),
            };
            assert!(Checkpoint::decode(&bad, optional).is_err());
            rejected += 1;
        }
        count += 1;
    }
    println!("PASSED,{count},{rejected}");
}
