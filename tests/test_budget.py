"Every result fits the budget its caller sets, and one that nothing can page keeps the rest in a readable file."
import re
from pathlib import Path
from types import SimpleNamespace as NS
from shalya.tools import shell_tools, session_tools, web_tools, skill_tools

BIG = ''.join(f'row {i}\n' for i in range(5000))


def _saved(out):
    m = re.search(r'saved to (\S+?);', out)
    return Path(m.group(1)) if m else None


def test_long_results_fit_the_budget_and_keep_the_rest():
    mx = 2000
    host = NS(run_cmd=lambda cmd, cwd=None, timeout=120: (0, BIG), cmd_output=lambda rid, n: ('done', BIG),
              run_python=lambda code: BIG, inspect_python=lambda code, scope='isolated': BIG, list_vars=lambda: BIG,
              terminal_text=lambda n: BIG, read_url=lambda url, remember=True: NS(text=BIG), research_note='')
    skill = NS(name='big', where='skills/big', text=lambda: BIG)
    tools = {t.__name__: t for t in shell_tools(host, mx) + session_tools(host, mx) + web_tools(host, mx)
             + skill_tools(host, lambda: [skill], mx)}
    calls = {'run_shell': ('make',), 'shell_output': ('r1',), 'run_python': ('x',), 'inspect_python': ('x',),
             'read_terminal': (), 'read_url': ('https://example.com',), 'read_skill': ('big',)}
    for name, args in calls.items():
        out = tools[name](*args)
        assert len(out) <= mx, (name, len(out))
        p = _saved(out)
        assert p is not None and BIG.strip() in p.read_text(), (name, out[-300:])
    assert '| tail' not in tools['run_shell']('make')
