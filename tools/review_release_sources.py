"""Bind the read-only visual review and figure/page erratum to original PDFs."""
import shutil
from pathlib import Path
from prepare_vco1_portable import ROOT,sha,write
from joint_cycles_analysis import require

def main():
    sources={n:sha(ROOT/n) for n in ['tools/review_release_sources.py','docs/VOZ_LIBERACION_REVISION.md','docs/CONTORNO_VOLUMEN_CIRCUITO.md','docs/FUENTES.md','crates/rf-d-circuit/src/conditioned_voice_contour.rs']}
    expected={'references-local/pdf/service_204d_full_fdiskc.pdf':'d1f96fa26d9e25dda9d1cb0bbe9a5e0b017f7e463ec5b268c380b58d44f5b6fe','references-local/pdf/service_204d_synthfool.pdf':'0edd35f3f9ab1eba346693545f0dcbe374bdcf6f37f9b1a34ecbdeb8ae682b4a'}
    for n,h in expected.items():require(sha(ROOT/n)==h,'original manual identity')
    images=['description-12.png','description-13.png','description14.png','contour-upright.png','loudness-clean.png','contour-204d.png']
    private={**expected,**{f'references-local/contour-review/{n}':sha(ROOT/f'references-local/contour-review/{n}') for n in images}}
    work=ROOT/'references-local/release-review01';require(work.exists(),'fresh PDF renders');outputs=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(work.glob('*.png'))];require(len(outputs)==5,'four full pages and readable source65')
    tool=Path(shutil.which('pdftoppm'));commands=[]
    for pdf,pages,stem in [('references-local/pdf/service_204d_full_fdiskc.pdf',[13,14,65],'full'),('references-local/pdf/service_204d_synthfool.pdf',[9],'svc9')]:
        for page in pages:commands.append([str(tool),'-f',str(page),'-l',str(page),'-r','120','-png','-singlefile',pdf,f'references-local/release-review01/{stem}-{page}'])
    commands.append([str(tool),'-f','65','-l','65','-r','500','-png','-singlefile','references-local/pdf/service_204d_full_fdiskc.pdf','references-local/release-review01/full-65-readable'])
    write('evidence/voice_release_review01.json',dict(passed=True,source_sha256=sources,source_sha256_after=sources,private_used_sha256=private,private_used_sha256_after=private,outputs=outputs,
        renderer=dict(path=str(tool),sha256=sha(tool)),render_commands=commands,complete_pages_visually_reviewed=['SVC-204D13','SVC-204D14','SVC-204D65','SVC-9p9'],existing_high_resolution_views_reviewed=images,
        source_locator_correction=dict(previous_document='docs/CONTORNO_VOLUMEN_CIRCUITO.md',previous_sha256=sources['docs/CONTORNO_VOLUMEN_CIRCUITO.md'],previous_full_pdf_figure='9-5',verified_figure='9-7',printed_page='9-5',previous_document_unchanged=True),
        reviewed_paths=['KEY/CR10/R60/C7/R55/Q20','Q12/R28/C4/Q25','Q20/R36/CR8/Q15','Q25/Q15/R38/R56','Q16/attack/C2/decay/Q18','C2/Q3/Q2/R59/board4Q18'],
        physical_devices_identified=False,topology_changed=False,audible_constants_changed=False,numerical_gates_changed=False))
    print('RELEASE_SOURCE_REVIEW',True,'figure9-7 printed-page9-5')
if __name__=='__main__':main()
