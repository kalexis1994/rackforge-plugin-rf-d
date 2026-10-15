//! Prepared audio graph, derived verbatim laws; HYBRID_STAMP_PROTOCOLO.
use rf_d_circuit::{cutoff_ladder_output,output_conversion::{Parameters as ConversionParameters},vca2_output::Parameters as Bjt,Parameters as HeadphoneParameters,SolverBudget,StepError,output::OutputBoundary};
pub use rf_d_circuit::cutoff_ladder_output::{Boundary,Parameters};
const N: usize = 66;
const K_B: f64 = 1.380_649e-23;
const Q_E: f64 = 1.602_176_634e-19;

const POSITION:[usize;N]={let mut a=[0;N];let mut i=0;while i<N{a[i]=i;i+=1;}a};
fn natural_jacobian(j:&[[f64;N];N])->[[f64;N];N]{*j}
#[derive(Clone, Copy)]
enum Terminal {
    Node(usize),
    Fixed(f64),
}
use Terminal::{Fixed, Node};

// Algebraically identical junction law. Near zero, retain expm1 to avoid
// cancellation. Away from zero one exp suffices; its derivative is never
// reconstructed from expm1 + 1 (which would erase weak reverse conductance).
fn junction_exp(exponent: f64) -> (f64, f64) {
    let exponential = exponent.exp();
    let excess = if cfg!(feature = "solver-dual-exp") || exponent.abs() < 0.5 {
        exponent.exp_m1()
    } else {
        exponential - 1.0
    };
    (excess, exponential)
}
impl Terminal {
    fn value(self, x: &[f64; N]) -> f64 {
        match self {
            Node(i) => x[i],
            Fixed(v) => v,
        }
    }
}

struct Stamp<'a,const FULL:bool> {
    x: &'a [f64; N],
    low: &'a [f64;N],
    r: [f64; N],
    j: [[f64; N]; N],
}
impl<'a,const FULL:bool> Stamp<'a,FULL> {
    fn low(&self,t:Terminal)->f64{match t{Node(k)=>self.low[k],Fixed(_)=>0.}}
    fn branch(&mut self, left: Terminal, right: Terminal, current: f64, g: f64) {
        let current=current+g*(self.low(left)-self.low(right));
        for (terminal, sign) in [(left, 1.0), (right, -1.0)] {
            if let Node(i) = terminal {
                self.r[i] += sign * current;
                if FULL {
                for (other, slope) in [(left, g), (right, -g)] {
                    if let Node(k) = other {
                        self.j[POSITION[i]][POSITION[k]] += sign * slope;
                    }
                }
                }
            }
        }
    }
    fn resistor(&mut self, left: Terminal, right: Terminal, ohm: f64) {
        let g = 1.0 / ohm;
        self.branch(
            left,
            right,
            (left.value(self.x) - right.value(self.x)) * g,
            g,
        );
    }
    fn capacitor(&mut self, left: Terminal, right: Terminal, farad: f64, old: f64, dt: f64) {
        let g = farad / dt;
        self.branch(
            left,
            right,
            g * (left.value(self.x) - right.value(self.x) - old),
            g,
        );
    }
    fn transistor(
        &mut self,
        base: Terminal,
        collector: Terminal,
        emitter: Terminal,
        polarity: f64,
        p: Bjt,
    ) -> Result<(), StepError> {
        let vt = K_B * p.temperature_k / Q_E;
        let be = polarity * (base.value(self.x) - emitter.value(self.x)) / vt;
        let bc = polarity * (base.value(self.x) - collector.value(self.x)) / vt;
        if !be.is_finite() || !bc.is_finite() || be.max(bc) > 45.0 {
            return Err(StepError::ExponentialDomain);
        }
        let (f_excess, f_exp) = junction_exp(be);
        let (r_excess, r_exp) = junction_exp(bc);
        let f = p.transistor_is_a * f_excess;
        let rev = p.transistor_is_a * r_excess;
        let gf = p.transistor_is_a * f_exp / vt;
        let gr = p.transistor_is_a * r_exp / vt;
        let ib = f / p.beta_forward + rev / p.beta_reverse;
        let ic = f - (1.0 + 1.0 / p.beta_reverse) * rev;
        let db = [
            gf / p.beta_forward + gr / p.beta_reverse,
            -gr / p.beta_reverse,
            -gf / p.beta_forward,
        ];
        let dc = [
            gf - (1.0 + 1.0 / p.beta_reverse) * gr,
            (1.0 + 1.0 / p.beta_reverse) * gr,
            -gf,
        ];
        let slopes = [db, dc, std::array::from_fn(|i| -db[i] - dc[i])];
        let terminals = [base, collector, emitter];
        for row in 0..3 {
            if let Node(i) = terminals[row] {
                self.r[i] += polarity * [ib, ic, -ib - ic][row];
                if FULL {
                for col in 0..3 {
                    if let Node(k) = terminals[col] {
                        self.j[POSITION[i]][POSITION[k]] += slopes[row][col];
                    }
                }
                }
                let mut v=0.;for col in 0..3{v+=slopes[row][col]*self.low(terminals[col]);}self.r[i]+=v;

            }
        }
        Ok(())
    }
    fn diode(
        &mut self,
        anode: Terminal,
        cathode: Terminal,
        is_a: f64,
        ideality: f64,
        temperature: f64,
    ) -> Result<(), StepError> {
        let nvt = ideality * K_B * temperature / Q_E;
        let exponent = (anode.value(self.x) - cathode.value(self.x)) / nvt;
        if !exponent.is_finite() || exponent > 45.0 {
            return Err(StepError::ExponentialDomain);
        }
        let (excess, exponential) = junction_exp(exponent);
        self.branch(anode, cathode, is_a * excess, is_a * exponential / nvt);
        Ok(())
    }
}

