#!/usr/bin/env python3
# -*- coding: utf-8 -*-

assert "__main__" != __name__


def _private():
    import os
    import magic
    import typing

    def _is_seekable(stream: typing.IO[bytes]):
        try: _seekable = stream.seekable
        except AttributeError: return False
        if not (callable(_seekable) and stream.seekable()): return False
        try: _tell, _seek = stream.tell, stream.seek
        except AttributeError: return False
        if not (callable(_tell) and callable(_seek)): return False
        try: _tell = stream.tell()
        except OSError: return False
        try: _seek = stream.seek(_tell, os.SEEK_SET)
        except OSError: return False
        assert 0 == _seek
        assert _tell == stream.tell()
        return True

    def _read_magic(stream: typing.IO[bytes]):
        _offset = stream.tell()
        assert isinstance(_offset, int)
        assert 0 <= _offset
        assert 0 == stream.seek(0)
        _magic = magic.from_buffer(stream.read(2048), mime = True)
        assert _offset == stream.seek(_offset)
        assert _offset == stream.tell()
        assert isinstance(_magic, str)
        assert _magic.startswith("application/")
        return _magic

    class _Class(object):
        @property
        def stream(self): return self.__stream

        @property
        def magic(self):
            if self.__magic is None:
                assert self.seekable
                self.__magic = _read_magic(stream = self.__stream)
            return self.__magic

        @property
        def seekable(self):
            if self.__seekable is None: self.__seekable = _is_seekable(stream = self.__stream)
            return self.__seekable

        def __init__(self, stream: typing.IO[bytes]):
            super().__init__()
            self.__magic = None
            self.__stream = stream
            self.__seekable = None

    class _Result(object):
        Class = _Class

    return _Result


_private = _private()
try: Class = _private.Class
finally: del _private


# noinspection PyArgumentList
def make(*args, **kwargs): return Class(*args, **kwargs)
