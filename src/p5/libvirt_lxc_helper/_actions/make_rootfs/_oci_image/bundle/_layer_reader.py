#!/usr/bin/env python3
# -*- coding: utf-8 -*-

assert "__main__" != __name__


def _private():
    import tarfile

    from ..... import _common as _common_module

    _normalize_path = _common_module.path.normalize

    def _validate_path(value: str):
        assert isinstance(value, str)
        assert value
        value, = f"{value}\r\n".splitlines()
        assert value.strip(".")
        assert value == _normalize_path(value = value, drop_root = True).as_posix()
        return value

    class _Class(object):
        @property
        def members(self): return None if self.__members is None else self.__members[1]

        def open(self, stream):
            assert stream is not None

            assert self.__stream is None
            assert self.__tarfile is None
            assert self.__members is None

            _members = set(), list()
            _tarfile = tarfile.open(mode = "r", fileobj = stream)

            try:
                for _path in _tarfile.getnames():
                    _path = _validate_path(value = _path)
                    assert _path not in _members[0]
                    _members[0].add(_path)
                    _members[1].append(_path)

                _members[1].sort()

            except BaseException:
                _tarfile.close()
                raise

            self.__stream = stream
            self.__tarfile = _tarfile
            self.__members = _members[0], tuple(_members[1])

        def close(self):
            _stream = self.__stream
            _tarfile = self.__tarfile
            _members = self.__members

            self.__stream = None
            self.__tarfile = None
            self.__members = None

            try: _members is not None
            finally:
                try:
                    assert isinstance(_tarfile, tarfile.TarFile)
                    _tarfile.close()

                finally:
                    assert _stream is not None
                    _stream.close()

        def __call__(self, path: str):
            assert self.__stream is not None
            assert self.__members is not None
            assert isinstance(self.__tarfile, tarfile.TarFile)
            assert isinstance(path, str)
            assert path in self.__members[0]
            _member = self.__tarfile.getmember(path)
            assert isinstance(_member, tarfile.TarInfo)
            _stream = self.__tarfile.extractfile(_member) if _member.isreg() else None
            return _member, _stream

        def __init__(self, stream = None):
            super().__init__()
            self.__stream = None
            self.__tarfile = None
            self.__members = None
            if stream is not None: self.open(stream)

    class _Result(object):
        Class = _Class

    return _Result


_private = _private()
try: Class = _private.Class
finally: del _private


# noinspection PyArgumentList
def make(*args, **kwargs): return Class(*args, **kwargs)
