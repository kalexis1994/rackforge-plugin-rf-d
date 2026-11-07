use std::ffi::c_void;

#[repr(C)]
#[derive(Clone, Copy, Default)]
struct FileTime {
    low: u32,
    high: u32,
}

impl FileTime {
    fn ticks(self) -> u64 {
        (u64::from(self.high) << 32) | u64::from(self.low)
    }
}

#[link(name = "kernel32")]
extern "system" {
    fn GetCurrentProcess() -> *mut c_void;
    fn GetCurrentThread() -> *mut c_void;
    fn GetCurrentProcessorNumber() -> u32;
    fn GetProcessAffinityMask(process: *mut c_void, mask: *mut usize, system: *mut usize) -> i32;
    fn GetThreadTimes(thread: *mut c_void, created: *mut FileTime, exited: *mut FileTime,
                      kernel: *mut FileTime, user: *mut FileTime) -> i32;
}

pub fn affinity() -> std::io::Result<()> {
    let mut mask = 0;
    let mut system = 0;
    if unsafe { GetProcessAffinityMask(GetCurrentProcess(), &mut mask, &mut system) } == 0 {
        return Err(std::io::Error::last_os_error());
    }
    println!("AFFINITY,{mask},{}", unsafe { GetCurrentProcessorNumber() });
    Ok(())
}

pub fn thread_ns() -> std::io::Result<u64> {
    let [mut created, mut exited, mut kernel, mut user] = [FileTime::default(); 4];
    if unsafe { GetThreadTimes(GetCurrentThread(), &mut created, &mut exited, &mut kernel, &mut user) } == 0 {
        return Err(std::io::Error::last_os_error());
    }
    Ok(100 * (kernel.ticks() + user.ticks()))
}
