"""A hard link is a second name for the same file, so one inside a root can hold a file that lives outside it.

`Sandbox.check` resolves symbolic links, which a hard link is not. A read through one is refused instead.
"""
import os
import pytest

from shalya import LocalHost
from shalya.core import SANDBOX, SECRET, Unsafe, denied
from shalya.tools import tools_for


def test_a_read_through_a_hard_link_is_refused_and_a_plain_file_is_read(tmp_path):
    root, ref, outside = tmp_path/'root', tmp_path/'ref', tmp_path/'outside.txt'
    root.mkdir(); ref.mkdir(); outside.write_text('outside secret\n')
    for d in (root, ref):
        os.link(outside, d/'link.txt')
        (d/'plain.txt').write_text('inside\n')
    assert os.stat(root/'link.txt').st_nlink == 3, 'outside.txt and the two links share one file'
    h = LocalHost([str(root)], read_roots=[str(ref)], index=False, web=False)
    view = {t.__name__: t for t in tools_for(h)}['view_file']
    (root/'sym.txt').symlink_to(outside)
    with pytest.raises(Unsafe, match=SANDBOX): h.check(root/'sym.txt', must_exist=True, reading=True)
    for d in (root, ref):
        assert os.stat(d/'plain.txt').st_nlink == 1
        assert h.read(str(d/'plain.txt')) == 'inside\n'
        with pytest.raises(Unsafe, match='hard link'): h.check(d/'link.txt', must_exist=True, reading=True)
        assert h.read(str(d/'link.txt')) is None
        shown = view(str(d/'link.txt'))
        assert shown.startswith('ERROR') and 'outside secret' not in shown


@pytest.mark.parametrize('package', ['.venv/lib/python3.13/site-packages/pkg/mod.py', 'node_modules/pkg/mod.js'])
def test_package_manager_hard_links_remain_readable(tmp_path, package):
    root, cache = tmp_path/'root', tmp_path/'cache'
    cache.mkdir()
    source = cache/'module'; source.write_text('package code\n')
    installed = root/package
    installed.parent.mkdir(parents=True)
    os.link(source, installed)
    host = LocalHost([str(root)], index=False, web=False)
    view = {t.__name__: t for t in tools_for(host)}['view_file']
    assert host.read(str(installed)) == 'package code\n'
    assert 'package code' in view(str(installed))


def test_keychain_kdbx_and_pfx_files_are_credentials(tmp_path):
    for name in ('login.keychain', 'login.keychain-db', 'vault.kdbx', 'cert.pfx', 'CERT.PFX'): assert denied(f'/proj/{name}'), name
    ref = tmp_path/'ref'; ref.mkdir(); (ref/'vault.kdbx').write_text('x')
    h = LocalHost([], read_roots=[str(ref)], index=False, web=False)
    with pytest.raises(Unsafe, match=SECRET): h.check(ref/'vault.kdbx', reading=True)
