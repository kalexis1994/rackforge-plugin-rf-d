//! Route one selected hardware capture channel and MIDI through a RackForge slot.
use rackforge_core::{
    parallel_render::{RenderPool, RenderTelemetry, MAX_RENDER_SLOTS},
    parameter_link::ControlLayers,
    rack_graph::CompiledAudioSource,
    rack_voice::{RackCapture, RackEngine, RackSlotRuntimeSpec, RackSlotStateLoad},
    LoadedPlugin, PluginPackage,
};
use rackforge_midi_api::{IngressMidiEvent, MidiPacket, MidiSourceKey};
use std::{
    collections::BTreeMap,
    error::Error,
    io::{BufWriter, Write},
    path::Path,
};

fn main() -> Result<(), Box<dyn Error>> {
    let args: Vec<_> = std::env::args_os().collect();
    assert!(matches!(args.len(), 6..=9));
    let package = PluginPackage::open(Path::new(&args[1]))?;
    let plugin =
        unsafe { LoadedPlugin::load(&package, None, &BTreeMap::new(), Some(Path::new(&args[2])))? };
    let raw = std::fs::read(&args[3])?;
    assert!(!raw.is_empty() && raw.len() % 4 == 0);
    let capacity: usize = args[4].to_str().unwrap().parse()?;
    let preset = args[5].to_str().unwrap();
    if let Some(path) = args.get(8) {
        let mut instance = plugin.create_instance()?;
        instance.load_preset(preset)?;
        instance.activate(48000., capacity.try_into()?, 1, 2)?;
        std::fs::write(path, instance.save_state()?)?;
    }
    let state = if let Some(path) = args.get(6).filter(|path| *path != "-") {
        RackSlotStateLoad::Opaque(std::fs::read(path)?)
    } else {
        RackSlotStateLoad::LegacyPreset(preset.into())
    };
    let capture: Vec<f32> = raw
        .chunks_exact(4)
        .enumerate()
        .flat_map(|(index, sample)| {
            let distractor = if index % 40 < 20 { 0.75 } else { -0.75 };
            [distractor, f32::from_le_bytes(sample.try_into().unwrap())]
        })
        .collect();
    let events: Vec<(usize, [u8; 3])> = if let Some(path) = args.get(7) {
        let bytes = std::fs::read(path)?;
        assert_eq!(bytes.len() % 7, 0);
        bytes.chunks_exact(7).map(|entry| {
            (u32::from_le_bytes(entry[..4].try_into().unwrap()) as usize, entry[4..].try_into().unwrap())
        }).collect()
    } else {
        vec![(960, [0x90, 57, 100])]
    };
    assert!(events.windows(2).all(|pair| pair[0].0 <= pair[1].0));
    assert!(events.iter().all(|(frame, _)| *frame < capture.len() / 2));
    let id = plugin.manifest().id.clone();
    let mut source = CompiledAudioSource::HardwareInput {
        bus_id: "main".into(),
        route: Default::default(),
    };
    if let CompiledAudioSource::HardwareInput { route, .. } = &mut source {
        route.channels.push(2);
    }
    let slot = RackSlotRuntimeSpec {
        slot_id: "rf-d-external".into(),
        plugin_id: id.clone(),
        state,
        midi_stages: vec![],
        audio_sources: vec![source],
        sends_to_main: true,
        level_per_mille: 1000,
        pan_per_mille: 0,
    };
    let mut writer = BufWriter::new(std::io::stdout().lock());
    for inputs in [[1, 2], [1, 3]] {
        let mut rack = RackEngine::build(
            &BTreeMap::from([(id.clone(), &plugin)]),
            std::slice::from_ref(&slot),
            48000,
            capacity.try_into()?,
            2,
        )?;
        let telemetry = RenderTelemetry::new(MAX_RENDER_SLOTS);
        let mut pool = RenderPool::with_workers(0, telemetry.clone());
        let mut layers = ControlLayers::default();
        let mut output = vec![0.; 2 * capacity];
        let mut events = events.iter().peekable();
        for (block, samples) in capture.chunks(2 * capacity).enumerate() {
            let first = block * capacity;
            let frames = samples.len() / 2;
            while let Some(&(frame, data)) = events.next_if(|(frame, _)| *frame < first + frames) {
                rack.route(
                    IngressMidiEvent {
                        source: MidiSourceKey::new(0),
                        packet: MidiPacket {
                            frame: (frame - first) as u32,
                            length: 3,
                            data,
                            wide: None,
                        },
                    },
                    None,
                    &mut layers,
                );
            }
            let output = &mut output[..2 * frames];
            rack.render(
                &mut pool,
                &telemetry,
                frames as u32,
                frames as u64 * 1_000_000_000 / 48000,
                Some(RackCapture {
                    samples,
                    channels: 2,
                    inputs: &inputs,
                }),
                output,
            )?;
            for sample in output {
                writer.write_all(&sample.to_le_bytes())?;
            }
        }
        let measured = telemetry.snapshot_and_reset();
        eprintln!(
            "RF_D_EXT,{},{},{},{},{}",
            inputs[1],
            measured.block.count,
            measured.block.max_ns,
            measured.deadline_misses,
            measured.slot_faults.iter().sum::<u64>()
        );
        assert_eq!(rack.take_dropped_events(), 0);
    }
    writer.flush()?;
    Ok(())
}
