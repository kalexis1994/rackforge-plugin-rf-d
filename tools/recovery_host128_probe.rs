// Appended to the frozen host probe by check_recovery_host128.py.
use windows::{
    core::{PCWSTR, PWSTR},
    Win32::{
        Devices::Properties::DEVPKEY_Device_FriendlyName,
        Foundation::{CloseHandle, BOOL, HANDLE, WAIT_OBJECT_0},
        Media::Audio::{
            self as audio, AudioCategory_Other, AudioClientProperties,
            IAudioClient, IAudioClient3, IAudioRenderClient, IAudioSessionManager2,
            IMMDevice, IMMDeviceEnumerator, MMDeviceEnumerator,
            WAVEFORMATEX,
        },
        System::{
            Com::{CoCreateInstance, CoInitializeEx, CoTaskMemFree, CoUninitialize, CLSCTX_ALL, COINIT_APARTMENTTHREADED, STGM_READ},
            Threading::{CreateEventW, WaitForSingleObject},
            Variant::VT_LPWSTR,
        },
    },
};

const HOST_FRAMES: u32 = 128;
const HOST_RATE: u32 = 48000;
type HostResult<T> = Result<T, Box<dyn std::error::Error>>;

struct Com;
impl Com {
    fn init() -> HostResult<Self> {
        unsafe { CoInitializeEx(None, COINIT_APARTMENTTHREADED).ok()? };
        Ok(Self)
    }
}
impl Drop for Com {
    fn drop(&mut self) { unsafe { CoUninitialize() } }
}

struct Format(*mut WAVEFORMATEX);
impl Format {
    fn rate(&self) -> u32 { unsafe { (*self.0).nSamplesPerSec } }
    fn channels(&self) -> u16 { unsafe { (*self.0).nChannels } }
}
impl Drop for Format {
    fn drop(&mut self) { unsafe { CoTaskMemFree(Some(self.0.cast())) } }
}

struct Event(HANDLE);
impl Drop for Event {
    fn drop(&mut self) { let _ = unsafe { CloseHandle(self.0) }; }
}

fn endpoints128() -> HostResult<Vec<(String, IMMDevice)>> {
    let enumerator: IMMDeviceEnumerator =
        unsafe { CoCreateInstance(&MMDeviceEnumerator, None, CLSCTX_ALL)? };
    let devices = unsafe { enumerator.EnumAudioEndpoints(audio::eRender, audio::DEVICE_STATE_ACTIVE)? };
    let mut result = Vec::new();
    for index in 0..unsafe { devices.GetCount()? } {
        let device = unsafe { devices.Item(index)? };
        let name = unsafe {
            let store = device.OpenPropertyStore(STGM_READ)?;
            let key = DEVPKEY_Device_FriendlyName;
            let value = store.GetValue(std::ptr::addr_of!(key).cast())?;
            let raw = &value.as_raw().Anonymous.Anonymous;
            if raw.vt != VT_LPWSTR.0 {
                return Err("Unexpected friendly-name type".into());
            }
            let ptr = *(&raw.Anonymous as *const _ as *const *mut u16);
            PWSTR(ptr).to_string()?
        };
        result.push((name, device));
    }
    Ok(result)
}

struct Stream128 {
    client: IAudioClient3,
    mix: Format,
    periods: [u32; 4],
}

impl Stream128 {
    fn query(device: &IMMDevice, raw: bool) -> HostResult<Self> {
        let client: IAudioClient3 = unsafe { device.Activate(CLSCTX_ALL, None)? };
        let properties = AudioClientProperties {
            cbSize: std::mem::size_of::<AudioClientProperties>() as u32,
            bIsOffload: BOOL(0),
            eCategory: AudioCategory_Other,
            Options: if raw { audio::AUDCLNT_STREAMOPTIONS_RAW } else { audio::AUDCLNT_STREAMOPTIONS_NONE },
        };
        unsafe { client.SetClientProperties(&properties)? };
        let mix = Format(unsafe { client.GetMixFormat()? });
        let (mut default, mut fundamental, mut minimum, mut maximum) = (0, 0, 0, 0);
        unsafe {
            client.GetSharedModeEnginePeriod(mix.0, &mut default, &mut fundamental, &mut minimum, &mut maximum)?;
        }
        Ok(Self { client, mix, periods: [default, fundamental, minimum, maximum] })
    }

