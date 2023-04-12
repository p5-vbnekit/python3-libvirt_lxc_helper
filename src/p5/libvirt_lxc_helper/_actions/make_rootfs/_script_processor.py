#!/usr/bin/env python3
# -*- coding: utf-8 -*-

if "__main__" == __name__:
    def _private():
        import os
        import sys
        import json
        import subprocess

        def _main_action_routine(payload: dict):
            assert isinstance(payload, dict)
            assert payload
            import io
            import shutil
            payload = payload.copy()
            _script = payload.pop("script")
            _source = payload.pop("source")
            _executor = payload.pop("executor")
            _directory = payload.pop("directory")
            assert isinstance(_script, list)
            assert isinstance(_source, int)
            assert isinstance(_executor, list)
            assert isinstance(_directory, str)
            assert _script and _executor and _directory
            assert 2 < _source
            try: assert not payload
            except AssertionError: raise OverflowError()
            with io.StringIO() as _chroot_request:
                print(json.dumps({"action": "chroot", "payload": _script}), file = _chroot_request, flush = True)
                _chroot_request = _chroot_request.getvalue().encode("utf-8")
            print(f"extracting rootfs to temporary directory: {_directory}", file = sys.stderr, flush = True)
            os.makedirs(_directory, exist_ok = False)
            try:
                subprocess.check_call(
                    ("tar", "--extract", "--same-permissions"), cwd = _directory, stdin = _source, stdout = sys.stderr
                )
                with os.fdopen(_source, "rb", closefd = True) as _source:
                    try: assert not _source.read(1)
                    except AssertionError: raise OverflowError()
                _chroot_request = subprocess.run(
                    _executor, cwd = _directory, input = _chroot_request, stdout = sys.stderr
                ).returncode
                assert 0 == _chroot_request
                _content = os.listdir(_directory)
                if _content:
                    _content.sort()
                    subprocess.check_call(("tar", "--create", "--same-permissions", "--", *_content), cwd = _directory)
                    return
                sys.stdout.buffer.flush()
                sys.stdout.buffer.close()
            finally: shutil.rmtree(_directory)

        def _chroot_action_routine(payload: list):
            assert isinstance(payload, list)
            assert payload
            import shlex
            _directory = os.path.realpath(".")
            os.chroot(_directory)
            for _index, payload in enumerate(payload, start = 1):
                assert isinstance(payload, dict)
                payload = payload.copy()
                _command = payload.pop("command")
                _environment = payload.pop("environment")
                try: _input = payload.pop("input")
                except KeyError: _input = None
                else: assert isinstance(_input, str)
                try: assert not payload
                except AssertionError: raise OverflowError()
                assert isinstance(_command, list)
                assert isinstance(_environment, dict)
                assert _command
                assert isinstance(_command[0], str)
                assert _command[0]
                for _item in _command: assert isinstance(_item, str)
                for _item in _environment.items():
                    assert isinstance(_item[0], str)
                    assert _item[0]
                    assert isinstance(_item[1], str)
                _options = {"env": _environment, "stdout": sys.stderr}
                if _input is None: _options["input"] = bytes()
                else: _options["input"] = _input.encode("utf-8")
                print(f"processing command #{_index}: {shlex.join(_command)}", file = sys.stderr, flush = True)
                assert 0 == subprocess.run(_command, **_options).returncode

        def _routine():
            _input = sys.stdin.readline()
            try: assert not sys.stdin.buffer.read(1)
            except AssertionError: raise OverflowError()
            assert isinstance(_input, str)
            assert _input
            _input = _input.strip()
            assert _input
            _input = json.loads(_input)
            assert isinstance(_input, dict)
            _action = _input.pop("action")
            _payload = _input.pop("payload")
            try: assert not _input
            except AssertionError: raise OverflowError()
            assert isinstance(_action, str)
            if "main" == _action: return _main_action_routine(payload = _payload)
            assert "chroot" == _action
            _chroot_action_routine(payload = _payload)

        class _Result(object):
            routine = _routine

        return _Result

    try: _private().routine()
    finally: del _private

else:
    def _private():
        import io
        import os
        import sys
        import json
        import typing
        import pathlib
        import contextlib
        import subprocess

        _executor = sys.executable, "-m", __name__

        @contextlib.contextmanager
        def _make_destination(target: typing.Optional[str]):
            if target is None:
                yield None
                return
            assert isinstance(target, str)
            assert target
            target = pathlib.Path(target).resolve()
            assert target.parent.resolve(strict = True).is_dir()
            with open(target.as_posix(), "wb") as target:
                yield target
                target.flush()

        @contextlib.contextmanager
        def _make_fifo():
            _reader, _writer = os.pipe()
            try:
                with (
                    os.fdopen(_reader, "rb", closefd = True) as _reader,
                    os.fdopen(_writer, "wb", closefd = True) as _writer
                ): yield _reader, _writer
            finally:
                if isinstance(_reader, int):
                    try: os.close(_reader)
                    finally:
                        if isinstance(_writer, int): os.close(_writer)

        @contextlib.contextmanager
        def _make(script: list, destination: typing.Optional[str], working_directory: str):
            assert isinstance(script, list)
            assert isinstance(working_directory, str)
            assert script and working_directory

            with (
                _make_fifo() as (_fifo_reader, _fifo_writer),
                _make_destination(target = destination) as destination
            ):
                with io.StringIO() as _request:
                    print(json.dumps({"action": "main", "payload": {
                        "script": script, "source": _fifo_reader.fileno(),
                        "executor": _executor, "directory": working_directory
                    }}), file = _request, flush = True)
                    _request = _request.getvalue().encode("utf-8")

                with subprocess.Popen(
                    ("unshare", "--map-auto", "--map-root-user", "--", *_executor),
                    stdin = subprocess.PIPE, stdout = destination, pass_fds = (_fifo_reader.fileno(), )
                ) as _subprocess:
                    try:
                        _subprocess.stdin.write(_request)
                        _subprocess.stdin.flush()
                        _subprocess.stdin.close()
                        _fifo_reader.close()
                        yield _fifo_writer
                        _fifo_writer.flush()
                        _fifo_writer.close()
                        _subprocess.wait()

                    finally:
                        try:
                            try:
                                if _subprocess.returncode is None:
                                    _subprocess.terminate()
                                    _subprocess.wait(timeout = 15)

                            finally:
                                if _subprocess.returncode is None: _subprocess.kill()

                        finally: assert 0 == _subprocess.returncode

        class _Result(object):
            make = _make

        return _Result

    _private = _private()
    try: make = _private.make
    finally: del _private
