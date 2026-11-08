// Appended inside the graph module to reuse the exact contour stamp.
pub use contour::Parts as ContourParts;

pub fn reduced_contour<const FULL: bool>(
    old: State, change: [f64; 56], key: f64, h: f64,
) -> Result<ContourParts<FULL>, StepError> {
    let delta = State::new(std::array::from_fn(|k| change.get(k).copied().unwrap_or(0.)), old.optional);
    let now = old.advanced(delta.high);
    contour::parts::<FULL>(old.contour(), delta.contour(), Controls {
        key, short: false, optional: old.optional,
    }, h, now.contour())
}
