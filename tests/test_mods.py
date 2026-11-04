"Mod discovery, ownership, callback isolation, and dry inspection."
import inspect
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from importlib.metadata import EntryPoint
from pathlib import Path

import pytest
import shalya.skills as skills
from shalya.skills import Registry, load


MOD = r'''
def setup(reg):
    reg.tool(lambda: 'tool')
    reg.skill('owned', 'skill body')
    reg.command('shared', lambda a, arg: 'mod')
    reg.on('session_end', lambda a: 'hook')
    reg.approval(lambda *a: 'approved')
    reg.status(lambda a: 'status')
    reg.band(lambda view: ['band'], rows=3)
    reg.after(3600, lambda: None)
    reg.every(3600, lambda: None)
'''


def test_discovery_and_replacement(tmp_path, monkeypatch):
    cfg, root = tmp_path/'cfg', tmp_path/'project'
    epdir = tmp_path/'package'
    epdir.mkdir()
    (epdir/'sample_mod.py').write_text("def setup(reg): reg.command('entry', lambda a, x: x)")
    monkeypatch.syspath_prepend(str(epdir))
    monkeypatch.setattr(skills, 'entry_points', lambda **kw: [EntryPoint(name='entry', value='sample_mod:setup', group='ramabana.mods')])
    for base in (cfg, root/'.leela'):
        for folder in ('extensions', 'mods'):
            d = base/folder
            d.mkdir(parents=True)
            for name in ('plain', '_ignored', '.hidden'):
                (d/f'{name}.py').write_text(f"def setup(reg): reg.command('{base.name}_{folder}_{name}', lambda a, x: x)")
            (d/'same.py').write_text(f"def setup(reg): reg.skill('winner', '{base.name}_{folder}')")
        folder = base/'mods'/'bundle'
        (folder/'skills'/'guide').mkdir(parents=True)
        (folder/'mod.py').write_text("def setup(reg): reg.command('bundle', lambda a, x: x)")
        (folder/'mod.toml').write_text('description = "Bundle"\nversion = "1.2"\n')
        (folder/'skills'/'guide'/'SKILL.md').write_text('A bundled skill.')
        for hidden in ('_skip', '.skip'):
            (base/'mods'/hidden).mkdir()
            (base/'mods'/hidden/'mod.py').write_text('raise RuntimeError("hidden")')
    reg = load(Registry(), [root], cfg, False, ())
    assert 'entry' in reg.commands
    assert {m.name for m in reg.mods} == {'entry', 'plain', 'same', 'bundle'}
    assert reg.skills[0].text() == 'cfg_mods'
    assert {s.name for s in reg.skills} == {'winner', 'guide'}
    assert next(m for m in reg.mods if m.name == 'bundle').version == '1.2'
    assert not any('project' in m.source for m in reg.mods)
    reg.drop_loaded()
    load(reg, [root], cfg, True, ())
    assert next(s for s in reg.skills if s.name == 'winner').text() == '.leela_mods'
    assert len(reg.mods) == 4
    assert 'guide' in {s.name for s in reg.skills}
    explicit = tmp_path/'explicit.py'
    explicit.write_text("def setup(reg): reg.command('explicit', lambda a, x: x)")
    load(reg.drop_loaded(), (), cfg, False, [explicit])
    assert 'explicit' in reg.commands


