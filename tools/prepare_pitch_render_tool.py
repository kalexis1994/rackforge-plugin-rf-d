"""Derive publication wrapper, preserving nominal process/IO failure handling."""
from prepare_dual_chain import ROOT
from prepare_pitch_program import replace_once as r

def image():
    s=(ROOT/'tools/render_nominal.py').read_text(encoding='utf8')
    s=r(s,'Render the admitted 300 ms scene, then atomically publish its single current WAV.','Render experimental Hz transposition; publish only the admitted fine-scene hash.')
    s=r(s,"REFERENCE='evidence/long_note_aa_listening01.json'","REFERENCE='evidence/pitch_render_listening01.json'")
    s=r(s,'tmp/nominal-render-current.json','tmp/pitch-render-current.json')
    s=r(s,"str(ROOT/'tools/nominal_render_main.rs')","str(ROOT/'tools/pitch_render_main.rs')")
    a=s.index('def parse_complete(raw):');b=s.index('\ndef render(',a)
    s=s[:a]+'''def parse_complete(raw):
    from check_pitch_render import parse_complete as parse
    m=parse(raw);reference=json.loads((ROOT/REFERENCE).read_text(encoding='utf8'));assert reference['passed']
    assert m['complete'][:9]==reference['complete'][:9]
    assert struct.pack('<236d',*m['state'])==struct.pack('<236d',*reference['final_state'])
    return m

'''+s[b:]
    s=r(s,"names=['tools/render_nominal.py','tools/nominal_render_main.rs','crates/rf-d-circuit/src/nominal_render.rs','docs/NOMINAL_RENDER_PROTOCOLO.md']","names=['tools/render_pitch.py','tools/pitch_render_main.rs','crates/rf-d-circuit/src/pitch_program_render.rs','docs/PITCH_RENDER_PROTOCOLO.md',REFERENCE]")
    s=r(s,"str(quota),'300'","str(quota),'0.5','render'")
    s=r(s,'Render nominal de 300 ms, perfil fino 1 us; un unico WAV actual. Ctrl+C cancela entre cuotas.','Transposicion experimental Hz de 300 ms, perfil fino 0.5 us; un unico WAV actual. Ctrl+C cancela entre cuotas.')
    s=s.replace('.read_text())',".read_text(encoding='utf8'))")
    return s

def main():
    p=ROOT/'tools/render_pitch.py';s=image()
    if p.exists():assert p.read_bytes()==s.encode()
    else:p.write_text(s,encoding='utf8',newline='\n')
if __name__=='__main__':main()
