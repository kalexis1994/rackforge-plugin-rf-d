"""Compare initial nodes and complete jump rows in IEEE-754 bits, not timing."""
import argparse
import hashlib
import json
from pathlib import Path
from compare_circuit66_direction_traces import compare


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for name in ("left","right","output"): parser.add_argument("--"+name,type=Path,required=True)
    args = parser.parse_args()
    a = json.loads(args.left.read_text(encoding="utf-8-sig"))
    b = json.loads(args.right.read_text(encoding="utf-8-sig"))
    counts = {"float_values":0,"scalar_values":0}
    for left,right in zip(a["cases"],b["cases"],strict=True):
        for key in ("mode","r61_ohm","initial_node_v","rows"):
            compare(left[key],right[key],counts=counts)
    report = dict(schema="rf-d/circuit66-vca-jump-trace-comparison/v1",passed=True,counts=counts,
                  scope="case identities, initial nodes and complete rows; excludes environment and timing",
                  left_sha256=hashlib.sha256(args.left.read_bytes()).hexdigest(),
                  right_sha256=hashlib.sha256(args.right.read_bytes()).hexdigest(),audio_fidelity_claim=False)
    args.output.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))
