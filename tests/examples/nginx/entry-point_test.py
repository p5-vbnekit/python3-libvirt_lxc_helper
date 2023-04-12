import os
import sys
import pytest
import pathlib
import tarfile


@pytest.fixture
def local_configuration(request, tmp_path_factory):
    import p5.libvirt_lxc_helper as _target_module

    def _parse_command_line():
        _arguments = request.config.getoption("--tests.examples.nginx-source")
        assert isinstance(_arguments, list)
        for _argument in _arguments:
            assert isinstance(_argument, str)
            assert _argument
            _argument, = f"{_argument}\r\n".splitlines()
            yield pathlib.Path(_argument).resolve(strict = True)

    _sources = tuple(_parse_command_line())
    if not _sources: return None

    _temporary = tmp_path_factory.mktemp("data").resolve(strict = True)

    _destinations = _temporary / "destinations"
    os.makedirs(_destinations.as_posix(), exist_ok = False)
    _destinations = _destinations.resolve(strict = True)
    assert _destinations.is_dir()

    _working = _temporary / "working"
    assert not _working.exists()

    def _make_index_generator(start: int = 0):
        assert isinstance(start, int)

        def _routine():
            _value = start
            while True:
                yield _value
                _value += 1

        return iter(_routine())

    def _rebuild_sources():
        _index_generator = _make_index_generator()

        for _source in _sources:
            yield _source
            assert isinstance(_source, pathlib.Path)
            with tarfile.open(_source.as_posix(), "r") as _reader:
                _directory = _temporary / f"sources/{next(_index_generator)}"
                os.makedirs(_directory, exist_ok = False)
                _reader.extractall(path = _directory)
                assert 2 < len(os.listdir(_directory))
                yield _directory
            _path = _temporary / f"sources/{next(_index_generator)}"
            with tarfile.open(_path.as_posix(), "w") as _writer:
                for _item in os.listdir(_directory): _writer.add(name = _directory / _item, arcname = _item)
            yield _path

        for _name in ("", ".", "/"):
            _path = _temporary / f"sources/{next(_index_generator)}"
            with tarfile.open(_path.as_posix(), "w") as _writer: _writer.add(name = _directory, arcname = _name)
            yield _path

        for _compression in ("xz", "gz", "bz2"):
            _path = _temporary / f"sources/{next(_index_generator)}"
            with tarfile.open(_path.as_posix(), f"w|{_compression}") as _writer: _writer.add(
                name = _directory, arcname = _name
            )
            yield _path

    _sources = tuple(_rebuild_sources())

    class _Result(object):
        working = _working
        sources = _sources
        destinations = _destinations
        target_module = _target_module

    return _Result