def test_off_on_owns_every_registration(tmp_path, monkeypatch):
    monkeypatch.setattr(skills, 'entry_points', lambda **kw: [])
    p = tmp_path/'mods'/'owned.py'
    p.parent.mkdir()
    p.write_text(MOD)
    reg = Registry(host='host', agent='agent')
    baseline = lambda *a: 'baseline'
    reg.command('shared', baseline)
    reg.approval(baseline)
    load(reg, cfg=tmp_path)
    assert reg.mod is None and reg.home is None
    assert len(reg.tools) == len(reg.skills) == len(reg.status_segments) == len(reg.bands) == 1
    assert reg.status_segments[0](None) == 'status'
    assert not (tmp_path/'mods'/'owned').exists()
    assert reg.bands[0].rows == 3 and reg.bands[0](None) == ['band']
    assert reg.fire('session_end', None) == ['hook']
    handles = list(reg.timers)
    assert len(handles) == 2 and all(t.thread.daemon for t in handles)
    reg.off('owned')
    assert not reg.tools and not reg.skills and not reg.status_segments and not reg.bands and not reg.timers
    assert reg.commands['shared'][0] is baseline and reg.approve is baseline
    assert reg.fire('session_end', None) == []
    assert all(t.cancelled for t in handles)
    reg.on_mod('owned')
    assert len(reg.tools) == len(reg.skills) == len(reg.status_segments) == len(reg.bands) == 1
    assert len(reg.timers) == 2 and reg.commands['shared'][0] is not baseline
    assert all(t.thread.is_alive() and not t.cancelled for t in reg.timers)
    outside = lambda: 'outside'
    reg.tool(outside)
    reg.drop_loaded()
    assert reg.tools == [outside] and not reg.mods and not reg.timers
    assert reg.commands['shared'][0] is baseline and reg.approve is baseline


def test_overlapping_mods_and_setup_context(tmp_path, monkeypatch):
    monkeypatch.setattr(skills, 'entry_points', lambda **kw: [])
    d = tmp_path/'mods'
    d.mkdir()
    for name in ('a', 'b'):
        (d/f'{name}.py').write_text(f"def setup(reg):\n    assert reg.mod == '{name}'\n    assert reg.home.name == '{name}'\n    assert not reg.home.exists()\n    reg.tool(reg.agent)\n    reg.command('shared', lambda a, x: '{name}')\n    reg.approval(lambda *a: '{name}')\n")
    reg = load(Registry(agent=lambda: None), cfg=tmp_path)
    assert len(reg.mods) == 2 and len(reg.tools) == 2
    reg.off('a')
    assert len(reg.tools) == 1 and reg.commands['shared'][0](None, '') == 'b'
    reg.off('b')
    assert not reg.tools and not reg.commands and reg.approve is None
    reg.on_mod('a')
    assert reg.commands['shared'][0](None, '') == 'a'
    reg.drop_loaded()


def test_failing_callbacks_are_isolated_once(tmp_path, monkeypatch):
    monkeypatch.setattr(skills, 'entry_points', lambda **kw: [])
    d = tmp_path/'mods'
    d.mkdir()
    (d/'bad.py').write_text(r'''
def setup(reg):
    def broken(*a):
        reg.agent.append('bad')
        raise ValueError('callback broke')
    reg.on('session_end', broken)
    reg.status(broken)
    reg.band(broken)
    reg.every(0.01, broken)
''')
    (d/'good.py').write_text("def setup(reg):\n    reg.on('session_end', lambda a: 'good')\n    reg.status(lambda a: 'good')\n    reg.band(lambda v: ['good'])\n    reg.after(0.02, lambda: reg.host.set())\n")
    done = threading.Event()
    calls = []
    reg = load(Registry(host=done, agent=calls), cfg=tmp_path)
    try:
        for _ in range(3):
            assert reg.fire('session_end', None) == ['good']
            assert [f(None) for f in reg.status_segments] == [None, 'good']
            assert [b(None) for b in reg.bands] == [None, ['good']]
        assert done.wait(2)
        for timer in reg.timers: timer.thread.join(2)
        assert calls == ['bad'] * 4
        note = next(m.note for m in reg.mods if m.name == 'bad')
        assert note.count('callback broke') == 4
        assert sum(n.count('callback broke') for n in reg.notes) == 4
    finally:
        reg.drop_loaded()


