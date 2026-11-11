//! Conditional depletion charge, NG-46 pp.138-145/152-154. SI units.
//! Fixed previous junction voltage during Newton; no state publication.
#[derive(Clone, Copy, Debug)]
pub struct Parameters {
    pub zero_bias_capacitance_f: f64,
    pub potential_v: f64,
    pub grading: f64,
    pub forward_fraction: f64,
}

#[derive(Clone, Copy, Debug)]
pub struct Charge {
    pub charge_c: f64,
    pub capacitance_f: f64,
}

#[derive(Clone, Copy, Debug)]
pub struct Companion {
    pub next_charge_c: f64,
    pub capacitance_f: f64,
    pub delta_charge_c: f64,
    pub current_a: f64,
    pub conductance_s: f64,
}

/// Fixed beginning of the depletion-charge integral for a series of trials.
pub struct PreparedIncrement {
    parameters: Parameters,
    from_v: f64,
    previous: Charge,
    low_factor: Option<f64>,
}

impl PreparedIncrement {
    pub fn previous_capacitance_f(&self) -> f64 {
        self.previous.capacitance_f
    }

    /// Return (signed charge increment in C, endpoint capacitance in F).
    pub fn evaluate(&self, to_v: f64) -> Result<(f64, f64), Error> {
        let p = self.parameters;
        if let Some(previous_factor) = self.low_factor.filter(|_| to_v < p.splice_voltage()) {
            p.validate(to_v)?;
            let log = p.low_log(to_v);
            let next = p.low_point(log)?;
            let delta = if to_v > self.from_v {
                p.low_increment_with_factor(self.from_v, to_v, previous_factor)
            } else if to_v < self.from_v {
                -p.low_increment_with_factor(to_v, self.from_v, p.low_factor(log))
            } else {
                0.0
            };
            if !delta.is_finite() {
                return Err(Error::NonFiniteResult);
            }
            return Ok((delta, next.capacitance_f));
        }
        Ok((p.charge_increment(self.from_v, to_v)?, p.charge(to_v)?.capacitance_f))
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Error { InvalidInput, NonFiniteResult }

impl Parameters {
    fn validate(self, v: f64) -> Result<(), Error> {
        if !v.is_finite() || !(-40.0..=40.0).contains(&v)
            || !self.zero_bias_capacitance_f.is_finite() || self.zero_bias_capacitance_f < 0.0
            || !self.potential_v.is_finite() || self.potential_v <= 0.0
            || !self.grading.is_finite() || !(0.0..1.0).contains(&self.grading)
            || !self.forward_fraction.is_finite() || !(0.0..=0.95).contains(&self.forward_fraction)
        { return Err(Error::InvalidInput); }
        Ok(())
    }

    fn splice_voltage(self) -> f64 {
        self.forward_fraction * self.potential_v
    }

    fn splice(self) -> (f64, f64, f64) {
        let v = self.splice_voltage();
        let c = self.zero_bias_capacitance_f*(1.0-self.forward_fraction).powf(-self.grading);
        let slope = c*self.grading/(self.potential_v*(1.0-self.forward_fraction));
        (v, c, slope)
    }

    fn low_log(self, v: f64) -> f64 {
        (-v / self.potential_v).ln_1p()
    }

    fn low_charge(self, log: f64) -> f64 {
        let exponent = 1.0-self.grading;
        -self.zero_bias_capacitance_f*self.potential_v/exponent
            * (exponent * log).exp_m1()
    }

    fn low_point(self, log: f64) -> Result<Charge, Error> {
        let result = Charge {
            charge_c: self.low_charge(log),
            capacitance_f: self.zero_bias_capacitance_f * (-self.grading * log).exp(),
        };
        if !result.charge_c.is_finite() || !result.capacitance_f.is_finite() {
            return Err(Error::NonFiniteResult);
        }
        Ok(result)
    }

    pub fn charge(self, v: f64) -> Result<Charge, Error> {
        self.validate(v)?;
        if self.zero_bias_capacitance_f == 0.0 {
            return Ok(Charge { charge_c: 0.0, capacitance_f: 0.0 });
        }
        if v < self.splice_voltage() {
            return self.low_point(self.low_log(v));
        }
        let (vf, cf, slope) = self.splice();
        let delta = v-vf;
        let result = Charge { charge_c: self.low_charge(self.low_log(vf))+delta*(cf+0.5*slope*delta),
                              capacitance_f: cf+slope*delta };
        if !result.charge_c.is_finite() || !result.capacitance_f.is_finite() {
            return Err(Error::NonFiniteResult);
        }
        Ok(result)
    }

    fn low_factor(self, log: f64) -> f64 {
        ((1.0 - self.grading) * log).exp()
    }

    fn low_increment_with_factor(self, from: f64, to: f64, factor: f64) -> f64 {
        let exponent = 1.0-self.grading;
        let relative = (-(to-from)/(self.potential_v-from)).ln_1p();
        -self.zero_bias_capacitance_f*self.potential_v/exponent
            * factor * (exponent*relative).exp_m1()
    }

    fn low_increment(self, from: f64, to: f64) -> f64 {
        self.low_increment_with_factor(from, to, self.low_factor(self.low_log(from)))
    }

    fn high_increment(self, from: f64, to: f64) -> f64 {
        let (vf, cf, slope) = self.splice();
        (to-from)*(cf+slope*(from-vf)+0.5*slope*(to-from))
    }

    /// Exact piecewise integral of C(v), evaluated without Q(to)-Q(from).
    pub fn charge_increment(self, from: f64, to: f64) -> Result<f64, Error> {
        self.validate(from)?; self.validate(to)?;
        // Also validate the charge domain and derived coefficients.
        self.charge(from)?; self.charge(to)?;
        if from == to || self.zero_bias_capacitance_f == 0.0 { return Ok(0.0); }
        let (lo, hi, sign) = if to > from { (from, to, 1.0) } else { (to, from, -1.0) };
        let (vf, _, _) = self.splice();
        let value = sign*if hi <= vf { self.low_increment(lo, hi) }
            else if lo >= vf { self.high_increment(lo, hi) }
            else { self.low_increment(lo, vf)+self.high_increment(vf, hi) };
        if !value.is_finite() { return Err(Error::NonFiniteResult); }
        Ok(value)
    }

    pub fn prepare_increment(self, from_v: f64) -> Result<PreparedIncrement, Error> {
        self.validate(from_v)?;
        let (previous, low_factor) =
            if self.zero_bias_capacitance_f != 0.0 && from_v < self.splice_voltage() {
                let log = self.low_log(from_v);
                (self.low_point(log)?, Some(self.low_factor(log)))
            } else {
                (self.charge(from_v)?, None)
            };
        Ok(PreparedIncrement { parameters: self, from_v, previous, low_factor })
    }

    /// Current enters the anode. The caller retains the same previous_v
    /// for all trials and confirms its node/charge state only after convergence.
    pub fn companion(self, v: f64, previous_v: f64, dt_s: f64) -> Result<Companion, Error> {
        if !dt_s.is_finite() || dt_s <= 0.0 { return Err(Error::InvalidInput); }
        let q = self.charge(v)?;
        let delta = self.charge_increment(previous_v, v)?;
        let current = delta/dt_s; let conductance = q.capacitance_f/dt_s;
        if !current.is_finite() || !conductance.is_finite() { return Err(Error::NonFiniteResult); }
        Ok(Companion { next_charge_c: q.charge_c, capacitance_f: q.capacitance_f,
            delta_charge_c: delta, current_a: current, conductance_s: conductance })
    }
}
