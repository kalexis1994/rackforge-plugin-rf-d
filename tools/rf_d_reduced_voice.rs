//! Reduced fixed-bias audio arm for the monophonic RF-D pilot.
use crate::{coefficients, plant, wave};

pub const MAX_BLOCK: usize = 128;
pub const RATE: usize = 48_000;
pub const LATENCY: usize = 48;
pub const AUDITION_VOLTS_PER_FULL_SCALE: f64 = 0.000125;
const INPUT_PEAK_V: f64 = 0.08;
const RAMP_S: f64 = 0.005;
const TABLE: usize = wave::SAW.len();

#[derive(Clone, Copy)]
pub enum Message {
    NoteOn(u8),
    NoteOff(u8),
    AllNotesOff,
}

#[derive(Clone, Copy)]
pub struct Event {
    pub offset: usize,
    pub message: Message,
}

#[derive(Clone, Copy, Debug)]
pub enum Error {
    Input,
    Plant(plant::Error),
}

#[derive(Clone, Copy, Debug, Default, PartialEq)]
pub struct Frame {
    pub j7_v: f64,
    pub bus_v: f64,
    pub c27_v: f64,
    pub panel_a: f64,
    #[cfg(pilot_returns)]
    pub returns_a: [f64; 2],
}

#[cfg(pilot_returns)]
#[derive(Clone, Copy)]
pub struct Panel {
    pub drive: plant::Drive,
    pub mixer_gain: f64,
    pub attack_ms: f64,
    pub release_ms: f64,
}

#[cfg(pilot_returns)]
impl Default for Panel {
    fn default() -> Self {
        Self {
            drive: plant::Drive::default(),
            mixer_gain: 1.,
            attack_ms: RAMP_S * 1000.,
            release_ms: RAMP_S * 1000.,
        }
    }
}

#[cfg(pilot_returns)]
impl Panel {
    fn valid(self) -> bool {
        self.drive.valid()
            && (0. ..=1.).contains(&self.mixer_gain)
            && (1. ..=100.).contains(&self.attack_ms)
            && (1. ..=200.).contains(&self.release_ms)
    }
}

#[derive(Clone)]
pub struct Voice<const FACTOR: usize> {
    circuit: plant::State,
    held: u64,
    phase: f64,
    increment: f64,
    trim: f64,
    history: [f64; 769],
    head: usize,
    frames: usize,
    #[cfg(pilot_returns)]
    drive: plant::Drive,
}

impl<const FACTOR: usize> Voice<FACTOR> {
    pub fn new() -> Self {
        #[cfg(not(pilot_returns))]
        assert!(matches!(FACTOR, 4 | 8));
        #[cfg(all(pilot_returns, not(pilot_pi)))]
        assert_eq!(FACTOR, 4);
        #[cfg(pilot_pi)]
        assert_eq!(FACTOR, 2);
        Self {
            circuit: plant::State::dc(1).unwrap(),
            held: 0,
            phase: 0.,
            increment: 440. / (FACTOR * RATE) as f64,
            trim: 0.,
            history: [0.; 769],
            head: 0,
            frames: 0,
            #[cfg(pilot_returns)]
            drive: plant::Drive::default(),
        }
    }

    fn event(&mut self, message: Message) -> Result<(), Error> {
        match message {
            Message::NoteOn(note @ 36..=72) => self.held |= 1 << (note - 36),
            Message::NoteOff(note @ 36..=72) => self.held &= !(1 << (note - 36)),
            Message::AllNotesOff => self.held = 0,
            _ => return Err(Error::Input),
        }
        if self.held != 0 {
            let note = self.held.trailing_zeros() + 36;
            self.increment = 440. * ((f64::from(note) - 69.) / 12.).exp2() / (FACTOR * RATE) as f64;
        }
        Ok(())
    }

