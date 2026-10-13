import importlib.util
from pathlib import Path
import tempfile
import unittest

SCRIPT=Path(__file__).with_name('audit.py')
# Temp roots are resolved: macOS puts them under /var, a symlink the no-follow reader refuses.

def load():
    assert SCRIPT.exists(), 'Missing safe librarian audit implementation'
    spec=importlib.util.spec_from_file_location('librarian_audit',SCRIPT)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class PrivacyTest(unittest.TestCase):
    def test_nested_numbered_vault_folder_is_refused(self):
        m=load()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve()
            target=root/'7 - Wikipedia'/'raw'/'9 - synthetic'/'x.md'
            self.assertFalse(m.permitted(root,target))

    def test_symlink_and_path_escape_are_refused(self):
        m=load()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve(); notes=root/'2 - Notes'; notes.mkdir()
            (notes/'link.md').symlink_to(root/'outside.md')
            self.assertIsNone(m.read_public(root,notes/'link.md'))
            self.assertFalse(m.permitted(root,notes/'..'/'..'/'outside.md'))

    def test_malformed_header_reads_as_empty_meta_and_keeps_text(self):
        m=load()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve(); notes=root/'2 - Notes'; notes.mkdir()
            p=notes/'case.md'
            for value in ('{broken','&flag false\nb: *flag\nb: [','[1, 2'):
                with self.subTest(value=value):
                    text='---\nbackground: '+value+'\n---\nSYNTHETIC BODY\n'
                    p.write_text(text)
                    self.assertEqual(m.read_public(root,p),({},text))

    def test_header_parser_matches_wikilib(self):
        lib_path=SCRIPT.parents[4]/'0 - System'/'scripts'/'wikilib.py'
        if not lib_path.is_file(): self.skipTest('wikilib not reachable from this copy')
        spec=importlib.util.spec_from_file_location('wikilib_copy',lib_path)
        guard=importlib.util.module_from_spec(spec); spec.loader.exec_module(guard)
        m=load()
        for text in ('', 'plain\n', '---\n---\nbody\n', '--- \na: 1\n---\nbody\n',
                     '---\na: 1\na: 2\n---\nbody\n', '---\nx: [\n---\nbody\n', '---\n- a\n---\nbody\n',
                     '---\nlast_compiled: 2026-10-08\nflag: true\n---\nbody\n', '---\nunclosed: 1\nbody\n',
                     '---\na: &x 1\nb: *x\n---\nbody\n', '---\n1: one\n---\nbody\n',
                     '---\na: 1\n---', '---\r\na: 1\r\n---\r\nbody\n'):
            with self.subTest(text=text):
                self.assertEqual(m.split_header(text),guard.split_header(text))

    def test_dated_filenames_are_not_mistaken_for_numbered_areas(self):
        m=load()
        root=Path('/vault')
        self.assertTrue(m.permitted(root,root/'2 - Notes'/'2026-10-13 standup.md'))
        self.assertFalse(m.permitted(root,root/'2 - Notes'/'3 - Area'/'x.md'))

class AuditTest(unittest.TestCase):
    def test_audit_uses_actual_pages_not_reports_or_stale_manifest(self):
        m=load()
        with tempfile.TemporaryDirectory() as tmp:
            r=Path(tmp).resolve(); w=r/'7 - Wikipedia'; w.mkdir()
            (r/'0 - System').mkdir()
            (r/'0 - System'/'SCHEMA.md').write_text('# SCHEMA\n## type\n- `wiki-page`\n## tags\n`wiki`\n## subject\n')
            (w/'One.md').write_text('---\ntype: wiki-page\ntags: [wiki]\nlast_compiled: 2026-10-06\nwiki_sources: ["https://example.org/source"]\n---\n[[Missing]]\n')
            (w/'report.md').write_text('---\ntype: report\n---\nReport')
            (w/'broken.md').write_text('---\ntype: wiki-page\ntags: [wiki\n---\nBroken')
            (w/'index.md').write_text('---\ntype: index\n---\n')
            (w/'.manifest.json').write_text('[{"path":"gone.md","pages_produced":["Deleted"]}]')
            before={str(p):p.read_bytes() for p in r.rglob('*') if p.is_file()}
            result=m.audit(r)
            after={str(p):p.read_bytes() for p in r.rglob('*') if p.is_file()}
            self.assertEqual(before,after)
            self.assertEqual(result['counts']['wiki_pages'],2)
            self.assertEqual(result['counts']['unindexed_pages'],2)
            self.assertIn({'page':'7 - Wikipedia/broken.md','issue':'malformed_header'},result['errors'])
            self.assertEqual(result['counts']['broken_body_links'],1)
            self.assertEqual(result['counts']['external_source_references_unverified'],1)
            self.assertEqual(result['scope'],'wiki-structural-read-only')

    def test_raw_sources_resolve_against_the_wiki_folder(self):
        m=load()
        with tempfile.TemporaryDirectory() as tmp:
            r=Path(tmp).resolve(); w=r/'7 - Wikipedia'; (w/'raw').mkdir(parents=True)
            (w/'raw'/'youtube-abc.md').write_text('transcript')
            (w/'index.md').write_text('[[7 - Wikipedia/Page]]\n')
            for source in ('[[raw/youtube-abc.md]]','[[7 - Wikipedia/raw/youtube-abc.md]]','[[raw/missing.md]]'):
                with self.subTest(source=source):
                    (w/'Page.md').write_text('---\ntype: wiki-page\ntags: [wiki]\nlast_compiled: 2026-10-13\nwiki_sources: ["'+source+'"]\n---\nBody\n')
                    count=m.audit(r)['counts']['source_references_unavailable_or_ambiguous']
                    self.assertEqual(count,1 if 'missing' in source else 0)

if __name__=='__main__': unittest.main()
