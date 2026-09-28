#!/usr/bin/env python3
"""Read-only local inventory. Does not authenticate, spawn agents or inspect credentials."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
sys.dont_write_bytecode = True
import install as kit_install
try:
    import tomllib
except ImportError:
    raise SystemExit('Python 3.11+ is required; this tool installs nothing.')

MARKERS=re.compile(r'(?i)\boh-my-codex\b|\bomx\b|\.omx[/\\]|mcp__omx')

def scan(path: Path, findings: list[dict]) -> None:
    if not path.is_file(): return
    if path.stat().st_size>1024*1024:
        findings.append({'kind':'not_scanned','path':str(path),'reason':'larger than 1 MiB'})
        return
    try: lines=path.read_text().splitlines()
    except (OSError,UnicodeError):
        findings.append({'kind':'not_scanned','path':str(path),'reason':'unreadable text'})
        return
    for i,line in enumerate(lines,1):
        if MARKERS.search(line):
            # Do not echo config content: lines can contain user credentials.
            findings.append({'kind':'possible_omx_reference','path':str(path),'line':i,
                             'note':'Inspect locally; a historical mention is not a live dependency.'})


def skill_frontmatter_name(path: Path) -> str | None:
    """Read only a small, explicit SKILL.md frontmatter name."""
    try:
        if not path.is_file() or path.stat().st_size > 65536:
            return None
        lines=path.read_text(encoding='utf-8').splitlines()
    except (OSError,UnicodeError):
        return None
    if not lines or lines[0].strip()!='---':
        return None
    try:
        closing=next(i for i,line in enumerate(lines[1:],1) if line.strip()=='---')
    except StopIteration:
        return None
    names=[]
    for line in lines[1:closing]:
        match=re.fullmatch(r'name:\s*(?:"([^"]+)"|\'([^\']+)\'|([a-z][a-z0-9_-]*))\s*',line)
        if match:
            names.append(next(value for value in match.groups() if value is not None))
    return names[0] if len(names)==1 and kit_install.NAME.fullmatch(names[0]) else None


def focused_skill(name: str, home: Path, codex: Path, repo: Path | None) -> int:
    roots=[home/'.agents/skills',codex/'skills']
    if repo:
        roots += [repo/'.agents/skills',repo/'.codex/skills']
    target=roots[0]/name
    package=kit_install.ROOT/'skills'/name
    active=kit_install.active_path(codex)
    result={'skill':name,'package_present':False,
            'inventory_state':'absent','managed_target':{'path':str(target),'state':'indeterminate'},
            'ownership':'indeterminate','candidate_roots':[str(root) for root in roots],
            'possible_collisions':[],'collision_verification':'not_verified',
            'source_bytes_verified':False,'runtime_discovery':'not_verified'}
    def emit(code: int) -> int:
        print(json.dumps(result,ensure_ascii=False,separators=(',',':')))
        return code
    if not kit_install.NAME.fullmatch(name):
        result['skill']=None
        result['error']='invalid_skill_name'
        return emit(2)
    locations={'home':str(home),'codex':str(codex),'skills':str(roots[0])}
    try:
        kit_install.safe_parents(target,home)
        kit_install.safe_parents(active,codex)
        if package.is_symlink():
            result['error']='unsafe_package_path'
            return emit(2)
        result['package_present']=package.is_dir() and (package/'SKILL.md').is_file()
        inventory=None
        if active.exists() or active.is_symlink():
            try:
                _,_,inventory=kit_install.read_inventory(locations)
                result['inventory_state']='valid'
            except (kit_install.InstallError,OSError,ValueError,KeyError,TypeError):
                result['inventory_state']='drift'
                result['error']='inventory_validation_failed'
                return emit(2)
        record=next((rec for rec in inventory['records'] if rec['target']==str(target)),None) if inventory else None
        if not result['package_present'] and record is None:
            result['ownership']='unmanaged'
            result['error']='unknown_skill'
            return emit(2)
        if record is not None and not record['installed'].startswith('link:'):
            result['error']='invalid_managed_skill_record'
            return emit(2)
        result['ownership']='recorded' if record else 'unmanaged'
        if record and not result['package_present']:
            state='retired'
        elif target.is_symlink():
            if not target.exists():
                state='broken_link' if record else 'foreign_broken'
            elif target.resolve()==package.resolve():
                state='link_current'
            else:
                state='stale_link' if record else 'foreign'
        elif target.exists():
            state='foreign'
        else:
            state='missing'
        result['managed_target']['state']=state
        for root in roots:
            boundary=repo if repo and root.is_relative_to(repo) else (codex if root.is_relative_to(codex) else home)
            kit_install.safe_parents(root/name,boundary)
            if root.is_symlink():
                result['managed_target']['state']='indeterminate'
                result['ownership']='indeterminate'
                result['error']='unsafe_candidate_root'
                return emit(2)
            if not root.exists():
                continue
            if not root.is_dir():
                result['managed_target']['state']='indeterminate'
                result['ownership']='indeterminate'
                result['error']='unsafe_candidate_root'
                return emit(2)
            for entry in sorted(root.iterdir()):
                by=[]
                if entry.name==name:
                    by.append('directory_basename')
                if skill_frontmatter_name(entry/'SKILL.md')==name:
                    by.append('frontmatter_name')
                if by and (entry!=target or state not in {'link_current','missing','retired'}):
                    result['possible_collisions'].append({'path':str(entry),'matched_by':by})
    except (kit_install.InstallError,OSError,ValueError,KeyError,TypeError):
        result['managed_target']['state']='indeterminate'
        result['ownership']='indeterminate'
        result['error']='unsafe_or_unreadable_path'
        return emit(2)
    return emit(0)

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--home'); p.add_argument('--codex-home'); p.add_argument('--repo')
    p.add_argument('--skill',help='Read-only focused status for one packaged or recorded skill')
    a=p.parse_args()
    home=Path(a.home).expanduser().resolve() if a.home else Path.home().resolve()
    selected=a.codex_home or (os.environ.get('CODEX_HOME') if not a.home else None)
    codex=Path(selected).expanduser().resolve() if selected else home/'.codex'
    repo=Path(a.repo).expanduser().resolve() if a.repo else None
    if a.skill is not None:
        return focused_skill(a.skill,home,codex,repo)
    out={'codex_home':str(codex),'skills_root':str(home/'.agents/skills'),
         'native_runtime':'not_verified','model_authentication':'not_probed',
         'goal_support':'confirm in the installed interactive client',
         'agent_discovery':'confirm actual configured-role spawn in a new Codex session',
         'scope':'Selected config/guidance/skill roots; not a full machine or plugin-cache scan',
         'findings':[],'skills':[],'agents':[],
         'installation':{'status':'not_installed','inventory':str(kit_install.active_path(codex))}}
    locations={'home':str(home),'codex':str(codex),'skills':str(home/'.agents/skills')}
    active=kit_install.active_path(codex)
    if active.exists() or active.is_symlink():
        try:
            _,_,inventory=kit_install.read_inventory(locations)
            out['installation']={'status':'installed','inventory':str(active),
                                 'version':inventory['version'],'source':inventory['source']}
            desired=kit_install.desired_assets(locations,inventory['agents_only'])
            managed={Path(rec['target']):rec for rec in inventory['records']}
            for target,rec in managed.items():
                if target==codex/'AGENTS.md':
                    expected_block=kit_install.marked_block(kit_install.guidance(
                        b'',(kit_install.ROOT/'AGENTS.native.md').read_bytes()))[0]
                    if kit_install.digest(expected_block)!=rec['block']:
                        out['findings'].append({'kind':'kit_update_available','path':str(target)})
                    continue
                wanted=desired.pop(target,None)
                if wanted is None:
                    out['findings'].append({'kind':'retired_kit_asset','path':str(target)})
                    continue
                wanted.prepare()
                if wanted.after!=rec['installed']:
                    out['findings'].append({'kind':'kit_update_available','path':str(target)})
            for target,wanted in desired.items():
                wanted.prepare()
                if kit_install.fingerprint(target)!=wanted.after:
                    out['findings'].append({'kind':'new_kit_asset','path':str(target)})
            if inventory['version']!=kit_install.version():
                out['findings'].append({'kind':'kit_version_differs',
                                        'installed':inventory['version'],
                                        'package':kit_install.version()})
        except (kit_install.InstallError,OSError,ValueError,KeyError,TypeError) as exc:
            out['installation']={'status':'drift','inventory':str(active)}
            out['findings'].append({'kind':'installation_drift','error':type(exc).__name__,
                                    'note':'Inspect the active inventory and managed files locally.'})
    exe=shutil.which('codex')
    out['codex_binary']=exe
    if exe:
        try:
            r=subprocess.run([exe,'--version'],capture_output=True,text=True,timeout=10,check=False)
            out['codex_version']=(r.stdout or r.stderr).strip()[:250]
            if r.returncode: out['findings'].append({'kind':'version_command_failed','exit':r.returncode})
        except (OSError,subprocess.TimeoutExpired) as exc:
            out['findings'].append({'kind':'version_probe_failed','error':type(exc).__name__})
    else:
        out['findings'].append({'kind':'codex_not_on_path'})
    configs=[codex/'config.toml']+([repo/'.codex/config.toml'] if repo else [])
    for c in configs:
        scan(c,out['findings'])
        if c.is_file():
            try:
                data=tomllib.loads(c.read_text())
                agents = data.get('agents', {})
                skills_config = data.get('skills', {})
                if not isinstance(agents, dict) or not isinstance(skills_config, dict):
                    raise ValueError('agents and skills must be tables')
                configured = skills_config.get('config', [])
                if not isinstance(configured, list) or not all(isinstance(x, dict) for x in configured):
                    raise ValueError('skills.config must be an array of tables')
                if agents.get('enabled') is False:
                    out['findings'].append({'kind':'agents_disabled','path':str(c)})
                disabled=[x.get('path','unknown') for x in configured if x.get('enabled') is False]
                for item in disabled: out['findings'].append({'kind':'disabled_skill','path':str(item)})
            except (ValueError,OSError) as exc:
                out['findings'].append({'kind':'invalid_config','path':str(c),'error':type(exc).__name__})
    guidance=[codex/'AGENTS.md',codex/'AGENTS.override.md',codex/'hooks.json']
    if repo: guidance += [repo/'AGENTS.md',repo/'AGENTS.override.md',repo/'.codex/hooks.json']
    for c in guidance: scan(c,out['findings'])
    if (codex/'AGENTS.override.md').is_file() and (codex/'AGENTS.override.md').stat().st_size:
        out['findings'].append({'kind':'global_guidance_override','path':str(codex/'AGENTS.override.md')})
    roots=[home/'.agents/skills',codex/'skills']
    if repo: roots += [repo/'.agents/skills',repo/'.codex/skills']
    names={}
    for root in roots:
        if not root.is_dir(): continue
        for d in sorted(root.iterdir()):
            f=d/'SKILL.md'
            if d.is_symlink() and not d.exists():
                out['findings'].append({'kind':'broken_skill_link','path':str(d)}); continue
            if not f.is_file(): continue
            try:
                text=f.read_text(errors='replace')[:16000]
            except OSError:
                out['findings'].append({'kind':'unreadable_skill','path':str(f)})
                continue
            m=re.search(r'^name:\s*["\']?([^\n"\']+)',text,re.M)
            name=m.group(1).strip() if m else d.name
            names.setdefault(name,[]).append(str(f))
            out['skills'].append({'name':name,'path':str(f),'source':str(f.resolve())})
            scan(f,out['findings'])
    for name,paths in names.items():
        if len(paths)>1:
            out['findings'].append({'kind':'possible_duplicate_skill','name':name,'paths':paths,
                                    'note':'Includes legacy candidate roots; verify actual active discovery.'})
    agent_roots=[codex/'agents']+([repo/'.codex/agents'] if repo else [])
    agent_names={}
    for root in agent_roots:
        for f in sorted(root.glob('*.toml')):
            scan(f,out['findings'])
            try:
                d=tomllib.loads(f.read_text())
                missing=[k for k in ['name','description','developer_instructions'] if not isinstance(d.get(k),str) or not d[k].strip()]
                if missing: out['findings'].append({'kind':'legacy_or_invalid_agent','path':str(f),'missing':missing})
                else:
                    out['agents'].append({'name':d['name'],'path':str(f),'model':d.get('model','inherit'),
                                          'sandbox_default':d.get('sandbox_mode','inherit')})
                    agent_names.setdefault(d['name'],[]).append(str(f))
            except (ValueError,OSError) as exc:
                out['findings'].append({'kind':'invalid_agent','path':str(f),'error':type(exc).__name__})
    for name,paths in agent_names.items():
        if len(paths)>1: out['findings'].append({'kind':'duplicate_agent_name','name':name,'paths':paths})
    print(json.dumps(out,ensure_ascii=False,indent=2))
    fatal={'codex_not_on_path','invalid_config','agents_disabled','invalid_agent','legacy_or_invalid_agent','broken_skill_link','unreadable_skill','installation_drift'}
    return 2 if any(f['kind'] in fatal for f in out['findings']) else 0

if __name__=='__main__':
    raise SystemExit(main())
