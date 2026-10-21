"The pane a host runs in is the one tmux started it in, `$TMUX_PANE`, not whichever pane is active. Runs a private tmux server; skipped without tmux or fastmux."
import os, shutil, subprocess, tempfile
import pytest
from shalya.host import LocalHost

pytestmark = pytest.mark.skipif(not shutil.which('tmux'), reason='needs tmux')
pytest.importorskip('fastmux')

@pytest.fixture
def server():
    "A tmux server of its own, with two windows; the second is active."
    sock = os.path.join(tempfile.mkdtemp(dir='/tmp'), 's')   # a socket path must stay under ~104 bytes
    tm = lambda *a: subprocess.run(['tmux', '-S', sock, *a], capture_output=True, text=True, check=True, stdin=subprocess.DEVNULL).stdout.strip()
    first = tm('new-session', '-d', '-P', '-F', '#{pane_id}', 'sleep 60')
    second = tm('new-window', '-P', '-F', '#{pane_id}', 'sleep 60')
    yield sock, first, second
    subprocess.run(['tmux', '-S', sock, 'kill-server'], capture_output=True, stdin=subprocess.DEVNULL)

def test_the_host_takes_its_own_pane_not_the_active_one(server, tmp_path, monkeypatch):
    sock, first, second = server
    monkeypatch.setenv('TMUX', f'{sock},0,0')
    monkeypatch.setenv('TMUX_PANE', first)
    assert LocalHost([str(tmp_path)], index=False, web=False).tmux_pane.id == first, f'{second} is active, but this process runs in {first}'
    assert LocalHost([str(tmp_path)], index=False, web=False, tmux=second).tmux_pane.id == second, 'a pane named for the host is that pane'
