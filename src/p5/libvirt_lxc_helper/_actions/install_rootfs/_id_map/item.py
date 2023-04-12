#!/usr/bin/env python3
# -*- coding: utf-8 -*-

assert "__main__" != __name__


def _private():
    class _Class(object):
        @property
        def container(self): return self.__container

        @property
        def host(self): return self.__host

        @property
        def size(self): return self.__size

        def __init__(self, container: int, host: int, size: int):
            super().__init__()
            assert isinstance(container, int)
            assert 0 <= container
            assert isinstance(host, int)
            assert 0 <= host
            assert isinstance(size, int)
            assert 0 < size
            self.__size = size
            self.__host = host
            self.__container = container

    class _Result(object):
        Class = _Class

    return _Result


_private = _private()

try: Class = _private.Class
finally: del _private


# noinspection PyArgumentList
def make(*args, **kwargs): return Class(*args, **kwargs)
