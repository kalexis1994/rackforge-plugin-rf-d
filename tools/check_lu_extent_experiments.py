"""Protect the marginal first hypothesis, confirmation and separate diagnostic."""
import json,statistics
from prepare_vco1_portable import ROOT,sha
from joint_cycles_analysis import require
from prepare_lu_support import kernel as indexed_kernel
def read(n):return json.loads((ROOT/n).read_text(encoding='utf8'))
def rows(obj):
 lines=obj['commands'][-1]['stdout'].splitlines();require(lines[-1]=='PASSED,84,5,stored_and_candidate_bits','paired benchmark scope');q=[list(map(int,x.split(',')[1:])) for x in lines if x.startswith('ROUND,')];require(len(q)==5 and [x[0] for x in q]==list(range(5)),'alternated rounds');return q
def extra_experiments(private):
 first=read('evidence/voice_lu_support_bench_native01.json');diag=read('evidence/voice_lu_extent_diagnostic01.json');confirmation=read('evidence/voice_lu_extent_confirmation01.json');decision=read('evidence/voice_lu_extent_decision01.json');require(decision['prior_bench_sha256']==sha(ROOT/'evidence/voice_lu_support_bench_native01.json') and not decision['numerical_gates_changed'],'preserved first hypothesis')
 for n,h in decision['first_experiment_source_sha256'].items():require(sha(ROOT/n)==h,'first hypothesis source')
 require((ROOT/'tools/joint_lu_support_kernel.rs').read_text(encoding='utf8')==indexed_kernel(),'indexed hypothesis recipe')
 for obj in [first,diag,confirmation]:
  require(obj['passed'] and obj['source_sha256']==obj['source_sha256_after'] and obj['private_used_sha256']==obj['private_used_sha256_after'],'stable auxiliary experiment')
  for n,h in obj['source_sha256'].items():require(sha(ROOT/n)==h,'auxiliary source')
  for n,h in obj['private_used_sha256'].items():require(sha(ROOT/n)==h,'auxiliary input');private[n]=h
  for f in obj.get('outputs',[]):require(sha(ROOT/f['path'])==f['sha256'],'auxiliary output');private[f['path']]=f['sha256']
  require(all(q['exit_code']==0 for q in obj['commands']),'auxiliary command acceptance')
 require(len(confirmation['commands'])==1 and confirmation['commands'][0]['wall_s']<=300,'confirmation budget');a,b=rows(first),rows(confirmation);lines=diag['commands'][-1]['stdout'].splitlines();require(lines[-1]=='DIAGNOSTIC_PASSED,8,84' and len([x for x in lines if x.startswith('REGRESSION,')])==8,'solver regression scope');u=next(x for x in lines if x.startswith('UPDATES,')).split(',');old,new,n=map(int,u[1:]);require(old>new>0 and n==84,'reduced matrix updates')
 inp=read('evidence/voice_lu_support_inputs01.json')
 for n,h in inp['private_used_sha256'].items():require(sha(ROOT/n)==h,'indexed input');private[n]=h
 return dict(indexed_median_paired_speedup=statistics.median(x[1]/x[2] for x in a),indexed_speedup_range=[min(x[1]/x[2] for x in a),max(x[1]/x[2] for x in a)],confirmation_median_paired_speedup=statistics.median(x[1]/x[2] for x in b),confirmation_speedups=[x[1]/x[2] for x in b],solver_regressions=8,diagnostic_selected_pairs=84,reference_matrix_updates=old,extent_matrix_updates=new,matrix_update_reduction_fraction=1-new/old,diagnostic_counts_not_in_timing=True)
