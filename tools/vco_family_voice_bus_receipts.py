"""Store the exact BUS oracle and coupled receipts in one lossless archive."""
import io
import json
import re
import tarfile

from prepare_dual_chain import ROOT

ARCHIVE = "evidence/vco_family_voice_bus_receipts01.tar.xz"
PATTERN = re.compile(r"vco_family_voice_bus_(?:oracle|coupled)\d{2}\.json")


def archive_members():
    path = ROOT / ARCHIVE
    if not path.is_file():
        return set()
    with tarfile.open(path, "r:xz") as archive:
        members = archive.getmembers()
        names = {item.name for item in members}
        assert len(names) == len(members)
        assert all(item.isfile() and PATTERN.fullmatch(item.name) for item in members)
    return {f"evidence/{name}" for name in names}


def receipt_bytes(name):
    path = ROOT / name
    assert path.parent == ROOT / "evidence" and PATTERN.fullmatch(path.name)
    if path.is_file():
        return path.read_bytes()
    with tarfile.open(ROOT / ARCHIVE, "r:xz") as archive:
        item = archive.getmember(path.name)
        assert item.isfile()
        source = archive.extractfile(item)
        assert source is not None
        with source:
            raw = source.read()
        assert len(raw) == item.size
        return raw


def read_receipt(name):
    return json.loads(receipt_bytes(name))


def archive_receipts():
    directory = ROOT / "evidence"
    paths = sorted(path for path in directory.glob("vco_family_voice_bus_*.json")
                   if PATTERN.fullmatch(path.name))
    destination = ROOT / ARCHIVE
    assert paths and not destination.exists()
    originals = {path: path.read_bytes() for path in paths}
    with tarfile.open(destination, "x:xz", preset=9) as archive:
        for path, raw in originals.items():
            item = tarfile.TarInfo(path.name)
            item.size = len(raw)
            archive.addfile(item, io.BytesIO(raw))
    with tarfile.open(destination, "r:xz") as archive:
        for path, raw in originals.items():
            source = archive.extractfile(path.name)
            assert source is not None
            with source:
                assert source.read() == raw
    assert archive_members() == {f"evidence/{path.name}" for path in paths}
    for path in paths:
        assert path.resolve().parent == directory.resolve()
        path.unlink()
    assert all(receipt_bytes(f"evidence/{path.name}") == raw for path, raw in originals.items())


if __name__ == "__main__":
    archive_receipts()
