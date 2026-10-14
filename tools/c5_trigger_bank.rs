pub use rf_d_circuit::{junction_charge, StepError};
#[path = "../crates/rf-d-circuit/src/dual_contour.rs"]
mod circuit;
use circuit::*;
use std::{
    fs,
    io::{BufWriter, Write},
    time::Instant,
};
const TICK: f64 = 1e-6 / 1073741824.;
fn state(w: &mut impl Write, s: State) {
    for x in s.high.into_iter().chain(s.low) {
        write!(w, ",{x:.17e}").unwrap();
    }
}
fn values(w: &mut impl Write, x: impl IntoIterator<Item = f64>) {
    for x in x {
        write!(w, ",{x:.17e}").unwrap();
    }
}
fn root(w: &mut impl Write, old: State, pair: &Pair, c: Controls, h: f64, jac: bool) {
    write!(w, "ROOT,{:.17e},{},{}", h, c.key, c.short as u8).unwrap();
    state(w, old);
    for s in pair.delta.into_iter().chain(pair.stages) {
        state(w, s);
    }
    values(w, [pair.residual_a, pair.correction_v]);
    writeln!(w).unwrap();
    if jac {
        for stage in pair.delta {
            let p = parts(old, stage, c, h).unwrap();
            write!(w, "STAMP").unwrap();
            values(w, p.j.into_iter().flatten());
            values(w, p.mass.into_iter().flatten());
            writeln!(w).unwrap();
        }
    }
}
#[derive(Clone, Copy, Default)]
struct Sum {
    hi: f64,
    lo: f64,
}
impl Sum {
    fn add(&mut self, v: f64) {
        let y = v - self.lo;
        let t = self.hi + y;
        self.lo = (t - self.hi) - y;
        self.hi = t;
    }
}
fn bits(s: State) -> Vec<u64> {
    s.high
        .into_iter()
        .chain(s.low)
        .map(f64::to_bits)
        .chain([s.optional as u64])
        .collect()
}
fn run() -> Result<(), String> {
    let args: Vec<_> = std::env::args().collect();
    let raw = fs::read(&args[1]).map_err(|e| e.to_string())?;
    if raw.len() != 54 * 8 {
        return Err("seed format".into());
    }
    let seed =
        std::array::from_fn(|k| f64::from_le_bytes(raw[8 * k..8 * k + 8].try_into().unwrap()));
    let optional = args[2] == "1";
    let max_us = args[3].parse::<u64>().unwrap();
    let mode = &args[4];
    let max_ticks = max_us * 1073741824;
    let mut s = initial(seed, optional).map_err(|e| format!("DC:{e:?}"))?;
    let start = s;
    let mut w = BufWriter::new(std::io::stdout());
    let initial_dc = dc(
        s,
        Controls {
            optional,
            ..Controls::default()
        },
    )
    .unwrap();
    write!(w, "DC,{},{max_us},{mode}", optional as u8).unwrap();
    state(&mut w, s);
    values(&mut w, initial_dc.dc);
    values(&mut w, initial_dc.ports);
    values(&mut w, initial_dc.j.into_iter().flatten());
    writeln!(w).unwrap();
    let mut elapsed = 0_u64;
    let mut next = max_ticks;
    let (mut steps, mut replays, mut events, mut roots) = (0, 0, 0, 0);
    let mut totals = [Sum::default(); N];
    let mut charges = [Sum::default(); N];
    let mut terminals = [Sum::default(); P];
    let mut c = Controls {
        optional,
        ..Controls::default()
    };
    let mut last_latch = [s.high[26] > 4., s.high[40] > 4.];
    let begun = Instant::now();
    for cut in 1..=144_u64 {
        let target = cut * 250 * 1073741824;
        while elapsed < target {
            if begun.elapsed().as_secs_f64() > 300. {
                state(&mut w, s);
                w.flush().unwrap();
                return Err("wall budget".into());
            }
            let us = elapsed / 1073741824;
            let on = (1000..10000).contains(&us) || (20000..30000).contains(&us);
            let new = Controls {
                optional,
                key: if on && mode == "key" { 10. } else { 0. },
                short: on && mode == "s",
            };
            let changed = new != c;
            if changed {
                write!(w, "EVENT,{elapsed},{},{}", new.key, new.short as u8).unwrap();
                state(&mut w, s);
                writeln!(w).unwrap();
                c = new;
                next = max_ticks;
                events += 1;
            }
            let remain = target - elapsed;
            let bound = next.min(max_ticks).min(remain);
            let width = 1_u64 << (63 - bound.leading_zeros());
            if width < 2 {
                return Err("clock budget".into());
            }
            let old = s;
            let a = advance(&mut s, c, width as f64 * TICK)
                .map_err(|e| format!("advance:{elapsed}:{e:?}"))?;
            let accepted = (a.h / TICK).round() as u64;
            if accepted < 2 || accepted > width || accepted % 2 != 0 {
                return Err("nonintegral clock".into());
            }
            let switched = [s.high[26] > 4., s.high[40] > 4.] != last_latch;
            let selected =
                steps == 0 || changed || switched || elapsed + accepted == target && cut % 36 == 0;
            if selected {
                let mut replay = old;
                let b = advance(&mut replay, c, width as f64 * TICK).unwrap();
                if bits(replay) != bits(s)
                    || a.h.to_bits() != b.h.to_bits()
                    || a.error.to_bits() != b.error.to_bits()
                {
                    return Err("replay".into());
                }
                for (pa, pb) in a
                    .fine
                    .iter()
                    .chain([&a.coarse])
                    .zip(b.fine.iter().chain([&b.coarse]))
                {
                    for (x, y) in pa
                        .delta
                        .into_iter()
                        .chain(pa.stages)
                        .zip(pb.delta.into_iter().chain(pb.stages))
                    {
                        if bits(x) != bits(y) {
                            return Err("complete pair replay".into());
                        }
                    }
                }
                replays += 1;
                write!(w, "SELECT,{elapsed},{accepted}").unwrap();
                writeln!(w).unwrap();
                root(&mut w, old, &a.coarse, c, a.h, true);
                root(&mut w, old, &a.fine[0], c, a.h / 2., false);
                root(&mut w, a.fine[0].stages[1], &a.fine[1], c, a.h / 2., false);
                roots += 3;
            }
            for (old, pair) in [(old, &a.fine[0]), (a.fine[0].stages[1], &a.fine[1])] {
                let h = a.h / 2.;
                let p0 = parts(old, pair.delta[0], c, h).unwrap();
                let p1 = parts(old, pair.delta[1], c, h).unwrap();
                for k in 0..N {
                    totals[k].add(h * (0.75 * p0.dc[k] + 0.25 * p1.dc[k]));
                    charges[k].add(h * p1.dq[k]);
                }
                for k in 0..P {
                    terminals[k]
                        .add(h * (0.75 * p0.ports[k] + 0.25 * p1.ports[k] + p1.charge_ports[k]));
                }
            }
            write!(
                w,
                "ACCEPT,{elapsed},{accepted},{:.17e},{},{:.17e},{:.17e}",
                a.error, a.attempts, a.fine[0].residual_a, a.fine[1].residual_a
            )
            .unwrap();
            writeln!(w).unwrap();
            elapsed += accepted;
            steps += 1;
            next = if a.error < 0.0625 {
                accepted.saturating_mul(2).min(max_ticks)
            } else {
                accepted
            };
            last_latch = [s.high[26] > 4., s.high[40] > 4.];
        }
        write!(w, "GRID,{elapsed},{},{}", c.key, c.short as u8).unwrap();
        state(&mut w, s);
        values(&mut w, dc(s, c).unwrap().ports);
        writeln!(w).unwrap();
    }
    write!(w, "LEDGER").unwrap();
    values(&mut w, totals.map(|v| v.hi));
    values(&mut w, charges.map(|v| v.hi));
    values(&mut w, terminals.map(|v| v.hi));
    writeln!(w).unwrap();
    for invalid in 0..4 {
        let mut test = s;
        let saved = bits(test);
        let mut p = c;
        let mut h = 8e-6;
        match invalid {
            0 => p.optional = !p.optional,
            1 => h = 0.,
            2 => p.key = f64::NAN,
            _ => test.high[38] = f64::NAN,
        };
        let before = bits(test);
        assert!(advance(&mut test, p, h).is_err());
        assert_eq!(before, bits(test));
        if invalid < 3 {
            assert_eq!(saved, bits(test));
        }
    }
    write!(
        w,
        "FINAL,{steps},{replays},{events},{roots},4,{:.17e}",
        begun.elapsed().as_secs_f64()
    )
    .unwrap();
    state(&mut w, start);
    state(&mut w, s);
    writeln!(w).unwrap();
    w.flush().unwrap();
    Ok(())
}
fn main() {
    if let Err(e) = run() {
        eprintln!("FAILURE,{e}");
        std::process::exit(1);
    }
}
