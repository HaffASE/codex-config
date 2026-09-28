"""Filesystem-only checks. No real home, network, Codex session or model calls."""
from __future__ import annotations
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('kit_install',ROOT/'install.py')
installer=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=installer
spec.loader.exec_module(installer)

class InstallationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home=Path(self.tmp.name)/'home'
        self.home.mkdir()
        self.codex=self.home/'.codex'
        self.skills=self.home/'.agents/skills'

    def run_install(self,*args):
        stdout,stderr=io.StringIO(),io.StringIO()
        with contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stderr):
            rc=installer.main(['--home',str(self.home),*map(str,args)])
        return rc,stdout.getvalue(),stderr.getvalue()

    def manifests(self):
        return list(self.codex.glob('backups/native-codex-kit/*/manifest.json'))

    def kit_copy(self):
        """A disposable source package for lifecycle tests that change kit assets."""
        kit=Path(self.tmp.name)/'kit'
        kit.mkdir()
        for name in ('skills','agents'):
            shutil.copytree(ROOT/name,kit/name)
        for name in ('VERSION','AGENTS.native.md'):
            shutil.copy2(ROOT/name,kit/name)
        return kit

    def test_dry_run_creates_nothing(self):
        before=installer.fingerprint(self.home)
        rc,out,_=self.run_install()
        self.assertEqual(rc,0,out)
        self.assertIn('No files changed',out)
        self.assertEqual(installer.fingerprint(self.home),before)

    def test_apply_installs_links_and_native_agents_without_config(self):
        rc,out,err=self.run_install('--apply')
        self.assertEqual(rc,0,err)
        self.assertEqual(len(list(self.skills.iterdir())),17)
        for p in self.skills.iterdir():
            self.assertTrue(p.is_symlink())
            self.assertEqual(p.resolve(),ROOT/'skills'/p.name)
        self.assertEqual(len(list((self.codex/'agents').glob('*.toml'))),13)
        self.assertFalse((self.codex/'config.toml').exists())
        self.assertFalse((self.codex/'AGENTS.md').exists())
        self.assertEqual(len(self.manifests()),1)

    def test_second_apply_is_idempotent(self):
        self.assertEqual(self.run_install('--apply')[0],0)
        before=installer.fingerprint(self.home)
        rc,out,err=self.run_install('--apply')
        self.assertEqual(rc,0,err)
        self.assertIn('Already installed',out)
        self.assertEqual(installer.fingerprint(self.home),before)

    def test_collision_blocks_all_writes(self):
        p=self.skills/'code-review'
        p.mkdir(parents=True);(p/'SKILL.md').write_text('custom skill')
        before=installer.fingerprint(self.home)
        rc,_,err=self.run_install('--apply')
        self.assertEqual(rc,2)
        self.assertIn('Existing targets differ',err)
        self.assertEqual(installer.fingerprint(self.home),before)

    def test_replace_and_restore_original_directory_and_broken_symlink(self):
        p=self.skills/'code-review';p.mkdir(parents=True)
        (p/'SKILL.md').write_text('custom skill')
        (p/'empty').mkdir()
        other=self.skills/'checkpoint';other.symlink_to('/does-not-exist/original')
        original=installer.fingerprint(p)
        self.assertEqual(self.run_install('--replace','--apply')[0],0)
        manifest=self.manifests()[0]
        self.assertEqual(self.run_install('--restore',manifest)[0],0)
        self.assertTrue(p.is_symlink()) # restoration preview does not apply
        rc,_,err=self.run_install('--restore',manifest,'--apply')
        self.assertEqual(rc,0,err)
        self.assertEqual(installer.fingerprint(p),original)
        self.assertEqual(os.readlink(other),'/does-not-exist/original')
        self.assertEqual(json.loads(manifest.read_text())['status'],'restored')

    def test_restore_refuses_new_user_edits_before_touching_anything(self):
        self.assertEqual(self.run_install('--apply')[0],0)
        p=self.codex/'agents/nc_scout.toml'
        p.write_text(p.read_text()+'\n# User edited\n')
        before=installer.fingerprint(self.home)
        rc,_,err=self.run_install('--restore',self.manifests()[0],'--apply')
        self.assertEqual(rc,2)
        self.assertIn('user changes',err)
        self.assertEqual(installer.fingerprint(self.home),before)

    def test_restore_rolls_back_if_copy_fails_after_a_prior_target(self):
        originals={}
        for name in ('browser-debug','checkpoint'):
            path=self.skills/name
            path.mkdir(parents=True)
            (path/'SKILL.md').write_text('user '+name)
            originals[path]=installer.fingerprint(path)
        self.assertEqual(self.run_install('--replace','--apply')[0],0)
        active=installer.active_path(self.codex)
        inventory=active.read_bytes()
        installed={path:installer.fingerprint(path) for path in originals}
        manifest=self.manifests()[0]
        real_copy=installer.copy_node
        restored=0
        def fail_second_original(source,dest):
            nonlocal restored
            if (dest.parent.resolve()==self.skills.resolve() and dest.name in {'browser-debug','checkpoint'}
                    and source.resolve().is_relative_to(manifest.parent.resolve())):
                restored+=1
                if restored==2:
                    raise OSError('injected restore failure')
            return real_copy(source,dest)
        with patch.object(installer,'copy_node',fail_second_original):
            rc,_,err=self.run_install('--restore',manifest,'--apply')
        self.assertEqual(rc,2)
        self.assertIn('injected restore failure',err)
        self.assertEqual({path:installer.fingerprint(path) for path in originals},installed)
        self.assertEqual(active.read_bytes(),inventory)
        self.assertEqual(json.loads(manifest.read_text())['status'],'installed')
        self.assertEqual(self.run_install('--remove','--apply')[0],0)
        self.assertEqual({path:installer.fingerprint(path) for path in originals},originals)

    def test_config_auth_hooks_and_omx_are_untouched(self):
        self.codex.mkdir()
        paths=[self.codex/'config.toml',self.codex/'auth.json',self.codex/'hooks.json',self.home/'.omx/state.json']
        for p in paths:
            p.parent.mkdir(exist_ok=True);p.write_text('preserve '+p.name)
        previous={p:p.read_bytes() for p in paths}
        self.assertEqual(self.run_install('--apply')[0],0)
        self.assertEqual(previous,{p:p.read_bytes() for p in paths})

    def test_guidance_preserves_original_bytes_and_is_idempotent(self):
        self.codex.mkdir();p=self.codex/'AGENTS.md'
        original=b'# My rules\nImportant trailing spaces.  \n\n\n'
        p.write_bytes(original)
        self.assertEqual(self.run_install('--with-guidance','--apply')[0],0)
        current=p.read_bytes()
        self.assertTrue(current.startswith(original))
        self.assertEqual(current.count(installer.START.encode()),1)
        self.assertEqual(self.run_install('--with-guidance','--apply')[0],0)
        self.assertEqual(p.read_bytes(),current)
        self.assertEqual(self.run_install('--restore',self.manifests()[0],'--apply')[0],0)
        self.assertEqual(p.read_bytes(),original)

    def test_override_refuses_guidance_without_other_changes(self):
        self.codex.mkdir();(self.codex/'AGENTS.override.md').write_text('override')
        before=installer.fingerprint(self.home)
        rc,_,err=self.run_install('--with-guidance','--apply')
        self.assertEqual(rc,2)
        self.assertIn('masks',err)
        self.assertEqual(installer.fingerprint(self.home),before)

    def test_malformed_guidance_markers_refuse(self):
        self.codex.mkdir();(self.codex/'AGENTS.md').write_text(installer.START+'\nunfinished')
        before=installer.fingerprint(self.home)
        rc,_,err=self.run_install('--with-guidance','--apply')
        self.assertEqual(rc,2)
        self.assertIn('Malformed',err)
        self.assertEqual(installer.fingerprint(self.home),before)

    def test_symlinked_managed_parent_refuses(self):
        elsewhere=Path(self.tmp.name)/'elsewhere';elsewhere.mkdir()
        (self.home/'.agents').symlink_to(elsewhere,target_is_directory=True)
        before=installer.fingerprint(elsewhere)
        rc,_,err=self.run_install('--apply')
        self.assertEqual(rc,2)
        self.assertIn('symlinked managed',err)
        self.assertEqual(installer.fingerprint(elsewhere),before)

    def test_agents_only_installs_no_skills(self):
        rc,_,err=self.run_install('--agents-only','--apply')
        self.assertEqual(rc,0,err)
        self.assertFalse((self.home/'.agents').exists())
        self.assertEqual(len(list((self.codex/'agents').glob('*.toml'))),13)

    def test_explicit_codex_home_keeps_skills_at_home(self):
        codex=Path(self.tmp.name)/'custom-codex'
        rc,_,err=self.run_install('--codex-home',codex,'--apply')
        self.assertEqual(rc,0,err)
        self.assertTrue((codex/'agents/nc_scout.toml').is_file())
        self.assertTrue(self.skills.is_dir())
        self.assertFalse(self.codex.exists())

    def test_home_override_does_not_use_process_codex_home(self):
        with patch.dict(os.environ,{'CODEX_HOME':str(Path(self.tmp.name)/'wrong')}):
            self.assertEqual(self.run_install('--apply')[0],0)
        self.assertFalse((Path(self.tmp.name)/'wrong').exists())
        self.assertTrue(self.codex.is_dir())

    def test_restore_refuses_a_different_home(self):
        self.assertEqual(self.run_install('--apply')[0],0)
        other=Path(self.tmp.name)/'other';other.mkdir()
        out=io.StringIO()
        with contextlib.redirect_stdout(out),contextlib.redirect_stderr(out):
            rc=installer.main(['--home',str(other),'--restore',str(self.manifests()[0]),'--apply'])
        self.assertEqual(rc,2)
        self.assertEqual(list(other.iterdir()),[])

    def test_rollback_restores_written_targets_after_injected_failure(self):
        self.skills.mkdir(parents=True)
        old=self.skills/'browser-debug';old.mkdir();(old/'SKILL.md').write_text('old browser skill')
        original=installer.fingerprint(old)
        real_apply=installer.Change.apply
        count=0
        def fail_second(change):
            nonlocal count
            count+=1
            if count==2:
                raise OSError('injected write failure')
            return real_apply(change)
        with patch.object(installer.Change,'apply',fail_second):
            rc,_,err=self.run_install('--replace','--apply')
        self.assertEqual(rc,2)
        self.assertIn('injected',err)
        self.assertEqual(installer.fingerprint(old),original)
        self.assertEqual([p.name for p in self.skills.iterdir()],['browser-debug'])
        self.assertFalse((self.codex/'.native-codex-kit.install.lock').exists())

    def test_lock_refuses_install_and_preserves_existing_lock(self):
        self.codex.mkdir();lock=self.codex/'.native-codex-kit.install.lock';lock.write_text('other process')
        before=installer.fingerprint(self.home)
        rc,_,err=self.run_install('--apply')
        self.assertEqual(rc,2)
        self.assertIn('lock exists',err)
        self.assertEqual(installer.fingerprint(self.home),before)

    def test_update_reconciles_changed_and_retired_assets_then_remove(self):
        kit=self.kit_copy()
        with patch.object(installer,'ROOT',kit):
            self.assertEqual(self.run_install('--apply')[0],0)
            old_skill=self.skills/'checkpoint'
            old_agent=self.codex/'agents/nc_scout.toml'
            (kit/'skills/checkpoint/SKILL.md').unlink()
            (kit/'agents/nc_scout.toml').unlink()
            changed=kit/'agents/nc_docs.toml'
            changed.write_bytes(changed.read_bytes()+b'\n# kit update\n')
            new_skill=kit/'skills/new-skill';new_skill.mkdir()
            (new_skill/'SKILL.md').write_text('---\nname: new-skill\ndescription: New skill\n---\n')
            new_agent=kit/'agents/nc_new.toml';new_agent.write_text('name = "new"\n')
            rc,_,err=self.run_install('--update','--apply')
            self.assertEqual(rc,0,err)
            self.assertFalse(old_skill.exists() or old_skill.is_symlink())
            self.assertFalse(old_agent.exists())
            self.assertEqual((self.codex/'agents/nc_docs.toml').read_bytes(),changed.read_bytes())
            self.assertEqual((self.skills/'new-skill').resolve(),new_skill.resolve())
            self.assertEqual((self.codex/'agents/nc_new.toml').read_bytes(),new_agent.read_bytes())
            self.assertEqual(self.run_install('--remove','--apply')[0],0)
        self.assertFalse(installer.active_path(self.codex).exists())
        self.assertFalse((self.skills/'new-skill').exists())
        self.assertFalse((self.codex/'agents/nc_docs.toml').exists())

    def test_update_foreign_collision_requires_replace_and_remove_restores_it(self):
        kit=self.kit_copy()
        with patch.object(installer,'ROOT',kit):
            self.assertEqual(self.run_install('--apply')[0],0)
            new=kit/'skills/new-skill';new.mkdir()
            (new/'SKILL.md').write_text('new kit skill')
            foreign=self.skills/'new-skill';foreign.mkdir()
            (foreign/'SKILL.md').write_text('user skill')
            prior=installer.fingerprint(self.home)
            rc,_,err=self.run_install('--update','--apply')
            self.assertEqual(rc,2)
            self.assertIn('Existing targets differ',err)
            self.assertEqual(installer.fingerprint(self.home),prior)
            self.assertEqual(self.run_install('--update','--replace','--apply')[0],0)
            self.assertTrue(foreign.is_symlink())
            self.assertEqual(self.run_install('--remove','--apply')[0],0)
        self.assertTrue(foreign.is_dir())
        self.assertFalse(foreign.is_symlink())
        self.assertEqual((foreign/'SKILL.md').read_text(),'user skill')

    def test_update_repoints_skills_after_source_package_moves(self):
        first=self.kit_copy()
        with patch.object(installer,'ROOT',first):
            self.assertEqual(self.run_install('--apply')[0],0)
        installed=self.skills/'code-review'
        self.assertEqual(os.readlink(installed),str(first.resolve()/'skills/code-review'))
        moved=Path(self.tmp.name)/'moved-kit'
        first.rename(moved)
        self.assertFalse(installed.exists())
        with patch.object(installer,'ROOT',moved):
            rc,_,err=self.run_install('--update','--apply')
            self.assertEqual(rc,0,err)
        self.assertEqual(installed.resolve(),moved.resolve()/'skills/code-review')
        self.assertTrue((installed/'SKILL.md').is_file())

    def test_update_and_remove_refuse_user_edits_without_writes(self):
        self.assertEqual(self.run_install('--apply')[0],0)
        managed=self.codex/'agents/nc_scout.toml'
        managed.write_bytes(managed.read_bytes()+b'\n# user edit\n')
        before=installer.fingerprint(self.home)
        for flag in ('--update','--remove'):
            rc,_,err=self.run_install(flag,'--apply')
            self.assertEqual(rc,2)
            self.assertIn('Managed target changed',err)
            self.assertEqual(installer.fingerprint(self.home),before)

    def test_guidance_outside_block_edits_survive_remove_but_block_edit_refuses(self):
        self.codex.mkdir();guidance=self.codex/'AGENTS.md'
        guidance.write_text('User preface\n')
        self.assertEqual(self.run_install('--with-guidance','--apply')[0],0)
        guidance.write_bytes(b'New preface\n'+guidance.read_bytes()+b'New suffix\n')
        self.assertEqual(self.run_install('--update','--apply')[0],0)
        self.assertEqual(self.run_install('--remove','--apply')[0],0)
        self.assertIn(b'New preface\n',guidance.read_bytes())
        self.assertIn(b'New suffix\n',guidance.read_bytes())
        self.assertNotIn(installer.START.encode(),guidance.read_bytes())

        self.assertEqual(self.run_install('--with-guidance','--apply')[0],0)
        guidance.write_bytes(guidance.read_bytes().replace(b'native-codex-kit:end',b'user-edited:end'))
        before=installer.fingerprint(self.home)
        rc,_,err=self.run_install('--remove','--apply')
        self.assertEqual(rc,2)
        self.assertIn('guidance',err.lower())
        self.assertEqual(installer.fingerprint(self.home),before)

    def test_lifecycle_rejects_tampered_inventory_and_backup_paths(self):
        skill=self.skills/'code-review';skill.mkdir(parents=True)
        (skill/'SKILL.md').write_text('original')
        self.assertEqual(self.run_install('--replace','--apply')[0],0)
        active=installer.active_path(self.codex)
        inventory=json.loads(active.read_text())
        original=active.read_bytes()
        for mutation in ('target','backup'):
            bad=json.loads(original)
            rec=next(r for r in bad['records'] if r['target'].endswith('/skills/code-review'))
            if mutation=='target':
                rec['target']=str(Path(self.tmp.name)/'outside')
            else:
                rec['original']=str(Path(self.tmp.name)/'outside')
            active.write_text(json.dumps(bad))
            before=installer.fingerprint(self.home)
            rc,_,err=self.run_install('--remove','--apply')
            self.assertEqual(rc,2,mutation)
            self.assertIn('Unsafe',err)
            self.assertEqual(installer.fingerprint(self.home),before)
            active.write_bytes(original)
        backup=Path(next(r for r in inventory['records'] if r['target'].endswith('/skills/code-review'))['original'])
        (backup/'SKILL.md').write_text('tampered')
        before=installer.fingerprint(self.home)
        rc,_,err=self.run_install('--remove','--apply')
        self.assertEqual(rc,2)
        self.assertIn('backup content mismatch',err.lower())
        self.assertEqual(installer.fingerprint(self.home),before)

    def test_lifecycle_dry_run_does_not_write(self):
        self.assertEqual(self.run_install('--apply')[0],0)
        before=installer.fingerprint(self.home)
        for flag in ('--update','--remove'):
            rc,out,err=self.run_install(flag)
            self.assertEqual(rc,0,err)
            self.assertIn('No files changed',out)
            self.assertEqual(installer.fingerprint(self.home),before)

    def test_update_rollback_preserves_active_inventory_and_managed_targets(self):
        kit=self.kit_copy()
        with patch.object(installer,'ROOT',kit):
            self.assertEqual(self.run_install('--apply')[0],0)
            for name in ('nc_docs.toml','nc_scout.toml'):
                p=kit/'agents'/name
                p.write_bytes(p.read_bytes()+b'\n# kit update\n')
            active=installer.active_path(self.codex)
            original_inventory=active.read_bytes()
            original_docs=(self.codex/'agents/nc_docs.toml').read_bytes()
            real_apply=installer.LifecycleChange.apply
            count=0
            def fail_second(change):
                nonlocal count
                count+=1
                if count==2:
                    raise OSError('injected lifecycle failure')
                return real_apply(change)
            with patch.object(installer.LifecycleChange,'apply',fail_second):
                rc,_,err=self.run_install('--update','--apply')
            self.assertEqual(rc,2)
            self.assertIn('injected lifecycle failure',err)
            self.assertEqual(active.read_bytes(),original_inventory)
            self.assertEqual((self.codex/'agents/nc_docs.toml').read_bytes(),original_docs)
            self.assertFalse((self.codex/'.native-codex-kit.install.lock').exists())

    def test_doctor_does_not_offer_update_for_identical_unowned_asset(self):
        self.skills.mkdir(parents=True)
        existing=self.skills/'checkpoint'
        existing.symlink_to(ROOT/'skills/checkpoint',target_is_directory=True)
        self.assertEqual(self.run_install('--apply')[0],0)
        result=subprocess.run([sys.executable,str(ROOT/'doctor.py'),'--home',str(self.home)],
                              capture_output=True,text=True,env=dict(os.environ,PATH=''))
        report=json.loads(result.stdout)
        self.assertEqual(report['installation']['status'],'installed')
        self.assertFalse(any(f['kind']=='new_kit_asset' and f['path']==str(existing)
                             for f in report['findings']))

    def test_doctor_detects_new_guidance_in_source_package(self):
        kit=self.kit_copy()
        for name in ('doctor.py','install.py'):
            shutil.copy2(ROOT/name,kit/name)
        with patch.object(installer,'ROOT',kit):
            self.assertEqual(self.run_install('--with-guidance','--apply')[0],0)
        guidance=kit/'AGENTS.native.md'
        guidance.write_bytes(guidance.read_bytes()+b'\nNew source guidance.\n')
        result=subprocess.run([sys.executable,str(kit/'doctor.py'),'--home',str(self.home)],
                              capture_output=True,text=True,env=dict(os.environ,PATH=''))
        report=json.loads(result.stdout)
        self.assertIn({'kind':'kit_update_available','path':str(self.codex.resolve()/'AGENTS.md')},
                      report['findings'])

