// Appended to the frozen DSP adapter when building the wasm-v1 guest.
use rackforge_plugin_sdk::{MidiEvent, ParameterEvent, Processor, export_processor};

struct Guest {
    handle: *mut c_void,
    raw: [f64; 1024],
    filtered: [f64; 128],
}

impl Default for Guest {
    fn default() -> Self {
        Self { handle: std::ptr::null_mut(), raw: [0.; 1024], filtered: [0.; 128] }
    }
}

impl Drop for Guest {
    fn drop(&mut self) {
        if !self.handle.is_null() {
            unsafe { rf_free(self.handle) };
        }
    }
}

impl Processor for Guest {
    fn prepare(&mut self, rate: f64, frames: u32, inputs: u32, outputs: u32) -> bool {
        if rate != 48000. || frames > 128 || inputs != 0 || outputs != 2 {
            return false;
        }
        if !cfg!(engine_silence) {
            if !self.handle.is_null() {
                unsafe { rf_free(self.handle) };
            }
            self.handle = rf_new();
        }
        true
    }

    fn set_parameter(&mut self, _: u32, _: f64) -> bool { false }

    fn load_preset(&mut self, id: &str) -> bool { id == "default" }

    fn latency_frames(&self) -> u32 { 48 }

    fn process(
        &mut self,
        _: &[f32],
        output: &mut [f32],
        _: &[MidiEvent],
        _: &[ParameterEvent],
        frames: u32,
        _: u32,
        _: u32,
    ) {
        if cfg!(engine_silence) {
            output.fill(0.);
            return;
        }
        let produced = unsafe {
            rf_render(self.handle, frames as usize, self.raw.as_mut_ptr(), self.filtered.as_mut_ptr())
        };
        assert!(produced >= 0 && produced <= frames as i32);
        let padding = frames as usize - produced as usize;
        output[..padding * 2].fill(0.);
        for (frame, value) in output[padding * 2..].chunks_exact_mut(2).zip(&self.filtered[..produced as usize]) {
            frame.fill(*value as f32);
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
