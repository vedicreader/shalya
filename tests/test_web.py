"""read_page: fossick.read delegates the dedicated readers, and the generic-web path stays its own.

No network. Every fossick is a stand-in whose `read`, `what_is`, `fetch` and `to_md` answer the way
the real module does, so each branch of `read_page` is exercised without touching Chrome or the web.
"""
from fastcore.basics import AttrDict
from shalya.host import read_page, THIN_PAGE

LONG = 'word ' * 400          # comfortably over THIN_PAGE, so a page never counts as thin
KEYS = {'text', 'url', 'title', 'kind', 'sections', 'strategy'}


class _Page:
    "A fetched page: its markdown, the tier `auto` reached, and no articles."
    def __init__(self, md='', tier=None):
        self.md, self.tier, self.html_content = md, tier, ''
    def css(self, sel): return []


class _Fossick:
    "A fossick with `read`, so `read_page` delegates the dedicated readers to it."
    def __init__(self, kind, res=None, page=None):
        self._kind, self._res, self._page, self.reads, self.fetches = kind, res, page, [], []
    def what_is(self, url): return self._kind
    def read(self, url, **kw):
        self.reads.append(url)
        return self._res
    def fetch(self, url, **kw):
        self.fetches.append(kw)
        return self._page
    def to_md(self, page, sel=None, multi=False):
        return page.md if isinstance(page, _Page) else ''


def _res(kind, text=LONG, title='', source=None, ok=True):
    return AttrDict(ok=ok, kind=kind, title=title, source=source, text=text, skipped=None, meta={})


def test_a_pdf_url_now_returns_text_mapped_to_a_page():
    "shalya used to drop PDF urls; fossick.read gives it real text, tagged page/pdf2md."
    f = _Fossick('pdf', _res('pdf', text='pdf body ' * 200, title='Doc', source='https://x/doc.pdf'))
    got = read_page(f, 'https://x/doc.pdf')
    assert (got.kind, got.strategy, got.sections) == ('page', 'pdf2md', [])
    assert got.text.startswith('pdf body') and got.title == 'Doc' and got.url == 'https://x/doc.pdf'
    assert f.fetches == [], 'the reader answered, so the page is never fetched'


def test_an_arxiv_url_maps_to_a_paper_via_the_reader():
    f = _Fossick('arxiv', _res('arxiv', title='A Paper', source='https://arxiv.org/abs/2401.00001'))
    got = read_page(f, 'https://arxiv.org/abs/2401.00001')
    assert (got.kind, got.strategy, got.sections) == ('paper', 'read_arxiv', [])
    assert got.title == 'A Paper' and got.text == LONG


def test_a_ghfile_maps_to_repo_and_youtube_maps_to_page():
    gh = _Fossick('ghfile', _res('ghfile', title='m.py'))
    assert read_page(gh, 'https://github.com/o/r/blob/main/m.py').kind == 'repo'
    assert read_page(gh, 'https://github.com/o/r/blob/main/m.py').strategy == 'read_gh_file'
    yt = _Fossick('youtube', _res('youtube', title='A Video'))
    assert read_page(yt, 'https://youtu.be/abc').kind == 'page'
    assert read_page(yt, 'https://youtu.be/abc').strategy == 'read_yt'


def test_a_reader_that_cannot_answer_falls_through_to_the_page():
    "ok=False (a youtube with no transcript, say) is not a url that cannot be read: fetch the page."
    f = _Fossick('youtube', _res('youtube', text='', ok=False), page=_Page(md=LONG))
    got = read_page(f, 'https://youtu.be/abc')
    assert got.kind == 'page' and got.strategy == 'readability'
    assert f.fetches == [{}]   # no `auto`: an untrusted host never reaches the logged-in Chrome


def test_a_generic_web_url_stays_on_the_fetch_and_extract_path():
    "kind 'web' is not a dedicated reader: read is never called, and the extractor names the strategy."
    f = _Fossick('web', res=None, page=_Page(md=LONG))
    got = read_page(f, 'https://example.com/a')
    assert f.reads == [], 'the generic path never calls fossick.read'
    assert f.fetches == [{}]
    assert got.kind == 'page' and got.strategy == 'readability' and isinstance(got.sections, list)


def test_every_path_returns_the_same_result_keys():
    "The reader branch and the generic branch return the identical contract."
    reader = read_page(_Fossick('pdf', _res('pdf')), 'https://x/doc.pdf')
    web = read_page(_Fossick('web', page=_Page(md=LONG)), 'https://example.com/a')
    assert set(reader) == set(web) == KEYS


class _Spy:
    "A fossick whose every fetch answers with the same thin page, tagged with the tier `auto` reached."
    def __init__(self, tier):
        self.tier, self.fetches = tier, []
    def what_is(self, url): return 'web'
    def read(self, url, **kw): return None
    def fetch(self, url, **kw):
        self.fetches.append(kw)
        return _Page(md='thin', tier=self.tier)
    def to_md(self, page, sel=None, multi=False): return page.md


