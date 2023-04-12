#!/usr/bin/env python3
# -*- coding: utf-8 -*-

assert "__main__" != __name__


def _private():
    import os
    import sys
    import typing
    import shutil
    import pathlib
    import tarfile
    import contextlib
    import subprocess

    from . import _oci_image as _oci_image_module
    from . import _script_processor as _script_processor_module
    from . import _temporary_directory as _temporary_directory_module

    from ... import _common as _common_module

    _OciImage = _oci_image_module.Class

    _parse_digest = _oci_image_module.digest.parse
    _make_oci_image = _oci_image_module.make
    _normalize_path = _common_module.path.normalize
    _make_tar_reader = _common_module.tar.reader.make
    _make_tar_writer = _common_module.tar.writer.make
    _parse_manifest_ref = _oci_image_module.meta.parse_manifest_ref
    _validate_manifest_ref = _oci_image_module.meta.validate_manifest_ref
    _make_script_processor = _script_processor_module.make
    _make_temporary_directory = _temporary_directory_module.make

    def _make_digest(ref: typing.Optional[str], digest: typing.Optional[str], image: _OciImage):
        assert isinstance(image, _OciImage)
        if ref is None:
            if digest is None:
                image = tuple(image)[-1]
                assert isinstance(image, dict)
                digest = _parse_digest(value = image["digest"]).value
                image = _parse_manifest_ref(manifest = image)
                image = f"digest = {digest}" if image is None else f"ref = {image}"
                print(f"last manifest will be selected by default, {image}", file = sys.stderr, flush = True)
                return digest
            return _parse_digest(value = digest).value
        ref = _validate_manifest_ref(value = ref)
        _manifests = dict()
        for _manifest in image:
            assert isinstance(_manifest, dict)
            _digest = _parse_digest(value = _manifest["digest"]).value
            _ref = _parse_manifest_ref(manifest = _manifest)
            if _ref is None: continue
            _manifests[_ref] = _digest
        if digest is None: digest = _manifests[ref]
        else:
            assert digest == _parse_digest(digest).value
            assert digest == _manifests[ref]
        return digest

    @contextlib.contextmanager
    def _open_source(path: typing.Optional[str], working_directory: str):
        assert isinstance(working_directory, str)
        assert working_directory
        working_directory, = f"{working_directory}\r\n".splitlines()
        working_directory = _normalize_path(value = working_directory).as_posix()
        working_directory = pathlib.Path(working_directory).resolve(strict = True).as_posix()

        if path is not None:
            assert isinstance(path, str)
            assert path
            if os.path.isdir(path):
                yield _make_oci_image(source = path)
                return

        with _make_tar_reader(source = path) as _reader:
            _reader.open()

            if _reader.seekable and ("application/x-tar" == _reader.magic):
                yield _make_oci_image(source = _reader)
                return

            working_directory = os.path.join(working_directory, "oci")
            print(f"extracting source to temporary directory: {working_directory}", file = sys.stderr, flush = True)
            os.makedirs(working_directory, exist_ok = False)

            try:
                def _extract_member(member: tarfile.TarInfo, stream: typing.Optional[typing.IO[bytes]]):
                    assert isinstance(member, tarfile.TarInfo)
                    _member_path = _member.name
                    assert isinstance(_member_path, str)
                    _member_path = _normalize_path(value = _member_path, drop_root = True).as_posix()
                    if not _member_path.strip("."): return
                    _member_path = os.path.join(working_directory, _member_path)
                    if member.isdir():
                        assert stream is None
                        os.makedirs(_member_path, exist_ok = True)
                        return
                    assert member.isreg()
                    with open(_member_path, "wb") as _destination:
                        while True:
                            _chunk = stream.read(32 * 1024 * 1024)
                            if not _chunk: break
                            assert len(_chunk) == _destination.write(_chunk)

                for _member, _stream in _reader: _extract_member(member = _member, stream = _stream)

                _reader.close()
                if path is None:
                    _stdin_descriptor = sys.stdin.buffer.fileno()
                    sys.stdin.close()
                    sys.stdin.buffer.close()
                    os.close(_stdin_descriptor)

                yield _make_oci_image(source = working_directory)

            finally: shutil.rmtree(working_directory)

    def _inspect_bundle(source: _OciImage, digest: str, working_directory: str):
        assert isinstance(source, _OciImage)
        assert isinstance(digest, str)
        assert isinstance(working_directory, str)
        assert working_directory
        working_directory = os.path.normpath(os.path.abspath(working_directory))
        _collector = []
        os.makedirs(working_directory, exist_ok = False)
        try:
            _oci_path = os.path.join(working_directory, "oci")
            print(f"generating fake image in temporary directory: {_oci_path}", file = sys.stderr, flush = True)
            os.makedirs(_oci_path, exist_ok = False)
            source.install_fake(digest = digest, destination = _oci_path)
            _bundle_path = os.path.join(working_directory, "bundle")
            print(f"extracting fake rootfs to temporary directory: {_bundle_path}", file = sys.stderr, flush = True)
            os.makedirs(_bundle_path, exist_ok = False)
            subprocess.check_call(
                ("oci-image-tool", "unpack", _oci_path, _bundle_path, "--ref", "name=latest"),
                stdin = subprocess.DEVNULL, stdout = sys.stderr
            )
            shutil.rmtree(_oci_path)
            for _absolute_root, _directories, _files in os.walk(_bundle_path):
                _relative_root = pathlib.PurePosixPath(pathlib.Path(_absolute_root).relative_to(_bundle_path).as_posix())
                for _path in _files: _collector.append((_relative_root / _path).as_posix())
                for _path in _directories: _collector.append((_relative_root / _path).as_posix())
        finally: shutil.rmtree(working_directory)
        _collector.sort()
        return tuple(_collector)

    @contextlib.contextmanager
    def _make_destination(
        target: typing.Optional[str],
        script: typing.Optional[list],
        working_directory: str
    ):
        if script is None:
            with _make_tar_writer(destination = target) as _writer:
                _writer.open()
                yield lambda *args, **kwargs: _writer(*args, **kwargs)
            return

        assert isinstance(working_directory, str)
        assert working_directory
        assert os.path.isdir(working_directory)
        working_directory = os.path.join(working_directory, "script")
        assert not os.path.exists(working_directory)

        with _make_script_processor(
            script = script, destination = target, working_directory = working_directory
        ) as _stream:
            with _make_tar_writer(destination = _stream) as _writer:
                _writer.open()
                yield lambda *args, **kwargs: _writer(*args, **kwargs)

    def _routine(
        ref: typing.Optional[str],
        digest: typing.Optional[str],
        source: typing.Optional[str],
        destination: typing.Optional[str],
        working_directory: typing.Optional[str]
    ):
        with _make_temporary_directory(path = working_directory) as working_directory:
            with _open_source(path = source, working_directory = working_directory) as source:
                digest = _make_digest(ref = ref, digest = digest, image = source)
                with source.open_bundle(digest = digest) as _bundle:
                    _bundle_script = _bundle.script
                    try: _bundle_script_path = _bundle_script.pop("path")
                    except KeyError: _bundle_script_path = None
                    else: assert isinstance(_bundle_script_path, str) and bool(_bundle_script_path)
                    _bundle_script = _bundle_script.pop("body") or None
                    _bundle_items = _inspect_bundle(
                        source = source, digest = digest, working_directory = os.path.join(working_directory, "fake")
                    )
                    if destination is None: print(
                        f"writing rootfs tar archive to stdout", file = sys.stderr, flush = True
                    )
                    else: print(f"writing rootfs tar archive file: {destination}", file = sys.stderr, flush = True)
                    with _make_destination(
                        target = destination, script = _bundle_script, working_directory = working_directory
                    ) as destination:
                        for _path in _bundle_items:
                            _member, _stream = _bundle(path = _path)
                            if _bundle_script_path and (_bundle_script_path == _path): continue
                            destination(member = _member, stream = _stream)

    class _Result(object):
        routine = _routine

    return _Result


_private = _private()
try: routine = _private.routine
finally: del _private
