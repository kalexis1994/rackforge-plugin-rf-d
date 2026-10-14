"""Derive exact zero traversal from the admitted loaded public family."""
import base64,json,struct,subprocess
from prepare_vco1_portable import ROOT,sha,write
from prepare_release_voice import once
from prepare_voice_pivot import bank as old_bank
from joint_cycles_analysis import require
RUST=['tools/zero_voice_solver.rs','tools/zero_voice_kernel.rs','tools/zero_baseline_solver.rs','tools/zero_baseline_kernel.rs','tools/zero_voice_bench.rs']
ATTR=('\n'+''.join('/'+n+' text eol=lf\n' for n in RUST)).encode()
def solver():
 s=(ROOT/'crates/rf-d-circuit/src/block_decay_solver.rs').read_text(encoding='utf8')
 s=once(s,'struct Lu<const N:usize>{a:[[f64;N];N],perm:[usize;N]}','struct Lu<const N:usize>{a:[[f64;N];N],perm:[usize;N],columns:[[u16;N];N],lower:[usize;N],length:[usize;N]}')
 s=once(s,'if a.iter().flatten().any(|v|!v.is_finite()){return Err(StepError::SingularJacobian);}Ok(())','''if a.iter().flatten().any(|v|!v.is_finite()){return Err(StepError::SingularJacobian);}
  for row in 0..N{let mut count=0;let mut lower=0;for col in 0..N{if col!=row&&a[row][col]!=0.{self.columns[row][count]=col as u16;count+=1;if col<row{lower+=1;}}}self.lower[row]=lower;self.length[row]=count;}Ok(())''')
 a=s.index('  let mut x=[0.;N];for row');b=s.index('\n  if x.iter().any',a)
 s=s[:a]+'''  let mut x=[0.;N];for row in 0..N{let mut v=b[self.perm[row]];let mut start=0;for &col in &self.columns[row][..self.lower[row]]{let col=col as usize;if v==0.{for k in start..col{v-=self.a[row][k]*x[k];}}v-=self.a[row][col]*x[col];start=col+1;}if v==0.{for k in start..row{v-=self.a[row][k]*x[k];}}if !v.is_finite(){return Err(StepError::SingularJacobian);}x[row]=v;}
  for row in(0..N).rev(){let mut v=x[row];let mut start=row+1;for &col in &self.columns[row][self.lower[row]..self.length[row]]{let col=col as usize;if v==0.{for k in start..col{v-=self.a[row][k]*x[k];}}v-=self.a[row][col]*x[col];start=col+1;}if v==0.{for k in start..N{v-=self.a[row][k]*x[k];}}x[row]=v/self.a[row][row];if !x[row].is_finite(){return Err(StepError::SingularJacobian);}}'''+s[b:]
 # Fixed storage; no allocation or support cache across different matrices.
 import re
 s,n=re.subn(r'Lu\{a:\[\[0\.;(\d+)\];\1\],perm:\[0;\1\]\}',lambda m:'Lu{a:[[0.;'+m[1]+'];'+m[1]+'],perm:[0;'+m[1]+'],columns:[[0;'+m[1]+'];'+m[1]+'],lower:[0;'+m[1]+'],length:[0;'+m[1]+']}',s);require(n==5,'all fixed LU initializers')
 old='for i in 0..458{self.row[i]=n;for k in 0..458{let a=j[i][k];if !a.is_finite(){return Err(StepError::InvalidInput);}if a==0.{continue;}if n==CAPACITY{return Err(StepError::InvalidInput);}self.column[n]=k as u16;self.value[n]=a;self.floor[i]+=a.abs()*tau(k);n+=1;}}'
 new='for i in 0..458{self.row[i]=n;for(block,values)in j[i].chunks(8).enumerate(){if values.iter().all(|v|*v==0.){continue;}for(offset,&a)in values.iter().enumerate(){let k=8*block+offset;if !a.is_finite(){return Err(StepError::InvalidInput);}if a==0.{continue;}if n==CAPACITY{return Err(StepError::InvalidInput);}self.column[n]=k as u16;self.value[n]=a;self.floor[i]+=a.abs()*tau(k);n+=1;}}}'
 return once(s,old,new)
