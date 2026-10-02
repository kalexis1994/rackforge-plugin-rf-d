import gzip
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from loudness_latch_bdf_checkout_audit import (OUTPUT, SUMMARY, REPORTS, EXPECTED_EXCEPTIONS,
    recover_historical_input, git_bytes, sha)
from loudness_latch_bdf_doubling_survey import canonical


class CheckoutAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = OUTPUT.read_bytes()
        cls.report = json.loads(gzip.decompress(cls.raw))

    def test_all_frozen_inputs_recover_from_committed_blobs_without_modification(self):
        report = self.report; archives = {r["path"]:r for r in report["archived_inputs"]}
        self.assertEqual(tuple(archives), EXPECTED_EXCEPTIONS)
        self.assertEqual(len(report["entries"]), 49)
        recovered = {}
        for entry in report["entries"]:
            name = entry["path"]; blob = git_bytes(report["reference_git_head"], name)
            self.assertEqual(sha(blob), entry["git_blob_sha256"])
            raw = recover_historical_input(blob, archives[name]) if name in archives else blob
            self.assertEqual(sha(raw), entry["working_copy_sha256"])
            self.assertEqual(entry["identical_bytes"], name not in archives)
            recovered[name] = raw
        for path in REPORTS:
            data = json.loads(gzip.decompress(path.read_bytes()))
            for name, expected in data["source_sha256"].items():
                self.assertEqual(sha(recovered[name]), expected)
        summary = json.loads(SUMMARY.read_text()); storage = summary["storage"]
        self.assertEqual(len(self.raw), storage["bytes"])
        self.assertEqual(sha(self.raw), storage["compressed_sha256"])
        self.assertEqual(sha(canonical(report)), storage["canonical_json_sha256"])
        self.assertEqual(gzip.decompress(self.raw), canonical(report))
        for name, expected in report["source_sha256"].items():
            self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(), expected)
        self.assertFalse(report["original_direct_blob_comparison_passed"])
        self.assertTrue(report["all_differences_declared_crlf_expansion"])
        for key in ("prior_reports_modified", "input_files_modified", "numerical_experiment_repeated",
                    "numerical_gates_changed", "audio_admitted"):
            self.assertFalse(report[key])

    def test_reconstruction_rejects_unidentified_or_changed_data(self):
        archived = self.report["archived_inputs"][0]
        blob = git_bytes(self.report["reference_git_head"], archived["path"])
        with self.assertRaisesRegex(ValueError, "Git blob identity"):
            recover_historical_input(blob+b" ", archived)
        with self.assertRaisesRegex(ValueError, "working bytes"):
            recover_historical_input(blob, archived|dict(working_copy_source_utf8="{}\r\n"))
        modified = b"{}\r\n"
        with self.assertRaisesRegex(ValueError, "LF to CRLF"):
            recover_historical_input(blob, archived|dict(working_copy_source_utf8=modified.decode(),working_copy_sha256=sha(modified)))


if __name__ == "__main__":
    unittest.main()
