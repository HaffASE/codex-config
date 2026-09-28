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

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--home'); p.add_argument('--codex-home'); p.add_argument('--repo')
    a=p.parse_args()
    home=Path(a.home).expanduser().resolve() if a.home else Path.home().resolve()
    selected=a.codex_home or (os.environ.get('CODEX_HOME') if not a.home else None)
    codex=Path(selected).expanduser().resolve() if selected else home/'.codex'
    repo=Path(a.repo).expanduser().resolve() if a.repo else None
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
