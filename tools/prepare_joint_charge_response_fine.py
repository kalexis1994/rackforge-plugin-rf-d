"""Derive a smaller-perturbation caller and checker without altering failed inputs."""
from prepare_vco1_portable import ROOT
from joint_cycles_analysis import require

def derive():
    text=(ROOT/'tools/joint_charge_response_runner.rs').read_text(encoding='utf8')
    a='for h in [0.001,0.0005]';require(text.count(a)==1,'one perturbation pair')
    return text.replace(a,'for h in [0.000125,0.0000625]')

def fine_checker():
    text=(ROOT/'tools/check_joint_charge_response.py').read_text(encoding='utf8')
    changes=[('[-.001,.001,-.0005,.0005]','[-.000125,.000125,-.0000625,.0000625]'),
      ('for h in [.001,.0005]','for h in [.000125,.0000625]'),
      ('tools/check_joint_charge_response.py','tools/check_joint_charge_response_fine.py'),
      ('voice_joint_charge_response_reference{a.attempt:02d}.json','voice_joint_charge_response_fine_reference{a.attempt:02d}.json'),
      ('voice_joint_charge_response_native01.json','voice_joint_charge_response_fine_native01.json'),
      ('docs/VOZ_CARGAS_RESPUESTA_PROTOCOLO.md','docs/VOZ_CARGAS_RESPUESTA_FINA_PROTOCOLO.md'),
      ("central_refinement_max_voltage_ratio_v_per_v=float(np.max(abs(central[1]-central[0])))", "central_refinement_max_voltage_v_per_v=float(np.max(abs(central[1]-central[0])[[k for k in range(200) if not 98<=k<133]])),central_refinement_max_current_a_per_v=float(np.max(abs(central[1]-central[0])[[k for k in range(218) if 98<=k<133 or k>=200]]))")]
    for a,b in changes:require(text.count(a)>=1,'checker substitution '+a);text=text.replace(a,b)
    return text

def fine_runner():
    text=(ROOT/'tools/run_joint_charge_response.py').read_text(encoding='utf8')
    for a,b in [('voice_joint_charge_response_native','voice_joint_charge_response_fine_native'),('joint-charge-response','joint-charge-response-fine'),('tools/run_joint_charge_response.py','tools/run_joint_charge_response_fine.py'),('tools/joint_charge_response_runner.rs','tools/joint_charge_response_fine_runner.rs'),('tools/prepare_joint_charge_response.py','tools/prepare_joint_charge_response_fine.py'),('docs/VOZ_CARGAS_RESPUESTA_PROTOCOLO.md','docs/VOZ_CARGAS_RESPUESTA_FINA_PROTOCOLO.md')]:require(a in text,'runner substitution '+a);text=text.replace(a,b)
    return text

def main():
    for name,text in [('tools/joint_charge_response_fine_runner.rs',derive()),('tools/check_joint_charge_response_fine.py',fine_checker()),('tools/run_joint_charge_response_fine.py',fine_runner())]:
        p=ROOT/name;require(not p.exists(),'exclusive fine source '+name);p.write_text(text,encoding='utf8',newline='\n')
    p=ROOT/'.gitattributes';p.write_bytes(p.read_bytes()+b'\n/tools/joint_charge_response_fine_runner.rs text eol=lf\n')
    print('CHARGE_RESPONSE_FINE_PREPARED',flush=True)

if __name__=='__main__':main()
