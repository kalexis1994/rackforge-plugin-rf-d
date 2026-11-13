"""Compare the transcribed SynthMania Oboe phrase with the RF-D MIDI voice."""
import argparse
import json
import wave

import numpy as np

from check_rf_d_oboe import DEMO, SETTINGS
from check_rf_d_playable_filter import change, peak_frequency, rms
from check_rf_d_playable_voice import ROOT, SAMPLE_RATE, main as build_voice, sha, write

REFERENCE = ROOT / "references-local/rhea-synthmania-oboe-frase.wav"
REFERENCE_SHA256 = "fcbb03351506ee287ad9f932dfadce6d1bf2f1240e97220aa5826ecfaaf90280"
AUDITION = ROOT / "artifacts/rf-d-oboe-ab.wav"
RECEIPT = ROOT / "evidence/rf_d_oboe_ab01.json"
FRAMES = 85_440
PREROLL = 4_403
VOICE_DELAY = 48
CONTROLS = dict(SETTINGS, tune=25, osc3_frequency=4.47)
# Offsets in ms from the start of the captured excerpt. The 4' register sounds an octave higher.
KEYS = (
    (15, 89, 55), (89, 148, 56), (148, 254, 55), (254, 450, 53),
    (519, 743, 55), (743, 919, 56), (1028, 1510, 59),
)
WHEEL = (
    (1045, 0), (1100, 2), (1180, 6), (1275, 12), (1355, 20),
    (1395, 21), (1455, 18), (1505, 11), (1540, 4), (1590, 0),
)
NOTE_WINDOWS = ((43, 77), (100, 135), (160, 239), (275, 430), (600, 720), (763, 895), (1070, 1110))


def frames_at(ms):
    return round(ms * SAMPLE_RATE / 1000)


def read_reference():
    if not REFERENCE.is_file():
        raise SystemExit(f"Reference WAV required at {REFERENCE}")
    if sha(REFERENCE) != REFERENCE_SHA256:
        raise SystemExit(f"Reference WAV hash differs from the transcribed capture at {REFERENCE}")
    with wave.open(str(REFERENCE), "rb") as wav:
        assert (wav.getnchannels(), wav.getsampwidth(), wav.getframerate(), wav.getnframes()) == (
            2, 2, SAMPLE_RATE, FRAMES,
        )
        pcm = np.frombuffer(wav.readframes(FRAMES), dtype="<i2")
    return pcm.reshape(-1, 2).mean(axis=1) / 32768.


def score(schema, *, controls=CONTROLS, keys=KEYS, wheel=WHEEL):
    indices = {parameter["id"]: parameter["index"] for parameter in schema["parameters"]}
    events = [change(indices[name], value) for name, value in controls.items()]
    performance = []
    for start_ms, stop_ms, note in keys:
        performance.append([PREROLL + frames_at(start_ms), 0x90, note, 100])
        performance.append([PREROLL + frames_at(stop_ms), 0x80, note, 0])
    # For a legato change, press the next key before releasing the previous one.
    performance.sort(key=lambda event: (event[0], -event[1]))
    if wheel:
        times, values = zip(*wheel)
        samples = sorted(set(range(times[0], times[-1], 4)) | set(times))
        amounts = np.rint(np.interp(samples, times, values)).astype(int).tolist()
        performance.extend([PREROLL + frames_at(ms), 0xb0, 1, value]
                           for ms, value in zip(samples, amounts))
    return events + sorted(performance, key=lambda event: event[0])


def pitch_and_harmonics(audio, start_ms, stop_ms, note):
    signal = audio[frames_at(start_ms):frames_at(stop_ms)]
    frequency, _ = peak_frequency(signal)
    nominal_hz = 440. * 2 ** ((note - 69) / 12.)
    assert abs(1200. * np.log2(frequency / nominal_hz) - CONTROLS["tune"]) < 9., frequency
    weighted = (signal - signal.mean()) * np.hanning(signal.size)
    phase = np.exp(-2j * np.pi * frequency / SAMPLE_RATE * np.arange(signal.size))
    harmonic_ratio = 20. * np.log10(abs((phase**2) @ weighted) / abs(phase @ weighted))
    return dict(fundamental_hz=frequency, harmonic_2_over_1_db=float(harmonic_ratio))


