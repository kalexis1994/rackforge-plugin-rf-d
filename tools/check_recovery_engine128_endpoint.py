"""Check the physical stereo pair in the disposable ASIO benchmark profile."""

import argparse
import json
import subprocess
import sys
import traceback
import winreg

from affine_evidence import Sources
from check_hybrid_voice import packed
from check_recovery_engine128 import AREA, HOST, HOST_COMPILER, retire_lab
from check_recovery_host128 import asio_profile
from prepare_dual_chain import ROOT, sha, write

SOURCE = "tools/recovery_engine128_endpoint.rs"
RUNNER = "tools/check_recovery_engine128_endpoint.py"
PREFIX = "evidence/recovery_engine128_endpoint"
PARENT = r"Software\ASIO4ALL v2 by Wuschel"
PHYSICAL = ("HD Audio output 1", "HD Audio output 2")
NVIDIA = ("High Definition Audio 1", "High Definition Audio 2")
ENABLED = 0x80000000
DEVICES = (
    ("NVIDIA High Definition Audio", "A65359A8", ("8948B95D",)),
    ("Realtek(R) Audio", "2885C3C9", ("9CF5B46F", "B8A24F9D")),
)


def snapshot(path):
    values = {}
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path) as key:
        keys, count, _ = winreg.QueryInfoKey(key)
        values[""] = {name: [value, kind] for name, value, kind in
                      (winreg.EnumValue(key, i) for i in range(count))}
        for i in range(keys):
            child = winreg.EnumKey(key, i)
            for suffix, data in snapshot(path + "\\" + child).items():
                values[child + ("\\" + suffix if suffix else "")] = data
    return values


def endpoint_rows(raw, expected=PHYSICAL):
    header, *lines = raw.decode("utf8", errors="replace").splitlines()
    tag, rate, inputs, outputs = header.split("\t")
    assert tag == "ASIO_ENDPOINTS"
    parsed = []
    for i, line in enumerate(lines):
        marker, channel, sample_type, name = line.split("\t")
        assert marker == "ASIO_OUTPUT" and int(channel) == i
        parsed.append(dict(channel=i, sample_type=int(sample_type), name=name))
    assert len(parsed) == int(outputs)
    return dict(rate=float(rate), inputs=int(inputs), outputs=parsed,
                recovered=[(item["name"], item["sample_type"]) for item in parsed[:2]] ==
                [(name, 18) for name in expected])


def device_hash(identifier):
    value = 0
    for byte in identifier.encode("mbcs"):
        low = value & 255
        shift = (low - byte) & 31
        value = (value & 0xFFFFFF00) | (low ^ byte)
        value = ((value >> shift) | (value << ((32 - shift) & 31))) & 0xFFFFFFFF
    return f"{value:08X}"


def active_hardware():
    command = (
        "$ErrorActionPreference='Stop'; "
        "$end=Get-PnpDevice -Class AudioEndpoint -PresentOnly | Where-Object Status -eq 'OK'; "
        "$media=Get-PnpDevice -Class Media -PresentOnly | Where-Object {$_.Status -eq 'OK' -and "
        "$_.FriendlyName -in @('NVIDIA High Definition Audio','Realtek(R) Audio')}; "
        "@(foreach ($p in $media) { $ids=(Get-PnpDeviceProperty -InstanceId $p.InstanceId "
        "-KeyName DEVPKEY_Device_HardwareIds).Data; [pscustomobject]@{name=$p.FriendlyName; hardware=@($ids); "
        "endpoints=@($end | Where-Object FriendlyName -like ('*'+$p.FriendlyName+'*') | "
        "Select-Object -ExpandProperty FriendlyName)} }) | ConvertTo-Json -Compress -AsArray"
    )
    output = subprocess.check_output(["pwsh", "-NoProfile", "-Command", command], cwd=ROOT)
    return {item["name"]: dict(hashes=[device_hash(value) for value in item["hardware"]],
                              endpoints=item["endpoints"]) for item in json.loads(output)}


def discard_new_device(profile, device):
    assert profile == PARENT + "\\C1EA3620"
    assert device in {item[1] for item in DEVICES}
    path = profile + "\\" + device
    for child in sorted(snapshot(path), key=lambda key: len(key.split("\\")) if key else 0, reverse=True):
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, path + ("\\" + child if child else ""))


