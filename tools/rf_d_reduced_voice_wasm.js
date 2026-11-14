const fs = require("node:fs");
const { performance } = require("node:perf_hooks");

const [, , path, encodedScore, length, option, requestedBlock, requestedCapacity, schema, inputPath, preset] = process.argv;
const blockSize = Number(requestedBlock ?? 128);
const capacity = Number(requestedCapacity ?? blockSize);
if (!Number.isInteger(blockSize) || blockSize < 1 || blockSize > capacity) {
    throw new Error("Invalid RF-D block size");
}
const {parameters: parametersSchema} = schema
    ? JSON.parse(fs.readFileSync(schema))
    : require("../plugin/package/metadata/parameters.json");
const panel = parametersSchema.filter(({kind}) => kind.type !== "meter");
const writable = new Map(panel.map((parameter) => [parameter.index, parameter]));
const meter = parametersSchema.find(({kind}) => kind.type === "meter");
const score = JSON.parse(encodedScore);
const frames = Number(length);
const input = inputPath && inputPath !== "-" ? fs.readFileSync(inputPath) : null;
const inputChannels = Number(input !== null);
if (input && input.length !== frames * 4) throw new Error("Expected one float32 per input frame");
const { exports: wasm } = new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path)));

function check(status) {
    if (status !== 0) throw new Error(`RackForge ABI status ${status}`);
}

function prepare() {
    check(wasm.rackforge_prepare(48000, capacity, inputChannels, 2));
    if (wasm.rackforge_latency_frames() !== 48) throw new Error("Unexpected RF-D latency");
}

prepare();
function loadPreset(id) {
    const bytes = Buffer.from(id);
    new Uint8Array(wasm.memory.buffer, wasm.rackforge_transfer_ptr(), bytes.length).set(bytes);
    check(wasm.rackforge_load_preset(bytes.length));
}

if (option === "--panel-state" || option === "--voice-state") {
    const stateBytes = 4 + 8 * panel.length;
    const stateTag = option === "--voice-state" ? "RFDC" : "RFD1";
    const transfer = () => new Uint8Array(wasm.memory.buffer, wasm.rackforge_transfer_ptr(), stateBytes);
    const bounds = (kind) => {
        if (kind.type === "boolean") return [0, 1];
        if (kind.type === "enum") return [kind.choices[0].value, kind.choices.at(-1).value];
        return [kind.minimum, kind.maximum];
    };
    const values = panel.map(({index, kind}) => {
        const initial = Number(kind.default);
        const [minimum, maximum] = bounds(kind);
        if (wasm.rackforge_get_parameter(index) !== initial) throw new Error(`Panel default mismatch at ${index}`);
        const value = minimum === initial ? maximum : minimum;
        check(wasm.rackforge_set_parameter(index, value));
        if (wasm.rackforge_set_parameter(index, NaN) === 0) throw new Error("Accepted invalid parameter");
        if (["boolean", "enum", "integer"].includes(kind.type) && wasm.rackforge_set_parameter(index, 0.5) === 0) {
            throw new Error("Accepted fractional discrete parameter");
        }
        return value;
    });
    if (meter && (wasm.rackforge_get_parameter(meter.index) !== 0 ||
        wasm.rackforge_set_parameter(meter.index, 1) === 0)) {
        throw new Error("Overload meter must start at zero and be read-only");
    }
    if (wasm.rackforge_save_state() !== stateBytes) throw new Error("Panel state size");
    const saved = transfer().slice();
    if (Buffer.from(saved.subarray(0, 4)).toString() !== stateTag) throw new Error("Panel state tag");
    prepare();
    transfer().set(saved);
    check(wasm.rackforge_load_state(saved.length));
    const checkValues = () => {
        if (values.some((value, index) => wasm.rackforge_get_parameter(panel[index].index) !== value)) {
            throw new Error("Panel state round trip");
        }
    };
    checkValues();
    new DataView(wasm.memory.buffer, wasm.rackforge_transfer_ptr(), stateBytes)
        .setFloat64(stateBytes - 8, NaN, true);
    if (wasm.rackforge_load_state(saved.length) === 0) throw new Error("Accepted corrupt panel state");
    checkValues();
    if (option === "--voice-state" && panel.length > 11) {
        // The original voice used the same header with just the first eleven controls.
        for (const count of [11, 26, 29, 35, 37, 39, 40, 42, 44, 48, 54, 55].filter((size) => size < panel.length)) {
            transfer().set(saved);
            // The previous output profile only stored HI or LO.
            if (count === 42) new DataView(transfer().buffer, transfer().byteOffset).setFloat64(4 + 41 * 8, 1, true);
            check(wasm.rackforge_load_state(4 + count * 8));
            if (panel.some(({index, kind}, slot) => {
                const expected = count === 42 && index === 42 ? 1 :
                    slot < count ? values[slot] : Number(kind.default);
                return wasm.rackforge_get_parameter(index) !== expected;
            })) {
                throw new Error(`Voice state migration failed for ${count} controls`);
            }
        }
        loadPreset("three_oscillators");
        prepare();
        if ([14, 19, 24].some((index) => wasm.rackforge_get_parameter(index) !== 1) ||
            wasm.rackforge_get_parameter(17) !== 7) throw new Error("Prepare lost the three-oscillator preset");
        if (panel.length > 26) {
            loadPreset("resonant_bass");
            prepare();
            if (wasm.rackforge_get_parameter(26) !== 82 || wasm.rackforge_get_parameter(28) !== 1) {
                throw new Error("Prepare lost the resonant bass preset");
            }
        }
        if (panel.length > 29) {
            loadPreset("wheel_motion");
            prepare();
            if (wasm.rackforge_get_parameter(31) !== 1 || wasm.rackforge_get_parameter(32) !== 12 ||
                wasm.rackforge_get_parameter(33) !== 1 || wasm.rackforge_get_parameter(34) !== 1) {
                throw new Error("Prepare lost the wheel motion preset");
            }
        }
    }
    if (meter) {
        loadPreset("external_filter");
        prepare();
        if (wasm.rackforge_get_parameter(37) !== 1 || wasm.rackforge_get_parameter(38) !== 60) {
            throw new Error("Prepare lost the external filter preset");
        }
    }
    if (writable.has(40)) {
        loadPreset("loop_drive");
        prepare();
        if (wasm.rackforge_get_parameter(40) !== 1 || wasm.rackforge_get_parameter(37) !== 1) {
            throw new Error("Prepare lost the feedback connection");
        }
    }
    const livePanel = panel.filter(({index}) => index >= 49 && index <= 55);
    const liveValues = livePanel.map(({index}) => wasm.rackforge_get_parameter(index));
    loadPreset("default");
    for (const {index, kind} of panel) {
        const liveIndex = livePanel.findIndex((parameter) => parameter.index === index);
        const expected = liveIndex >= 0 ? liveValues[liveIndex] : Number(kind.default);
        if (wasm.rackforge_get_parameter(index) !== expected) {
            throw new Error(`Pilot Saw preset lost the expected value for parameter ${index}`);
        }
    }
    for (const {index, kind} of livePanel) check(wasm.rackforge_set_parameter(index, Number(kind.default)));
    prepare();
}
let midi = new DataView(wasm.memory.buffer, wasm.rackforge_midi_ptr());
midi.setUint32(0, 0, true);
midi.setUint32(4, 0x90 | 57 << 8 | 100 << 16 | 3 << 24, true);
for (let i = 0; i < 128; i++) {
    check(wasm.rackforge_process(Math.min(128, capacity), inputChannels, 2, i === 0 ? 1 : 0, 0));
}