def test_replacement_order_and_reload_span(tmp_path, monkeypatch):
    monkeypatch.setattr(skills, 'entry_points', lambda **kw: [])
    cfg, root = tmp_path/'cfg', tmp_path/'project'
    (cfg/'mods').mkdir(parents=True)
    (root/'.leela'/'mods').mkdir(parents=True)
    for target, label in ((cfg/'mods'/'a.py', 'loser'), (cfg/'mods'/'b.py', 'first'), (root/'.leela'/'mods'/'a.py', 'last')):
        target.write_text(f"def setup(reg): reg.on('session_end', lambda a: '{label}')")
    reg = load(Registry(), [root], cfg, True)
    assert reg.fire('session_end', None) == ['first', 'last']
    load(reg, [root], cfg, True)
    reg.drop_loaded()
    assert not reg.mods and not any(reg.hooks.values())


def test_callback_can_register_owned_timer(tmp_path, monkeypatch):
    monkeypatch.setattr(skills, 'entry_points', lambda **kw: [])
    path = tmp_path/'nested.py'
    path.write_text(r'''
def setup(reg):
    reg.on('session_end', lambda a: reg.after(0.01, lambda: reg.host.set()))
''')
    done = threading.Event()
    reg = load(Registry(host=done), paths=[path])
    reg.fire('session_end', None)
    assert done.wait(2)
    reg.off('nested')
    assert not reg.timers


def test_hooks_do_not_serialize_user_callbacks():
    reg = Registry()
    entered, release, second = threading.Event(), threading.Event(), threading.Event()
    def hook(slow):
        if slow:
            entered.set()
            release.wait(2)
        else: second.set()
    reg.on('before_tool', hook)
    first = threading.Thread(target=lambda: reg.fire('before_tool', True))
    other = threading.Thread(target=lambda: reg.fire('before_tool', False))
    first.start()
    try:
        assert entered.wait(2)
        other.start()
        assert second.wait(0.5)
    finally:
        release.set()
        first.join(2)
        if other.ident is not None: other.join(2)


def test_callback_attributes_do_not_replace_guard_state():
    class Hook:
        def __init__(self):
            self.fn = lambda *args: 'wrong callback'
            self.failed = True
        def __call__(self, agent): return 'right callback'
    reg = Registry()
    reg.on('session_end', Hook())
    assert reg.fire('session_end', None) == ['right callback']


def test_unknown_mod_names_are_key_errors(tmp_path, monkeypatch):
    monkeypatch.setattr(skills, 'entry_points', lambda **kw: [])
    path = tmp_path/'known.py'
    path.write_text('def setup(reg): pass')
    reg = load(Registry(), paths=[path])
    for fn in (reg.off, reg.on_mod):
        with pytest.raises(KeyError, match='missing.*known'):
            fn('missing')


@pytest.mark.parametrize('rows', [1.5, '3', None, True, False])
def test_band_rows_must_be_an_int(rows):
    reg = Registry()
    with pytest.raises(ValueError):
        reg.band(lambda view: [], rows=rows)
    assert not reg.bands
    for ok in (1, 6, 50):
        reg.band(lambda view: [], rows=ok)
    assert [b.rows for b in reg.bands] == [1, 6, 50]


def test_notices_from_threads_and_redraw():
    reg = Registry()
    draws = []
    reg.on_redraw = lambda: draws.append(True)
    threads = [threading.Thread(target=lambda i=i: [reg.notify(f'{i}:{j}') for j in range(100)]) for i in range(8)]
    for t in threads: t.start()
    for t in threads: t.join()
    notices = reg.drain_notices()
    assert len(notices) == 800
    assert {n['text'] for n in notices} == {f'{i}:{j}' for i in range(8) for j in range(100)}
    for i in range(8):
        assert [n['text'] for n in notices if n['text'].startswith(f'{i}:')] == [f'{i}:{j}' for j in range(100)]
    assert reg.drain_notices() == []
    reg.redraw()
    assert draws


