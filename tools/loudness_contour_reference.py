"""Offline board-2 loudness/trigger circuit, not a complete Model D voice.

Nominal passive graph: evidence/loudness_contour_graph.json. Ebers-Moll and
Shockley parameters below are explicit laboratory hypotheses, not vintage fits.
All Newton trials use the same capacitor history. No stage/timer ADSR logic.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path

from filter_ladder_ebers_moll_dc_reference import _solve_linear
from semiconductor_ideal import thermal_voltage_v

GRAPH = Path(__file__).resolve().parents[1] / "evidence/loudness_contour_graph.json"
KCL_A = 1e-11
CORRECTION_V = 1e-8


@dataclass(frozen=True)
class Controls:
    attack_ohm: float = 10000.0
    decay_ohm: float = 100000.0
    sustain_lower_ohm: float = 2500.0
    final_decay: bool = True
    external_s_short: bool = False
    # Candidate values; designators conflict in the documentary corpus.
    trigger_base_ohm: float = 10000.0
    reset_pullup_ohm: float = 3300.0

    def validate(self):
        for value, maximum in ((self.attack_ohm, 1e6), (self.decay_ohm, 1e6),
                               (self.sustain_lower_ohm, 5000.0)):
            if not math.isfinite(value) or not 0 <= value <= maximum:
                raise ValueError("electrical pot resistance outside documentary domain")
        if self.trigger_base_ohm not in (10000.0, 4700.0):
            raise ValueError("unregistered trigger-base candidate")
        if self.reset_pullup_ohm not in (3300.0, 1000.0):
            raise ValueError("unregistered reset-pullup candidate")
        if type(self.final_decay) is not bool or type(self.external_s_short) is not bool:
            raise ValueError("ideal contact states must be boolean")


@dataclass(frozen=True)
class Semiconductors:
    is_a: float = 1e-14
    beta_forward: float = 100.0
    beta_reverse: float = 5.0
    temperature_k: float = 298.15
    germanium_is_a: float = 1e-8
    silicon_is_a: float = 1e-12
    diode_ideality: float = 1.5

    def validate(self):
        if any(not math.isfinite(value) or value <= 0 for value in vars(self).values()):
            raise ValueError("positive finite imposed semiconductor parameters required")


@dataclass(frozen=True)
class State:
    # Named terminals survive exact topological changes at pot endpoints.
    node_v: dict[str, float]
    capacitor_v: dict[str, float]


class Network:
    def __init__(self, controls=Controls(), devices=Semiconductors(), *,
                 load_conductance_s=0.0, load_reference_v=0.0, load_current_a=0.0,
                 timing_cap_farad=10e-6):
        controls.validate()
        devices.validate()
        if (not math.isfinite(load_conductance_s) or load_conductance_s < 0
                or not math.isfinite(load_reference_v) or not math.isfinite(load_current_a)
                or not math.isfinite(timing_cap_farad) or timing_cap_farad <= 0):
            raise ValueError("finite load and positive timing capacitance required")
        self.controls, self.devices = controls, devices
        self.load = (load_conductance_s, load_reference_v, load_current_a)
        self.graph = json.loads(GRAPH.read_text(encoding="utf-8"))
        self.rails = dict(self.graph["rails"], KEYBOARD_TRIGGER=0.0, EXTERNAL_S_TRIGGER=0.0)
        pot = dict(attack_ohm=controls.attack_ohm, decay_ohm=controls.decay_ohm,
                   sustain_lower_ohm=controls.sustain_lower_ohm,
                   sustain_upper_ohm=5000.0-controls.sustain_lower_ohm)
        self.resistors = []
        for part in self.graph["resistors"]:
            if (part["ref"] == "R49" and not controls.external_s_short
                    or part["ref"] == "LHC_FAST_DECAY" and controls.final_decay):
                continue
            value = pot[part["ohm"]] if isinstance(part["ohm"], str) else part["ohm"]
            if part["ref"] == "R_TRIGGER_BASE_DRAWING":
                value = controls.trigger_base_ohm
            if part["ref"] == "R25_DRAWING":
                value = controls.reset_pullup_ohm
            self.resistors.append((part["ref"], *part["between"], value))
        self.caps = [(p["ref"], *p["between"],
                      timing_cap_farad if p["ref"] == "C2" else p["farad"])
                     for p in self.graph["capacitors"]]
        self.bjts = self.graph["transistors"]
        self.diodes = [p for p in self.graph["diodes"]
                       if p.get("condition") != "final_decay_off" or not controls.final_decay]
        # Union exact zero-ohm branches, never add an epsilon resistance.
        self.alias = {}

        def find(name):
            parent = self.alias.setdefault(name, name)
            if parent != name:
                self.alias[name] = find(parent)
            return self.alias[name]

        for _, a, b, ohm in self.resistors:
            if ohm == 0:
                a, b = find(a), find(b)
                if a != b:
                    if a in self.rails and b in self.rails:
                        raise ValueError("contradictory ideal rail short")
                    if b in self.rails:
                        a, b = b, a
                    self.alias[b] = a
        names = set()
        for _, a, b, _ in self.resistors + self.caps:
            names.update((a, b))
        for p in self.bjts:
            names.update(p[k] for k in ("base", "collector", "emitter"))
        for p in self.diodes:
            names.update((p["anode"], p["cathode"]))
        self.alias = {name: find(name) for name in sorted(names)}
        self.nodes = sorted({self.alias[name] for name in names
                             if self.alias[name] not in self.rails})
        self.index = {name: i for i, name in enumerate(self.nodes)}
        self.vt = thermal_voltage_v(devices.temperature_k)

    def evaluate(self, x, keyboard_v, previous=None, dt_s=None, *, jacobian=True):
        if (len(x) != len(self.nodes) or not all(math.isfinite(v) for v in x)
                or not math.isfinite(keyboard_v) or not 0 <= keyboard_v <= 10):
            raise ValueError("finite trial and keyboard source in 0..10 V required")
        if previous is not None:
            if dt_s is None or not math.isfinite(dt_s) or dt_s <= 0:
                raise ValueError("positive finite transient interval required")
            if set(previous.capacitor_v) != {p[0] for p in self.caps} or any(
                    not math.isfinite(v) for v in previous.capacitor_v.values()):
                raise ValueError("complete finite capacitor history required")
        voltage = dict(self.rails, KEYBOARD_TRIGGER=keyboard_v)
        voltage.update(zip(self.nodes, x))
        voltage.update({name: voltage[alias] for name, alias in self.alias.items()})
        n = len(x)
        r = [0.0]*n
        j = [[0.0]*n for _ in x] if jacobian else None
        d = self.devices

        def row(name, current, derivatives):
            i = self.index.get(self.alias[name])
            if i is None:
                return
            r[i] += current
            if j is not None:
                for terminal, derivative in derivatives:
                    k = self.index.get(self.alias[terminal])
                    if k is not None:
                        j[i][k] += derivative

        def branch(a, b, current, g):
            row(a, current, ((a, g), (b, -g)))
            row(b, -current, ((a, -g), (b, g)))

        for _, a, b, ohm in self.resistors:
            if ohm:
                branch(a, b, (voltage[a]-voltage[b])/ohm, 1/ohm)
        if previous is not None:
            for ref, a, b, c in self.caps:
                g = c/dt_s
                branch(a, b, g*(voltage[a]-voltage[b]-previous.capacitor_v[ref]), g)
        for p in self.bjts:
            b, c, e = (p[k] for k in ("base", "collector", "emitter"))
            polarity = 1 if p["kind"] == "NPN" else -1
            xbe = polarity*(voltage[b]-voltage[e])/self.vt
            xbc = polarity*(voltage[b]-voltage[c])/self.vt
            if max(xbe, xbc) > 45:
                raise ValueError("trial outside BJT exponential domain")
            f, rev = d.is_a*math.expm1(xbe), d.is_a*math.expm1(xbc)
            gf, gr = d.is_a*math.exp(xbe)/self.vt, d.is_a*math.exp(xbc)/self.vt
            ib, ic = f/d.beta_forward+rev/d.beta_reverse, f-rev*(1+1/d.beta_reverse)
            gbf, gbr = gf/d.beta_forward, gr/d.beta_reverse
            gc_rev = gr*(1+1/d.beta_reverse)
            row(b, polarity*ib, ((b, gbf+gbr), (e, -gbf), (c, -gbr)))
            row(c, polarity*ic, ((b, gf-gc_rev), (e, -gf), (c, gc_rev)))
            row(e, -polarity*(ib+ic), ((b, -gf-gbf+gr), (e, gf+gbf), (c, -gr)))
        for p in self.diodes:
            a, k = p["anode"], p["cathode"]
            is_a = d.germanium_is_a if p["marking"] == "1N34A" else d.silicon_is_a
            scale = d.diode_ideality*self.vt
            exponent = (voltage[a]-voltage[k])/scale
            if exponent > 45:
                raise ValueError("trial outside diode exponential domain")
            branch(a, k, is_a*math.expm1(exponent), is_a*math.exp(exponent)/scale)
        g, ref, current = self.load
        row("LOUDNESS_OUT", g*(voltage["LOUDNESS_OUT"]-ref)+current,
            (("LOUDNESS_OUT", g),))
        return r, j

    def _direction(self, x, r, keyboard_v, previous, dt_s, use_fd):
        if not use_fd:
            _, j = self.evaluate(x, keyboard_v, previous, dt_s)
        else:
            j = [[0.0]*len(x) for _ in x]
            for col in range(len(x)):
                h = 1e-6
                a, b = x.copy(), x.copy()
                a[col] += h
                b[col] -= h
                ra, _ = self.evaluate(a, keyboard_v, previous, dt_s, jacobian=False)
                rb, _ = self.evaluate(b, keyboard_v, previous, dt_s, jacobian=False)
                for row in range(len(x)):
                    j[row][col] = (ra[row]-rb[row])/(2*h)
        return _solve_linear(j, [-v for v in r])

    def solve(self, seed, keyboard_v, previous=None, dt_s=None, *,
              use_fd=False, iterations=80, halvings=24):
        if type(iterations) is not int or iterations < 1 or type(halvings) is not int or halvings < 1:
            raise ValueError("positive integer offline budgets required")
        x = list(seed)
        for iteration in range(iterations):
            r, _ = self.evaluate(x, keyboard_v, previous, dt_s, jacobian=False)
            error = max(abs(v) for v in r)
            direction = self._direction(x, r, keyboard_v, previous, dt_s, use_fd)
            correction = max(abs(v) for v in direction)
            if error < KCL_A and correction < CORRECTION_V:
                values = dict(self.rails, KEYBOARD_TRIGGER=keyboard_v)
                values.update(zip(self.nodes, x))
                values.update({name: values[alias] for name, alias in self.alias.items()})
                state = State(values, {ref: values[a]-values[b] for ref, a, b, _ in self.caps})
                return state, dict(iterations=iteration, max_kcl_a=error,
                                   correction_v=correction, unknowns=len(x))
            for power in range(halvings):
                trial = [v+2.0**-power*dv for v, dv in zip(x, direction)]
                try:
                    rt, _ = self.evaluate(trial, keyboard_v, previous, dt_s, jacobian=False)
                    next_error = max(abs(v) for v in rt)
                    accepted = next_error < error
                    if error < KCL_A:
                        accepted = next_error < KCL_A and max(abs(v) for v in self._direction(
                            trial, rt, keyboard_v, previous, dt_s, use_fd)) < correction
                    if accepted:
                        x = trial
                        break
                except (ValueError, OverflowError):
                    continue
            else:
                raise ValueError("contour Newton line search exhausted")
        raise ValueError("contour Newton iteration budget exhausted")

    def initial_state(self, *, use_fd=False):
        if self.controls.external_s_short:
            raise ValueError("initialize with S-trigger open, then apply contact through step")
        # Numerical off seed, not a voltage trajectory or capacitor reset law.
        values = dict.fromkeys(self.nodes, 0.0)
        values.update(TRIGGER_COLLECTOR=9.0, Q12_BASE=.7, RESET_DRIVER=.05,
                      RESET_BASE=.7, RESET_COLLECTOR=8.7, ATTACK_GATE_LOWER=.05,
                      ATTACK_PNP_BASE=9.2, DECAY_DRIVER_EMITTER=8.0,
                      DECAY_SWITCH_BASE=1.3, SUSTAIN_DRIVER_EMITTER=.6,
                      SUSTAIN_COLLECTOR=.01, FOLLOWER_SUPPLY=9.3,
                      FOLLOWER_BASE=.1, FOLLOWER_MID=-.5, LOUDNESS_OUT=-1.0,
                      RESET_FEEDBACK=-3.6, RESET_DIODE_A=.9,
                      TIMING_C2=.7, DECAY_OUT=.7, FAST_DIODE_K=.05,
                      SUSTAIN_BASE=4.0, SUSTAIN_WIPER=5.0)
        seed = [values[name] for name in self.nodes]
        # Preset shunt parameters can change DC enormously; sustain is held in
        # reset by CR9, so no attack sequence is invented for preparation.
        return self.solve(seed, 0.0, use_fd=use_fd)

    def step(self, previous, keyboard_v, dt_s, *, use_fd=False, **budget):
        if any(not math.isfinite(v) for v in previous.node_v.values()):
            raise ValueError("finite previous node voltages required")
        try:
            seed = [previous.node_v[name] if name in previous.node_v else
                    previous.node_v["RESET_DRIVER"] if name == "FAST_DIODE_K" else
                    self._missing_previous_node(name) for name in self.nodes]
        except KeyError as exc:
            raise ValueError("complete previous node voltages required") from exc
        # CR10's algebraic cathode can jump with the imposed ideal source. This
        # finite numerical seed does not touch C7 or subdivide physical time.
        k = self.index[self.alias["KEY_DIODE_K"]]
        if keyboard_v-seed[k] > 1.0:
            seed[k] = keyboard_v-.3
        return self.solve(seed, keyboard_v,
                          previous, dt_s, use_fd=use_fd, **budget)

    @staticmethod
    def _missing_previous_node(name):
        raise ValueError(f"missing previous circuit node: {name}")

    def probe_step_roots(self, previous, keyboard_v, dt_s, *, use_fd=False):
        """Enumerate numerical roots; never select/publish a latch transition.

        Every candidate closes the same full KCL, dt and capacitor histories.
        More than one root is an unresolved switching/stability question.
        """
        if not math.isfinite(keyboard_v) or not 0 <= keyboard_v <= 10:
            raise ValueError("keyboard source outside 0..10 V")
        if not math.isfinite(dt_s) or dt_s <= 0:
            raise ValueError("positive finite transient interval required")
        roots, rejected = [], []

        def record(state, diagnostics, seed_policy):
            if all(max(abs(state.node_v[n]-r["state"].node_v[n]) for n in self.nodes)
                   >= 1e-8 for r in roots):
                roots.append(dict(state=state, diagnostics=diagnostics, seed_policy=seed_policy))

        try:
            state, diagnostics = self.step(previous, keyboard_v, dt_s, use_fd=use_fd)
            record(state, diagnostics, "previous")
        except ValueError as exc:
            rejected.append(dict(seed_policy="previous", error=str(exc)))
        for active in (False, True):
            for trigger_on in (False, True):
                values = dict(previous.node_v)
                values.setdefault("FAST_DIODE_K", values["RESET_DRIVER"])
                values.update(SET_BASE=.7 if active else .01,
                              RESET_BASE=.01 if active else .7,
                              RESET_COLLECTOR=.05 if active else 8.3,
                              ATTACK_GATE_LOWER=5.0 if active else .01,
                              ATTACK_PNP_BASE=8.6 if active else 9.15,
                              DECAY_DRIVER_EMITTER=-.6 if active else 7.6,
                              DECAY_SWITCH_BASE=-.6 if active else
                              min(7.6, previous.node_v["SUSTAIN_DRIVER_EMITTER"]+.7),
                              Q12_BASE=.01 if trigger_on else .7,
                              RESET_DRIVER=9.0 if trigger_on else .03,
                              TRIGGER_COLLECTOR=.05 if trigger_on else 6.0,
                              Q20_BASE=.7 if trigger_on else .01,
                              RESET_DIODE_A=.05 if trigger_on else 1.1)
                values["KEY_DIODE_K"] = max(values["KEY_DIODE_K"], keyboard_v-.3)
                try:
                    state, diagnostics = self.solve([values[name] for name in self.nodes],
                        keyboard_v, previous, dt_s, use_fd=use_fd)
                    record(state, diagnostics, f"latch_{int(active)}_trigger_{int(trigger_on)}")
                except ValueError as exc:
                    rejected.append(dict(seed_policy=f"latch_{int(active)}_trigger_{int(trigger_on)}",
                                         error=str(exc)))
        return dict(roots=roots, rejected=rejected, selected=None)


if __name__ == "__main__":
    network = Network()
    state, diagnostics = network.initial_state()
    print(json.dumps(dict(node_v=state.node_v, capacitor_v=state.capacitor_v,
                          diagnostics=diagnostics), indent=2))
