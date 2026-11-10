//! Decode and run the native C4 clock in the probes.
use crate::{carry, clock, crossing};

pub const WORDS: usize = crossing::POINTS * 10
    + carry::POINTS * (carry::STATE * 5 + 1)
    + carry::POST_POINTS * 31
    + carry::STATE;

pub struct Fixture {
    family: clock::Family<{ carry::STATE }, { carry::POINTS }>,
    crossing: crossing::Profile,
    post: carry::PostProfile,
    initial: [f64; carry::STATE],
}

impl Fixture {
    pub fn read(mut values: impl Iterator<Item = f64>) -> Self {
        let mut next = || values.next().unwrap();
        let crossing = crossing::Profile {
            rising: std::array::from_fn(|_| crossing::Point {
                collector: next(),
                neighbors: std::array::from_fn(|_| next()),
            }),
            tail: std::array::from_fn(|_| std::array::from_fn(|_| next())),
        };
        let phase = std::array::from_fn(|_| next());
        let family = clock::Family {
            phase,
            knots: std::array::from_fn(|_| clock::Knot {
                nominal: std::array::from_fn(|_| next()),
                linear: std::array::from_fn(|_| std::array::from_fn(|_| next())),
                quadratic: std::array::from_fn(|_| std::array::from_fn(|_| next())),
            }),
        };
        let post = carry::PostProfile(std::array::from_fn(|_| carry::PostKnot {
            time: next(),
            nominal: std::array::from_fn(|_| std::array::from_fn(|_| next())),
            linear: std::array::from_fn(|_| {
                std::array::from_fn(|_| std::array::from_fn(|_| next()))
            }),
            quadratic: std::array::from_fn(|_| {
                std::array::from_fn(|_| std::array::from_fn(|_| next()))
            }),
            readout: std::array::from_fn(|_| std::array::from_fn(|_| next())),
        }));
        let initial = std::array::from_fn(|_| next());
        Self {
            family,
            crossing,
            post,
            initial,
        }
    }

    pub fn render(
        &self,
        mut emit: impl FnMut([f64; 2], [[f64; 3]; 2], f64),
        mut emit_cv: impl FnMut([f64; 3]),
    ) -> Option<[f64; 7]> {
        let mut voice = carry::Carry::start(&self.family, self.initial)?;
        for slot in 0..64 {
            let (timers, currents) = voice.observe()?;
            emit(timers, currents, voice.filter_sum());
            let sample = voice.advance(&self.crossing, &self.post)?;
            emit_cv(voice.cv_stages());
            match sample {
                carry::Sample::Boundary => (),
                carry::Sample::Event {
                    seconds,
                    timers,
                    filter_sum,
                } => {
                    let [c2_weight, c5_weight] = voice.load_weights();
                    return Some([
                        slot as f64,
                        seconds,
                        timers[0],
                        timers[1],
                        filter_sum,
                        c2_weight,
                        c5_weight,
                    ]);
                }
            }
        }
        None
    }
}