@pytest.mark.parametrize('folder', [False, True])
def test_check_is_dry_for_files_and_folders(tmp_path, monkeypatch, folder):
    check = getattr(skills, 'check', None)
    assert callable(check)
    def forbidden(*a, **kw):
        pytest.fail('a dry registry started a thread')
    monkeypatch.setattr(skills, 'startthread', forbidden)
    p = tmp_path/'example.py'
    if folder:
        p = tmp_path/'example'
        (p/'skills'/'extra').mkdir(parents=True)
        (p/'skills'/'extra'/'SKILL.md').write_text('Extra skill')
        (p/'mod.toml').write_text('description = "Example"\n')
    target = p/'mod.py' if folder else p
    target.write_text(MOD)
    report = check(p)
    assert len(report['tools']) == len(report['commands']) == len(report['status']) == len(report['bands']) == 1
    assert set(report['skills']) == ({'owned', 'extra'} if folder else {'owned'})
    assert report['hooks'] == {'session_end': 1}
    assert len(report['timers']) == 2
    assert report['mods'][0]['on']


def mod_file(tmp_path, body, name='example'):
    path = tmp_path/f'{name}.py'
    path.write_text(body)
    return path


def test_unowned_hooks_retry_and_note_every_failure():
    reg = Registry()
    calls = []
    def broken():
        calls.append(True)
        raise ValueError('again')
    reg.on('session_end', broken)
    assert reg.fire('session_end') == []
    assert reg.fire('session_end') == []
    assert len(calls) == len(reg.notes) == 2


@pytest.mark.parametrize('event', ['before_tool', 'before_turn', 'approval'])
def test_mod_decisions_fail_closed_and_retry(tmp_path, event):
    path = mod_file(tmp_path, r'''
def setup(reg):
    def broken(*args):
        reg.agent.append(reg.mod)
        raise ValueError(reg.host[0])
    if reg.host[1] == 'approval': reg.approval(broken)
    else: reg.on(reg.host[1], broken)
''', 'guard')
    messages, calls = ['first', event], []
    reg = load(Registry(host=messages, agent=calls), paths=[path])
    baseline = len(reg.notes)
    for message in ('first', 'first', 'second'):
        messages[0] = message
        result = reg.approve('tool', {}) if event == 'approval' else reg.fire(event)
        assert result == ('deny' if event == 'approval' else [f'mod guard failed: {message}'])
    assert calls == ['guard'] * 3
    assert len(reg.notes) == baseline + 2


@pytest.mark.parametrize('kind', ['once', 'failed', 'cancelled'])
def test_timers_remove_finished_entries(kind):
    reg = Registry()
    def callback():
        if kind == 'failed': raise ValueError('timer stopped')
    timer = reg.after(0.001, callback) if kind == 'once' else reg.every(0.001 if kind == 'failed' else 3600, callback)
    if kind == 'cancelled': timer.cancel()
    timer.thread.join(2)
    assert not timer.thread.is_alive()
    assert not reg.timers
    assert not any(e.kind == 'timer' for e in reg._entries)


def test_load_marks_span_even_on_interrupt(tmp_path):
    path = mod_file(tmp_path, r'''
def setup(reg):
    reg.command('partial', lambda a, arg: arg)
    raise KeyboardInterrupt()
''')
    reg = Registry()
    with pytest.raises(KeyboardInterrupt): load(reg, paths=[path])
    assert reg.loaded
    reg.drop_loaded()
    assert not reg.mods and not reg.commands


def test_system_exit_disables_mod(tmp_path):
    path = mod_file(tmp_path, "def setup(reg): raise SystemExit('exit from mod')")
    reg = load(Registry(), paths=[path])
    assert not reg.mods[0].on
    assert 'exit from mod' in reg.mods[0].note


