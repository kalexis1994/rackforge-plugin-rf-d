use rf_d_circuit::{conditioned_recipe::{self as recipe,Recipe,FinalDecay,Resolution},
    conditioned_engine as temporal,conditioned_voice as voice,
    chain_charge::Parameters as Chain,mixer_on::OnMixer,vco1_stamp::Controls};
#[allow(dead_code)] #[path="support/mixer_chain_lab.rs"] mod lab;
#[allow(dead_code)] #[path="support/conditioned_seed.rs"] mod seed;
#[allow(dead_code)] #[path="support/conditioned_recipe_fine_seed.rs"] mod fine_seed;
fn bits(s:voice::State)->[u64;458]{std::array::from_fn(|i|if i<229{s.high[i].to_bits()}else{s.low[i-229].to_bits()})}
#[test]
fn explicit_scene_preserves_all_legacy_parameters_and_loads(){
    let(mut a,b,c)=lab::lab_parameters();a.r61_ohm=200.0;
    let mut chain=Chain{circuit:a,conversion:b,headphone:c,boundary:lab::controlled_boundary(0,true),mixer:OnMixer::new([false;5],[0.5;4]).unwrap()};
    chain.boundary.panel.cutoff_fraction_from_neg10=1.0;
    let expected=voice::Parameters::new(Controls::default(),chain,[false;4],[0.5;4],[0.,0.2,-0.3,0.1,0.4]).unwrap();
    for mode in [FinalDecay::On,FinalDecay::Off] {
        let actual=Recipe{final_decay:mode,resolution:Resolution::Half1Us}.parameters();
        assert_eq!(actual.controls,expected.controls);
        let a=actual.chain();let b=expected.chain();
        // The aggregate intentionally has no Debug; its five complete fields do.
        assert_eq!(format!("{:?}",(a.circuit,a.conversion,a.headphone,a.boundary,a.mixer)),
            format!("{:?}",(b.circuit,b.conversion,b.headphone,b.boundary,b.mixer)));
        assert_eq!(actual.sources.map(f64::to_bits),expected.sources.map(f64::to_bits));
        for(a,b)in [actual.c2_v,actual.reset_v,actual.q25,actual.reset_driver,actual.keyboard,actual.set_base].into_iter().zip([expected.c2_v,expected.reset_v,expected.q25,expected.reset_driver,expected.keyboard,expected.set_base]){assert_eq!(a.to_bits(),b.to_bits());}
        assert_eq!(actual.final_decay,mode==FinalDecay::On);assert_eq!(actual.short,expected.short);
    }
}
#[test]
fn own_history_matches_decay_mode_and_resolution_metadata(){
    for mode in [FinalDecay::On,FinalDecay::Off] {for resolution in [Resolution::Half2Us,Resolution::Half1Us]{
        let recipe=Recipe{final_decay:mode,resolution};let q=recipe.engine().unwrap().checkpoint();
        let expected=match(mode,resolution){
            (FinalDecay::On,Resolution::Half2Us)=>seed::A_STATE,
            (FinalDecay::Off,Resolution::Half2Us)=>seed::D_STATE,
            (FinalDecay::On,Resolution::Half1Us)=>fine_seed::A_FINE_STATE,
            (FinalDecay::Off,Resolution::Half1Us)=>fine_seed::D_FINE_STATE,
        };assert_eq!(bits(q.state),expected);
        assert_eq!(q.elapsed_ticks,recipe::START_TICKS);assert_eq!(q.next_full_ticks,1024);
        assert_eq!(q.settings.maximum_half_ticks,if resolution==Resolution::Half2Us{1048576}else{524288});assert_eq!(q.settings.attempt_limit,20);
        assert_eq!(q.parameters.final_decay,mode==FinalDecay::On);
    }}
    assert_ne!(seed::A_STATE,seed::D_STATE);
}
#[test]
fn source_events_require_exact_clock_and_preserve_all_accepted_charges(){
    let recipe=Recipe{final_decay:FinalDecay::On,resolution:Resolution::Half1Us};
    let mut engine=recipe.engine().unwrap();let original=engine.checkpoint();
    for bad in [1,2,3,usize::MAX] {assert_eq!(recipe.apply(&mut engine,bad),Err(temporal::Error::InvalidInput));assert_eq!(bits(engine.checkpoint().state),bits(original.state));assert_eq!(engine.checkpoint().parameters.keyboard.to_bits(),0_f64.to_bits());}
    for (index,event) in recipe::EVENTS.iter().enumerate(){
        // Source-only test: inject an already public stress history at the clock,
        // not a claim that this injected state is a trajectory at every event.
        let state=voice::State{high:std::array::from_fn(|i|f64::from_bits(seed::TRIGGER_STATE[i])),low:std::array::from_fn(|i|f64::from_bits(seed::TRIGGER_STATE[229+i]))};
        let q=temporal::Checkpoint{elapsed_ticks:event.elapsed_ticks,state,..original};
        let mut e=temporal::Engine::restore(q).unwrap();recipe.apply(&mut e,index).unwrap();
        assert_eq!(bits(e.checkpoint().state),bits(state));assert_eq!(e.checkpoint().next_full_ticks,q.next_full_ticks);
        assert_eq!(e.checkpoint().parameters.keyboard.to_bits(),event.keyboard_v.to_bits());assert_eq!(e.checkpoint().parameters.short,event.short);
        let wrong=Recipe{final_decay:FinalDecay::Off,..recipe};assert_eq!(wrong.apply(&mut e,index),Err(temporal::Error::InvalidInput));
    }
    assert_eq!(recipe::TARGETS[10],recipe::END_TICKS);
    assert!(recipe::TARGETS.windows(2).all(|x|x[0]<x[1]));
    assert!(recipe::TARGETS.iter().all(|x|x%8==0));
    assert_eq!(recipe::EVENTS[1].elapsed_ticks,recipe::TARGETS[0]);assert_eq!(recipe::EVENTS[2].elapsed_ticks,recipe::TARGETS[5]);
}
