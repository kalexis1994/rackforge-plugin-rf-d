use rackforge_plugin_sdk::{export_processor, MidiEvent, ParameterEvent, Processor};
pub use rf_d_circuit::{junction_charge, StepError};

#[path = "MONO_VOICE_PATH"]
mod mono;
#[path = "MONO_PATCH_PATH"]
mod patch;

use mono::{Event, Message, Stats, Voice, Workspace};

#[derive(Default)]
struct Guest {
    voice: Option<Voice>,
    work: Option<Box<Workspace>>,
    stats: Stats,
}

fn note_event(event: &MidiEvent) -> Option<Event> {
    let [status, note, velocity] = event.data;
    let message = match (status & 0xf0, event.length) {
        (0x80, 3) => Message::NoteOff { note },
        (0x90, 3) => Message::NoteOn { note, velocity },
        (0xb0, 3) if note == 123 => Message::AllNotesOff,
        _ => return None,
    };
    Some(Event { offset: event.frame as usize, message })
}

impl Processor for Guest {
    fn prepare(&mut self, rate: f64, frames: u32, inputs: u32, outputs: u32) -> bool {
        if rate != 48000. || !(1..=128).contains(&frames) || inputs != 0 || outputs != 2 {
            return false;
        }
        let (circuit, conversion, headphone) = patch::lab_parameters();
        let parameters = rf_d_circuit::chain_charge::Parameters {
            circuit, conversion, headphone, boundary: patch::controlled_boundary(0, true),
            mixer: rf_d_circuit::mixer_on::OnMixer::new([false; 5], [0.5; 4]).unwrap(),
        };
        let Ok(voice) = Voice::cold_start(parameters) else { return false; };
        self.voice = Some(voice);
        self.work = Some(Box::new(Workspace::new()));
        self.stats = Stats::default();
        true
    }

    fn set_parameter(&mut self, _: u32, _: f64) -> bool { false }
    fn load_preset(&mut self, id: &str) -> bool { id == "default" }
    fn latency_frames(&self) -> u32 { mono::LATENCY as u32 }

    fn process(
        &mut self, _: &[f32], output: &mut [f32], midi: &[MidiEvent], _: &[ParameterEvent],
        frames: u32, inputs: u32, outputs: u32,
    ) {
        assert!(inputs == 0 && outputs == 2 && output.len() == 2 * frames as usize);
        let mut events = [Event { offset: 0, message: Message::AllNotesOff }; 256];
        let mut count = 0;
        for event in midi.iter().filter_map(note_event) {
            events[count] = event;
            count += 1;
        }
        let mut volts = [0.; mono::MAX_BLOCK];
        let block = &mut volts[..frames as usize];
        self.stats = self.voice.as_mut().unwrap()
            .render_block(self.work.as_deref_mut().unwrap(), &events[..count], block)
            .expect("RF-D nominal electrical solve");
        for (frame, volts) in output.chunks_exact_mut(2).zip(block) {
            frame.fill(*volts as f32);
        }
    }
}

export_processor!(
    Guest, max_frames = 128, max_input_channels = 0, max_output_channels = 2,
    max_midi_events = 256, max_parameter_events = 256, max_transfer_bytes = 4096
);

// Read-only diagnostic. The bench calls this after processing, outside the callback.
static mut OBSERVATION: [f64; 242] = [0.; 242];

#[no_mangle]
pub extern "C" fn rf_d_mono_observation() -> i32 {
    unsafe {
        if !RF_PREPARED { return 0; }
        let guest = &*std::ptr::addr_of!(RF_PROCESSOR).cast::<Guest>();
        let voice = guest.voice.as_ref().unwrap();
        let state = voice.state();
        let out = &mut *std::ptr::addr_of_mut!(OBSERVATION);
        out[..118].copy_from_slice(&state.high);
        out[118..236].copy_from_slice(&state.low);
        out[236..].copy_from_slice(&[
            voice.samples() as f64, guest.stats.calls as f64, guest.stats.attempts as f64,
            guest.stats.max_residual_a, guest.stats.max_correction_v, guest.stats.max_error,
        ]);
        std::ptr::addr_of!(OBSERVATION) as i32
    }
}