    fn next(&mut self, #[cfg(pilot_returns)] panel: Panel) -> Result<Frame, Error> {
        #[cfg(pilot_pi)]
        let kernel = &crate::pi_coefficients::H96000[..];
        #[cfg(not(pilot_pi))]
        let kernel = if FACTOR == 4 {
            &coefficients::H192000[..]
        } else {
            &coefficients::H384000[..]
        };
        #[cfg(not(pilot_returns))]
        let ramp_s = RAMP_S;
        #[cfg(pilot_returns)]
        let ramp_s = 0.001
            * if self.held != 0 {
                panel.attack_ms
            } else {
                panel.release_ms
            };
        let change = 1. / (ramp_s * (RATE * FACTOR) as f64);
        #[cfg(not(pilot_returns))]
        let input_peak = INPUT_PEAK_V;
        #[cfg(pilot_returns)]
        let input_peak = INPUT_PEAK_V * panel.mixer_gain;
        let mut last = Frame::default();
        for _substep in 0..FACTOR {
            self.phase += self.increment;
            if self.phase >= 1. {
                self.phase -= 1.;
            }
            if self.held != 0 {
                self.trim = (self.trim + change).min(1.);
            } else {
                self.trim = (self.trim - change).max(0.);
            }
            let position = self.phase * TABLE as f64;
            let index = position as usize;
            let left = wave::SAW[index % TABLE];
            let right = wave::SAW[(index + 1) % TABLE];
            let input = input_peak * self.trim * (left + position.fract() * (right - left));
            #[cfg(not(pilot_returns))]
            let ports = plant::step(&mut self.circuit, input).map_err(Error::Plant)?;
            #[cfg(pilot_returns)]
            let ports = plant::step(
                &mut self.circuit,
                input,
                self.drive
                    .interpolate(panel.drive, (_substep + 1) as f64 / FACTOR as f64),
            )
            .map_err(Error::Plant)?;
            self.history[self.head] = ports.j7_v;
            self.head = (self.head + 1) % kernel.len();
            last.bus_v = ports.bus_v;
            last.c27_v = ports.base_v - ports.bus_v;
            last.panel_a = ports.panel_a;
            #[cfg(pilot_returns)]
            {
                last.returns_a = ports.returns_a;
            }
        }
        #[cfg(pilot_returns)]
        {
            self.drive = panel.drive;
        }
        self.frames += 1;
        if self.frames > LATENCY {
            let (first, second) = kernel.split_at(kernel.len() - self.head);
            last.j7_v = first
                .iter()
                .zip(&self.history[self.head..kernel.len()])
                .chain(second.iter().zip(&self.history[..self.head]))
                .fold(0., |sum, (coefficient, value)| sum + coefficient * value);
        }
        Ok(last)
    }

    /// Events at one offset are applied in caller order. Failed blocks publish no state.
    pub fn render(&mut self, events: &[Event], frames: &mut [Frame]) -> Result<(), Error> {
        self.render_inner(
            events,
            frames,
            #[cfg(pilot_returns)]
            |_| Panel::default(),
        )
    }

    #[cfg(pilot_returns)]
    pub fn render_with_returns(
        &mut self,
        events: &[Event],
        frames: &mut [Frame],
        drives: &[plant::Drive],
    ) -> Result<(), Error> {
        if drives.len() != frames.len() || drives.iter().any(|drive| !drive.valid()) {
            return Err(Error::Input);
        }
        self.render_inner(events, frames, |i| Panel {
            drive: drives[i],
            ..Panel::default()
        })
    }

    #[cfg(pilot_returns)]
    pub fn render_panel(
        &mut self,
        events: &[Event],
        frames: &mut [Frame],
        panel: &[Panel],
    ) -> Result<(), Error> {
        if panel.len() != frames.len() || panel.iter().any(|control| !control.valid()) {
            return Err(Error::Input);
        }
        self.render_inner(events, frames, |i| panel[i])
    }

    fn render_inner(
        &mut self,
        events: &[Event],
        frames: &mut [Frame],
        #[cfg(pilot_returns)] panel: impl Fn(usize) -> Panel,
    ) -> Result<(), Error> {
        if frames.is_empty()
            || frames.len() > MAX_BLOCK
            || events.len() > 256
            || events.iter().any(|event| event.offset >= frames.len())
            || events
                .windows(2)
                .any(|pair| pair[0].offset > pair[1].offset)
        {
            return Err(Error::Input);
        }
        let mut candidate = self.clone();
        let mut output = [Frame::default(); MAX_BLOCK];
        let mut events = events.iter().peekable();
        for (offset, frame) in output[..frames.len()].iter_mut().enumerate() {
            while let Some(event) = events.next_if(|event| event.offset == offset) {
                candidate.event(event.message)?;
            }
            *frame = candidate.next(
                #[cfg(pilot_returns)]
                panel(offset),
            )?;
        }
        *self = candidate;
        frames.copy_from_slice(&output[..frames.len()]);
        Ok(())
    }
}
