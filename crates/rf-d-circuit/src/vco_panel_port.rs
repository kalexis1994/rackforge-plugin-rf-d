//! Exact resistive OSC1 ON R6/R45 port, SVC-9 pp.5/19.
//! Terminal order [SAW_OUTPUT_9B, GROUND, MIX_BUS_BOARD4_PIN4].
//! No oscillator waveform or output-impedance approximation is supplied here.
pub const R6_OHM:f64=25_000.;
pub const R45_OHM:f64=33_000.;
#[derive(Clone,Copy,Debug,PartialEq)]
pub struct Port {
    pub current_a:[f64;3],
    pub admittance_s:[[f64;3];3],
    pub cursor_v:f64,
    pub open_voltage_v:f64,
    pub resistance_ohm:f64,
    pub dissipated_w:f64,
}
#[derive(Clone,Copy,Debug,PartialEq)]
pub struct InvalidInput;
pub fn evaluate(alpha:f64,voltage:[f64;3])->Result<Port,InvalidInput> {
    if !alpha.is_finite() || !(0. ..=1.).contains(&alpha) ||
        voltage.iter().any(|v|!v.is_finite()||v.abs()>40.) {
        return Err(InvalidInput);
    }
    let source=voltage[0]-voltage[1];
    let resistance=R45_OHM+R6_OHM*alpha*(1.-alpha);
    let open=voltage[1]+alpha*source;
    let outward=(open-voltage[2])/resistance;
    let current=[source/R6_OHM+alpha*outward,
        -source/R6_OHM+(1.-alpha)*outward,-outward];
    let w=[alpha,1.-alpha,-1.];
    let g=std::array::from_fn(|i|std::array::from_fn(|j|
        w[i]*w[j]/resistance+if i<2&&j<2 {
            if i==j{1./R6_OHM}else{-1./R6_OHM}
        }else{0.}));
    Ok(Port{current_a:current,admittance_s:g,cursor_v:voltage[2]+R45_OHM*outward,
        open_voltage_v:open,resistance_ohm:resistance,
        dissipated_w:source*source/R6_OHM+resistance*outward*outward})
}
