"""Build the RF-D PLAY surface from the public parameter schema."""
from html import escape
import json
from math import cos, radians, sin
from pathlib import Path

from rf_d_rocker_svg import rocker_symbols

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "plugin/package/web"
LIVE_PARAMETERS = {
    "tuner_a440", "pitch_cv", "filter_cv", "loudness_cv", "external_s_trigger",
    "pitch_wheel", "mod_wheel", "glide_pedal", "decay_pedal",
    "glide_pedal_resistance", "decay_pedal_resistance",
    "voice_mode",
}


def program_parameters(schema):
    return [param for param in schema["parameters"]
            if param["id"] not in LIVE_PARAMETERS and param["kind"]["type"] != "meter"]


def hardware(shape, css_class=""):
    return f'<svg class="{css_class}" viewBox="0 0 100 100" aria-hidden="true"><use href="#{shape}"/></svg>'


WAVEFORM_MARKS = {
    "Triangle": "M0 3 5 -3 10 3",
    "Saw–Triangle": "M0 3 6 -3 6 0 10 3",
    "Reverse Sawtooth": "M0 3V-3L10 3",
    "Sawtooth": "M0 3 10 -3V3",
    "Square": "M0 3V-3H5V3H10",
    "Wide Pulse": "M0 3V-3H7V3H10",
    "Narrow Pulse": "M0 3V-3H2V3H10",
}
MODULATION_ENDPOINTS = ('<span class="scale-endpoints" aria-hidden="true">'
                        '<span>Osc. 3</span><span>Noise</span></span>')


def selector_scale(choices):
    marks = []
    for index, name in choices:
        angle = radians(-135 + 270 * index / (len(choices) - 1))
        x, y = 50 + 44 * sin(angle), 50 - 44 * cos(angle)
        if name in WAVEFORM_MARKS:
            marks.append(f'<path d="{WAVEFORM_MARKS[name]}" transform="translate({x - 5:.2f} {y:.2f})"/>')
        else:
            marks.append(f'<text x="{x:.2f}" y="{y:.2f}">{escape(name)}</text>')
    return '<svg class="selector-scale" viewBox="0 0 100 100" aria-hidden="true">' + "".join(marks) + '</svg>'


def link_target(param):
    if param["kind"]["type"] == "meter" or param["flags"].get("read_only", False):
        return ""
    return f' data-rackforge-parameter-index="{param["index"]}"'


