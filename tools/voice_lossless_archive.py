"""Lossless storage only; never removes the source or changes electrical data."""
import gzip, hashlib, lzma, time
from pathlib import Path

CHUNK = 1024 * 1024
CODECS = ('gzip9', 'xz6-crc64')

def decoded_identity(path, codec):
    if codec not in CODECS:
        raise ValueError('unknown archive codec')
    opener = gzip.open if codec == 'gzip9' else lzma.open
    digest = hashlib.sha256(); size = 0
    with opener(path, 'rb') as stream:
        while chunk := stream.read(CHUNK):
            digest.update(chunk); size += len(chunk)
    return dict(sha256=digest.hexdigest(), bytes=size)

def verify(path, codec, sha256, size):
    actual = decoded_identity(path, codec)
    if actual != dict(sha256=sha256, bytes=size):
        raise ValueError('restored byte identity differs')
    return actual

def encode(source, target, codec):
    source, target = Path(source), Path(target)
    if codec not in CODECS or source.resolve() == target.resolve():
        raise ValueError('distinct paths and known codec required')
    start = time.perf_counter(); digest = hashlib.sha256(); size = 0
    # Exclusive creation preserves any previous attempt, including partial output.
    with source.open('rb') as incoming, target.open('xb') as destination:
        outgoing = (gzip.GzipFile(filename='', mode='wb', compresslevel=9,
                    fileobj=destination, mtime=0) if codec == 'gzip9' else
                    lzma.LZMAFile(destination, mode='wb', format=lzma.FORMAT_XZ,
                                  check=lzma.CHECK_CRC64, preset=6))
        with outgoing:
            while chunk := incoming.read(CHUNK):
                digest.update(chunk); size += len(chunk); outgoing.write(chunk)
    elapsed = time.perf_counter() - start
    check_start = time.perf_counter()
    restored = verify(target, codec, digest.hexdigest(), size)
    archive_digest = hashlib.sha256()
    with target.open('rb') as stream:
        while chunk := stream.read(CHUNK): archive_digest.update(chunk)
    return dict(codec=codec, original_sha256=digest.hexdigest(), original_bytes=size,
                archive_sha256=archive_digest.hexdigest(), archive_bytes=target.stat().st_size,
                encoding_s=elapsed, verification_s=time.perf_counter()-check_start,
                restored=restored, passed=True, source_retained=True)
