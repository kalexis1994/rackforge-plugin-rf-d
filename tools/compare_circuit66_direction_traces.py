"""Exact IEEE-754 trace comparison, excluding build/environment metadata."""
import argparse
import hashlib
import json
import struct
from pathlib import Path


def compare(a,b,path="$",counts=None):
    if counts is None:
        counts = {"float_values":0,"scalar_values":0}
    if type(a) is not type(b):
        raise AssertionError(f"type mismatch at {path}")
    if isinstance(a,dict):
        if a.keys() != b.keys(): raise AssertionError(f"keys at {path}")
        for k in a: compare(a[k],b[k],f"{path}.{k}",counts)
    elif isinstance(a,list):
        if len(a) != len(b): raise AssertionError(f"length at {path}")
        for i,(x,y) in enumerate(zip(a,b)): compare(x,y,f"{path}[{i}]",counts)
    elif isinstance(a,float):
        if struct.pack(">d",a) != struct.pack(">d",b):
            raise AssertionError(f"float bits at {path}: {a} vs {b}")
        counts["float_values"] += 1
    else:
        if a != b: raise AssertionError(f"value at {path}: {a} vs {b}")
        counts["scalar_values"] += 1
    return counts


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--left",type=Path,required=True)
    parser.add_argument("--right",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args = parser.parse_args()
    a = json.loads(args.left.read_text(encoding="utf-8-sig"))
    b = json.loads(args.right.read_text(encoding="utf-8-sig"))
    a.pop("metadata",None)
    b.pop("metadata",None)
    counts = compare(a,b)
    report = dict(schema="rf-d/circuit66-direction-trace-comparison/v1",passed=True,
                  method="recursive comparison with IEEE-754 double bits; only metadata excluded",
                  left_path=str(args.left),right_path=str(args.right),
                  left_sha256=hashlib.sha256(args.left.read_bytes()).hexdigest(),
                  right_sha256=hashlib.sha256(args.right.read_bytes()).hexdigest(),
                  baseline_features=["solver-uncached-direction"],candidate_features=[],
                  cases=len(a["cases"]),captured_probes=sum(len(c["probes"]) for c in a["cases"]),
                  known_abrupt_failures=a["failed_cases"],counts=counts,audio_fidelity_claim=False)
    args.output.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))
