#!/usr/bin/env python3
# -*- coding: utf-8 -*-

assert "__main__" != __name__


def _private():
    import os
    import sys
    import typing
    import tarfile
    import pathlib

    from . import _stream_inspector as _stream_inspector_module
    from .. import path as _path_module

    _normalize_path = _path_module.normalize
    _make_stream_inspector = _stream_inspector_module.make

    _destination_type_hint = typing.Union[str, typing.IO[bytes]]

    def _write_data(data: bytes, stream: typing.IO[bytes]):
        assert isinstance(data, bytes)
        assert data
        _size = stream.write(data)
        if _size is None: _size = len(data)
        else:
            assert isinstance(_size, int)
            assert _size == len(data)
        return _size

    class _SeekableStreamWrapper(object):
        def tell(self): return self.__stream.tell()

        def flush(self): return self.__stream.flush()

        @staticmethod
        def seekable(): return True

        def seek(self, offset: int, whence: int = os.SEEK_SET):
            assert isinstance(offset, int)
            assert isinstance(whence, int)
            if os.SEEK_SET == whence: assert 0 <= offset
            else: assert whence in {os.SEEK_CUR, os.SEEK_END}
            return self.__stream.seek(offset, whence)

        def write(self, data: bytes): return _write_data(data = data, stream = self.__stream)

        def __init__(self, stream: typing.IO[bytes]):
            super().__init__()
            self.__stream = stream

    class _NonSeekableStreamWrapper(object):
        def tell(self): return self.__offset

        def flush(self): return self.__stream.flush()

        @staticmethod
        def seekable(): return False

        def write(self, data: bytes):
            _size = _write_data(data = data, stream = self.__stream)
            self.__offset += _size
            return _size

        def __init__(self, stream: typing.IO[bytes]):
            super().__init__()
            self.__offset = 0
            self.__stream = stream

    def _validate_member_path(value: str):
        assert isinstance(value, str)
        assert value.strip(".")
        assert value == _normalize_path(value = value, drop_root = True).as_posix()
        return value

    def _open(destination: typing.Optional[_destination_type_hint]):
        _stream, _tarfile = None, None
        try:
            if isinstance(destination, str):
                destination, = f"{destination}\r\n".splitlines()
                destination = pathlib.Path(destination).resolve().as_posix()
                _stream = open(destination, "wb")
            else: _stream = sys.stdout.buffer if destination is None else destination
            _inspector = _make_stream_inspector(stream = _stream)
            _wrapper = _SeekableStreamWrapper if _inspector.seekable else _NonSeekableStreamWrapper
            _wrapper = typing.cast(typing.IO[bytes], _wrapper(stream = _stream))
            _tarfile = tarfile.open(mode = "w", fileobj = _wrapper)
        except BaseException:
            try:
                if _tarfile is not None: _tarfile.close()
            finally:
                if (_stream is not None) and isinstance(destination, str): _stream.close()
            raise
        return _stream, _tarfile

    class _Class(object):
        @property
        def destination(self): return self.__destination

        def open(self):
            assert self.__stream is None
            self.__stream, self.__tarfile = _open(destination = self.__destination)

        def close(self):
            _stream, _tarfile = self.__stream, self.__tarfile

            self.__stream = None
            self.__tarfile = None

            try:
                assert isinstance(_tarfile, tarfile.TarFile)
                _tarfile.close()
            finally:
                assert _stream is not None
                if isinstance(self.__destination, str): _stream.close()

        def __call__(self, member: tarfile.TarInfo, stream: typing.Optional[typing.IO[bytes]]):
            assert isinstance(member, tarfile.TarInfo)
            if member.isreg(): assert stream is not None
            else: assert stream is None
            _dictionary = dict(member.get_info())
            _path = _dictionary.pop("name")
            if tarfile.DIRTYPE == member.type: _path = _path.rstrip("/")
            member = tarfile.TarInfo(name = _validate_member_path(value = _path))
            for _key, _value in _dictionary.items(): setattr(member, _key, _value)
            if 0 == member.uid: member.uname = "root"
            if 0 == member.gid: member.gname = "root"
            assert isinstance(self.__tarfile, tarfile.TarFile)
            self.__tarfile.addfile(member, stream)

        def __enter__(self): return self

        def __exit__(self, exception_type, exception_instance, exception_traceback):
            _stream, _tarfile = self.__stream, self.__tarfile

            self.__stream = None
            self.__tarfile = None

            try:
                if _tarfile is not None: _tarfile.close()
            finally:
                if (_stream is not None) and isinstance(self.__destination, str): _stream.close()

        def __init__(self, destination: _destination_type_hint = None):
            super().__init__()
            assert (destination is None) or destination
            self.__stream = None
            self.__tarfile = None
            self.__destination = destination

    class _Result(object):
        Class = _Class

    return _Result


_private = _private()
try: Class = _private.Class
finally: del _private


# noinspection PyArgumentList
def make(*args, **kwargs): return Class(*args, **kwargs)
