use rackforge_midi_api::{IngressMidiEvent, MidiPacket, MidiSourceKey};
use rackforge_core::parameter_link::ControlLayers;
use rackforge_plugin_api::abi::MidiEventV1;

const MONO_NOTE: [u8; 3] = [0x90, 69, 100];

fn mono_note(rack: &mut RackEngine<'_>, layers: &mut ControlLayers) {
    let packet = MidiPacket { frame: 0, length: 3, data: MONO_NOTE, wide: None };
    rack.route(IngressMidiEvent { source: MidiSourceKey::new(0), packet }, None, layers);
}

fn engine_mono_fence(package: &Path, cache: &Path) -> HostResult<()> {
    let mut work = EngineWork::load("instance", package, cache)?;
    let EngineRoute::Instance(instance) = &mut work.route else { unreachable!() };
    let events = [MidiEventV1 { frame: 0, length: 3, data: MONO_NOTE }];
    let begin = Instant::now();
    let result = instance.process_interleaved(&[], &mut work.output, 128, 0, 2, &events, &[]);
    let elapsed = ns(begin.elapsed());
    match result {
        Err(error) => {
            let message = format!("{error:#}");
            eprintln!("MONO_FENCE\t{elapsed}\t{message}");
            if !message.to_ascii_lowercase().contains("interrupt") || elapsed > 1_000_000_000 {
                return Err("unexpected or late portable fault".into());
            }
        }
        Ok(()) => return Err("full render unexpectedly completed before the epoch limit".into()),
    }
    Ok(())
}
