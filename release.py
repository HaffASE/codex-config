#!/usr/bin/env python3
"""Verify package hashes or build a reproducible ZIP; no network or installation."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import re
import tempfile
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parent
ROOT_FILES = {'.gitignore', 'AGENTS.native.md', 'README.ru.md', 'VERSION',
              'check.py', 'doctor.py', 'install.py', 'release.py'}
ROOT_DIRS = {'agents', 'config', 'docs', 'migration', 'skills', 'templates',
             'tests', 'validation'}
IGNORED = {'.git', '.DS_Store', '__pycache__', '.local-validation'}


def package_files() -> list[Path]:
    files = []
    for item in ROOT.iterdir():
        if item.name in IGNORED:
            continue
        if item.name == 'SHA256SUMS':
            continue
        if item.name in ROOT_FILES and item.is_file() and not item.is_symlink():
            files.append(item)
        elif item.name in ROOT_DIRS and item.is_dir() and not item.is_symlink():
            for child in item.rglob('*'):
                if child.name in IGNORED or any(p in IGNORED for p in child.relative_to(item).parts):
                    continue
                if child.is_symlink() or (not child.is_file() and not child.is_dir()):
                    raise ValueError(f'Unsupported package node: {child}')
                if child.is_file():
                    files.append(child)
        else:
            raise ValueError(f'Unexpected package node: {item}')
    if {p.name for p in files if p.parent == ROOT} != ROOT_FILES:
        raise ValueError('Required root files are missing')
    return sorted(files, key=lambda p: p.relative_to(ROOT).as_posix())


def checksums(files: list[Path]) -> bytes:
    return ''.join(
        f'{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(ROOT).as_posix()}\n'
        for path in files
    ).encode()


def check(files: list[Path]) -> None:
    actual = (ROOT / 'SHA256SUMS').read_bytes()
    if actual != checksums(files):
        raise ValueError('SHA256SUMS differs from package contents; run --write after validation')


def build_zip(destination: Path, files: list[Path]) -> None:
    check(files)
    version = (ROOT / 'VERSION').read_text().strip()
    if not re.fullmatch(r'\d+\.\d+\.\d+', version):
        raise ValueError('VERSION must be a semantic release number')
    destination = destination.expanduser().resolve()
    if destination.is_relative_to(ROOT):
        raise ValueError('Write the release ZIP outside the source package')
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=destination.parent, prefix='.nck-release-',
                                     suffix='.zip', delete=False) as temporary:
        staged = Path(temporary.name)
    try:
        with ZipFile(staged, 'w', compression=ZIP_DEFLATED, compresslevel=9) as archive:
            for path in [*files, ROOT / 'SHA256SUMS']:
                name = 'native-codex-kit/' + path.relative_to(ROOT).as_posix()
                info = ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                info.compress_type = ZIP_DEFLATED
                archive.writestr(info, path.read_bytes(), compress_type=ZIP_DEFLATED,
                                 compresslevel=9)
        staged.replace(destination)
    finally:
        staged.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument('--write', action='store_true', help='Regenerate SHA256SUMS')
    action.add_argument('--zip', type=Path, metavar='PATH', help='Build a verified ZIP outside this repo')
    args = parser.parse_args()
    try:
        files = package_files()
        if args.write:
            (ROOT / 'SHA256SUMS').write_bytes(checksums(files))
            print(f'Wrote SHA256SUMS for {len(files)} files')
        elif args.zip:
            build_zip(args.zip, files)
            print(f'Wrote {args.zip}')
        else:
            check(files)
            print(f'PASS: {len(files)} package files match SHA256SUMS')
        return 0
    except (OSError, ValueError) as exc:
        parser.exit(2, f'ERROR: {exc}\n')


if __name__ == '__main__':
    raise SystemExit(main())
