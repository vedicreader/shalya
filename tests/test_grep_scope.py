"`grep`'s `path_filter` names a folder or file the way a model writes one, and a path outside the open folders is said to be outside, not reported as empty."
import pytest
from shalya.host import LocalHost
from shalya.tools import code_tools


@pytest.fixture
def tree(tmp_path):
    root, out = tmp_path/'proj', tmp_path/'elsewhere'
    for p, s in [(root/'pkg'/'sub'/'mod.py', 'needle = 1'), (root/'xpkg'/'sub2'/'a.py', 'needle = 2'),
                 (root/'nb'/'n.ipynb', '"needle"'), (out/'deep'/'o.py', 'needle = 3')]:
        p.parent.mkdir(parents=True, exist_ok=True); p.write_text(s)
    return root, out


def _tools(root, rg=True, read_outside=True):
    h = LocalHost([str(root)], index=False, web=False, read_outside=read_outside)
    if not rg: h.grep = lambda *a, **kw: None   # the tool's own file scan
    return {f.__name__: f for f in code_tools(h)}


@pytest.mark.parametrize('rg', [True, False])
def test_a_folder_or_file_filter_finds_only_that_place(tree, rg):
    root, _ = tree
    g = _tools(root, rg)['grep']
    for pf in ['pkg', 'pkg/sub', 'pkg/sub/', './pkg/sub', 'MOD', 'sub/mod.py', str(root/'pkg'), f'{root.name}/pkg/sub']:
        out = g('needle', path_filter=pf)
        assert 'mod.py' in out and 'a.py' not in out and 'n.ipynb' not in out, (pf, out)
    assert 'n.ipynb' in g('needle', path_filter='*.ipynb')
    assert '3 match' in g('needle', path_filter=str(root))


@pytest.mark.parametrize('rg', [True, False])
def test_an_unresolved_spelling_of_a_folder_inside_still_matches(tree, rg, tmp_path):
    root, _ = tree
    link = tmp_path/'alias'; link.symlink_to(root)
    out = _tools(root, rg)['grep']('needle', path_filter=str(link/'pkg'))
    assert 'mod.py' in out and 'a.py' not in out


@pytest.mark.parametrize('read_outside', [True, False])
def test_a_filter_outside_the_open_folders_says_so(tree, read_outside):
    root, out = tree
    said = _tools(root, read_outside=read_outside)['grep']('needle', path_filter=str(out))
    assert 'outside the open folders' in said and 'no matches' not in said
    assert ('view_file' in said) == read_outside


def test_a_recursive_listing_outside_the_open_folders_says_so_and_inside_is_sorted(tree):
    root, out = tree
    ls = _tools(root)['ls']
    assert 'outside the open folders' in ls(str(out), recursive=True)
    rows = ls(str(root), recursive=True).splitlines()
    assert rows == sorted(rows) and len(rows) == 3
