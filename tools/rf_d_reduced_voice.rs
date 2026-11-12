//! Monophonic RF-D voice, with distinct laboratory and playable signal paths.
#[cfg(not(pilot_pi))]
use crate::coefficients;
#[cfg(not(pilot_voice_contours))]
use crate::plant;
#[cfg(not(pilot_oscillator_bank))]
use crate::wave;
#[cfg(pilot_oscillator_bank)]
#[path = "rf_d_voice_oscillators.rs"]
pub mod oscillator;
#[cfg(pilot_voice_modulation)]
#[path = "rf_d_voice_modulation.rs"]
pub mod modulation;
#[cfg(pilot_voice_performance)]
#[path = "rf_d_voice_keyboard.rs"]
pub mod keyboard;
#[cfg(pilot_voice_external)]
#[path = "rf_d_voice_external.rs"]
pub mod external;
#[cfg(pilot_voice_feedback)]
#[path = "rf_d_voice_feedback.rs"]
pub mod feedback;
#[cfg(pilot_voice_contours)]
#[path = "rf_d_voice_contour.rs"]
pub mod contour;
#[cfg(pilot_voice_contours)]
#[path = "rf_d_voice_ladder.rs"]
mod ladder;
#[cfg(pilot_voice_filter)]
pub use ladder::Controls as FilterControls;

pub const MAX_BLOCK: usize = 128;
pub const RATE: usize = 48_000;
pub const LATENCY: usize = 48;
pub const AUDITION_VOLTS_PER_FULL_SCALE: f64 = 0.000125;
const INPUT_PEAK_V: f64 = 0.08;
const RAMP_S: f64 = 0.005;
#[cfg(not(pilot_oscillator_bank))]
const TABLE: usize = wave::SAW.len();

#[derive(Clone, Copy)]
pub enum Message {
    NoteOn(u8),
    NoteOff(u8),
    AllNotesOff,
    #[cfg(pilot_voice_modulation)]
    ModWheel(u8),
    #[cfg(pilot_voice_performance)]
    PitchBend(u16),
    #[cfg(pilot_voice_performance)]
    ResetControllers,
}

#[derive(Clone, Copy)]
pub struct Event {
    pub offset: usize,
    pub message: Message,
}

#[derive(Clone, Copy, Debug)]
pub enum Error {
    Input,
    #[cfg(not(pilot_voice_contours))]
    Plant(plant::Error),
}

#[derive(Clone, Copy, Debug, Default, PartialEq)]
pub struct Frame {
    #[cfg(pilot_voice_external)]
    pub overload: f64,
    #[cfg(not(pilot_voice_contours))]
    pub j7_v: f64,
    #[cfg(pilot_voice_contours)]
    pub sample: f64,
    #[cfg(not(pilot_voice_contours))]
    pub bus_v: f64,
    #[cfg(not(pilot_voice_contours))]
    pub c27_v: f64,
    #[cfg(not(pilot_voice_contours))]
    pub panel_a: f64,
    #[cfg(all(pilot_returns, not(pilot_voice_contours)))]
    pub returns_a: [f64; 2],
}

#[cfg(pilot_returns)]
#[derive(Clone, Copy)]
pub struct Panel {
    #[cfg(not(pilot_voice_contours))]
    pub drive: plant::Drive,
    #[cfg(not(pilot_oscillator_bank))]
    pub mixer_gain: f64,
    #[cfg(pilot_oscillator_bank)]
    pub oscillators: oscillator::Panel,
    #[cfg(not(pilot_voice_contours))]
    pub attack_ms: f64,
    #[cfg(not(pilot_voice_contours))]
    pub release_ms: f64,
    #[cfg(pilot_voice_contours)]
    pub contours: Contours,
    #[cfg(pilot_voice_filter)]
    pub filter: FilterControls,
    #[cfg(pilot_voice_modulation)]
    pub modulation: modulation::Controls,
    #[cfg(pilot_voice_performance)]
    pub keyboard: keyboard::Controls,
    #[cfg(pilot_voice_external)]
    pub external: external::Controls,
    #[cfg(pilot_voice_feedback)]
    pub feedback: feedback::Controls,
}

#[cfg(pilot_voice_contours)]
#[derive(Clone, Copy, Default)]
pub struct Contours {
    pub volume: contour::Settings,
    pub filter: contour::Settings,
    pub cutoff: f64,
    pub amount: f64,
    pub decay_on: bool,
}

