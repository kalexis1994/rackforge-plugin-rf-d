// Appended inside the graph module to reuse the exact contour stamp.
pub use contour::Parts as ContourParts;

pub fn contour_workspace<const FULL: bool, const T: usize>(old: State) -> [ContourParts<FULL, T>; 2] {
    contour::pair_workspace(old.contour())
}

pub fn reduced_contours<const FULL: bool, const T: usize>(
    workspace: &mut [ContourParts<FULL, T>; 2], old: State, change: &[f64; 2 * contour::N], key: f64, h: f64,
) -> Result<(), StepError> {
    let old = old.contour();
    let controls = Controls { key, short: false, optional: old.optional };
    let stages = [change[..contour::N].try_into().unwrap(), change[contour::N..].try_into().unwrap()];
    contour::stamp_pair(workspace, old, stages, controls, h)
}
