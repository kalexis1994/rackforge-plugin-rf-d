"""Capture the extended H128 training and untouched BUS reserves."""
import shutil
import traceback

import check_vco_family as original
from affine_evidence import Sources
from check_hybrid_voice import packed
from prepare_dual_chain import ROOT, sha, write
from vco_family import CV
from vco_family_receipts import read as read_reference
from vco_family_voice_bus_receipts import archive_members

OWN = "tools/check_vco_family_voice_bus.py"
PROTOCOL = "docs/VCO_FAMILIA_BUS_VOZ_PROTOCOLO.md"
ORIGINAL = "evidence/vco_family_oracle03.json"
TRAINING = tuple((float(cv), bus) for cv in CV for bus in (-1., 1.))
RESERVED = ((-2.6, -.94), (-1.6, -.91), (-.6, -.96),
            (-2.6, .89), (-1.6, .91), (-.6, .94))
METHODS = ((-1.6, -.91, "trap", 125e-9), (-1.6, -.91, "gear", 62.5e-9))
PREFIX = "evidence/vco_family_voice_bus"


def main():
    area = original.AREA
    assert not list(area.iterdir()) and shutil.disk_usage(ROOT).free > 1024**3
    ref = read_reference(ORIGINAL)
    paths = [original.EXE, original.MODEL]
    digests = {path: sha(ROOT / path) for path in paths}
    assert digests == {path: ref["private_used_sha256"][path] for path in paths}
    names = [OWN, PROTOCOL, *original.OWN, "tools/family_mixer_data128.rs"]
    sources = Sources(names)
    number = 1
    archived = archive_members()
    while (ROOT / f"{PREFIX}_oracle{number:02}.json").exists() or f"{PREFIX}_oracle{number:02}.json" in archived:
        number += 1
    receipt = ROOT / f"{PREFIX}_oracle{number:02}.json"
    pack = ROOT / f"{PREFIX}_windows{number:02}.xz"
    assert not pack.exists()
    report = dict(passed=False, **sources.fields(), private_used_sha256=digests,
                  pack=pack.relative_to(ROOT).as_posix(), training=[], reserved=[], method=[], rejected=[])

    def clear_case():
        for name in ("family.cir", "family.raw"):
            path = area / name
            assert path.resolve().parent == area.resolve()
            path.unlink(missing_ok=True)

    def scene_attempt(scene, sink):
        original.LAST = None
        try:
            return dict(result=original.run(scene, sink, pack))
        except Exception:
            record = dict(failure=traceback.format_exc(), process=original.LAST)
            export = area / "family.raw"
            if export.is_file():
                record.update(export_bytes=export.stat().st_size, export_sha256=sha(export))
            if record["process"] is None and (area / "family.cir").exists():
                record["deck"] = packed((area / "family.cir").read_bytes())
            return record
        finally:
            clear_case()

    groups = (
        ("training", [(cv, bus, "gear", 125e-9) for cv, bus in TRAINING]),
        ("reserved", [(cv, bus, "gear", 125e-9) for cv, bus in RESERVED]),
        ("method", METHODS),
    )
    with pack.open("xb") as sink:
        for group, cases in groups:
            for cv, bus, method, step in cases:
                scene = original.Scenario(keyboard_v=cv, imposed_mixer_v=bus, r8_fraction=original.R8,
                                          r11_active_ohm=original.R11, duration_s=.03,
                                          max_step_s=step, method=method)
                trial = scene_attempt(scene, sink)
                if "result" in trial:
                    report[group].append(trial["result"])
                else:
                    report["rejected"].append(dict(group=group, cv=cv, bus=bus, method=method, step=step,
                                                   original=trial, replay=scene_attempt(scene, sink)))
                write(receipt, report)
                print("H128_BUS", group, cv, bus, method, step, "result" in trial, flush=True)
    sources.unchanged()
    report["pack_sha256"] = sha(pack)
    report["pack_bytes"] = pack.stat().st_size
    report["temporary_area_empty"] = not list(area.iterdir())
    report["passed"] = not report["rejected"] and report["temporary_area_empty"]
    write(receipt, report)
    print("H128_BUS_ORACLE", report["passed"], report["pack_bytes"], flush=True)
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