def test(local_configuration):
    if local_configuration is None: pytest.skip("no one source provided")

    import magic
    import shlex
    import shutil
    import typing
    import subprocess
    import contextlib

    _oci_image_module = getattr(
        getattr(local_configuration.target_module, "_actions").make_rootfs,
        "_oci_image"
    )
    _make_oci_image = _oci_image_module.make
    _parse_digest = _oci_image_module.digest.parse
    _validate_manifest = _oci_image_module.meta.validate_manifest
    _parse_manifest_ref = _oci_image_module.meta.parse_manifest_ref
    del _oci_image_module

    def _make_source_handler():
        _flags = set()
        _unique_digests = dict()
        _target_module_name = local_configuration.target_module.__name__
        _script_example_base_name = f".{_target_module_name}.script.example"
        _target_module_entry_point = sys.executable, "-m", _target_module_name

        def _inspect_source(source: str):
            assert isinstance(source, str)
            _manifests = [_validate_manifest(value = _manifest) for _manifest in _make_oci_image(source = source)]
            _manifests.reverse()
            _ref = None
            _digest = None
            _last_digest = None
            for _manifest in _manifests:
                _last_digest = _parse_digest(value = _manifest["digest"]).value
                _ref = _parse_manifest_ref(manifest = _manifest)
                if _ref is None: continue
                _digest = _last_digest
                break
            return _ref, (_digest or _last_digest)

        @contextlib.contextmanager
        def _make_destination_context(key: int):
            assert isinstance(key, int)
            assert 0 <= key

            @contextlib.contextmanager
            def _make_common_context(path: pathlib.Path):
                assert isinstance(path, pathlib.Path)
                _archive_path = f"{path.as_posix()}.tar"
                yield _archive_path
                os.makedirs(path.as_posix(), exist_ok = False)
                with tarfile.open(_archive_path, "r|") as _reader: _reader.extractall(path = path.as_posix())
                _script_directory_path = os.path.join(path, _script_example_base_name)
                _script_archive_path = f"{_script_directory_path}.tar"
                os.makedirs(_script_directory_path, exist_ok = False)
                with tarfile.open(_script_archive_path, "r|") as _reader: _reader.extractall(
                    path = _script_directory_path
                )
                os.remove(_script_archive_path)
                if not (0 < key): return
                subprocess.check_call((
                    "diff", "--recursive", "--no-dereference", "--",
                    (pathlib.PurePosixPath("0/first") / _script_example_base_name).as_posix(),
                    (path.relative_to(local_configuration.destinations) / _script_example_base_name).as_posix()
                ), cwd = local_configuration.destinations, stdout = subprocess.DEVNULL)

            _key_path = local_configuration.destinations / str(key)
            _directory_name = "first"

            try: os.makedirs(_key_path.as_posix(), exist_ok = False)
            except FileExistsError: _directory_name = "next"

            _common_path = _key_path / _directory_name
            with _make_common_context(path = _common_path) as _final_path: yield _final_path

            _common_path = _common_path.as_posix()
            assert os.listdir(_common_path)

            if "first" == _directory_name: return

            subprocess.check_call(
                ("diff", "--recursive", "--no-dereference", "--", "first", "next"),
                cwd = _key_path.as_posix(), stdout = subprocess.DEVNULL
            )

            shutil.rmtree(_common_path)
            os.remove(_final_path)

        @contextlib.contextmanager
        def _make_working_directory_context():
            _path = local_configuration.working.as_posix()
            if "existing working directory" in _flags:
                assert not local_configuration.working.exists()
                yield _path
                assert not local_configuration.working.exists()
                return
            _flags.add("existing working directory")
            os.makedirs(_path, exist_ok = False)
            yield _path
            assert not os.listdir(_path), "working directory is empty after execution"
            os.rmdir(_path)

        @contextlib.contextmanager
        def _make_routine_context(digest: str):
            digest = _parse_digest(value = digest).value

            try: _key = _unique_digests[digest]
            except KeyError:
                _key = len(_unique_digests)
                _unique_digests[digest] = _key

            with (
                _make_destination_context(key = _key) as _destination,
                _make_working_directory_context() as _working_directory
            ): yield _destination, _working_directory

        def _subprocess_routine(*arguments: typing.Iterable[str]):
            arguments = tuple(arguments)
            for _argument in arguments:
                assert isinstance(_argument, str)
                assert _argument
                _argument, = f"{_argument}\r\n".splitlines()
            _command = *_target_module_entry_point, *arguments
            print(f"executing: {shlex.join(_command)}", file = sys.stderr, flush = True)
            subprocess.check_call(_command, stdin = subprocess.DEVNULL, stdout = subprocess.DEVNULL)

        def _shell_routine(source: str, digest: str):
            for _command in (
                "{command} --source={source} --destination={destination}",
                "{command} --source={source} > {destination}",
                "{command} --destination={destination} < {source}",
                "{command} < {source} > {destination}",
                "cat < {source} | {command} --destination={destination}",
                "cat < {source} | {command} > {destination}",
                "{command} --source={source} | cat > {destination}",
                "{command} < {source} | cat > {destination}",
                "cat < {source} | {command} | cat > {destination}"
            ):
                with _make_routine_context(digest = digest) as (_destination, _working_directory):
                    _command = _command.format_map(dict(command = shlex.join((
                        *_target_module_entry_point, "make-rootfs", f"--working-directory={_working_directory}"
                    )), source = shlex.quote(source), destination = shlex.quote(_destination)))
                    print(f"executing in shell: {_command}", file = sys.stderr, flush = True)
                    _command = _command.encode("utf-8")
                    assert 0 == subprocess.run(("sh", "-e"), input = _command, stdout = subprocess.DEVNULL).returncode

        def _routine(source: pathlib.Path):
            _is_directory, source = source.is_dir(), source.as_posix()
            _ref, _digest = _inspect_source(source = source)

            with _make_routine_context(digest = _digest) as (_destination, _working_directory): _subprocess_routine(
                "make-rootfs", f"--source={source}", f"--destination={_destination}",
                f"--working-directory={_working_directory}"
            )

            if not (
                ("shell" in _flags) or _is_directory or ("application/x-tar" != magic.from_file(source, mime = True))
            ):
                _flags.add("shell")
                _shell_routine(source = source, digest = _digest)

            if "digest key" not in _flags:
                _flags.add("digest key")
                with _make_routine_context(digest = _digest) as (_destination, _working_directory): _subprocess_routine(
                    "make-rootfs", f"--digest={_digest}",
                    f"--source={source}", f"--destination={_destination}",
                    f"--working-directory={_working_directory}"
                )

            if not (("ref key" in _flags) or (_ref is None)):
                _flags.add("ref key")
                with _make_routine_context(digest = _digest) as (_destination, _working_directory): _subprocess_routine(
                    "make-rootfs", f"--ref={_ref}",
                    f"--source={source}", f"--destination={_destination}",
                    f"--working-directory={_working_directory}"
                )
                with _make_routine_context(digest = _digest) as (_destination, _working_directory): _subprocess_routine(
                    "make-rootfs", f"--ref={_ref}", f"--digest={_digest}",
                    f"--source={source}", f"--destination={_destination}",
                    f"--working-directory={_working_directory}"
                )

        return _routine

    _handle_source = _make_source_handler()
    del _make_source_handler

    for _source in local_configuration.sources: _handle_source(source = _source)
