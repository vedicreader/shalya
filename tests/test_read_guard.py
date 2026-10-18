"""A host's `read_guard` sees every read a tool would send a model, and can let it go, mask it, or withhold it.

Leela marks some vault sources Local only. The file tools read them from disk with no check, so a hosted model
could be sent a document its owner kept on the machine.
"""
import json, subprocess
import pytest

from shalya import LocalHost
from shalya.core import Hit, Refusal, failed
from shalya.tools import tools_for, image_refs, screen_hits, screen_diff, web_tools, browser_tools

PNG = b'\x89PNG\r\n\x1a\n' + b'\0' * 32
NB = {'cells': [{'id': 'a1', 'cell_type': 'code', 'source': 'mail = "ada@x.org"', 'metadata': {}, 'outputs': [], 'execution_count': None}],
      'metadata': {}, 'nbformat': 4, 'nbformat_minor': 5}

def mask(r): return r.text.replace('ada@x.org', '[EMAIL]') if isinstance(r.text, str) else 'a picture, withheld'
def refuse(r): return Refusal('Local only, and this turn runs on a hosted model')

@pytest.fixture
def proj(tmp_path):
    (tmp_path/'notes.md').write_text('# Notes\nmail ada@x.org today\n')
    (tmp_path/'mod.py').write_text('def ada_x(): "ada@x.org"\n')
    (tmp_path/'pic.png').write_bytes(PNG)
    (tmp_path/'n.ipynb').write_text(json.dumps(NB))
    return tmp_path

def host(root, guard=None, local=False):
    return LocalHost([str(root)], index=False, web=False, read_guard=guard, model_local=lambda: (local, 'claude-opus'))

CALLS = [('view_file', lambda p: (str(p/'notes.md'),)), ('view_file', lambda p: (str(p/'pic.png'),)),
         ('grep', lambda p: ('ada@x',)), ('search_code', lambda p: ('ada@x.org',)), ('outline', lambda p: (str(p/'mod.py'),)),
         ('notebook_cells', lambda p: (str(p/'n.ipynb'),)), ('view_cell', lambda p: (str(p/'n.ipynb'), 'a1'))]

def run(h, root):
    t = {f.__name__: f for f in tools_for(h)}
    return [str(t[n](*a(root))) for n, a in CALLS]

def same(o): return ['\n'.join(sorted(x.splitlines())) for x in o]   # ripgrep's file order varies run to run

def test_no_guard_and_an_allowing_guard_send_the_same(proj):
    plain = run(host(proj), proj)
    assert same(plain) == same(run(host(proj, lambda r: None), proj)) == same(run(host(proj, lambda r: True), proj))
    assert 'ada@x.org' in plain[0] and 'ada@x.org' in plain[2]

def test_a_masking_guard_masks_every_read_tool(proj):
    seen = []
    out = run(host(proj, lambda r: seen.append(r) or mask(r)), proj)
    for (name, _), o in zip(CALLS, out):
        assert 'ada@x.org' not in o and not failed(o), (name, o)
    assert '[EMAIL]' in out[0] and '[EMAIL]' in out[2] and out[1] == 'a picture, withheld'
    assert {r.tool for r in seen} >= {'view_file', 'grep', 'search_code', 'outline', 'notebook_cells', 'view_cell'}
    assert all((r.model, r.local) == ('claude-opus', False) for r in seen)
    assert {r.kind for r in seen} >= {'text', 'image', 'hits', 'cell'}

def test_a_refusing_guard_returns_a_structured_refusal(proj):
    out = run(host(proj, refuse), proj)
    for (name, _), o in zip(CALLS, out):
        assert 'ada@x.org' not in o and 'ERROR: withheld: ' in o and 'hosted model' in o, (name, o)
    assert out[0] == f'ERROR: withheld: {proj/"notes.md"}: Local only, and this turn runs on a hosted model'

def test_a_guard_deciding_on_the_path_reads_nothing_and_a_raising_guard_refuses(proj):
    loaded = []
    def by_path(r):
        loaded.append(r.path)
        return refuse(r) if r.path.endswith('notes.md') else None
    t = {f.__name__: f for f in tools_for(host(proj, by_path))}
    assert failed(t['view_file'](str(proj/'notes.md')))
    assert 'ada@x.org' in t['view_file'](str(proj/'mod.py'))
    g = t['grep']('ada@x')
    assert 'withheld' in g and f'{proj/"mod.py"}:1:' in g, 'one file refused, the other still answers'
    def boom(r): raise RuntimeError('vault closed')
    v = {f.__name__: f for f in tools_for(host(proj, boom))}['view_file'](str(proj/'notes.md'))
    assert v.startswith('ERROR: guard_failed: ') and 'ada@x.org' not in v