const R20_OHM: f64 = 5000.0;
const R57_OHM: f64 = 33000.0;
const R58_OHM: f64 = 1000.0;
#[derive(Clone, Copy)]
struct MainLoad {
    pub equivalent_ohm: f64,
    pub hi_to_pin21: f64,
    pub lo_to_hi: f64,
}

fn main_load(b: OutputBoundary) -> Result<MainLoad, StepError> {
    if !b.q17_collector_v.is_finite()
        || !b.r20_lower_ohm.is_finite()
        || b.r20_lower_ohm < 0.0
        || b.r20_lower_ohm > R20_OHM
        || !b.hi_load_ohm.is_finite()
        || b.hi_load_ohm <= 0.0
        || !b.lo_load_ohm.is_finite()
        || b.lo_load_ohm <= 0.0
        || !b.dt_s.is_finite()
        || b.dt_s <= 0.0
    {
        return Err(StepError::InvalidInput);
    }
    let upper = R20_OHM - b.r20_lower_ohm;
    if !b.sw18_on {
        return Ok(MainLoad {
            equivalent_ohm: upper,
            hi_to_pin21: 0.0,
            lo_to_hi: 0.0,
        });
    }
    let low_shunt = 1.0 / (1.0 / R58_OHM + 1.0 / b.lo_load_ohm);
    let low_leg = R57_OHM + low_shunt;
    let hi_shunt = 1.0 / (1.0 / b.hi_load_ohm + 1.0 / low_leg);
    // Exact lower-end short: HI and LO are grounded. At the upper end
    // upper=0 joins PIN21 to HI; R75 remains in series in every caller.
    // SW18 OFF at the upper end has equivalent=0 (PIN21 grounded), also
    // finite after adding R75. No epsilon resistor or zero-ohm division.
    let wiper_shunt = if b.r20_lower_ohm == 0.0 {
        0.0
    } else {
        1.0 / (1.0 / b.r20_lower_ohm + 1.0 / hi_shunt)
    };
    let equivalent = upper + wiper_shunt;
    if !equivalent.is_finite() || equivalent <= 0.0 {
        return Err(StepError::InvalidInput);
    }
    Ok(MainLoad {
        equivalent_ohm: equivalent,
        hi_to_pin21: wiper_shunt / equivalent,
        lo_to_hi: low_shunt / low_leg,
    })
}

