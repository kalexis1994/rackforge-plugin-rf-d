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
const MAX_INPUT_CHANNELS: usize = cfg!(pilot_voice_external) as usize;

#[derive(Default)]
struct Guest {
    voice: Option<Voice<PILOT_FACTOR>>,
    #[cfg(pilot_returns)]
    controls: Controls,
    #[cfg(pilot_returns)]
    master: f64,
    #[cfg(pilot_voice_external)]
    overload: f64,
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
const VOICE_DEFAULTS: [f64; 11] = [72., 60., 100., 100., 5., 180., 70., 5., 240., 30., 0.];
#[cfg(all(pilot_voice_contours, not(pilot_oscillator_bank)))]
const DEFAULTS: [f64; 11] = VOICE_DEFAULTS;
#[cfg(pilot_oscillator_bank)]
const OSC_DEFAULTS: [f64; 15] = [0., 3., 2., 1., 3., 2., 0., 65., 0., 3., 2., 0., 55., 0., 1.];
#[cfg(pilot_oscillator_bank)]
const OSC_RANGES: [(f64, f64); OSC_DEFAULTS.len()] = [
    (-100., 100.), (0., 5.), (0., 5.), (0., 1.),
    (0., 5.), (0., 5.), (-9., 9.), (0., 100.), (0., 1.),
    (0., 5.), (0., 5.), (-9., 9.), (0., 100.), (0., 1.), (0., 1.),
];
#[cfg(pilot_oscillator_bank)]
const OSC_END: usize = VOICE_DEFAULTS.len() + OSC_DEFAULTS.len();
#[cfg(pilot_oscillator_bank)]
const FILTER_END: usize = OSC_END + 3;
#[cfg(pilot_oscillator_bank)]
const MOD_DEFAULTS: [f64; 6] = [0., 35., 0., 0., 0., 0.];
#[cfg(pilot_oscillator_bank)]
const MOD_END: usize = FILTER_END + MOD_DEFAULTS.len();
#[cfg(pilot_oscillator_bank)]
const KEYBOARD_END: usize = MOD_END + 2;
#[cfg(pilot_voice_external)]
const OVERLOAD_INDEX: u32 = (KEYBOARD_END + 2) as u32;
#[cfg(pilot_oscillator_bank)]
const CONTROL_COUNT: usize = if cfg!(pilot_voice_external) {
    KEYBOARD_END + 2
} else if cfg!(pilot_voice_performance) {
    KEYBOARD_END
} else if cfg!(pilot_voice_modulation) {
    MOD_END
} else if cfg!(pilot_voice_filter) {
    FILTER_END
} else {
    OSC_END
};
#[cfg(pilot_oscillator_bank)]
const DEFAULTS: [f64; CONTROL_COUNT] = {
    let mut values = [0.; CONTROL_COUNT];
    let mut index = 0;
    while index < values.len() {
        values[index] = if index < VOICE_DEFAULTS.len() {
            VOICE_DEFAULTS[index]
        } else if index < OSC_END {
            OSC_DEFAULTS[index - VOICE_DEFAULTS.len()]
        } else if (index >= FILTER_END) && (index < MOD_END) {
            MOD_DEFAULTS[index - FILTER_END]
        } else if index == MOD_END + 1 {
            120.
        } else if index == KEYBOARD_END + 1 {
            20.
        } else {
            0.
        };
        index += 1;
    }
    values
};
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
    #[cfg(pilot_voice_external)]
    if index >= KEYBOARD_END {
        return match index - KEYBOARD_END {
            0 if value == 0. || value == 1. => Some(index),
            1 if (0. ..=100.).contains(&value) => Some(index),
            _ => None,
        };
    }
    #[cfg(pilot_voice_performance)]
    if index >= MOD_END {
        return match index - MOD_END {
            0 if value == 0. || value == 1. => Some(index),
            1 if (1. ..=10_000.).contains(&value) => Some(index),
            _ => None,
        };
    }
    #[cfg(pilot_voice_modulation)]
    if index >= FILTER_END {
        return match index - FILTER_END {
            1 | 3 if (0. ..=100.).contains(&value) => Some(index),
            0 | 2 | 4 | 5 if value == 0. || value == 1. => Some(index),
            _ => None,
        };
    }
    #[cfg(pilot_voice_filter)]
    if index >= OSC_END {
        return match index - OSC_END {
            0 if (0. ..=100.).contains(&value) => Some(index),
            1 | 2 if value == 0. || value == 1. => Some(index),
            _ => None,
        };
    }
    #[cfg(pilot_oscillator_bank)]
    if let Some(osc_index) = index.checked_sub(VOICE_DEFAULTS.len()) {
        let &(min, max) = OSC_RANGES.get(osc_index)?;
        let discrete = matches!(index, 12..=16 | 19..=21 | 24..=25);
        return ((min..=max).contains(&value) && (!discrete || value.fract() == 0.)).then_some(index);
    }
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
            self.0[..VOICE_DEFAULTS.len()].try_into().unwrap();
        voice::Panel {
            #[cfg(not(pilot_oscillator_bank))]
            mixer_gain: mix * 0.01,
            #[cfg(pilot_oscillator_bank)]
            oscillators: self.oscillators(mix),
            #[cfg(pilot_voice_filter)]
            filter: voice::FilterControls {
                emphasis: self.0[OSC_END] * 0.01,
                tracking_thirds: self.0[OSC_END + 1] as u8 + 2 * self.0[OSC_END + 2] as u8,
            },
            #[cfg(pilot_voice_modulation)]
            modulation: voice::modulation::Controls {
                noise_pink: self.0[29] == 1.,
                noise_level: self.0[30] * 0.01,
                noise_enabled: self.0[31] == 1.,
                mix: self.0[32] * 0.01,
                oscillator: self.0[33] == 1.,
                filter: self.0[34] == 1.,
            },
            #[cfg(pilot_voice_performance)]
            keyboard: voice::keyboard::Controls {
                glide: self.0[MOD_END] == 1.,
                time_ms: self.0[MOD_END + 1],
            },
            #[cfg(pilot_voice_external)]
            external: voice::external::Controls {
                enabled: self.0[KEYBOARD_END] == 1.,
                level: self.0[KEYBOARD_END + 1] * 0.01,
                input: 0.,
            },
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

    #[cfg(pilot_oscillator_bank)]
    fn oscillators(self, osc1_level: f64) -> voice::oscillator::Panel {
        let [tune, range1, wave1, on1, range2, wave2, freq2, level2, on2,
             range3, wave3, freq3, level3, on3, tracking] =
            self.0[VOICE_DEFAULTS.len()..OSC_END].try_into().unwrap();
        let settings = |range, wave, semitones, level, enabled| voice::oscillator::Settings {
            range: range as usize,
            shape: wave as usize,
            semitones,
            level: level * 0.01,
            enabled: enabled == 1.,
        };
        voice::oscillator::Panel {
            oscillators: [
                settings(range1, wave1, 0., osc1_level, on1),
                settings(range2, wave2, freq2, level2, on2),
                settings(range3, wave3, freq3, level3, on3),
            ],
            tune_cents: tune,
            osc3_tracking: tracking == 1.,
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
        #[cfg(pilot_voice_external)] input: &[f32],
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
        for (_offset, ((panel, master), changes)) in panels[..frames.len()]
            .iter_mut()
            .zip(&mut masters)
            .zip(changes)
            .enumerate()
        {
            for (value, change) in controls.0.iter_mut().zip(changes) {
                if let Some(change) = change {
                    *value = change;
                }
            }
            *panel = controls.voice();
            #[cfg(pilot_voice_external)]
            if let Some(sample) = input.get(_offset).filter(|sample| sample.is_finite()) {
                panel.external.input = f64::from(sample.clamp(-1., 1.));
            }
            *master = controls.master();
        }
        self.voice
            .as_mut()
            .expect("prepared pilot")
            .render_panel(midi, frames, &panels[..frames.len()])
            .expect("pilot render");
        self.controls = controls;
        #[cfg(pilot_voice_external)]
        if let Some(frame) = frames.last() {
            self.overload = frame.overload;
        }
        for ((stereo, frame), master) in output.chunks_exact_mut(2).zip(frames).zip(masters) {
            // A full-scale fader move settles in 64 host frames.
            self.master += (master - self.master).clamp(-1. / 64., 1. / 64.);
            #[cfg(pilot_voice_contours)]
            let signal = frame.sample;
            #[cfg(pilot_oscillator_bank)]
            let signal = {
                let excess = (signal.abs() - 0.8).max(0.);
                signal.signum() * (signal.abs().min(0.8) + 0.2 * excess / (0.2 + excess))
            };
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
        #[cfg(pilot_voice_modulation)]
        (0xb0, 1, 0..=127) => Message::ModWheel(velocity),
        #[cfg(all(pilot_voice_modulation, not(pilot_voice_performance)))]
        (0xb0, 121, _) => Message::ModWheel(0),
        #[cfg(pilot_voice_performance)]
        (0xb0, 121, _) => Message::ResetControllers,
        #[cfg(pilot_voice_performance)]
        (0xe0, low @ 0..=127, high @ 0..=127) => Message::PitchBend(u16::from(low) | u16::from(high) << 7),
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
            || inputs as usize > MAX_INPUT_CHANNELS
            || outputs != 2
        {
            return false;
        }
        #[cfg(all(pilot_returns, not(pilot_oscillator_bank)))]
        {
            self.controls = Controls::default();
        }
        self.reset();
        true
    }

    fn reset(&mut self) {
        self.voice = Some(Voice::new());
        #[cfg(pilot_voice_external)]
        {
            self.overload = 0.;
        }
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
        #[cfg(pilot_voice_external)]
        if index == OVERLOAD_INDEX {
            return Some(self.overload);
        }
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
        let valid_length = bytes.len() == STATE_BYTES;
        #[cfg(pilot_oscillator_bank)]
        let valid_length = valid_length
            || bytes.len() == 4 + VOICE_DEFAULTS.len() * 8
            || bytes.len() == 4 + OSC_END * 8;
        #[cfg(pilot_voice_modulation)]
        let valid_length = valid_length || bytes.len() == 4 + FILTER_END * 8;
        #[cfg(pilot_voice_performance)]
        let valid_length = valid_length || bytes.len() == 4 + MOD_END * 8;
        #[cfg(pilot_voice_external)]
        let valid_length = valid_length || bytes.len() == 4 + KEYBOARD_END * 8;
        if !valid_length || &bytes[..4] != STATE_TAG {
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
        #[cfg(pilot_voice_external)]
        if id == "external_filter" {
            self.controls = Controls::default();
            self.controls.0[0] = 100.;
            self.controls.0[1] = 0.;
            self.controls.0[6] = 100.;
            self.controls.0[14] = 0.;
            self.controls.0[KEYBOARD_END] = 1.;
            self.controls.0[KEYBOARD_END + 1] = 60.;
            return true;
        }
        #[cfg(pilot_voice_modulation)]
        if id == "wheel_motion" {
            self.controls = Controls::default();
            self.controls.0[0] = 71.;
            self.controls.0[16] = 0.; // OSC2 triangle an octave below OSC1.
            self.controls.0[15] = 2.;
            self.controls.0[18] = 55.;
            self.controls.0[19] = 1.;
            self.controls.0[20] = 0.; // Free-running OSC3 in LO.
            self.controls.0[21] = 0.;
            self.controls.0[25] = 0.;
            self.controls.0[26] = 52.;
            self.controls.0[29] = 1.;
            self.controls.0[30] = 7.;
            self.controls.0[31] = 1.;
            self.controls.0[32] = 12.;
            self.controls.0[33] = 1.;
            self.controls.0[34] = 1.;
            return true;
        }
        #[cfg(pilot_voice_filter)]
        if id == "resonant_bass" {
            self.controls = Controls::default();
            self.controls.0[0] = 56.;
            self.controls.0[1] = 55.;
            self.controls.0[16] = 0.; // Lightly detuned triangle at the keyboard pitch.
            self.controls.0[17] = 0.06;
            self.controls.0[18] = 45.;
            self.controls.0[19] = 1.;
            self.controls.0[20] = 2.; // OSC3 sawtooth an octave below OSC1.
            self.controls.0[24] = 1.;
            self.controls.0[26] = 82.;
            self.controls.0[28] = 1.;
            return true;
        }
        #[cfg(pilot_oscillator_bank)]
        if id == "three_oscillators" {
            self.controls = Controls::default();
            self.controls.0[16] = 0.; // OSC2 triangle, fifth above OSC1.
            self.controls.0[17] = 7.;
            self.controls.0[19] = 1.;
            self.controls.0[20] = 2.; // OSC3 square, octave below OSC1.
            self.controls.0[21] = 3.;
            self.controls.0[24] = 1.;
            return true;
        }
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
        _input: &[f32],
        output: &mut [f32],
        midi: &[MidiEvent],
        _parameters: &[ParameterEvent],
        _: u32,
        _: u32,
        _: u32,
    ) {
        for (index, stereo) in output.chunks_mut(2 * voice::MAX_BLOCK).enumerate() {
            let first = index * voice::MAX_BLOCK;
            #[cfg(pilot_voice_external)]
            let input = if _input.is_empty() { &[] } else { &_input[first..first + stereo.len() / 2] };
            self.process_chunk(
                stereo, midi, _parameters, first,
                #[cfg(pilot_voice_external)]
                input,
            );
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
        #[cfg(pilot_voice_external)] input: &[f32],
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
        self.render_panel(
            &events[..count], _parameters, first_frame, block, output,
            #[cfg(pilot_voice_external)]
            input,
        );
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
    max_input_channels = MAX_INPUT_CHANNELS,
    max_output_channels = 2,
    max_midi_events = 256,
    max_parameter_events = 256,
    max_transfer_bytes = 4096
);
