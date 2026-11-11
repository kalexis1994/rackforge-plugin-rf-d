//! RackForge host render of the bounded pilot workload.
use rackforge_core::{
    LoadedPlugin, PluginPackage,
    parallel_render::{RenderPool, RenderTelemetry, MAX_RENDER_SLOTS},
    rack_voice::{RackEngine, RackSlotRuntimeSpec, RackSlotStateLoad},
};
use std::{collections::BTreeMap, error::Error, io::{BufWriter, Write}, path::Path, sync::Arc, time::Instant};

fn main() -> Result<(), Box<dyn Error>> {
    let args: Vec<_> = std::env::args().collect();
    assert!(args.len() == 3
        && matches!(args[2].as_str(), "negative" | "positive" | "q15" | "q15-direct" | "q15-stream"));
    let package = PluginPackage::open(Path::new(&args[1]))?;
    let plugin = unsafe { LoadedPlugin::load(&package, None, &BTreeMap::new(), None)? };
    if args[2] == "q15-direct" {
        return q15_direct(&plugin);
    }
    let id = plugin.manifest().id.clone();
    let spec = RackSlotRuntimeSpec {
        slot_id: "rf-d-pilot".into(), plugin_id: id.clone(),
        state: if matches!(args[2].as_str(), "q15" | "q15-stream") {
            RackSlotStateLoad::Default
        } else {
            RackSlotStateLoad::LegacyPreset(args[2].clone())
        },
        midi_stages: vec![], audio_sources: vec![], sends_to_main: true,
        level_per_mille: 1000, pan_per_mille: 0,
    };
    let mut rack = RackEngine::build(&BTreeMap::from([(id, &plugin)]), &[spec], 48000, 128, 2)?;
    let telemetry = RenderTelemetry::new(MAX_RENDER_SLOTS);
    let mut pool = RenderPool::with_workers(0, telemetry.clone());
    if args[2] == "q15" {
        return q15(&mut rack, &mut pool, &telemetry);
    }
    if args[2] == "q15-stream" {
        return q15_stream(&mut rack, &mut pool, &telemetry);
    }
    let mut output = [0.; 256];
    let mut times = [0_u64; 376];
    let mut audio = Vec::with_capacity(376 * 256);
    for time in &mut times {
        let start = Instant::now();
        rack.render(&mut pool, &telemetry, 128, 128 * 1_000_000_000 / 48_000, None, &mut output)?;
        *time = start.elapsed().as_nanos().try_into()?;
        audio.extend_from_slice(&output);
    }
    let snapshot = telemetry.snapshot_and_reset();
    eprintln!("PILOT_RACK,128,{},{},{},{}",
              snapshot.block.count, snapshot.block.max_ns, snapshot.deadline_misses,
              snapshot.slot_faults.iter().sum::<u64>());
    let mut out = BufWriter::new(std::io::stdout().lock());
    for v in times {
        out.write_all(&v.to_le_bytes())?;
    }
    for v in audio {
        out.write_all(&v.to_le_bytes())?;
    }
    out.flush()?;
    Ok(())
}

fn q15_stream(
    rack: &mut RackEngine,
    pool: &mut RenderPool,
    telemetry: &Arc<RenderTelemetry>,
) -> Result<(), Box<dyn Error>> {
    let mut output = [0_f32; Q15_STEREO];
    let mut out = BufWriter::new(std::io::stdout().lock());
    for _ in 0..128 {
        rack.render(pool, telemetry, Q15_FRAMES, Q15_DEADLINE_NS, None, &mut output)?;
        for value in output {
            out.write_all(&value.to_le_bytes())?;
        }
    }
    let snapshot = telemetry.snapshot_and_reset();
    assert_eq!(snapshot.block.count, 128);
    let faults = snapshot.slot_faults.iter().sum::<u64>();
    for value in [snapshot.block.max_ns, snapshot.deadline_misses, faults] {
        out.write_all(&value.to_le_bytes())?;
    }
    out.flush()?;
    Ok(())
}

fn q15(
    rack: &mut RackEngine,
    pool: &mut RenderPool,
    telemetry: &Arc<RenderTelemetry>,
) -> Result<(), Box<dyn Error>> {
    let replay = replay_q15(|call| {
        match call {
            Q15Call::Reset => rack.reset(),
            Q15Call::Process(output) => {
                rack.render(pool, telemetry, Q15_FRAMES, Q15_DEADLINE_NS, None, output)?;
            }
        }
        Ok(())
    })?;
    let snapshot = telemetry.snapshot_and_reset();
    write_q15(replay, [
        snapshot.block.count,
        snapshot.block.max_ns,
        snapshot.deadline_misses,
        snapshot.slot_faults.iter().sum::<u64>(),
    ])
}

fn q15_direct(plugin: &LoadedPlugin) -> Result<(), Box<dyn Error>> {
    let mut instance = plugin.create_instance()?;
    instance.activate(48_000., Q15_FRAMES, 0, 2)?;
    let replay = replay_q15(|call| {
        match call {
            Q15Call::Reset => instance.reset()?,
            Q15Call::Process(output) => {
                instance.process_wide(&[], output, Q15_FRAMES, 0, 2, &[], &[])?;
            }
        }
        Ok(())
    })?;
    let peak = replay.times.iter().flatten().copied().max().unwrap();
    let misses = replay.times.iter().flatten().filter(|&&ns| ns > Q15_DEADLINE_NS).count() as u64;
    write_q15(replay, [2 * Q15_REPEATS as u64, peak, misses, 0])
}

const Q15_FRAMES: u32 = 128;
const Q15_DEADLINE_NS: u64 = 128 * 1_000_000_000 / 48_000;
const Q15_STEREO: usize = 2 * Q15_FRAMES as usize;
const Q15_REPEATS: usize = 64;

enum Q15Call<'a> {
    Reset,
    Process(&'a mut [f32]),
}

struct Q15Replay {
    times: [[u64; 2]; Q15_REPEATS],
    first: [[u32; Q15_STEREO]; 2],
}

fn replay_q15(
    mut call: impl FnMut(Q15Call<'_>) -> Result<(), Box<dyn Error>>,
) -> Result<Q15Replay, Box<dyn Error>> {
    let mut times = [[0_u64; 2]; Q15_REPEATS];
    let mut first = [[0_u32; Q15_STEREO]; 2];
    let mut output = [0_f32; Q15_STEREO];
    for (repeat, pair) in times.iter_mut().enumerate() {
        if repeat != 0 {
            call(Q15Call::Reset)?;
        }
        for (block, time) in pair.iter_mut().enumerate() {
            let start = Instant::now();
            call(Q15Call::Process(&mut output))?;
            *time = start.elapsed().as_nanos().try_into()?;
            let bits = output.map(f32::to_bits);
            if repeat == 0 {
                first[block] = bits;
            } else {
                assert_eq!(first[block], bits, "scene changed after reset in block {block}");
            }
        }
    }
    Ok(Q15Replay { times, first })
}

fn write_q15(replay: Q15Replay, diagnostics: [u64; 4]) -> Result<(), Box<dyn Error>> {
    let mut out = BufWriter::new(std::io::stdout().lock());
    for value in diagnostics {
        out.write_all(&value.to_le_bytes())?;
    }
    for value in replay.times.into_iter().flatten() {
        out.write_all(&value.to_le_bytes())?;
    }
    for value in replay.first.into_iter().flatten() {
        out.write_all(&value.to_le_bytes())?;
    }
    out.flush()?;
    Ok(())
}