def test_edit_diffs_go_through_the_guard(proj):
    t = {f.__name__: f for f in tools_for(host(proj, refuse))}
    out = t['replace_text'](str(proj/'notes.md'), [{'oldText': 'today', 'newText': 'now'}])
    assert out.startswith('replaced 1 block(s)') and 'ada@x.org' not in out and 'withheld' in out
    assert 'now' in (proj/'notes.md').read_text()
    out = t['edit_cell'](str(proj/'n.ipynb'), 'a1', [{'oldText': 'mail', 'newText': 'email'}])
    assert 'ada@x.org' not in out and 'withheld' in out

def test_git_diff_is_guarded_file_by_file(proj):
    git = lambda *a: subprocess.run(['git', '-C', str(proj), '-c', 'user.name=t', '-c', 'user.email=t@t', *a], check=True, capture_output=True)
    git('init', '-q'); git('add', '-A'); git('commit', '-qm', 'one')
    (proj/'notes.md').write_text('mail ada@x.org tomorrow\n'); (proj/'mod.py').write_text('x = 2\n')
    plain = {f.__name__: f for f in tools_for(host(proj))}['git_diff']()
    assert 'tomorrow' in plain and 'x = 2' in plain
    t = {f.__name__: f for f in tools_for(host(proj, lambda r: refuse(r) if r.path.endswith('notes.md') else None))}
    d = t['git_diff']()
    assert 'tomorrow' not in d and 'withheld' in d and 'x = 2' in d
    assert screen_diff(host(proj), proj, plain) == plain

def test_screen_hits_masks_line_for_line_and_asks_once_per_file():
    class H: model_local = None
    asked = []
    H.read_guard = staticmethod(lambda r: asked.append(r.path) or r.text.upper())
    hs = [Hit('/a', 1, 's', 'x'), Hit('/b', 2, '', 'y'), Hit('/a', 3, '', 'z')]
    assert [h.text for h in screen_hits(H(), hs, 'grep')] == ['X', 'Y', 'Z'] and asked == ['/a', '/b']
    H.read_guard = staticmethod(lambda r: 'one line')
    assert [(h.path, h.text) for h in screen_hits(H(), hs, 'grep')] == [('/a', 'one line'), ('/b', 'one line')]
    H.read_guard = None
    assert screen_hits(H(), hs, 'grep') == hs

def test_web_and_browser_reads_go_through_the_guard(tmp_path):
    from fastcore.basics import AttrDict
    shot = tmp_path/'shot.png'; shot.write_bytes(PNG)
    class H(LocalHost):
        def read_url(self, url, remember=True): return AttrDict(text='page ada@x.org')
        def page_text(self, page=''): return 'tab ada@x.org'
        def screenshot(self, page=''): return str(shot)
    h = H([str(tmp_path)], index=False, web=False)
    w, b = {f.__name__: f for f in web_tools(h)}, {f.__name__: f for f in browser_tools(h)}
    assert w['read_url']('https://x.org') == 'page ada@x.org' and b['screenshot']().media == [str(shot)]
    h.read_guard = mask
    assert w['read_url']('https://x.org') == 'page [EMAIL]' and b['page_text']() == 'tab [EMAIL]'
    assert b['screenshot']() == 'a picture, withheld'
    h.read_guard = refuse
    assert w['read_url']('https://x.org').startswith('ERROR: withheld: https://x.org: ')

def test_a_reference_picture_is_never_sent_masked(proj):
    seen = []
    h = host(proj, lambda r: seen.append(r) or None, local=True)
    refs, e = image_refs(h, [str(proj/'pic.png')], model='gpt-image-1')
    assert e == '' and len(refs) == 1 and (seen[0].model, seen[0].local, seen[0].kind) == ('gpt-image-1', False, 'image')
    h.read_guard = mask
    refs, e = image_refs(h, [str(proj/'pic.png')])
    assert refs == [] and e.startswith('ERROR: withheld: ') and 'masked' in e
