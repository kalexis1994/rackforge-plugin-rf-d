"""Documentary inventory of the frozen conditional VCO1 oracle (not Rust)."""
from pathlib import Path
from vco1_circuit_reference import netlist, Scenario, ROOT
import lm741_reference as op

def inventory(s=Scenario()):
 text, provenance=netlist(s,Path('C:/rf_vco1_inventory.txt'))
 lines=[]
 for line in text.splitlines()[1:]:
  if line.startswith('.control'):break
  if not line or line[0].upper() not in 'RCVIQJX':continue
  lines.append(line.upper().split())
 nodes=sorted({n for w in lines for n in (w[1:6] if w[0][0]=='X' else w[1:4] if w[0][0] in 'QJ' else w[1:3]) if n!='0'})
 if len(nodes)!=56 or len(lines)!=100:raise ValueError('frozen board inventory')
 vs=[w for w in lines if w[0][0]=='V' and w[0] not in ('VR8_HIGH','VR8_LOW','VR11_ACTIVE')];amps=[w for w in lines if w[0][0]=='X']
 trims=['RR8_HIGH','RR8_LOW','RR11_ACTIVE']
 # Always retain three trim-current unknowns, including exact zero-ohm contacts.
 names=nodes+[w[0]+'.'+str(n) for w in amps for n in op.NODES[5:]]
 names+=['I('+w[0]+')' for w in vs]
 names+=[w[0]+'.I('+n+')' for w in amps for n in op.V_NAMES+op.L_NAMES]
 names+=['I('+n+')' for n in trims]
 def ix(n):return 134 if n=='0' else nodes.index(n)
 maps=[]
 for k,w in enumerate(amps):maps.append([*[ix(n) for n in w[1:6]],*range(56+21*k,77+21*k),*range(109+11*k,120+11*k)])
 if len(names)!=134 or len(vs)!=11 or len(maps)!=2:raise ValueError('frozen expanded MNA')
 return dict(lines=lines,nodes=nodes,names=names,opamp_maps=maps,provenance=provenance)

def rust_data():
 inv=inventory();lines=inv['lines'];nodes=inv['nodes'];ix=lambda n:134 if n=='0' else nodes.index(n)
 out=['// Generated from SVC-9 p.5/p.19 and vco1_circuit_reference.py; see protocol.',
      'pub const NV: usize = 98;','pub const N: usize = 134;','pub const GROUND: usize = N;']
 out.append('pub const NAMES: [&str;N] = ['+','.join('"'+n+'"' for n in inv['names'])+'];')
 def arr(name,typ,items):out.append('pub(crate) const '+name+': ['+typ+';'+str(len(items))+'] = ['+','.join(items)+'];')
 trims={'RR8_HIGH','RR8_LOW','RR11_ACTIVE'}
 arr('RESISTORS','(usize,usize,f64)',[f'({ix(w[1])},{ix(w[2])},{float(w[3])!r})' for w in lines if w[0][0]=='R' and w[0] not in trims])
 arr('CAPACITORS','(usize,usize,f64)',[f'({ix(w[1])},{ix(w[2])},{float(w[3])!r})' for w in lines if w[0][0]=='C'])
 arr('TRANSISTORS','(bool,[usize;4])',[f'({str(w[4]=="LAB_PNP").lower()},[{ix(w[1])},{ix(w[2])},{ix(w[3])},134])' for w in lines if w[0][0]=='Q'])
 arr('JFETS','[usize;3]',[str([ix(n) for n in w[1:4]]) for w in lines if w[0][0]=='J'])
 arr('VOLTAGES','(usize,usize,f64)',[f'({ix(w[1])},{ix(w[2])},{float(w[3])!r})' for w in lines if w[0][0]=='V'])
 arr('TRIMS','(usize,usize)',[f'({ix(w[1])},{ix(w[2])})' for n in ('RR8_HIGH','RR8_LOW','RR11_ACTIVE') for w in lines if w[0]==n])
 arr('OPAMPS','[usize;37]',[str(m) for m in inv['opamp_maps']])
 return '\n'.join(out)+'\n'

if __name__=='__main__':
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');a=ap.parse_args()
 p=ROOT/'crates/rf-d-circuit/src/vco1_stamp_data.rs';data=rust_data().encode()
 if a.check:
  if p.read_bytes()!=data:raise ValueError('generated physical incidence changed')
 else:
  if p.exists():raise ValueError('preserve generated inventory')
  p.write_bytes(data)
 print('VCO1 inventory: 100 board devices, 2 x 41 LM741 devices, 134 unknowns')
