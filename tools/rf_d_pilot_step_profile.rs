//! Optional native timing inside the contour benchmark.
#[derive(Clone, Copy)]
pub enum Part {
    Contours,
    Audio,
    Schur,
    Linear,
    ReceiverHistory,
    ReceiverLatch,
    ReceiverReturns,
    ReceiverDefects,
    ReceiverProduct,
    ReceiverNodal,
    ReceiverInterface,
}

#[cfg(pilot_profile_steps)]
mod enabled {
    use super::Part;
    use std::{cell::Cell, time::Instant};

    const COUNT: usize = Part::ReceiverInterface as usize + 1;

    thread_local! {
        static ELAPSED: Cell<[u128; COUNT]> = const { Cell::new([0; COUNT]) };
        static CALLS: Cell<[usize; COUNT]> = const { Cell::new([0; COUNT]) };
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
        let [c, a, s, l, ..] = ELAPSED.with(Cell::get);
        let [cn, an, sn, ln, ..] = CALLS.with(Cell::get);
        eprintln!("PROFILE,{c},{a},{s},{l},{cn},{an},{sn},{ln}");
    }

    pub fn report_receiver() {
        let times = ELAPSED.with(Cell::get);
        let calls = CALLS.with(Cell::get);
        for (i, label) in [
            "history",
            "latch",
            "returns",
            "defects",
            "product",
            "nodal",
            "interface",
        ]
        .into_iter()
        .enumerate()
        {
            let index = Part::ReceiverHistory as usize + i;
            println!("RECEIVER,{label},{},{}", times[index], calls[index]);
        }
    }
}

#[cfg(pilot_profile_steps)]
pub use enabled::{report, report_receiver, split, start};

#[cfg(not(pilot_profile_steps))]
pub fn start() {}

#[cfg(not(pilot_profile_steps))]
pub fn split(_: Part, _: ()) {}

#[cfg(not(pilot_profile_steps))]
pub fn report() {}

#[cfg(not(pilot_profile_steps))]
pub fn report_receiver() {}
