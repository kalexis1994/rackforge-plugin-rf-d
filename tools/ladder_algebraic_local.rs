pub use rf_d_circuit::{junction_charge,StepError};
#[path="../crates/rf-d-circuit/src/ladder_algebraic.rs"] mod ladder;
#[path="../crates/rf-d-circuit/src/prepared_audio_stamp.rs"] mod reference;
#[path="../crates/rf-d-circuit/src/prepared_chain_charge.rs"] mod chain;
#[path="../crates/rf-d-circuit/tests/support/mixer_chain_lab.rs"] mod lab;
use ladder::*;
use std::{io::{self,BufRead},alloc::{GlobalAlloc,Layout,System},sync::atomic::{AtomicUsize,Ordering}};
static ALLOCS:AtomicUsize=AtomicUsize::new(0);
struct Counting;
unsafe impl GlobalAlloc for Counting{
    unsafe fn alloc(&self,l:Layout)->*mut u8{ALLOCS.fetch_add(1,Ordering::Relaxed);System.alloc(l)}
    unsafe fn dealloc(&self,p:*mut u8,l:Layout){System.dealloc(p,l)}
    unsafe fn realloc(&self,p:*mut u8,l:Layout,n:usize)->*mut u8{ALLOCS.fetch_add(1,Ordering::Relaxed);System.realloc(p,l,n)}
}
#[global_allocator]static GLOBAL:Counting=Counting;
fn index(k:usize)->usize{match k{5=>55,32=>54,62..=65=>k-28,_=>56+k-(k>5)as usize-(k>32)as usize-4*(k>65)as usize}}
fn distance(a:Nodes,b:Nodes)->f64{(0..16).fold(0_f64,|m,k|{let(h,l)=add_pair(a.high[k],a.low[k],-b.high[k]);let(h,l)=add_pair(h,l,-b.low[k]);m.max((h+l).abs())})}
fn equal(a:&Solution,b:&Solution){
    for (a,b)in a.nodes.high.iter().chain(a.nodes.low.iter()).chain(a.z.high.iter()).chain(a.z.low.iter())
        .chain(a.reaction.iter()).chain(a.reaction_j.iter().flatten()).chain(a.source.iter()).chain(a.source_j.iter().flatten()).chain(a.dz_dy.iter().flatten())
        .zip(b.nodes.high.iter().chain(b.nodes.low.iter()).chain(b.z.high.iter()).chain(b.z.low.iter())
        .chain(b.reaction.iter()).chain(b.reaction_j.iter().flatten()).chain(b.source.iter()).chain(b.source_j.iter().flatten()).chain(b.dz_dy.iter().flatten())){assert_eq!(a.to_bits(),b.to_bits());}
    assert_eq!(a.iterations,b.iterations);assert_eq!(a.residual_a.to_bits(),b.residual_a.to_bits());assert_eq!(a.correction_v.to_bits(),b.correction_v.to_bits());
}
fn guards(model:Model,y:Retained,z:Algebraic,h:f64,d:Nodes)->usize{
    let good=model.solve(y,z,Budget::default()).unwrap();let mut count=0;
    let mut retry=|bad:bool|{assert!(bad);equal(&good,&model.solve(y,z,Budget::default()).unwrap());count+=1;};
    for v in[f64::NAN,f64::INFINITY,f64::NEG_INFINITY]{
        for k in 0..7{let mut q=z;q.high[k]=v;retry(model.solve(y,q,Budget::default()).is_err());let mut q=z;q.low[k]=v;retry(model.solve(y,q,Budget::default()).is_err());}
        for k in 0..9{let mut q=y;q.high[k]=v;retry(model.solve(q,z,Budget::default()).is_err());let mut q=y;q.low[k]=v;retry(model.solve(q,z,Budget::default()).is_err());}
        retry(charge(d,v).is_err());let mut q=d;q.high[15]=v;retry(charge(q,h).is_err());let mut q=d;q.low[0]=v;retry(charge(q,h).is_err());
    }
    for k in 0..7{let mut q=z;q.low[k]=1.;retry(model.solve(y,q,Budget::default()).is_err());}
    for k in 0..9{let mut q=y;q.low[k]=1.;retry(model.solve(q,z,Budget::default()).is_err());}
    let mut q=y;q.high[0]=100.;q.low[0]=0.;retry(model.solve(q,z,Budget::default()).is_err());
    for value in[-40.01,40.01,40.]{let mut q=y;q.high[3]=value;q.low[3]=if value==40.{1e-16}else{0.};retry(model.solve(q,z,Budget::default()).is_err());}
    let mut q=z;q.high[0]=40.;q.low[0]=0.;retry(model.solve(y,q,Budget::default()).is_err());
    for b in[Budget{iterations:0,backtracks:24},Budget{iterations:81,backtracks:24},Budget{iterations:80,backtracks:0},Budget{iterations:80,backtracks:25}]{retry(model.solve(y,z,b).is_err());}
    retry(model.solve(y,z.advanced([0.01;7]),Budget{iterations:1,backtracks:24}).is_err());
    for dt in[0.,-1.,MIN_DT_S/2.,1e-3+1e-9]{retry(charge(d,dt).is_err());}
    let mut q=d;q.low[8]=1.;retry(charge(q,h).is_err());
    let mut q=d;q.high[4]=f64::MAX;q.low[4]=0.;retry(charge(q,MIN_DT_S).is_err());
    let mut a=[[0.;7];7];retry(Factor::new(a).is_err());
    for k in 0..7{a[k][k]=1.;}let f=Factor::new(a).unwrap();let expected=f.solve([1.;7]).unwrap();
    for v in[f64::NAN,f64::INFINITY,f64::NEG_INFINITY]{let mut q=a;q[6][0]=v;retry(Factor::new(q).is_err());retry(f.solve([v;7]).is_err());assert_eq!(f.solve([1.;7]).unwrap(),expected);}
    let mut q=a;q[1]=q[0];retry(Factor::new(q).is_err());
    let mut q=a;q[0][0]=1e308;q[0][1]=1e308;q[1][0]=1e308;q[1][1]=-1e308;retry(Factor::new(q).is_err());
    let mut q=a;q[0][0]=1e-308;let tiny=Factor::new(q).unwrap();retry(tiny.solve([1e308;7]).is_err());
    let mut q=y;q.high[3]=40.;q.low[3]=0.;let mut seed=z;seed.high[0]=40.;seed.low[0]=0.;retry(model.solve(q,seed,Budget::default()).is_err());
    count
}
fn main(){
    let(p,c,hp)=lab::lab_parameters();let model=Model::new(p).unwrap();let full=reference::Prepared::new(p,c,hp,lab::controlled_boundary(0,true)).unwrap();
    let parent=chain::Parameters::new(rf_d_circuit::chain_charge::Parameters{circuit:p,conversion:c,headphone:hp,boundary:lab::controlled_boundary(0,true),mixer:rf_d_circuit::mixer_on::OnMixer::new([false;5],[0.5;4]).unwrap()}).unwrap();
    assert_eq!(&chain::CAPACITORS[..5],&OWNED_CAPACITORS.map(|(a,b,c)|(a,if b==16{68}else{b},c)));
    assert_eq!(&chain::CAPACITORS[5..8],&[(6,66,10e-6),(16,11,0.22e-6),(17,15,0.22e-6)]);
    let mut stages=0;let mut solves=0;let mut fdcols=0;let mut max_iter=0;let mut invalid=0;let mut invalid_p=0;
    let(mut dc_fraction,mut jac_fraction,mut reconstructed_v,mut solved_v,mut reaction_a,mut fd_fraction,mut dx_fraction,mut source_fraction,mut conservation_a,mut conservation_s,mut charge_a,mut mass_s,mut residual_a,mut correction_v)=(0_f64,0_f64,0_f64,0_f64,0_f64,0_f64,0_f64,0_f64,0_f64,0_f64,0_f64,0_f64,0_f64,0_f64);
    let mut heap=0;let mut parent_checks=0;let mut direct_fd_columns=0;let mut direct_fd_fraction=0_f64;let mut parent_charge_a=0_f64;let mut parent_mass_s=0_f64;
    for line in io::stdin().lock().lines(){
        let row:Vec<f64>=line.unwrap().split(',').map(|x|x.parse().unwrap()).collect();assert_eq!(row.len(),1185);
        let dt=row[1];
        for stage in 0..2{
            let get=|block:usize|Nodes{high:std::array::from_fn(|k|row[3+block*236+index(k)]),low:std::array::from_fn(|k|row[3+block*236+118+index(k)])};
            let now=get(3+stage);let delta=get(1+stage);
            let hi:[f64;66]=std::array::from_fn(|k|row[3+(3+stage)*236+index(k)]);
            let lo:[f64;66]=std::array::from_fn(|k|row[3+(3+stage)*236+118+index(k)]);
            let get_chain=|block:usize|chain::State{high:std::array::from_fn(|k|row[3+block*236+index(k)]),low:std::array::from_fn(|k|row[3+block*236+118+index(k)])};
            let start=ALLOCS.load(Ordering::Relaxed);
            let(z,y)=coordinates(now).unwrap();let reconstructed=reconstruct(z,y).unwrap();let rec=distance(now,reconstructed);assert!(rec<=2e-9);reconstructed_v=reconstructed_v.max(rec);
            let s=stamp::linearize(p,&now.high,&now.low).unwrap();let(r,j)=full.linearize::<true>(&hi,&lo).unwrap();
            for a in 0..16{
                dc_fraction=dc_fraction.max((s.dc[a]-r[a]).abs()/20e-12);
                for b in 0..16{jac_fraction=jac_fraction.max((s.j[a][b]-j[a][b]).abs()/2e-9);}
                for b in 16..66{assert_eq!(j[a][b],0.);}
            }
            assert!(dc_fraction<=1.&&jac_fraction<=1.);
            let e=model.evaluate(z,y).unwrap();let original=covector(&r[..16].try_into().unwrap());
            let base=model.solve(y,z,Budget::default()).unwrap();
            for amplitude in[0.,0.001,-0.001,0.01,-0.01]{
                let seed=z.advanced(std::array::from_fn(|k|if k%2==0{amplitude}else{-amplitude}));
                let solution=model.solve(y,seed,Budget::default()).unwrap();solves+=1;max_iter=max_iter.max(solution.iterations);
                residual_a=residual_a.max(solution.residual_a);correction_v=correction_v.max(solution.correction_v);
                let err=distance(solution.nodes,now);solved_v=solved_v.max(err);assert!(err<=2e-9,"stage {stages} seed {amplitude} reconstructed error {err}");
                for k in 0..9{let d=(solution.reaction[k]-original[7+k]).abs();reaction_a=reaction_a.max(d);assert!(d<=20e-12);}
                let kcl=solution.source.iter().sum::<f64>()+solution.reaction[3..].iter().sum::<f64>();conservation_a=conservation_a.max(kcl.abs());assert!(kcl.abs()<=20e-12);
                for col in 0..9{let sum=solution.source_j.iter().map(|r|r[col]).sum::<f64>()+solution.reaction_j[3..].iter().map(|r|r[col]).sum::<f64>();conservation_s=conservation_s.max(sum.abs());assert!(sum.abs()<=2e-9);}
            }
            let q=charge(delta,dt).unwrap();let mut physical_q=[0.;16];let mut physical_m=[[0.;16];16];let mut ground=0.;
            for(a,b,c)in OWNED_CAPACITORS{
                let(h,l)=if b==16{(delta.high[a],delta.low[a])}else{let(h,l)=add_pair(delta.high[a],delta.low[a],-delta.high[b]);add_pair(h,l,-delta.low[b])};
                let g=c/dt;let current=g*(h+l);physical_q[a]+=current;if b==16{ground-=current;}else{physical_q[b]-=current;}
                for(row,sr)in[(a,1.),(b,-1.)]{for(col,sc)in[(a,1.),(b,-1.)]{if row<16&&col<16{physical_m[row][col]+=sr*sc*g;}}}
            }
            let transformed=covector(&physical_q);let tm=congruence(&physical_m);
            for k in 0..7{assert_eq!(transformed[k],0.);for i in 0..16{assert_eq!(tm[k][i],0.);assert_eq!(tm[i][k],0.);}}
            for a in 0..9{charge_a=charge_a.max((q.current_a[a]-transformed[7+a]).abs());for b in 0..9{mass_s=mass_s.max((q.mass_s[a][b]-tm[7+a][7+b]).abs());}}
            assert_eq!(q.ground_a,ground);assert_eq!(charge_a,0.);assert_eq!(mass_s,0.);
            let chain_delta=get_chain(1+stage);let all=chain::linearize_prevalidated::<true>(parent,[0.;5],get_chain(0),chain_delta,dt,get_chain(3+stage)).unwrap();
            // Assemble independently from the frozen parent's ledger, including C10.
            // The nominal scene has no R21 endpoint alias and positive R14+R30 series.
            let boundary=lab::controlled_boundary(0,true);
            assert!(boundary.r14_ohm.unwrap()+1330.-p.r30_ohm>0.);
            assert!(boundary.recovery.vca.second.output.output.r21_lower_ohm>0.&&boundary.recovery.vca.second.output.output.r21_lower_ohm<5000.);
            let mut all_q=[0.;68];let mut all_m=[[0.;68];68];let mut outer_q=[0.;68];let mut outer_m=[[0.;68];68];
            for(n,(a,b,c))in chain::CAPACITORS.into_iter().chain([(67,7,10e-6)]).enumerate(){
                let(h,l)=if b==68{(chain_delta.high[a],chain_delta.low[a])}else{let(h,l)=add_pair(chain_delta.high[a],chain_delta.low[a],-chain_delta.high[b]);add_pair(h,l,-chain_delta.low[b])};
                let g=c/dt;let i=g*(h+l);
                for(r,sign)in[(a,1.),(b,-1.)]{if r<68{all_q[r]+=sign*i;if n>=5{outer_q[r]+=sign*i;}for(col,slope)in[(a,g),(b,-g)]{if col<68{all_m[r][col]+=sign*slope;if n>=5{outer_m[r][col]+=sign*slope;}}}}}
            }
            for a in 0..68{assert_eq!(all_q[a].to_bits(),all.charge_over_h[a].to_bits());for b in 0..68{assert_eq!(all_m[a][b].to_bits(),all.mass_over_h[a][b].to_bits());}}
            for a in 0..16{parent_charge_a=parent_charge_a.max((all.charge_over_h[a]-outer_q[a]-physical_q[a]).abs());for b in 0..16{parent_mass_s=parent_mass_s.max((all.mass_over_h[a][b]-outer_m[a][b]-physical_m[a][b]).abs());}}
            assert!(parent_charge_a<=20e-12&&parent_mass_s<=2e-9);parent_checks+=1;
            if stages%6==0{
                for col in 0..16{
                    let(mut zp,mut zm,mut yp,mut ym)=(z,z,y,y);
                    if col<7{let mut step=[0.;7];step[col]=1e-6;zp=z.advanced(step);step[col]=-1e-6;zm=z.advanced(step);}
                    else{let mut step=[0.;9];step[col-7]=1e-6;yp=y.advanced(step);step[col-7]=-1e-6;ym=y.advanced(step);}
                    let plus=model.evaluate(zp,yp).unwrap();let minus=model.evaluate(zm,ym).unwrap();
                    for k in 0..16{let fd=(plus.f[k]-minus.f[k])/2e-6;let frac=(fd-e.j[k][col]).abs()/(2e-9+2e-5*fd.abs());direct_fd_fraction=direct_fd_fraction.max(frac);assert!(frac<=1.,"direct transformed FD {k},{col}: {frac}");}
                    direct_fd_columns+=1;
                }
                for col in 0..9{
                    let mut step=[0.;9];step[col]=1e-6;let plus=model.solve(y.advanced(step),base.z,Budget::default()).unwrap();step[col]=-1e-6;
                    let minus=model.solve(y.advanced(step),base.z,Budget::default()).unwrap();
                    for k in 0..9{let fd=(plus.reaction[k]-minus.reaction[k])/2e-6;let frac=(fd-base.reaction_j[k][col]).abs()/(2e-9+2e-5*fd.abs());fd_fraction=fd_fraction.max(frac);assert!(frac<=1.,"reaction FD stage {stages} {k},{col}: {frac}");}
                    for k in 0..2{let fd=(plus.source[k]-minus.source[k])/2e-6;let frac=(fd-base.source_j[k][col]).abs()/(2e-9+2e-5*fd.abs());source_fraction=source_fraction.max(frac);assert!(frac<=1.,"source FD {frac}");}
                    for k in 0..16{
                        let fd=((plus.nodes.high[k]-minus.nodes.high[k])+(plus.nodes.low[k]-minus.nodes.low[k]))/2e-6;
                        let analytic=T[k][7+col]+(0..7).map(|a|T[k][a]*base.dz_dy[a][col]).sum::<f64>();
                        let frac=(fd-analytic).abs()/(2e-5+2e-5*fd.abs());dx_fraction=dx_fraction.max(frac);assert!(frac<=1.,"dx FD {frac}");
                    }
                    fdcols+=1;solves+=2;
                }
            }
            if stages==0{
                invalid=guards(model,y,z,dt,delta);
                for field in 0..6{for value in[f64::NAN,f64::INFINITY,f64::NEG_INFINITY,0.,-1.]{let mut q=p;match field{0=>q.ladder_transistor.transistor_is_a=value,1=>q.ladder_transistor.beta_forward=value,2=>q.ladder_transistor.beta_reverse=value,3=>q.ladder_transistor.temperature_k=value,4=>q.r61_ohm=value,_=>q.r30_ohm=value};assert!(Model::new(q).is_err());equal(&base,&model.solve(y,z,Budget::default()).unwrap());invalid_p+=1;}}
                for(r61,r30)in[(200.,330.),(200.,1330.),(200000.,830.)]{let mut q=p;q.r61_ohm=r61;q.r30_ohm=r30;assert!(Model::new(q).is_ok());}
                // Independent LU swap/fill and multiple RHS checks.
                let a=std::array::from_fn(|i|std::array::from_fn(|j|if i==j{2.+i as f64}else{((i+2*j)%5)as f64/10.}));
                let mut a=a;a.swap(0,6);let factor=Factor::new(a).unwrap();
                for col in 0..8{let expected:[f64;7]=std::array::from_fn(|k|if col==7{(k as f64-3.)/7.}else if k==col{1.}else{0.});let rhs=std::array::from_fn(|i|(0..7).map(|j|a[i][j]*expected[j]).sum());let got=factor.solve(rhs).unwrap();for k in 0..7{assert!((got[k]-expected[k]).abs()<=2e-12);}}
                // Same HIGH, opposite LOW: the capacitor delta must not disappear.
                let mut cancellation=Nodes{high:[0.;16],low:[0.;16]};
                cancellation.high[8]=1.;cancellation.high[12]=1.;cancellation.low[8]=2_f64.powi(-54);cancellation.low[12]=-2_f64.powi(-54);
                let cq=charge(cancellation,dt).unwrap();assert_eq!(cq.current_a[0],68e-9/dt*2_f64.powi(-53));assert!(cq.current_a[0]>0.);
                let(cz,cy)=coordinates(cancellation).unwrap();assert_eq!(distance(reconstruct(cz,cy).unwrap(),cancellation),0.);
                for legal_h in[MIN_DT_S,1e-3]{assert!(charge(cancellation,legal_h).is_ok());}
            }
            heap+=ALLOCS.load(Ordering::Relaxed)-start;
            let _=e;stages+=1;
        }
    }
    assert_eq!(stages,48);assert_eq!(heap,0);
    println!("LOCAL,{stages},{solves},{fdcols},{max_iter},{invalid},{invalid_p},{heap},{dc_fraction:.17e},{jac_fraction:.17e},{reconstructed_v:.17e},{solved_v:.17e},{reaction_a:.17e},{fd_fraction:.17e},{dx_fraction:.17e},{source_fraction:.17e},{conservation_a:.17e},{conservation_s:.17e},{charge_a:.17e},{mass_s:.17e},{residual_a:.17e},{correction_v:.17e},{parent_checks},{direct_fd_columns},{direct_fd_fraction:.17e},{parent_charge_a:.17e},{parent_mass_s:.17e},1,8,2");
}
