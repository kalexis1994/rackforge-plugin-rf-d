use rackforge_plugin_sdk::{export_processor, MidiEvent, ParameterEvent, Processor};
use voice::{Event, Frame, Message, Voice};

#[cfg(pilot_pi)]
const PILOT_FACTOR: usize = 2;
#[cfg(not(pilot_pi))]
const PILOT_FACTOR: usize = 4;

// Desktop prepares for its maximum callback, independently of the device period.
const MAX_HOST_FRAMES: usize = if cfg!(pilot_host_blocks) {
    4096
} else {
    voice::MAX_BLOCK
};

#[derive(Default)]
struct Guest {
    voice: Option<Voice<PILOT_FACTOR>>,
    #[cfg(pilot_returns)]
    controls: Controls,
    #[cfg(pilot_returns)]
    master: f64,
}

#[cfg(all(pilot_returns, not(pilot_voice_contours)))]
const RANGES: [(f64, f64); 6] = [
    (-15., 15.),
    (-1., 1.),
    (0., 100.),
    (0., 100.),
    (1., 100.),
    (1., 200.),
];
#[cfg(all(pilot_returns, not(pilot_voice_contours)))]
const DEFAULTS: [f64; 6] = [0., 0., 100., 100., 5., 5.];
#[cfg(all(pilot_returns, not(pilot_voice_contours)))]
const STATE_TAG: &[u8; 4] = b"RFD1";
#[cfg(pilot_voice_contours)]
const RANGES: [(f64, f64); 11] = [
    (0., 100.), (0., 100.), (0., 100.), (0., 100.),
    (1., 2000.), (5., 5000.), (0., 100.),
    (1., 2000.), (5., 5000.), (0., 100.), (0., 1.),
];
#[cfg(pilot_voice_contours)]
const DEFAULTS: [f64; 11] = [72., 60., 100., 100., 5., 180., 70., 5., 240., 30., 0.];
#[cfg(pilot_voice_contours)]
const STATE_TAG: &[u8; 4] = b"RFDC";
#[cfg(pilot_returns)]
const STATE_BYTES: usize = 4 + DEFAULTS.len() * 8;

#[cfg(pilot_returns)]
#[derive(Clone, Copy)]
struct Controls([f64; DEFAULTS.len()]);

#[cfg(pilot_returns)]
impl Default for Controls {
    fn default() -> Self {
        Self(DEFAULTS)
    }
}

#[cfg(pilot_returns)]
fn control_index(index: u32, value: f64) -> Option<usize> {
    let index = index as usize;
    let &(min, max) = RANGES.get(index)?;
    (min..=max).contains(&value).then_some(index)
}

#[cfg(pilot_returns)]
impl Controls {
    #[cfg(not(pilot_voice_contours))]
    fn voice(self) -> voice::Panel {
        let [r59_mv, pin16_mv, mix, _, attack_ms, release_ms] = self.0;
        voice::Panel {
            drive: plant::Drive {
                volume_delta_v: r59_mv * 1e-3,
                filter_delta_v: pin16_mv * 1e-3,
            },
            mixer_gain: mix * 0.01,
            attack_ms,
            release_ms,
        }
    }

    #[cfg(pilot_voice_contours)]
    fn voice(self) -> voice::Panel {
        let [cutoff, amount, mix, _, volume_a, volume_d, volume_s, filter_a, filter_d, filter_s, decay] =
            self.0;
        voice::Panel {
            mixer_gain: mix * 0.01,
            contours: voice::Contours {
                volume: voice::contour::Settings {
                    attack_ms: volume_a,
                    decay_ms: volume_d,
                    sustain: volume_s * 0.01,
                },
                filter: voice::contour::Settings {
                    attack_ms: filter_a,
                    decay_ms: filter_d,
                    sustain: filter_s * 0.01,
                },
                cutoff: cutoff * 0.01,
                amount: amount * 0.01,
                decay_on: decay >= 0.5,
            },
        }
    }

    fn master(self) -> f64 {
        self.0[3] * 0.01
    }
}

#[cfg(pilot_returns)]
impl Guest {
    fn render_panel(
        &mut self,
        midi: &[Event],
        automation: &[ParameterEvent],
        first_frame: usize,
        frames: &mut [Frame],
        output: &mut [f32],
    ) {
        let mut changes = [[None; DEFAULTS.len()]; voice::MAX_BLOCK];
        let span = first_frame..first_frame + frames.len();
        for event in automation
            .iter()
            .filter(|event| span.contains(&(event.frame as usize)))
        {
            if let Some(index) = control_index(event.index, event.value) {
                changes[event.frame as usize - first_frame][index] = Some(event.value);
            }
        }
        let mut controls = self.controls;
        let mut panels = [voice::Panel::default(); voice::MAX_BLOCK];
        let mut masters = [0.; voice::MAX_BLOCK];
        for ((panel, master), changes) in panels[..frames.len()]
            .iter_mut()
            .zip(&mut masters)
            .zip(changes)
        {
            for (value, change) in controls.0.iter_mut().zip(changes) {
                if let Some(change) = change {
                    *value = change;
                }
            }
            *panel = controls.voice();
            *master = controls.master();
        }
        self.voice
            .as_mut()
            .expect("prepared pilot")
            .render_panel(midi, frames, &panels[..frames.len()])
            .expect("pilot render");
        self.controls = controls;
        for ((stereo, frame), master) in output.chunks_exact_mut(2).zip(frames).zip(masters) {
            // A full-scale fader move settles in 64 host frames.
            self.master += (master - self.master).clamp(-1. / 64., 1. / 64.);
            #[cfg(pilot_voice_contours)]
            let signal = frame.sample;
            #[cfg(not(pilot_voice_contours))]
            let signal = frame.j7_v / voice::AUDITION_VOLTS_PER_FULL_SCALE;
            let sample = if self.master == 0. {
                0.
            } else {
                (signal * self.master) as f32
            };
            stereo.fill(sample);
        }
    }
}