def probe(s,candidate):
 init='Lu{a:j,perm:[0;4]'+(',columns:[[0;4];4],lower:[0;4],length:[0;4]' if candidate else '')+'}'
 return s+'''\n/// Laboratory-only access to private substitution, excluded from public source.
pub fn rhs_probe(j:[[f64;4];4],b:[f64;4])->Result<[u64;4],StepError>{let mut lu='''+init+''';lu.factor_in_place()?;Ok(lu.solve(b)?.map(f64::to_bits))}
pub fn scratch_bytes()->usize{std::mem::size_of::<Prepared>()}
'''
def kernel(path):
 s=(ROOT/'crates/rf-d-circuit/src/block_decay_voice.rs').read_text(encoding='utf8')
 s=once(s,'#[path="block_decay_solver.rs"]',f'#[path="{path}"]')
 for n in ['conditioned_voice_latch.rs','decay_contour.rs']:s=s.replace(f'#[path="{n}"]',f'#[path="../crates/rf-d-circuit/src/{n}"]')
 return s
def bank():
 raw,paths=old_bank();records=[raw[12:]]
 for maximum in [1048576,524288]:
  n=f'references-local/extended-release01/{maximum}/selected.txt';paths.append(n);lines=(ROOT/n).read_text(encoding='utf8').splitlines()
  for i,l in enumerate(lines):
   if l.startswith('JOINT_ROOT,'):
    _,mask,h,res,corr=l.split(',');require(mask=='0','loaded own scene');states=[list(map(float,x.split(',')[1:])) for x in lines[i+1:i+6]];require(all(len(s)==458 for s in states),'root widths');records.append(struct.pack('<2d458d1834d2Q',1000.,float(h),*states[0],*[v for s in states[1:] for v in s],float(res),float(corr),2**64-1,2**64-1))
 require(len(records)==91,'90 new selected pairs');return b'RFPIVT01'+struct.pack('<I',168)+b''.join(records),paths
def main():
 old=json.loads((ROOT/'evidence/voice_extended_tests01.json').read_text(encoding='utf8'));head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();require(old['passed'] and head=='ca7e574e7b647b16735215ffb64aa76e7be679a2','admitted base');require(not (ROOT/'evidence/voice_zero_before01.json').exists(),'exclusive experiment');mutable=['.gitattributes','README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md','crates/rf-d-circuit/src/lib.rs'];write('evidence/voice_zero_before01.json',dict(base_commit=head,previous_qa_sha256=sha(ROOT/'evidence/voice_extended_tests01.json'),mutable_before_base64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in mutable}))
 sources={RUST[0]:probe(solver(),True),RUST[1]:kernel('zero_voice_solver.rs'),RUST[2]:probe((ROOT/'crates/rf-d-circuit/src/block_decay_solver.rs').read_text(encoding='utf8'),False),RUST[3]:kernel('zero_baseline_solver.rs')}
 for n,s in sources.items():require(not (ROOT/n).exists(),'exclusive source');(ROOT/n).write_text(s,encoding='utf8',newline='\n')
 p=ROOT/'.gitattributes';p.write_bytes(p.read_bytes()+ATTR);data,paths=bank();work=ROOT/'references-local/voice-zero-inputs01';work.mkdir();(work/'pairs.bin').write_bytes(data)
 for n in paths:require(sha(ROOT/n)==old['private_input_sha256'][n],'protected own bank input')
 write('evidence/voice_zero_inputs01.json',dict(passed=True,source_sha256={n:sha(ROOT/n) for n in ['tools/prepare_zero_voice.py','docs/VOZ_CEROS_PROTOCOLO.md',*sources]},private_used_sha256={n:sha(ROOT/n) for n in paths},outputs=[dict(path='references-local/voice-zero-inputs01/pairs.bin',sha256=sha(work/'pairs.bin'),bytes=len(data))],pairs=168,record_bytes=18368,new_pairs=90,median_ratio_gate=.95,worst_round_ratio_gate=1.05))
 print('ZERO_INPUTS',168,len(data))
if __name__=='__main__':main()
