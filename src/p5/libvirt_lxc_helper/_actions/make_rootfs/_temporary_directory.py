#!/usr/bin/env python3
# -*- coding: utf-8 -*-

assert "__main__" != __name__


def _private():
    import os
    import sys
    import typing
    import shutil
    import tempfile
    import traceback

    _my_prefix = ".".join(__package__.split(".")[:2])
    _my_prefix = f"{_my_prefix}.tmp."

    def _make_dirs(path: str):
        assert isinstance(path, str)
        assert path
        path = os.path.normpath(os.path.abspath(path))
        assert not os.path.exists(path)
        _collector = []
        while not os.path.exists(path):
            _collector.append(path)
            path = os.path.dirname(path)
        assert _collector
        os.makedirs(_collector[0], exist_ok = False)
        return tuple(_collector)

    class _Class(object):
        @property
        def path(self): return self.__path

        @property
        def location(self): return self.__temporary[0] if self.__temporary else None

        def __enter__(self):
            assert self.__temporary is None
            if self.__path is None: self.__temporary = tempfile.mkdtemp(prefix = _my_prefix),
            elif os.path.exists(self.__path): self.__temporary = tempfile.mkdtemp(prefix = _my_prefix, dir = self.__path),
            else: self.__temporary = _make_dirs(path = self.__path)
            return self.__temporary[0]

        def __exit__(self, exception_type, exception_instance, exception_traceback):
            _temporary = self.__temporary
            assert _temporary is not None
            self.__temporary = None
            _temporary = list(_temporary)
            assert _temporary
            try:
                shutil.rmtree(_temporary.pop(0))
                while _temporary: os.rmdir(_temporary.pop(0))
            except OSError: print(traceback.format_exc(), file = sys.stderr, flush = True)

        def __init__(self, path: typing.Optional[str]):
            super().__init__()
            if path is not None:
                assert isinstance(path, str)
                assert path
            self.__path = path
            self.__temporary = None

    class _Result(object):
        Class = _Class

    return _Result


_private = _private()
try: Class = _private.Class
finally: del _private


# noinspection PyArgumentList
def make(*args, **kwargs): return Class(*args, **kwargs)
