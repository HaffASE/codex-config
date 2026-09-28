#!/usr/bin/env python3
"""Run deterministic local package tests. Does not invoke Codex, models or the network."""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parent

def main() -> int:
    if sys.version_info<(3,11):
        print('Python 3.11+ required; nothing will be installed.',file=sys.stderr)
        return 2
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,help='Explicit directory for JSON result and logs; otherwise stdout only')
    args=parser.parse_args()
    results=[];logs=[]
    suites=[('package',ROOT/'tests'),('planning-guards',ROOT/'skills/feature-discovery/tests')]
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
    for name,directory in suites:
        command=[sys.executable,'-B','-m','unittest','discover','-s',str(directory),'-v']
        try:
            r=subprocess.run(command,cwd=ROOT,env=env,text=True,capture_output=True,timeout=120,check=False)
            log=r.stdout+r.stderr
            match=re.search(r'Ran (\d+) tests? in ',log)
            entry={'suite':name,'exit_code':r.returncode,'tests':int(match.group(1)) if match else 0,
                   'status':'PASS' if r.returncode==0 and match and int(match.group(1))>0 else 'FAIL'}
        except subprocess.TimeoutExpired:
            log='Suite timeout after 120 seconds; not PASS.'
            entry={'suite':name,'tests':0,'status':'TIMEOUT'}
        results.append(entry);logs.append((name,log))
        print(f'=== {name} ===\n{log}')
    outcome={'checked_at_utc':datetime.now(timezone.utc).isoformat(),
             'python_version':sys.version.split()[0],
             'suites':results,'total_tests':sum(x['tests'] for x in results),
             'result':'PASS' if all(x['status']=='PASS' for x in results) else 'FAIL',
             'scope':'Static structure and local deterministic filesystem/planning validators only',
             'live_codex_session':'NOT_RUN','model_behavior_evaluation':'NOT_RUN',
             'user_machine_migration':'NOT_PERFORMED'}
    if args.output:
        args.output.mkdir(parents=True,exist_ok=True)
        (args.output/'VALIDATION.json').write_text(json.dumps(outcome,ensure_ascii=False,indent=2)+'\n')
        for name,log in logs:(args.output/(name+'.txt')).write_text(log)
    print(json.dumps(outcome,ensure_ascii=False,indent=2))
    return 0 if outcome['result']=='PASS' else 1

if __name__=='__main__':
    raise SystemExit(main())
