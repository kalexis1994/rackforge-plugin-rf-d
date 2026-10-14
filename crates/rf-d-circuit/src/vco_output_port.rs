//! Exact output resistor network, SVC-9 pp.5/19, OSC1 saw ON.
//! Terminals [drive48, triangle54, ground, BUS12]; three internal nodes removed.
#[path="vco_panel_port.rs"] mod panel;
pub const PULLDOWN_OHM:f64=4700.;
pub const DRIVE_OHM:f64=4300.;
pub const TRIANGLE_OHM:f64=47000.+10000.;
#[derive(Clone,Copy,Debug,PartialEq)]
pub struct Port {
    pub current_a:[f64;4],pub admittance_s:[[f64;4];4],
    pub saw_v:f64,pub tap_v:f64,pub cursor_v:f64,pub dissipated_w:f64,
}
pub fn evaluate(alpha:f64,v:[f64;4])->Result<Port,panel::InvalidInput> {
    if !alpha.is_finite()||!(0. ..=1.).contains(&alpha)||v.iter().any(|x|!x.is_finite()||x.abs()>40.) {return Err(panel::InvalidInput);}
    let resistance=panel::R45_OHM+panel::R6_OHM*alpha*(1.-alpha);
    let conductance=1./PULLDOWN_OHM+1./DRIVE_OHM+1./TRIANGLE_OHM+1./panel::R6_OHM+alpha*alpha/resistance;
    let saw=v[2]+((v[0]-v[2])/DRIVE_OHM+(v[1]-v[2])/TRIANGLE_OHM+alpha*(v[3]-v[2])/resistance)/conductance;
    let p=panel::evaluate(alpha,[saw,v[2],v[3]])?;
    let drive=(v[0]-saw)/DRIVE_OHM;let tri=(v[1]-saw)/TRIANGLE_OHM;
    let ground=-(saw-v[2])/PULLDOWN_OHM+p.current_a[1];
    let derivative=[1./(DRIVE_OHM*conductance),1./(TRIANGLE_OHM*conductance),
        1.-(1./DRIVE_OHM+1./TRIANGLE_OHM+alpha/resistance)/conductance,alpha/(resistance*conductance)];
    let mut y=[[0.;4];4];
    for k in 0..4 {
        y[0][k]=((if k==0{1.}else{0.})-derivative[k])/DRIVE_OHM;
        y[1][k]=((if k==1{1.}else{0.})-derivative[k])/TRIANGLE_OHM;
        y[3][k]=((if k==3{1.}else{0.})-alpha*derivative[k]-(if k==2{1.-alpha}else{0.}))/resistance;
        y[2][k]=-y[0][k]-y[1][k]-y[3][k];
    }
    let power=(v[0]-saw).powi(2)/DRIVE_OHM+(v[1]-saw).powi(2)/TRIANGLE_OHM+(saw-v[2]).powi(2)/PULLDOWN_OHM+p.dissipated_w;
    Ok(Port{current_a:[drive,tri,ground,p.current_a[2]],admittance_s:y,saw_v:saw,
        tap_v:saw+47000.*(v[1]-saw)/TRIANGLE_OHM,cursor_v:p.cursor_v,dissipated_w:power})
}
