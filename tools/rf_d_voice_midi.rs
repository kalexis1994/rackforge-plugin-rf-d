//! MIDI ownership, keyboard expression and pedal gates for low-note priority.

#[derive(Clone, Copy)]
pub enum Action {
    NoteOn(u8, u8),
    NoteOff(u8),
    ChannelPressure(u8),
    PolyPressure(u8, u8),
    Sustain(bool),
    AllNotesOff,
    AllSoundOff,
    ResetControllers,
}

#[derive(Clone, Copy)]
struct Channel {
    counts: [u16; 128],
    velocities: [u8; 128],
    key_pressure: [u8; 128],
    pressure: u8,
    pressed: u128,
    pedal: bool,
    sustained: bool,
}

impl Channel {
    const EMPTY: Self = Self {
        counts: [0; 128], velocities: [0; 128], key_pressure: [0; 128], pressure: 0,
        pressed: 0, pedal: false, sustained: false,
    };

    fn release_keys(&mut self) {
        self.sustained |= self.pedal && self.pressed != 0;
        self.pressed = 0;
        self.counts.fill(0);
    }
}

#[derive(Clone)]
pub struct Notes {
    channels: [Channel; 16],
    pub pressed: u128,
    pub sustained: bool,
}

impl Default for Notes {
    fn default() -> Self {
        Self { channels: [Channel::EMPTY; 16], pressed: 0, sustained: false }
    }
}

impl Notes {
    pub fn expression(&self, note: u8) -> [u8; 2] {
        let mut expression = [0; 2];
        for channel in &self.channels {
            if channel.pressed & (1 << note) != 0 {
                let key = usize::from(note);
                expression[0] = expression[0].max(channel.velocities[key]);
                expression[1] = expression[1].max(channel.pressure.max(channel.key_pressure[key]));
            }
        }
        expression
    }

    pub fn apply(&mut self, channel: u8, action: Action) -> bool {
        let Some(channel) = self.channels.get_mut(usize::from(channel)) else {
            return false;
        };
        match action {
            Action::NoteOn(note @ 0..=127, velocity @ 1..=127) => {
                let key = usize::from(note);
                let count = &mut channel.counts[key];
                if *count == 0 {
                    channel.key_pressure[key] = 0;
                }
                *count = count.saturating_add(1);
                channel.velocities[key] = velocity;
                channel.pressed |= 1 << note;
            }
            Action::NoteOff(note @ 0..=127) => {
                let count = &mut channel.counts[usize::from(note)];
                if *count != 0 {
                    *count -= 1;
                    if *count == 0 {
                        channel.pressed &= !(1 << note);
                        channel.sustained |= channel.pedal;
                    }
                }
            }
            Action::ChannelPressure(pressure @ 0..=127) => {
                channel.pressure = pressure;
                return true;
            }
            Action::PolyPressure(note @ 0..=127, pressure @ 0..=127) => {
                if channel.pressed & (1 << note) != 0 {
                    channel.key_pressure[usize::from(note)] = pressure;
                }
                return true;
            }
            Action::Sustain(down) => {
                channel.pedal = down;
                channel.sustained &= down;
            }
            Action::ResetControllers => {
                channel.pedal = false;
                channel.sustained = false;
                channel.pressure = 0;
                channel.key_pressure.fill(0);
            }
            Action::AllNotesOff => channel.release_keys(),
            Action::AllSoundOff => {
                channel.release_keys();
                channel.sustained = false;
            }
            _ => return false,
        }
        self.pressed = 0;
        self.sustained = false;
        for channel in &self.channels {
            self.pressed |= channel.pressed;
            self.sustained |= channel.sustained;
        }
        true
    }
}
