//! Laboratory-only inclusive wall timers; errors also close their scopes.
use std::{time::Instant,sync::atomic::{AtomicU64,Ordering}};
const N:usize=19;
static NS:[AtomicU64;N]=[const{AtomicU64::new(0)};N];
static COUNT:[AtomicU64;N]=[const{AtomicU64::new(0)};N];
pub struct Scope{index:usize,start:Instant}
pub fn enter(index:usize)->Scope{COUNT[index].fetch_add(1,Ordering::Relaxed);Scope{index,start:Instant::now()}}
impl Drop for Scope{fn drop(&mut self){NS[self.index].fetch_add(self.start.elapsed().as_nanos()as u64,Ordering::Relaxed);}}
pub fn read()->[(u64,u64);N]{std::array::from_fn(|k|(NS[k].load(Ordering::Relaxed),COUNT[k].load(Ordering::Relaxed)))}
