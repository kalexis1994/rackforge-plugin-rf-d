use rackforge_plugin_sdk::{export_processor, MidiEvent, ParameterEvent, Processor};
use voice::{Event, Frame, Message, Voice};

#[derive(Default)]
struct Guest(Option<Voice<4>>);

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
    Some(Event { offset: event.frame as usize, message })
}

impl Processor for Guest {
    fn prepare(&mut self, rate: f64, frames: u32, inputs: u32, outputs: u32) -> bool {
        if rate != voice::RATE as f64 || !(1..=voice::MAX_BLOCK as u32).contains(&frames)
            || inputs != 0 || outputs != 2 {
            return false;
        }
        self.0 = Some(Voice::new());
        true
    }

    fn set_parameter(&mut self, _: u32, _: f64) -> bool { false }

    fn load_preset(&mut self, id: &str) -> bool { id == "default" }

    fn latency_frames(&self) -> u32 { voice::LATENCY as u32 }

    fn process(
        &mut self, _: &[f32], output: &mut [f32], midi: &[MidiEvent], _: &[ParameterEvent],
        frames: u32, _: u32, _: u32,
    ) {
        let mut events = [Event { offset: 0, message: Message::AllNotesOff }; 256];
        let mut count = 0;
        for event in midi.iter().filter_map(note_event) {
            events[count] = event;
            count += 1;
        }
        let mut result = [Frame::default(); voice::MAX_BLOCK];
        let block = &mut result[..frames as usize];
        self.0.as_mut().expect("prepared pilot").render(&events[..count], block).expect("pilot render");
        for (stereo, frame) in output.chunks_exact_mut(2).zip(block) {
            stereo.fill((frame.j7_v / voice::AUDITION_VOLTS_PER_FULL_SCALE) as f32);
        }
    }
}

export_processor!(
    Guest, max_frames = 128, max_input_channels = 0, max_output_channels = 2,
    max_midi_events = 256, max_parameter_events = 256, max_transfer_bytes = 4096
);
