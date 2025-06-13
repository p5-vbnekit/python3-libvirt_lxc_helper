#!/usr/bin/env python3
# -*- coding: utf-8 -*-

assert "__main__" != __name__


def _private():
    import sys
    import typing
    import pathlib
    import tarfile

    from . import _stream_inspector as _stream_inspector_module
    from .. import path as _path_module

    _normalize_path = _path_module.normalize
    _make_stream_inspector = _stream_inspector_module.make

    def _make_mapping(tar: tarfile.TarFile):
        assert isinstance(tar, tarfile.TarFile)
        _collector = dict()
        for _name in tar.getnames():
            assert isinstance(_name, str)
            assert _name
            _normalized = _normalize_path(value = _name, drop_root = True).as_posix()
            if not _normalized.strip("."): continue
            if _name == _normalized: continue
            assert _normalized not in _collector
            _collector[_normalized] = _name
        return _collector

    class _Class(object):
        @property
        def state(self): return self.__tarfile is not None

        @property
        def magic(self): return self.__magic

        @property
        def source(self): return self.__source

        @property
        def seekable(self): return self.__seekable

        def open(self):
            assert self.__tarfile is None

            _magic = None
            _source = self.__source
            _stream = None
            _tarfile = None
            _seekable = False

            try:
                if _source is None: _stream = sys.stdin.buffer
                elif isinstance(_source, str):
                    assert _source
                    _source = _normalize_path(value = pathlib.Path(_source).resolve(strict = True)).as_posix()
                    _stream = open(_source, "rb")
                else: _stream = self.__source
                _inspector = _make_stream_inspector(stream = _stream)
                _seekable = _inspector.seekable
                if _seekable:
                    _magic = _inspector.magic
                    _tarfile = tarfile.open(mode = "r", fileobj = _stream)
                else: _tarfile = tarfile.open(mode = "r|", fileobj = _stream)

            except BaseException:
                if _stream is not None:
                    try:
                        if _tarfile is not None: _tarfile.close()
                    finally:
                        if isinstance(self.__source, str): _stream.close()
                raise

            self.__magic = _magic
            self.__stream = _stream
            self.__tarfile = _tarfile
            self.__seekable = _seekable

        def close(self):
            _stream, _tarfile = self.__stream, self.__tarfile

            self.__magic = None
            self.__stream = None
            self.__tarfile = None
            self.__mapping = None
            self.__seekable = None

            try:
                assert isinstance(_tarfile, tarfile.TarFile)
                _tarfile.close()
            finally:
                assert _stream is not None
                if isinstance(self.__source, str): _stream.close()

        def __iter__(self):
            assert isinstance(self.__tarfile, tarfile.TarFile)
            for _member in self.__tarfile:
                _path = _member.name
                if not _path: continue
                _path = _normalize_path(value = _path, drop_root = True).as_posix()
                if not _path.strip("."): continue
                if not _member.isreg():
                    _member.name = _member.path = _path
                    yield _member, None
                    continue
                with self.__tarfile.extractfile(_member) as _stream:
                    _member.name = _member.path = _path
                    yield _member, _stream

        def __call__(self, path: str):
            assert isinstance(path, str)
            assert path
            path = _normalize_path(value = path, drop_root = True).as_posix()
            assert path.strip(".")
            assert isinstance(self.__tarfile, tarfile.TarFile)
            try: _stream = self.__tarfile.extractfile(path)
            except KeyError:
                if self.__mapping is None: self.__mapping = _make_mapping(tar = self.__tarfile)
                _stream = self.__tarfile.extractfile(self.__mapping[path])
            assert _stream is not None
            return _stream

        def __enter__(self): return self

        def __exit__(self, exception_type, exception_instance, exception_traceback):
            _stream, _tarfile = self.__stream, self.__tarfile

            self.__magic = None
            self.__stream = None
            self.__tarfile = None
            self.__mapping = None
            self.__seekable = None

            try:
                if _tarfile is not None: _tarfile.close()
            finally:
                if (_stream is not None) and isinstance(self.__source, str): _stream.close()

        def __init__(self, source: typing.Union[str, typing.IO[bytes]] = None):
            super().__init__()
            self.__magic = None
            self.__stream = None
            self.__source = source
            self.__tarfile = None
            self.__mapping = None
            self.__seekable = None

    class _Result(object):
        Class = _Class

    return _Result


_private = _private()
try: Class = _private.Class
finally: del _private


# noinspection PyArgumentList
def make(*args, **kwargs): return Class(*args, **kwargs)
