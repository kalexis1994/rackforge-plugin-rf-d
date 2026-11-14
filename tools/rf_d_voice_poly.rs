//! Keyboard allocation for the optional RF-D polyphonic mode.
use super::{midi::Action, Frame, Message, Panel, Voice};

pub const MAX_VOICES: usize = 6;
const QUIET_FRAMES: usize = 128;

struct Slot<const FACTOR: usize> {
    voice: Voice<FACTOR>,
    key: Option<(u8, u8)>,
    pressed: u16,
    key_pressure: u8,
    sustained: bool,
    active: bool,
    serial: u64,
    quiet: usize,
}

impl<const FACTOR: usize> Slot<FACTOR> {
    fn new() -> Self {
        let mut voice = Voice::new();
        voice.poly_gate = Some(false);
        Self { voice, key: None, pressed: 0, key_pressure: 0, sustained: false, active: false, serial: 0, quiet: 0 }
    }

    fn held(&self) -> bool {
        self.pressed != 0 || self.sustained
    }

    fn start(&mut self, key: (u8, u8), pressed: u16, serial: u64, velocity: u8, pressure: u8) {
        if self.key != Some(key) || self.pressed == 0 {
            self.key_pressure = 0;
        }
        self.key = Some(key);
        self.pressed = pressed;
        self.sustained = false;
        self.active = true;
        self.serial = serial;
        self.quiet = 0;
        self.voice.select_note(key.1);
        self.voice.velocity = velocity;
        self.voice.pressure = pressure.max(self.key_pressure);
        self.voice.poly_gate = Some(true);
        // The attack starts from the charge left on this voice card.
        for contour in &mut self.voice.contours {
            contour.gate(true);
        }
    }

    fn release(&mut self, sustain: bool) {
        let previous = self.voice.contour_gate();
        self.pressed = 0;
        self.key_pressure = 0;
        self.voice.pressure = 0;
        self.sustained = sustain;
        self.voice.poly_gate = Some(sustain);
        self.voice.update_contour_gate(previous);
    }
}

pub struct Polyphony<const FACTOR: usize> {
    slots: [Slot<FACTOR>; MAX_VOICES],
    // Held keys can outlive their sounding voice after a steal.
    keys: [[u16; 128]; 16],
    pedals: [bool; 16],
    pressure: [u8; 16],
    cursor: usize,
    serial: u64,
}

impl<const FACTOR: usize> Polyphony<FACTOR> {
    pub fn new() -> Self {
        Self {
            slots: std::array::from_fn(|_| Slot::new()), keys: [[0; 128]; 16],
            pedals: [false; 16], pressure: [0; 16], cursor: 0, serial: 0,
        }
    }

    fn note_on(&mut self, channel: u8, note: u8, velocity: u8, count: usize) {
        let key = (channel, note);
        let pressed = &mut self.keys[usize::from(channel)][usize::from(note)];
        *pressed = pressed.saturating_add(1);
        let pressed = *pressed;
        let slots = &mut self.slots[..count];
        let slot = slots.iter().position(|slot| slot.key == Some(key))
            .or_else(|| (0..count).map(|i| (self.cursor + i) % count).find(|&i| !slots[i].active))
            .or_else(|| (0..count).filter(|&i| !slots[i].held()).min_by_key(|&i| slots[i].serial))
            .unwrap_or_else(|| (0..count).min_by_key(|&i| slots[i].serial).unwrap());
        self.serial = self.serial.wrapping_add(1);
        slots[slot].start(key, pressed, self.serial, velocity, self.pressure[usize::from(channel)]);
        self.cursor = (slot + 1) % count;
    }

    pub fn event(&mut self, message: Message, count: usize) {
        let Message::Midi(channel, action) = message else { return };
        let channel_index = usize::from(channel);
        match action {
            Action::NoteOn(note, velocity) => self.note_on(channel, note, velocity, count),
            Action::NoteOff(note) => {
                let pressed = &mut self.keys[channel_index][usize::from(note)];
                if *pressed == 0 { return; }
                *pressed -= 1;
                if let Some(slot) = self.slots[..count].iter_mut().find(|s| s.key == Some((channel, note))) {
                    slot.pressed = *pressed;
                    if *pressed == 0 {
                        slot.release(self.pedals[channel_index]);
                    }
                }
            }
            Action::ChannelPressure(pressure) => {
                self.pressure[channel_index] = pressure;
                for slot in &mut self.slots[..count] {
                    if slot.pressed != 0 && slot.key.map(|key| key.0) == Some(channel) {
                        slot.voice.pressure = pressure.max(slot.key_pressure);
                    }
                }
            }
            Action::PolyPressure(note, pressure) => {
                if let Some(slot) = self.slots[..count].iter_mut()
                    .find(|slot| slot.pressed != 0 && slot.key == Some((channel, note)))
                {
                    slot.key_pressure = pressure;
                    slot.voice.pressure = pressure.max(self.pressure[channel_index]);
                }
            }
            action => {
                match action {
                    Action::Sustain(down) => self.pedals[channel_index] = down,
                    Action::ResetControllers => {
                        self.pedals[channel_index] = false;
                        self.pressure[channel_index] = 0;
                    }
                    Action::AllNotesOff | Action::AllSoundOff => self.keys[channel_index].fill(0),
                    _ => unreachable!(),
                }
                for slot in &mut self.slots[..count] {
                    if slot.key.map(|key| key.0) != Some(channel) { continue; }
                    if matches!(action, Action::ResetControllers) {
                        slot.key_pressure = 0;
                        slot.voice.pressure = 0;
                    }
                    match action {
                        Action::AllSoundOff => {
                            let trigger = slot.voice.trigger_closed;
                            *slot = Slot::new();
                            slot.voice.set_trigger(trigger);
                        }
                        Action::AllNotesOff if slot.held() => slot.release(self.pedals[channel_index]),
                        Action::Sustain(false) | Action::ResetControllers if slot.sustained => slot.release(false),
                        _ => {}
                    }
                }
            }
        }
    }

    pub fn trigger(&mut self, closed: bool) {
        self.slots[0].voice.set_trigger(closed);
    }

    pub fn next(&mut self, count: usize, mut panel: Panel) -> Frame {
        let mut mix = Frame::default();
        // Fixed headroom for the chosen limit avoids level jumps when notes are released.
        let gain = [0., 1., std::f64::consts::FRAC_1_SQRT_2,
            0.577_350_269_189_625_8, 0.5, 0.447_213_595_499_957_9, 0.408_248_290_463_863_1][count];
        for (i, slot) in self.slots[..count].iter_mut().enumerate() {
            // The physical reference oscillator and trigger belong to one panel.
            if i != 0 {
                panel.output.tuner = false;
            }
            if !slot.active && i != 0 { continue; }
            let frame = slot.voice.next(panel).expect("polyphonic RF-D frame");
            mix.sample += frame.sample * gain;
            mix.overload = mix.overload.max(frame.overload);
            if slot.active && !slot.voice.contour_gate() && slot.voice.contours[0].idle()
                && frame.sample.abs() < 1e-5
            {
                slot.quiet += 1;
                if slot.quiet == QUIET_FRAMES {
                    slot.active = false;
                }
            } else {
                slot.quiet = 0;
            }
        }
        let excess = (mix.sample.abs() - 0.8).max(0.);
        if excess > 0. {
            mix.sample = mix.sample.signum() * (0.8 + 0.2 * excess / (0.2 + excess));
        }
        mix
    }
}