def field(param, label=None, *, style=None, socket=False, accessible_name=None):
    name = label or param["name"]
    index = param["index"]
    kind = param["kind"]
    variant = kind["type"]
    style = style or {"boolean": "rocker", "meter": "lamp"}.get(variant, "knob")
    attrs = f'data-index="{index}" disabled'
    if accessible_name:
        attrs += f' aria-label="{escape(accessible_name, quote=True)}"'
    number = '<output class="value" aria-hidden="true"></output>'
    choices = ""
    if variant == "enum":
        values = [(choice["value"], choice["name"]) for choice in kind["choices"]]
        assert [value for value, _ in values] == list(range(len(values)))
        encoded = escape(json.dumps([name for _, name in values], ensure_ascii=False), quote=True)
        choices = f' data-choices="{encoded}"'
    link = link_target(param)
    marks = ""
    orientation = ""
    if style == "pedal":
        return (f'<button class="control jack pedal" type="button" id="control-{param["id"]}"{link} '
                f'aria-pressed="false" {attrs}>{hardware("jack")}<span>{escape(name)}</span></button>')
    if style == "rocker":
        assert variant != "enum" or len(values) == 2
        stem = param["id"]
        axis = "horizontal"
        frame = "horizontal"
        if stem == "noise_color":
            orientation = " rocker-vertical rocker-noise"
            axis, frame = "down", "vertical"
            marks = ('<span class="switch-legend switch-start" aria-hidden="true">White</span>'
                     '<span class="switch-legend switch-end" aria-hidden="true">Pink</span>')
        elif stem == "external_s_trigger":
            choices = ' data-choices="[&quot;Open&quot;, &quot;Closed&quot;]"'
            marks = '<span class="switch-legend switch-end" aria-hidden="true">Closed</span>'
        else:
            if stem == "osc3_tracking":
                orientation = " rocker-vertical"
                axis, frame = "up", "vertical"
            elif stem == "filter_tracking_one_third":
                orientation = " rocker-mark-above"
            marks = '<span class="switch-legend switch-end" aria-hidden="true">On</span>'
        checked = " checked" if kind["default"] else ""
        state_id = f'state-{stem}'
        number = f'<output id="{state_id}" class="value sr-only" aria-hidden="true"></output>'
        widget = (f'<input type="checkbox"{checked}{choices} {attrs} aria-describedby="{state_id}">'
                  '<svg viewBox="0 0 100 100" aria-hidden="true">'
                  f'<use href="#rocker-frame-{frame}"/>'
                  f'<use href="#rocker-{axis}-on" class="rocker-on"/>'
                  f'<use href="#rocker-{axis}-off" class="rocker-off"/>'
                  '</svg>')
    elif style == "lamp":
        widget = hardware("lamp") + f'<meter data-index="{index}" min="0" max="1" value="0"></meter>'
        number = ""
    elif variant == "enum":
        scale = selector_scale(values) if len(values) == 6 else ""
        widget = (hardware("selector") + scale + hardware("pointer", "pointer")
                  + f'<input type="range" min="0" max="{len(values) - 1}" step="1"'
                    f' value="{kind["default"]}"{choices} {attrs}>')
    else:
        scale = ' data-scale="log"' if kind.get("taper") == "logarithmic" else ""
        unit = escape(kind.get("unit", ""), quote=True)
        front = hardware("wheel") if style == "wheel" else hardware("pot") + hardware("pointer", "pointer")
        wheel = f' data-wheel="{param["id"]}"' if style == "wheel" else ""
        widget = (front + f'<input type="range" min="{kind["minimum"]}" max="{kind["maximum"]}"'
                  f' step="{kind["step"]}" value="{kind["default"]}" data-unit="{unit}"{scale}{wheel} {attrs}>')
    classes = f"rotary {style}" if style in ("knob", "wheel") else style + orientation
    socket_icon = hardware("trigger-jack" if param["id"] == "external_s_trigger" else "jack", "socket") if socket else ""
    endpoints = MODULATION_ENDPOINTS if param["id"] == "modulation_mix" else ""
    return (f'<label class="control {classes}" id="control-{param["id"]}"{link}>'
            f'<span class="label">{escape(name)}</span><span class="mechanism">{widget}{marks}</span>'
            f'{socket_icon}{number}{endpoints}</label>')


def group(title, controls, css_class=""):
    return f'<div class="group {css_class}" role="group" aria-label="{title}">{"".join(controls)}</div>'


def section(title, content, css_class=""):
    return f'<section class="module {css_class}"><h2>{title}</h2><div class="module-body">{content}</div></section>'


