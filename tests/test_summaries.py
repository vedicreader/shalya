"""The one line a person reads after a call, and the guarantee that every tool carries one.

The summary used to live in a dispatch on tool names, in the package that runs the tools rather
than the one that defines them. It drifted both ways: the git group moved here and its five tools
were never given one, and four delegation tools were added there and forgotten. Both rendered as
`git_status(path='/proj')` in an activity feed, beside `Search frontmatter`.

The mark is on the tool now, beside its docstring, so the two cannot separate. What is worth
asserting is that no tool is ever built without one, and that the fallback still says something
when a caller names a tool this package has never heard of.
"""
import pytest

from shalya.core import SUMMARIES, one_line, summarise, summary
from shalya.host import LocalHost
from shalya.tools import (api_tools, ask_tools, code_tools, file_tools, git_tools, image_tools,
                          memory_tools, notebook_tools, session_tools, shell_tools, skill_tools,
                          watch_tools, web_tools)


class AnyHost:
    "Answers anything a factory asks for while it builds, so every group can be built here."
    roots = ('/proj',)
    indexed = True
    def __getattr__(self, n): return lambda *a, **kw: None
    def __init__(self): pass


def every_tool(tmp_path):
    "One of every tool this package defines, whatever host each factory wants."
    h = AnyHost()
    out = list(code_tools(LocalHost([tmp_path], index=False, web=False)))
    for f in (file_tools, notebook_tools, web_tools, memory_tools, ask_tools, watch_tools,
              session_tools, shell_tools, skill_tools, api_tools, git_tools):
        try: out += list(f(h))
        except Exception: pass
    try: out += list(image_tools(h))
    except Exception: pass
    return out


def test_every_tool_this_package_builds_carries_its_own_summary(tmp_path):
    "A tool without one renders as `name(args)`, which is what the dispatch used to do by accident."
    built = every_tool(tmp_path)
    assert len(built) > 30, f'only {len(built)} tools built; the sweep stopped finding them'
    bare = sorted({t.__name__ for t in built if getattr(t, 'summary', None) is None})
    assert bare == [], f'no summary on: {bare}'


def test_the_summary_reads_the_arguments_of_the_call_it_labels(tmp_path):
    by = {t.__name__: t for t in every_tool(tmp_path)}
    assert summarise(by['search_code'], {'query': 'frontmatter'}) == 'Search frontmatter'
    assert summarise(by['view_file'], {'path': 'a.py', 'start': 4, 'end': 9}) == 'View a.py:4-9'
    assert summarise(by['view_file'], {'path': 'a.py'}) == 'View a.py'


def test_a_name_is_enough_because_an_activity_row_holds_no_tool():
    "What was called is recorded, not the object that ran it, so the mark is indexed by name too."
    assert 'search_code' in SUMMARIES
    assert summarise('search_code', {'query': 'x'}) == 'Search x'


def test_a_tool_nobody_marked_still_says_what_was_called():
    got = summarise('word_count', {'path': '/proj/a.py'})
    assert got.startswith('word_count(') and '/proj/a.py' in got


def test_a_summary_that_raises_costs_a_label_and_not_the_call():
    "It labels a call that has already happened. A bad one must never surface as a tool failure."
    @summary(lambda a: a['missing'])
    def brittle(): pass
    assert summarise(brittle, {}).startswith('brittle(')


def test_one_line_keeps_a_value_to_one_line_and_says_where_it_cut():
    assert one_line('a\n  b\tc') == 'a b c'
    assert one_line('x' * 200).endswith('…') and len(one_line('x' * 200)) == 90
    assert one_line(None) == ''


@pytest.mark.parametrize('name', ['git_status', 'git_divergence', 'git_rebase_preview',
                                  'git_remote', 'git_checkout', 'add_root', 'ask_memory',
                                  'api_load', 'api_ops', 'api_call', 'generate_image', 'public_api'])
def test_the_tools_the_old_dispatch_never_named_have_one_now(name):
    assert name in SUMMARIES, f'{name} still renders as its own call'
    assert not SUMMARIES[name]({}).startswith(f'{name}('), 'that is the fallback, not a summary'
