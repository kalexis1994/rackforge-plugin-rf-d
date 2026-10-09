"""Preserve and correct notation; verify physical charges at imposed rails."""
import base64,json,re,subprocess
from decimal import Decimal,localcontext
from prepare_vco1_portable import ROOT,sha,write
from check_joint_reference import D,decode,ci
from chain_charge_reference import CAPS
from joint_cycles_analysis import require

def main():
    name='docs/VOZ_CARGAS_SEMILLA_PROTOCOLO.md';before_name='evidence/voice_joint_seed_cycles_rail_before01.json';out='evidence/voice_joint_seed_cycles_rail_reference01.json';require(not (ROOT/before_name).exists() and not (ROOT/out).exists(),'new errata receipt');raw=(ROOT/name).read_bytes();old='v en V, i en A, Q=C·v en C. Una corriente positiva va de a a b.'
    text=raw.decode('utf8');require(text.count(old)==1,'original notation')
    write(before_name,dict(schema='rf-d/fixed-rail-notation-before/v1',base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),original_source_sha256={name:sha(ROOT/name)},mutable_before_base64={name:base64.b64encode(raw).decode()},original_notation=old,reason='E-transpose-x omits the constant fixed terminal; absolute Q needs its rail offset. Incremental charge and preserved-charge roots are unchanged.'))
    fixed='v=Eᵀx en V, i en A; Q=C·(v−v_fijo) en C, con la referencia\ndel terminal fijo restada en la tensión física. Para riel constante,\nΔQ=C·Δv. [Aclaración y errata](VOZ_CARGAS_RIELES_NOTA.md).\nUna corriente positiva va de a a b.'
    (ROOT/name).write_bytes(text.replace(old,fixed).encode('utf8'))
    names=['tools/check_joint_fixed_rail_coordinates.py',name,'docs/VOZ_CARGAS_RIELES_NOTA.md',before_name,'evidence/voice_joint_charge_seed_native02.json','evidence/voice_joint_charge_seed_targets01.txt','crates/rf-d-circuit/src/circuit66.rs','crates/rf-d-circuit/src/chain_charge.rs','crates/rf-d-circuit/tests/support/mixer_chain_lab.rs','tools/circuit66_vca_release_probes.py'];sources={n:sha(ROOT/n) for n in names}
    lab=(ROOT/names[-2]).read_text();values=re.findall(r'plus_v:\s*([0-9.]+)',lab);require(values==['10.0'],'one fixed laboratory PLUS');plus=D(float(values[0]));native=json.loads((ROOT/'evidence/voice_joint_charge_seed_native02.json').read_text());lines=native['commands'][-1]['stdout'].splitlines();checks=[]
    with localcontext() as ctx:
        ctx.prec=100;initial=decode(lines[lines.index('INITIAL_HISTORY')+1]);targets=[]
        for line in (ROOT/'evidence/voice_joint_charge_seed_targets01.txt').read_text().splitlines():
            vals=list(map(float,line.split()));targets.append([D(vals[i])+D(vals[i+1]) for i in range(0,36,2)])
        for i,line in enumerate(lines):
            if not line.startswith('CHARGE_ROOT,'):continue
            id,guess=map(int,line.split(',')[1:3]);state=decode(lines[i+1]);rows=[]
            for k,(a,b,c) in enumerate([*CAPS,(67,7,10e-6)]):
                coord=lambda s:s[ci(a)]-(s[ci(b)] if isinstance(b,int) else s[ci(66)] if b=='BUS' else Decimal(0));offset=plus if b=='PLUS' else Decimal(0);physical=coord(state)-offset;desired=targets[id][k]-offset;error=D(c)*(physical-desired);require(abs(error)<=D(c)*D(1e-11),'physical charge target')
                change=D(c)*(physical-(coord(initial)-offset));expected=D(c)*(targets[id][k]-coord(initial));require(abs(change-expected)<=D(c)*D(1e-11),'fixed reference cancels in changes')
                rows.append(dict(index=k,a=a,b=b,capacitance_f=c,fixed_reference_v=str(offset),coordinate_v=str(coord(state)),physical_voltage_v=str(physical),physical_charge_c=str(D(c)*physical),physical_charge_target_error_c=str(error),physical_charge_change_from_lift_c=str(change)))
            checks.append(dict(seed_id=id,guess=guess,capacitors=rows))
    require(len(checks)==4,'all native roots');require('(Node(40), Fixed(b.recovery.vca.second.output.plus_v), 220e-6)' in (ROOT/'crates/rf-d-circuit/src/circuit66.rs').read_text(),'physical terminal source');require('(40,GROUND,220e-6)' in (ROOT/'crates/rf-d-circuit/src/chain_charge.rs').read_text(),'incremental incidence source')
    write(out,dict(schema='rf-d/fixed-rail-charge-reference/v1',passed=True,source_sha256=sources,source_sha256_after={n:sha(ROOT/n) for n in names},fixed_plus_lab_v=str(plus),native_root_checks=checks,physical_charge_checks=72,preserved_physical_charges_target0=18,preserved_physical_charges_target1=17,retargeted_capacitor_index=5,notation_only_correction=True,new_native_processes=0,physical_cards_changed=False,new_time_integration=False,new_audio=False))
    print('FIXED_RAIL_COORDINATES',len(checks)*18,'PLUS',plus,flush=True)
if __name__=='__main__':main()
