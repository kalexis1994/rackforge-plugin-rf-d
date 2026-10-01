"""Lossless storage of the generated survey, with scientific object identity."""
import gzip
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evidence/loudness_latch_increment_survey.json"
COMPRESSED=RAW.with_suffix(".json.gz")
MANIFEST=ROOT/"evidence/loudness_latch_increment_storage.json"


def compress():
    original=json.loads(RAW.read_bytes())
    canonical=json.dumps(original,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
    encoded=gzip.compress(canonical,compresslevel=9,mtime=0)
    if json.loads(gzip.decompress(encoded))!=original:
        raise ValueError("compression changed the scientific object")
    COMPRESSED.write_bytes(encoded)
    if gzip.decompress(COMPRESSED.read_bytes())!=canonical:
        raise ValueError("written compressed evidence differs")
    manifest=dict(schema="rf-d/latch-survey-storage/v1",dataset_schema=original["schema"],
        path=str(COMPRESSED.relative_to(ROOT)).replace("\\","/"),encoding="gzip of UTF-8 canonical JSON",
        scientific_object_unchanged=True,canonical_json_sha256=hashlib.sha256(canonical).hexdigest(),
        compressed_sha256=hashlib.sha256(encoded).hexdigest(),compressed_bytes=len(encoded),
        canonical_bytes=len(canonical),gzip_mtime=0,
        compression_tool_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        summary=dict(cases=[{k:c[k] for k in ("complete","final_time_s","accepted_macro_steps",
            "accepted_backward_euler_steps","attempts")} for c in original["cases"]],
            refinement=original["refinement"]))
    MANIFEST.write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    # Only this exact generated file is removed, after verified round trip.
    RAW.unlink()
    return manifest


if __name__=="__main__":
    m=compress();print(json.dumps(dict(compressed_bytes=m["compressed_bytes"],canonical_bytes=m["canonical_bytes"],
                                      scientific_object_unchanged=m["scientific_object_unchanged"])))