def test_registry_mutations_hold_lock(tmp_path):
    reg = Registry()
    class LockedList(list):
        def append(self, value):
            assert reg._lock._is_owned()
            super().append(value)
    reg.mods = LockedList()
    path = mod_file(tmp_path, 'def setup(reg): pass')
    load(reg, paths=[path])
    class LockedMod(skills.AttrDict):
        def __setattr__(self, key, value):
            if key == 'on': assert reg._lock._is_owned()
            super().__setattr__(key, value)
    mod = LockedMod(reg.mods[0])
    reg.mods[0] = mod
    reg.off('example')
    reg.on_mod('example')
    reg.notes = LockedList()
    def broken(): raise ValueError('raw hook')
    reg.hooks['session_end'].append(broken)
    reg.fire('session_end')


def test_drop_loaded_reassignments_hold_lock(tmp_path):
    class LockedRegistry(Registry):
        checking = False
        def __setattr__(self, key, value):
            if self.checking and key in ('mods', 'notes'): assert self._lock._is_owned()
            super().__setattr__(key, value)
    path = mod_file(tmp_path, 'def setup(reg): pass')
    reg = load(LockedRegistry(), paths=[path])
    reg.checking = True
    reg.drop_loaded()


def test_plain_tuple_mark_preserves_existing_registrations():
    reg = Registry()
    original = lambda: 'original'
    reg.tool(original)
    reg.command('original', original)
    before = tuple(reg.mark())
    reg.tool(lambda: 'loaded')
    reg.command('loaded', lambda: None)
    reg.mark_loaded(before)
    reg.drop_loaded()
    assert reg.tools == [original]
    assert list(reg.commands) == ['original']


@pytest.mark.parametrize('configured', [False, True])
def test_explicit_file_home(tmp_path, configured):
    path = mod_file(tmp_path, 'def setup(reg): pass')
    cfg = tmp_path/'cfg' if configured else None
    reg = load(Registry(), cfg=cfg, paths=[path])
    assert reg.mods[0].home == (cfg/'mods'/'example' if configured else path.parent/'example')


def test_owned_threads_and_callback_context(tmp_path):
    path = mod_file(tmp_path, r'''
def setup(reg):
    def context(*args):
        return reg.mod, reg.home
    def worker():
        reg.notify(reg.mod)
        reg.command('threaded', lambda a, arg: context())
    reg.host.append(reg.thread(worker))
    reg.tool(context)
    reg.command('context', context)
    reg.on('session_end', context)
    reg.status(context)
    reg.band(context)
    reg.after(0.001, lambda: reg.agent.append(context()))
''')
    threads, timer_results = [], []
    reg = load(Registry(host=threads, agent=timer_results), cfg=tmp_path, paths=[path])
    assert reg.mods[0].on, reg.notes
    for thread in threads:
        thread.join(2)
        assert thread.daemon and not thread.is_alive()
    for timer in list(reg.timers): timer.thread.join(2)
    expected = ('example', tmp_path/'mods'/'example')
    assert reg.tools[0]() == expected
    assert reg.commands['context'][0](None, '') == expected
    assert reg.commands['threaded'][0](None, '') == expected
    assert reg.fire('session_end') == [expected]
    assert reg.status_segments[0](None) == expected
    assert reg.bands[0](None) == expected
    assert timer_results == [expected]
    assert reg.drain_notices() == [dict(mod='example', text='example')]
    assert reg.mod is None and reg.home is None
    reg.off('example')
    assert not reg.commands


def test_only_defers_module_execution(tmp_path):
    path = mod_file(tmp_path, r'''
raise RuntimeError('module ran')
''')
    reg = load(Registry(), paths=[path], only=[])
    assert not reg.mods[0].on and reg.mods[0].note == 'not in this vesha'
    path.write_text("def setup(reg): reg.command('enabled', lambda a, arg: arg)")
    reg.on_mod('example')
    assert reg.mods[0].on and 'enabled' in reg.commands


