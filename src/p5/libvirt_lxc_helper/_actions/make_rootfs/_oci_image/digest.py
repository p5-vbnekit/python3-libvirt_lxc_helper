#!/usr/bin/env python3
# -*- coding: utf-8 -*-

assert "__main__" != __name__


def _private():
    import re
    import pathlib

    _invalid_pattern = re.compile("[^a-z0-9]")

    def _validate_part(value: str):
        assert isinstance(value, str)
        assert value
        assert _invalid_pattern.match(value) is None

    class _Class(object):
        @property
        def type(self): return self.__type

        @property
        def hash(self): return self.__hash

        @property
        def path(self): return self.__path

        @property
        def value(self): return self.__value

        @classmethod
        def parse(cls, value: str):
            assert isinstance(value, str)
            _type, _hash = value.split(":")
            return cls(type = _type, hash = _hash)

        # noinspection PyShadowingBuiltins
        def __init__(self, type: str, hash: str):
            super().__init__()
            _validate_part(value = type)
            _validate_part(value = hash)
            _path = pathlib.PurePosixPath(type, hash)
            assert not _path.is_absolute()
            _path = pathlib.PurePosixPath("blobs") / _path
            _path = _path.as_posix()
            _value = f"{type}:{hash}"
            self.__type = type
            self.__hash = hash
            self.__path = _path
            self.__value = _value

    def _parse(*args, **kwargs): return _Class.parse(*args, **kwargs)

    class _Result(object):
        Class = _Class
        parse = _parse

    return _Result


_private = _private()
try:
    Class = _private.Class
    parse = _private.parse
finally: del _private


# noinspection PyArgumentList
def make(*args, **kwargs): return Class(*args, **kwargs)
