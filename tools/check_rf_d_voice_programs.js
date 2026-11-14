const assert = require("node:assert/strict");
const fs = require("node:fs");

const moduleBytes = fs.readFileSync(process.argv[2]);
const {parameters} = JSON.parse(fs.readFileSync(process.argv[3]));
const module_ = new WebAssembly.Module(moduleBytes);

function openVoice() {
  const wasm = new WebAssembly.Instance(module_).exports;
  assert.equal(wasm.rackforge_prepare(48000, 128, 0, 2), 0);
  assert.equal(wasm.rackforge_program_editing_capabilities(), 7);
  const write = (bytes, pointer) => {
    new Uint8Array(wasm.memory.buffer, pointer, bytes.length).set(bytes);
    return bytes.length;
  };
  const read = (length) => {
    assert.ok(length > 0, `Program ABI result ${length}`);
    return JSON.parse(Buffer.from(wasm.memory.buffer, wasm.rackforge_transfer_ptr(), length));
  };
  return {
    get: wasm.rackforge_get_parameter,
    set: (index, value) => assert.equal(wasm.rackforge_set_parameter(index, value), 0),
    exchange: (method, value) => wasm[`rackforge_program_${method}`](
      write(Buffer.from(JSON.stringify(value)), wasm.rackforge_exchange_input_ptr()),
    ),
    catalog: () => read(wasm.rackforge_preset_catalog()),
    load: (id) => assert.equal(wasm.rackforge_load_preset(
      write(Buffer.from(id), wasm.rackforge_transfer_ptr()),
    ), 0),
    read,
  };
}

const voice = openVoice();
const catalog = voice.catalog();
const banks = catalog.banks.map(({id}) => id);
if (banks.includes("poly")) {
  assert.deepEqual(banks, ["mono", "poly", "user"]);
  assert.equal(catalog.presets[0].id, "classic_saw");
  assert.equal(catalog.presets.filter(({bank}) => bank === "mono").length, 24);
  assert.equal(catalog.presets.filter(({bank}) => bank === "poly").length, 16);
  assert.ok(!catalog.presets.some(({id}) => ["default", "three_oscillators", "resonant_bass",
    "wheel_motion", "external_filter", "loop_drive"].includes(id)));
  assert.equal(voice.get(55), 0);
  voice.load("afterglow_strings");
  assert.equal(voice.get(55), 1);
  voice.set(55, 5);
  voice.load("classic_saw");
  assert.equal(voice.get(55), 0);
}
const cutoff = 38.82345678901234;
voice.set(0, cutoff);
voice.set(11, -27.25);
voice.set(42, 2);
voice.set(45, 1.125);
voice.set(48, 1);
voice.set(49, 1234);
voice.set(50, 71);
voice.set(51, 1);
voice.set(53, 1.25);
voice.set(55, 3);
const {document} = voice.read(voice.exchange("begin_edit", {schema_version: 1}));
assert.equal(document.payload.parameters.cutoff, cutoff);
assert.equal(document.payload.parameters.tune, -27.25);
assert.equal(document.payload.parameters.output_jack, 2);
const live = [
  "external_overload", "tuner_a440", "pitch_cv", "filter_cv", "loudness_cv", "external_s_trigger",
  "pitch_wheel", "mod_wheel", "glide_pedal", "decay_pedal", "glide_pedal_resistance", "decay_pedal_resistance",
  "voice_mode",
];
assert.deepEqual(Object.keys(document.payload.parameters).sort(),
  parameters.map(({id}) => id).filter((id) => !live.includes(id)).sort());

const editor = voice.read(voice.exchange("editor_view", document));
assert.deepEqual(editor.pages[0].fields[0].value, {type: "integer", value: 3882});
const edited = voice.read(voice.exchange("apply_edit", {
  schema_version: 1, document, field_id: "cutoff", value: {type: "integer", value: 4025},
}));
assert.equal(edited.document.payload.parameters.cutoff, 40.25);
for (const changes of [{cutoff: 101}, {output_jack: 1.5}, {external_s_trigger: 1}, {cutoff: undefined}]) {
  const invalid = {...document, payload: {parameters: {...document.payload.parameters, ...changes}}};
  assert.ok(voice.exchange("prepare_save", invalid) < 0);
  assert.equal(voice.get(0), cutoff);
}

document.name = "Oboe nocturno";
const prepared = voice.read(voice.exchange("prepare_save", document));
voice.set(0, 91);
voice.set(45, -0.5);
assert.equal(voice.exchange("preview", prepared), 0);
assert.equal(voice.get(0), cutoff);
assert.equal(voice.get(45), -0.5);
assert.equal(voice.get(48), 1);
assert.deepEqual([49, 50, 51, 53].map(voice.get), [1234, 71, 1, 1.25]);
assert.equal(voice.get(55), 3);
assert.equal(voice.exchange("install", prepared), 0);
assert.ok(voice.catalog().presets.some(({id, name, bank, editable}) =>
  id === prepared.preview_sound_id && name === document.name && bank === "user" && editable));
assert.deepEqual(voice.read(voice.exchange("begin_edit", {
  schema_version: 1, program_id: prepared.preview_sound_id,
})).document, document);

const reopened = openVoice();
assert.equal(reopened.exchange("install", prepared), 0);
reopened.load(prepared.preview_sound_id);
for (const {id, index} of parameters.filter(({id}) => !live.includes(id))) {
  assert.equal(reopened.get(index), document.payload.parameters[id], id);
}
assert.equal(reopened.get(45), 0);
assert.equal(reopened.get(48), 0);
assert.deepEqual([49, 50, 51, 53].map(reopened.get), [8192, 0, 0, 0]);
assert.equal(reopened.get(55), 0);
for (let slot = 2; slot <= 64; slot++) {
  const id = `user-${String(slot).padStart(2, "0")}`;
  const label = "Ó".repeat(61) + String(slot);
  const draft = {...document, id, name: label};
  const saved = reopened.read(reopened.exchange("prepare_save", draft));
  assert.equal(reopened.exchange("install", saved), 0, id);
}
assert.equal(reopened.catalog().presets.filter(({bank}) => bank === "user").length, 64);
assert.ok(reopened.exchange("begin_edit", {schema_version: 1}) < 0);
fs.writeFileSync(process.argv[4], JSON.stringify(document));
console.log("RF-D program round trip, validation, preview and fresh-instance restore passed");
