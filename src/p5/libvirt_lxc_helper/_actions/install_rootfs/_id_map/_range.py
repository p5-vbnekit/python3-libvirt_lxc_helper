#!/usr/bin/env python3
# -*- coding: utf-8 -*-

assert "__main__" != __name__


def _private():
    class _Class(object):
        @property
        def offset(self): return self.__offset

        @property
        def size(self): return self.__size

        @property
        def last(self): return self.__last

        def __init__(self, offset: int, size: int):
            super().__init__()
            assert isinstance(offset, int)
            assert 0 <= offset
            assert isinstance(size, int)
            assert 0 <= size
            assert isinstance(size, int)
            assert 0 < size
            self.__size = size
            self.__last = offset + size - 1
            self.__offset = offset

    class _Result(object):
        Class = _Class

    return _Result


_private = _private()

try: Class = _private.Class
finally: del _private


# noinspection PyArgumentList
def make(*args, **kwargs): return Class(*args, **kwargs)
