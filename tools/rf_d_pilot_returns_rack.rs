//! RackForge host render of the bounded pilot workload.
use rackforge_core::{
    LoadedPlugin, PluginPackage,
    parallel_render::{RenderPool, RenderTelemetry, MAX_RENDER_SLOTS},
    rack_voice::{RackEngine, RackSlotRuntimeSpec, RackSlotStateLoad},
};
use std::{collections::BTreeMap, error::Error, io::{BufWriter, Write}, path::Path, sync::Arc, time::Instant};

fn main() -> Result<(), Box<dyn Error>> {
    let args: Vec<_> = std::env::args().collect();
    assert!(args.len() == 3 && matches!(args[2].as_str(), "negative" | "positive" | "q15"));
    let package = PluginPackage::open(Path::new(&args[1]))?;
    let plugin = unsafe { LoadedPlugin::load(&package, None, &BTreeMap::new(), None)? };
    let id = plugin.manifest().id.clone();
    let spec = RackSlotRuntimeSpec {
        slot_id: "rf-d-pilot".into(), plugin_id: id.clone(),
        state: if args[2] == "q15" {
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

fn q15(
    rack: &mut RackEngine,
    pool: &mut RenderPool,
    telemetry: &Arc<RenderTelemetry>,
) -> Result<(), Box<dyn Error>> {
    const FRAMES: u32 = 128;
    const STEREO: usize = 2 * FRAMES as usize;
    const REPEATS: usize = 64;
    let mut times = [[0_u64; 2]; REPEATS];
    let mut first = [[0_u32; STEREO]; 2];
    let mut output = [0_f32; STEREO];
    for (repeat, pair) in times.iter_mut().enumerate() {
        if repeat != 0 {
            rack.reset();
        }
        for (block, time) in pair.iter_mut().enumerate() {
            let start = Instant::now();
            rack.render(pool, telemetry, FRAMES, 128 * 1_000_000_000 / 48_000, None, &mut output)?;
            *time = start.elapsed().as_nanos().try_into()?;
            let bits = output.map(f32::to_bits);
            if repeat == 0 {
                first[block] = bits;
            } else {
                assert_eq!(first[block], bits, "scene changed after reset in block {block}");
            }
        }
    }
    let snapshot = telemetry.snapshot_and_reset();
    eprintln!(
        "Q15_RACK,{FRAMES},{REPEATS},{},{},{},{}",
        snapshot.block.count, snapshot.block.max_ns, snapshot.deadline_misses,
        snapshot.slot_faults.iter().sum::<u64>()
    );
    let mut out = BufWriter::new(std::io::stdout().lock());
    for value in [
        snapshot.block.count,
        snapshot.block.max_ns,
        snapshot.deadline_misses,
        snapshot.slot_faults.iter().sum::<u64>(),
    ] {
        out.write_all(&value.to_le_bytes())?;
    }
    for value in times.into_iter().flatten() {
        out.write_all(&value.to_le_bytes())?;
    }
    for value in first.into_iter().flatten() {
        out.write_all(&value.to_le_bytes())?;
    }
    out.flush()?;
    Ok(())
}
