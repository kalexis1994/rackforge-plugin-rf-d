//! Optional native timing inside the contour benchmark.
#[derive(Clone, Copy)]
pub enum Part {
    Contours,
    Audio,
    Schur,
    Linear,
}

#[cfg(pilot_profile_steps)]
mod enabled {
    use super::Part;
    use std::{cell::Cell, time::Instant};

    thread_local! {
        static ELAPSED: Cell<[u128; 4]> = const { Cell::new([0; 4]) };
        static CALLS: Cell<[usize; 4]> = const { Cell::new([0; 4]) };
    }

    pub fn start() -> Instant {
        Instant::now()
    }

    pub fn split(part: Part, began: Instant) -> Instant {
        let now = Instant::now();
        ELAPSED.with(|data| {
            let mut times = data.get();
            times[part as usize] += (now - began).as_nanos();
            data.set(times);
        });
        CALLS.with(|data| {
            let mut counts = data.get();
            counts[part as usize] += 1;
            data.set(counts);
        });
        now
    }

    pub fn report() {
        let [c, a, s, l] = ELAPSED.with(Cell::get);
        let [cn, an, sn, ln] = CALLS.with(Cell::get);
        eprintln!("PROFILE,{c},{a},{s},{l},{cn},{an},{sn},{ln}");
    }
}

#[cfg(pilot_profile_steps)]
pub use enabled::{report, split, start};

#[cfg(not(pilot_profile_steps))]
pub fn start() {}

#[cfg(not(pilot_profile_steps))]
pub fn split(_: Part, _: ()) {}

#[cfg(not(pilot_profile_steps))]
pub fn report() {}
