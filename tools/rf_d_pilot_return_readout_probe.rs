//! Read the physical return currents at 96 kHz boundaries.
//! The CV return, VCA base and TAIL are imposed by the comparison bench.
pub use rf_d_circuit::StepError;
#[path = "rf_d_pilot_contour_ports.rs"]
mod contour_ports;
#[path = "latch_charge_driver.rs"]
mod latch_charge;
#[path = "rf_d_reduced_engine_lu.rs"]
mod reduced_lu;

use contour_ports::Returns;
use std::{
    error::Error,
    io::{Read, Write},
};

fn main() -> Result<(), Box<dyn Error>> {
    let mut raw = Vec::new();
    std::io::stdin().read_to_end(&mut raw)?;
    assert!(raw.len() >= 6 * 8 && (raw.len() - 6 * 8) % (6 * 8) == 0);
    let mut values = raw
        .chunks_exact(8)
        .map(|x| f64::from_le_bytes(x.try_into().unwrap()));
    let mut read = || std::array::from_fn::<_, 3, _>(|_| values.next().unwrap());
    let mut cells = Returns {
        volume: read(),
        filter: read(),
    };
    let mut out = std::io::BufWriter::new(std::io::stdout().lock());
    while let Some(c2) = values.next() {
        let [sum, collector_seed, cv, base, tail] = std::array::from_fn(|_| values.next().unwrap());
        let volume = contour_ports::volume(cells.volume, c2, [collector_seed, cv, base]);
        let filter = contour_ports::filter(cells.filter, [sum, tail]);
        cells = Returns {
            volume: volume.map_err(|e| format!("R59 volume cell: {e:?}"))?,
            filter: filter.map_err(|e| format!("R60 filter cell: {e:?}"))?,
        };
        for value in [cells.volume[2], cells.filter[2]]
            .into_iter()
            .chain(cells.currents(base, tail))
        {
            out.write_all(&value.to_le_bytes())?;
        }
    }
    out.flush()?;
    Ok(())
}
