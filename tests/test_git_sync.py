"""Merge, rebase and conflict tools, against a real repository in a temporary folder."""
import json, subprocess
import pytest

from shalya import LocalHost
from shalya.core import GIT_WRITE_TOOLS, failed
from shalya.tools import tools_for


def git(cwd, *args): return subprocess.run(['git', *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def commit(cwd, name, text, msg):
    (cwd/name).write_text(text)
    git(cwd, 'add', name); git(cwd, 'commit', '-qm', msg)


@pytest.fixture
def repo(tmp_path, monkeypatch):
    for k, v in dict(GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@t', GIT_COMMITTER_NAME='t', GIT_COMMITTER_EMAIL='t@t').items(): monkeypatch.setenv(k, v)
    git(tmp_path, 'init', '-q', '-b', 'main')
    commit(tmp_path, 'a.txt', 'base\n', 'base')
    git(tmp_path, 'branch', 'side'); git(tmp_path, 'branch', 'feature')
    commit(tmp_path, 'a.txt', 'main\n', 'main edits a')
    git(tmp_path, 'checkout', '-q', 'side'); commit(tmp_path, 'c.txt', 'c\n', 'side adds c')
    git(tmp_path, 'checkout', '-q', 'feature'); commit(tmp_path, 'a.txt', 'feature\n', 'feature edits a')
    host = LocalHost([str(tmp_path)], index=False, web=False)
    return tmp_path, {t.__name__: t for t in tools_for(host)}


def test_names_are_write_tools():
    assert {'git_sync', 'git_conflicts'} <= GIT_WRITE_TOOLS


def test_merge_without_conflict(repo):
    cwd, ts = repo
    git(cwd, 'checkout', '-q', 'side')
    r = json.loads(ts['git_sync']('main', 'merge'))
    assert r['conflicted'] == [] and r['moved'] and r['undo']
    assert (cwd/'c.txt').exists() and (cwd/'a.txt').read_text() == 'main\n'


def test_rebase_conflict_returns_the_plan_then_resolves_and_continues(repo):
    cwd, ts = repo
    r = json.loads(ts['git_sync']('main'))
    assert r['conflicted'] == ['a.txt'] and r['plan']['files'][0]['path'] == 'a.txt'
    assert json.loads(ts['git_status']())['plan']['files'][0]['path'] == 'a.txt'
    safe = json.loads(ts['git_conflicts']('resolve_safe'))
    assert safe['resolved'] == [] and safe['plan']['summary']['manual'] == 1, 'differing sides are never removed for you'
    assert failed(ts['git_conflicts']('resolve', file='a.txt'))
    done = json.loads(ts['git_conflicts']('resolve', file='a.txt', choice='theirs'))
    assert done['conflicted'] == []
    end = json.loads(ts['git_conflicts']('continue'))
    assert end['conflicted'] == [] and not end['operation']['active']
    assert (cwd/'a.txt').read_text() == 'feature\n' and git(cwd, 'merge-base', '--is-ancestor', 'main', 'HEAD') == ''
    assert 'plan' not in json.loads(ts['git_status']())


def test_resolve_with_given_content(repo):
    cwd, ts = repo
    ts['git_sync']('main')
    assert failed(ts['git_conflicts']('resolve', file='a.txt', choice='resolved'))
    ts['git_conflicts']('resolve', file='a.txt', choice='resolved', content='both\n')
    assert not json.loads(ts['git_conflicts']('continue'))['operation']['active']
    assert (cwd/'a.txt').read_text() == 'both\n'


def test_abort_restores_the_branch(repo):
    cwd, ts = repo
    before = git(cwd, 'rev-parse', 'HEAD')
    ts['git_sync']('main')
    assert git(cwd, 'rev-parse', 'HEAD') != before or git(cwd, 'branch', '--show-current') == ''
    r = json.loads(ts['git_conflicts']('abort'))
    assert git(cwd, 'rev-parse', 'HEAD') == before and git(cwd, 'branch', '--show-current') == 'feature'
    assert r['conflicted'] == [] and not r['operation']['active']


def test_skip_drops_the_stopped_commit(repo):
    cwd, ts = repo
    ts['git_sync']('main')
    json.loads(ts['git_conflicts']('skip'))
    assert (cwd/'a.txt').read_text() == 'main\n' and not (cwd/'.git'/'rebase-merge').exists()


def test_reset_and_nonsense_are_refused(repo):
    cwd, ts = repo
    before = git(cwd, 'rev-parse', 'HEAD')
    for how in ('reset', 'bogus'):
        r = ts['git_sync']('main', how)
        assert failed(r) and 'fast-forward, merge or rebase' in r
    assert failed(ts['git_conflicts']('plan')) and failed(ts['git_conflicts']('continue'))
    assert git(cwd, 'rev-parse', 'HEAD') == before and (cwd/'a.txt').read_text() == 'feature\n'
