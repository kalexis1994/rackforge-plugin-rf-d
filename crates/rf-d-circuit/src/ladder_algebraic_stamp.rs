//! Isolated original ladder laws; LADDER_ALGEBRAICO_PROTOCOLO.
use rf_d_circuit::{vca2_output::Parameters as Bjt,StepError};
pub use rf_d_circuit::cutoff_ladder_output::Parameters;
const N: usize = 16;
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
    fixed:[f64;2],fixed_j:[[f64;N];2],
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
            }else if let Fixed(v)=terminal{
                let k=if v==0.{0}else{1};self.fixed[k]+=sign*current;
                for(other,slope)in[(left,g),(right,-g)]{if let Node(col)=other{self.fixed_j[k][col]+=sign*slope;}}
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
            }else if let Fixed(v)=terminals[row]{
                let k=if v==0.{0}else{1};self.fixed[k]+=polarity*[ib,ic,-ib-ic][row];
                let mut low=0.;for col in 0..3{low+=slopes[row][col]*self.low(terminals[col]);if let Node(a)=terminals[col]{self.fixed_j[k][a]+=slopes[row][col];}}self.fixed[k]+=low;
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

pub struct Linear{pub dc:[f64;N],pub j:[[f64;N];N],pub fixed:[f64;2],pub fixed_j:[[f64;N];2]}
pub fn linearize(p:Parameters,x:&[f64;N],low:&[f64;N])->Result<Linear,StepError>{
 if x.iter().chain(low.iter()).any(|v|!v.is_finite()){return Err(StepError::InvalidInput);}
    let mut s = Stamp::<true> {
        x,low,
        r: [0.0; N],
        j: [[0.0; N]; N],fixed:[0.;2],fixed_j:[[0.;N];2],
    };
    // Ladder, Fig.9-11. Documentary R61 alternatives stay explicit.
    s.resistor(Node(0), Fixed(10.0), 220.0);
    for i in 0..4 {
        s.resistor(Node(i), Node(i + 1), 150.0);
    }
    s.resistor(Node(4), Fixed(0.0), p.r61_ohm);
    s.resistor(Node(4), Node(6), 470.0);
    s.resistor(Node(4), Node(7), p.r30_ohm);
    for (base, collector, emitter) in [
        (6, Node(8), 5),
        (3, Node(9), 8),
        (2, Node(10), 9),
        (1, Node(11), 10),
        (0, Fixed(10.0), 11),
        (7, Node(12), 5),
        (3, Node(13), 12),
        (2, Node(14), 13),
        (1, Node(15), 14),
        (0, Fixed(10.0), 15),
    ] {
        s.transistor(
            Node(base),
            collector,
            Node(emitter),
            1.0,
            p.ladder_transistor,
        )?;
    }

 if s.r.iter().chain(s.j.iter().flatten()).chain(s.fixed.iter()).chain(s.fixed_j.iter().flatten()).any(|v|!v.is_finite()){return Err(StepError::ExponentialDomain);}
 Ok(Linear{dc:s.r,j:s.j,fixed:s.fixed,fixed_j:s.fixed_j})
}
