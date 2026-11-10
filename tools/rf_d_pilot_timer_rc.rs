//! Two charge states of the loaded C2/C5 timing network, in volts.
pub const TIMER_NODES: [usize; 2] = [5, 38];
pub const LOAD_NODES: [[usize; 3]; 2] = [[8, 11, 0], [44, 47, 29]];
pub const CAPACITANCE_F: f64 = 10e-6;
pub const RESISTANCE_OHM: [[f64; 3]; 2] = [[1_000., 10_000., 10_000.], [100., 1_000., 10_000.]];

#[derive(Clone, Copy)]
pub struct Step {
    load_mix: [[f64; 3]; 2],
    moved: [f64; 2],
    start_weight: [f64; 2],
    end_weight: [f64; 2],
}

impl Step {
    /// Prepare for a known positive interval. Normal clock coefficients
    /// are reused. Only a step split at an event needs new coefficients.
    pub fn new(seconds: f64) -> Self {
        let g = RESISTANCE_OHM.map(|row| row.map(|r| r.recip()));
        let total = g.map(|row| row.into_iter().sum::<f64>());
        let load_mix = std::array::from_fn(|i| g[i].map(|v| v / total[i]));
        let x = total.map(|v| v * seconds / CAPACITANCE_F);
        let moved = x.map(|v| -(-v).exp_m1());
        let end_weight = x.map(|v| {
            // Taylor series of 1 - (1 - exp(-v)) / v near zero.
            if v < 1e-3 {
                v * (0.5 - v * (1. / 6. - v * (1. / 24. - v * (1. / 120. - v / 720.))))
            } else {
                1. + (-v).exp_m1() / v
            }
        });
        let start_weight = std::array::from_fn(|i| moved[i] - end_weight[i]);
        Self {
            load_mix,
            moved,
            start_weight,
            end_weight,
        }
    }

    /// Exact RC update for affine load voltages between the interval ends.
    pub fn advance(
        &self,
        capacitor_v: [f64; 2],
        start_v: [[f64; 3]; 2],
        end_v: [[f64; 3]; 2],
    ) -> [f64; 2] {
        std::array::from_fn(|i| {
            let v = capacitor_v[i];
            v + self.start_weight[i] * self.load_delta(i, v, start_v[i])
                + self.end_weight[i] * self.load_delta(i, v, end_v[i])
        })
    }

    /// Exact RC update for held or exponentially averaged load voltages.
    pub fn advance_held(&self, capacitor_v: [f64; 2], ports_v: [[f64; 3]; 2]) -> [f64; 2] {
        std::array::from_fn(|i| {
            let v = capacitor_v[i];
            v + self.moved[i] * self.load_delta(i, v, ports_v[i])
        })
    }

    fn load_delta(&self, i: usize, capacitor_v: f64, ports_v: [f64; 3]) -> f64 {
        self.load_mix[i]
            .into_iter()
            .zip(ports_v)
            .map(|(weight, port)| weight * (port - capacitor_v))
            .sum()
    }
}
