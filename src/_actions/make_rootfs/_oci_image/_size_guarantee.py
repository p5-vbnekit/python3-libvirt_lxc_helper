#!/usr/bin/env python3
# -*- coding: utf-8 -*-

assert "__main__" != __name__


def _private():
    import typing
    import contextlib

    class _Reader(object):
        @property
        def left(self): return self.__left

        def tell(self, *args, **kwargs): return self.__stream.tell(*args, **kwargs)

        def seek(self, *args, **kwargs):
            try: return self.__stream.seek(*args, **kwargs)
            finally: self.__finally()

        def read(self, *args, **kwargs):
            try: return self.__stream.read(*args, **kwargs)
            finally: self.__finally()

        def __init__(self, stream, size: int):
            super().__init__()
            assert isinstance(size, int)
            assert 0 < size
            _begin = stream.tell()
            self.__end = size + _begin
            self.__left = size
            self.__begin = _begin
            self.__stream = stream

        def __finally(self):
            _position = self.__stream.tell()

            try:
                assert self.__begin <= _position
                assert self.__end >= _position
            finally:
                _position = max(self.__begin, min(self.__end, _position))
                self.__left = min(self.__left, self.__end - _position)

    @contextlib.contextmanager
    def _data_wrapper(source: typing.Union[str, bytes], limit: typing.Optional[int], exact: typing.Optional[int]):
        assert isinstance(source, (str, bytes))
        _size = len(source)
        if exact is None:
            assert limit is not None
            assert isinstance(limit, int)
            assert 0 < limit
            assert _size <= limit
        else:
            assert limit is None
            assert isinstance(exact, int)
            assert 0 < exact
            assert _size == exact
        yield source

    @contextlib.contextmanager
    def _stream_wrapper(source, limit: typing.Optional[int], exact: typing.Optional[int]):
        if exact is None: _helper = _Reader(stream = source, size = limit)
        else:
            assert limit is None
            _helper = _Reader(stream = source, size = exact)

        class _Class(object):
            @staticmethod
            def tell(*args, **kwargs): return _helper.tell(*args, **kwargs)

            @staticmethod
            def seek(*args, **kwargs): return _helper.seek(*args, **kwargs)

            @staticmethod
            def read(*args, **kwargs): return _helper.read(*args, **kwargs)

        yield _Class()
        assert (exact is None) or (0 == _helper.left)

    def _make(source: typing.Union[str, bytes, object], limit: int = None, exact: int = None):
        if isinstance(source, (str, bytes)): return _data_wrapper(source = source, limit = limit, exact = exact)
        return _stream_wrapper(source = source, limit = limit, exact = exact)

    class _Result(object):
        make = _make

    return _Result


_private = _private()
try: make = _private.make
finally: del _private
