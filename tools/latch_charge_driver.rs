//! Compatible Ebers-Moll/depletion/low-injection charge for Q25/Q15.
//! Synthetic laboratory parameters; not an identified 2N3392.
use rf_d_circuit::StepError;
#[cfg(not(pilot_r59_prepared_terminal))]
use rf_d_circuit::junction_charge::Parameters as Depletion;
#[cfg(pilot_r59_prepared_terminal)]
#[path = "../crates/rf-d-circuit/src/junction_charge.rs"]
mod prepared_depletion;
#[cfg(pilot_r59_prepared_terminal)]
use prepared_depletion::Parameters as Depletion;
pub const VT:f64=1.380649e-23*298.15/1.602176634e-19;
pub const BE:Depletion=Depletion{zero_bias_capacitance_f:7e-12,potential_v:0.75,grading:0.5,forward_fraction:0.4};
pub const BC:Depletion=Depletion{zero_bias_capacitance_f:5e-12,potential_v:0.7,grading:0.33,forward_fraction:0.4};
// Return Q increment and dQ/dV, keeping high/low histories distinct.
pub fn junction(law:Depletion,t:f64,old:(f64,f64),now:(f64,f64))->Result<(f64,f64),StepError>{
 let (a,al)=old;let(b,bl)=now;
 if a/VT>45.||b/VT>45.||![al,bl,t].iter().all(|v|v.is_finite())||t<0. {return Err(StepError::ExponentialDomain);}
 let ca=law.charge(a).map_err(|_|StepError::ExponentialDomain)?.capacitance_f+t*1e-14*(a/VT).exp()/VT;
 let cb=law.charge(b).map_err(|_|StepError::ExponentialDomain)?.capacitance_f+t*1e-14*(b/VT).exp()/VT;
 let dq=law.charge_increment(a,b).map_err(|_|StepError::ExponentialDomain)?+t*1e-14*(a/VT).exp()*((b-a)/VT).exp_m1()+cb*bl-ca*al;
 if !dq.is_finite()||!cb.is_finite(){return Err(StepError::ExponentialDomain);}Ok((dq,cb))
}
pub fn terminal(old:[(f64,f64);2],now:[(f64,f64);2])->Result<([f64;2],[[f64;2];2]),StepError>{
 let bc_old=difference(old[0],old[1]);
 let bc_now=difference(now[0],now[1]);
 let(qbe,cbe)=junction(BE,1e-9,old[0],now[0])?;
 let(qbc,cbc)=junction(BC,3e-9,bc_old,bc_now)?;
 Ok(terminal_stamp((qbe,cbe),(qbc,cbc)))
}

fn difference(a: (f64, f64), b: (f64, f64)) -> (f64, f64) {
    let h = a.0 - b.0;
    let v = h - a.0;
    let e = (a.0 - (h - v)) + (-b.0 - v);
    (h, e + a.1 - b.1)
}

fn terminal_stamp(
    (qbe, cbe): (f64, f64),
    (qbc, cbc): (f64, f64),
) -> ([f64; 2], [[f64; 2]; 2]) {
    ([qbe + qbc, -qbc], [[cbe + cbc, -cbc], [-cbc, cbc]])
}

#[cfg(pilot_r59_prepared_terminal)]
struct PreparedJunction {
    previous: (f64, f64),
    diffusion: f64,
    previous_diffusion: f64,
    previous_capacitance: f64,
    depletion: prepared_depletion::PreparedIncrement,
}

#[cfg(pilot_r59_prepared_terminal)]
impl PreparedJunction {
    fn new(law: Depletion, t: f64, (a, al): (f64, f64)) -> Result<Self, StepError> {
        if a / VT > 45. || !al.is_finite() {
            return Err(StepError::ExponentialDomain);
        }
        let depletion = law.prepare_increment(a).map_err(|_| StepError::ExponentialDomain)?;
        let diffusion = t * 1e-14;
        let previous_diffusion = diffusion * (a / VT).exp();
        let previous_capacitance = depletion.previous_capacitance_f() + previous_diffusion / VT;
        Ok(Self { previous: (a, al), diffusion, previous_diffusion, previous_capacitance, depletion })
    }

    fn evaluate(&self, (b, bl): (f64, f64)) -> Result<(f64, f64), StepError> {
        if b / VT > 45. || !bl.is_finite() {
            return Err(StepError::ExponentialDomain);
        }
        let (increment, capacitance) = self.depletion.evaluate(b)
            .map_err(|_| StepError::ExponentialDomain)?;
        let cb = capacitance + self.diffusion * (b / VT).exp() / VT;
        let dq = increment + self.previous_diffusion * ((b - self.previous.0) / VT).exp_m1()
            + cb * bl - self.previous_capacitance * self.previous.1;
        if !dq.is_finite() || !cb.is_finite() {
            return Err(StepError::ExponentialDomain);
        }
        Ok((dq, cb))
    }
}

#[cfg(pilot_r59_prepared_terminal)]
pub(crate) struct PreparedTerminal {
    be: PreparedJunction,
    bc: PreparedJunction,
}

#[cfg(pilot_r59_prepared_terminal)]
impl PreparedTerminal {
    pub(crate) fn new(old: [(f64, f64); 2]) -> Result<Self, StepError> {
        Ok(Self {
            be: PreparedJunction::new(BE, 1e-9, old[0])?,
            bc: PreparedJunction::new(BC, 3e-9, difference(old[0], old[1]))?,
        })
    }

    pub(crate) fn evaluate(&self, now: [(f64, f64); 2]) -> Result<([f64; 2], [[f64; 2]; 2]), StepError> {
        Ok(terminal_stamp(self.be.evaluate(now[0])?, self.bc.evaluate(difference(now[0], now[1]))?))
    }
}

#[cfg(all(test, pilot_r59_prepared_terminal))]
mod tests {
    use super::*;

    #[test]
    fn prepared_terminal_preserves_bits() {
        let v = [-10., -0.35, 0., 0.4 * BC.potential_v, 0.4 * BE.potential_v, 0.71];
        for from in v {
            let old = [(from, 1e-18), (0., -2e-18)];
            let prepared = PreparedTerminal::new(old).unwrap();
            for to in v {
                let now = [(to, 3e-18), (0., -4e-18)];
                let (increment, mass) = prepared.evaluate(now).unwrap();
                let (expected_increment, expected_mass) = terminal(old, now).unwrap();
                assert_eq!(increment.map(f64::to_bits), expected_increment.map(f64::to_bits));
                assert_eq!(mass.map(|row| row.map(f64::to_bits)),
                           expected_mass.map(|row| row.map(f64::to_bits)));
            }
            assert!(prepared.evaluate([(f64::NAN, 0.), (0., 0.)]).is_err());
        }
        assert!(PreparedTerminal::new([(0., f64::NAN), (0., 0.)]).is_err());
    }
}