fn note_event(event: &MidiEvent) -> Option<Event> {
    let [status, note, velocity] = event.data;
    if event.length != 3 {
        return None;
    }
    let message = match (status & 0xf0, note, velocity) {
        (0x80, 36..=72, _) | (0x90, 36..=72, 0) => Message::NoteOff(note),
        (0x90, 36..=72, _) => Message::NoteOn(note),
        (0xb0, 120 | 123, _) => Message::AllNotesOff,
        _ => return None,
    };
    Some(Event {
        offset: event.frame as usize,
        message,
    })
}

impl Processor for Guest {
    fn prepare(&mut self, rate: f64, frames: u32, inputs: u32, outputs: u32) -> bool {
        if rate != voice::RATE as f64
            || !(1..=MAX_HOST_FRAMES as u32).contains(&frames)
            || inputs != 0
            || outputs != 2
        {
            return false;
        }
        #[cfg(pilot_returns)]
        {
            self.controls = Controls::default();
        }
        self.reset();
        true
    }

    fn reset(&mut self) {
        self.voice = Some(Voice::new());
        #[cfg(pilot_returns)]
        {
            self.master = self.controls.master();
        }
    }

    #[cfg(not(pilot_returns))]
    fn set_parameter(&mut self, _: u32, _: f64) -> bool {
        false
    }

    #[cfg(pilot_returns)]
    fn set_parameter(&mut self, index: u32, value: f64) -> bool {
        let Some(index) = control_index(index, value) else {
            return false;
        };
        self.controls.0[index] = value;
        true
    }

    #[cfg(pilot_returns)]
    fn get_parameter(&self, index: u32) -> Option<f64> {
        self.controls.0.get(index as usize).copied()
    }

    #[cfg(pilot_returns)]
    fn save_state(&self, destination: &mut [u8]) -> Option<usize> {
        let bytes = destination.get_mut(..STATE_BYTES)?;
        bytes[..4].copy_from_slice(STATE_TAG);
        for (value, word) in self
            .controls
            .0
            .into_iter()
            .zip(bytes[4..].chunks_exact_mut(8))
        {
            word.copy_from_slice(&value.to_le_bytes());
        }
        Some(STATE_BYTES)
    }

    #[cfg(pilot_returns)]
    fn load_state(&mut self, bytes: &[u8]) -> bool {
        if bytes.len() != STATE_BYTES || &bytes[..4] != STATE_TAG {
            return false;
        }
        let mut candidate = Controls::default();
        for (index, word) in bytes[4..].chunks_exact(8).enumerate() {
            let value = f64::from_le_bytes(word.try_into().unwrap());
            if control_index(index as u32, value).is_none() {
                return false;
            }
            candidate.0[index] = value;
        }
        self.controls = candidate;
        true
    }

    fn load_preset(&mut self, id: &str) -> bool {
        if id != "default" {
            return false;
        }
        #[cfg(pilot_returns)]
        {
            self.controls = Controls::default();
        }
        true
    }

    fn latency_frames(&self) -> u32 {
        voice::LATENCY as u32
    }

    fn process(
        &mut self,
        _: &[f32],
        output: &mut [f32],
        midi: &[MidiEvent],
        _parameters: &[ParameterEvent],
        _: u32,
        _: u32,
        _: u32,
    ) {
        for (index, stereo) in output.chunks_mut(2 * voice::MAX_BLOCK).enumerate() {
            self.process_chunk(stereo, midi, _parameters, index * voice::MAX_BLOCK);
        }
    }
}

impl Guest {
    fn process_chunk(
        &mut self,
        output: &mut [f32],
        midi: &[MidiEvent],
        _parameters: &[ParameterEvent],
        first_frame: usize,
    ) {
        let frames = output.len() / 2;
        let span = first_frame..first_frame + frames;
        let mut events = [Event {
            offset: 0,
            message: Message::AllNotesOff,
        }; 256];
        let mut count = 0;
        for mut event in midi
            .iter()
            .filter(|event| span.contains(&(event.frame as usize)))
            .filter_map(note_event)
        {
            event.offset -= first_frame;
            events[count] = event;
            count += 1;
        }
        let mut result = [Frame::default(); voice::MAX_BLOCK];
        let block = &mut result[..frames];
        #[cfg(pilot_returns)]
        self.render_panel(&events[..count], _parameters, first_frame, block, output);
        #[cfg(not(pilot_returns))]
        {
            self.voice
                .as_mut()
                .expect("prepared pilot")
                .render(&events[..count], block)
                .expect("pilot render");
            for (stereo, frame) in output.chunks_exact_mut(2).zip(block) {
                stereo.fill((frame.j7_v / voice::AUDITION_VOLTS_PER_FULL_SCALE) as f32);
            }
        }
    }
}

export_processor!(
    Guest,
    max_frames = MAX_HOST_FRAMES,
    max_input_channels = 0,
    max_output_channels = 2,
    max_midi_events = 256,
    max_parameter_events = 256,
    max_transfer_bytes = 4096
);
