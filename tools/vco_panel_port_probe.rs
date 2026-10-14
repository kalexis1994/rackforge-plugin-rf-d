#[path="../crates/rf-d-circuit/src/vco_panel_port.rs"] mod panel;
use std::io::{self,BufRead};
fn main() {
    for line in io::stdin().lock().lines() {
        let line=line.unwrap();let x:Vec<f64>=line.split(',').map(|v|v.parse().unwrap()).collect();
        assert_eq!(x.len(),4);
        match panel::evaluate(x[0],[x[1],x[2],x[3]]) {
            Err(_)=>println!("REJECT"),
            Ok(p)=>{
                let all=p.current_a.into_iter().chain(p.admittance_s.into_iter().flatten()).chain([p.cursor_v,p.open_voltage_v,p.resistance_ohm,p.dissipated_w]);
                println!("{}",all.map(|v|format!("{v:.17e}")).collect::<Vec<_>>().join(","));
            }
        }
    }
}
