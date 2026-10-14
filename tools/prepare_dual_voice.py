"""Bind the existing VCO and loaded dual chain; derive a three-block Schur map."""
import base64,json,re,subprocess
from prepare_dual_chain import ROOT,sha,write
def generate_chain():
    s=(ROOT/'crates/rf-d-circuit/src/dual_chain.rs').read_text(encoding='utf8')
    s=s[:s.index('pub fn gaussian')]
    a='OnMixer::new([true,false,false,false,false],[0.5;4])';assert s.count(a)==1
    s=s.replace(a,'OnMixer::new([false;5],[0.5;4])')
    a=s.index('pub fn sources(');b=s.index('\npub fn parts',a)
    s=s[:a]+'pub fn sources(_t:f64)->[f64;5]{[0.;5]}'+s[b:]
    return '//! Generated chain binding: OSC1 belongs to VCO; BUS is shared.\n'+s
def generate_solver():
    s=(ROOT/'crates/rf-d-circuit/src/block_decay_solver.rs').read_text(encoding='utf8')
    def constant(name,value):
        nonlocal s
        s,count=re.subn(r'const '+name+r':[^;]+;[^=]*=\[.*?\];',value,s,count=1)
        # Array declarations contain semicolons; replace line by exact name instead.
    lines=s.splitlines()[1:];replacements={}
    inner=[];ports=[]
    for a,b in [(list(range(56,77))+list(range(108,119)),[8,9,None,14,7]),(list(range(77,98))+list(range(119,130)),[35,15,19,14,10])]:
        inner.append(a+[k+250 for k in a]);ports.append(b+[None if k is None else k+250 for k in b])
    chain=list(range(133,250));chain+= [k+250 for k in chain]
    ext=list(range(56))+list(range(98,108))+list(range(130,133));ext+= [k+250 for k in ext]
    def arr(x):return '['+','.join(arr(v) if isinstance(v,list) else 'usize::MAX' if v is None else str(v) for v in x)+']'
    for name,typ,value in [('INNER','[[usize;64];2]',inner),('PORTS','[[usize;10];2]',ports),('CHAIN','[usize;234]',chain),('CHAIN_PORTS','[usize;2]',[12,262]),('EXTERNAL','[usize;138]',ext)]:
        replacements[name]='const '+name+':'+typ+'='+arr(value)+';'
    result=[]
    for line in lines:
        if line.startswith('const CONTOUR'):continue
        name=next((n for n in replacements if line.startswith('const '+n+':')),None)
        result.append(replacements[name] if name else line)
    s='\n'.join(result)+'\n'
    # Remove only the former separately condensed contour; it is inside CHAIN now.
    for text in [',contour:Lu<58>,contour_response:[[f64;2];58]',',contour:Lu{a:[[0.;58];58],perm:[0;58]},contour_response:[[0.;2];58]']:
        assert s.count(text)==1,text;s=s.replace(text,'')
    s='\n'.join(line for line in s.splitlines() if not line.lstrip().startswith(('for r in 0..58','for k in 0..2{let p=CONTOUR','for &p in &CONTOUR','for i in 0..58')))+'\n'
    s=s.replace('let uc=self.contour.solve(CONTOUR.map(|k|b[k]))?;','')
    s='\n'.join(line if any(line.startswith('const '+n+':') for n in replacements) else re.sub(r'\b(458|459|229|132|140)\b',lambda m:{'458':'500','459':'501','229':'250','132':'234','140':'138'}[m[0]],line) for line in s.splitlines())+'\n'
    # Only CHAIN has two ports; LM741s still have ten.
    s=s.replace('[[f64;4];234]','[[f64;2];234]').replace('[[0.;4];234]','[[0.;2];234]')
    s=s.replace('for k in 0..4','for k in 0..2').replace('CAPACITY:usize=4096','CAPACITY:usize=8192')
    # Rebuild incidence masks/audit without the former contour block.
    a=s.index('const fn structural_masks()')
    s=s[:a]+'''const fn structural_masks()->([u8;500],[u8;500]){let mut owner=[0_u8;500];let mut allowed=[0_u8;500];let mut group=0;while group<2{let bit=1<<group;let mut i=0;while i<64{let k=INNER[group][i];owner[k]|=bit;allowed[k]|=bit;i+=1;}i=0;while i<10{let k=PORTS[group][i];if k!=usize::MAX{allowed[k]|=bit;}i+=1;}group+=1;}let mut i=0;while i<234{let k=CHAIN[i];owner[k]|=4;allowed[k]|=4;i+=1;}i=0;while i<2{allowed[CHAIN_PORTS[i]]|=4;i+=1;}(owner,allowed)}
const OWNER:[u8;500]=structural_masks().0;const ALLOWED:[u8;500]=structural_masks().1;
'''
    assert 'CONTOUR' not in s and 'contour' not in s
    assert sorted(sum(inner,[])+chain+ext)==list(range(500))
    return '//! Generated two LM741 blocks plus complete loaded dual chain; no coefficient drop.\n'+s
def main():
    before=ROOT/'evidence/dual_voice_before01.json';assert not before.exists()
    qa='evidence/dual_chain_tests01.json'
    write(before,dict(base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),previous_qa=qa,previous_qa_sha256=sha(ROOT/qa),mutable_original_b64={n:base64.b64encode((ROOT/n).read_bytes()).decode() for n in ['.gitattributes','README.md','docs/PLAN.md','docs/MATRIZ_DE_FIDELIDAD.md']}))
    for n,s in [('dual_voice_chain.rs',generate_chain()),('dual_voice_solver.rs',generate_solver())]:
        p=ROOT/'crates/rf-d-circuit/src'/n;assert not p.exists();p.write_text(s,encoding='utf8',newline='\n')
    print('DUAL_VOICE_PREPARED')
if __name__=='__main__':main()