def test_each_names_live_hooks_and_chains_rewrites(tmp_path):
    path = mod_file(tmp_path, r'''
def setup(reg):
    reg.on('before_turn', lambda a, prompt: dict(prompt=prompt + ' owned'))
    def broken(*args): raise ValueError('closed')
    reg.on('before_turn', broken)
    reg.on('session_end', broken)
''')
    reg = Registry()
    reg.on('before_turn', lambda a, prompt: dict(prompt=prompt + ' unowned'))
    load(reg, paths=[path])
    hooks = reg.each('before_turn')
    assert [name for name, fn in hooks] == [None, 'example', 'example']
    prompt = 'start'
    for name, fn in hooks[:2]: prompt = fn(None, prompt)['prompt']
    assert prompt == 'start unowned owned'
    assert hooks[2][1](None, prompt) == 'mod example failed: closed'
    assert reg.each('session_end')[0][1]() is None
    assert reg.each('session_end') == []
    reg.off('example')
    assert [name for name, fn in reg.each('before_turn')] == [None]


def test_tool_wrapper_preserves_schema(tmp_path):
    path = mod_file(tmp_path, r'''
def setup(reg):
    def documented(value: int, label: str = 'x') -> str:
        "Return the labeled value."
        assert reg.mod == 'example'
        return f'{label}: {value}'
    reg.agent.append(documented)
    reg.tool(documented)
''')
    originals = []
    reg = load(Registry(agent=originals), paths=[path])
    tool = reg.tools[0]
    assert tool(2) == 'x: 2'
    assert inspect.signature(tool) == inspect.signature(originals[0])
    assert (tool.__name__, tool.__doc__, tool.__annotations__) == (originals[0].__name__, originals[0].__doc__, originals[0].__annotations__)


def test_store_persistence_and_locked_updates(tmp_path):
    path = mod_file(tmp_path, r'''
def setup(reg):
    reg.agent.append(reg.store({'count': 0}))
    reg.command('store', lambda a, arg: reg.store())
''')
    stores = []
    reg = load(Registry(agent=stores), cfg=tmp_path, paths=[path])
    assert reg.mods[0].on, reg.notes
    store = stores[0]
    target = tmp_path/'mods'/'example'/'state.json'
    assert not target.exists()
    assert store.data == {'count': 0}
    assert reg.commands['store'][0](None, '') is store
    store.save()
    assert json.loads(target.read_text()) == {'count': 0}
    other = load(Registry(agent=stores), cfg=tmp_path, paths=[path])
    def increment(i):
        current = stores[i % 2]
        return current.update(lambda data: data.update(count=data['count'] + 1))
    with ThreadPoolExecutor(max_workers=8) as pool: list(pool.map(increment, range(40)))
    assert json.loads(target.read_text()) == {'count': 40}
    assert store.update(lambda data: None) == {'count': 40}
    target.write_text('not json')
    stores2 = []
    load(Registry(agent=stores2), cfg=tmp_path, paths=[path])
    assert stores2[0].data == {'count': 0}
    assert (target.parent/'state.lock').exists()
    assert {p.name for p in target.parent.iterdir()} == {'state.json', 'state.lock'}


def test_store_without_home_stays_in_memory():
    reg = Registry()
    stores = []
    def setup(reg):
        assert reg.mod == 'memory' and reg.home is None
        stores.append(reg.store({'count': 1}))
        reg.command('store', lambda a, arg: reg.store())
    mod = reg.add_mod('memory', setup)
    assert mod is reg.mods[0] and mod.setup is setup and mod.on
    store = stores[0]
    assert store.update(lambda data: data.update(count=data['count'] + 1)) == {'count': 2}
    store.save()
    assert reg.commands['store'][0](None, '') is store
    assert reg.mod is None and reg.home is None
    reg.off('memory')
    assert not reg.commands
    reg.on_mod('memory')
    assert stores[-1] is store


