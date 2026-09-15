"""Validate archive integrity and preservation of existing executable paths."""
import hashlib
import importlib.machinery
import importlib.util
import io
import os
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest import mock

SOURCE = Path(__file__).resolve().parents[1] / 'bin/install-zellij'
LOADER = importlib.machinery.SourceFileLoader('install_zellij', str(SOURCE))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
MODULE = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(MODULE)
ROUTER_LOADER = importlib.machinery.SourceFileLoader('zellij_compat', str(SOURCE.with_name('zellij-compat')))
ROUTER_SPEC = importlib.util.spec_from_loader(ROUTER_LOADER.name, ROUTER_LOADER)
ROUTER = importlib.util.module_from_spec(ROUTER_SPEC)
ROUTER_LOADER.exec_module(ROUTER)

class InstallZellijTests(unittest.TestCase):
    def archive(self, name='zellij', symlink=False):
        stream = io.BytesIO()
        with tarfile.open(fileobj=stream, mode='w:gz') as tar:
            member = tarfile.TarInfo(name)
            if symlink:
                member.type = tarfile.SYMTYPE
                member.linkname = '/etc/passwd'
                tar.addfile(member)
            else:
                member.size = 6
                tar.addfile(member, io.BytesIO(b'binary'))
        return stream.getvalue()

    def test_valid_archive_extracts_only_binary(self):
        archive = self.archive()
        self.assertEqual(MODULE.extract_binary(archive, hashlib.sha256(archive).hexdigest()), b'binary')

    def test_checksum_failure(self):
        with self.assertRaisesRegex(ValueError, 'checksum'):
            MODULE.extract_binary(self.archive(), '0' * 64)

    def test_symlink_and_path_traversal_refused(self):
        for archive in [self.archive(symlink=True), self.archive('../zellij')]:
            with self.assertRaises(ValueError):
                MODULE.extract_binary(archive, hashlib.sha256(archive).hexdigest())

    def test_existing_executable_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            old = root / 'zellij'
            old.write_text('old')
            old.chmod(0o755)
            new = root / 'new'
            new.write_text('new')
            MODULE.activate(new, old)
            self.assertEqual(old.resolve(), new.resolve())
            self.assertEqual((root / ('zellij.before-' + MODULE.VERSION)).read_text(), 'old')
            MODULE.activate(new, old)

    def test_existing_relative_symlink_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            old = root / 'zellij'
            old.symlink_to('previous')
            new = root / 'new'
            new.write_text('new')
            MODULE.activate(new, old)
            self.assertEqual(os.readlink(root / ('zellij.before-' + MODULE.VERSION)), 'previous')

    def test_mac_launcher_quotes_paths_and_preserves_explicit_socket_directory(self):
        with tempfile.TemporaryDirectory(prefix='zellij test ') as directory:
            binary = Path(directory) / 'zellij'
            binary.write_text('#!/bin/sh\nprintf "%s\\n" "$ZELLIJ_SOCKET_DIR" "$1"\n')
            binary.chmod(0o755)
            with mock.patch.object(MODULE.platform, 'system', return_value='Darwin'):
                launcher = MODULE.write_launcher(binary)
            result = MODULE.subprocess.run([str(launcher), 'one argument'], capture_output=True,
                text=True, env={**os.environ, 'ZELLIJ_SOCKET_DIR':'/explicit/path'})
            self.assertEqual(result.stdout, '/explicit/path\none argument\n')
            environment = dict(os.environ)
            environment.pop('ZELLIJ_SOCKET_DIR', None)
            result = MODULE.subprocess.run([str(launcher), 'one argument'], capture_output=True,
                text=True, env=environment)
            self.assertEqual(result.stdout, '/tmp/zellij-' + str(os.getuid()) + '\none argument\n')

    def test_exact_session_detection(self):
        self.assertEqual(ROUTER.target_session(['-s', 'music', 'action', 'dump-screen'], {}), 'music')
        self.assertEqual(ROUTER.target_session(['attach', '--create', 'music'], {}), 'music')
        self.assertIsNone(ROUTER.target_session(['attach', '--index', '1'], {}))
        self.assertIsNone(ROUTER.target_session(['action', 'write-chars', '-s', 'draft'], {}))
        self.assertEqual(ROUTER.target_session(['action', 'dump-screen'],
                                             {'ZELLIJ_SESSION_NAME': 'music'}), 'music')

    def test_existing_session_routes_to_old_client_without_new_socket_override(self):
        config = {'current': '/new', 'legacy': '/old', 'socket_directory': '/new-sockets'}
        with mock.patch.object(ROUTER.Path, 'is_file', return_value=True), \
             mock.patch.object(ROUTER, 'session_names', side_effect=[{'music'}, {'new-task'}]), \
             mock.patch.dict(os.environ, {}, clear=True), \
             mock.patch.object(ROUTER.os, 'execve', side_effect=RuntimeError('exec')) as execute:
            with self.assertRaisesRegex(RuntimeError, 'exec'):
                ROUTER.run(config, ['attach', 'music'])
            self.assertEqual(execute.call_args.args, ('/old', ['/old', 'attach', 'music'], {}))

    def test_duplicate_session_refused(self):
        with mock.patch.object(ROUTER.Path, 'is_file', return_value=True), \
             mock.patch.object(ROUTER, 'session_names', return_value={'music'}), \
             mock.patch.object(ROUTER.os, 'execve') as execute:
            with self.assertRaisesRegex(ValueError, 'both protocol namespaces'):
                ROUTER.run({'current': '/new', 'legacy': '/old'}, ['attach', 'music'])
            execute.assert_not_called()

    def test_new_session_uses_current_client(self):
        config = {'current': '/new', 'legacy': '/old', 'socket_directory': '/new-sockets'}
        with mock.patch.object(ROUTER.Path, 'is_file', return_value=True), \
             mock.patch.object(ROUTER, 'session_names', return_value={'music'}), \
             mock.patch.dict(os.environ, {}, clear=True), \
             mock.patch.object(ROUTER.os, 'execve', side_effect=RuntimeError('exec')) as execute:
            with self.assertRaisesRegex(RuntimeError, 'exec'):
                ROUTER.run(config, ['attach', '--create', 'new-task'])
            self.assertEqual(execute.call_args.args, ('/new', ['/new', 'attach', '--create', 'new-task'],
                                                     {'ZELLIJ_SOCKET_DIR': '/new-sockets'}))

if __name__ == '__main__':
    unittest.main()
