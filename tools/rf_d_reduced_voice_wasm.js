const fs = require("node:fs");
const { performance } = require("node:perf_hooks");

const [, , path, encodedScore, length, option, requestedBlock, requestedCapacity] = process.argv;
const blockSize = Number(requestedBlock ?? 128);
const capacity = Number(requestedCapacity ?? blockSize);
if (!Number.isInteger(blockSize) || blockSize < 1 || blockSize > capacity) {
    throw new Error("Invalid RF-D block size");
}
const {parameters: panel} = require("../plugin/package/metadata/parameters.json");
const score = JSON.parse(encodedScore);
const frames = Number(length);
const { exports: wasm } = new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path)));

function check(status) {
    if (status !== 0) throw new Error(`RackForge ABI status ${status}`);
}

function prepare() {
    check(wasm.rackforge_prepare(48000, capacity, 0, 2));
    if (wasm.rackforge_latency_frames() !== 48) throw new Error("Unexpected RF-D latency");
}

prepare();
if (option === "--panel-state") {
    const transfer = () => new Uint8Array(wasm.memory.buffer, wasm.rackforge_transfer_ptr(), 52);
    const values = panel.map(({index, kind}) => {
        if (wasm.rackforge_get_parameter(index) !== kind.default) throw new Error("Panel default mismatch");
        const value = kind.minimum === kind.default ? kind.maximum : kind.minimum;
        check(wasm.rackforge_set_parameter(index, value));
        if (wasm.rackforge_set_parameter(index, NaN) === 0) throw new Error("Accepted invalid parameter");
        return value;
    });
    if (wasm.rackforge_save_state() !== 52) throw new Error("Panel state size");
    const saved = transfer().slice();
    if (Buffer.from(saved.subarray(0, 4)).toString() !== "RFD1") throw new Error("Panel state tag");
    prepare();
    transfer().set(saved);
    check(wasm.rackforge_load_state(saved.length));
    const checkValues = () => {
        if (values.some((value, index) => wasm.rackforge_get_parameter(index) !== value)) {
            throw new Error("Panel state round trip");
        }
    };
    checkValues();
    new DataView(wasm.memory.buffer, wasm.rackforge_transfer_ptr(), 52).setFloat64(44, NaN, true);
    if (wasm.rackforge_load_state(saved.length) === 0) throw new Error("Accepted corrupt panel state");
    checkValues();
    transfer().set(Buffer.from("default"));
    check(wasm.rackforge_load_preset(7));
    if (panel.some(({index, kind}) => wasm.rackforge_get_parameter(index) !== kind.default)) {
        throw new Error("Pilot Saw preset did not restore defaults");
    }
    prepare();
}
let midi = new DataView(wasm.memory.buffer, wasm.rackforge_midi_ptr());
midi.setUint32(0, 0, true);
midi.setUint32(4, 0x90 | 57 << 8 | 100 << 16 | 3 << 24, true);
for (let i = 0; i < 128; i++) {
    check(wasm.rackforge_process(Math.min(128, capacity), 0, 2, i === 0 ? 1 : 0, 0));
}

prepare();
const output = Buffer.alloc(frames * 8);
const timings = [];
for (let start = 0, event = 0; start < frames; start += blockSize) {
    const size = Math.min(blockSize, frames - start);
    midi = new DataView(wasm.memory.buffer, wasm.rackforge_midi_ptr());
    const parameters = new DataView(wasm.memory.buffer, wasm.rackforge_parameter_ptr());
    let count = 0;
    let parameterCount = 0;
    while (event < score.length && score[event][0] < start + size) {
        const [sample, status, note, value = 100] = score[event++];
        if (status === 0xb0 && panel[note - 20]) {
            if (value !== 0 && value !== 127) throw new Error("Expected an endpoint control value");
            const at = parameterCount++ * 16;
            parameters.setUint32(at, sample - start, true);
            parameters.setUint32(at + 4, note - 20, true);
            const {minimum, maximum} = panel[note - 20].kind;
            parameters.setFloat64(at + 8, value === 0 ? minimum : maximum, true);
            continue;
        }
        midi.setUint32(count * 8, sample - start, true);
        midi.setUint32(count * 8 + 4, status | note << 8 | value << 16 | 3 << 24, true);
        count++;
    }
    const time = performance.now();
    const status = wasm.rackforge_process(size, 0, 2, count, parameterCount);
    timings.push(Math.round((performance.now() - time) * 1e6));
    check(status);
    output.set(new Uint8Array(wasm.memory.buffer, wasm.rackforge_output_ptr(), size * 8), start * 8);
}
process.stderr.write(JSON.stringify(timings));
process.stdout.write(output);