@pytest.mark.parametrize('damage', ['json', 'shape', 'encoding', 'unreadable'])
def test_store_problem_blocks_writes_and_reload_recovers(tmp_path, damage):
    path = mod_file(tmp_path, "def setup(reg): reg.agent.append(reg.store({'count': 1}))")
    stores = []
    load(Registry(agent=stores), paths=[path])
    store = stores[0]
    target = tmp_path/'example'/'state.json'
    target.parent.mkdir()
    if damage == 'unreadable': target.mkdir()
    else: target.write_bytes({'json': b'broken', 'shape': b'[]', 'encoding': b'\xff'}[damage])
    assert store.data == {'count': 1}
    assert store.problem
    def forbidden(data): pytest.fail('corrupt data reached update callback')
    with pytest.raises(ValueError, match='state.json'): store.update(forbidden)
    with pytest.raises(ValueError, match='state.json'): store.save()
    if damage == 'unreadable': target.rmdir()
    else:
        assert target.read_bytes() == {'json': b'broken', 'shape': b'[]', 'encoding': b'\xff'}[damage]
    target.write_text('{"count": 7}')
    assert store.reload() == {'count': 7} and store.problem == ''
    assert store.update(lambda data: data.update(count=8)) == {'count': 8}
    target.write_text('broken again')
    with pytest.raises(ValueError, match='state.json'): store.save()
    assert target.read_text() == 'broken again'
    target.unlink()
    assert store.reload() == {'count': 1} and store.problem == ''
    store.save()
    assert json.loads(target.read_text()) == {'count': 1}


@pytest.mark.parametrize('name', ['sample', '_sample', '.sample'])
def test_add_mod_home_and_setup_failure(tmp_path, name):
    reg = Registry()
    def setup(reg):
        assert reg.mod == name and reg.home == tmp_path
        reg.command('sample', lambda a, arg: (reg.mod, reg.home))
    mod = reg.add_mod(name, setup, home=str(tmp_path))
    assert mod.source and mod.path is None
    assert reg.commands['sample'][0](None, '') == (name, tmp_path)
    def broken(reg):
        reg.tool(lambda: None)
        raise ValueError('setup broke')
    replacement = reg.add_mod(name, broken, home=tmp_path)
    assert reg.mods == [replacement] and not replacement.on
    assert 'setup broke' in replacement.note
    assert not reg.tools and not reg.commands
    assert reg.mod is None and reg.home is None


def test_setup_note_lists_only_registered_kinds(tmp_path):
    path = mod_file(tmp_path, r'''
def setup(reg):
    reg.tool(lambda: None)
    reg.command('example', lambda a, arg: arg)
    reg.on('before_turn', lambda a: None)
    reg.on('after_turn', lambda a: None)
    reg.status(lambda a: 'ready')
''')
    reg = load(Registry(), paths=[path])
    assert reg.mods[0].note == '1 tool, 1 command, 2 hooks, 1 status'
    reg.off('example')
    path.write_text('def setup(reg): pass')
    reg.mods[0].setup = None
    reg.on_mod('example')
    assert reg.mods[0].note == 'nothing registered'


def test_status_texts_reentry_order_and_failure_isolation():
    reg = Registry()
    calls = []
    def nested(agent):
        calls.append(agent)
        assert reg.status_texts(agent) == []
        return 'nested'
    def broken(agent):
        calls.append('broken')
        raise ValueError('status broke')
    for fn in (nested, lambda a: None, lambda a: '', broken, lambda a: 'last', lambda a: 7):
        reg.status(fn)
    assert reg.status_texts('agent') == ['nested', 'last']
    assert reg.status_texts('again') == ['nested', 'last']
    assert calls == ['agent', 'broken', 'again']
    assert len(reg.notes) == 1 and 'status broke' in reg.notes[0]


def test_check_adds_tool_docs(tmp_path):
    path = mod_file(tmp_path, r'''
def setup(reg):
    def documented(value: int, label: str = 'x') -> str:
        "Return the labeled value."
        return str(value)
    reg.tool(documented)
''')
    report = skills.check(path)
    assert report['tools'] == ['documented']
    assert report['tool_docs'] == [dict(name='documented', signature="(value: int, label: str = 'x') -> str", doc='Return the labeled value.')]
