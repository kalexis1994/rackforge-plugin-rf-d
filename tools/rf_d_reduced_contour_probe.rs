use crate::{family::Family, graph, original_graph, parameters, voice};
use voice::{Controls, Parameters, State, BUS, N};
use std::{error::Error, fs, io::{BufWriter, Read, Write}};

#[path = "PORTS_PATH"]
mod ports;

const INPUT: usize = 2 * N + 2;

fn read(raw: &[u8], k: usize) -> f64 {
    f64::from_le_bytes(raw[8 * k..8 * (k + 1)].try_into().unwrap())
}

fn write(out: &mut impl Write, values: impl IntoIterator<Item = f64>) -> std::io::Result<()> {
    for value in values {
        out.write_all(&value.to_le_bytes())?;
    }
    Ok(())
}

pub fn stamps(path: &str) -> Result<(), Box<dyn Error>> {
    let raw = fs::read(path)?;
    assert!(raw.len() % (8 * INPUT) == 0);
    let p = Parameters::new(parameters()).map_err(|error| format!("{error:?}"))?;
    let reference = original_graph::Parameters::new(parameters()).map_err(|error| format!("{error:?}"))?;
    let family = Family::prepare(-1.6).unwrap();
    let mut out = BufWriter::new(std::io::stdout().lock());
    for item in raw.chunks_exact(8 * INPUT) {
        let state = State {
            high: std::array::from_fn(|k| read(item, k)),
            low: std::array::from_fn(|k| read(item, N + k)),
            optional: false,
        };
        let phase = read(item, 2 * N);
        let c = Controls { key: read(item, 2 * N + 1), short: false, optional: false };
        graph::export_split(p, state, c, &mut out).map_err(|error| format!("{error:?}"))?;
        let mut union = original_graph::dc(reference, original_graph::State { high: state.high, low: state.low, optional: state.optional }, original_graph::Controls { key: c.key, short: c.short, optional: c.optional }).map_err(|error| format!("{error:?}"))?;
        let bus = state.high[BUS] + state.low[BUS];
        let port = family.observe(bus, phase).unwrap();
        union.dc[BUS] += port.currents_a[2];
        union.tangent.add(BUS, BUS, port.bus_dbus, 0.).map_err(|error| format!("{error:?}"))?;
        let (g, c) = union.tangent.dense();
        write(&mut out, union.dc)?;
        write(&mut out, g.into_iter().flatten())?;
        write(&mut out, c.into_iter().flatten().map(|value| value * 1e-6))?;
        write(&mut out, [port.currents_a[2], port.bus_dbus, port.bus_dphase, port.frequency_hz, port.frequency_dbus])?;
    }
    out.flush()?;
    Ok(())
}

pub fn close(path: &str) -> Result<(), Box<dyn Error>> {
    use ports::{Error, Reaction};
    let zero = Reaction { jacobian: [[0.; 4]; 4], current_a: [0.; 4] };
    assert_eq!(ports::close(zero, zero), Err(Error::Singular));
    let identity = Reaction { jacobian: std::array::from_fn(|i| std::array::from_fn(|j| u8::from(i == j) as f64)),
                              current_a: [1., -2., 3., -4.] };
    assert_eq!(ports::close(identity, zero), Ok([-1., 2., -3., 4.]));
    let raw = fs::read(path)?;
    assert!(raw.len() % (40 * 8) == 0);
    let mut out = BufWriter::new(std::io::stdout().lock());
    for row in raw.chunks_exact(40 * 8) {
        let reaction = |offset| Reaction {
            jacobian: std::array::from_fn(|i| std::array::from_fn(|j| read(row, offset + 4 * i + j))),
            current_a: std::array::from_fn(|i| read(row, offset + 16 + i)),
        };
        write(&mut out, ports::close(reaction(0), reaction(20)).map_err(|error| format!("{error:?}"))?)?;
    }
    out.flush()?;
    Ok(())
}

pub fn contour_stages() -> Result<(), Box<dyn Error>> {
    const LEN: usize = 56;
    const VALUES: usize = 4 * LEN + 5;
    const A: [[f64; 2]; 2] = [[5. / 12., -1. / 12.], [3. / 4., 1. / 4.]];
    let family = Family::prepare(-1.6).unwrap();
    let mut input = std::io::stdin().lock();
    let mut output = BufWriter::new(std::io::stdout().lock());
    let mut request = [0; 8 * VALUES];
    loop {
        if input.read(&mut request[..1])? == 0 {
            return Ok(());
        }
        input.read_exact(&mut request[1..])?;
        let state = State {
            high: std::array::from_fn(|k| if k < LEN { read(&request, k) } else { 0. }),
            low: std::array::from_fn(|k| if k < LEN { read(&request, LEN + k) } else { 0. }),
            optional: false,
        };
        let key = read(&request, 4 * LEN);
        let h = read(&request, 4 * LEN + 1);
        let mut reply = Vec::with_capacity((2 * (2 * LEN + 2 * LEN * LEN) + 7) * 8);
        let result = (0..2).try_for_each(|stage| {
            let delta = State::new(std::array::from_fn(|k| {
                if k < LEN { read(&request, (2 + stage) * LEN + k) } else { 0. }
            }), false);
            graph::export_contour_stage(state, delta, key, h, &mut reply)
        });
        let result = result.and_then(|()| {
            let phase = read(&request, 4 * LEN + 2);
            let bus: [f64; 2] = std::array::from_fn(|j| read(&request, 4 * LEN + 3 + j));
            let frequency = bus.map(|v| family.frequency(v));
            let rates = frequency.map(|v| v.map_err(|_| "frequency domain"));
            let [first, second] = rates;
            let rate = [first?, second?];
            let angle = A.map(|a| (phase + h * (a[0] * rate[0].0 + a[1] * rate[1].0)).rem_euclid(1.));
            let ports = [family.observe(bus[0], angle[0]).map_err(|_| "panel domain")?,
                         family.observe(bus[1], angle[1]).map_err(|_| "panel domain")?];
            write(&mut reply, ports.each_ref().map(|p| p.currents_a[2]))?;
            for i in 0..2 {
                let row: [f64; 2] = std::array::from_fn(|j| {
                    let dc = if i == j { ports[i].bus_dbus } else { 0. };
                    dc + ports[i].bus_dphase * A[i][j] * h * rate[j].1
                });
                write(&mut reply, row)?;
            }
            write(&mut reply, [angle[1]])?;
            Ok(())
        });
        match result {
            Ok(()) => {
                output.write_all(&[0])?;
                output.write_all(&reply)?;
            }
            Err(_) => output.write_all(&[1])?,
        }
        output.flush()?;
    }
}
