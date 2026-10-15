pub use rf_d_circuit::StepError;
#[path="../crates/rf-d-circuit/src/ladder_voice_solver.rs"]mod solver;
use solver::*;
fn equal(a:[f64;M],b:[f64;M]){for k in 0..M{assert_eq!(a[k].to_bits(),b[k].to_bits());}}
fn main(){
    let mut workspace=Workspace::new();let mut dc=[[0.;N];N];let mass=dc;for k in 0..N{dc[k][k]=1.;}
    let b=[[1.5,0.5],[-4.5,2.5]];let rhs=[1.;M];let valid=[Stage{dc:&dc,mass:&mass};2];
    let expected=workspace.solve(valid,b,rhs).unwrap();equal(expected,rhs);
    let mut guards=0;
    let mut bad=|stage:[Stage;2],weights:[[f64;2];2],input:[f64;M]|{
        assert!(workspace.solve(stage,weights,input).is_err());equal(expected,workspace.solve(valid,b,rhs).unwrap());guards+=1;
    };
    for value in[f64::NAN,f64::INFINITY,f64::NEG_INFINITY]{
        for stage in 0..2{for (a,c)in[(0,0),(54,55),(110,110)]{
            let mut corrupt=dc;corrupt[a][c]=value;let mut s=valid;s[stage]=Stage{dc:&corrupt,mass:&mass};bad(s,b,rhs);
            let mut corrupt=mass;corrupt[a][c]=value;let mut s=valid;s[stage]=Stage{dc:&dc,mass:&corrupt};bad(s,b,rhs);
        }}
        for i in 0..2{for j in 0..2{let mut weights=b;weights[i][j]=value;bad(valid,weights,rhs);}}
        for k in[0,54,55,110,111,165,166,221]{let mut input=rhs;input[k]=value;bad(valid,b,input);}
    }
    for stage in 0..2{for(a,c)in[(0,56),(56,0)]{
        let mut corrupt=dc;corrupt[a][c]=1e-20;let mut s=valid;s[stage]=Stage{dc:&corrupt,mass:&mass};bad(s,b,rhs);
        let mut corrupt=mass;corrupt[a][c]=1e-20;let mut s=valid;s[stage]=Stage{dc:&dc,mass:&corrupt};bad(s,b,rhs);
    }}
    let mut zero=dc;zero[55]=[0.;N];bad([Stage{dc:&zero,mass:&mass};2],b,rhs);
    // Finite entries whose factorization overflows, followed by exact valid retry.
    let mut overflow=dc;overflow[0][0]=1e308;overflow[0][1]=1e308;overflow[1][0]=1e308;overflow[1][1]=-1e308;
    bad([Stage{dc:&overflow,mass:&mass};2],b,rhs);
    let mut dense=dc;for i in 0..54{for j in 0..54{dense[i][j]=if i==j{2.}else{0.001};}}
    bad([Stage{dc:&dense,mass:&mass};2],b,rhs);let capacity_retries=1;
    drop(bad);
    let mut coefficient_entries=0;let mut fill_rhs=0;
    for variant in 0..2{
        let mut a=dc;let mut m=mass;
        let fill=[[2.,0.,1.,0.],[1.,2.,0.,1.],[2.,1.,1.,0.],[0.,0.,1.,2.]];
        let swap=[[0.,2.,1.,0.],[1.,1.,0.,0.],[2.,0.,3.,1.],[0.,0.,1.,2.]];
        for i in 0..4{for j in 0..4{a[i][j]=if variant==0{fill[i][j]}else{swap[i][j]};}}
        a[54][0]=0.03125;a[0][54]=0.0625;a[54][56]=0.015625;a[56][54]=0.03125;a[55][1]=0.015625;a[1][55]=0.03125;
        m[1][1]=0.25;m[55][55]=0.02;
        let stages=[Stage{dc:&a,mass:&m};2];let matrix=workspace.coefficients(stages,b).unwrap();
        for i in 0..M{for j in 0..M{let value=b[i/N][j/N]*m[i%N][j%N]+if i/N==j/N{a[i%N][j%N]}else{0.};if value==0.{assert_eq!(matrix[i][j],0.);}else{assert_eq!(matrix[i][j].to_bits(),value.to_bits());}coefficient_entries+=1;}}
        for col in 0..8{
            let target:[f64;M]=std::array::from_fn(|k|if col==7{(((k*7+3)%23)as f64-11.)/23.}else if k==[0,54,55,56,165,166,221][col]{1.}else{0.});
            let input=std::array::from_fn(|i|(0..M).map(|j|matrix[i][j]*target[j]).sum());let got=workspace.solve(stages,b,input).unwrap();
            for k in 0..M{assert!((got[k]-target[k]).abs()<=2e-12);}fill_rhs+=1;
        }
        // Add a legal, previously absent edge; remove it by reinitializing.
        let mut changed=a;changed[0][10]=1e-20;let new=[Stage{dc:&changed,mass:&m};2];let actual=workspace.coefficients(new,b).unwrap();assert_eq!(actual[0][10],1e-20);
        equal(expected,workspace.solve(valid,b,rhs).unwrap());
    }
    println!("GUARDS,{guards},{guards},{coefficient_entries},{fill_rhs},{capacity_retries},1,2");
}
