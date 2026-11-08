const fs = require("node:fs");
const { performance } = require("node:perf_hooks");

const [, , path, encodedScore, length] = process.argv;
const score = JSON.parse(encodedScore);
const frames = Number(length);
const { exports: wasm } = new WebAssembly.Instance(new WebAssembly.Module(fs.readFileSync(path)));

function check(status) {
    if (status !== 0) throw new Error(`RackForge ABI status ${status}`);
}

function prepare() {
    check(wasm.rackforge_prepare(48000, 128, 0, 2));
    if (wasm.rackforge_latency_frames() !== 48) throw new Error("Unexpected RF-D latency");
}

prepare();
let midi = new DataView(wasm.memory.buffer, wasm.rackforge_midi_ptr());
midi.setUint32(0, 0, true);
midi.setUint32(4, 0x90 | 57 << 8 | 100 << 16 | 3 << 24, true);
for (let i = 0; i < 128; i++) {
    check(wasm.rackforge_process(128, 0, 2, i === 0 ? 1 : 0, 0));
}

prepare();
const output = Buffer.alloc(frames * 8);
const timings = [];
for (let start = 0, event = 0; start < frames; start += 128) {
    const size = Math.min(128, frames - start);
    midi = new DataView(wasm.memory.buffer, wasm.rackforge_midi_ptr());
    let count = 0;
    while (event < score.length && score[event][0] < start + size) {
        const [sample, status, note] = score[event++];
        midi.setUint32(count * 8, sample - start, true);
        midi.setUint32(count * 8 + 4, status | note << 8 | 100 << 16 | 3 << 24, true);
        count++;
    }
    const time = performance.now();
    const status = wasm.rackforge_process(size, 0, 2, count, 0);
    timings.push(Math.round((performance.now() - time) * 1e6));
    check(status);
    output.set(new Uint8Array(wasm.memory.buffer, wasm.rackforge_output_ptr(), size * 8), start * 8);
}
process.stderr.write(JSON.stringify(timings));
process.stdout.write(output);
