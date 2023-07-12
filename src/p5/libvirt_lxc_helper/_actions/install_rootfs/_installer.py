#!/usr/bin/env python3
# -*- coding: utf-8 -*-

assert "__main__" != __name__


def _private():
    import os
    import sys
    import stat
    import typing
    import tarfile
    import pathlib
    import asyncio
    import traceback
    import contextlib

    from . import _id_map as _id_map_module

    from ... import _common as _common_module

    _IdMap = _id_map_module.Class
    _Asynchronizer = _common_module.Asynchronizer

    _normalize_path = _common_module.path.normalize
    _make_tar_reader = _common_module.tar.reader.make
    _make_tar_writer = _common_module.tar.writer.make

    @contextlib.contextmanager
    def _prepare_source(path: typing.Optional[str]):
        if path is None:
            yield None
            return

        assert isinstance(path, str)
        assert path
        path, = f"{path}\r\n".splitlines()
        path = pathlib.Path(path).resolve(strict = True).as_posix()

        with open(path, mode = "rb") as _stream: yield _stream

    def _prepare_destination(path: str, dry: bool):
        assert isinstance(path, str)
        assert isinstance(dry, bool)

        assert path
        path, = f"{path}\r\n".splitlines()
        path = pathlib.Path(path).resolve().as_posix()

        if dry:
            try: assert not os.listdir(path), f"directory is not empty: {path}"
            except AssertionError:
                print(traceback.format_exc(), file = sys.stderr, flush = True)
                pass
        else:
            try: os.makedirs(path, exist_ok = False)
            except FileExistsError: assert not os.listdir(path), f"directory is not empty: {path}"

        return path

    @contextlib.contextmanager
    def _make_fifo():
        _reader, _writer = os.pipe()

        try:
            with (
                os.fdopen(_reader, mode = "rb", closefd = True) as _reader,
                os.fdopen(_writer, mode = "wb", closefd = True) as _writer
            ): yield _reader, _writer

        finally:
            if isinstance(_reader, int):
                try: os.close(_reader)
                finally:
                    if isinstance(_writer, int): os.close(_writer)

    async def _remap_coroutine(
        source: typing.Optional[typing.IO[bytes]], destination: typing.IO[bytes],
        id_map: _IdMap, asynchronizer: _Asynchronizer
    ):
        assert isinstance(id_map, _IdMap)
        assert isinstance(asynchronizer, _Asynchronizer)

        if source is None: source = sys.stdin.buffer

        _loop = asyncio.get_running_loop()
        assert isinstance(_loop, asyncio.AbstractEventLoop)

        _descriptor = await asynchronizer(source.fileno)
        assert isinstance(_descriptor, int)
        assert 0 <= _descriptor

        @contextlib.asynccontextmanager
        async def _wrap_source():
            def _is_possible():
                _mode = os.fstat(_descriptor).st_mode
                return stat.S_ISFIFO(_mode) or stat.S_ISSOCK(_mode) or stat.S_ISCHR(_mode)

            if not await asynchronizer(_is_possible):
                yield source
                return

            _asynchronous_reader = asyncio.StreamReader(loop = _loop)

            with os.fdopen(_descriptor, mode = "rb", closefd = False) as _asynchronous_stream:
                await _loop.connect_read_pipe(
                    lambda: asyncio.StreamReaderProtocol(_asynchronous_reader),
                    pipe = _asynchronous_stream
                )

                try:
                    async def _asynchronous_read(size: int):
                        assert isinstance(size, int)
                        assert (-1 == size) or (0 < size)
                        return await _asynchronous_reader.read(size)

                    class _Wrapper(object):
                        @staticmethod
                        def read(size: int): return asyncio.run_coroutine_threadsafe(
                            _asynchronous_read(size = size), loop = _loop
                        ).result()

                        @staticmethod
                        def seekable(): return False

                    yield _Wrapper()
                    assert _asynchronous_reader.at_eof()

                finally: await asynchronizer(_asynchronous_reader.feed_eof)

        def _transform_member(member: tarfile.TarInfo):
            assert isinstance(member, tarfile.TarInfo)
            _attributes = dict(member.get_info())
            _path = _normalize_path(_attributes.pop("name"), drop_root = True).as_posix()
            if member.isdir(): _path = _path.rstrip("/")
            if not _path.strip("."): return
            member = tarfile.TarInfo(name = _path)
            for _key, _value in _attributes.items(): setattr(member, _key, _value)
            _uid, _gid = member.uid, member.gid
            if 0 == _uid: member.uname = "root"
            if 0 == _gid: member.gname = "root"
            try: _uid = id_map.user(value = _uid)
            except KeyError: pass
            else: member.uid = _uid
            try: _gid = id_map.group(value = _gid)
            except KeyError: pass
            else: member.gid = _gid
            return member

        async with _wrap_source() as source:
            async with (
                asynchronizer(await asynchronizer(lambda: _make_tar_reader(source = source))) as _reader,
                asynchronizer(await asynchronizer(lambda: _make_tar_writer(destination = destination))) as _writer
            ):
                await asynchronizer(_reader.open)
                await asynchronizer(_writer.open)
                async for _member, _stream in asynchronizer(_reader):
                    _member = await asynchronizer(lambda: _transform_member(member = _member))
                    await asynchronizer(lambda: _writer(member = _member, stream = _stream))

    @contextlib.asynccontextmanager
    async def _make_tar_subprocess(dry: bool, source: typing.Optional[typing.IO[bytes]], destination: str):
        assert isinstance(dry, bool)
        assert isinstance(destination, str)
        assert destination

        if dry: _command = "tar", "--list", "--verbose", "--numeric-owner"
        else: _command = "tar", "--extract", "--same-owner", "--numeric-owner", "--same-permissions"

        _subprocess = await asyncio.create_subprocess_exec(
            *_command, cwd = destination, stdin = source, stdout = sys.stderr
        )

        try:
            # noinspection PyShadowingNames
            async def _coroutine():
                await _subprocess.wait()
                _exit_code = _subprocess.returncode
                assert isinstance(_exit_code, int)
                assert 0 == _exit_code
            yield _coroutine

        finally:
            if _subprocess.returncode is None:
                _subprocess.terminate()
                try: await asyncio.wait_for(_subprocess.wait(), timeout = +5.0e+0)
                finally:
                    if _subprocess.returncode is None:
                        try: _subprocess.kill()
                        except OSError: pass

    async def _coroutine(
        dry: bool,
        source: typing.Optional[str],
        destination: str,
        id_map: typing.Optional[_IdMap],
        asynchronizer: _Asynchronizer
    ):
        assert isinstance(dry, bool)

        assert isinstance(asynchronizer, _Asynchronizer)
        async with asynchronizer(_prepare_source(path = source)) as source:
            destination = await asynchronizer(lambda: _prepare_destination(path = destination, dry = dry))

            if source is None:
                async def _close_stdin():
                    def _routine():
                        _descriptor = sys.stdin.buffer.fileno()
                        sys.stdin.close()
                        sys.stdin.buffer.close()
                        os.close(_descriptor)
                    await asynchronizer(_routine)

                _source_name = "stdin"

            else: _source_name = source.name

            _dry_prefix = "dry mode:" if dry else "extracting: "
            print(f"{_dry_prefix} {_source_name} => {destination}", file = sys.stderr, flush = True)

            if id_map is None:
                async with _make_tar_subprocess(
                    dry = dry, source = source, destination = destination
                ) as _tar_subprocess:
                    if source is None: await _close_stdin()
                    await _tar_subprocess()
                    return

            assert isinstance(id_map, _IdMap)

            async with asynchronizer(_make_fifo()) as (_fifo_reader, _fifo_writer):
                async with _make_tar_subprocess(
                    dry = dry, source = _fifo_reader, destination = destination
                ) as _tar_subprocess:
                    await asynchronizer(_fifo_reader.close)
                    await _remap_coroutine(
                        source = source, destination = _fifo_writer,
                        id_map = id_map, asynchronizer = asynchronizer
                    )
                    if source is None: await _close_stdin()
                    await asynchronizer(_fifo_writer.close)
                    await _tar_subprocess()

    def _spawn(*args, **kwargs): return asyncio.create_task(_coroutine(*args, **kwargs))

    class _Result(object):
        spawn = _spawn

    return _Result


_private = _private()
try: spawn = _private.spawn
finally: del _private
