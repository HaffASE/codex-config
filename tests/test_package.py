"""Structural checks only: passing is not proof of model behavior or native discovery."""
from __future__ import annotations
import ast
import importlib.util
import json
from pathlib import Path
import re
import tempfile
import tomllib
import unittest

ROOT=Path(__file__).resolve().parents[1]
release_spec=importlib.util.spec_from_file_location('kit_release',ROOT/'release.py')
release=importlib.util.module_from_spec(release_spec)
release_spec.loader.exec_module(release)

class PackageTests(unittest.TestCase):
    def test_release_manifest_and_zip_are_reproducible(self):
        files=release.package_files()
        release.check(files)
        with tempfile.TemporaryDirectory() as tmp:
            first,second=Path(tmp)/'first.zip',Path(tmp)/'second.zip'
            release.build_zip(first,files)
            release.build_zip(second,files)
            self.assertEqual(first.read_bytes(),second.read_bytes())

    def test_skill_catalog(self):
        names={p.parent.name for p in (ROOT/'skills').glob('*/SKILL.md')}
        expected={'feature-discovery','testing-code-changes','debug-by-evidence',
                  'skill-evaluation','evidence-before-claims','review-feedback',
                  'code-review','deep-interview','implementation-plan','execute-plan',
                  'parallel-work','verify-work','frontend-tests','browser-debug',
                  'security-review','checkpoint','git-message'}
        self.assertEqual(names,expected)

    def test_frontmatter_and_native_manual_policy(self):
        for p in (ROOT/'skills').glob('*/SKILL.md'):
            with self.subTest(skill=p.parent.name):
                text=p.read_text();self.assertTrue(text.startswith('---\n'))
                front=text.split('---',2)[1]
                name=re.search(r'^name:\s*(.+)$',front,re.M).group(1).strip('"\' ')
                self.assertEqual(name,p.parent.name)
                self.assertRegex(front,r'(?m)^description:\s*\S')
                self.assertNotIn('disable-model-invocation',front)
                ui=(p.parent/'agents/openai.yaml').read_text()
                self.assertRegex(ui,r'(?m)^policy:\n  allow_implicit_invocation: false$')
                description=json.loads(re.search(r'^  short_description: (.+)$',ui,re.M).group(1))
                self.assertLessEqual(len(description),64)
                self.assertIn('$'+name,ui)

    def test_custom_agent_schema_and_model_inheritance(self):
        agents=list((ROOT/'agents').glob('*.toml'));self.assertEqual(len(agents),13)
        names=[]
        for p in agents:
            data=tomllib.loads(p.read_text());names.append(data['name'])
            self.assertEqual(data['name'],p.stem)
            for key in ['name','description','developer_instructions']:
                self.assertIsInstance(data[key],str);self.assertTrue(data[key].strip())
            self.assertNotIn('model',data);self.assertNotIn('model_reasoning_effort',data)
            self.assertIn('Do not spawn agents',data['developer_instructions'])
        self.assertEqual(len(set(names)),len(names))

    def test_agent_permission_defaults(self):
        for p in (ROOT/'agents').glob('*.toml'):
            data=tomllib.loads(p.read_text())
            if p.stem in {'nc_implementer','nc_test_writer'}:
                self.assertNotIn('sandbox_mode',data)
            else:
                self.assertEqual(data['sandbox_mode'],'read-only')
        self.assertIn('parent live permission overrides',
                      (ROOT/'skills/feature-discovery/references/integrations.md').read_text())

    def test_role_references_exist(self):
        names={p.stem for p in (ROOT/'agents').glob('*.toml')}
        for p in (ROOT/'skills').rglob('*.md'):
            for name in re.findall(r'\bnc_[a-z_]+\b',p.read_text()):
                self.assertIn(name,names,(str(p),name))

    def test_skill_relative_links_resolve(self):
        for p in (ROOT/'skills').rglob('*.md'):
            if {'assets','tests'} & set(p.parts):continue
            for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',p.read_text()):
                if target.startswith(('https:','http:','#','mailto:')):continue
                target=target.split('#')[0]
                if target:self.assertTrue((p.parent/target).exists(),f'{p}: {target}')

    def test_no_active_omx_runtime_in_entrypoints(self):
        paths=[ROOT/'AGENTS.native.md',*list((ROOT/'agents').glob('*.toml')),
               *list((ROOT/'skills').glob('*/SKILL.md'))]
        for p in paths:
            # Historical import docs may mention .omx; entrypoints must not call its runtime.
            text=p.read_text()
            self.assertNotRegex(text,r'(?im)^\s*(?:\$\s*)?omx\s+(?:state|team|question|ask|setup|hud)\b')
            self.assertNotRegex(text,r'mcp__omx|\$(?:ralplan|ultragoal|ultraqa|autopilot)\b')
        self.assertFalse((ROOT/'hooks.json').exists())
        self.assertFalse((ROOT/'plugin.json').exists())

    def test_python_sources_parse(self):
        for p in ROOT.rglob('*.py'):
            ast.parse(p.read_text(),filename=str(p))

    def test_json_sources_parse(self):
        for p in ROOT.rglob('*.json'):
            json.loads(p.read_text())

    def test_source_manifest_is_not_a_claim_of_host_access(self):
        data=json.loads((ROOT/'migration/source-manifest.json').read_text())
        self.assertIn('Not a dump',data['scope_note'])
        self.assertEqual(len(data['sources']),9)
        for source in data['sources']:
            self.assertRegex(source['sha256'],r'^[a-f0-9]{64}$')

    def test_fourteen_review_dimensions_retained(self):
        path=ROOT/'skills/code-review/references/dimensions'
        self.assertEqual(len([p for p in path.glob('*.md') if p.name!='index.md']),14)
        for p in path.glob('*.md'):
            if p.name=='index.md':continue
            self.assertIn('## Метод',p.read_text())

    def test_optional_config_is_valid_without_model_override(self):
        data=tomllib.loads((ROOT/'config/agents.example.toml').read_text())
        self.assertEqual(data['agents']['max_concurrent_threads_per_session'],3)
        self.assertIs(data['agents']['enabled'],True)
        self.assertNotIn('model',data)

if __name__=='__main__':
    unittest.main()
