import gzip
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from loudness_latch_bdf_static_precision_enclosure_inputs import OUTPUT,SUMMARY,REPORTS,sha,read,identities,validation_versions
from loudness_latch_bdf_checkout_audit import EXPECTED_EXCEPTIONS,recover_historical_input,git_bytes
from loudness_latch_bdf_doubling_survey import canonical


class StaticInputs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = OUTPUT.read_bytes()
        cls.report = json.loads(gzip.decompress(cls.raw))

    def test_all_frozen_inputs_recover_from_committed_blobs_without_modification(self):
        # The frozen numerical receipt inherited a Gauss envelope label. Its typed
        # experiment identity is fixed by exact path, suite, command and data schema.
        receipt=read(ROOT/'evidence/loudness_latch_bdf_static_precision_charge_enclosure_validation.json')
        self.assertEqual(receipt['schema'],'rf-d/bdf-static-charge-gauss-validation/v1')
        self.assertEqual(len(receipt['attempts']),1)
        suite=receipt['attempts'][0]['suites'][0]
        self.assertEqual(suite['command'][-2:],["test_loudness_latch_bdf_static_precision_charge_enclosure.py","-v"])
        self.assertEqual(suite['reported_tests'],5);self.assertTrue(suite['passed'])
        self.assertEqual(read(ROOT/'evidence/loudness_latch_bdf_static_precision_charge_enclosure.json.gz')['schema'],
                         'rf-d/bdf-static-charge-enclosure/v1')
        report = self.report; archives = {r["path"]:r for r in report["archived_inputs"]}
        self.assertEqual(tuple(archives), EXPECTED_EXCEPTIONS)
        self.assertEqual(len(report["entries"]), 254)
        self.assertEqual(len(REPORTS), 38)
        recovered = {}
        for entry in report["entries"]:
            name = entry["path"]; blob = git_bytes(report["reference_git_head"], name)
            self.assertEqual(sha(blob), entry["git_blob_sha256"])
            raw = recover_historical_input(blob, archives[name]) if name in archives else blob
            self.assertEqual(sha(raw), entry["working_copy_sha256"])
            self.assertEqual(entry["identical_bytes"], name not in archives)
            recovered[name] = raw
        for path in REPORTS:
            data = read(path)
            for group in identities(data):
                for name, expected in group.items():
                    self.assertEqual(sha(recovered[name]), expected)
        versions=report["archived_validation_test_versions"]
        self.assertEqual(len(versions),5)
        for v in versions:
            self.assertEqual(sha(v["source_utf8"].encode("utf-8")),v["source_sha256"])
            receipt=read(ROOT/v["receipt"])
            archived=validation_versions(receipt)
            self.assertIn({k:value for k,value in v.items() if k!="receipt"},archived)
            self.assertEqual(receipt["attempts"][v["attempt_index"]]["source_sha256_before"][v["path"]],v["source_sha256"])
            self.assertNotEqual(sha(recovered[v["path"]]),v["source_sha256"])
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
        v=self.report["archived_validation_test_versions"][0]
        receipt=read(ROOT/v["receipt"])
        for suite in receipt["attempts"][v["attempt_index"]]["suites"]:
            if "failed_test_source_utf8" in suite:suite["failed_test_source_utf8"]+="\n"
        with self.assertRaisesRegex(ValueError,"failed test source identity"):
            validation_versions(receipt)


if __name__ == "__main__":
    unittest.main()
