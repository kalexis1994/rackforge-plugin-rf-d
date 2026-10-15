"""Only skip zero coefficients of the current pivot row, including actual fill."""
from prepare_dual_chain import ROOT
from prepare_hybrid_stamp import once
def derive():
    prefix='crates/rf-d-circuit/src/'
    s=(ROOT/(prefix+'direct_hybrid_solver.rs')).read_text(encoding='utf8')
    old='let(head,tail)=self.lu.a.split_at_mut(col+1);let row=&head[col];let upper=self.border[col];'
    s=once(s,old,old+'''
            // Inspect the current pivot row after all previous fill and swaps.
            let mut columns=[0_usize;N];let mut count=0;
            for k in col+1..end{if row[k]!=0.{columns[count]=k;count+=1;}}
''')
    for old,new in [('for k in col+1..end{current[k]-=factor*row[k];}','for k in columns[..count].iter().copied(){current[k]-=factor*row[k];}'),('for k in col+1..end{self.cross[p][k]-=factor*row[k];}','for k in columns[..count].iter().copied(){self.cross[p][k]-=factor*row[k];}')]:s=once(s,old,new)
    v=(ROOT/(prefix+'direct_hybrid_voice.rs')).read_text(encoding='utf8');v=once(v,'#[path="direct_hybrid_solver.rs"]','#[path="support_pivot_solver.rs"]')
    p=(ROOT/'tools/split_ladder_probe.rs').read_text(encoding='utf8');p=once(p,'src/split_ladder_voice.rs','src/support_pivot_voice.rs')
    local=(ROOT/'tools/hybrid_direct_local.rs').read_text(encoding='utf8');local=once(local,'src/direct_hybrid_voice.rs','src/support_pivot_voice.rs');local=once(local,'println!("DIRECT,','println!("SUPPORT,')
    local=once(local,'assert_eq!(got[0][column],j[0][column]+1e-20);retry', '''assert_eq!(got[0][column],j[0][column]+1e-20);
  let fresh=w.solve(input,B,rhs).unwrap();let previous=control.solve(&got,rhs).unwrap();for k in 0..M{assert_eq!(fresh[k].to_bits(),previous[k].to_bits());}
  retry''')
    local=once(local,'   let zero=[[0.;N];N];', '''   // A row swap creates fill that was absent in the input support.
   let mut fill=[[0.;N];N];for k in 0..N{fill[k][k]=1.;}
   for (i,row) in [[0.,2.,1.],[1.,0.,3.],[4.,1.,0.]].into_iter().enumerate(){fill[i][..3].copy_from_slice(&row);}
   let zero_mass=[[0.;N];N];let input=[direct::Stage{dc:&fill,mass:&zero_mass};2];
   let matrix=w.coefficients(input,B).unwrap();let d=w.solve(input,B,rhses[7]).unwrap();let previous=control.solve(&matrix,rhses[7]).unwrap();
   for k in 0..M{assert_eq!(d[k].to_bits(),previous[k].to_bits());}retry(&mut w,&s,rhs,expected);
   let zero=[[0.;N];N];''')
    return {prefix+'support_pivot_solver.rs':s,prefix+'support_pivot_voice.rs':v,'tools/support_pivot_probe.rs':p,'tools/support_pivot_local.rs':local}
def main():
    for n,s in derive().items():assert not (ROOT/n).exists();(ROOT/n).write_text(s,encoding='utf8',newline='\n')
if __name__=='__main__':main()
