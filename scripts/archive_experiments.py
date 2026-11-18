#!/usr/bin/env python3
"""Package, verify, and restore full-run artifacts without running any evaluation."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
RUN = Path('experiments/runs/full-reference')
ARCHIVES = ROOT / 'experiments/artifacts'


def digest_file(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def add_digest(digest, name, size, sha256):
    digest.update(f'{name}\0{size}\0{sha256}\n'.encode())


def pack():
    ARCHIVES.mkdir(parents=True, exist_ok=True)
    records = []
    for folder in sorted((ROOT / RUN).iterdir()):
        if not folder.is_dir() or folder.name == 'source':
            continue
        paths = [p for name in ('checkpoints', 'traces') for p in (folder / name).rglob('*') if p.is_file()]
        paths += [folder / name for name in ('results.json', 'report.html') if (folder / name).is_file()]
        if not paths:
            continue
        archive = ARCHIVES / f'full-reference-{folder.name}.tar.gz'
        temporary = archive.with_suffix('.tmp')
        content_digest = hashlib.sha256()
        total_bytes = 0
        with temporary.open('wb') as raw:
            with gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0, compresslevel=6) as compressed:
                with tarfile.open(fileobj=compressed, mode='w|', format=tarfile.PAX_FORMAT) as tar:
                    for path in sorted(paths):
                        if path.is_symlink():
                            raise ValueError(f'Refusing symlink: {path}')
                        name = path.relative_to(ROOT).as_posix()
                        info = tar.gettarinfo(str(path), arcname=name)
                        info.uid = info.gid = 0
                        info.uname = info.gname = ''
                        with path.open('rb') as stream:
                            tar.addfile(info, stream)
                        add_digest(content_digest, name, info.size, digest_file(path))
                        total_bytes += info.size
        if temporary.stat().st_size >= 100 * 1024**2:
            raise ValueError(f'Archive exceeds GitHub single-file limit: {temporary}')
        temporary.replace(archive)
        record = dict(evaluation=folder.name, archive=archive.name, files=len(paths),
                      uncompressed_bytes=total_bytes, compressed_bytes=archive.stat().st_size,
                      sha256=digest_file(archive), content_sha256=content_digest.hexdigest())
        records.append(record)
        print(f'{folder.name}: {len(paths)} files, {record["compressed_bytes"] / 1024**2:.2f} MiB', flush=True)
    index = dict(format_version=1, source_run=RUN.as_posix(), archives=records)
    (ARCHIVES / 'index.json').write_text(json.dumps(index, indent=2) + '\n')


def inspect_archive(record, destination=None):
    archive = ARCHIVES / record['archive']
    if digest_file(archive) != record['sha256']:
        raise ValueError(f'Archive checksum mismatch: {archive}')
    expected_prefix = (*RUN.parts, record['evaluation'])
    count = total_bytes = 0
    content_digest = hashlib.sha256()
    with tarfile.open(archive, 'r|gz') as tar:
        for member in tar:
            name = PurePosixPath(member.name)
            if not member.isfile() or name.is_absolute() or '..' in name.parts or name.parts[:len(expected_prefix)] != expected_prefix:
                raise ValueError(f'Unsafe archive member: {member.name}')
            digest = hashlib.sha256()
            with tar.extractfile(member) as source:
                if destination is None:
                    while chunk := source.read(1024**2):
                        digest.update(chunk)
                else:
                    target = (destination / Path(*name.parts)).resolve()
                    if not target.is_relative_to(destination):
                        raise ValueError(f'Unsafe destination: {target}')
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as output:
                        temporary = Path(output.name)
                        while chunk := source.read(1024**2):
                            digest.update(chunk)
                            output.write(chunk)
                    try:
                        if target.exists():
                            if digest_file(target) != digest.hexdigest():
                                raise ValueError(f'Existing file differs; refusing overwrite: {target}')
                        else:
                            temporary.replace(target)
                            os.chmod(target, 0o644)
                            os.utime(target, (member.mtime, member.mtime))
                    finally:
                        temporary.unlink(missing_ok=True)
            add_digest(content_digest, member.name, member.size, digest.hexdigest())
            count += 1
            total_bytes += member.size
    if (count, total_bytes, content_digest.hexdigest()) != (record['files'], record['uncompressed_bytes'], record['content_sha256']):
        raise ValueError(f'Archive content mismatch: {archive}')
    return dict(evaluation=record['evaluation'], files=count, archive_sha256=record['sha256'], content_verified=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('pack', 'verify', 'restore'))
    parser.add_argument('--eval', help='Select one archived evaluator for verification/restoration')
    parser.add_argument('--destination', type=Path, default=ROOT, help='Root for restored paths; defaults to this checkout')
    args = parser.parse_args()
    if args.action == 'pack':
        pack()
        return
    index = json.loads((ARCHIVES / 'index.json').read_text())
    records = [r for r in index['archives'] if not args.eval or r['evaluation'] == args.eval]
    if not records:
        parser.error('No matching archive')
    destination = args.destination.resolve() if args.action == 'restore' else None
    if destination:
        destination.mkdir(parents=True, exist_ok=True)
    for record in records:
        print(json.dumps(inspect_archive(record, destination)), flush=True)
    if destination:
        # The full archive payload is restored without downloading models or invoking graders.
        print(f'Restored artifacts under {destination}')


if __name__ == '__main__':
    main()
