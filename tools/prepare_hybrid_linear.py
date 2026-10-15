"""Derive solver profiling variants without changing admitted circuit code."""
import base64, subprocess
from prepare_dual_chain import ROOT, sha, write
from prepare_hybrid_stamp import once

def derive():
    solver=(ROOT/'crates/rf-d-circuit/src/hybrid_schur_solver.rs').read_text(encoding='utf8')
    solver=once(solver,'pub struct Workspace{','pub struct Workspace{pub profile:[u128;7],')
    solver=once(solver,'Self{contour:Block::new()', 'Self{profile:[0;7],contour:Block::new()')
    # Mutually exclusive measured sections: CSR, factorization, triangular solves,
    # compensated residual. Profiling is compiled out for the cost comparison.
    solver=once(solver,'        self.sparse.initialize(j)?;', '''        #[cfg(timings)] let start=std::time::Instant::now();
        self.sparse.initialize(j)?;
        #[cfg(timings)] {self.profile[2]+=start.elapsed().as_nanos();}
        #[cfg(timings)] let start=std::time::Instant::now();''')
    solver=once(solver,'self.outer.factor()','''self.outer.factor()?;
        #[cfg(timings)] {self.profile[3]+=start.elapsed().as_nanos();} Ok(())''')
    solver=once(solver,'let mut d=self.correction(j,b)?;let(mut r,mut metric)=self.sparse.residual(&b,&d)?;let initial=metric;', '''#[cfg(timings)] let start=std::time::Instant::now();
        let mut d=self.correction(j,b)?;
        #[cfg(timings)] {self.profile[4]+=start.elapsed().as_nanos();}
        #[cfg(timings)] let start=std::time::Instant::now();
        let(mut r,mut metric)=self.sparse.residual(&b,&d)?;let initial=metric;
        #[cfg(timings)] {self.profile[5]+=start.elapsed().as_nanos();}''')
    solver=once(solver,'let e=self.correction(j,r)?;for k in 0..M{d[k]+=e[k];}', '''#[cfg(timings)] let start=std::time::Instant::now();
            let e=self.correction(j,r)?;for k in 0..M{d[k]+=e[k];}''')
    solver=once(solver,'let(rr,next)=self.sparse.residual(&b,&d)?;', '''let(rr,next)=self.sparse.residual(&b,&d)?;
            #[cfg(timings)] {self.profile[6]+=start.elapsed().as_nanos();}''')
    voice=(ROOT/'crates/rf-d-circuit/src/prepared_hybrid_voice.rs').read_text(encoding='utf8')
    voice=once(voice,'hybrid_schur_solver.rs','profiled_hybrid_solver.rs')
    voice=once(voice,'let (r, j, stages) = system(d)?;', '''#[cfg(timings)] let start=std::time::Instant::now();
        let ss=evaluate(d)?;
        #[cfg(timings)] {w.profile[0]+=start.elapsed().as_nanos();}
        #[cfg(timings)] let start=std::time::Instant::now();
        let (r,j,stages)=(residual(&ss),jacobian(&ss),[ss[0].now,ss[1].now]);
        #[cfg(timings)] {w.profile[1]+=start.elapsed().as_nanos();}''')
    probe=(ROOT/'tools/hybrid_stamp_probe.rs').read_text(encoding='utf8')
    probe=once(probe,'hybrid_schur_voice.rs','prepared_hybrid_voice.rs')
    probe=once(probe,'#[path="../crates/rf-d-circuit/src/prepared_hybrid_voice.rs"] mod circuit;\n#[path=', '#[path="../crates/rf-d-circuit/src/profiled_hybrid_voice.rs"] mod circuit;\n#[path=')
    probe=once(probe,'    assert_eq!(heap,0);','''    #[cfg(timings)] {write!(w,"PROFILE").unwrap();for n in workspace.profile{write!(w,",{n}").unwrap();}writeln!(w).unwrap();}
    assert_eq!(heap,0);''')
    return {'crates/rf-d-circuit/src/profiled_hybrid_solver.rs':solver,'crates/rf-d-circuit/src/profiled_hybrid_voice.rs':voice,'tools/hybrid_linear_probe.rs':probe}

def main():
    write(ROOT/'evidence/hybrid_linear_before01.json',dict(base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),previous_qa='evidence/hybrid_stamp_tests01.json',previous_qa_sha256=sha(ROOT/'evidence/hybrid_stamp_tests01.json'),mutable_original_b64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in ['.gitattributes','README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']}))
    for n,s in derive().items():
        p=ROOT/n;assert not p.exists();p.write_text(s,encoding='utf8',newline='\n')
if __name__=='__main__':main()
