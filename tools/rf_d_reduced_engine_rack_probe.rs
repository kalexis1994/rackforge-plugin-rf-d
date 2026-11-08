//! One bounded 128-frame render through a real RackForge slot and mixer.
use rackforge_core::{
    LoadedPlugin, PluginPackage,
    parallel_render::{RenderPool, RenderTelemetry, MAX_RENDER_SLOTS},
    rack_voice::{RackEngine, RackSlotRuntimeSpec, RackSlotStateLoad},
};
use std::{collections::BTreeMap, error::Error, path::Path, time::Instant};

fn main() -> Result<(), Box<dyn Error>> {
    let args: Vec<_> = std::env::args().collect();
    assert!(args.len() == 3 && matches!(args[2].as_str(), "negative" | "positive"));
    let package = PluginPackage::open(Path::new(&args[1]))?;
    let plugin = unsafe { LoadedPlugin::load(&package, None, &BTreeMap::new(), None)? };
    let id = plugin.manifest().id.clone();
    let slot = RackSlotRuntimeSpec {
        slot_id: "rf-d-loaded".into(), plugin_id: id.clone(),
        state: RackSlotStateLoad::LegacyPreset(args[2].clone()),
        midi_stages: vec![], audio_sources: vec![], sends_to_main: true,
        level_per_mille: 1000, pan_per_mille: 0,
    };
    let mut rack = RackEngine::build(&BTreeMap::from([(id, &plugin)]), &[slot], 48000, 128, 2)?;
    let telemetry = RenderTelemetry::new(MAX_RENDER_SLOTS);
    let mut pool = RenderPool::with_workers(0, telemetry.clone());
    let mut output = [0.; 256];
    let start = Instant::now();
    rack.render(&mut pool, &telemetry, 128, 128 * 1_000_000_000 / 48_000, None, &mut output)?;
    let ns = start.elapsed().as_nanos();
    let snapshot = telemetry.snapshot_and_reset();
    println!("RACK,128,{ns},{},{},{},{}",
             snapshot.block.count, snapshot.block.max_ns, snapshot.deadline_misses,
             snapshot.slot_faults.iter().sum::<u64>());
    for (i, stereo) in output.chunks_exact(2).enumerate() {
        println!("SAMPLE,{i},{:08x},{:08x}", stereo[0].to_bits(), stereo[1].to_bits());
    }
    Ok(())
}
