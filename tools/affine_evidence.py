"""Bound source images by bytes and immutable Git references, without nested receipts."""
import base64,hashlib,json,re,subprocess
from pathlib import PurePosixPath
from prepare_dual_chain import ROOT,sha
from check_hybrid_voice import packed,unpack
def encode_json(value):return json.dumps(value,sort_keys=True,separators=(',',':')).encode()
def valid_name(name):
    p=PurePosixPath(name);assert not p.is_absolute() and '..' not in p.parts
    assert name.split('/')[0] in ['crates','tools','docs','evidence','plugin']
class Sources:
    def __init__(self,names):
        self.commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();self.hashes={};self.manifest={};self.images={}
        for name in sorted(set(names)):
            valid_name(name);data=(ROOT/name).read_bytes();h=hashlib.sha256(data).hexdigest();self.hashes[name]=h
            p=subprocess.run(['git','show',self.commit+':'+name],cwd=ROOT,capture_output=True)
            mode='exact' if p.returncode==0 and p.stdout==data else 'lf-to-crlf' if p.returncode==0 and p.stdout.replace(b'\n',b'\r\n')==data else None
            if mode:self.manifest[name]=dict(storage='git',commit=self.commit,path=name,sha256=h,git_sha256=hashlib.sha256(p.stdout).hexdigest(),materialization=mode)
            else:self.manifest[name]=dict(storage='image',sha256=h);self.images[name]=base64.b64encode(data).decode()
    def fields(self):return dict(source_sha256=self.hashes,source_manifest=self.manifest,source_images=packed(encode_json(self.images)))
    def unchanged(self):assert all(sha(ROOT/n)==h for n,h in self.hashes.items())
def recover(r):
    embedded=json.loads(unpack(r['source_images']));out={}
    assert set(r['source_manifest'])==set(r['source_sha256'])
    for name,entry in r['source_manifest'].items():
        valid_name(name)
        if entry['storage']=='image':data=base64.b64decode(embedded[name])
        else:
            assert entry['storage']=='git' and re.fullmatch('[0-9a-f]{40}',entry['commit']) and entry['path']==name
            data=subprocess.check_output(['git','show',entry['commit']+':'+name],cwd=ROOT);assert hashlib.sha256(data).hexdigest()==entry['git_sha256']
            assert entry['materialization'] in ['exact','lf-to-crlf']
            if entry['materialization']=='lf-to-crlf':data=data.replace(b'\n',b'\r\n')
        assert hashlib.sha256(data).hexdigest()==entry['sha256']==r['source_sha256'][name],name;out[name]=data
    assert set(embedded)=={n for n,e in r['source_manifest'].items() if e['storage']=='image'};return out
