#!/usr/bin/env python3
# -*- coding: utf-8 -*-

assert "__main__" != __name__


def _private():
    import json
    import typing
    import contextlib

    from . import meta as _meta_module
    from . import _fake as _fake_module
    from . import bundle as _bundle_module
    from . import digest as _digest_module
    from . import _source_reader as _source_reader_module
    from . import _size_guarantee as _size_guarantee_module

    _Digest = _digest_module.Class
    _SourceReader = _source_reader_module.Class

    _make_bundle = _bundle_module.make
    _parse_digest = _digest_module.parse
    _parse_manifest = _meta_module.parse_manifest
    _meta_blob_limit = _meta_module.blob_limit
    _make_source_reader = _source_reader_module.make
    _fake_module_routine = _fake_module.routine
    _make_size_guarantee = _size_guarantee_module.make

    def _read_index(source: _SourceReader):
        assert isinstance(source, _SourceReader)
        with source.open("index.json") as _stream:
            with _make_size_guarantee(
                source = _stream, limit = _meta_blob_limit
            ) as _guarantee: _data = json.load(_guarantee)
        assert isinstance(_data, dict)
        _data = _data["schemaVersion"], _data["manifests"]
        assert isinstance(_data[0], int)
        assert 2 == _data[0]
        _data = _data[1]
        assert isinstance(_data, list)
        assert _data
        _collector = list(), dict()
        for _data in _data:
            _data = _parse_manifest(value = _data)
            _digest = _data["digest"]
            assert _digest not in _collector[1]
            _collector[0].append(_data)
            _collector[1][_digest] = _data
        return tuple(_collector[0]), _collector[1]

    class _Class(object):
        @property
        def source(self): return self.__source.source

        def __iter__(self):
            for _manifest in self.__manifests[0]: yield json.loads(json.dumps(_manifest))

        @contextlib.contextmanager
        def open_bundle(self, digest: typing.Union[str, _Digest]):
            if isinstance(digest, _Digest): digest = digest.value
            else: digest = _parse_digest(digest).value
            with _make_bundle(source = self.__source).open(
                manifest = self.__manifests[1][digest]
            ) as _bundle: yield _bundle

        def install_fake(self, digest: typing.Union[str, _Digest], destination: str):
            if isinstance(digest, _Digest): digest = digest.value
            else: digest = _parse_digest(digest).value
            return _fake_module_routine(
                manifest = self.__manifests[1][digest], source = self.__source, destination = destination
            )

        def __init__(self, source: str):
            super().__init__()
            source = _make_source_reader(source = source)
            _manifests = _read_index(source = source)
            self.__source = source
            self.__manifests = _manifests

    class _Result(object):
        Class = _Class

    return _Result


_private = _private()
try: Class = _private.Class
finally: del _private


# noinspection PyArgumentList
def make(*args, **kwargs): return Class(*args, **kwargs)