def render_panel(schema, bank, programs=False):
    params = {item["id"]: item for item in schema["parameters"]}
    used = set()

    def control(name, label=None, *, style=None, socket=False, accessible_name=None):
        if name not in params:
            return ""
        assert name not in used, name
        used.add(name)
        return field(params[name], label, style=style, socket=socket, accessible_name=accessible_name)

    voices = ""
    if "voice_mode" in params:
        mode = params["voice_mode"]
        used.add(mode["id"])
        voices = (f'<label class="control voice-mode"{link_target(mode)}><span>Voices</span>'
                  f'<select data-index="{mode["index"]}" disabled>'
                  + "".join(f'<option value="{choice["value"]}">{escape(choice["name"])}</option>'
                            for choice in mode["kind"]["choices"])
                  + '</select></label>')

    if not bank:
        front = "".join(section(page["name"], group(page["name"], [
            control(p["id"]) for p in sorted(params.values(), key=lambda p: p["order"]) if p["page"] == page["id"]
        ])) for page in sorted(schema["pages"], key=lambda page: page["order"]))
        rear = ""
        left_hand = ""
    else:
        has_left_hand = "pitch_wheel" in params
        hand_switches = ((control("glide_enabled", "Glide"), control("decay_enabled", "Decay", style="rocker"))
                         if not has_left_hand else ())
        oscillator_modulation = control("oscillator_modulation", "Oscillator Modulation")
        controllers = section("Controllers", group("Tuning and performance", (
            control("tune", "Tune"),
            f'<div class="oscillator-modulation">{oscillator_modulation}</div>' if oscillator_modulation else "",
            control("glide_time", "Glide"), control("modulation_mix", "Modulation Mix"),
            *hand_switches,
        )), "controllers")
        left_hand = ""
        if has_left_hand:
            left_hand = ('<section class="left-hand" id="left-hand" aria-label="Left-hand controller">'
                         '<div class="pedal-switches">'
                         + control("glide_pedal", "Glide Pedal", style="pedal")
                         + control("glide_enabled", "Glide")
                         + control("decay_pedal", "Decay Pedal", style="pedal")
                         + control("decay_enabled", "Decay", style="rocker")
                         + '</div><div class="wheels">'
                         + control("pitch_wheel", "Pitch", style="wheel")
                         + control("mod_wheel", "Mod.", style="wheel")
                         + '</div><details><summary>Resistive pedals</summary>'
                         + group("Pedal resistance", (
                             control("glide_pedal_resistance", "Glide"),
                             control("decay_pedal_resistance", "Decay"),
                         ))
                         + '</details></section>')
        oscillator_rows = ""
        for index in range(1, 4):
            tracking = control("osc3_tracking", "Osc. 3 Control") if index == 3 else ""
            oscillator_rows += (
                f'<div class="osc-row" role="group" aria-label="Oscillator {index}">'
                f'<h3>Oscillator {index}</h3>'
                + control(f"osc{index}_range", "Range", accessible_name=f"Oscillator {index} Range")
                + (control(f"osc{index}_frequency", "Frequency", accessible_name=f"Oscillator {index} Frequency")
                   if index > 1 else '<span></span>')
                + control(f"osc{index}_wave", "Waveform", accessible_name=f"Oscillator {index} Waveform")
                + (f'<div class="oscillator-control">{tracking}</div>' if tracking else "")
                + "</div>"
            )
        oscillators = section("Oscillator Bank", oscillator_rows, "oscillators")

        def mixer_channel(level, enable, label, *, indicator=""):
            heading = f"{label} Volume" if indicator else label
            return (f'<div class="mixer-channel" role="group" aria-label="{label}">'
                    f'<h3>{heading}</h3><div class="channel">'
                    + control(level, "Volume", accessible_name=f"{label} Volume")
                    + control(enable, label, accessible_name=f"{label} Mixer Switch")
                    + indicator + '</div></div>')

        external = mixer_channel("external_level", "external_enabled", "External Input",
                                 indicator=control("external_overload")) if "external_level" in params else ""
        noise = mixer_channel("noise_level", "noise_enabled", "Noise",
                              indicator=control("noise_color", "Noise Color", style="rocker")) if "noise_level" in params else ""
        mixer = section("Mixer",
            '<div class="mixer-oscillators">'
            + mixer_channel("saw_mix", "osc1_enabled", "OSC 1")
            + mixer_channel("osc2_level", "osc2_enabled", "OSC 2")
            + mixer_channel("osc3_level", "osc3_enabled", "OSC 3")
            + '</div><div class="mixer-sources">' + external + noise + '</div>', "mixer")


        filter_switches = ""
        if "filter_tracking_one_third" in params:
            filter_switches = ('<div class="filter-switches" role="group" aria-label="Filter switches">'
                + control("filter_modulation", "Filter Modulation")
                + '<div class="keyboard-control" role="group" aria-labelledby="keyboard-control-heading">'
                  '<h4 id="keyboard-control-heading">Keyboard Control</h4>'
                + control("filter_tracking_one_third", "1", accessible_name="Keyboard Control 1 (one-third)")
                + control("filter_tracking_two_thirds", "2", accessible_name="Keyboard Control 2 (two-thirds)")
                + '</div></div>')
        modifiers = section("Modifiers",
            '<h3>Filter</h3>' + group("Filter", (control("cutoff", "Cutoff Frequency"), control("emphasis"),
                                                control("contour_amount", "Amount of Contour")), "three")
            + filter_switches
            + '<h3>Filter Contour</h3>' + group("Filter Contour", (
                control("filter_attack", "Attack Time", accessible_name="Filter Attack Time"),
                control("filter_decay", "Decay Time", accessible_name="Filter Decay Time"),
                control("filter_sustain", "Sustain Level", accessible_name="Filter Sustain Level")), "three")
            + '<h3>Loudness Contour</h3>' + group("Loudness Contour", (
                control("loudness_attack", "Attack Time", accessible_name="Loudness Attack Time"),
                control("loudness_decay", "Decay Time", accessible_name="Loudness Decay Time"),
                control("loudness_sustain", "Sustain Level", accessible_name="Loudness Sustain Level")), "three"), "modifiers")

        output = section("Output", group("Output controls", (
            control("output_level", "Volume", accessible_name="Main Output Volume"), control("main_output_enabled", "Main Output"),
            control("tuner_a440", "A-440"), control("headphones_level", "Phones Volume"),
        ), "output-controls"), "output")
        if has_left_hand:
            controllers = f'<div class="left-column">{controllers}{left_hand}</div>'
        front = controllers + oscillators + mixer + modifiers + output

        rear_parts = []
        has_feedback = "output_feedback" in params
        if "output_jack" in params:
            selector = params["output_jack"]
            used.add("output_jack")
            index = selector["index"]
            choices = {entry["name"]: entry["value"] for entry in selector["kind"]["choices"]}
            items = "".join(f'<button type="button" class="jack route" data-choice="{choices[name]}"{link_target(selector)} '
                            f'aria-pressed="{str(choices[name] == selector["kind"]["default"]).lower()}" '
                            f'aria-label="{name} output" disabled>{hardware("jack")}<span>{name}</span></button>'
                            for name in ("LO", "HI", "Phones") if name in choices)
            select_attr = "" if has_feedback else "hidden "
            rear_parts.append(
                '<section class="patch-block"><h3>Monitor Output</h3>'
                f'<div class="control output-route"{link_target(selector)}>'
                f'<select {select_attr}aria-label="Monitor Output" data-index="{index}" disabled>'
                + "".join(f'<option value="{value}"{" selected" if value == selector["kind"]["default"] else ""}>'
                          f'{escape(name)}</option>' for name, value in choices.items())
                + '</select>'
                + ("" if has_feedback else f'<div class="jacks">{items}</div>')
                + '</div><p>RackForge main bus</p></section>'
            )
        if "external_enabled" in params and not has_feedback:
            rear_parts.append('<section class="patch-block"><h3>Signal In</h3>'
                              f'<a class="jack" href="#control-external_level"{link_target(params["external_level"])}>'
                              f'{hardware("jack")}<span>External</span></a>'
                              '<p>Rack audio input</p></section>')
        if "pitch_cv" in params:
            rear_parts.append('<section class="patch-block"><h3>Ext. Control Inputs</h3><div class="jacks cv">'
                              + control("loudness_cv", "Loudness CV", socket=True)
                              + control("filter_cv", "Filter CV", socket=True)
                              + control("pitch_cv", "Oscillator CV", socket=True)
                              + control("external_s_trigger", "S-Trigger", style="rocker", socket=True)
                              + '</div></section>')
        if has_feedback:
            used.add("output_feedback")
            rear_parts.insert(0, feedback_patch(params["output_feedback"]))
        if "glide_enabled" in params and not has_left_hand:
            rear_parts.append(
                '<section class="patch-block"><h3>Pedal Controls</h3><div class="jacks">'
                + "".join(f'<a class="jack" href="#control-{name}" '
                          f'{link_target(params[name])}>'
                          f'{hardware("jack")}<span>{label}</span></a>'
                          for name, label in (("glide_enabled", "Glide"), ("decay_enabled", "Decay")))
                + '</div><p>Link a MIDI pedal</p></section>'
            )
        rear = ('<section class="rear" id="connections" aria-labelledby="connections-heading">'
                '<h2 id="connections-heading">Connections</h2><div class="patch-panel">'
                + "".join(rear_parts) + '</div></section>') if rear_parts else ""

    assert used == params.keys(), sorted(params.keys() - used)
    symbols = (WEB / "hardware.svg").read_text(encoding="utf8")
    symbols = symbols.replace("</defs>", rocker_symbols() + "\n  </defs>", 1)
    program_panel = program_toolbar("play", schema) if programs else "<rf-program-select></rf-program-select>"
    program_script = '<script src="programs.js" defer></script>' if programs else ""
    patch_script = '<script src="patch-cable.js" defer></script>' if "output_feedback" in params else ""
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>RF-D</title>
  <link rel="stylesheet" href="voice.css">
  {patch_script}
  <script src="panel.js" defer></script>
  {program_script}
