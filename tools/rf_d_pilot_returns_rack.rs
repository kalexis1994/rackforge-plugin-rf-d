//! RackForge host render of the bounded pilot workload.
use rackforge_core::{
    LoadedPlugin, PluginPackage,
    parallel_render::{RenderPool, RenderTelemetry, MAX_RENDER_SLOTS},
    rack_voice::{RackEngine, RackSlotRuntimeSpec, RackSlotStateLoad},
};
use std::{collections::BTreeMap, error::Error, io::{BufWriter, Write}, path::Path, time::Instant};

fn main() -> Result<(), Box<dyn Error>> {
    let args: Vec<_> = std::env::args().collect();
    assert!(args.len() == 3 && matches!(args[2].as_str(), "negative" | "positive"));
    let package = PluginPackage::open(Path::new(&args[1]))?;
    let plugin = unsafe { LoadedPlugin::load(&package, None, &BTreeMap::new(), None)? };
    let id = plugin.manifest().id.clone();
    let spec = RackSlotRuntimeSpec {
        slot_id: "rf-d-pilot".into(), plugin_id: id.clone(),
        state: RackSlotStateLoad::LegacyPreset(args[2].clone()),
        midi_stages: vec![], audio_sources: vec![], sends_to_main: true,
        level_per_mille: 1000, pan_per_mille: 0,
    };
    let mut rack = RackEngine::build(&BTreeMap::from([(id, &plugin)]), &[spec], 48000, 128, 2)?;
    let telemetry = RenderTelemetry::new(MAX_RENDER_SLOTS);
    let mut pool = RenderPool::with_workers(0, telemetry.clone());
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
