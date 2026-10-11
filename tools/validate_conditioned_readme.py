"""Restore only the intended README edit; retain the rejected encoding and replay."""
import argparse,base64,hashlib,json,subprocess,traceback
from prepare_vco1_portable import ROOT,sha
from joint_cycles_analysis import require
from validate_mixer_on_native import native_source_identity
from validate_joint_charge_seed import local_links

BASE='afb5b057237c8fc52703f4dfb9b37cd100821b7e'
PREVIOUS='evidence/voice_conditioned_return_tests01.json'
OUT='evidence/voice_conditioned_return_utf8_tests01.json'
FAILURE='evidence/voice_conditioned_readme_failure01.json'
SELF='tools/validate_conditioned_readme.py'
ADDITION='''
[Retorno desde la raíz condicionada](docs/VOZ_RETORNO_CONDICIONADO_RESULTADOS.md):
42544 pasos base y 170176 solves perturbados de C27 desde sus propias
raíces. Ambos tiempos de reset, periodo y deriva en fase contrastados;
20 operadores independientes para las 18 columnas. FD completa sólo C27.
[QA vigente](evidence/voice_conditioned_return_utf8_tests01.json).
'''

def expected():
    before=json.loads((ROOT/'evidence/voice_conditioned_return_before01.json').read_text(encoding='utf8'))
    original=base64.b64decode(before['mutable_before_base64']['README.md'])
    return original.replace(b'[QA vigente](evidence/voice_charge_basis_tests01.json)',('[QA vigente]('+OUT+')').encode(),1)+ADDITION.encode('utf8')

def audit():
    require((ROOT/'README.md').read_bytes()==expected(),'README differs from exact intended UTF8 byte mutation')
    require(subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==BASE,'repair base')
    old=json.loads((ROOT/PREVIOUS).read_text(encoding='utf8'));require(old['passed'],'numeric release')
    bad=subprocess.check_output(['git','show',BASE+':README.md'],cwd=ROOT)
    require(hashlib.sha256(bad).hexdigest()==old['source_sha256']['README.md'],'preserved rejected README in Git')
    for name,digest in old['source_sha256'].items():
        if name!='README.md':require(sha(ROOT/name)==digest,'unchanged numeric source '+name)
    for name,digest in old['private_input_sha256'].items():require(sha(ROOT/name)==digest,'unchanged evidence '+name)
    failure=json.loads((ROOT/FAILURE).read_text(encoding='utf8'))
    require(base64.b64decode(failure['bad_readme_base64'])==bad and failure['failure']==failure['replay'] and failure['source_sha256']==sha(ROOT/SELF),'preserved exact failure/replay')
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).splitlines()
    require(set(staged)=={'README.md',SELF,FAILURE,OUT},'only declared repair files')
    names=set(old['source_sha256'])|{PREVIOUS,SELF,FAILURE};sources={name:sha(ROOT/name) for name in sorted(names)}
    for name in staged:
        if name!=OUT:native_source_identity(name,sources[name],subprocess.check_output(['git','show',':'+name],cwd=ROOT))
    report=dict(old);report.update(schema='rf-d/conditioned-return-utf8-release/v1',base_commit=BASE,measurement_base_commit=old['base_commit'],previous_qa_sha256=sha(ROOT/PREVIOUS),source_sha256=sources,source_sha256_after=sources,publication_encoding_repair=True,numerical_sources_reexecuted=False,readme_before_sha256=hashlib.sha256(bad).hexdigest(),readme_expected_sha256=hashlib.sha256(expected()).hexdigest(),local_markdown_links=local_links(['README.md']))
    return report

def main():
    p=argparse.ArgumentParser();p.add_argument('--repair',action='store_true');args=p.parse_args()
    if args.repair:
        require((ROOT/FAILURE).exists(),'preserve failure before repair');(ROOT/'README.md').write_bytes(expected());print('README_EXACT_BYTES_RESTORED');return
    try:report=audit()
    except Exception:
        failure=traceback.format_exc()
        try:audit();replay='unexpected pass'
        except Exception:replay=traceback.format_exc()
        # Compare the exception message, not differing replay call-site line numbers.
        failure=failure.splitlines()[-1];replay=replay.splitlines()[-1]
        require(not (ROOT/FAILURE).exists(),'exclusive encoding failure')
        record=dict(passed=False,failure=failure,replay=replay,source_sha256=sha(ROOT/SELF),failed_source_text=(ROOT/SELF).read_text(encoding='utf8'),bad_readme_base64=base64.b64encode((ROOT/'README.md').read_bytes()).decode(),preserved_git_commit=BASE)
        (ROOT/FAILURE).write_text(json.dumps(record,indent=2)+'\n',encoding='utf8',newline='\n');print('README_REJECTED',failure);return
    (ROOT/OUT).write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n');print('README_QA',report['passed'],len(report['source_sha256']),len(report['private_input_sha256']))
if __name__=='__main__':main()
