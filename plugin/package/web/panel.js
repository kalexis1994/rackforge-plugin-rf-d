(() => {
  const protocol = "rackforge.plugin.web@1";
  const origin = window.location.origin;
  const status = document.getElementById("status");
  const controls = new Map();
  const pending = new Map();
  // Use RackForge's long-press interval and travel tolerance for touch gestures.
  const longPressMs = 560;
  const touchTolerance = 10;
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
    if (input.tagName === "BUTTON") return Number(input.getAttribute("aria-pressed") === "true");
    return input.type === "checkbox" ? Number(input.checked) : input.valueAsNumber;
  }

  function rotaryScale(input, value) {
    return input.dataset.scale === "log" ? Math.log(value) : value;
  }

  function paint(control, value) {
    const {input, label, choices, routes} = control;
    if (input.tagName === "SELECT") {
      input.value = value;
      for (const route of routes) route.setAttribute("aria-pressed", Number(route.dataset.choice) === value);
      return;
    }
    if (input.tagName === "METER") {
      input.value = value;
      input.dataset.active = value >= 0.1;
      return;
    }
    if (input.tagName === "BUTTON") {
      input.setAttribute("aria-pressed", value === 1);
      return;
    }
    const toggle = input.type === "checkbox";
    if (toggle) {
      input.checked = value >= 0.5;
      if (input.hasAttribute("data-patch-feedback")) input.dispatchEvent(new Event("rfd-patch-state"));
    }
    else input.value = value;
    const current = readValue(input);
    const wheel = input.dataset.wheel;
    const text = wheel ? formatWheel(wheel, current) : choices?.[current] ?? (toggle
      ? (input.checked ? "On" : "Off")
      : [input.value, input.dataset.unit].filter(Boolean).join(" "));
    label.querySelector(".value").textContent = text;
    input.setAttribute("aria-valuetext", text);
    if (label.classList.contains("rotary")) {
      const min = rotaryScale(input, Number(input.min));
      const max = rotaryScale(input, Number(input.max));
      const fraction = (rotaryScale(input, current) - min) / (max - min);
      if (wheel) label.style.setProperty("--wheel-offset", (32 - 64 * fraction) + "px");
      else label.style.setProperty("--rotation", (-135 + 270 * fraction) + "deg");
    }
  }

  function formatWheel(wheel, value) {
    if (wheel === "mod_wheel") return `${Math.round(100 * value / 127)} %`;
    const bend = (value - 8192) / (value < 8192 ? 8192 : 8191);
    return `${(6 * bend).toFixed(1)} st`;
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
      flushControl(index, control);
    }
  }

  function flushControl(index, control) {
    if (control.waiting || control.queued === undefined) return;
    const value = control.queued;
    control.queued = undefined;
    control.waiting = true;
    const param = {parameter_index: index, value};
    request("plugin.set_parameter", param, (message) => {
      control.waiting = false;
      if (message.ok) {
        acceptValue(index, message.result?.value ?? value);
        setStatus("Ready for MIDI", true);
      } else {
        setStatus(message.error || "RackForge rejected the control.");
        if (control.queued === undefined) paint(control, control.canonical);
      }
      if (control.queued !== undefined) {
        if (control.input.tagName === "BUTTON") flushControl(index, control);
        else schedule();
      }
    });
  }

  function queue(control, value) {
    if (!connected) return;
    control.queued = value;
    paint(control, value);
    schedule();
  }

  function bindPedal(index, control) {
    const {input} = control;
    let press;
    let keyHeld = false;
    const send = (value) => {
      if (!connected) return;
      control.queued = value;
      paint(control, value);
      flushControl(index, control);
    };
    input.addEventListener("pointerdown", (event) => {
      if (!event.isPrimary || event.button !== 0 || press) return;
      press = startGesture(event);
      input.setPointerCapture(event.pointerId);
      if (press.active && !keyHeld) send(1);
    });
    input.addEventListener("pointermove", (event) => {
      if (press?.id !== event.pointerId || press.active || !beginDrag(press, event)) return;
      press.active = true;
      if (!keyHeld) send(1);
    });
    input.addEventListener("lostpointercapture", (event) => {
      if (press?.id !== event.pointerId) return;
      const held = press.active;
      press = undefined;
      if (held && !keyHeld) send(0);
    });
    input.addEventListener("pointerup", (event) => {
      if (press?.id !== event.pointerId || press.active || keyHeld
          || event.timeStamp - press.time >= longPressMs) return;
      send(1);
      send(0);
    });
    const pedalKey = (event) => event.key === " " || event.key === "Enter";
    input.addEventListener("keydown", (event) => {
      if (!pedalKey(event)) return;
      event.preventDefault();
      if (!keyHeld) {
        keyHeld = true;
        if (!press?.active) send(1);
      }
    });
    const releaseKey = () => {
      if (!keyHeld) return;
      keyHeld = false;
      if (!press?.active) send(0);
    };
    input.addEventListener("keyup", (event) => {
      if (!pedalKey(event)) return;
      event.preventDefault();
      releaseKey();
    });
    input.addEventListener("blur", releaseKey);
  }

  function startGesture(event) {
    return {id: event.pointerId, x: event.clientX, y: event.clientY, time: event.timeStamp,
      active: event.pointerType === "mouse"};
  }

  function beginDrag(gesture, event) {
    return event.timeStamp - gesture.time < longPressMs
      && Math.hypot(event.clientX - gesture.x, event.clientY - gesture.y) > touchTolerance;
  }

  function schedule() {
    if (!frame) frame = window.requestAnimationFrame(flush);
  }

  for (const input of document.querySelectorAll("[data-index]")) {
    const index = Number(input.dataset.index);
    const label = input.closest(".control");
    const choices = input.dataset.choices ? JSON.parse(input.dataset.choices) : undefined;
    const routes = label.querySelectorAll("[data-choice]");
    const control = {input, label, choices, routes, canonical: readValue(input)};
    controls.set(index, control);
    paint(control, control.canonical);
    if (input.tagName === "METER") continue;
    if (input.tagName === "BUTTON") {
      bindPedal(index, control);
      continue;
    }
    input.addEventListener("input", () => queue(control, readValue(input)));
    if (input.dataset.wheel === "pitch_wheel") {
      input.addEventListener("keydown", (event) => {
        if (event.key !== "Escape") return;
        event.preventDefault();
        queue(control, 8192);
      });
      input.addEventListener("dblclick", () => queue(control, 8192));
    }
    for (const route of routes) {
      route.addEventListener("click", () => queue(control, Number(route.dataset.choice)));
      route.addEventListener("keydown", (event) => {
        const direction = ["ArrowRight", "ArrowDown"].includes(event.key) ? 1
          : ["ArrowLeft", "ArrowUp"].includes(event.key) ? -1 : 0;
        if (!direction) return;
        event.preventDefault();
        const options = [...routes];
        const next = options[(options.indexOf(route) + direction + options.length) % options.length];
        next.focus();
        next.click();
      });
    }
    if (!label.classList.contains("rotary")) continue;
    // Chromium's range thumb also responds to native touch events.
    input.addEventListener("touchstart", (event) => event.preventDefault(), {passive: false});
    input.addEventListener("pointerdown", (event) => {
      if (!connected || !event.isPrimary || event.button !== 0 || control.drag) return;
      event.preventDefault();
      input.focus();
      input.setPointerCapture(event.pointerId);
      control.drag = {...startGesture(event), value: rotaryScale(input, readValue(input))};
    });
    input.addEventListener("pointermove", (event) => {
      const drag = control.drag;
      if (!drag || drag.id !== event.pointerId) return;
      if (!drag.active) {
        if (!beginDrag(drag, event)) return;
        drag.active = true;
      }
      const min = rotaryScale(input, Number(input.min));
      const max = rotaryScale(input, Number(input.max));
      const distance = input.dataset.wheel ? 96 : 144;
      const next = Math.max(min, Math.min(max, drag.value + (drag.y - event.clientY) * (max - min) / distance));
      input.value = input.dataset.scale === "log" ? Math.exp(next) : next;
      input.dispatchEvent(new Event("input"));
    });
    input.addEventListener("lostpointercapture", (event) => {
      if (control.drag?.id !== event.pointerId) return;
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
      if (!message.instance?.instance_id) return;
      const key = JSON.stringify([message.instance.instance_id, message.instance.selected_sound_id,
        message.program_draft?.document_json]);
      if (key === contextKey) return;
      contextKey = key;
      if (!controls.size) {
        setStatus("Connected to RackForge", true);
        return;
      }
      request("plugin.parameters", {}, ({ok, result, error}) => {
        if (key !== contextKey) return;
        if (!ok || !Array.isArray(result?.values)) {
          contextKey = undefined;
          setStatus(error || "Could not read RF-D controls.");
          return;
        }
        for (const {index, value} of result.values) acceptValue(index, value);
        connected = true;
        for (const {input, routes} of controls.values()) {
          if (input.tagName !== "METER") input.disabled = false;
          for (const route of routes) route.disabled = false;
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
