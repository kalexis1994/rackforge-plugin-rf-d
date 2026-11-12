//! MIDI ownership and pedal gates for a single low-note-priority voice.

#[derive(Clone, Copy)]
pub enum Action {
    NoteOn(u8),
    NoteOff(u8),
    Sustain(bool),
    AllNotesOff,
    AllSoundOff,
    ResetControllers,
}

#[derive(Clone, Copy)]
struct Channel {
    counts: [u16; 128],
    pressed: u128,
    pedal: bool,
    sustained: bool,
}

impl Channel {
    const EMPTY: Self = Self { counts: [0; 128], pressed: 0, pedal: false, sustained: false };

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
    pub fn apply(&mut self, channel: u8, action: Action) -> bool {
        let Some(channel) = self.channels.get_mut(usize::from(channel)) else {
            return false;
        };
        match action {
            Action::NoteOn(note @ 0..=127) => {
                let count = &mut channel.counts[usize::from(note)];
                *count = count.saturating_add(1);
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
            Action::Sustain(down) => {
                channel.pedal = down;
                channel.sustained &= down;
            }
            Action::ResetControllers => {
                channel.pedal = false;
                channel.sustained = false;
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
