//! Circuit-derived guess only; final startup is the unchanged full 134-row Newton.
//! SVC-9 p.5/p.19, fixed nominal cards at 25 C. See VCO1_ARRANQUE_PROTOCOLO.md.
use crate::{lm741_port,vco1_newton,vco1_stamp,vco_bjt};
use vco1_stamp::{Controls,Mode,N,NAMES};
#[derive(Clone,Copy,Debug,PartialEq)]
pub enum Error { InvalidControls, SeedDomain, Opamp(lm741_port::Error), Device(vco1_stamp::Error), Newton(vco1_newton::Error) }
const IS:f64=1e-14;
const BF:f64=100.;
const BR:f64=5.;
const VT:f64=vco_bjt::THERMAL_VOLTAGE_V;
fn junction(i:f64)->Result<f64,Error> {
 if !i.is_finite()||i<=0. {return Err(Error::SeedDomain);}Ok(VT*(i/IS).ln_1p())
}
fn put(x:&mut [f64;N],name:&str,v:f64) {x[NAMES.iter().position(|n|*n==name).unwrap()]=v;}
/// Analytic KCL/KVL approximation; no file, table of roots, fitted pitch or waveform.
pub fn seed(c:Controls)->Result<[f64;N],Error> {
 if c.cv_v.iter().chain([c.mixer_v].iter()).any(|v|!v.is_finite()||v.abs()>40.)||!c.r8_fraction.is_finite()||!(0. ..=1.).contains(&c.r8_fraction)||!c.r11_ohm.is_finite()||!(0. ..=1000.).contains(&c.r11_ohm)||!c.external_neg4_load_a.is_finite()||c.external_neg4_load_a.abs()>1. {return Err(Error::InvalidControls);}
 let mut x=[0.;N];
 let rail_r=1./(1./6200.+1./3900.);let mut ref4=-10.*3900./(6200.+3900.);let mut e4=ref4;
 for _ in 0..8 {let ie=(e4+10.)/12000.;let ic=ie*BF/(BF+1.);ref4=-10.*3900./(6200.+3900.)-rail_r*(ie/(BF+1.)+c.external_neg4_load_a);e4=ref4-1000.*ie/(BF+1.)-junction(ic)?;}
 let tail4=(e4+10.)/12000.*BF/(BF+1.);
 // Balanced JFET gates at C1=0 imply this DC drive through R4/R25/R24.
 let drive=10700.*(10./15000.-10./33200.);
 let mut fs=2.5-(tail4/(2.*0.0003018867924528302)).sqrt();
 let fd=10.-5600.*tail4/2.;
 for _ in 0..8 {fs=2.5-(tail4/(2.*0.0003018867924528302*(1.+0.003*(fd-fs)))).sqrt();}
 let mut ep=fd;
 for _ in 0..8 {ep=fd+junction((10.-ep)/1200./2.*BF/(BF+1.))?;}
 let i8=(10.-ep)/1200./2.*BF/(BF+1.);
 let mut be3=junction(i8)?;
 for _ in 0..8 {let f=IS*(be3/VT).exp_m1();be3-=(be3/2700.+f/BF-i8)/(1./2700.+(f+IS)/(VT*BF));}
 // Q2 is saturated at startup. Solve its transport currents, not an arbitrary VCE drop.
 let mut q2c=drive;let mut q2e=drive;let mut q1e=drive;
 for _ in 0..8 {
  let ie1=(q1e+10.)/(750.+8200.);let ic2=(10.-q2c)/10700.-(q2c+10.)/150000.-ie1/(BF+1.);let ie2=(q2e+10.)/10000.;
  let f=((1.+1./BR)*ie2-ic2)/((1.+1./BR)*(1.+1./BF)-1.);let r=f*(1.+1./BF)-ie2;
  q2e=drive-junction(f)?;q2c=drive-junction(r)?;q1e=q2c-junction(ie1*BF/(BF+1.))?;
 }
 let tri=(q1e/750.-10./8200.)/(1./750.+1./8200.);
 let gw=2./12500.+1./33000.;let saw=(drive/4300.+tri/57000.+c.mixer_v/(12500.*33000.*gw))/(1./4300.+1./4700.+1./57000.+1./12500.-1./(12500.*12500.*gw));
 let wiper=(saw/12500.+c.mixer_v/33000.)/gw;
 let mut b6=0.;let mut c6=0.;let mut reset=0.;let mut sense=0.;
 for _ in 0..8 {
  sense=(10./33200.+drive/10700.+reset/10000.)/(1./33200.+1./10700.+1./10000.);
  reset=(c6/56.-10./1000.+sense/10000.)/(1./56.+1./1000.+1./10000.);
  let ic=(c6-reset)/56.;let ib=(10.+b6)/10000.;let f=(ic+(BR+1.)*ib)/(1.+(BR+1.)/BF);let r=BR*(ib-f/BF);
  b6=-junction(f)?;c6=b6+junction(r)?;
 }
 let sum=-5.+0.001;let mut qce=-10.;let mut out=sum;let mut qa=-5.;let mut qb=qa;let mut pair=qa;let mut qbc=ref4;let mut qcb=qa;let mut out3=ref4;let mut it=0.;let mut track=0.;let mut top=out;let mut bottom=out;
 for _ in 0..8 {
  let external=c.cv_v.iter().zip([150000.,560000.,51100.,51100.,51100.,15000.]).map(|(v,r)|(sum-v)/r).sum::<f64>();
  it=(sum+10.)/(c.r11_ohm+11800.);out=sum+1000.*(external+it+(sum-qce)/160000.);
  track=(out+5.)/(33.+100.+1000.);top=out-33.*track;bottom=-5.+1000.*track;qb=bottom+c.r8_fraction*(top-bottom);
  // CM equation of the complete 741: G4/Rcm contribution, seed only.
  qbc=ref4-0.001-3.1623e-5*ref4;
  let ib=(0.-qbc)/39000.;let ia=ib*((qa-qb)/VT).exp();qa=-5.-100.*ia/BF;
  pair=qb-junction(ib)?;let ic=(ia+ib)*(1.+1./BF);
  qce=(-10./1000.+sum/160000.+ic*(1.+1./BF))/(1./1000.+1./160000.);
  qcb=qce+junction(ic)?;out3=qcb+15000.*((qcb+10.)/2000.+ic/BF);
 }
 let q11b=(drive/43000.-10./390000.)/(2./43000.+1./390000.+1./910000.);
 for (n,v) in [
  ("NEG10_V",-10.),("POS10_V",10.),("NEG5_V",-5.),("NEG4_REF",ref4),
  ("Q4_BASE",ref4-1000.*tail4/BF),("Q4_EMITTER",e4),("Q4_COLLECTOR",fs-100.*tail4),
  ("FET_COMMON_SOURCE",fs),("FET_LEFT_DRAIN",fd),("FET_RIGHT_DRAIN",fd),("FET_C3_LEFT",ep),("FET_C4_LEFT",0.),
  ("SCHMITT_DRIVE",drive),("Q3_BASE",-10.+be3),("Q2_COLLECTOR",q2c),("Q2_EMITTER",q2e),("Q1_EMITTER",q1e),
  ("TRI_OUTPUT_21B",tri),("SAW_OUTPUT_9B",saw),("R6_WIPER",wiper),("MIX_BUS_BOARD4_PIN4",c.mixer_v),
  ("SAW_TRI_TAP",(saw/47000.+tri/10000.)/(1./47000.+1./10000.)),
  ("SCHMITT_SENSE",sense),("SCHMITT_Q5_COLLECTOR",b6),("SCHMITT_Q6_COLLECTOR",c6),("RESET_BIAS",reset),("Q10_BASE",c6),
  ("Q11_BASE",q11b),("Q11_COLLECTOR",-10.),("Q12_BASE",-10.),("Q12_COLLECTOR",0.),("RECT_OUTPUT_20B",0.),
  ("IC1_PLUS",-5.),("IC1_SUM",sum),("IC1_OUT",out),("IC3_OUT",out3),("QA_BASE",qa),("QB_BASE",qb),
  ("QB_COLLECTOR",qbc),("PAIR_EMITTER",pair),("QC_EMITTER",qce),("QC_BASE",qcb),("R78_RC_MID",qcb),
  ("R37_TOP",-10.+11800.*it),("R8_TOP",top),("R8_BOTTOM",bottom),("SW6_11",-1.5),("SW6_12",-2.5)] {put(&mut x,n,v);}
 for (n,v) in ["BEND","TUNE","KEYBOARD","MOD","EXT","OSC1_RANGE"].into_iter().zip(c.cv_v) {put(&mut x,n,v);}
 x[131]=track;x[132]=track;x[133]=it;
 // Own analytic seeds/solves of both nominal 741 interiors, then full coupled Newton.
 for (k,p) in [[x[8],x[9],0.,-10.,x[7]],[x[35],x[15],10.,-10.,x[10]]].into_iter().enumerate() {
  let op=lm741_port::dc(p).map_err(Error::Opamp)?;
  x[56+21*k..77+21*k].copy_from_slice(&op.nodes[5..26]);x[109+11*k..120+11*k].copy_from_slice(&op.nodes[26..37]);
 }
 vco1_stamp::linearize(x,c,Mode::Dc).map_err(Error::Device)?;Ok(x)
}
pub fn startup(c:Controls)->Result<vco1_newton::Solution,Error> {
 vco1_newton::solve(c,Mode::Dc,vco1_newton::Boundary::StartupRampZero,seed(c)?,vco1_newton::Budget::default()).map_err(Error::Newton)
}
