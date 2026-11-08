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
}

impl<const FACTOR: usize> Voice<FACTOR> {
    pub fn new() -> Self {
        assert!(matches!(FACTOR, 4 | 8));
        Self {
            circuit: plant::State::dc(1).unwrap(),
            held: 0,
            phase: 0.,
            increment: 440. / (FACTOR * RATE) as f64,
            trim: 0.,
            history: [0.; 769],
            head: 0,
            frames: 0,
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

    fn next(&mut self) -> Result<Frame, Error> {
        let kernel = if FACTOR == 4 { &coefficients::H192000[..] } else { &coefficients::H384000[..] };
        let change = 1. / (RAMP_S * (RATE * FACTOR) as f64);
        let mut last = Frame::default();
        for _ in 0..FACTOR {
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
            let input = INPUT_PEAK_V * self.trim * (left + position.fract() * (right - left));
            let ports = plant::step(&mut self.circuit, input).map_err(Error::Plant)?;
            self.history[self.head] = ports.j7_v;
            self.head = (self.head + 1) % kernel.len();
            last.bus_v = ports.bus_v;
            last.c27_v = ports.base_v - ports.bus_v;
            last.panel_a = ports.panel_a;
        }
        self.frames += 1;
        if self.frames > LATENCY {
            let (first, second) = kernel.split_at(kernel.len() - self.head);
            last.j7_v = first.iter().zip(&self.history[self.head..kernel.len()])
                .chain(second.iter().zip(&self.history[..self.head]))
                .fold(0., |sum, (coefficient, value)| sum + coefficient * value);
        }
        Ok(last)
    }

    /// Events at one offset are applied in caller order. Failed blocks publish no state.
    pub fn render(&mut self, events: &[Event], frames: &mut [Frame]) -> Result<(), Error> {
        if frames.is_empty() || frames.len() > MAX_BLOCK || events.len() > 256
            || events.iter().any(|event| event.offset >= frames.len())
            || events.windows(2).any(|pair| pair[0].offset > pair[1].offset) {
            return Err(Error::Input);
        }
        let mut candidate = self.clone();
        let mut output = [Frame::default(); MAX_BLOCK];
        let mut events = events.iter().peekable();
        for (offset, frame) in output[..frames.len()].iter_mut().enumerate() {
            while let Some(event) = events.next_if(|event| event.offset == offset) {
                candidate.event(event.message)?;
            }
            *frame = candidate.next()?;
        }
        *self = candidate;
        frames.copy_from_slice(&output[..frames.len()]);
        Ok(())
    }
}
