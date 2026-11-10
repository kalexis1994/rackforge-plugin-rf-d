//! Radau response on capacitor voltages with bias-scaled junction currents.
use super::{chain, local, voltage, A, B, LOAD, PAIR, R59, R60, SIZE};
use crate::{
    family::Family,
    radau_devices as devices,
    reduced_lu::{dot, maximum, Lu},
    StepError,
};

const CAP_COUNT: usize = 17;
const LAWS: usize = devices::D.len();
const AFFINE: usize = CAP_COUNT + 5;
const DEFECT: usize = 2 * (LAWS + 1);

pub(super) struct Map {
    anchor: chain::State,
    wires: [f64; 2],
    bus_current: f64,
    bus_slope: f64,
    bias: [f64; LAWS],
    affine: [[f64; AFFINE]; PAIR],
    defect: [[f64; DEFECT]; PAIR],
}

fn capacitors() -> [(usize, usize, f64); CAP_COUNT] {
    let mut caps = [(chain::C10_LEFT, 7, 10e-6); CAP_COUNT];
    caps[..CAP_COUNT - 1].copy_from_slice(&chain::CAPACITORS);
    caps
}

fn pair_value(v: &[f64; chain::N], k: usize) -> f64 {
    v.get(k).copied().unwrap_or(0.)
}

fn remainder(z: f64) -> f64 {
    if z.abs() < 1e-4 {
        z * z * (0.5 + z * (1. / 6. + z * (1. / 24. + z * (1. / 120. + z / 720.))))
    } else {
        z.exp_m1() - z
    }
}

impl Map {
    pub(super) fn new(
        anchor: chain::State,
        wires: [f64; 2],
        panel: [f64; 2],
        params: chain::Parameters,
        stamp: &chain::Parts,
        lu: &Lu<PAIR>,
        h: f64,
    ) -> Result<Self, StepError> {
        let lower = params
            .boundary
            .recovery
            .vca
            .second
            .output
            .output
            .r21_lower_ohm;
        let series = params.boundary.r14_ohm.ok_or(StepError::InvalidInput)?
            + (1330. - params.circuit.r30_ohm);
        if series <= 0. {
            return Err(StepError::InvalidInput);
        }
        let row = |k| {
            if k == 49 && lower == 0. {
                chain::N
            } else if k == 49 && lower == 5000. {
                48
            } else {
                k
            }
        };
        let caps = capacitors();
        let mut charge = [[0.; CAP_COUNT]; chain::N];
        let mut mass = [[0.; chain::N]; chain::N];
        for (i, (a, b, c)) in caps.into_iter().enumerate() {
            let y = c / h;
            for (r, sign) in [(row(a), 1.), (row(b), -1.)] {
                if r < chain::N {
                    charge[r][i] += sign * y;
                    mass[r][a] += sign * y;
                    if b < chain::N {
                        mass[r][b] -= sign * y;
                    }
                }
            }
        }
        if mass.iter().zip(&stamp.mass_over_h).any(|(a, b)| a != b) {
            return Err(StepError::InvalidInput);
        }
        let mut constant = stamp.dc;
        constant[chain::BUS] += panel[0];
        for (i, resistance) in [R59, R60].into_iter().enumerate() {
            constant[LOAD[i]] +=
                ((anchor.high[LOAD[i]] - wires[i]) + anchor.low[LOAD[i]]) / resistance;
        }
        let bias = devices::S.map(|(a, b, scale, fixed)| {
            let values = |k| if k < chain::N { voltage(anchor, k) } else { 0. };
            scale * (values(a) - values(b)) + fixed
        });
        let current = std::array::from_fn::<_, LAWS, _>(|i| devices::IS[i] * bias[i].exp());
        let mut affine = [[0.; AFFINE]; PAIR];
        for column in 0..AFFINE {
            let rhs = std::array::from_fn(|r| {
                let i = r / SIZE;
                let node = local(r % SIZE);
                if column < CAP_COUNT {
                    (B[i][0] + B[i][1]) * charge[node][column]
                } else if column == CAP_COUNT {
                    -constant[node]
                } else {
                    let input = column - CAP_COUNT - 1;
                    if input / 2 == i && LOAD[input % 2] == node {
                        1. / [R59, R60][input % 2]
                    } else {
                        0.
                    }
                }
            });
            let value = lu.solve(rhs)?;
            for (row, entry) in affine.iter_mut().zip(value) {
                row[column] = entry;
            }
        }
        let mut defect = [[0.; DEFECT]; PAIR];
        for column in 0..DEFECT {
            let stage = column / (LAWS + 1);
            let branch = column % (LAWS + 1);
            let rhs = std::array::from_fn(|r| {
                if r / SIZE != stage {
                    return 0.;
                }
                let node = local(r % SIZE);
                if branch == LAWS {
                    if node == chain::BUS {
                        -1.
                    } else {
                        0.
                    }
                } else {
                    -devices::D[branch][r % SIZE] * current[branch]
                }
            });
            let value = lu.solve(rhs)?;
            for (row, entry) in defect.iter_mut().zip(value) {
                row[column] = entry;
            }
        }
        Ok(Self {
            anchor,
            wires,
            bus_current: panel[0],
            bus_slope: panel[1],
            bias,
            affine,
            defect,
        })
    }

