"""What an agent is left holding when it may not act.

`read_only` answers three separate questions, and a caller can ask them in any combination: may it
write a file the user owns, may it act in the other ways that write nothing, and are there names
this particular caller refuses. The notebook shows the shape of the result; what is worth asserting
here is each axis on its own, and the two ways a tool can be recognised.

A tool built by the factories carries its mark. A tool that arrived from an extension may not, so
every refusal is checked by name as well. The doubles below are deliberately unmarked: they stand
for exactly that case.
"""
import pytest

from shalya.core import ACTING_TOOLS, WRITE_TOOLS, acts, has_effect, is_write, writes
from shalya.tools import read_only


def tool(name, **attrs):
    "An unmarked function under `name`, standing in for a tool that arrived without its mark."
    def f(**kw): return name
    f.__name__ = name
    for k, v in attrs.items(): setattr(f, k, v)
    return f


def names(ts): return {t.__name__ for t in ts}


def test_a_write_is_refused_by_its_mark():
    marked = writes(tool('anything_at_all'))
    assert is_write(marked)
    assert names(read_only([marked, tool('search_code')])) == {'search_code'}


def test_a_write_is_refused_by_its_name_when_the_mark_never_arrived():
    "An extension may register `edit_file` and forget `@writes`. The refusal cannot depend on it."
    assert not is_write(tool('edit_file'))
    assert names(read_only([tool('edit_file'), tool('search_code')])) == {'search_code'}


def test_granting_writes_returns_them_all():
    ts = [writes(tool('run_shell')), tool('edit_file'), tool('search_code')]
    assert names(read_only(ts, writes=True)) == {'run_shell', 'edit_file', 'search_code'}


def test_acting_tools_are_kept_by_default_because_a_sub_agent_still_researches():
    ts = [tool('research'), tool('inspect_python'), tool('search_code')]
    assert names(read_only(ts)) == {'research', 'inspect_python', 'search_code'}


def test_effects_false_withholds_what_acts_without_writing_a_file_the_user_owns():
    ts = [acts(tool('generate_image')), tool('api_call'), tool('search_code')]
    assert names(read_only(ts, effects=False)) == {'search_code'}


@pytest.mark.parametrize('name', sorted(ACTING_TOOLS))
def test_every_named_acting_tool_is_withheld_by_effects_false(name):
    assert names(read_only([tool(name), tool('view_file')], effects=False)) == {'view_file'}


@pytest.mark.parametrize('name', sorted(WRITE_TOOLS))
def test_every_named_write_tool_is_withheld_by_default(name):
    assert names(read_only([tool(name), tool('view_file')])) == {'view_file'}


def test_the_two_axes_are_independent():
    "Approval gates writes and nothing else, so a tool that acts must not become a write."
    acting = acts(tool('research'))
    assert has_effect(acting) and not is_write(acting)
    written = writes(tool('create_file'))
    assert is_write(written) and not has_effect(written)


def test_block_refuses_names_the_caller_names_whatever_else_they_are():
    "Ramabana passes its own delegation tools here; they are reads by every other measure."
    ts = [tool('delegate_search'), tool('search_code')]
    assert names(read_only(ts, block={'delegate_search'})) == {'search_code'}
    assert names(read_only(ts, writes=True, block={'delegate_search'})) == {'search_code'}


def test_a_safe_variant_replaces_the_tool_it_belongs_to():
    "`read_url` keeps its page and loses the vault entry, and the argument leaves the schema."
    full = tool('read_url')
    safe = tool('read_url')
    full.read_only = safe
    got, = read_only([full])
    assert got is safe
    assert read_only([full], writes=True) == [full]


def test_the_budget_stops_the_loop_and_does_not_call_itself_a_sub_agents():
    "The guard is reachable now without delegating, so the message cannot say `sub-agent`."
    look, = read_only([tool('search_code')], max_calls=1)
    assert look() == 'search_code'
    spent = look()
    assert 'budget exhausted' in spent.lower()
    assert 'sub-agent' not in spent.lower()


def test_the_budget_is_shared_across_every_tool_in_one_grant():
    "One task, one allowance. A budget per tool would be no budget at all."
    ts = read_only([tool('search_code'), tool('view_file')], max_calls=1)
    by = {t.__name__: t for t in ts}
    by['search_code']()
    assert 'budget exhausted' in str(by['view_file']()).lower()