fn valid_bjt(p: Bjt) -> bool {
    [
        p.transistor_is_a,
        p.beta_forward,
        p.beta_reverse,
        p.temperature_k,
    ]
    .iter()
    .all(|v| v.is_finite() && *v > 0.0)
}
fn prepare(
    p: Parameters,
    conversion: ConversionParameters,
    headphone: HeadphoneParameters,
    b: Boundary,
    budget: SolverBudget,
) -> Result<(rf_d_circuit::cutoff::PanelEquivalent, MainLoad), StepError> {
    let cb = Bjt {
        transistor_is_a: conversion.transistor_is_a,
        beta_forward: conversion.beta_forward,
        beta_reverse: conversion.beta_reverse,
        temperature_k: conversion.temperature_k,
    };
    let hb = Bjt {
        transistor_is_a: headphone.transistor_is_a,
        beta_forward: headphone.beta_forward,
        beta_reverse: headphone.beta_reverse,
        temperature_k: headphone.temperature_k,
    };
    let vb = b.recovery.vca;
    let sb = vb.second;
    let ob = sb.output.output;
    if ![p.ladder_transistor, p.cutoff.q26, p.cutoff.q28, cb, hb]
        .into_iter()
        .all(valid_bjt)
        || !matches!(p.r61_ohm, 200.0 | 200_000.0)
        || !p.r30_ohm.is_finite()
        || !(330.0..=1330.0).contains(&p.r30_ohm)
        || !b.range_fraction_from_ground.is_finite()
        || !(0.0..=1.0).contains(&b.range_fraction_from_ground)
        || b.r14_ohm
            .is_some_and(|v| !v.is_finite() || !(0.0..=50_000.0).contains(&v))
        || ![
            b.bus_v,
            vb.loudness_v,
            sb.q21_base_v,
            sb.minus_v,
            sb.output.plus_v,
        ]
        .iter()
        .all(|v| v.is_finite())
        || sb.output.plus_v <= sb.minus_v
        || !vb.first_balance_left_ohm.is_finite()
        || !(0.0..=25.0).contains(&vb.first_balance_left_ohm)
        || !sb.second_balance_left_ohm.is_finite()
        || !(0.0..=100.0).contains(&sb.second_balance_left_ohm)
        || !ob.r21_lower_ohm.is_finite()
        || !(0.0..=5000.0).contains(&ob.r21_lower_ohm)
        || ![headphone.diode_is_a, headphone.diode_ideality]
            .iter()
            .all(|v| v.is_finite() && *v > 0.0)
        || conversion.diode.is_some_and(|d| {
            !d.is_a.is_finite() || d.is_a <= 0.0 || !d.ideality.is_finite() || d.ideality <= 0.0
        })
        || ob.tip_load_ohm.is_some_and(|v| !v.is_finite() || v <= 0.0)
        || ob.ring_load_ohm.is_some_and(|v| !v.is_finite() || v <= 0.0)
        || !(1..=16).contains(&budget.iterations)
        || !(1..=16).contains(&budget.line_search_halvings)
    {
        return Err(StepError::InvalidInput);
    }
    Ok((rf_d_circuit::cutoff::reduce_panel(b.panel)?, main_load(ob)?))
}

