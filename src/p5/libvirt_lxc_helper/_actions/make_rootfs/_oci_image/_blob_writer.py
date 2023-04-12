#!/usr/bin/env python3
# -*- coding: utf-8 -*-

assert "__main__" != __name__


def _private():
    import typing
    import hashlib

    from . import digest as _digest_module

    _Digest = _digest_module.Class
    _make_digest = _digest_module.make

    class _Class(object):
        @property
        def stream(self): return self.__stream

        @property
        def digest(self):
            if self.__digest is None: self.__digest = _make_digest(
                type = "sha256", hash = self.__hash.hexdigest()
            )
            assert isinstance(self.__digest, _Digest)
            return self.__digest

        def tell(self, *args, **kwargs): return self.__stream.tell(*args, **kwargs)

        def write(self, data: typing.Union[str, bytes]):
            if isinstance(data, str): data = data.encode("utf-8")
            assert isinstance(data, bytes)
            assert data
            _size = self.__stream.write(data)
            assert isinstance(_size, int)
            if 0 < _size:
                self.__digest = None
                self.__hash.update(data[:_size])
            else: assert 0 == _size

        def __init__(self, stream):
            super().__init__()
            _hash = hashlib.sha256()
            self.__hash = _hash
            self.__stream = stream
            self.__digest = None

    class _Result(object):
        Class = _Class

    return _Result


_private = _private()
try: Class = _private.Class
finally: del _private


# noinspection PyArgumentList
def make(*args, **kwargs): return Class(*args, **kwargs)
