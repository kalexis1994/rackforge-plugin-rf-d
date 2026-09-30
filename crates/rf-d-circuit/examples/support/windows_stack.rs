//! Read-only Win64 memory observations in an offline worker, never in DSP.
//! ABI and semantics: Microsoft GetCurrentThreadStackLimits, VirtualQuery,
//! MEMORY_BASIC_INFORMATION. No reserved/guard page is read or written.
use std::ffi::c_void;
use std::mem::{size_of, MaybeUninit};

#[repr(C)]
struct MemoryInfo {
    base_address: *mut c_void,
    allocation_base: *mut c_void,
    allocation_protect: u32,
    partition_id: u16,
    region_size: usize,
    state: u32,
    protect: u32,
    kind: u32,
}

#[link(name = "kernel32")]
unsafe extern "system" {
    fn GetCurrentThreadStackLimits(low: *mut usize, high: *mut usize);
    fn VirtualQuery(address: *const c_void, info: *mut MemoryInfo, length: usize) -> usize;
}

#[derive(Clone, Copy)]
pub struct Snapshot {
    pub allocated_bytes: usize,
    pub committed_bytes: usize,
    pub guard_bytes: usize,
    pub uncommitted_bytes: usize,
    pub regions: usize,
}

fn query(address: usize) -> Result<MemoryInfo, String> {
    let mut info = MaybeUninit::<MemoryInfo>::zeroed();
    // SAFETY: info has the documented Win64 layout/size and is writable. The
    // address is only queried by the OS; this function never dereferences it.
    let written = unsafe {
        VirtualQuery(
            address as *const c_void,
            info.as_mut_ptr(),
            size_of::<MemoryInfo>(),
        )
    };
    if written != size_of::<MemoryInfo>() {
        return Err(format!("VirtualQuery returned {written} bytes"));
    }
    // SAFETY: a successful full-size query initialized every structure field.
    Ok(unsafe { info.assume_init() })
}

#[inline(never)]
pub fn snapshot() -> Result<Snapshot, String> {
    if size_of::<MemoryInfo>() != 48 {
        return Err("Unsupported MEMORY_BASIC_INFORMATION layout".into());
    }
    let mut low = 0;
    let mut high = 0;
    // SAFETY: two separate writable usize outputs, as required by Win64 ABI.
    unsafe {
        GetCurrentThreadStackLimits(&mut low, &mut high);
    }
    let marker = std::hint::black_box(0u8);
    let address = std::hint::black_box(&marker) as *const u8 as usize;
    if !(low..high).contains(&address) {
        return Err("Worker marker is outside system stack bounds".into());
    }
    let allocation = query(address)?.allocation_base as usize;
    let mut cursor = allocation;
    let mut result = Snapshot {
        allocated_bytes: high - allocation,
        committed_bytes: 0,
        guard_bytes: 0,
        uncommitted_bytes: 0,
        regions: 0,
    };
    while cursor < high {
        let info = query(cursor)?;
        let end = (info.base_address as usize)
            .checked_add(info.region_size)
            .ok_or("Region address overflow")?;
        if info.allocation_base as usize != allocation || end <= cursor || end > high {
            return Err("Inconsistent worker stack allocation regions".into());
        }
        match info.state {
            0x1000 => result.committed_bytes += info.region_size, // MEM_COMMIT
            0x2000 => result.uncommitted_bytes += info.region_size, // MEM_RESERVE
            _ => return Err("Unexpected stack region state".into()),
        }
        if info.state == 0x1000 && info.protect & 0x100 != 0 {
            result.guard_bytes += info.region_size;
        } // PAGE_GUARD
        result.regions += 1;
        cursor = end;
    }
    if result.committed_bytes + result.uncommitted_bytes != result.allocated_bytes {
        return Err("Stack region sizes do not cover allocation".into());
    }
    Ok(result)
}

pub fn json(s: Snapshot) -> serde_json::Value {
    serde_json::json!({"allocated_bytes":s.allocated_bytes,"committed_bytes":s.committed_bytes,
        "guard_bytes":s.guard_bytes,"uncommitted_bytes":s.uncommitted_bytes,"regions":s.regions})
}
