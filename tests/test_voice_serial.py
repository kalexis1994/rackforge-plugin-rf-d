import hashlib,json,os,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import voice_serial_archive as storage
import voice_serial_long as serial
import voice_binary_runner as runner

class SerialTests(unittest.TestCase):
    def seed(self,root):
        work=Path(root);data=bytes(range(256))*200+b'\x00\x80'
        raw=work/'nominal500.raw';raw.write_bytes(data)
        r=dict(raw_sha256=hashlib.sha256(data).hexdigest(),raw_bytes=len(data))
        runner.write(work/'nominal500.json',r)
        return work,data,r

    def test_roundtrip_both_codecs(self):
        for codec in storage.SUFFIX:
            with tempfile.TemporaryDirectory() as root:
                work,data,r=self.seed(root);original=(work/'nominal500.json').read_bytes()
                manifest=storage.archive_run(work,'nominal500',r,codec)
                self.assertTrue(manifest['raw_retired']);self.assertFalse((work/'nominal500.raw').exists())
                with storage.restored(work,'nominal500') as (raw,event):self.assertEqual(raw.read_bytes(),data)
                self.assertTrue(event['passed']);self.assertTrue(event['temporary_retired'])
                self.assertFalse(raw.exists());self.assertEqual((work/'nominal500.json').read_bytes(),original)

    def test_failed_consumer_preserves_restoration(self):
        with tempfile.TemporaryDirectory() as root:
            work,data,r=self.seed(root);storage.archive_run(work,'nominal500',r,'gzip9')
            with self.assertRaisesRegex(ValueError,'consumer'):
                with storage.restored(work,'nominal500') as (raw,event):raise ValueError('consumer')
            self.assertEqual(raw.read_bytes(),data);self.assertFalse(event['passed'])
            with self.assertRaises(ValueError):
                with storage.restored(work,'nominal500'):pass

    def test_modified_restoration_is_not_retired(self):
        with tempfile.TemporaryDirectory() as root:
            work,data,r=self.seed(root);storage.archive_run(work,'nominal500',r,'gzip9')
            with self.assertRaisesRegex(ValueError,'changed'):
                with storage.restored(work,'nominal500') as (raw,event):raw.write_bytes(b'diagnostic')
            self.assertEqual(raw.read_bytes(),b'diagnostic');self.assertFalse(event['temporary_retired'])

    def test_corrupt_container_never_creates_restoration(self):
        with tempfile.TemporaryDirectory() as root:
            work,data,r=self.seed(root);manifest=storage.archive_run(work,'nominal500',r,'gzip9')
            (work/manifest['archive_path']).write_bytes(b'corrupt')
            with self.assertRaises(ValueError):
                with storage.restored(work,'nominal500'):pass
            self.assertFalse((work/'nominal500.raw').exists())

    def test_wrong_receipt_retains_raw(self):
        with tempfile.TemporaryDirectory() as root:
            work,data,r=self.seed(root);bad=dict(r,raw_sha256='0'*64)
            runner.write(work/'nominal500.json',bad)
            with self.assertRaises(ValueError):storage.archive_run(work,'nominal500',bad,'gzip9')
            self.assertEqual((work/'nominal500.raw').read_bytes(),data)

    def test_verification_failure_retains_raw_and_container(self):
        with tempfile.TemporaryDirectory() as root:
            work,data,r=self.seed(root)
            with patch.object(storage.archive,'verify',side_effect=ValueError('verification')):
                with self.assertRaises(ValueError):storage.archive_run(work,'nominal500',r,'gzip9')
            self.assertEqual((work/'nominal500.raw').read_bytes(),data)
            self.assertTrue((work/'nominal500.raw.gz').exists())
            self.assertFalse((work/'nominal500.archive.json').exists())

    def test_paths_and_existing_attempt_preserved(self):
        with tempfile.TemporaryDirectory() as root:
            work,data,r=self.seed(root)
            for name,suffix in (('../nominal500','.raw'),('old','.raw'),('nominal500','.cir')):
                with self.assertRaises(ValueError):storage.member(work,name,suffix)
            p=work/'nominal500.raw.gz';p.write_bytes(b'previous')
            with self.assertRaises(ValueError):storage.archive_run(work,'nominal500',r,'gzip9')
            self.assertEqual(p.read_bytes(),b'previous');self.assertEqual((work/'nominal500.raw').read_bytes(),data)

    def test_hardlinked_original_not_retired(self):
        with tempfile.TemporaryDirectory() as root:
            work,data,r=self.seed(root);alias=work/'history.raw'
            os.link(work/'nominal500.raw',alias)
            with self.assertRaises(ValueError):storage.archive_run(work,'nominal500',r,'gzip9')
            self.assertEqual(alias.read_bytes(),data);self.assertTrue((work/'nominal500.raw').exists())

    def test_manifest_redirect_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            work,data,r=self.seed(root);m=storage.archive_run(work,'nominal500',r,'gzip9')
            m['original_path']='../old.raw';runner.write(work/'nominal500.archive.json',m)
            with self.assertRaises(ValueError):
                with storage.restored(work,'nominal500'):pass

    def test_budget_peak_and_phase_accounting(self):
        estimates={n:dict(estimated_long_export_bytes=x) for n,x in zip(storage.SCENES,(100,200,400,300))}
        b=serial.budget(estimates,.5,serial.MARGIN+900)
        self.assertTrue(b['passed']);self.assertEqual(b['required_free_bytes'],serial.MARGIN+900)
        self.assertFalse(serial.budget(estimates,.5,serial.MARGIN+899)['passed'])
        p=serial.phase_budget(estimates,.5,storage.SCENES[2:],serial.MARGIN+750)
        self.assertEqual(p['required_free_bytes'],serial.MARGIN+750);self.assertTrue(p['passed'])

    def test_incomplete_and_pending_never_complete_contrasts(self):
        bank=dict(records={'nominal500':dict(trajectory_complete=False)},archives={},electrical_errors={},
                  storage_errors={},resource_errors={'nominal250':'pending'},measurements={},comparisons={})
        def forbidden(name):self.fail('incomplete or missing scene must not restore')
        serial.evaluate(bank,forbidden)
        self.assertFalse(bank['long_note_admitted_locally']);self.assertEqual(len(bank['comparisons']),3)
        self.assertTrue(all(not c['measured'] for c in bank['comparisons'].values()))
        self.assertEqual(set(bank['electrical_errors']),{'nominal500'})

    def test_completed_scene_without_archive_is_storage_error(self):
        bank=dict(records={'nominal500':dict(trajectory_complete=True)},archives={},electrical_errors={},
                  storage_errors={},resource_errors={},measurements={},comparisons={})
        serial.evaluate(bank,lambda name:self.fail('archive missing'))
        self.assertFalse(bank['long_note_admitted_locally']);self.assertFalse(bank['electrical_errors'])
        self.assertEqual(set(bank['storage_errors']),{'nominal500'})

if __name__=='__main__':unittest.main()
