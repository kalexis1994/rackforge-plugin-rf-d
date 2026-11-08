//! Native ABI adapter for the two frozen electrical scenes.
use crate::{
    abi::{copy_to_host_buffer, pack_version, HostApiV1, PluginApiV1, ProcessBlockV1,
          STATUS_INTERNAL_ERROR, STATUS_INVALID_ARGUMENT, STATUS_INVALID_STATE, STATUS_OK,
          STATUS_UNKNOWN_PARAMETER},
    reduced_engine::{Engine, Frame, BLOCK, RATE},
};
use std::{ffi::c_void, mem::size_of, ptr, slice};

const DESCRIPTOR: &[u8] = br#"{"schema_version":1,"id":"org.rackforge.lab.rf-d-contours","version":"0.1.0","state_version":1}"#;
const PARAMETERS: &[u8] = br#"{"schema_version":1,"pages":[],"parameters":[]}"#;
const PRESETS: &[u8] = br#"{"schema_version":1,"banks":[{"id":"lab","name":"Lab","order":0}],"presets":[
    {"id":"positive","name":"Positive reserve","bank":"lab","category":"Lab","order":0,"tags":[]},
    {"id":"negative","name":"Negative reserve","bank":"lab","category":"Lab","order":1,"tags":[]}]}"#;

#[derive(Default)]
struct Voice {
    engine: Option<Engine>,
    frame: usize,
    maximum: usize,
    negative: bool,
}

impl Voice {
    fn prepare(&mut self, negative: bool) -> i32 {
        let (bank, cap): (&[u8], usize) = if negative {
            (include_bytes!("NEGATIVE_BANK"), 32)
        } else {
            (include_bytes!("POSITIVE_BANK"), 64)
        };
        let cap = if cfg!(adaptive_contour_clock) {
            crate::reduced_engine::TICKS >> (crate::reduced_engine::BANKS - 1)
        } else {
            cap
        };
        match Engine::prepare(bank, cap) {
            Ok(engine) => {
                self.engine = Some(engine);
                self.negative = negative;
                self.frame = 0;
                STATUS_OK
            }
            Err(_) => STATUS_INTERNAL_ERROR,
        }
    }
}

unsafe extern "C" fn descriptor(out: *mut u8, cap: usize) -> usize {
    unsafe { copy_to_host_buffer(DESCRIPTOR, out, cap) }
}
unsafe extern "C" fn parameters(out: *mut u8, cap: usize) -> usize {
    unsafe { copy_to_host_buffer(PARAMETERS, out, cap) }
}
unsafe extern "C" fn presets(out: *mut u8, cap: usize) -> usize {
    unsafe { copy_to_host_buffer(PRESETS, out, cap) }
}
unsafe extern "C" fn create(_: *const HostApiV1) -> *mut c_void {
    Box::into_raw(Box::new(Voice::default())).cast()
}
unsafe extern "C" fn destroy(raw: *mut c_void) {
    if !raw.is_null() {
        unsafe { drop(Box::from_raw(raw.cast::<Voice>())) };
    }
}

unsafe extern "C" fn activate(raw: *mut c_void, rate: f64, frames: u32, inputs: u32, outputs: u32) -> i32 {
    let Some(voice) = (unsafe { raw.cast::<Voice>().as_mut() }) else { return STATUS_INVALID_ARGUMENT };
    if rate != RATE as f64 || !(1..=BLOCK as u32).contains(&frames) || inputs != 0 || outputs != 2 {
        return STATUS_INVALID_ARGUMENT;
    }
    let status = voice.prepare(voice.negative);
    if status == STATUS_OK {
        voice.maximum = frames as usize;
    }
    status
}
unsafe extern "C" fn deactivate(raw: *mut c_void) -> i32 {
    let Some(voice) = (unsafe { raw.cast::<Voice>().as_mut() }) else { return STATUS_INVALID_ARGUMENT };
    voice.engine = None;
    voice.maximum = 0;
    STATUS_OK
}
unsafe extern "C" fn reset(raw: *mut c_void) -> i32 {
    let Some(voice) = (unsafe { raw.cast::<Voice>().as_mut() }) else { return STATUS_INVALID_ARGUMENT };
    if let Some(engine) = &mut voice.engine {
        engine.reset();
    }
    voice.frame = 0;
    STATUS_OK
}

unsafe extern "C" fn set(_: *mut c_void, _: u32, _: f64) -> i32 { STATUS_UNKNOWN_PARAMETER }
unsafe extern "C" fn get(_: *mut c_void, _: u32, _: *mut f64) -> i32 { STATUS_UNKNOWN_PARAMETER }
unsafe extern "C" fn save(_: *mut c_void, _: *mut u8, _: usize) -> usize { 0 }
unsafe extern "C" fn load(_: *mut c_void, _: *const u8, _: usize) -> i32 { STATUS_INVALID_STATE }

unsafe extern "C" fn preset(raw: *mut c_void, data: *const u8, len: usize) -> i32 {
    let Some(voice) = (unsafe { raw.cast::<Voice>().as_mut() }) else { return STATUS_INVALID_ARGUMENT };
    if data.is_null() || len != 8 {
        return STATUS_INVALID_ARGUMENT;
    }
    let negative = match unsafe { slice::from_raw_parts(data, len) } {
        b"positive" => false,
        b"negative" => true,
        _ => return STATUS_INVALID_ARGUMENT,
    };
    if voice.engine.is_some() {
        return voice.prepare(negative);
    }
    voice.negative = negative;
    STATUS_OK
}

unsafe extern "C" fn process(raw: *mut c_void, block: *const ProcessBlockV1) -> i32 {
    let Some(voice) = (unsafe { raw.cast::<Voice>().as_mut() }) else { return STATUS_INVALID_ARGUMENT };
    let Some(block) = (unsafe { block.as_ref() }) else { return STATUS_INVALID_ARGUMENT };
    let frames = block.frames as usize;
    if !(1..=voice.maximum).contains(&frames) || block.output_interleaved.is_null()
        || block.input_channels != 0 || block.output_channels != 2
    {
        return STATUS_INVALID_ARGUMENT;
    }
    let Some(engine) = &mut voice.engine else { return STATUS_INVALID_STATE };
    let keys: [f64; BLOCK] = std::array::from_fn(|i| {
        if voice.negative && (16..96).contains(&(voice.frame + i)) { 10. } else { 0. }
    });
    let mut result = [Frame::EMPTY; BLOCK];
    if engine.render(&keys[..frames], &mut result[..frames]).is_err() {
        return STATUS_INTERNAL_ERROR;
    }
    let output = unsafe { slice::from_raw_parts_mut(block.output_interleaved, frames * 2) };
    for (stereo, frame) in output.chunks_exact_mut(2).zip(&result) {
        stereo.fill(frame.j7_v as f32);
    }
    voice.frame += frames;
    STATUS_OK
}

static PLUGIN: PluginApiV1 = PluginApiV1 {
    struct_size: size_of::<PluginApiV1>() as u32,
    api_version: pack_version(1, 0),
    runtime_descriptor_json: descriptor,
    parameter_schema_json: parameters,
    preset_catalog_json: presets,
    create, destroy, activate, deactivate, reset,
    set_parameter: set, get_parameter: get, save_state: save, load_state: load, load_preset: preset, process,
};

#[unsafe(no_mangle)]
pub extern "C" fn rackforge_plugin_entry_v1() -> *const PluginApiV1 {
    ptr::addr_of!(PLUGIN)
}