#[inline(always)]
fn evaluate<const FULL:bool>(
    x: &[f64; N],
    low: &[f64;N],
    p: Parameters,
    conversion: ConversionParameters,
    headphone: HeadphoneParameters,
    b: Boundary,
    prepared: (rf_d_circuit::cutoff::PanelEquivalent, MainLoad),
) -> Result<([f64; N], [[f64; N]; N]), StepError> {
    let mut s = Stamp::<FULL> {
        x,low,
        r: [0.0; N],
        j: [[0.0; N]; N],
    };
    let vb = b.recovery.vca;
    let sb = vb.second;
    let plus = sb.output.plus_v;
    let minus = sb.minus_v;
    // Ladder DC belongs exclusively to the local reconstruction kernel.
    // Recovery Q8/Q6/Q7/Q5.
    for (node, fixed, ohm) in [
        (16, 0.0, 47000.0),
        (17, 0.0, 47000.0),
        (18, minus, 220000.0),
        (19, minus, 100000.0),
        (20, minus, 1000.0),
        (23, plus, 47.0),
    ] {
        s.resistor(Node(node), Fixed(fixed), ohm);
    }
    s.resistor(Node(21), Node(22), 1000.0);
    s.resistor(Node(22), Node(23), 180.0);
    for (base, collector, emitter) in [
        (16, Node(21), 18),
        (17, Fixed(plus), 19),
        (18, Node(21), 20),
        (19, Fixed(plus), 20),
    ] {
        s.transistor(
            Node(base),
            collector,
            Node(emitter),
            1.0,
            p.ladder_transistor,
        )?;
    }
    // First VCA, including the input and first balance.
    for (left, right, ohm) in [
        (21, 24, 82000.0),
        (25, 26, 820.0),
        (26, 33, 120.0),
        (27, 28, 1000.0),
        (30, 33, 100.0 + vb.first_balance_left_ohm),
        (31, 33, 125.0 - vb.first_balance_left_ohm),
    ] {
        s.resistor(Node(left), Node(right), ohm);
    }
    for (node, fixed, ohm) in [
        (26, 0.0, 510.0),
        (29, 0.0, 6800.0),
        (29, minus, 270000.0),
    ] {
        s.resistor(Node(node), Fixed(fixed), ohm);
    }
    for (base, collector, emitter) in [(25, 30, 27), (26, 31, 27), (32, 28, 29)] {
        s.transistor(
            Node(base),
            Node(collector),
            Node(emitter),
            1.0,
            p.ladder_transistor,
        )?;
    }
    // Second VCA and its supply through R13/R11.
    for (left, right, ohm) in [
        (34, 35, 470.0),
        (37, 39, 330.0 + sb.second_balance_left_ohm),
        (38, 39, 430.0 - sb.second_balance_left_ohm),
        (39, 33, 120.0),
    ] {
        s.resistor(Node(left), Node(right), ohm);
    }
    s.resistor(Node(36), Fixed(0.0), 3300.0);
    s.resistor(Node(36), Fixed(minus), 150000.0);
    s.transistor(Node(30), Node(37), Node(34), 1.0, p.ladder_transistor)?;
    s.transistor(Node(31), Node(38), Node(34), 1.0, p.ladder_transistor)?;
    s.transistor(
        Fixed(sb.q21_base_v),
        Node(35),
        Node(36),
        1.0,
        p.ladder_transistor,
    )?;
    // PNP conversion Q1/Q12/Q17.
    let cp = Bjt {
        transistor_is_a: conversion.transistor_is_a,
        beta_forward: conversion.beta_forward,
        beta_reverse: conversion.beta_reverse,
        temperature_k: conversion.temperature_k,
    };
    for (left, right, ohm) in [(40, 39, 150.0), (42, 43, 8.2), (42, 44, 8.2)] {
        s.resistor(Node(left), Node(right), ohm);
    }
    for (node, fixed, ohm) in [
        (40, plus, 120.0),
        (41, plus, 62.0),
        (45, 0.0, 680.0),
        (46, 0.0, 680.0),
    ] {
        s.resistor(Node(node), Fixed(fixed), ohm);
    }
    for (base, collector, emitter) in [(40, 42, 41), (37, 45, 43), (38, 46, 44)] {
        s.transistor(Node(base), Node(collector), Node(emitter), -1.0, cp)?;
    }
    if let Some(d) = conversion.diode {
        s.diode(Node(46), Fixed(plus), d.is_a, d.ideality, cp.temperature_k)?;
        s.diode(Fixed(0.0), Node(46), d.is_a, d.ideality, cp.temperature_k)?;
    } else if !(0.0..=plus).contains(&x[46]) {
        return Err(StepError::ExponentialDomain);
    }
    // Panel algebraic reduction, R77 and both R21 segments.
    let ob = sb.output.output;
    s.resistor(Node(47), Fixed(0.0), 1000.0 + prepared.1.equivalent_ohm);
    s.resistor(Node(47), Node(48), 1000.0);
    if ob.r21_lower_ohm < 5000.0 {
        s.resistor(Node(48), Node(49), 5000.0 - ob.r21_lower_ohm);
    }
    if ob.r21_lower_ohm > 0.0 {
        s.resistor(Node(49), Fixed(0.0), ob.r21_lower_ohm);
    }
    // Board 3 circuit 11, Fig.9-8. Separate device parameters and ±20 V supply.
    for (node, fixed, ohm) in [
        (50, -10.0, 6200.0),
        (50, 0.0, 24000.0),
        (55, -20.0, 10.0),
        (53, 0.0, 1200.0),
        (58, 0.0, 10.0),
        (61, 0.0, 390.0),
    ] {
        s.resistor(Node(node), Fixed(fixed), ohm);
    }
    for (left, right, ohm) in [
        (51, 54, 390.0),
        (56, 60, 4.7),
        (60, 59, 4.7),
        (53, 57, 390.0),
    ] {
        s.resistor(Node(left), Node(right), ohm);
    }
    for load in [ob.tip_load_ohm, ob.ring_load_ohm].into_iter().flatten() {
        s.resistor(Node(61), Fixed(0.0), load);
    }
    let hp = Bjt {
        transistor_is_a: headphone.transistor_is_a,
        beta_forward: headphone.beta_forward,
        beta_reverse: headphone.beta_reverse,
        temperature_k: headphone.temperature_k,
    };
    s.transistor(Node(50), Fixed(-20.0), Node(51), -1.0, hp)?;
    s.transistor(Node(54), Node(55), Node(56), -1.0, hp)?;
    s.transistor(Node(57), Node(58), Node(59), 1.0, hp)?;
    for (anode, cathode) in [(52, 51), (53, 52)] {
        s.diode(
            Node(anode),
            Node(cathode),
            headphone.diode_is_a,
            headphone.diode_ideality,
            hp.temperature_k,
        )?;
    }
    // Identify terminals AFTER all devices and capacitor currents are stamped.
    // Keep documentary coordinates: row 49 becomes a voltage equality (V),
    // not a physical KCL row (A). Its Jacobian is dimensionless, not 1 siemens.
    if ob.r21_lower_ohm == 0.0 || ob.r21_lower_ohm == 5000.0 {
        if ob.r21_lower_ohm == 5000.0 {
            s.r[48] += s.r[49];
            for k in 0..N {
                s.j[POSITION[48]][k] += s.j[POSITION[49]][k];
            }
        }
        s.r[49] = r21_constraint(x, ob.r21_lower_ohm);
        s.r[49]+=if ob.r21_lower_ohm==5000.{low[49]-low[48]}else{low[49]};
        s.j[POSITION[49]] = [0.0; N];
        s.j[POSITION[49]][POSITION[49]] = 1.0;
        if ob.r21_lower_ohm == 5000.0 {
            s.j[POSITION[49]][POSITION[48]] = -1.0;
        }
    }
    if s.r.iter().any(|v|!v.is_finite()) || (FULL && s.j.iter().flatten().any(|v|!v.is_finite()))
    {
        return Err(StepError::ExponentialDomain);
    }
    Ok((s.r, s.j))
}

fn r21_constraint(x: &[f64; N], lower: f64) -> f64 {
    if lower == 0.0 {
        x[49]
    } else if lower == 5000.0 {
        x[49] - x[48]
    } else {
        0.0
    }
}

#[derive(Clone,Copy)]
pub struct Prepared{p:Parameters,conversion:ConversionParameters,headphone:HeadphoneParameters,b:Boundary,metadata:(rf_d_circuit::cutoff::PanelEquivalent,MainLoad)}
impl Prepared{
 pub fn new(p:Parameters,conversion:ConversionParameters,headphone:HeadphoneParameters,b:Boundary)->Result<Self,StepError>{
  let metadata=prepare(p,conversion,headphone,b,SolverBudget::default())?;Ok(Self{p,conversion,headphone,b,metadata})
 }
 #[inline(always)]
 pub fn linearize<const FULL:bool>(self,x:&[f64;N],low:&[f64;N])->Result<([f64;N],[[f64;N];N]),StepError>{
  if x.iter().any(|v|!v.is_finite()){return Err(StepError::InvalidInput);}
  let(r,j)=evaluate::<FULL>(x,low,self.p,self.conversion,self.headphone,self.b,self.metadata)?;Ok((r,natural_jacobian(&j)))
 }
}
