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

  function readValue(input) {
    if (input.tagName === "SELECT") return Number(input.value);
    if (input.tagName === "METER") return input.value;
    return input.type === "checkbox" ? Number(input.checked) : input.valueAsNumber;
  }

  function rotaryScale(input, value) {
    return input.dataset.scale === "log" ? Math.log(value) : value;
  }

  function paint(control, value) {
    const {input, label} = control;
    if (input.tagName === "SELECT") {
      input.value = value;
      return;
    }
    if (input.tagName === "METER") {
      input.value = value;
      input.dataset.active = value >= 0.1;
      return;
    }
    const toggle = input.type === "checkbox";
    if (toggle) input.checked = value >= 0.5;
    else input.value = value;
    const text = toggle ? (input.checked ? "On" : "Off") : input.value + " " + input.dataset.unit;
    label.querySelector(".value").textContent = text;
    input.setAttribute("aria-valuetext", text);
    if (label.classList.contains("rotary")) {
      const min = rotaryScale(input, Number(input.min));
      const max = rotaryScale(input, Number(input.max));
      const fraction = (rotaryScale(input, readValue(input)) - min) / (max - min);
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

  for (const input of document.querySelectorAll("[data-index]")) {
    const index = Number(input.dataset.index);
    const label = input.closest(".control");
    const control = {input, label, canonical: readValue(input)};
    controls.set(index, control);
    paint(control, control.canonical);
    if (input.tagName === "METER") continue;
    input.addEventListener("input", () => {
      if (!connected) return;
      control.queued = readValue(input);
      paint(control, control.queued);
      schedule();
    });
    if (!label.classList.contains("rotary")) continue;
    input.addEventListener("pointerdown", (event) => {
      if (!connected || event.button !== 0 || control.drag) return;
      event.preventDefault();
      input.focus();
      input.setPointerCapture(event.pointerId);
      control.drag = {id: event.pointerId, y: event.clientY, value: rotaryScale(input, readValue(input))};
    });
    input.addEventListener("pointermove", (event) => {
      const drag = control.drag;
      if (!drag || drag.id !== event.pointerId) return;
      const min = rotaryScale(input, Number(input.min));
      const max = rotaryScale(input, Number(input.max));
      const next = Math.max(min, Math.min(max, drag.value + (drag.y - event.clientY) * (max - min) / 144));
      input.value = input.dataset.scale === "log" ? Math.exp(next) : next;
      input.dispatchEvent(new Event("input"));
    });
    input.addEventListener("lostpointercapture", () => {
      control.drag = undefined;
      if (!control.waiting && control.queued === undefined) paint(control, control.canonical);
    });
  }

  const meters = new Set(
    [...controls].filter(([, control]) => control.input.tagName === "METER").map(([index]) => index)
  );
  if (meters.size) {
    let polling = false;
    window.setInterval(() => {
      if (!connected || document.hidden || polling) return;
      polling = true;
      request("plugin.parameters", {}, ({ok, result}) => {
        polling = false;
        if (!ok || !Array.isArray(result?.values)) return;
        for (const {index, value} of result.values) {
          if (meters.has(index)) acceptValue(index, value);
        }
      });
    }, 100);
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
        for (const {input} of controls.values()) {
          if (input.tagName !== "METER") input.disabled = false;
        }
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
