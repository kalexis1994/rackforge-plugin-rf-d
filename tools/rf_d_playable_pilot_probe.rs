//! Render the RF-D portable package through RackForge's real MIDI ingress.
use rackforge_core::{
    parallel_render::{RenderPool, RenderTelemetry, MAX_RENDER_SLOTS},
    parameter_link::{CompiledParameterLink, ControlLayers},
    rack_voice::{RackEngine, RackSlotRuntimeSpec, RackSlotStateLoad},
    LoadedPlugin, PluginPackage,
};
use rackforge_midi_api::{
    ControlTakeover, IngressMidiEvent, MidiPacket, MidiSourceId, MidiSourceKey, ParameterLink,
    ParameterLinkId, ParameterLinkMessage, ParameterLinkPassThrough, ParameterLinkSource,
    PARAMETER_LINK_SCHEMA_VERSION,
};
use std::{
    collections::BTreeMap,
    error::Error,
    io::{BufWriter, Write},
    path::Path,
    time::Instant,
};

const FRAMES: u32 = 128;
const RATE: u32 = 48_000;
const BLOCKS: u32 = 376;

fn main() -> Result<(), Box<dyn Error>> {
    let args: Vec<_> = std::env::args_os().collect();
    assert_eq!(args.len(), 4);
    let package = PluginPackage::open(Path::new(&args[1]))?;
    let plugin =
        unsafe { LoadedPlugin::load(&package, None, &BTreeMap::new(), Some(Path::new(&args[2])))? };
    let id = plugin.manifest().id.clone();
    let slot = RackSlotRuntimeSpec {
        slot_id: "rf-d-pilot".into(),
        plugin_id: id.clone(),
        state: RackSlotStateLoad::Default,
        midi_stages: vec![],
        audio_sources: vec![],
        sends_to_main: true,
        level_per_mille: 1000,
        pan_per_mille: 0,
    };
    let mut rack = RackEngine::build(&BTreeMap::from([(id, &plugin)]), &[slot], RATE, FRAMES, 2)?;
    let source = MidiSourceKey::new(0);
    let links = [(0, 20, "pilot.r59"), (1, 21, "pilot.pin16")]
        .into_iter()
        .map(|(parameter_index, controller, id)| {
            let link = ParameterLink {
                schema_version: PARAMETER_LINK_SCHEMA_VERSION,
                id: ParameterLinkId::new(id).unwrap(),
                instance_id: "rf-d-pilot".into(),
                parameter_index,
                source: ParameterLinkSource {
                    source_id: MidiSourceId::new("lab.returns").unwrap(),
                    display_name: "Lab return drives".into(),
                },
                channel: Default::default(),
                message: ParameterLinkMessage::ControlChange { controller },
                transform: Default::default(),
                pass_through: ParameterLinkPassThrough::Consume,
                mode: Default::default(),
                layer: Default::default(),
            };
            let mut compiled = CompiledParameterLink::new(link, source, plugin.parameters())?;
            compiled.set_takeover(ControlTakeover::Jump);
            Ok(compiled)
        })
        .collect::<Result<_, Box<dyn Error>>>()?;
    rack.set_parameter_links(links);
    let telemetry = RenderTelemetry::new(MAX_RENDER_SLOTS);
    let mut pool = RenderPool::with_workers(0, telemetry.clone());
    let mut layers = ControlLayers::default();
    let score = std::fs::read(&args[3])?;
    assert_eq!(score.len() % 8, 0);
    let mut events = score
        .chunks_exact(8)
        .map(|event| {
            (
                u32::from_le_bytes(event[..4].try_into().unwrap()),
                event[4..7].try_into().unwrap(),
            )
        })
        .peekable();
    let mut output = [0_f32; 2 * FRAMES as usize];
    let mut timings = [0_u64; BLOCKS as usize];
    let mut audio = Vec::with_capacity(2 * (FRAMES * BLOCKS) as usize);
    let mut routed = 0;
    for (block, time) in timings.iter_mut().enumerate() {
        let offset = block as u32 * FRAMES;
        while let Some((frame, data)) = events.next_if(|(frame, _)| *frame < offset + FRAMES) {
            rack.route(
                IngressMidiEvent {
                    source,
                    packet: MidiPacket {
                        frame: frame - offset,
                        length: 3,
                        data,
                        wide: None,
                    },
                },
                None,
                &mut layers,
            );
            routed += 1;
        }
        let start = Instant::now();
        rack.render(
            &mut pool,
            &telemetry,
            FRAMES,
            u64::from(FRAMES) * 1_000_000_000 / u64::from(RATE),
            None,
            &mut output,
        )?;
        *time = start.elapsed().as_nanos().try_into()?;
        audio.extend_from_slice(&output);
    }
    assert!(events.next().is_none());
    let snap = telemetry.snapshot_and_reset();
    eprintln!(
        "RF_D_MIDI,{routed},{},{},{},{},{}",
        snap.block.count,
        snap.block.max_ns,
        snap.deadline_misses,
        snap.slot_faults.iter().sum::<u64>(),
        rack.take_dropped_events()
    );
    let mut out = BufWriter::new(std::io::stdout().lock());
    for t in timings {
        out.write_all(&t.to_le_bytes())?;
    }
    for sample in audio {
        out.write_all(&sample.to_le_bytes())?;
    }
    out.flush()?;
    Ok(())
}
