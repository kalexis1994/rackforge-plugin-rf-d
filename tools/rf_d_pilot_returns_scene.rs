//! Repeatable pilot workload used only in the native and RackForge banks.
use crate::{plant::Drive, score::SCENE, voice::{Error, Event, Frame, Message, Voice, MAX_BLOCK}};

pub const LENGTH: usize = 48_128;

fn triangle(frame: usize, period: usize) -> f64 {
    let phase = (frame % period) as f64 / period as f64;
    1. - 4. * (phase - 0.5).abs()
}

pub struct Scene {
    voice: Voice<4>,
    frame: usize,
    driven: bool,
}

impl Scene {
    pub fn new(driven: bool) -> Self {
        Self { voice: Voice::new(), frame: 0, driven }
    }

    pub fn render(&mut self, frames: &mut [Frame]) -> Result<(), Error> {
        let start = self.frame % LENGTH;
        let mut events = [Event { offset: 0, message: Message::AllNotesOff }; 9];
        let mut count = 0;
        for i in 0..frames.len() {
            let at = (start + i) % LENGTH;
            for event in SCENE.iter().filter(|event| event.offset == at) {
                events[count] = Event { offset: i, message: event.message };
                count += 1;
            }
        }
        if self.driven {
            let drives: [Drive; MAX_BLOCK] = std::array::from_fn(|i| Drive {
                volume_delta_v: 0.014 * triangle(self.frame + i + 120, 480),
                filter_delta_v: 0.0009 * triangle(self.frame + i + 73, 292),
            });
            self.voice.render_with_returns(&events[..count], frames, &drives[..frames.len()])?;
        } else {
            self.voice.render(&events[..count], frames)?;
        }
        self.frame += frames.len();
        Ok(())
    }
}