#[cfg(pilot_returns)]
impl Default for Panel {
    fn default() -> Self {
        Self {
            #[cfg(not(pilot_voice_contours))]
            drive: plant::Drive::default(),
            #[cfg(not(pilot_oscillator_bank))]
            mixer_gain: 1.,
            #[cfg(pilot_oscillator_bank)]
            oscillators: oscillator::Panel::default(),
            #[cfg(not(pilot_voice_contours))]
            attack_ms: RAMP_S * 1000.,
            #[cfg(not(pilot_voice_contours))]
            release_ms: RAMP_S * 1000.,
            #[cfg(pilot_voice_contours)]
            contours: Contours::default(),
            #[cfg(pilot_voice_filter)]
            filter: FilterControls::default(),
            #[cfg(pilot_voice_modulation)]
            modulation: modulation::Controls::default(),
            #[cfg(pilot_voice_performance)]
            keyboard: keyboard::Controls::default(),
            #[cfg(pilot_voice_external)]
            external: external::Controls::default(),
            #[cfg(pilot_voice_feedback)]
            feedback: feedback::Controls::default(),
        }
    }
}

#[cfg(pilot_returns)]
impl Panel {
    fn valid(self) -> bool {
        #[cfg(not(pilot_voice_contours))]
        let contour_valid = self.drive.valid()
            && (1. ..=100.).contains(&self.attack_ms)
            && (1. ..=200.).contains(&self.release_ms);
        #[cfg(pilot_voice_contours)]
        let contour_valid = self.contours.volume.valid()
            && self.contours.filter.valid()
            && (0. ..=1.).contains(&self.contours.cutoff)
            && (0. ..=1.).contains(&self.contours.amount);
        #[cfg(not(pilot_oscillator_bank))]
        let mixer_valid = (0. ..=1.).contains(&self.mixer_gain);
        #[cfg(pilot_oscillator_bank)]
        let mixer_valid = self.oscillators.valid();
        #[cfg(pilot_voice_filter)]
        let filter_valid = self.filter.valid();
        #[cfg(not(pilot_voice_filter))]
        let filter_valid = true;
        #[cfg(pilot_voice_modulation)]
        let modulation_valid = self.modulation.valid();
        #[cfg(not(pilot_voice_modulation))]
        let modulation_valid = true;
        #[cfg(pilot_voice_performance)]
        let keyboard_valid = self.keyboard.valid();
        #[cfg(not(pilot_voice_performance))]
        let keyboard_valid = true;
        #[cfg(pilot_voice_external)]
        let external_valid = self.external.valid();
        #[cfg(not(pilot_voice_external))]
        let external_valid = true;
        #[cfg(pilot_voice_feedback)]
        let feedback_valid = self.feedback.valid();
        #[cfg(not(pilot_voice_feedback))]
        let feedback_valid = true;
        mixer_valid && contour_valid && filter_valid && modulation_valid && keyboard_valid
            && external_valid && feedback_valid
    }
}

