const fs = require("node:fs");
const { performance } = require("node:perf_hooks");
const bytes = fs.readFileSync(process.argv[2]);
const { exports: wasm } = new WebAssembly.Instance(new WebAssembly.Module(bytes));
const score = [[48, 0x90, 69], [96, 0x90, 67], [144, 0x80, 67], [192, 0x80, 69],
               [288, 0x90, 72], [336, 0x80, 72]];

function requireStatus(status) {
    if (status !== 0) throw new Error(`RackForge ABI status ${status}`);
}
function snapshot() {
    const ptr = wasm.rf_d_mono_observation();
    if (!ptr) throw new Error("RF-D observation unavailable");
    return Buffer.from(new Uint8Array(wasm.memory.buffer, ptr, 242 * 8));
}

requireStatus(wasm.rackforge_prepare(48000, 128, 0, 2));
const data = [snapshot()];
for (let start = 0; start < 480; start += 128) {
    const frames = Math.min(128, 480 - start);
    const events = score.filter(([sample]) => sample >= start && sample < start + frames);
    const view = new DataView(wasm.memory.buffer, wasm.rackforge_midi_ptr());
    for (const [i, [sample, status, note]] of events.entries()) {
        view.setUint32(i * 8, sample - start, true);
        view.setUint32(i * 8 + 4, status | note << 8 | 100 << 16 | 3 << 24, true);
    }
    const began = performance.now();
    requireStatus(wasm.rackforge_process(frames, 0, 2, events.length, 0));
    const wallMs = performance.now() - began;
    process.stderr.write(`MONO_WASM\t${start}\t${frames}\t${wallMs}\n`);
    data.push(Buffer.from(new Uint8Array(wasm.memory.buffer, wasm.rackforge_output_ptr(), frames * 8)));
    data.push(snapshot());
}
process.stdout.write(Buffer.concat(data));
