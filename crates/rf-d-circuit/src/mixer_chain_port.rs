//! Loaded five-source ON port; SVC-9 pp.19/13/10, fixed incoming charge history.
//! Active downstream network: the loaded Jacobian need not be reciprocal.
use crate::{circuit66::{Boundary,Parameters,State},mixer_chain66::{self,ResultChain},mixer_on::OnMixer,
    output_conversion::{Parameters as Conversion,solve_linear_many},Parameters as Headphone,SolverBudget,StepError};

#[derive(Clone,Copy,Debug)]
pub struct PortResponse {
    pub next_state:State,
    pub result:ResultChain,
    pub current_a:[f64;5],
    pub admittance_s:[[f64;5];5],
    pub node_gradient_v_per_v:[[f64;5];66],
    pub bus_gradient_v_per_v:[f64;5],
}

pub fn solve_input_port(previous:&State,mixer:OnMixer,source_v:[f64;5],p:Parameters,c:Conversion,h:Headphone,
    b:Boundary,budget:SolverBudget)->Result<PortResponse,StepError> {
    let mut candidate=*previous;
    let result=mixer_chain66::step(&mut candidate,mixer,source_v,p,c,h,b,budget)?;
    let(_,j,port)=mixer_chain66::linearize(previous,mixer,source_v,p,c,h,b,&candidate.node_v)?;
    let mut rhs=[[0.;5];66];
    for column in 0..5 {rhs[6][column]=-port.jacobian_s[5][column];}
    let dx=solve_linear_many(j,rhs)?;
    let admittance=std::array::from_fn(|i|std::array::from_fn(|k|
        port.jacobian_s[i][k]+port.jacobian_s[i][5]*dx[6][k]));
    let gc=10e-6/b.recovery.vca.second.output.output.dt_s;
    let bus_gradient=std::array::from_fn(|k| dx[6][k]-(port.jacobian_s[5][k]+port.jacobian_s[5][5]*dx[6][k])/gc);
    if admittance.iter().flatten().chain(dx.iter().flatten()).chain(bus_gradient.iter()).any(|v:&f64|!v.is_finite()) {
        return Err(StepError::InvalidInput);
    }
    Ok(PortResponse {next_state:candidate,result,current_a:std::array::from_fn(|i|port.current_a[i]),
        admittance_s:admittance,node_gradient_v_per_v:dx,bus_gradient_v_per_v:bus_gradient})
}