#[derive(Clone)]
pub struct Voice<const FACTOR: usize> {
    #[cfg(not(pilot_voice_contours))]
    circuit: plant::State,
    #[cfg(pilot_voice_contours)]
    ladder: ladder::Ladder,
    held: u64,
    #[cfg(pilot_voice_filter)]
    last_note: u8,
    #[cfg(not(pilot_oscillator_bank))]
    phase: f64,
    #[cfg(pilot_oscillator_bank)]
    oscillators: oscillator::Bank,
    #[cfg(pilot_voice_modulation)]
    modulation: modulation::Sources,
    #[cfg(pilot_voice_performance)]
    keyboard: keyboard::Keyboard,
    #[cfg(pilot_voice_external)]
    external: external::Preamp,
    #[cfg(pilot_voice_feedback)]
    feedback: feedback::Loop,
    increment: f64,
    #[cfg(not(pilot_voice_contours))]
    trim: f64,
    #[cfg(pilot_voice_contours)]
    contours: [contour::Contour; 2],
    history: [f64; 769],
    head: usize,
    frames: usize,
    #[cfg(all(pilot_returns, not(pilot_voice_contours)))]
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
            #[cfg(not(pilot_voice_contours))]
            circuit: plant::State::dc(1).unwrap(),
            #[cfg(pilot_voice_contours)]
            ladder: ladder::Ladder::new((RATE * FACTOR) as f64),
            held: 0,
            #[cfg(pilot_voice_filter)]
            last_note: 57,
            #[cfg(not(pilot_oscillator_bank))]
            phase: 0.,
            #[cfg(pilot_oscillator_bank)]
            oscillators: oscillator::Bank::new((RATE * FACTOR) as f64, FACTOR),
            #[cfg(pilot_voice_modulation)]
            modulation: modulation::Sources::new((RATE * FACTOR) as f64, FACTOR),
            #[cfg(pilot_voice_performance)]
            keyboard: keyboard::Keyboard::new((RATE * FACTOR) as f64, FACTOR),
            #[cfg(pilot_voice_external)]
            external: external::Preamp::new((RATE * FACTOR) as f64, FACTOR),
            #[cfg(pilot_voice_feedback)]
            feedback: feedback::Loop::new(FACTOR),
            increment: 440. / (FACTOR * RATE) as f64,
            #[cfg(not(pilot_voice_contours))]
            trim: 0.,
            #[cfg(pilot_voice_contours)]
            contours: [contour::Contour::default(); 2],
            history: [0.; 769],
            head: 0,
            frames: 0,
            #[cfg(all(pilot_returns, not(pilot_voice_contours)))]
            drive: plant::Drive::default(),
        }
    }

    fn event(&mut self, message: Message) -> Result<(), Error> {
        #[cfg(pilot_voice_modulation)]
        if let Message::ModWheel(value) = message {
            if value > 127 {
                return Err(Error::Input);
            }
            self.modulation.set_wheel(value);
            return Ok(());
        }
        #[cfg(pilot_voice_performance)]
        match message {
            Message::PitchBend(value @ 0..=16383) => {
                self.keyboard.set_bend(value);
                return Ok(());
            }
            Message::ResetControllers => {
                self.keyboard.set_bend(8192);
                self.modulation.set_wheel(0);
                return Ok(());
            }
            _ => {}
        }
        #[cfg(pilot_voice_contours)]
        let was_held = self.held != 0;
        match message {
            Message::NoteOn(note @ 36..=72) => self.held |= 1 << (note - 36),
            Message::NoteOff(note @ 36..=72) => self.held &= !(1 << (note - 36)),
            Message::AllNotesOff => self.held = 0,
            _ => return Err(Error::Input),
        }
        #[cfg(pilot_voice_contours)]
        if was_held != (self.held != 0) {
            for contour in &mut self.contours {
                contour.gate(self.held != 0);
            }
        }
        if self.held != 0 {
            let note = self.held.trailing_zeros() + 36;
            #[cfg(pilot_voice_filter)]
            {
                self.last_note = note as u8;
            }
            #[cfg(pilot_voice_performance)]
            self.keyboard.select(note as u8);
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
        #[cfg(all(pilot_returns, not(pilot_voice_contours)))]
        let ramp_s = 0.001
            * if self.held != 0 {
                panel.attack_ms
            } else {
                panel.release_ms
            };
        #[cfg(not(pilot_voice_contours))]
        let change = 1. / (ramp_s * (RATE * FACTOR) as f64);
        #[cfg(not(pilot_returns))]
        let input_peak = INPUT_PEAK_V;
        #[cfg(all(pilot_returns, not(pilot_oscillator_bank)))]
        let input_peak = INPUT_PEAK_V * panel.mixer_gain;
        let mut last = Frame::default();
        for _substep in 0..FACTOR {
            #[cfg(not(pilot_voice_contours))]
            let input_gain = {
                if self.held != 0 {
                    self.trim = (self.trim + change).min(1.);
                } else {
                    self.trim = (self.trim - change).max(0.);
                }
                self.trim
            };
            #[cfg(all(pilot_voice_contours, not(pilot_oscillator_bank)))]
            let input_gain = 1.;
            #[cfg(not(pilot_oscillator_bank))]
            let input = {
                self.phase += self.increment;
                if self.phase >= 1. {
                    self.phase -= 1.;
                }
                let position = self.phase * TABLE as f64;
                let index = position as usize;
                let left = wave::SAW[index % TABLE];
                let right = wave::SAW[(index + 1) % TABLE];
                input_peak * input_gain * (left + position.fract() * (right - left))
            };
            #[cfg(pilot_voice_modulation)]
            let (noise, modulation) = self.modulation.step(panel.modulation, self.oscillators.osc3());
            #[cfg(pilot_voice_external)]
            let noise = {
                let ext = self.external.tick(
                    panel.external, (_substep + 1) as f64 / FACTOR as f64,
                    #[cfg(pilot_voice_feedback)]
                    self.feedback.jack(panel.feedback.connected),
                );
                [noise[0] + ext[0], noise[1] + ext[1]]
            };
            #[cfg(all(pilot_voice_filter, not(pilot_voice_performance)))]
            let key_cv = f64::from(self.last_note);
            #[cfg(pilot_voice_performance)]
            let (key_cv, bend) = self.keyboard.tick(self.held != 0, panel.keyboard);
            #[cfg(pilot_oscillator_bank)]
            let increment = self.increment;
            #[cfg(pilot_voice_performance)]
            let increment = if key_cv == f64::from(self.last_note) {
                increment
            } else {
                increment * ((key_cv - f64::from(self.last_note)) / 12.).exp2()
            };
            #[cfg(pilot_oscillator_bank)]
            let input = INPUT_PEAK_V * self.oscillators.sample(
                panel.oscillators,
                increment,
                #[cfg(pilot_voice_modulation)]
                noise,
                #[cfg(pilot_voice_modulation)]
                if panel.modulation.oscillator { modulation * modulation::PITCH_OCTAVES } else { 0. },
                #[cfg(pilot_voice_performance)]
                bend,
            );
            #[cfg(not(pilot_returns))]
            let ports = plant::step(&mut self.circuit, input).map_err(Error::Plant)?;
            #[cfg(all(pilot_returns, not(pilot_voice_contours)))]
            let ports = plant::step(
                &mut self.circuit,
                input,
                self.drive.interpolate(panel.drive, (_substep + 1) as f64 / FACTOR as f64),
            )
            .map_err(Error::Plant)?;
            #[cfg(pilot_voice_contours)]
            {
                let rate = (RATE * FACTOR) as f64;
                let settings = panel.contours;
                let volume = self.contours[0].tick(settings.volume, settings.decay_on, rate);
                let filter = self.contours[1].tick(settings.filter, settings.decay_on, rate);
                let cutoff = settings.cutoff + (1. - settings.cutoff) * settings.amount * filter;
                let filtered_v = self.ladder.step(
                    input,
                    cutoff,
                    #[cfg(pilot_voice_filter)]
                    panel.filter,
                    #[cfg(pilot_voice_filter)]
                    key_cv,
                    #[cfg(pilot_voice_modulation)]
                    if panel.modulation.filter { modulation * modulation::FILTER_OCTAVES } else { 0. },
                );
                let post_vca = (filtered_v / INPUT_PEAK_V) * volume;
                #[cfg(pilot_voice_feedback)]
                self.feedback.observe(post_vca, panel.feedback.output_level);
                self.history[self.head] = post_vca;
            }
            #[cfg(not(pilot_voice_contours))]
            {
                self.history[self.head] = ports.j7_v;
                last.bus_v = ports.bus_v;
                last.c27_v = ports.base_v - ports.bus_v;
                last.panel_a = ports.panel_a;
                #[cfg(pilot_returns)]
                {
                    last.returns_a = ports.returns_a;
                }
            }
            self.head = (self.head + 1) % kernel.len();
        }
        #[cfg(all(pilot_returns, not(pilot_voice_contours)))]
        {
            self.drive = panel.drive;
        }
        #[cfg(pilot_voice_external)]
        {
            last.overload = self.external.overload();
        }
        self.frames += 1;
        if self.frames > LATENCY {
            let (first, second) = kernel.split_at(kernel.len() - self.head);
            let filtered = first
                .iter()
                .zip(&self.history[self.head..kernel.len()])
                .chain(second.iter().zip(&self.history[..self.head]))
                .fold(0., |sum, (coefficient, value)| sum + coefficient * value);
            #[cfg(pilot_voice_contours)]
            {
                last.sample = filtered;
            }
            #[cfg(not(pilot_voice_contours))]
            {
                last.j7_v = filtered;
            }
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

    #[cfg(all(pilot_returns, not(pilot_voice_contours)))]
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
