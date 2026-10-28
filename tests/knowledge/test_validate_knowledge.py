"""CLI tests kept separate from the dependency-free application suite."""

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


CHECKER = Path(__file__).resolve().parents[2] / 'scripts/validate_knowledge.py'


class KnowledgeTests(unittest.TestCase):
    def check(self, files, strict=False, git=False):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name, text in files.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text)
            if git:
                subprocess.run(['git', 'init', '-q', folder], check=True)
            args = [sys.executable, str(CHECKER), '--root', folder]
            if strict:
                args.append('--strict')
            return subprocess.run(args, text=True, capture_output=True)

    def test_minimal_unknown_type_and_extensions_are_valid(self):
        result = self.check({'a.md': '---\ntype: Custom Thing\ncustom: {x: 1}\n---\n# A\n'})
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_missing_or_invalid_type_fails(self):
        for text in ('# No metadata', '---\ntype: ""\n---\n', '---\ntype: [x]\n---\n'):
            with self.subTest(text=text):
                self.assertEqual(self.check({'a.md': text}).returncode, 1)

    def test_unsafe_and_malformed_yaml_fail(self):
        for text in ('---\ntype: [broken\n---\n', '---\ntype: !!python/object:unsafe {}\n---\n'):
            with self.subTest(text=text):
                self.assertEqual(self.check({'a.md': text}).returncode, 1)

    def test_index_reserved_structure(self):
        for name, text in (('index.md', '---\nokf_version: 0.2\n---\n# Root\n'),
                           ('sub/index.md', '---\ntype: Index\n---\n# Sub\n'),
                           ('index.md', '# Root\nAn ordinary paragraph.\n')):
            with self.subTest(name=name, text=text):
                self.assertEqual(self.check({name: text}).returncode, 1)

    def test_log_dates_must_be_valid_and_newest_first(self):
        for text in ('# Log\n## 2026-02-30\n', '# Log\n## 2025-01-01\n## 2026-01-01\n',
                     '---\ntype: Log\n---\n# Log\n'):
            with self.subTest(text=text):
                self.assertEqual(self.check({'log.md': text}).returncode, 1)
        self.assertEqual(self.check({'log.md': '# Log\n## 2026-01-01: New\n- Update.\n'}).returncode, 0)

    def test_broken_links_are_base_conformant_but_fail_project_strict(self):
        files = {'index.md': '---\nokf_version: "0.2"\n---\n# Root\n- [A](a.md) - A\n',
                 'a.md': '---\ntype: Reference\n---\n[Missing](missing.md)\n'}
        self.assertEqual(self.check(files).returncode, 0)
        result = self.check(files, strict=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn('missing.md', result.stderr)

    def test_fenced_examples_are_not_live_links(self):
        files = {'index.md': '---\nokf_version: "0.2"\n---\n# Root\n- [A](a.md) - A\n',
                 'a.md': '---\ntype: Reference\n---\n```md\n[Example](missing.md)\n```\n'}
        self.assertEqual(self.check(files, strict=True).returncode, 0)

    def test_strict_detects_unreachable_concepts(self):
        result = self.check({'index.md': '---\nokf_version: "0.2"\n---\n# Root\n',
                             'orphan.md': '---\ntype: Concept\n---\n# Orphan\n'}, strict=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn('unreachable', result.stderr)

    def test_commonmark_indented_longer_and_unclosed_fences(self):
        for fenced in ('  ```md\n[Example](missing.md)\n  ```\n',
                       '```md\n[Example](missing.md)\n````\n',
                       '~~~md\n[Example](missing.md)\n~~~~\n',
                       '```md\n[Example](missing.md)\n'):
            with self.subTest(fenced=fenced):
                files = {'index.md': '---\nokf_version: "0.2"\n---\n# Root\n- [A](a.md) - A\n',
                         'a.md': '---\ntype: Reference\n---\n' + fenced}
                result = self.check(files, strict=True)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_link_titles_are_not_part_of_destinations(self):
        for link in ('[A](a.md "A title")', "[A](a.md 'A title')", '[A](a.md (A title))',
                     '[A](<a file.md> "A title")'):
            with self.subTest(link=link):
                name = 'a file.md' if '<' in link else 'a.md'
                files = {'index.md': '---\nokf_version: "0.2"\n---\n# Root\n- ' + link + ' - A\n',
                         name: '---\ntype: Reference\n---\n# A\n'}
                result = self.check(files, strict=True)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_bundle_relative_sources_and_bare_verifier(self):
        text = ('---\ntype: Reference\nsources: [{resource: /evidence.json}]\n'
                'verified: {by: process:fixture-check, at: "2026-10-28T12:00:00Z"}\n---\n# A\n')
        files = {'index.md': '---\nokf_version: "0.2"\n---\n# Root\n- [A](a.md) - A\n',
                 'a.md': text, 'evidence.json': '{}'}
        self.assertEqual(self.check(files, strict=True).returncode, 0)

    def test_provenance_datetime_requires_offset(self):
        files = {'a.md': '---\ntype: Concept\ngenerated: {by: process:fixture, at: "2026-10-28T12:00:00"}\n---\n'}
        self.assertEqual(self.check(files).returncode, 1)

    def test_strict_rejects_links_outside_bundle(self):
        files = {'index.md': '---\nokf_version: "0.2"\n---\n# Root\n- [A](../outside.md) - A\n'}
        self.assertEqual(self.check(files, strict=True).returncode, 1)

    def test_git_ignored_private_markdown_is_not_part_of_bundle(self):
        files = {'.gitignore': 'private/\n', 'private/secret.md': 'Not public OKF',
                 'a.md': '---\ntype: Concept\n---\n# A\n'}
        self.assertEqual(self.check(files, git=True).returncode, 0)


if __name__ == '__main__':
    unittest.main()