def vibrato_span(audio):
    start, stop = frames_at(1005), frames_at(1565)
    signal = audio[start:stop]
    frequencies = np.fft.fftfreq(signal.size, 1. / SAMPLE_RATE)
    band = np.fft.fft(signal)
    band[(frequencies < 451) | (frequencies > 549)] = 0.
    phase = np.unwrap(np.angle(np.fft.ifft(band)))
    width = frames_at(5)
    hz = (phase[width:] - phase[:-width]) * SAMPLE_RATE / (2. * np.pi * width)
    begin = frames_at(1295) - start - width // 2
    end = frames_at(1475) - start - width // 2
    low, high = np.percentile(1200. * np.log2(hz[begin:end]), [5, 95])
    return float(high - low)


def write_audition(takes, order, destination, *, sample_width=2):
    frames = len(next(iter(takes.values())))
    assert all(take.shape == (frames,) for take in takes.values())
    fade = np.ones(frames)
    edge = np.linspace(0., 1., frames_at(10))
    fade[:edge.size], fade[-edge.size:] = edge, edge[::-1]
    clips = {name: take * fade for name, take in takes.items()}
    # Use constant gain per complete phrase and leave 1 dB of peak headroom.
    target = min(10. ** (-22. / 20.), *(10. ** (-1. / 20.) * rms(clip) / np.max(abs(clip))
                                      for clip in clips.values()))
    gains = {name: target / rms(clip) for name, clip in clips.items()}
    assert sample_width in (2, 3)
    full_scale = 2 ** (8 * sample_width - 1) - 1
    dtype = "<i2" if sample_width == 2 else "<i4"
    pcm = {name: np.rint(full_scale * clip * gains[name]).astype(dtype) for name, clip in clips.items()}
    levels = {name: float(20. * np.log10(rms(clip.astype(np.float64) / full_scale)))
              for name, clip in pcm.items()}
    assert max(levels.values()) - min(levels.values()) < 0.01
    gap = np.zeros(frames_at(300), dtype=dtype)
    sequence = []
    for name in order:
        if sequence:
            sequence.append(gap)
        sequence.append(pcm[name])
    destination.parent.mkdir(exist_ok=True)
    samples = np.concatenate(sequence)
    if sample_width == 3:
        samples = samples.view(np.uint8).reshape(-1, 4)[:, :3]
    with wave.open(str(destination), "wb") as wav:
        wav.setparams((1, sample_width, SAMPLE_RATE, 0, "NONE", "not compressed"))
        wav.writeframes(samples.tobytes())
    playlist = [dict(source=source, start_frame=index * (frames + gap.size))
                for index, source in enumerate(order)]
    return dict(sha256=sha(destination), gain=list(gains.values()), rms_dbfs=list(levels.values()),
                playlist=playlist)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-report", action="store_true", help="save the measurements in evidence/")
    args = parser.parse_args()
    reference = read_reference()

    def inspect(render, schema, component_sha256):
        events = score(schema)
        audio, _ = render(events, frames=PREROLL + VOICE_DELAY + FRAMES)
        repeat, _ = render(events, block=480, frames=len(audio))
        assert np.array_equal(audio, repeat)
        candidate = audio[PREROLL + VOICE_DELAY:]
        measurements = []
        for (start, stop), (key_on, key_off, key) in zip(NOTE_WINDOWS, KEYS, strict=True):
            assert key_on < start < stop < key_off
            note = key + 12
            measurements.append(dict(window_ms=[start, stop], sounding_midi_note=note,
                                     minimoog=pitch_and_harmonics(reference, start, stop, note),
                                     rf_d=pitch_and_harmonics(candidate, start, stop, note)))
        vibrato = dict(minimoog=vibrato_span(reference), rf_d=vibrato_span(candidate))
        assert all(30. < value < 80. for value in vibrato.values()), vibrato
        report = dict(source=DEMO, source_excerpt="second played phrase, about 06:13",
                      reference_sha256=REFERENCE_SHA256, component_sha256=component_sha256,
                      sample_rate_hz=SAMPLE_RATE, frames_per_take=FRAMES, settings=CONTROLS,
                      gate_ms_and_midi_note=KEYS, estimated_mod_wheel_ms_and_cc1=WHEEL,
                      preroll_frames=PREROLL, compensated_voice_delay_frames=VOICE_DELAY,
                      bit_equal_block_frames=[128, 480], note_measurements=measurements,
                      final_vibrato_p95_minus_p05_cents=vibrato,
                      audition=write_audition({"Minimoog": reference, "RF-D": candidate},
                                              ("Minimoog", "RF-D") * 2, AUDITION))
        if args.write_report:
            write(RECEIPT, report)
        print(json.dumps(report, indent=2, allow_nan=False))

    build_voice(["--midi"], inspect_audio=inspect, legacy_timbre=True)


if __name__ == "__main__":
    main()
