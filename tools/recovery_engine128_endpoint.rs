//! Enumerate ASIO channels before linking the full RackForge benchmark.
use std::{ffi::{c_void, CString}, io};

#[path = "ASIO_BINDINGS_PATH"]
mod asio;

#[link(name = "ole32")]
unsafe extern "system" {
    fn CoInitializeEx(reserved: *mut c_void, flags: u32) -> i32;
    fn CoUninitialize();
}

struct Com;
impl Drop for Com {
    fn drop(&mut self) { unsafe { CoUninitialize(); } }
}

struct Driver;
impl Drop for Driver {
    fn drop(&mut self) { unsafe { asio::ASIOExit(); asio::remove_current_driver(); } }
}

fn asio_ok(operation: &str, status: i32) -> io::Result<()> {
    if status == 0 { Ok(()) } else { Err(io::Error::other(format!("{operation} returned {status}"))) }
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let status = unsafe { CoInitializeEx(std::ptr::null_mut(), 2) };
    if status < 0 { return Err(format!("CoInitializeEx returned {status}").into()); }
    let _com = Com;
    let mut name = CString::new("ASIO4ALL v2")?.into_bytes_with_nul();
    if !unsafe { asio::load_asio_driver(name.as_mut_ptr().cast()) } {
        return Err("ASIO4ALL load failed".into());
    }
    let _driver = Driver;
    let mut info = asio::ASIODriverInfo {
        asioVersion: 2, driverVersion: 0, name: [0; 32], errorMessage: [0; 124],
        sysRef: std::ptr::null_mut(),
    };
    asio_ok("ASIOInit", unsafe { asio::ASIOInit(&mut info) })?;
    let (mut inputs, mut outputs, mut rate) = (0, 0, 0.);
    asio_ok("ASIOGetChannels", unsafe { asio::ASIOGetChannels(&mut inputs, &mut outputs) })?;
    asio_ok("ASIOGetSampleRate", unsafe { asio::get_sample_rate(&mut rate) })?;
    println!("ASIO_ENDPOINTS\t{rate}\t{inputs}\t{outputs}");
    for channel in 0..outputs {
        let mut info = asio::ASIOChannelInfo {
            channel, isInput: 0, isActive: 0, channelGroup: 0, type_: 0, name: [0; 32],
        };
        asio_ok("ASIOGetChannelInfo", unsafe { asio::ASIOGetChannelInfo(&mut info) })?;
        let name: Vec<u8> = info.name.into_iter().take_while(|value| *value != 0).map(|value| value as u8).collect();
        println!("ASIO_OUTPUT\t{channel}\t{}\t{}", info.type_, String::from_utf8_lossy(&name));
    }
    Ok(())
}