    #[cfg(pilot_audio_readout)]
    pub(super) fn load_response(&self) -> [[f64; 4]; 4] {
        std::array::from_fn(|row| {
            let output = row / 2 * SIZE + LOAD[row % 2];
            std::array::from_fn(|column| self.affine[output][CAP_COUNT + 1 + column])
        })
    }

    pub(super) fn step(
        &self,
        old: chain::State,
        input: [[f64; 2]; 2],
        family: &Family,
        phase: f64,
        h: f64,
        seed: [chain::State; 2],
    ) -> Result<([chain::State; 2], f64, [chain::State; 2], usize, bool), StepError> {
        let old_offset = old.difference(self.anchor);
        let mut x = seed.map(|delta| {
            old.advanced(delta.high)
                .advanced(delta.low)
                .difference(self.anchor)
        });
        let state = std::array::from_fn(|i| match i {
            0..CAP_COUNT => {
                let (a, b, _) = capacitors()[i];
                old_offset[a] - pair_value(&old_offset, b)
            }
            CAP_COUNT => 1.,
            _ => {
                let i = i - CAP_COUNT - 1;
                input[i / 2][i % 2] - self.wires[i % 2]
            }
        });
        let linear = self.affine.each_ref().map(|row| dot(row, &state));
        let budget = 12;
        for iteration in 1..=budget {
            let bus = x.map(|row| voltage(self.anchor, chain::BUS) + row[chain::BUS]);
            let f = bus.map(|v| {
                family
                    .frequency(v)
                    .map(|p| p.0)
                    .map_err(|_| StepError::InvalidInput)
            });
            let [a, b] = f;
            let (a, b) = (a?, b?);
            let angles = A.map(|row| (phase + h * (row[0] * a + row[1] * b)).rem_euclid(1.));
            let mut correction = [0.; DEFECT];
            for i in 0..2 {
                for (j, (a, b, scale, _)) in devices::S.into_iter().enumerate() {
                    let z = scale * (pair_value(&x[i], a) - pair_value(&x[i], b));
                    if !z.is_finite() || self.bias[j] + z > 45. {
                        return Err(StepError::ExponentialDomain);
                    }
                    correction[i * (LAWS + 1) + j] = remainder(z);
                }
                let actual = family
                    .observe(bus[i], angles[i])
                    .map_err(|_| StepError::InvalidInput)?;
                correction[i * (LAWS + 1) + LAWS] =
                    (actual.currents_a[2] - self.bus_current) - self.bus_slope * x[i][chain::BUS];
            }
            let response = std::array::from_fn::<_, PAIR, _>(|r| {
                linear[r] + dot(&self.defect[r], &correction)
            });
            let error =
                std::array::from_fn::<_, PAIR, _>(|r| response[r] - x[r / SIZE][local(r % SIZE)]);
            for r in 0..PAIR {
                x[r / SIZE][local(r % SIZE)] = response[r];
            }
            let settled = iteration >= 2 && maximum(&error) <= 2e-12;
            if (settled || iteration == budget) && response.iter().all(|v| v.is_finite()) {
                let now = x.map(|v| self.anchor.advanced(v));
                return Ok((
                    now,
                    angles[1],
                    now.map(|v| chain::State::from_nodes(v.difference(old))),
                    iteration,
                    settled,
                ));
            }
        }
        Err(StepError::IterationBudget)
    }
}
