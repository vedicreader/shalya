"""LocalHost(url_ok=, on_read=): a URL policy and a read observer.

No network. The host's fossick is a stand-in that answers one search and one page, and keeps the URLs it was asked for.
"""
import pytest
from shalya.host import LocalHost, HostError
from shalya.tools import web_tools

LONG = ('word ' * 400).strip()
ROWS = [dict(title='Good', href='https://good.org/a'), dict(title='Bad', href='https://bad.com/b')]


class _Page:
    def __init__(self, md): self.md, self.html_content, self.tier = md, '', None
    def css(self, sel): return []


class _Fossick:
    def __init__(self): self.asked = []
    def search(self, q, n=20): return [dict(r) for r in ROWS]
    def fetch(self, url, **kw):
        self.asked.append(url)
        return _Page(LONG)
    def to_md(self, page, sel=None, multi=False): return page.md if isinstance(page, _Page) else ''


def no_bad(url): return 'a blocked site' if 'bad.com' in url else None


def _host(tmp_path, **kw):
    (tmp_path/'a.txt').write_text('hello')
    h, f = LocalHost([str(tmp_path)], index=False, **kw), _Fossick()
    h._fossick = lambda: f
    return h, f


def test_a_refused_url_never_reaches_fossick(tmp_path):
    h, f = _host(tmp_path, url_ok=no_bad)
    with pytest.raises(HostError, match='a blocked site'): h.read_url('https://bad.com/b')
    assert f.asked == []
    assert h.read_url('https://good.org/a').text == LONG and f.asked == ['https://good.org/a']


def test_the_read_url_tool_says_the_refusal(tmp_path):
    h, f = _host(tmp_path, url_ok=no_bad)
    read_url = {t.__name__: t for t in web_tools(h)}['read_url']
    said = read_url('https://bad.com/b')
    assert said.startswith('ERROR: read_url') and 'a blocked site' in said and f.asked == []


def test_the_search_rows_are_filtered(tmp_path):
    h, _ = _host(tmp_path, url_ok=no_bad)
    assert [r.url for r in h.web_search('q')] == ['https://good.org/a']


def test_the_observer_runs_one_time_for_each_read(tmp_path):
    log = []
    h, _ = _host(tmp_path, on_read=lambda *a: log.append(a))
    rows = h.web_search('q')
    page = h.read_url('https://good.org/a')
    text = h.read(str(tmp_path/'a.txt'))
    gone = h.read(str(tmp_path/'none.txt'))
    assert [a[:2] for a in log] == [('web_search', 'q'), ('read_url', 'https://good.org/a'),
                                    ('read', str(tmp_path/'a.txt')), ('read', str(tmp_path/'none.txt'))]
    assert [a[2] for a in log] == [rows, page, text, gone] and text == 'hello' and gone is None


def test_an_empty_search_is_not_a_read(tmp_path):
    log = []
    h, _ = _host(tmp_path, on_read=lambda *a: log.append(a))
    assert h.web_search('  ') == [] and log == []


def test_the_defaults_change_nothing(tmp_path):
    h, f = _host(tmp_path)
    assert (h.url_ok, h.on_read) == (None, None)
    assert [r.url for r in h.web_search('q')] == [r['href'] for r in ROWS]
    assert h.read_url('https://bad.com/b').text == LONG and f.asked == ['https://bad.com/b']
    assert h.read(str(tmp_path/'a.txt')) == 'hello'
