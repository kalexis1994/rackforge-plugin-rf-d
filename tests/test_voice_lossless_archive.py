import hashlib, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import voice_lossless_archive as archive

class ArchiveTests(unittest.TestCase):
    def test_exact_both_codecs(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root)/'original';data=bytes(range(256))*1000+b'\x00\x80\x00\x00'
            p.write_bytes(data)
            for codec in archive.CODECS:
                target=Path(root)/codec;r=archive.encode(p,target,codec)
                self.assertTrue(r['passed']);self.assertEqual(p.read_bytes(),data)
                self.assertEqual(r['restored'],dict(sha256=hashlib.sha256(data).hexdigest(),bytes=len(data)))

    def test_wrong_identity_and_truncation(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root)/'original';p.write_bytes(bytes(range(256))*100)
            for codec in archive.CODECS:
                target=Path(root)/codec;r=archive.encode(p,target,codec)
                with self.assertRaises(ValueError):archive.verify(target,codec,'0'*64,r['original_bytes'])
                with self.assertRaises(ValueError):archive.verify(target,codec,r['original_sha256'],r['original_bytes']+1)
                target.write_bytes(target.read_bytes()[:-8])
                with self.assertRaises((EOFError,ValueError,OSError)):archive.decoded_identity(target,codec)
                self.assertTrue(p.exists())

    def test_no_overwrite_and_invalid_codec(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root)/'original';p.write_bytes(b'unchanged');target=Path(root)/'archive';target.write_bytes(b'previous')
            with self.assertRaises(FileExistsError):archive.encode(p,target,'gzip9')
            with self.assertRaises(ValueError):archive.encode(p,p,'gzip9')
            with self.assertRaises(ValueError):archive.encode(p,Path(root)/'other','unknown')
            self.assertEqual(target.read_bytes(),b'previous');self.assertEqual(p.read_bytes(),b'unchanged')

if __name__=='__main__':unittest.main()