    fn supports_128(&self) -> bool {
        let [_, step, min, max] = self.periods;
        self.mix.rate() == HOST_RATE && step != 0 && HOST_FRAMES % step == 0
            && (min..=max).contains(&HOST_FRAMES)
    }

    fn active(&self) -> HostResult<(u32, u32)> {
        let mut ptr = std::ptr::null_mut();
        let mut period = 0;
        unsafe { self.client.GetCurrentSharedModeEnginePeriod(&mut ptr, &mut period)? };
        let format = Format(ptr);
        Ok((period, format.rate()))
    }

    fn initialize(&self) -> HostResult<(u32, u32, u32)> {
        unsafe {
            self.client.InitializeSharedAudioStream(
                audio::AUDCLNT_STREAMFLAGS_EVENTCALLBACK, HOST_FRAMES, self.mix.0, None,
            )?;
        }
        let (period, rate) = self.active()?;
        let capacity = unsafe { self.client.GetBufferSize()? };
        Ok((period, rate, capacity))
    }
}

fn discover128(devices: &[(String, IMMDevice)]) {
    for (name, device) in devices {
        for (category, raw) in [("standard", false), ("raw", true)] {
            match Stream128::query(device, raw) {
                Err(error) => println!("QUERY_ERROR\t{name}\t{category}\t{error}"),
                Ok(stream) => {
                    let [default, fundamental, minimum, maximum] = stream.periods;
                    println!("PERIODS\t{name}\t{category}\t{}\t{}\t{default}\t{fundamental}\t{minimum}\t{maximum}\t{}",
                        stream.mix.rate(), stream.mix.channels(), stream.supports_128());
                    if stream.supports_128() {
                        let event = unsafe { CreateEventW(None, false, false, PCWSTR::null()) };
                        match stream.initialize() {
                            Ok((period, rate, capacity)) => {
                                if let Ok(handle) = event {
                                    let event = Event(handle);
                                    let registered = unsafe { stream.client.SetEventHandle(event.0) };
                                    drop(stream);
                                    match registered {
                                        Ok(()) => println!("OPEN\t{name}\t{category}\t{period}\t{rate}\t{capacity}"),
                                        Err(error) => println!("OPEN_ERROR\t{name}\t{category}\t{error}"),
                                    }
                                } else {
                                    println!("OPEN_ERROR\t{name}\t{category}\tEvent creation failed");
                                }
                            }
                            Err(error) => println!("OPEN_ERROR\t{name}\t{category}\t{error}"),
                        }
                    }
                }
            }
        }
        match exclusive_capabilities(device) {
            Ok((default, minimum, active)) => {
                println!("EXCLUSIVE\t{name}\t{default}\t{minimum}\t{active}");
            }
            Err(error) => println!("EXCLUSIVE_ERROR\t{name}\t{error}"),
        }
    }
}

fn exclusive_capabilities(device: &IMMDevice) -> HostResult<(i64, i64, i32)> {
    unsafe {
        let client: IAudioClient = device.Activate(CLSCTX_ALL, None)?;
        let (mut default, mut minimum) = (0, 0);
        client.GetDevicePeriod(Some(&mut default), Some(&mut minimum))?;
        let manager: IAudioSessionManager2 = device.Activate(CLSCTX_ALL, None)?;
        let sessions = manager.GetSessionEnumerator()?;
        let mut active = 0;
        for index in 0..sessions.GetCount()? {
            if sessions.GetSession(index)?.GetState()? == audio::AudioSessionStateActive {
                active += 1;
            }
        }
        Ok((default, minimum, active))
    }
}

fn main() -> HostResult<()> {
    let args: Vec<_> = std::env::args().skip(1).collect();
    if args.first().is_some_and(|s| s == "fixtures") {
        return Ok(fixtures(Api::load()?)?);
    }
    let _com = Com::init()?;
    #[cfg(asio128)]
    if args.first().is_some_and(|s| s == "asio-query") {
        return asio_query128(args.get(1).ok_or("Missing ASIO driver name")?);
    }
    #[cfg(asio128)]
    if args.first().is_some_and(|s| s == "asio-bench") {
        let name = args.get(1).ok_or("Missing ASIO driver name")?;
        let blocks = args.get(2).ok_or("Missing block count")?.parse()?;
        let dsp = args.get(3).is_some_and(|s| s == "dsp");
        return asio_bench128(name, blocks, dsp);
    }
    let devices = endpoints128()?;
    discover128(&devices);
    Ok(())
}
