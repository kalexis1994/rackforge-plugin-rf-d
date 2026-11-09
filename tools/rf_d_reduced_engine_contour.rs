// Appended inside the graph module to reuse the exact contour stamp.
pub use contour::Parts as ContourParts;

pub fn reduced_contours<const FULL: bool, const T: usize>(
    old: State, change: &[f64; 2 * contour::N], key: f64, h: f64,
) -> Result<[ContourParts<FULL, T>; 2], StepError> {
    let old = old.contour();
    let controls = Controls { key, short: false, optional: old.optional };
    let stage = |change| {
        let delta = contour::State::new(change, old.optional);
        contour::parts_compact::<FULL, T>(old, delta, controls, h, old.advanced(change))
    };
    Ok([stage(change[..contour::N].try_into().unwrap())?,
        stage(change[contour::N..].try_into().unwrap())?])
}
