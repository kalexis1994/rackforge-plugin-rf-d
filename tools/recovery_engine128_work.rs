// Offline counters for the exact stimulus and internal step sequence of rf_render.
#[no_mangle]
extern "C" fn rf_profile_new() -> *mut c_void {
    rf_new()
}

#[no_mangle]
unsafe extern "C" fn rf_profile_block(handle: *mut c_void) -> u32 {
    let dsp = unsafe { &mut *handle.cast::<Dsp>() };
    let mut count = 0;
    let mut worst = 0;
    let mut large = 0;
    for _ in 0..1024 {
        let (_, z, iterations, _) =
            kernel::inspect(&mut dsp.state, dsp.input[dsp.position], 12).unwrap();
        count += iterations as u32;
        worst = worst.max(iterations as u32);
        large += u32::from(z.iter().any(|value| value.abs() >= 0.125));
        dsp.position += 1;
        if dsp.position == dsp.input.len() {
            dsp.position = 0;
        }
    }
    count | (worst << 14) | (large << 18)
}