def test_a_page_auto_already_took_to_stealthy_is_not_re_fetched_stealthily():
    f = _Spy('stealthy')
    read_page(f, 'https://example.com/a')
    assert f.fetches == [{}, {'heavy': True, 'network_idle': True}]
    assert not any(kw.get('stealthy') for kw in f.fetches)


def test_a_thin_page_that_never_reached_stealthy_still_retries_stealthily():
    f = _Spy('plain')
    read_page(f, 'https://example.com/a')
    assert {'stealthy': True} in f.fetches
    assert f.fetches == [{}, {'heavy': True, 'network_idle': True}, {'stealthy': True}]


class _Typed(_Fossick):
    "A fossick whose pages carry a Content-Type."
    def __init__(self, kind, ct, md=LONG, res=None):
        super().__init__(kind, res)
        self.ct, self.md = ct, md
    def fetch(self, url, **kw):
        self.fetches.append(kw)
        pg = _Page(md=self.md)
        pg.headers = {'Content-Type': self.ct}
        return pg


def test_fetch_kw_reaches_each_fetch():
    "`max_bytes` and the other options go to fossick.fetch as they are, on the first fetch and on the rendered retries."
    f = _Typed('web', 'text/html; charset=utf-8', md='thin')
    read_page(f, 'https://example.com/a', fetch_kw=dict(max_bytes=1000, timeout=5, allow_private=False))
    assert f.fetches[0] == dict(max_bytes=1000, timeout=5, allow_private=False)
    assert f.fetches[1:] == [dict(max_bytes=1000, timeout=5, allow_private=False, heavy=True, network_idle=True),
                             dict(max_bytes=1000, timeout=5, allow_private=False, stealthy=True)]


def test_fetch_kw_cannot_turn_on_auto():
    "Only `session_hosts` lets a fetch reach the logged-in debug Chrome."
    f = _Typed('web', 'text/html')
    read_page(f, 'https://example.com/a', fetch_kw=dict(auto=True, timeout=5))
    assert f.fetches == [dict(timeout=5)]


def test_thin_zero_is_one_plain_fetch():
    f = _Typed('web', 'text/html', md='thin')
    read_page(f, 'https://example.com/a', fetch_kw=dict(max_bytes=10), thin=0)
    assert f.fetches == [dict(max_bytes=10)]


def test_a_pdf_is_refused_when_types_is_set():
    "The pdf reader is not asked, and the fetched page says application/pdf, so the answer is None with a note."
    said, f = [], _Typed('pdf', 'application/pdf', res=_res('pdf', text='pdf body ' * 200))
    assert read_page(f, 'https://x/doc.pdf', types=('text/html', 'text/plain'), note=said.append) is None
    assert f.reads == [] and len(f.fetches) == 1
    assert 'application/pdf' in said[-1]


def test_a_page_of_an_allowed_type_is_read():
    f = _Typed('web', 'text/html; charset=utf-8')
    got = read_page(f, 'https://example.com/a', types=('text/html', 'text/plain'))
    assert got.strategy == 'readability' and got.text == LONG.strip()


def test_a_page_with_no_type_is_refused_when_types_is_set():
    f = _Fossick('web', page=_Page(md=LONG))
    assert read_page(f, 'https://example.com/a', types=('text/html',)) is None


def test_a_reader_runs_when_its_type_is_allowed():
    f = _Typed('pdf', 'application/pdf', res=_res('pdf', text='pdf body ' * 200))
    assert read_page(f, 'https://x/doc.pdf', types=('application/pdf',)).strategy == 'pdf2md'


def test_the_default_path_does_not_change():
    "No `fetch_kw` and no `types`: one fetch with no options, and a PDF still goes to the reader."
    f = _Typed('web', 'application/pdf')
    assert read_page(f, 'https://example.com/a').strategy == 'readability' and f.fetches == [{}]
    f = _Typed('pdf', 'application/pdf', res=_res('pdf', text='pdf body ' * 200))
    assert read_page(f, 'https://x/doc.pdf').strategy == 'pdf2md' and f.fetches == []


def test_a_host_passes_its_fetch_kw_and_types(tmp_path):
    "`LocalHost.FETCH_KW` and `LocalHost.TYPES` reach `read_page` through `read_url`."
    from shalya.host import LocalHost
    class H(LocalHost): FETCH_KW, TYPES = dict(max_bytes=10), ('text/html',)
    h, f = H([str(tmp_path)], index=False), _Typed('web', 'application/pdf')
    h._fossick = lambda: f
    assert h.read_url('https://example.com/a.pdf') is None and f.fetches == [dict(max_bytes=10)]
