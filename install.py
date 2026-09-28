#!/usr/bin/env python3
"""Install local native Codex assets; dry-run by default, backups before replacement.

Python 3.11+, standard library only. No network, model calls, config rewriting,
credential access, package installs or OMX removal.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

ROOT = Path(__file__).resolve().parent
START = '<!-- native-codex-kit:start -->'
END = '<!-- native-codex-kit:end -->'
NAME = re.compile(r'[a-z][a-z0-9_-]*')


class InstallError(ValueError):
    pass


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fingerprint(path: Path) -> str:
    """Hash a node without following symlinks. Include empty directories."""
    if path.is_symlink():
        return 'link:' + os.readlink(path)
    if not path.exists():
        return 'absent'
    if path.is_file():
        return 'file:' + digest(path.read_bytes())
    if path.is_dir():
        entries = []
        for entry in sorted(path.iterdir(), key=lambda p: p.name):
            entries.append([entry.name, fingerprint(entry)])
        return 'dir:' + digest(json.dumps(entries, ensure_ascii=True).encode())
    raise InstallError(f'Unsupported filesystem node: {path}')


def remove_node(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        raise InstallError(f'Refusing to remove special file: {path}')


def copy_node(source: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if source.is_symlink():
        dest.symlink_to(os.readlink(source))
    elif source.is_dir():
        shutil.copytree(source, dest, symlinks=True)
    elif source.is_file():
        shutil.copy2(source, dest)
    else:
        raise InstallError(f'Cannot back up unsupported node: {source}')


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.nck-', delete=False) as f:
            tmp = Path(f.name)
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp, 0o600 if path.name == 'manifest.json' else 0o644)
        os.replace(tmp, path)
        tmp = None
    finally:
        if tmp is not None:
            tmp.unlink(missing_ok=True)


def safe_parents(target: Path, root: Path) -> None:
    """Reject links below a deliberately selected managed root."""
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise InstallError(f'Target is outside managed root: {target}') from exc
    current = target.parent
    while True:
        if current.is_symlink():
            raise InstallError(f'Refusing symlinked managed directory: {current}')
        if current.exists() and not current.is_dir():
            raise InstallError(f'Parent is not a directory: {current}')
        if current == root:
            break
        current = current.parent


def guidance(current: bytes, block: bytes) -> bytes:
    text = current.decode('utf-8')
    if text.count(START) != text.count(END) or text.count(START) > 1:
        raise InstallError('Malformed native-codex-kit guidance markers')
    new = f'{START}\n{block.decode("utf-8").strip()}\n{END}'
    if START in text:
        a, b = text.index(START), text.index(END)
        if b < a:
            raise InstallError('Reversed guidance markers')
        return (text[:a] + new + text[b + len(END):]).encode()
    separator = '' if not text or text.endswith('\n\n') else ('\n' if text.endswith('\n') else '\n\n')
    return (text + separator + new + '\n').encode()


def marked_block(data: bytes) -> tuple[bytes, int, int]:
    """Return the exact managed block and its byte offsets."""
    start, end = START.encode(), END.encode()
    if data.count(start) != 1 or data.count(end) != 1:
        raise InstallError('Malformed native-codex-kit guidance markers')
    a = data.index(start)
    b = data.index(end)
    if b < a:
        raise InstallError('Reversed guidance markers')
    b += len(end)
    return data[a:b], a, b


def active_path(codex: Path) -> Path:
    return codex/'backups'/'native-codex-kit'/'active.json'


def version() -> str:
    return (ROOT/'VERSION').read_text().strip()


@dataclass
class Change:
    target: Path
    kind: str
    source: Path | None = None
    data: bytes | None = None
    before: str = ''
    after: str = ''

    def prepare(self) -> None:
        self.before = fingerprint(self.target)
        self.after = ('link:' + str(self.source) if self.kind == 'link'
                      else 'file:' + digest(self.data or b''))

    def apply(self) -> None:
        self.target.parent.mkdir(parents=True, exist_ok=True)
        remove_node(self.target)
        if self.kind == 'link':
            assert self.source is not None
            self.target.symlink_to(self.source, target_is_directory=True)
        else:
            atomic_write(self.target, self.data or b'')


def roots(args: argparse.Namespace) -> tuple[Path, Path, Path]:
    home = Path(args.home).expanduser().resolve() if args.home else Path.home().resolve()
    selected = args.codex_home or (os.environ.get('CODEX_HOME') if not args.home else None)
    codex = Path(selected).expanduser().resolve() if selected else home / '.codex'
    skills = home / '.agents' / 'skills'
    return home, codex, skills


def plan(args: argparse.Namespace) -> tuple[list[Change], dict[str, str], list[str]]:
    home, codex, skills = roots(args)
    changes: list[Change] = []
    conflicts: list[str] = []
    if not args.agents_only:
        for p in sorted((ROOT/'skills').iterdir()):
            if not p.is_dir() or not (p/'SKILL.md').is_file():
                continue
            if not NAME.fullmatch(p.name):
                raise InstallError(f'Invalid skill name: {p.name}')
            changes.append(Change(skills/p.name, 'link', source=p.resolve()))
    for p in sorted((ROOT/'agents').glob('*.toml')):
        if not NAME.fullmatch(p.stem):
            raise InstallError(f'Invalid agent name: {p.stem}')
        changes.append(Change(codex/'agents'/p.name, 'file', data=p.read_bytes()))
    if args.with_guidance:
        p = codex/'AGENTS.md'
        if p.is_symlink() or (p.exists() and not p.is_file()):
            raise InstallError('AGENTS.md is not a regular file; merge guidance manually')
        override = codex/'AGENTS.override.md'
        if override.is_file() and override.stat().st_size:
            raise InstallError('AGENTS.override.md masks AGENTS.md; review the override before installing guidance')
        current = p.read_bytes() if p.exists() else b''
        if START.encode() in current or END.encode() in current:
            marked_block(current)
            if not active_path(codex).is_file():
                raise InstallError('Existing guidance block has no active inventory; review it manually')
        changes.append(Change(p, 'file', data=guidance(current, (ROOT/'AGENTS.native.md').read_bytes())))
    result = []
    for c in changes:
        managed_root = home if c.target.is_relative_to(home) else codex
        safe_parents(c.target, managed_root)
        if c.target == ROOT or ROOT.is_relative_to(c.target):
            raise InstallError('Installation target contains the source package')
        c.prepare()
        if c.before == c.after:
            continue
        is_guidance = c.target == codex/'AGENTS.md'
        if c.before != 'absent' and not args.replace and not is_guidance:
            conflicts.append(str(c.target))
        result.append(c)
    return result, {'home':str(home),'codex':str(codex),'skills':str(skills)}, conflicts


def execute(changes: list[Change], locations: dict[str, str], args: argparse.Namespace) -> Path | None:
    if not changes:
        return None
    codex = Path(locations['codex'])
    codex.mkdir(parents=True, exist_ok=True)
    lock = codex/'.native-codex-kit.install.lock'
    try:
        fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise InstallError(f'Installation lock exists; inspect it rather than deleting blindly: {lock}') from exc
    with os.fdopen(fd, 'w') as f:
        f.write(json.dumps({'pid':os.getpid(),'source':str(ROOT)}))
    backup = codex/'backups'/'native-codex-kit'/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid4().hex[:8])
    active = active_path(codex)
    done: list[tuple[Change,Path]] = []
    try:
        safe_parents(active, codex)
        if active.exists() or active.is_symlink():
            raise InstallError(f'Active installation exists; use --update or --remove: {active}')
        safe_parents(backup/'manifest.json', codex)
        backup.mkdir(parents=True, mode=0o700)
        records = []
        for i,c in enumerate(changes):
            if fingerprint(c.target) != c.before:
                raise InstallError(f'Target changed after preflight: {c.target}')
            old = backup/'originals'/f'{i:04d}'
            if c.before != 'absent':
                copy_node(c.target, old)
                if fingerprint(old) != c.before:
                    raise InstallError(f'Backup does not match source: {c.target}')
            rec={'target':str(c.target),'before':c.before,'installed':c.after,
                 'original':str(old.relative_to(backup))}
            if c.target == codex/'AGENTS.md':
                block,a,b=marked_block(c.data or b'')
                prior=c.target.read_bytes() if c.before!='absent' else b''
                rec['block']=digest(block)
                # Only whitespace added by this installer is removed with the block.
                rec['lead']=(c.data or b'')[:a][len(prior):].decode() if START.encode() not in prior else ''
                rec['tail']=(c.data or b'')[b:].decode() if START.encode() not in prior else ''
            records.append(rec)
        manifest = {'schema_version':1,'status':'prepared','source':str(ROOT),
                    'roots':locations,'records':records}
        atomic_write(backup/'manifest.json',json.dumps(manifest,indent=2).encode())
        for c,rec in zip(changes,records):
            if fingerprint(c.target) != c.before:
                raise InstallError(f'Target changed before write: {c.target}')
            done.append((c,backup/rec['original']))
            c.apply()
            if fingerprint(c.target) != c.after:
                raise InstallError(f'Installed content mismatch: {c.target}')
        manifest['status']='installed'
        atomic_write(backup/'manifest.json',json.dumps(manifest,indent=2).encode())
        inventory={'schema_version':1,'version':version(),'source':str(ROOT),
                   'roots':locations,'agents_only':args.agents_only,
                   'with_guidance':args.with_guidance,
                   'records':[dict(rec,original=str(backup/rec['original'])) for rec in records]}
        atomic_write(active,json.dumps(inventory,indent=2).encode())
        return backup/'manifest.json'
    except Exception:
        # Restore only nodes written in this transaction; never touch unrelated paths.
        for c,old in reversed(done):
            current=fingerprint(c.target)
            if current not in {'absent',c.after}:
                print(f'ROLLBACK NEEDS MANUAL REVIEW (concurrent change): {c.target}',file=sys.stderr)
                continue
            remove_node(c.target)
            if c.before != 'absent':
                copy_node(old,c.target)
        raise
    finally:
        lock.unlink(missing_ok=True)


def restore(args: argparse.Namespace) -> int:
    manifest_path = Path(args.restore).expanduser().resolve()
    home,codex,skills=roots(args)
    if (manifest_path.name!='manifest.json' or
            not manifest_path.is_relative_to(codex/'backups'/'native-codex-kit')):
        raise InstallError('Restore manifest is outside the selected Codex backup root')
    manifest_bytes=manifest_path.read_bytes()
    m = json.loads(manifest_bytes)
    expected={'home':str(home),'codex':str(codex),'skills':str(skills)}
    if m.get('schema_version')!=1 or m.get('status')!='installed' or m.get('roots')!=expected:
        raise InstallError('Backup is not an installed manifest for the selected home/CODEX_HOME')
    active=active_path(codex)
    if active.is_symlink():
        raise InstallError(f'Unsafe active inventory: {active}')
    preflight_active_bytes=None
    if active.exists():
        try:
            _,preflight_active_bytes,inventory=read_inventory(expected)
        except InstallError as exc:
            if str(exc).startswith(('Managed target changed:','Managed guidance block changed:')):
                raise InstallError('Installed file changed; refusing to overwrite user changes') from exc
            raise
        indexed={rec['target']:rec for rec in inventory['records']}
        if (len(indexed)!=len(m['records']) or any(
                indexed.get(rec['target'],{}).get('installed')!=rec['installed'] or
                indexed.get(rec['target'],{}).get('original')!=str(manifest_path.parent/rec['original'])
                for rec in m['records'])):
            raise InstallError('Backup does not describe the active installation; use --remove')
    items=[]
    for rec in m.get('records',[]):
        target=Path(rec['target'])
        valid=(target.parent==skills and bool(NAME.fullmatch(target.name))) or (
            target.parent==codex/'agents' and target.suffix=='.toml' and bool(NAME.fullmatch(target.stem))) or target==codex/'AGENTS.md'
        if not valid:
            raise InstallError(f'Unexpected restore target: {target}')
        safe_parents(target,home if target.is_relative_to(home) else codex)
        rel=Path(rec['original'])
        if rel.is_absolute() or '..' in rel.parts:
            raise InstallError('Unsafe backup path')
        old=manifest_path.parent/rel
        safe_parents(old,manifest_path.parent)
        if fingerprint(target)!=rec['installed']:
            raise InstallError(f'Installed file changed; refusing to overwrite user changes: {target}')
        if rec['before']!='absent' and fingerprint(old)!=rec['before']:
            raise InstallError(f'Backup content mismatch: {old}')
        items.append((target,old,rec))
    print(json.dumps({'mode':'restore' if args.apply else 'dry-run-restore',
                      'targets':[str(t) for t,_,_ in items]},indent=2))
    if not args.apply:
        return 0
    lock=codex/'.native-codex-kit.install.lock'
    try:
        fd=os.open(lock,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    except FileExistsError as exc:
        raise InstallError(f'Installation lock exists; inspect it rather than deleting blindly: {lock}') from exc
    with os.fdopen(fd,'w') as f:
        f.write(json.dumps({'pid':os.getpid(),'source':str(ROOT),'mode':'restore'}))
    backup=codex/'backups'/'native-codex-kit'/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid4().hex[:8])
    done=[]
    active_bytes=None
    try:
        safe_parents(active,codex)
        if active.is_symlink():
            raise InstallError(f'Unsafe active inventory: {active}')
        active_bytes=active.read_bytes() if active.is_file() else None
        if manifest_path.read_bytes()!=manifest_bytes or active_bytes!=preflight_active_bytes:
            raise InstallError('Restore metadata changed after preflight')
        # Recheck every target and backup under the lock before the first write.
        for target,old,rec in items:
            if fingerprint(target)!=rec['installed']:
                raise InstallError(f'Target changed during restore: {target}')
            if rec['before']!='absent' and fingerprint(old)!=rec['before']:
                raise InstallError(f'Backup content mismatch: {old}')
        safe_parents(backup/'manifest.json',codex)
        backup.mkdir(parents=True,mode=0o700)
        snapshots={}
        for i,(target,_,rec) in enumerate(items):
            snapshot=backup/'originals'/f'{i:04d}'
            copy_node(target,snapshot)
            if fingerprint(snapshot)!=rec['installed']:
                raise InstallError(f'Restore snapshot mismatch: {target}')
            snapshots[target]=snapshot
        atomic_write(backup/'manifest.json',json.dumps({'schema_version':1,
            'status':'prepared','mode':'restore','source_manifest':str(manifest_path),
            'targets':[str(t) for t,_,_ in items]},indent=2).encode())
        for target,old,rec in reversed(items):
            if fingerprint(target)!=rec['installed']:
                raise InstallError(f'Target changed during restore: {target}')
            done.append((target,snapshots[target],rec))
            remove_node(target)
            if rec['before']!='absent':
                copy_node(old,target)
            if fingerprint(target)!=rec['before']:
                raise InstallError(f'Restored content mismatch: {target}')
        m['status']='restored'
        atomic_write(manifest_path,json.dumps(m,indent=2).encode())
        if active_bytes is not None:
            if active.read_bytes()!=active_bytes:
                raise InstallError('Active inventory changed during restore')
            active.unlink()
        return 0
    except Exception:
        for target,snapshot,rec in reversed(done):
            if fingerprint(target) not in {'absent',rec['before'],rec['installed']}:
                print(f'ROLLBACK NEEDS MANUAL REVIEW (concurrent change): {target}',file=sys.stderr)
                continue
            try:
                remove_node(target)
                copy_node(snapshot,target)
                if fingerprint(target)!=rec['installed']:
                    raise InstallError(f'Rollback content mismatch: {target}')
            except Exception as exc:
                print(f'ROLLBACK NEEDS MANUAL REVIEW: {target}: {type(exc).__name__}',file=sys.stderr)
        if manifest_path.read_bytes()!=manifest_bytes:
            atomic_write(manifest_path,manifest_bytes)
        if active_bytes is not None and not active.exists():
            atomic_write(active,active_bytes)
        raise
    finally:
        lock.unlink(missing_ok=True)


def valid_target(target: Path, locations: dict[str,str]) -> bool:
    codex,skills=Path(locations['codex']),Path(locations['skills'])
    return ((target.parent==skills and bool(NAME.fullmatch(target.name))) or
            (target.parent==codex/'agents' and target.suffix=='.toml' and
             bool(NAME.fullmatch(target.stem))) or target==codex/'AGENTS.md')


def read_inventory(locations: dict[str,str]) -> tuple[Path,bytes,dict]:
    codex=Path(locations['codex'])
    active=active_path(codex)
    safe_parents(active,codex)
    if active.is_symlink() or not active.is_file():
        raise InstallError(f'No regular active installation inventory: {active}')
    raw=active.read_bytes()
    data=json.loads(raw)
    if (not isinstance(data,dict) or data.get('schema_version')!=1 or
            data.get('roots')!=locations or not isinstance(data.get('records'),list) or
            not isinstance(data.get('agents_only'),bool) or
            not isinstance(data.get('with_guidance'),bool)):
        raise InstallError('Invalid inventory for selected home/CODEX_HOME')
    seen=set()
    base=codex/'backups'/'native-codex-kit'
    for rec in data['records']:
        if not isinstance(rec,dict) or any(not isinstance(rec.get(k),str) for k in
                ('target','before','installed','original')):
            raise InstallError('Invalid inventory record')
        target=Path(rec['target'])
        if not target.is_absolute() or not valid_target(target,locations) or target in seen:
            raise InstallError(f'Unsafe or duplicate inventory target: {target}')
        seen.add(target)
        safe_parents(target,Path(locations['home']) if target.is_relative_to(Path(locations['home'])) else codex)
        old=Path(rec['original'])
        if (not old.is_absolute() or '..' in old.parts or not old.is_relative_to(base) or
                len(old.relative_to(base).parts)!=3 or old.parent.name!='originals' or
                not re.fullmatch(r'\d{4}',old.name)):
            raise InstallError(f'Unsafe inventory backup: {old}')
        safe_parents(old,codex)
        if rec['before']!='absent' and fingerprint(old)!=rec['before']:
            raise InstallError(f'Original backup content mismatch: {old}')
        if target==codex/'AGENTS.md':
            if any(not isinstance(rec.get(k),str) for k in ('block','lead','tail')):
                raise InstallError('Invalid guidance inventory')
            if target.is_symlink() or not target.is_file():
                raise InstallError(f'Managed guidance changed: {target}')
            block,_,_=marked_block(target.read_bytes())
            if digest(block)!=rec['block']:
                raise InstallError(f'Managed guidance block changed: {target}')
        elif fingerprint(target)!=rec['installed']:
            raise InstallError(f'Managed target changed: {target}')
    return active,raw,data


@dataclass
class LifecycleChange:
    target: Path
    before: str
    after: str
    kind: str
    source: Path | None = None
    data: bytes | None = None
    restore_from: Path | None = None

    def apply(self) -> None:
        remove_node(self.target)
        if self.kind=='link':
            assert self.source is not None
            self.target.parent.mkdir(parents=True,exist_ok=True)
            self.target.symlink_to(self.source,target_is_directory=True)
        elif self.kind=='file':
            atomic_write(self.target,self.data or b'')
        elif self.kind=='restore':
            assert self.restore_from is not None
            copy_node(self.restore_from,self.target)


def desired_assets(locations: dict[str,str], agents_only: bool) -> dict[Path,Change]:
    codex,skills=Path(locations['codex']),Path(locations['skills'])
    desired={}
    if not agents_only:
        for p in sorted((ROOT/'skills').iterdir()):
            if not p.is_dir() or not (p/'SKILL.md').is_file():
                continue
            if not NAME.fullmatch(p.name):
                raise InstallError(f'Invalid skill name: {p.name}')
            desired[skills/p.name]=Change(skills/p.name,'link',source=p.resolve())
    for p in sorted((ROOT/'agents').glob('*.toml')):
        if not NAME.fullmatch(p.stem):
            raise InstallError(f'Invalid agent name: {p.stem}')
        desired[codex/'agents'/p.name]=Change(codex/'agents'/p.name,'file',data=p.read_bytes())
    return desired


def lifecycle_plan(mode: str, inventory: dict, locations: dict[str,str],
                   replace: bool) -> tuple[list[LifecycleChange],list[dict],list[str]]:
    codex=Path(locations['codex'])
    prior={Path(rec['target']):rec for rec in inventory['records']}
    desired=desired_assets(locations,inventory['agents_only']) if mode=='update' else {}
    changes=[]
    records=[]
    conflicts=[]
    for target,rec in prior.items():
        current=fingerprint(target)
        if target==codex/'AGENTS.md':
            content=target.read_bytes()
            block,a,b=marked_block(content)
            if digest(block)!=rec['block']:
                raise InstallError(f'Managed guidance block changed: {target}')
            if mode=='update' and inventory['with_guidance']:
                new_content=guidance(content,(ROOT/'AGENTS.native.md').read_bytes())
                next_record=dict(rec,installed='file:'+digest(new_content),
                                 block=digest(marked_block(new_content)[0]))
                records.append(next_record)
                if new_content!=content:
                    changes.append(LifecycleChange(target,current,next_record['installed'],'file',data=new_content))
            else:
                lead,tail=rec['lead'].encode(),rec['tail'].encode()
                left,right=content[:a],content[b:]
                if lead and left.endswith(lead):
                    left=left[:-len(lead)]
                if tail and right.startswith(tail):
                    right=right[len(tail):]
                result=left+right
                kind='remove' if rec['before']=='absent' and not result else 'file'
                after='absent' if kind=='remove' else 'file:'+digest(result)
                changes.append(LifecycleChange(target,current,after,kind,data=result))
            continue
        if target in desired:
            wanted=desired.pop(target)
            wanted.prepare()
            next_record=dict(rec,installed=wanted.after)
            records.append(next_record)
            if current!=wanted.after:
                changes.append(LifecycleChange(target,current,wanted.after,wanted.kind,
                                               source=wanted.source,data=wanted.data))
        else:
            old=Path(rec['original'])
            kind='remove' if rec['before']=='absent' else 'restore'
            changes.append(LifecycleChange(target,current,rec['before'],kind,restore_from=old))
    if mode=='update':
        for target,wanted in desired.items():
            safe_parents(target,Path(locations['home']) if target.is_relative_to(Path(locations['home'])) else codex)
            if target==ROOT or ROOT.is_relative_to(target):
                raise InstallError('Installation target contains the source package')
            wanted.prepare()
            if wanted.before==wanted.after:
                continue  # Pre-existing identical asset remains unowned.
            if wanted.before!='absent' and not replace:
                conflicts.append(str(target))
            changes.append(LifecycleChange(target,wanted.before,wanted.after,wanted.kind,
                                           source=wanted.source,data=wanted.data))
            records.append({'target':str(target),'before':wanted.before,'installed':wanted.after,
                            'original':''})
    return changes,records,conflicts


def lifecycle_execute(mode: str, locations: dict[str,str], active: Path, raw: bytes,
                      inventory: dict, changes: list[LifecycleChange], records: list[dict]) -> None:
    codex=Path(locations['codex'])
    lock=codex/'.native-codex-kit.install.lock'
    try:
        fd=os.open(lock,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    except FileExistsError as exc:
        raise InstallError(f'Installation lock exists; inspect it rather than deleting blindly: {lock}') from exc
    with os.fdopen(fd,'w') as f:
        f.write(json.dumps({'pid':os.getpid(),'source':str(ROOT)}))
    backup=codex/'backups'/'native-codex-kit'/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid4().hex[:8])
    done=[]
    try:
        if active.read_bytes()!=raw:
            raise InstallError('Active inventory changed after preflight')
        # Verify all managed targets and their original backups again under the lock.
        read_inventory(locations)
        for c in changes:
            if fingerprint(c.target)!=c.before:
                raise InstallError(f'Target changed after preflight: {c.target}')
            if c.restore_from and fingerprint(c.restore_from)!=c.after:
                raise InstallError(f'Original backup changed: {c.restore_from}')
        safe_parents(backup/'manifest.json',codex)
        backup.mkdir(parents=True,mode=0o700)
        snapshots=[]
        for i,c in enumerate(changes):
            old=backup/'originals'/f'{i:04d}'
            if c.before!='absent':
                copy_node(c.target,old)
                if fingerprint(old)!=c.before:
                    raise InstallError(f'Transaction backup mismatch: {c.target}')
            snapshots.append(old)
            for rec in records:
                if rec['target']==str(c.target) and not rec['original']:
                    rec['original']=str(old)
        atomic_write(backup/'manifest.json',json.dumps({'schema_version':1,'status':'prepared',
            'mode':mode,'roots':locations,'records':[{'target':str(c.target),'before':c.before,
            'after':c.after,'snapshot':str(p)} for c,p in zip(changes,snapshots)]},indent=2).encode())
        for c,old in zip(changes,snapshots):
            if fingerprint(c.target)!=c.before:
                raise InstallError(f'Target changed before write: {c.target}')
            done.append((c,old))
            c.apply()
            if fingerprint(c.target)!=c.after:
                raise InstallError(f'Installed content mismatch: {c.target}')
        # The inventory is the commit marker. Keep the snapshot manifest descriptive
        # so a failed final inventory write never claims a completed update.
        if mode=='remove':
            active.unlink()
        else:
            updated=dict(inventory,version=version(),source=str(ROOT),records=records)
            atomic_write(active,json.dumps(updated,indent=2).encode())
    except Exception:
        for c,old in reversed(done):
            if fingerprint(c.target) not in {'absent',c.after}:
                print(f'ROLLBACK NEEDS MANUAL REVIEW (concurrent change): {c.target}',file=sys.stderr)
                continue
            remove_node(c.target)
            if c.before!='absent':
                copy_node(old,c.target)
        raise
    finally:
        lock.unlink(missing_ok=True)


def lifecycle(args: argparse.Namespace, mode: str) -> int:
    home,codex,skills=roots(args)
    locations={'home':str(home),'codex':str(codex),'skills':str(skills)}
    active,raw,inventory=read_inventory(locations)
    changes,records,conflicts=lifecycle_plan(mode,inventory,locations,args.replace)
    print(json.dumps({'mode':mode if args.apply else 'dry-run-'+mode,'roots':locations,
                      'changes':[{'target':str(c.target),'action':c.kind} for c in changes],
                      'conflicts':conflicts},indent=2))
    if conflicts:
        raise InstallError('Existing targets differ. Review them; use --replace only for deliberate backed-up replacement.')
    if args.apply:
        if (mode=='update' and not changes and records==inventory['records'] and
                inventory.get('version')==version() and inventory.get('source')==str(ROOT)):
            print('Already up to date.')
            return 0
        lifecycle_execute(mode,locations,active,raw,inventory,changes,records)
        print('Updated active installation.' if mode=='update' else 'Removed active installation.')
    else:
        print('No files changed. Repeat with --apply to '+mode+'.')
    return 0


def parser() -> argparse.ArgumentParser:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--apply',action='store_true',help='Apply changes; otherwise only preview')
    p.add_argument('--replace',action='store_true',help='Replace colliding kit targets after backing them up')
    p.add_argument('--with-guidance',action='store_true',help='Merge a marked block into global AGENTS.md')
    p.add_argument('--agents-only',action='store_true',help='Install only standalone custom agents')
    p.add_argument('--home',help='Explicit home for isolated testing or a deliberate installation')
    p.add_argument('--codex-home',help='Explicit Codex home; otherwise honors CODEX_HOME')
    p.add_argument('--restore',help='Restore this installer\'s backup manifest; dry-run unless --apply')
    lifecycle=p.add_mutually_exclusive_group()
    lifecycle.add_argument('--update',action='store_true',help='Reconcile an active installation with this kit')
    lifecycle.add_argument('--remove',action='store_true',help='Remove an active installation and restore originals')
    return p


def main(argv: list[str] | None=None) -> int:
    args=parser().parse_args(argv)
    try:
        if args.restore:
            if args.replace or args.with_guidance or args.agents_only or args.update or args.remove:
                raise InstallError('--restore cannot be combined with installation options')
            return restore(args)
        if args.update or args.remove:
            if args.with_guidance or args.agents_only or (args.remove and args.replace):
                raise InstallError('Selection flags are fixed by the active installation')
            return lifecycle(args,'update' if args.update else 'remove')
        changes,locations,conflicts=plan(args)
        active=active_path(Path(locations['codex']))
        if changes and (active.exists() or active.is_symlink()):
            raise InstallError('Active installation exists; use --update to reconcile it')
        print(json.dumps({'mode':'apply' if args.apply else 'dry-run','roots':locations,
                          'changes':[{'target':str(c.target),'action':'create' if c.before=='absent' else 'replace',
                                      'kind':c.kind} for c in changes], 'conflicts':conflicts},indent=2))
        if conflicts:
            raise InstallError('Existing targets differ. Review them; use --replace only for deliberate backed-up replacement.')
        if not args.apply:
            print('No files changed. Repeat with --apply to install.')
            return 0
        backup=execute(changes,locations,args)
        print('Installed. Backup manifest: '+str(backup) if backup else 'Already installed; no changes.')
        print('Restart Codex and run doctor.py. No config, auth, hooks, OMX data or repository files were rewritten.')
        return 0
    except (InstallError,OSError,ValueError) as exc:
        print('ERROR: '+str(exc),file=sys.stderr)
        return 2


if __name__=='__main__':
    raise SystemExit(main())
