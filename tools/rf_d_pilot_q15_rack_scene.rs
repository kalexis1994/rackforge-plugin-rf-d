//! Two blocks of the admitted Q15/R59 scene, one J7 endpoint per host frame.
use crate::{fixture, probe::ALLOCS, q15_probe, q15_r59, voice::Frame};
use std::sync::atomic::Ordering::Relaxed;

pub(crate) struct Scene {
    state: q15_r59::State,
    tick: usize,
}

impl Scene {
    pub(crate) fn new() -> Result<Self, Box<dyn std::error::Error>> {
        Ok(Self {
            state: q15_probe::initial_state(&fixture::HEADER)?,
            tick: 0,
        })
    }

    pub(crate) fn render(&mut self, output: &mut [Frame]) -> Result<(), ()> {
        let end = self.tick + 2 * output.len();
        let input = fixture::INPUT.get(self.tick..end).ok_or(())?;
        let before = ALLOCS.load(Relaxed);
        let mut state = self.state;
        for (i, (frame, pair)) in output.iter_mut().zip(input.chunks_exact(2)).enumerate() {
            let tick = self.tick + i * 2;
            let (half, _) = q15_r59::advance(state, pair[0], tick % 256 == 0).map_err(|_| ())?;
            let (next, last) = q15_r59::advance(half, pair[1], false).map_err(|_| ())?;
            frame.j7_v = last.audio.ports.j7_v;
            state = next;
        }
        if ALLOCS.load(Relaxed) != before {
            return Err(());
        }
        self.state = state;
        self.tick = end;
        Ok(())
    }
}
