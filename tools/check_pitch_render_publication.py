"""Exercise native cancellation and the exact atomic publication path without a third long solve."""
import hashlib,json,traceback
from prepare_dual_chain import ROOT,sha,write
from affine_evidence import Sources
from check_hybrid_voice import unpack
from export_pitch_render import reference,REFERENCE
import render_pitch as cli

def main():
    native_name='evidence/pitch_render_native02.json'
    data,meta=reference(native_name)
    sources=Sources(['tools/render_pitch.py','tools/prepare_pitch_render_tool.py','tools/export_pitch_render.py','tools/check_pitch_render_publication.py','tools/pitch_render_main.rs','crates/rf-d-circuit/src/pitch_program_render.rs','docs/PITCH_RENDER_PROTOCOLO.md',REFERENCE])
    r=dict(passed=False,**sources.fields(),previous_wav_sha256=sha(cli.ARTIFACT),reference=REFERENCE,reference_sha256=sha(ROOT/REFERENCE),third_long_history=False);phase='invalid_quota'
    try:
        try:cli.render(0,quiet=True);raise AssertionError('zero quota accepted')
        except ValueError:pass
        phase='cancel';r['cancel_before_dc']=cli.render(128,pre_cancel=True,quiet=True)
        def cancel(line,path):
            if line.startswith('PROGRESS,'):path.write_bytes(b'cancel\n')
        r['cancel_after_progress']=cli.render(31,on_line=cancel,quiet=True)
        assert all(x['passed'] and x['cancelled'] and not x['published'] and x['temporary_area_empty'] and x['previous_wav_sha256']==x['final_wav_sha256']==r['previous_wav_sha256'] for x in [r['cancel_before_dc'],r['cancel_after_progress']])
        assert b'CANCELLED,before_dc' in unpack(r['cancel_before_dc']['stdout']) and b'CANCELLED,between_quotas' in unpack(r['cancel_after_progress']['stdout'])
        phase='candidate_gates';negative=[]
        with cli.Laboratory() as lab:
            stage=lab.own('render.wav.part')
            bad_payload=bytearray(data);bad_payload[60]^=1
            for label,bad in [('header',b'bad'),('payload',bytes(bad_payload))]:
                stage.write_bytes(bad)
                try:cli.promote(stage);raise RuntimeError('invalid candidate published')
                except AssertionError:pass
                assert sha(cli.ARTIFACT)==r['previous_wav_sha256'];negative.append(label)
            phase='complete_parse';native=json.loads((ROOT/native_name).read_text(encoding='utf8'));m=cli.parse_complete(unpack(native['profiles'][1]['stdout']));assert m['complete']==meta['complete']
            phase='publish';stage.write_bytes(data);r['output']=cli.promote(stage)
        assert sha(cli.ARTIFACT)==meta['sha256'] and cli.ARTIFACT.read_bytes()==data
        r.update(passed=True,negative_publication_controls=negative,full_fine_complete_parse=True,published=True,artifact_replaced_atomically=True,admitted_private_input_retired=False,previous_listening_view_retired=True,previous_listening_regenerable=True)
    except Exception:
        r.update(failure=traceback.format_exc(),failed_phase=phase)
        # Native wrapper itself retains exact failed input and never publishes on failure.
        # Never replay a successful replace; retain candidates by derivation from native receipt.
        write(ROOT/'evidence/pitch_render_publication_failure01.json',r);raise
    sources.unchanged();r['temporary_area_empty']=not list(cli.AREA.iterdir());write(ROOT/'evidence/pitch_render_publication01.json',r);print('PITCH_PUBLICATION',r['passed'],r['output']['sha256'],flush=True)
if __name__=='__main__':main()