def try_devices(profile, inspect, report, nvidia):
    hardware = active_hardware()
    report["active_hardware"] = hardware
    known = snapshot(PARENT + "\\7B8F8470")
    report["trials"] = []
    for name, device, interfaces in (DEVICES[:1] if nvidia else DEVICES):
        available = hardware.get(name, {})
        if device not in available.get("hashes", []) or not available["endpoints"]:
            continue
        for interface in interfaces:
            before = snapshot(profile)
            if device in before:
                break
            relatives = (device, device + "\\" + interface, device + "\\" + interface + "\\00000000")
            assert all(relative in known for relative in relatives)
            trial = dict(device=name, keys=relatives, passed=False)
            report["trials"].append(trial)
            try:
                for relative in relatives:
                    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, profile + "\\" + relative,
                                            0, winreg.KEY_SET_VALUE) as key:
                        winreg.SetValueEx(key, "Flags", 0, winreg.REG_DWORD, ENABLED)
                trial["reads"] = [inspect(), inspect()]
                trial["passed"] = all(item["metrics"]["recovered"] for item in trial["reads"])
            finally:
                if not trial["passed"] and device in snapshot(profile):
                    discard_new_device(profile, device)
                    trial["restored"] = snapshot(profile) == before
                    assert trial["restored"]
            if trial["passed"]:
                return True
    return False


def run(report, destination, restore=False, nvidia=False):
    keep = set(AREA.iterdir())
    assert all(path.name in ("host-target", "host-target-msvc.jsonl") for path in keep)
    vendor = HOST / "target/release/build/asio-sys-bb9248db199c7ec7/out"
    source = AREA / "endpoint-probe.rs"
    exe = AREA / "recovery-host128.exe"
    profile = asio_profile(exe)
    assert profile == PARENT + "\\C1EA3620"
    command = [str(HOST_COMPILER), "--edition=2021", "-C", "opt-level=2", "-A", "dead_code",
               "-A", "nonstandard_style", "-L", f"native={vendor}", "-l", "static=asio",
               "-l", "user32", "-l", "advapi32", str(source), "-o", str(exe)]
    expected = NVIDIA if nvidia else PHYSICAL
    if nvidia:
        report["expected_channels"] = expected
    before = snapshot(PARENT)
    lab_before = snapshot(profile)
    report.update(profile=profile, initial_lab=lab_before, asio_lib_sha256=sha(vendor / "asio.lib"),
                  asio_bindings_sha256=sha(vendor / "asio_bindings.rs"))
    try:
        generated = (ROOT / SOURCE).read_bytes().replace(
            b"ASIO_BINDINGS_PATH", (vendor / "asio_bindings.rs").as_posix().encode(),
        )
        source.write_bytes(generated)
        build = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=40)
        report["build"] = dict(command=command, exit_code=build.returncode, stderr=packed(build.stderr))
        assert build.returncode == 0, build.stderr.decode(errors="replace")
        report["probe_sha256"] = sha(exe)

        def inspect():
            probe = subprocess.run([exe], cwd=ROOT, capture_output=True, timeout=15)
            assert probe.returncode == 0, probe.stderr.decode(errors="replace")
            return dict(output=packed(probe.stdout), metrics=endpoint_rows(probe.stdout, expected))

        report["reads"] = [inspect(), inspect()]
        report["passed"] = all(item["metrics"]["recovered"] for item in report["reads"])
        if restore and not report["passed"]:
            report["passed"] = try_devices(profile, inspect, report, nvidia)
    except Exception:
        report["failure"] = traceback.format_exc()
    finally:
        report["final_lab"] = snapshot(profile)
        after = snapshot(PARENT)
        def other_profiles(tree):
            return {key: value for key, value in tree.items() if key.split("\\")[0] != "C1EA3620"}
        report["other_profiles_unchanged"] = other_profiles(before) == other_profiles(after)
        write(destination, report)
        retire_lab(keep)
        report["temporary_probe_retired"] = set(AREA.iterdir()) == keep
        write(destination, report)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--restore", action="store_true", help="enable a present HD Audio pair in the lab profile")
    parser.add_argument("--nvidia", action="store_true", help="expect the physical monitor stereo pair")
    args = parser.parse_args()
    number = 1
    while (ROOT / f"{PREFIX}{number:02d}.json").exists():
        number += 1
    sources = Sources([SOURCE, RUNNER])
    report = dict(passed=False, **sources.fields())
    run(report, ROOT / f"{PREFIX}{number:02d}.json", restore=args.restore, nvidia=args.nvidia)
    sources.unchanged()
    print("ASIO_ENDPOINTS", [item["metrics"] for item in report.get("reads", [])],
          [(item["device"], item["passed"], [read["metrics"] for read in item.get("reads", [])])
           for item in report.get("trials", [])],
          report.get("other_profiles_unchanged"), report.get("failure", ""), flush=True)
    sys.exit(0 if report["passed"] else 1)
