"""Execute recipe integration and rerun the four existing scratch/heap tests."""
import argparse,os
from prepare_vco1_portable import ROOT
from conditioned_recipe_native02 import experiment
from joint_cycles_analysis import require

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,default=1);attempt=parser.parse_args().attempt
    # Rust's test workers have a separate stack from the executable main thread.
    os.environ['RUST_MIN_STACK']='33554432'
    for name,count in [('conditioned_recipe',3),('conditioned_portable',4)]:
        path=f'crates/rf-d-circuit/tests/{name}.rs'
        text=(ROOT/path).read_text(encoding='utf8').replace('#[path="support/', '#[path="'+(ROOT/'crates/rf-d-circuit/tests/support').as_posix()+'/')
        def validate(work,result):
            require(f'test result: ok. {count} passed; 0 failed;' in result['stdout'],'executed tests')
            return dict(native_test_count=count,rerun_previous_tests=name=='conditioned_portable',
                processing_heap_remeasured=name=='conditioned_portable',deadline_measured=False)
        q=experiment(name+f'tests{attempt:02d}',text,['--test-threads=1','--nocapture'],
            [path,'tools/test_conditioned_recipe.py','crates/rf-d-circuit/tests/support/mixer_chain_lab.rs',
            'crates/rf-d-circuit/tests/support/conditioned_seed.rs','docs/RECETA_CONDICIONADA_PROTOCOLO.md'],[],validate,extra_compile=('--test',))
        require(q['passed'],'native tests')
if __name__=='__main__':main()
