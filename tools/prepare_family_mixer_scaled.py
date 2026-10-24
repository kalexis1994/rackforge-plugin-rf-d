"""Exact passive-coordinate source derivation; no active card or tolerance change."""
import difflib
from prepare_dual_chain import ROOT,write,sha
def main():
    origin='tools/check_family_mixer_oracle.py';out='tools/family_mixer_scaled_oracle.py';a=(ROOT/origin).read_text(encoding='utf8');b=a
    changes=[("'C27_port MIX_BUS_BOARD4_PIN4 BASE_Q29_boundary 1e-5'","'C27_state C27_STATE 0 1e-9','Ecap MIX_BUS_BOARD4_PIN4 BASE_Q29_boundary C27_STATE 0 .01','Fcap C27_STATE 0 Ecap -.01'"),('v(MIX_BUS_BOARD4_PIN4)={start:.17e}','v(C27_STATE)={start/.01:.17e}'),('family_mixer_windows02.xz','family_mixer_scaled_windows01.xz'),("OWN=['tools/check_family_mixer_oracle.py'","OWN=['tools/family_mixer_scaled_oracle.py','docs/FAMILIA_MIXER_COORDENADA.md','tools/check_family_mixer_oracle.py'"),('family_mixer_oracle02.json','family_mixer_scaled_oracle01.json')]
    for x,y in changes:assert b.count(x)==1,(x,b.count(x));b=b.replace(x,y,1)
    p=ROOT/out;assert not p.exists();p.write_text(b,encoding='utf8',newline='\n')
    write(ROOT/'evidence/family_mixer_coordinate_derivation01.json',dict(passed=True,origin=origin,origin_sha256=sha(ROOT/origin),derived=out,derived_sha256=sha(p),changes=changes,diff=''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True))),k=.01,c27_f=1e-5,state_capacitance_f=1e-9,electrical_port_law_unchanged=True,active_cards_unchanged=True,gates_unchanged=True))
if __name__=='__main__':main()
