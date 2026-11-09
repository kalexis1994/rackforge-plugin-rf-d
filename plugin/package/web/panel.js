(() => {
  const protocol = "rackforge.plugin.web@1";
  const origin = window.location.origin;
  const status = document.getElementById("status");
  const controls = new Map();
  const pending = new Map();
  let sequence = 0;
  let frame = 0;
  let connected = false;
  let contextKey;

  function setStatus(message, ready = false) {
    status.textContent = message;
    status.dataset.connected = ready;
  }

  function request(method, params, done) {
    const request_id = "rfd-" + ++sequence;
    const timer = window.setTimeout(() => {
      pending.delete(request_id);
      done({ok: false, error: "RackForge did not respond."});
    }, 4000);
    pending.set(request_id, (message) => {
      window.clearTimeout(timer);
      done(message);
    });
    window.parent.postMessage({protocol, kind: "request", request_id, method, params}, origin);
  }

  function paint(control, value) {
    const {input, label} = control;
    input.value = value;
    const actual = input.valueAsNumber;
    const text = input.value + " " + input.dataset.unit;
    label.querySelector(".value").textContent = text;
    input.setAttribute("aria-valuetext", text);
    if (label.classList.contains("rotary")) {
      const fraction = (actual - Number(input.min)) / (Number(input.max) - Number(input.min));
      label.style.setProperty("--rotation", (-135 + 270 * fraction) + "deg");
    }
  }

  function acceptValue(index, value) {
    const control = controls.get(index);
    if (!control || !Number.isFinite(value)) return;
    control.canonical = value;
    if (!control.waiting && control.queued === undefined && !control.drag) paint(control, value);
  }

  function flush() {
    frame = 0;
    for (const [index, control] of controls) {
      if (control.waiting || control.queued === undefined) continue;
      const value = control.queued;
      control.queued = undefined;
      control.waiting = true;
      request("plugin.set_parameter", {parameter_index: index, value}, (message) => {
        control.waiting = false;
        if (message.ok) {
          acceptValue(index, message.result?.value ?? value);
          setStatus("Ready for MIDI", true);
        } else {
          setStatus(message.error || "RackForge rejected the control.");
          if (control.queued === undefined) paint(control, control.canonical);
        }
        if (control.queued !== undefined) schedule();
      });
    }
  }

  function schedule() {
    if (!frame) frame = window.requestAnimationFrame(flush);
  }

  for (const input of document.querySelectorAll("input[data-index]")) {
    const index = Number(input.dataset.index);
    const label = input.closest(".control");
    const control = {input, label, canonical: input.valueAsNumber};
    controls.set(index, control);
    paint(control, control.canonical);
    input.addEventListener("input", () => {
      if (!connected) return;
      control.queued = input.valueAsNumber;
      paint(control, control.queued);
      schedule();
    });
    if (!label.classList.contains("rotary")) continue;
    input.addEventListener("pointerdown", (event) => {
      if (!connected || event.button !== 0 || control.drag) return;
      event.preventDefault();
      input.focus();
      input.setPointerCapture(event.pointerId);
      control.drag = {id: event.pointerId, y: event.clientY, value: input.valueAsNumber};
    });
    input.addEventListener("pointermove", (event) => {
      const drag = control.drag;
      if (!drag || drag.id !== event.pointerId) return;
      const span = Number(input.max) - Number(input.min);
      input.value = drag.value + (drag.y - event.clientY) * span / 144;
      input.dispatchEvent(new Event("input"));
    });
    input.addEventListener("lostpointercapture", () => {
      control.drag = undefined;
      if (!control.waiting && control.queued === undefined) paint(control, control.canonical);
    });
  }

  window.addEventListener("message", (event) => {
    const message = event.data;
    if (event.source !== window.parent || event.origin !== origin || message?.protocol !== protocol) return;
    if (message.kind === "context") {
      const key = message.instance?.instance_id;
      if (key === undefined || key === contextKey) return;
      contextKey = key;
      request("plugin.parameters", {}, ({ok, result, error}) => {
        if (!ok || !Array.isArray(result?.values)) {
          contextKey = undefined;
          setStatus(error || "Could not read RF-D controls.");
          return;
        }
        for (const {index, value} of result.values) acceptValue(index, value);
        connected = true;
        for (const {input} of controls.values()) input.disabled = false;
        setStatus("Ready for MIDI", true);
      });
    } else if (message.kind === "response") {
      const done = pending.get(message.request_id);
      pending.delete(message.request_id);
      done?.(message);
    } else if (message.kind === "parameter_changed") {
      acceptValue(message.parameter_index, message.value);
    }
  });

  if (window.parent === window) {
    setStatus("Open this panel from RackForge PLAY.");
  } else {
    window.parent.postMessage({protocol, kind: "ready"}, origin);
  }
})();
