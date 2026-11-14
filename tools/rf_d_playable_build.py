"""Paths and output helpers shared by the playable RF-D build and its checks."""

import os
from pathlib import Path

from prepare_dual_chain import ROOT, sha, write


AREA = ROOT / "tmp/lab-current"
HOST = Path(os.environ.get("RACKFORGE_ROOT", ROOT.parent / "rackforge")).resolve()
PACKAGE = ROOT / "plugin/package"
GUEST = "tools/rf_d_reduced_voice_guest.rs"
NODE = "tools/rf_d_reduced_voice_wasm.js"
SDK_PATH = "crates/rackforge-plugin-sdk/src/lib.rs"
WASM_OPT = ROOT.parent / "rackforge-plugin-rf-5/target/tools/binaryen/binaryen-version_132/bin/wasm-opt.exe"
COMPILER = "C:/Users/kalex/.rustup/toolchains/stable-x86_64-pc-windows-gnu/bin/rustc.exe"


def emit(name, source):
    path = AREA / name
    path.write_text(source, encoding="utf8", newline="\n")
    return path
