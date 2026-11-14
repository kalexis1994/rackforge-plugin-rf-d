(() => {
  const input = document.querySelector("[data-patch-feedback]");
  if (!input) return;
  const panel = input.closest(".feedback-patch");
  const connections = panel.closest("details");
  const shelf = panel.querySelector(".patch-sockets");
  const ports = [...shelf.querySelectorAll("[data-patch-port]")];
  const svg = shelf.querySelector(".patch-cable");
  const curve = svg.querySelector("#feedback-curve");
  const highlight = svg.querySelector("#feedback-highlight");
  const startPlug = svg.querySelector('[data-plug="start"]');
  const endPlug = svg.querySelector('[data-plug="end"]');
  const loosePlug = svg.querySelector('[data-plug="loose"]');
  const status = panel.querySelector("#feedback-status");
  const reduced = matchMedia("(prefers-reduced-motion: reduce)");
  let armed;
  let pointer;
  let drag;
  let suppressPointerClick = false;
  let observedFeedback = input.checked;
  let frame = 0;
  let previousTime = 0;
  let middle;
  const velocity = {x: 0, y: 0};
  const longPressMs = 560;

  function location(x, y, bounds) {
    return {x: x - bounds.left, y: y - bounds.top};
  }

  function center(port, bounds) {
    const jack = port.querySelector("svg").getBoundingClientRect();
    return location(jack.x + jack.width / 2, jack.y + jack.height / 2, bounds);
  }

  function translate(point) {
    return `translate(${point.x.toFixed(2)} ${point.y.toFixed(2)})`;
  }

  function drawHighlight(start, first, second, end) {
    // Project the overhead light onto the local normal of the Bézier.
    const steps = 12;
    let path = "";
    for (let i = 0; i <= steps; i++) {
      const t = i / steps;
      const u = 1 - t;
      const a = u * u, b = 2 * u * t, c = t * t;
      const dx = a * (first.x - start.x) + b * (second.x - first.x) + c * (end.x - second.x);
      const dy = a * (first.y - start.y) + b * (second.y - first.y) + c * (end.y - second.y);
      const normalLight = -dx + dy * 0.35;
      const offset = 1.4 * normalLight / Math.max(dx * dx + dy * dy, 1);
      const x = u * a * start.x + 3 * a * t * first.x + 3 * u * c * second.x + t * c * end.x - dy * offset;
      const y = u * a * start.y + 3 * a * t * first.y + 3 * u * c * second.y + t * c * end.y + dx * offset;
      path += `${i ? "L" : "M"}${x.toFixed(2)},${y.toFixed(2)}`;
    }
    highlight.setAttribute("d", path);
  }

  function draw(time) {
    frame = 0;
    if ((!armed && !input.checked) || shelf.offsetWidth === 0) {
      svg.removeAttribute("data-visible");
      middle = undefined;
      velocity.x = velocity.y = 0;
      previousTime = 0;
      return;
    }

    const bounds = shelf.getBoundingClientRect();
    const start = center(armed || ports[0], bounds);
    const end = armed && pointer ? location(pointer.x, pointer.y, bounds)
      : armed ? {x: start.x + 27, y: start.y + 29} : center(ports[1], bounds);
    const span = Math.hypot(end.x - start.x, end.y - start.y);
    const sag = Math.min(34, 8 + span * 0.19);
    const midpoint = {x: (start.x + end.x) / 2, y: (start.y + end.y) / 2};
    const goal = {x: midpoint.x, y: midpoint.y + sag};
    const dt = previousTime ? Math.min(0.024, (time - previousTime) / 1000) : 1 / 60;
    previousTime = time;
    if (!middle || reduced.matches) {
      middle = goal;
      velocity.x = velocity.y = 0;
    } else {
      // Semi-implicit spring integration, with enough damping to settle in a few frames.
      for (const axis of ["x", "y"]) {
        velocity[axis] += dt * (230 * (goal[axis] - middle[axis]) - 24 * velocity[axis]);
        middle[axis] += dt * velocity[axis];
      }
    }

    // The cable exits each seated plug axially, then bends down into the panel view.
    const bowX = Math.max(-32, Math.min(32, middle.x - midpoint.x));
    const bowY = Math.max(4, Math.min(sag + 24, middle.y - midpoint.y));
    const first = {x: start.x, y: start.y + 6 + bowY};
    const second = {
      x: armed ? end.x + 0.27 * (start.x - end.x) + bowX : end.x,
      y: end.y + bowY + (armed ? 0 : 6),
    };
    curve.setAttribute("d", [`M${start.x},${start.y}`, `C${first.x},${first.y}`,
      `${second.x},${second.y}`, `${end.x},${end.y}`].join(" "));
    drawHighlight(start, first, second, end);
    startPlug.setAttribute("transform", translate(start));
    endPlug.setAttribute("display", armed ? "none" : "inline");
    loosePlug.setAttribute("display", armed ? "inline" : "none");
    if (armed) {
      const dx = second.x - end.x;
      const angle = Math.atan2(second.y - end.y, dx) * 180 / Math.PI - 90;
      const flip = dx < 0 ? " scale(-1 1)" : "";
      loosePlug.setAttribute("transform", `${translate(end)} rotate(${angle.toFixed(2)})${flip}`);
    } else {
      endPlug.setAttribute("transform", translate(end));
    }
    svg.setAttribute("data-visible", "");
    const moving = Math.hypot(middle.x - goal.x, middle.y - goal.y) > 0.1
      || Math.hypot(velocity.x, velocity.y) > 1;
    if (moving && !reduced.matches) {
      schedule();
    } else {
      middle = goal;
      previousTime = 0;
      velocity.x = velocity.y = 0;
    }
  }

  function schedule() {
    if (!frame) frame = requestAnimationFrame(draw);
  }

  function update() {
    for (const port of ports) {
      port.toggleAttribute("data-armed", armed === port);
      port.setAttribute("aria-pressed", input.checked || armed === port);
    }
    const message = armed ? `Connect to ${armed === ports[0] ? "EXT" : "LO"} · Esc cancels`
      : input.checked ? "LO → EXT · External On in Mixer" : "Tap two jacks or drag";
    if (status.textContent !== message) status.textContent = message;
    schedule();
  }

  function setFeedback(value) {
    // The hidden control shares the same serialized parameter path as the panel knobs.
    input.checked = value;
    input.dispatchEvent(new Event("input"));
  }

  function cancel() {
    if (drag) suppressPointerClick = true;
    drag = undefined;
    armed = pointer = undefined;
    for (const port of ports) port.removeAttribute("data-target");
    update();
  }

  function drop(port) {
    const connected = Boolean(port && port !== armed);
    cancel();
    if (connected !== input.checked) setFeedback(connected);
  }

  function tap(port) {
    if (input.checked) {
      setFeedback(false);
    } else if (armed && armed !== port) {
      drop(port);
    } else if (armed === port) {
      cancel();
    } else {
      armed = port;
      update();
    }
  }

  function heldForMenu(gesture, event) {
    return event.pointerType !== "mouse" && event.timeStamp - gesture.time >= longPressMs;
  }

  function jackAt(x, y) {
    return ports.find((port) => {
      const bounds = port.getBoundingClientRect();
      return x >= bounds.left && x <= bounds.right && y >= bounds.top && y <= bounds.bottom;
    });
  }

  for (const port of ports) {
    port.addEventListener("click", (event) => {
      // RackForge can consume a long press in the capture phase before this click.
      if (event.detail > 0 && suppressPointerClick) return;
      if (!input.disabled && !drag) tap(port);
    });
    port.addEventListener("pointerdown", (event) => {
      if (input.disabled || drag || !event.isPrimary || event.button !== 0) return;
      suppressPointerClick = false;
      drag = {id: event.pointerId, port, x: event.clientX, y: event.clientY, time: event.timeStamp, moved: false};
      port.setPointerCapture(event.pointerId);
    });
  }

  document.addEventListener("pointermove", (event) => {
    const {clientX: x, clientY: y} = event;
    if (!drag) {
      if (armed && event.pointerType === "mouse" && panel.contains(event.target)) {
        pointer = {x, y};
        schedule();
      }
      return;
    }
    if (drag.id !== event.pointerId) return;
    if (!drag.moved) {
      // Match RackForge's touch long-press tolerance so small movements don't start a patch.
      if (heldForMenu(drag, event)) return;
      const threshold = event.pointerType === "mouse" ? 6 : 10;
      if (Math.hypot(x - drag.x, y - drag.y) <= threshold) return;
      drag.moved = true;
      suppressPointerClick = true;
      armed = input.checked ? ports.find((port) => port !== drag.port) : drag.port;
    }
    pointer = {x, y};
    const target = jackAt(x, y);
    for (const port of ports) port.toggleAttribute("data-target", port === target && port !== armed);
    update();
  });
  document.addEventListener("pointerup", (event) => {
    if (drag?.id !== event.pointerId) return;
    const finished = drag;
    drag = undefined;
    const target = jackAt(event.clientX, event.clientY);
    if (finished.moved) drop(target);
    else if (target !== finished.port || heldForMenu(finished, event)) suppressPointerClick = true;
  });
  for (const eventName of ["pointercancel", "lostpointercapture"]) {
    document.addEventListener(eventName, (event) => {
      if (drag?.id !== event.pointerId) return;
      cancel();
    });
  }
  window.addEventListener("blur", () => {
    if (!drag && !armed) return;
    cancel();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape" || (!drag && !armed)) return;
    cancel();
  });
  connections.addEventListener("toggle", () => {
    if (connections.open) schedule();
    else cancel();
  });
  new ResizeObserver(schedule).observe(shelf);
  reduced.addEventListener("change", schedule);
  const enablePorts = () => {
    for (const port of ports) port.disabled = input.disabled;
  };
  new MutationObserver(enablePorts).observe(input, {attributes: true, attributeFilter: ["disabled"]});
  input.addEventListener("rfd-patch-state", () => {
    const changed = input.checked !== observedFeedback;
    observedFeedback = input.checked;
    if (changed && (drag || armed)) cancel();
    else update();
  });
  enablePorts();
  update();
})();