class DoctorTests(unittest.TestCase):
    def test_active_installation_and_managed_edit_are_reported_read_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            home=Path(tmp)
            stdout=io.StringIO()
            with contextlib.redirect_stdout(stdout):
                self.assertEqual(installer.main(['--home',tmp,'--apply']),0)
            before=installer.fingerprint(home)
            env=dict(os.environ,PATH='')
            command=[sys.executable,str(ROOT/'doctor.py'),'--home',tmp]
            result=subprocess.run(command,capture_output=True,text=True,env=env)
            self.assertEqual(json.loads(result.stdout)['installation']['status'],'installed')
            self.assertEqual(installer.fingerprint(home),before)

            managed=home/'.codex/agents/nc_scout.toml'
            managed.write_bytes(managed.read_bytes()+b'\n# local change\n')
            before=installer.fingerprint(home)
            result=subprocess.run(command,capture_output=True,text=True,env=env)
            report=json.loads(result.stdout)
            self.assertEqual(report['installation']['status'],'drift')
            self.assertIn('installation_drift',{f['kind'] for f in report['findings']})
            self.assertEqual(installer.fingerprint(home),before)

    def test_missing_codex_and_wrong_config_shape_are_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            home=Path(tmp);codex=home/'.codex';codex.mkdir()
            (codex/'config.toml').write_text('agents = "wrong shape"\n')
            before=installer.fingerprint(home)
            env=dict(os.environ,PATH='')
            r=subprocess.run([sys.executable,str(ROOT/'doctor.py'),'--home',tmp],
                             capture_output=True,text=True,env=env)
            self.assertEqual(r.returncode,2,r.stderr)
            data=json.loads(r.stdout)
            kinds={f['kind'] for f in data['findings']}
            self.assertTrue({'codex_not_on_path','invalid_config'}<=kinds)
            self.assertEqual(installer.fingerprint(home),before)

    def test_duplicate_skills_and_omx_marker_do_not_echo_secret(self):
        with tempfile.TemporaryDirectory() as tmp:
            home=Path(tmp);codex=home/'.codex';codex.mkdir()
            (codex/'config.toml').write_text('# omx token=PRIVATE_SENTINEL\n')
            for root in [home/'.agents/skills',codex/'skills']:
                p=root/'review';p.mkdir(parents=True)
                (p/'SKILL.md').write_text('---\nname: review\ndescription: Review\n---\n')
            r=subprocess.run([sys.executable,str(ROOT/'doctor.py'),'--home',tmp],capture_output=True,text=True,env=dict(os.environ,PATH=''))
            data=json.loads(r.stdout);kinds={f['kind'] for f in data['findings']}
            self.assertIn('possible_duplicate_skill',kinds)
            self.assertIn('possible_omx_reference',kinds)
            self.assertNotIn('PRIVATE_SENTINEL',r.stdout+r.stderr)

if __name__=='__main__':
    unittest.main()
