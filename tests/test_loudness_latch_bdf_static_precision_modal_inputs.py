import gzip
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from loudness_latch_bdf_static_precision_modal_inputs import OUTPUT,SUMMARY,REPORTS,sha,read,identities,validation_versions
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
        self.assertEqual(read(ROOT/"evidence/loudness_latch_bdf_static_precision_constitutive_enclosure_validation.json")["schema"],
                         "rf-d/bdf-static-constitutive-enclosure-validation/v1")
        self.assertEqual(read(ROOT/"evidence/loudness_latch_bdf_static_precision_correlated_enclosure_validation.json")["schema"],
                         "rf-d/bdf-static-correlated-enclosure-validation/v1")
        corrected=read(ROOT/"evidence/loudness_latch_bdf_static_precision_descriptor_forcing_norm.json.gz")
        self.assertEqual(corrected['schema'],'rf-d/bdf-static-descriptor-forcing-norm/v1')
        self.assertFalse(corrected['prior_uniform_budgets_valid'])
        self.assertFalse(corrected['rounded_inverse_numerically_admitted'])
        self.assertEqual(read(ROOT/"evidence/loudness_latch_bdf_static_precision_descriptor_forcing_norm_validation.json")['schema'],
                         'rf-d/bdf-static-descriptor-forcing-norm-validation/v1')
        weighted=read(ROOT/"evidence/loudness_latch_bdf_static_precision_weighted_descriptor.json.gz")
        self.assertEqual(weighted['schema'],'rf-d/bdf-static-weighted-descriptor/v1')
        self.assertEqual(sum(len(c['ideal_temporal_cover']) for c in weighted['cases']),64)
        self.assertTrue(all(c['ideal_temporal_inverse_certified'] for c in weighted['cases']))
        self.assertFalse(weighted['actual_dae_error_bound'])
        self.assertEqual(read(ROOT/"evidence/loudness_latch_bdf_static_precision_weighted_descriptor_validation.json")['schema'],
                         'rf-d/bdf-static-weighted-descriptor-validation/v1')
        cells=read(ROOT/"evidence/loudness_latch_bdf_static_precision_cell_propagation.json.gz")
        self.assertEqual(cells['schema'],'rf-d/bdf-static-cell-propagation/v1')
        self.assertEqual(sum(len(c['cells']) for c in cells['cases']),64)
        self.assertTrue(all(c['recombined_l1_nonincreasing'] for c in cells['cases']))
        self.assertFalse(cells['actual_dae_error_bound'])
        self.assertEqual(read(ROOT/"evidence/loudness_latch_bdf_static_precision_cell_propagation_validation.json")['schema'],
                         'rf-d/bdf-static-cell-propagation-validation/v1')
        attempt=read(ROOT/"evidence/loudness_latch_bdf_static_precision_cell_inputs_destination_attempt.json")
        self.assertTrue(attempt['rejected']);self.assertTrue(attempt['prior_bytes_restored_exactly'])
        self.assertEqual(sha(attempt['source_utf8'].encode()),attempt['source_sha256'])
        self.assertEqual(sha(git_bytes(attempt['git_head'],attempt['helper_path'])),attempt['source_sha256'])
        self.assertNotEqual(sha((ROOT/attempt['helper_path']).read_bytes()),attempt['source_sha256'])
        self.assertEqual(sha((ROOT/attempt['overwritten_path']).read_bytes()),attempt['restored_original_sha256'])
        self.assertEqual(sha((ROOT/attempt['first_data_path']).read_bytes()),attempt['first_data_sha256'])
        self.assertEqual(sha((ROOT/attempt['first_summary_path']).read_bytes()),attempt['first_summary_sha256'])
        self.assertFalse(attempt['numerical_data_modified']);self.assertFalse(attempt['numerical_measurement_repeated'])
        blocks=read(ROOT/"evidence/loudness_latch_bdf_static_precision_block_comparison.json.gz")
        self.assertEqual(blocks['schema'],'rf-d/bdf-static-block-comparison/v1')
        self.assertEqual(sum(len(c['cells']) for c in blocks['cases']),64)
        self.assertEqual(len(blocks['blocks']),6);self.assertFalse(blocks['block_partition_fitted'])
        self.assertFalse(blocks['actual_dae_error_bound'])
        self.assertEqual(read(ROOT/"evidence/loudness_latch_bdf_static_precision_block_comparison_validation.json")['schema'],
                         'rf-d/bdf-static-block-comparison-validation/v1')
        self.assertNotEqual(OUTPUT,SUMMARY);self.assertNotIn(OUTPUT,REPORTS);self.assertNotIn(SUMMARY,REPORTS)
        self.assertEqual(SUMMARY.name,'loudness_latch_bdf_static_precision_modal_inputs_summary.json')
        rms=read(ROOT/"evidence/loudness_latch_bdf_static_precision_junction_rms.json.gz")
        self.assertEqual(rms['schema'],'rf-d/bdf-static-junction-rms/v1')
        self.assertEqual(sum(len(c['cells']) for c in rms['cases']),64)
        self.assertTrue(rms['junction_norm_changed']);self.assertFalse(rms['block_partition_changed'])
        self.assertEqual(rms['initial_anchor_reference'],'common weighted infinity')
        self.assertFalse(rms['actual_dae_error_bound'])
        self.assertEqual(read(ROOT/"evidence/loudness_latch_bdf_static_precision_junction_rms_validation.json")['schema'],
                         'rf-d/bdf-static-junction-rms-validation/v1')
        spectral=read(ROOT/"evidence/loudness_latch_bdf_static_precision_junction_spectral.json.gz")
        self.assertEqual(spectral['schema'],'rf-d/bdf-static-junction-spectral/v1')
        self.assertEqual(sum(len(c['cells']) for c in spectral['cases']),64)
        self.assertEqual(spectral['exact_ldlt_probes'],2112)
        self.assertTrue(spectral['only_junction_diagonal_changed']);self.assertFalse(spectral['norm_changed'])
        self.assertEqual(spectral['initial_anchor_reference'],'common weighted infinity')
        self.assertFalse(spectral['actual_dae_error_bound'])
        self.assertEqual(read(ROOT/"evidence/loudness_latch_bdf_static_precision_junction_spectral_validation.json")['schema'],
                         'rf-d/bdf-static-junction-spectral-validation/v1')
        modal=read(ROOT/"evidence/loudness_latch_bdf_static_precision_junction_modal.json.gz")
        self.assertEqual(modal['schema'],'rf-d/bdf-static-junction-modal/v1')
        self.assertEqual(sum(len(c['cells']) for c in modal['cases']),64)
        self.assertTrue(modal['isolated_frozen_generator_only']);self.assertFalse(modal['time_varying_stability_certified'])
        self.assertFalse(modal['actual_dae_error_bound']);self.assertFalse(modal['prior_propagation_modified'])
        self.assertEqual(read(ROOT/"evidence/loudness_latch_bdf_static_precision_junction_modal_validation.json")['schema'],
                         'rf-d/bdf-static-junction-modal-validation/v1')
        report = self.report; archives = {r["path"]:r for r in report["archived_inputs"]}
        self.assertEqual(tuple(archives), EXPECTED_EXCEPTIONS)
        self.assertEqual(len(report["entries"]), len({entry["path"] for entry in report["entries"]}))
        self.assertEqual(len(REPORTS), 61)
        recovered = {}; declared_sources=set()
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
                    self.assertEqual(sha(recovered[name]), expected);declared_sources.add(name)
        self.assertEqual(set(recovered),declared_sources)
        versions=report["archived_validation_test_versions"]
        self.assertEqual(len(versions),8)
        for v in versions:
            self.assertEqual(sha(v["source_utf8"].encode("utf-8")),v["source_sha256"])
            receipt=read(ROOT/v["receipt"])
            archived=validation_versions(receipt)
            self.assertIn({k:value for k,value in v.items() if k!="receipt"},archived)
            self.assertEqual(receipt["attempts"][v["attempt_index"]]["source_sha256_before"][v["path"]],v["source_sha256"])
            self.assertNotEqual(sha(recovered[v["path"]]),v["source_sha256"])
        summary = json.loads(SUMMARY.read_text(encoding="utf-8")); storage = summary["storage"]
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