if (preset) {
    check(wasm.rackforge_set_parameter(44, 1));
    check(wasm.rackforge_set_parameter(48, 1));
    loadPreset(preset);
}
prepare();
const output = Buffer.alloc(frames * 8);
const timings = [];
const overload = [];
for (let start = 0, event = 0; start < frames; start += blockSize) {
    const size = Math.min(blockSize, frames - start);
    midi = new DataView(wasm.memory.buffer, wasm.rackforge_midi_ptr());
    const parameters = new DataView(wasm.memory.buffer, wasm.rackforge_parameter_ptr());
    let count = 0;
    let parameterCount = 0;
    while (event < score.length && score[event][0] < start + size) {
        const [sample, status, note, value = 100, literalMidi = false] = score[event++];
        const parameter = writable.get(note - 20);
        if (!literalMidi && (status === 0xb0 || (status === 0xb1 && schema)) && parameter) {
            const at = parameterCount++ * 16;
            parameters.setUint32(at, sample - start, true);
            parameters.setUint32(at + 4, note - 20, true);
            const {minimum, maximum} = parameter.kind;
            if (value !== 0 && value !== 127 && !schema) throw new Error("Expected an endpoint control value");
            const target = status === 0xb1 ? value
                : value === 127 ? maximum : minimum + (maximum - minimum) * value / 127;
            parameters.setFloat64(at + 8, target, true);
            continue;
        }
        midi.setUint32(count * 8, sample - start, true);
        const channelPressure = (status & 0xf0) === 0xd0;
        midi.setUint32(count * 8 + 4,
            status | note << 8 | (channelPressure ? 2 << 24 : value << 16 | 3 << 24), true);
        count++;
    }
    if (input) {
        new Uint8Array(wasm.memory.buffer, wasm.rackforge_input_ptr(), size * 4)
            .set(input.subarray(start * 4, (start + size) * 4));
    }
    const time = performance.now();
    const status = wasm.rackforge_process(size, inputChannels, 2, count, parameterCount);
    timings.push(Math.round((performance.now() - time) * 1e6));
    check(status);
    if (input && meter) overload.push(wasm.rackforge_get_parameter(meter.index));
    output.set(new Uint8Array(wasm.memory.buffer, wasm.rackforge_output_ptr(), size * 8), start * 8);
}
process.stderr.write(JSON.stringify(input ? {timings, overload} : timings));
process.stdout.write(output);
