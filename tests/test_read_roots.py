"""A host opens some folders for reading only: every read tool searches them, and every write into them is refused.

A job that adapts a text reads a reference checkout it must not touch. Every root was writable, and `read_outside`
did not reach `grep` or a recursive `ls`, so an agent fell back to `rg` through the shell.
"""
import pytest

from shalya import LocalHost
from shalya.core import READ_ONLY, Unsafe
from shalya.tools import tools_for


def test_reads_reach_a_read_root_and_writes_there_are_refused(tmp_path):
    work, ref = tmp_path/'work', tmp_path/'ref'
    work.mkdir(); ref.mkdir()
    (ref/'source.py').write_text('def lawful_source(): pass\n')
    h = LocalHost([str(work)], read_roots=[str(ref)], index=False, web=False)
    assert h.roots == [str(work)] and h.read_roots == [str(ref.resolve())], 'writes go to the roots alone'
    tools = {t.__name__: t for t in tools_for(h)}
    assert 'lawful_source' in h.read(str(ref/'source.py'))
    assert 'lawful_source' in tools['grep']('lawful_source')
    assert 'source.py' in tools['ls'](recursive=True) and str(ref.resolve()) in tools['ls']()
    with pytest.raises(Unsafe, match=READ_ONLY): h.check(ref/'new.py')
    assert READ_ONLY in tools['create_file'](str(ref/'new.py'), 'y = 2') and not (ref/'new.py').exists()
    assert READ_ONLY in tools['run_shell']('touch made', cwd=str(ref)) and not (ref/'made').exists()
    assert 'ERROR' not in tools['create_file'](str(work/'new.py'), 'y = 2') and (work/'new.py').exists()
    assert str(ref.resolve()) in h.roots_note and 'read-only' in h.roots_note
    more = tmp_path/'more'; more.mkdir()
    h.add_root(str(more), readonly=True)
    assert str(more.resolve()) in h.read_roots and str(more.resolve()) not in h.roots
    with pytest.raises(Unsafe, match=READ_ONLY): h.check(more/'x.py')


def test_a_wide_read_root_keeps_credentials_shut_and_overlapping_roots_are_searched_once(tmp_path):
    from shalya.core import SECRET
    proj = tmp_path/'proj'; proj.mkdir()
    (proj/'a.py').write_text('x = 1\n')
    (tmp_path/'.env').write_text('TOKEN=secret\n')
    h = LocalHost([str(proj)], read_roots=[str(tmp_path)], index=False, web=False)
    with pytest.raises(Unsafe, match=SECRET): h.check(tmp_path/'.env', reading=True)
    assert h._search_roots == [str(tmp_path.resolve())], 'the write root inside the read root is searched with it'
    assert [str(p) for p in h.walk()].count(str((proj/'a.py').resolve())) == 1
