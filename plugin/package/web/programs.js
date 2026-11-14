(() => {
  const selector = document.querySelector(".programs rf-program-select");
  const status = document.getElementById("program-status");
  const importFile = document.getElementById("rfd-import");
  const exportButton = document.getElementById("rfd-export");
  const saveButton = document.getElementById("program-save-open");
  const saveDialog = document.getElementById("program-save-dialog");
  const saveName = document.getElementById("program-name");
  const saveStatus = document.getElementById("program-save-status");
  const saveCancel = document.getElementById("program-save-cancel");
  const saveConfirm = document.getElementById("program-save-confirm");
  const fields = JSON.parse(document.getElementById("program-fields").textContent);
  const api = "rackforge.plugin.web@1";
  const format = "rackforge.rf-d.program";
  const maxBytes = 16_384;
  const origin = window.location.origin;
  const pending = new Map();
  let requestIndex = 0;
  let context;
  let busy = false;

  function request(method, params = {}) {
    return new Promise((resolve, reject) => {
      const id = `rfd-program-${++requestIndex}`;
      const timer = setTimeout(() => {
        pending.delete(id);
        reject(new Error("RackForge did not respond."));
      }, 5000);
      pending.set(id, (message) => {
        clearTimeout(timer);
        if (message.ok) resolve(message.result);
        else reject(new Error(message.error || "RackForge rejected the program."));
      });
      window.parent.postMessage({protocol: api, kind: "request", request_id: id, method, params}, origin);
    });
  }

  function refresh() {
    const disabled = busy || !context || !!context.program_draft;
    const editingDisabled = disabled || !!context?.isolated;
    selector.toggleAttribute("disabled", disabled);
    exportButton.disabled = disabled;
    if (importFile) importFile.disabled = editingDisabled;
    if (saveButton) {
      saveButton.disabled = editingDisabled;
      saveName.readOnly = busy;
      saveConfirm.disabled = editingDisabled;
      saveCancel.disabled = busy;
    }
  }

  async function waitForDraft(check) {
    const until = performance.now() + 5000;
    while (performance.now() < until) {
      const draft = context?.program_draft;
      if (draft?.document_json) {
        const document = JSON.parse(draft.document_json);
        if (check(document, draft)) return {draft, document};
      }
      await new Promise((resolve) => setTimeout(resolve, 40));
    }
    throw new Error("The program draft was not published.");
  }

  function cleanName(value) {
    const trimmed = value.trim();
    if (!trimmed || trimmed.length > 64 || /[\p{Cc}\p{Cf}]/u.test(trimmed)) {
      throw new Error("Enter a program name of up to 64 characters.");
    }
    return trimmed;
  }

  async function run(action, allowIsolated = false, feedback = status) {
    if (busy || !context || (context.isolated && !allowIsolated) || context.program_draft) return;
    busy = true;
    status.textContent = "";
    refresh();
    try {
      await action();
    } catch (error) {
      feedback.textContent = error.message;
    } finally {
      busy = false;
      refresh();
    }
  }

  async function withNewDraft(action) {
    await request("plugin.begin_program_edit", {program_id: null});
    const {draft, document} = await waitForDraft(() => true);
    try {
      await action(draft, document);
      await request("plugin.save_program", {draft_id: draft.draft_id});
      return draft;
    } catch (error) {
      if (context?.program_draft?.draft_id === draft.draft_id) {
        await request("plugin.cancel_program", {draft_id: draft.draft_id}).catch(() => {});
      }
      throw error;
    }
  }

  async function activateSaved(draft, message) {
    const soundId = draft.preview_sound_id;
    const until = performance.now() + 5000;
    while (performance.now() < until) {
      if (!context?.program_draft && context?.instance.sounds?.some(({id}) => id === soundId)) {
        try {
          await request("plugin.select_sound", {sound_id: soundId});
          return message;
        } catch {
          break;
        }
      }
      await new Promise((resolve) => setTimeout(resolve, 40));
    }
    return `${message} Select it from Programs to load it.`;
  }

  function validateFile(source) {
    let file;
    try {
      file = JSON.parse(source);
    } catch {
      throw new Error("This .rfd file contains invalid JSON.");
    }
    if (file?.format !== format || file.version !== 1 || typeof file.name !== "string"
      || !file.parameters || Array.isArray(file.parameters) || typeof file.parameters !== "object"
      || Object.keys(file.parameters).some((key) => !fields.some(({id}) => id === key))) {
      throw new Error("This file is not an RF-D v1 program.");
    }
    const parameters = {};
    for (const {id, kind, missing_default} of fields) {
      const value = Object.hasOwn(file.parameters, id) ? file.parameters[id] : missing_default;
      if (!validValue(kind, value)) throw new Error(`Invalid program setting: ${id}.`);
      parameters[id] = value;
    }
    return {name: cleanName(file.name), parameters};
  }

  function validValue(kind, value) {
    if (!Number.isFinite(value)) return false;
    if (kind.type === "boolean") return value === 0 || value === 1;
    if (kind.type === "enum") return kind.choices.some((choice) => choice.value === value);
    return value >= kind.minimum && value <= kind.maximum;
  }

  saveButton?.addEventListener("click", () => {
    saveName.value = "";
    saveStatus.textContent = "";
    saveDialog.showModal();
  });
  saveCancel?.addEventListener("click", () => saveDialog.close());
  saveDialog?.addEventListener("close", () => saveButton.focus());
  saveDialog?.addEventListener("cancel", (event) => {
    if (busy) event.preventDefault();
  });
  saveName?.addEventListener("keydown", (event) => {
    if (event.key !== "Enter" || event.isComposing) return;
    event.preventDefault();
    saveConfirm.click();
  });
  saveConfirm?.addEventListener("click", async () => {
    let saved = false;
    await run(async () => {
      const programName = cleanName(saveName.value);
      saveStatus.textContent = "Saving…";
      const draft = await withNewDraft(async ({draft_id}) => {
        await request("plugin.set_program_name", {draft_id, name: programName});
        await waitForDraft((document, updated) => updated.dirty && document.name === programName);
      });
      status.textContent = await activateSaved(draft, `Saved “${programName}”.`);
      saved = true;
    }, false, saveStatus);
    if (saved) saveDialog.close();
  });

  exportButton.addEventListener("click", () => run(async () => {
    const selected = context.instance.sounds?.find((sound) => sound.id === context.instance.selected_sound_id);
    const programName = cleanName(selected?.name || "RF-D Program");
    const snapshot = await request("plugin.parameters");
    const byIndex = new Map(snapshot.values.map(({index, value}) => [index, value]));
    const parameters = Object.fromEntries(fields.map(({id, index}) => [id, byIndex.get(index)]));
    if (!fields.every(({id, kind}) => validValue(kind, parameters[id]))) {
      throw new Error("RackForge returned an incomplete panel.");
    }
    const file = JSON.stringify({format, version: 1, name: programName, parameters}, null, 2) + "\n";
    const url = URL.createObjectURL(new Blob([file], {type: "application/json"}));
    const link = document.createElement("a");
    link.href = url;
    link.download = programName.replace(/[^\p{L}\p{N}_ -]/gu, "_") + ".rfd";
    document.body.append(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    status.textContent = `Exported “${programName}”.`;
  }, true));

  importFile?.addEventListener("change", () => {
    const file = importFile.files[0];
    importFile.value = "";
    if (!file) return;
    run(async () => {
      if (file.size > maxBytes) throw new Error("The .rfd file exceeds 16 KiB.");
      const patch = validateFile(await file.text());
      const draft = await withNewDraft(async ({draft_id}, document) => {
        await request("plugin.replace_program_draft", {
          draft_id, document: {...document, name: patch.name, payload: {parameters: patch.parameters}},
        });
      });
      status.textContent = await activateSaved(draft, `Imported “${patch.name}”.`);
    });
  });

  window.addEventListener("message", (event) => {
    const message = event.data;
    if (event.source !== window.parent || event.origin !== origin || message?.protocol !== api) return;
    if (message.kind === "context") {
      context = message;
      refresh();
    } else if (message.kind === "response") {
      const callback = pending.get(message.request_id);
      pending.delete(message.request_id);
      callback?.(message);
    }
  });
})();
