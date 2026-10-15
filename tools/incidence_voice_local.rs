pub use rf_d_circuit::{junction_charge,StepError};
#[path="../crates/rf-d-circuit/src/direct_hybrid_voice.rs"]mod original;
#[path="../crates/rf-d-circuit/src/incidence_hybrid_voice.rs"]mod candidate;
#[path="../crates/rf-d-circuit/tests/support/mixer_chain_lab.rs"]mod lab;
use original::{State,Parts,Controls,N,M,B};
use candidate::{incidence::{Tangent,Row},solver};
use std::io::{self,BufRead};
fn chain()->rf_d_circuit::chain_charge::Parameters{let(a,b,c)=lab::lab_parameters();rf_d_circuit::chain_charge::Parameters{circuit:a,conversion:b,headphone:c,boundary:lab::controlled_boundary(0,true),mixer:rf_d_circuit::mixer_on::OnMixer::new([false;5],[0.5;4]).unwrap()}}
fn state(s:State)->candidate::State{candidate::State{high:s.high,low:s.low,optional:s.optional}}
fn view(t:&[Tangent;2])->[solver::Stage<'_>;2]{[solver::Stage{tangent:&t[0]},solver::Stage{tangent:&t[1]}]}
fn exact(a:[f64;M],b:[f64;M]){for k in 0..M{assert_eq!(a[k].to_bits(),b[k].to_bits());}}
fn retry(w:&mut solver::Workspace,t:&[Tangent;2],rhs:[f64;M],expected:[f64;M]){exact(w.solve(view(t),B,rhs).unwrap(),expected);}
fn bad(w:&mut solver::Workspace,t:&[Tangent;2],rhs:[f64;M],expected:[f64;M],dc:[[f64;N];N],mass:[[f64;N];N],stage:usize){
    let result=(||{let packet=Tangent::from_dense(&dc,&mass)?;let mut v=view(t);v[stage]=solver::Stage{tangent:&packet};w.solve(v,B,rhs)})();assert!(result.is_err());retry(w,t,rhs,expected);
}
fn full_reference(j:[[f64;M];M],b:[f64;M])->[f64;M]{
    let mut d=rf_d_circuit::block_decay_voice::solve_linear_extent(j,b).unwrap();
    for _ in 0..3{let mut r=[0.;M];for i in 0..M{let mut high=-b[i];let mut low=0.;for k in 0..M{let p=j[i][k]*d[k];let s=high+p;low+=if high.abs()>=p.abs(){(high-s)+p}else{(p-s)+high};low+=j[i][k].mul_add(d[k],-p);high=s;}r[i]=-(high+low);}let e=rf_d_circuit::block_decay_voice::solve_linear_extent(j,r).unwrap();for k in 0..M{d[k]+=e[k];}}
    let mut backward=0_f64;for i in 0..M{let mut high=-b[i];let mut low=0.;let mut scale=b[i].abs();for k in 0..M{let p=j[i][k]*d[k];let s=high+p;low+=if high.abs()>=p.abs(){(high-s)+p}else{(p-s)+high};low+=j[i][k].mul_add(d[k],-p);high=s;scale+=j[i][k].abs()*(d[k].abs()+2e-9);}backward=backward.max((high+low).abs()/scale.max(1e-300));}assert!(backward<=1e-11);d
}
fn packet_guards()->(usize,usize){
    let mut rejected=0;let mut retries=0;let zero=[[0.;N];N];let mut t=Tangent::from_dense(&zero,&zero).unwrap();
    for (a,b)in[(0,0),(54,55),(116,116),(117,0)]{for value in[f64::NAN,f64::INFINITY,f64::NEG_INFINITY]{for mass in[false,true]{let before=t.dense();assert!(t.add(a,b,if mass{0.}else{value},if mass{value}else{0.}).is_err());assert_eq!(before,t.dense());t.add(a,b,1e-20,0.).unwrap();t.add(a,b,-1e-20,0.).unwrap();assert_eq!(before,t.dense());rejected+=1;retries+=1;}}}
    for(a,b)in[(N,0),(0,N),(usize::MAX,0)]{assert!(t.add(a,b,1.,0.).is_err());assert_eq!(t.dense(),(zero,zero));rejected+=1;}
    t.add(0,0,1e308,0.).unwrap();let before=t.dense();assert!(t.add(0,0,1e308,0.).is_err());assert_eq!(before,t.dense());t.add(0,0,-1e308,0.).unwrap();rejected+=1;retries+=1;
    let mut sequential=Tangent::new();let mut row=Row::new();row.set(7,1e308,0.).unwrap();assert!(row.add(7,1e308,0.).is_err());assert!(row.set(N,0.,0.).is_err());assert!(row.add(N,0.,0.).is_err());rejected+=3;
    assert!(sequential.push_row(1,&mut row).is_err());sequential.push_row(0,&mut row).unwrap();assert!(sequential.push_row(0,&mut row).is_err());rejected+=2;
    for a in 1..N{sequential.push_row(a,&mut Row::new()).unwrap();}assert_eq!(sequential.dense().0[0][7],1e308);retries+=1;
    let mut dense=zero;for k in 0..candidate::incidence::CAPACITY{dense[k/N][k%N]=1.;}let mut full=Tangent::from_dense(&dense,&zero).unwrap();let before=full.dense();assert!(full.add(N-1,N-1,1.,0.).is_err());assert_eq!(before,full.dense());rejected+=1;
    full.add(0,0,-1.,0.).unwrap();full.add(N-1,N-1,1.,0.).unwrap();assert_eq!(full.dense().0[N-1][N-1],1.);retries+=1;
    dense[100][100]=1.;assert!(Tangent::from_dense(&dense,&zero).is_err());rejected+=1;
    let empty=Tangent::new();let mut w=solver::Workspace::new();assert!(w.solve([solver::Stage{tangent:&empty};2],B,[0.;M]).is_err());rejected+=1;
    let mut finite=zero;for k in 0..N{finite[k][k]=1.;}for k in 0..4{finite[0][k]=if k%2==0{1e308}else{-1e308};}let packet=Tangent::from_dense(&finite,&zero).unwrap();let mut d=[0.;M];d[..4].fill(0.5);
    assert!(w.check_direction([solver::Stage{tangent:&packet};2],B,[0.;M],d).is_err());rejected+=1;
    (rejected,retries)
}
fn main(){
    let mut w=solver::Workspace::new();let mut reference=original::Workspace::new();let mut pairs=0;let mut directions=0;let mut coefficient_entries=0;let mut physical_entries=0;let mut guards=0;let mut legal=0;let mut fraction=0_f64;let mut packet_max=0;
    for line in io::stdin().lock().lines(){let v:Vec<f64>=line.unwrap().split(',').map(|x|x.parse().unwrap()).collect();assert_eq!(v.len(),1185);
        let(t,h,key)=(v[0],v[1],v[2]);let c=Controls{key,short:false,optional:false};let cc=candidate::Controls{key,short:false,optional:false};let mut p=original::Parameters::new(chain()).unwrap();p.time=t;let mut q=candidate::Parameters::new(chain()).unwrap();q.time=t;
        let s=|b:usize|State{high:std::array::from_fn(|k|v[3+b*M+k]),low:std::array::from_fn(|k|v[3+b*M+N+k]),optional:false};let old=s(0);
        let original=[original::parts::<true>(p,old,s(1),c,h,t+h/3.).unwrap(),original::parts::<true>(p,old,s(2),c,h,t+h).unwrap()];
        let actual=[candidate::parts::<true>(q,state(old),state(s(1)),cc,h,t+h/3.).unwrap(),candidate::parts::<true>(q,state(old),state(s(2)),cc,h,t+h).unwrap()];
        for stage in 0..2{let(dc,mass)=actual[stage].tangent.dense();let residual=candidate::parts::<false>(q,state(old),state(s(stage+1)),cc,h,t+h*if stage==0{1./3.}else{1.}).unwrap();
            assert_eq!(actual[stage].dc,original[stage].dc);assert_eq!(actual[stage].dq,original[stage].dq);assert_eq!(actual[stage].now.high,original[stage].now.high);assert_eq!(actual[stage].now.low,original[stage].now.low);assert_eq!(residual.dc,actual[stage].dc);assert_eq!(residual.dq,actual[stage].dq);assert!(!residual.tangent.complete());
            for a in 0..N{for b in 0..N{assert_eq!(dc[a][b],original[stage].j[a][b]);assert_eq!(mass[a][b],original[stage].mass[a][b]);physical_entries+=2;}}
            packet_max=packet_max.max((0..N).map(|a|actual[stage].tangent.entries(a).count()).sum::<usize>());
        }
        let [a,b]=actual;let packet=[a.tangent,b.tangent];let matrix=w.coefficients(view(&packet),B).unwrap();
        for i in 0..M{for k in 0..M{let expected=B[i/N][k/N]*original[k/N].mass[i%N][k%N]+if i/N==k/N{original[i/N].j[i%N][k%N]}else{0.};assert_eq!(matrix[i][k].to_bits(),expected.to_bits());coefficient_entries+=1;}}
        let mut rhses=[[0.;M];8];rhses[0]=std::array::from_fn(|k|-(original[k/N].dc[k%N]+B[k/N][0]*original[0].dq[k%N]+B[k/N][1]*original[1].dq[k%N]));
        for(i,k)in[54,55,116,172,173,234].into_iter().enumerate(){rhses[i+1][k]=1.;}rhses[7]=std::array::from_fn(|k|(((k*17+11)%31)as f64-15.)/31.);
        let original_views=[original::solver::Stage{dc:&original[0].j,mass:&original[0].mass},original::solver::Stage{dc:&original[1].j,mass:&original[1].mass}];
        for rhs in rhses{let d=w.solve(view(&packet),B,rhs).unwrap();exact(d,reference.solve(original_views,B,rhs).unwrap());let full=full_reference(matrix,rhs);let worst=(0..M).fold(0_f64,|m,k|m.max((d[k]-full[k]).abs()/(2e-9+1e-7*full[k].abs())));assert!(worst<=1.);fraction=fraction.max(worst);directions+=1;}
        let rhs=rhses[0];let expected=w.solve(view(&packet),B,rhs).unwrap();let col=(0..54).find(|k|original[0].j[0][*k]==0.&&original[0].mass[0][*k]==0.).unwrap();let mut edge=Tangent::from_dense(&original[0].j,&original[0].mass).unwrap();edge.add(0,col,1e-20,0.).unwrap();
        let v=[solver::Stage{tangent:&edge},solver::Stage{tangent:&packet[1]}];let got=w.coefficients(v,B).unwrap();assert_eq!(got[0][col],1e-20);let d=w.solve(v,B,rhs).unwrap();let full=full_reference(got,rhs);assert!((0..M).all(|k|(d[k]-full[k]).abs()<=2e-9+1e-7*full[k].abs()));retry(&mut w,&packet,rhs,expected);legal+=1;
        if pairs==0{
            for stage in 0..2{for value in[f64::NAN,f64::INFINITY,f64::NEG_INFINITY]{let mut dc=original[stage].j;dc[117][117]=value;bad(&mut w,&packet,rhs,expected,dc,original[stage].mass,stage);let mut mass=original[stage].mass;mass[0][56]=value;bad(&mut w,&packet,rhs,expected,original[stage].j,mass,stage);guards+=2;}
                for(row,col)in[(0,56),(56,0)]{let mut dc=original[stage].j;dc[row][col]=1e-20;bad(&mut w,&packet,rhs,expected,dc,original[stage].mass,stage);let mut mass=original[stage].mass;mass[row][col]=1e-20;bad(&mut w,&packet,rhs,expected,original[stage].j,mass,stage);guards+=2;}}
            for value in[f64::NAN,f64::INFINITY,f64::NEG_INFINITY]{let mut r=rhs;r[235]=value;assert!(w.solve(view(&packet),B,r).is_err());retry(&mut w,&packet,rhs,expected);guards+=1;}
            for i in 0..2{for j in 0..2{for value in[f64::NAN,f64::INFINITY]{let mut weights=B;weights[i][j]=value;assert!(w.solve(view(&packet),weights,rhs).is_err());retry(&mut w,&packet,rhs,expected);guards+=1;}}}
            let zero=[[0.;N];N];let z=Tangent::from_dense(&zero,&zero).unwrap();assert!(w.solve([solver::Stage{tangent:&z};2],B,rhs).is_err());retry(&mut w,&packet,rhs,expected);guards+=1;
            let mut dense=zero;for a in 0..54{for b in 0..54{dense[a][b]=1e-8;}}bad(&mut w,&packet,rhs,expected,original[0].j,dense,0);guards+=1;
            let mut cancel=Tangent::from_dense(&original[0].j,&original[0].mass).unwrap();cancel.add(0,col,-B[0][0]*2e-20,2e-20).unwrap();let got=w.coefficients([solver::Stage{tangent:&cancel},solver::Stage{tangent:&packet[1]}],B).unwrap();assert_eq!(got[0][col],0.);assert_eq!(got[N][col],B[1][0]*2e-20);retry(&mut w,&packet,rhs,expected);
        }pairs+=1;
    }
    assert_eq!((pairs,directions,guards,legal),(24,192,33,24));let s=w.statistics;let(pg,pr)=packet_guards();
    println!("INCIDENCE,{pairs},{directions},{physical_entries},{coefficient_entries},{guards},{legal},{packet_max},{pg},{pr},{fraction:.17e},{},{},{:.17e},{:.17e},{}",s.solves,s.refinements,s.max_initial_backward,s.max_final_backward,s.max_nonzeros);
}
