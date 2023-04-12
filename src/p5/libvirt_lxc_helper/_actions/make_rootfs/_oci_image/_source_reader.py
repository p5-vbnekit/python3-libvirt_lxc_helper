#!/usr/bin/env python3
# -*- coding: utf-8 -*-

assert "__main__" != __name__


def _private():
    import os
    import typing
    import weakref
    import pathlib

    from .... import _common as _common_module

    _TarReader = _common_module.tar.Reader

    _normalize_path = _common_module.path.normalize
    _make_tar_reader = _common_module.tar.reader.make

    def _validate_path(value: str):
        assert isinstance(value, str)
        assert value.strip(".")
        assert value == _normalize_path(value = value, drop_root = True).as_posix()
        return value

    class _BackEnd(object):
        @staticmethod
        def open(path: str):
            _validate_path(value = path)
            raise NotImplementedError()

        def __init__(self): super().__init__()

    class _DirectoryBackEnd(_BackEnd):
        def open(self, path: str): return open(os.path.join(self.__source, _validate_path(value = path)), "rb")

        def __init__(self, source: str):
            super().__init__()
            assert isinstance(source, str)
            assert os.path.isdir(source)
            self.__source = source

    class _TarBackEnd(_BackEnd):
        def open(self, path: str):
            if self.__references is None: return self.__source(path = path)
            if 0 == self.__references: self.__source.open()
            self.__references += 1
            try:
                _stream = self.__source(path = path)
                assert _stream is not None
                weakref.finalize(_stream, self.__reference_handler)
                return _stream
            except BaseException:
                self.__reference_handler()
                raise

        def __reference_handler(self):
            assert 0 < self.__references
            self.__references -= 1
            if 0 < self.__references: return
            self.__source.close()

        def __init__(self, source: _TarReader, managed: bool):
            super().__init__()
            assert isinstance(source, _TarReader)
            assert isinstance(managed, bool)
            self.__source = source
            self.__references = 0 if managed else None

    class _Class(object):
        @property
        def source(self): return self.__source

        def open(self, path: str): return self.__back_end.open(path = path)

        def __init__(self, source: typing.Union[str, typing.IO[bytes], _TarReader]):
            super().__init__()
            if isinstance(source, str):
                assert source
                source = pathlib.Path(source).resolve(strict = True)
                if source.is_dir(): _back_end = _DirectoryBackEnd(source = source.as_posix())
                else: _back_end = _TarBackEnd(source = _make_tar_reader(source = source.as_posix()), managed = True)
            elif isinstance(source, _TarReader): _back_end = _TarBackEnd(source = source, managed = False)
            else: _back_end = _TarBackEnd(source = _make_tar_reader(source), managed = False)
            self.__source = source
            self.__back_end = _back_end

    class _Result(object):
        Class = _Class

    return _Result


_private = _private()
try: Class = _private.Class
finally: del _private


# noinspection PyArgumentList
def make(*args, **kwargs): return Class(*args, **kwargs)