</head>
<body>
  {symbols}
  <main class="instrument">
    <div class="faceplate">
      <header class="masthead">
        <h1 class="nameplate"><small>Rackforge Instruments</small><span>RF-D</span></h1>
        {program_panel}
        {voices}
        <p class="status" id="status" role="status">Connecting to RackForge…</p>
      </header>
      <div class="controls{' single' if not bank else ''}">{front}</div>
      {rear}
    </div>
  </main>
</body>
</html>
"""


def feedback_patch(parameter):
    index = parameter["index"]
    return f"""<section class="patch-block feedback-patch" aria-labelledby="feedback-heading">
      <h3 id="feedback-heading">Feedback</h3>
      <div class="control feedback-controls">
        <div class="patch-sockets">
          <button type="button" class="jack" data-patch-port="lo"{link_target(parameter)} aria-label="LO output for feedback"
            aria-pressed="false" aria-describedby="feedback-status" disabled>{hardware("jack")}<span>LO</span></button>
          <button type="button" class="jack" data-patch-port="ext"{link_target(parameter)} aria-label="External audio input for feedback"
            aria-pressed="false" aria-describedby="feedback-status" disabled>{hardware("jack")}<span>EXT</span></button>
          <svg class="patch-cable" aria-hidden="true">
            <defs><path id="feedback-curve"/><path id="feedback-highlight"/></defs>
            <use href="#feedback-plug-seated" data-plug="start"/>
            <use href="#feedback-plug-seated" data-plug="end"/>
            <use href="#feedback-curve" class="cable-shadow"/>
            <use href="#feedback-curve" class="cable-edge"/>
            <use href="#feedback-curve" class="cable-body"/>
            <use href="#feedback-highlight" class="cable-sheen"/>
            <use href="#feedback-highlight" class="cable-glint"/>
            <use href="#feedback-plug-loose" data-plug="loose" display="none"/>
          </svg>
        </div>
        <input type="checkbox" data-index="{index}" data-patch-feedback hidden disabled>
        <output class="value"></output>
      </div>
      <p id="feedback-status" role="status">Connect LO to EXT</p>
    </section>"""



def program_toolbar(surface, schema):
    fields = json.dumps([{key: param[key] for key in ("id", "index", "kind")}
                         for param in program_parameters(schema)], ensure_ascii=False).replace("<", "\\u003c")
    save_program = ('''<label class="program-name"><span>Program name</span>
          <input id="program-name" maxlength="64" placeholder="Program name" required disabled>
        </label>
        <button type="submit" disabled>Save new</button>''' if surface == "play" else "")
    import_file = ('<label class="file-button">Import .rfd'
                   '<input type="file" id="rfd-import" accept=".rfd" disabled></label>'
                   if surface == "config" else "")
    return f"""<section class="programs" aria-labelledby="programs-heading">
      <h2 id="programs-heading">Programs</h2>
      <script id="program-fields" type="application/json">{fields}</script>
      <rf-program-select label="Programs"></rf-program-select>
      <form id="program-actions">
        {save_program}
        <button type="button" id="rfd-export" disabled>Export .rfd</button>
        {import_file}
      </form>
      <p id="program-status" role="status"></p>
    </section>"""


def render_program_config(schema):
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>RF-D Programs</title>
  <link rel="stylesheet" href="voice.css">
  <script src="panel.js" defer></script>
  <script src="programs.js" defer></script>
</head>
<body>
  <main class="instrument">
    <div class="faceplate">
      <header class="masthead">
        <h1 class="nameplate"><small>Rackforge Instruments</small><span>RF-D</span></h1>
        {program_toolbar("config", schema)}
        <p class="status" id="status" role="status">Connecting to RackForge…</p>
      </header>
    </div>
  </main>
</body>
</html>
"""
