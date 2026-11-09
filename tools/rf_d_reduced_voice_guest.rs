use rackforge_plugin_sdk::{export_processor, MidiEvent, ParameterEvent, Processor};
use voice::{Event, Frame, Message, Voice};

#[derive(Default)]
struct Guest {
    voice: Option<Voice<4>>,
    #[cfg(pilot_returns)]
    return_mv: [f64; 2],
}

#[cfg(pilot_returns)]
const RETURN_RANGE_MV: [f64; 2] = [15., 1.];

#[cfg(pilot_returns)]
fn return_index(index: u32, value: f64) -> Option<usize> {
    let index = index as usize;
    (value.abs() <= *RETURN_RANGE_MV.get(index)?).then_some(index)
}

#[cfg(pilot_returns)]
impl Guest {
    fn render_returns(
        &mut self,
        midi: &[Event],
        automation: &[ParameterEvent],
        frames: &mut [Frame],
    ) {
        let mut changes = [[None; 2]; voice::MAX_BLOCK];
        for event in automation {
            let index = return_index(event.index, event.value).expect("bounded return input");
            changes[event.frame as usize][index] = Some(event.value);
        }
        let mut mv = self.return_mv;
        let mut drives = [plant::Drive::default(); voice::MAX_BLOCK];
        for (drive, changes) in drives[..frames.len()].iter_mut().zip(changes) {
            for (value, change) in mv.iter_mut().zip(changes) {
                if let Some(change) = change {
                    *value = change;
                }
            }
            *drive = plant::Drive {
                volume_delta_v: mv[0] * 1e-3,
                filter_delta_v: mv[1] * 1e-3,
            };
        }
        self.voice
            .as_mut()
            .expect("prepared pilot")
            .render_with_returns(midi, frames, &drives[..frames.len()])
            .expect("pilot render");
        self.return_mv = mv;
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
            || !(1..=voice::MAX_BLOCK as u32).contains(&frames)
            || inputs != 0
            || outputs != 2
        {
            return false;
        }
        self.voice = Some(Voice::new());
        #[cfg(pilot_returns)]
        {
            self.return_mv = [0.; 2];
        }
        true
    }

    #[cfg(not(pilot_returns))]
    fn set_parameter(&mut self, _: u32, _: f64) -> bool {
        false
    }

    #[cfg(pilot_returns)]
    fn set_parameter(&mut self, index: u32, value: f64) -> bool {
        let Some(index) = return_index(index, value) else {
            return false;
        };
        self.return_mv[index] = value;
        true
    }

    #[cfg(pilot_returns)]
    fn get_parameter(&self, index: u32) -> Option<f64> {
        self.return_mv.get(index as usize).copied()
    }

    fn load_preset(&mut self, id: &str) -> bool {
        if id != "default" {
            return false;
        }
        #[cfg(pilot_returns)]
        {
            self.return_mv = [0.; 2];
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
        frames: u32,
        _: u32,
        _: u32,
    ) {
        let mut events = [Event {
            offset: 0,
            message: Message::AllNotesOff,
        }; 256];
        let mut count = 0;
        for event in midi.iter().filter_map(note_event) {
            events[count] = event;
            count += 1;
        }
        let mut result = [Frame::default(); voice::MAX_BLOCK];
        let block = &mut result[..frames as usize];
        #[cfg(not(pilot_returns))]
        self.voice
            .as_mut()
            .expect("prepared pilot")
            .render(&events[..count], block)
            .expect("pilot render");
        #[cfg(pilot_returns)]
        self.render_returns(&events[..count], _parameters, block);
        for (stereo, frame) in output.chunks_exact_mut(2).zip(block) {
            stereo.fill((frame.j7_v / voice::AUDITION_VOLTS_PER_FULL_SCALE) as f32);
        }
    }
}

export_processor!(
    Guest,
    max_frames = 128,
    max_input_channels = 0,
    max_output_channels = 2,
    max_midi_events = 256,
    max_parameter_events = 256,
    max_transfer_bytes = 4096
);
