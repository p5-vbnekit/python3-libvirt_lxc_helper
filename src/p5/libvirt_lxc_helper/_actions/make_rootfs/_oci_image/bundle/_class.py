#!/usr/bin/env python3
# -*- coding: utf-8 -*-

assert "__main__" != __name__


def _private():
    import os
    import json
    import typing
    import tarfile
    import contextlib

    from . import _script as _script_module
    from . import _layer_reader as _layer_reader_module

    from .. import meta as _meta_module
    from .. import digest as _digest_module
    from .. import _source_reader as _source_reader_module
    from .. import _size_guarantee as _size_guarantee_module

    from ..... import _common as _common_module

    _meta_limit = _meta_module.blob_limit
    _normalize_path = _common_module.path.normalize
    _parse_meta = _meta_module.parse_bundle
    _parse_script = _script_module.parse
    _parse_manifest = _meta_module.parse_manifest
    _parse_blob_digest = _digest_module.parse
    _make_layer_reader = _layer_reader_module.make
    _make_size_guarantee = _size_guarantee_module.make

    _LayerReader = _layer_reader_module.Class
    _SourceReader = _source_reader_module.Class

    @contextlib.contextmanager
    def _open_blob_reader(digest: str, source: _SourceReader, size: int):
        assert isinstance(source, _SourceReader)
        assert isinstance(size, int)
        _path = _parse_blob_digest(value = digest).path
        with source.open(_path) as _stream:
            with _make_size_guarantee(source = _stream, exact = size) as _guarantee: yield _guarantee

    def _parse_config_environment(value: typing.Iterable[str]):
        _collector = dict()
        for value in value:
            assert isinstance(value, str)
            assert value
            value = value.split("=")
            value = value[0], value[1:]
            assert value[0]
            assert value[0].strip() == value[0]
            assert value[0] not in _collector
            assert value[1]
            _collector.update({value[0]: "".join(value[1])})
        return _collector

    def _parse_config_script_label(value: dict):
        assert isinstance(value, dict)
        try: value = value["p5.libvirt_lxc_helper.script"]
        except KeyError: return None
        assert isinstance(value, str)
        if not value: return None
        value = _normalize_path(value = value, drop_root = True).as_posix()
        assert value.strip(".")
        return value

    def _parse_config(value: dict):
        assert isinstance(value, dict)
        assert value
        try: value = value["config"]
        except KeyError: return None, None
        try: _environment = value["Env"]
        except KeyError: _environment = None
        else:
            assert isinstance(_environment, list)
            _environment = _parse_config_environment(value = _environment)
        try: _script = value["Labels"]
        except KeyError: _script = None
        else: _script = _parse_config_script_label(value = _script)
        return _environment, _script

    def _close_layers(layers: typing.Iterable[_LayerReader]):
        layers = list(layers)

        def _routine():
            while layers:
                _layer = layers.pop()
                try: _layer.close()
                finally: _routine()

        _routine()

    def _open_layers(meta: typing.Iterable[dict], source: _SourceReader):
        assert isinstance(source, _SourceReader)
        _collector = [list(), dict()]

        try:
            for _layer in meta:
                assert isinstance(_layer, dict)
                _media = _layer["mediaType"]
                assert isinstance(_media, str)
                assert "application/vnd.oci.image.layer.v1.tar+gzip" == _media
                _size = _layer["size"]
                assert isinstance(_size, int)
                assert 0 < _size
                _path = _parse_blob_digest(value = _layer["digest"]).path
                _reader = source.open(_path)
                try:
                    assert _size == _reader.seek(0, os.SEEK_END)
                    assert _size == _reader.tell()
                    assert 0 == _reader.seek(0, os.SEEK_SET)
                    assert 0 == _reader.tell()
                    _reader = _make_layer_reader(stream = _reader)
                    _collector[1].update({_member: _reader for _member in _reader.members})
                except BaseException:
                    _reader.close()
                    raise
                _actual = set(_collector[1].values())
                _collector[0] = [_layer for _layer in _collector[0] if _layer in _actual]

        finally: _close_layers(layers = _collector[0])

        return _collector[1]

    def _rebuild_environment(parent: dict, source: dict):
        assert isinstance(parent, dict)
        assert isinstance(source, dict)

        source = source.copy()
        _inherit = source.pop("inherit")
        _payload = source.pop("payload")

        try: assert not source
        except AssertionError: raise ValueError(source.keys())

        assert isinstance(_inherit, bool)
        assert isinstance(_payload, dict)

        for _key, _value in parent.items():
            assert isinstance(_key, str)
            assert _key
            assert isinstance(_value, str)

        _collector = dict()

        if _inherit:
            def _iteration(key: str, value: typing.Union[bool, str]):
                if value is False: _collector.pop(key)
                elif isinstance(value, str): _collector[key] = value
                else: assert value is True
            _collector.update(parent)
        else:
            def _iteration(key: str, value: typing.Union[bool, str]):
                if value is True: _collector[key] = parent[key]
                elif isinstance(value, str): _collector[key] = value
                else: assert value is False

        for _key, _value in _payload.items():
            assert isinstance(_key, str)
            assert _key
            _iteration(key = _key, value = _value)

        return _collector

    class _Context(object):
        def __init__(self):
            super().__init__()
            self.layers = None
            self.script = None
            self.config = None
            self.manifest = None

    class _Class(object):
        @property
        def script(self):
            return None if self.__context is None else json.loads(json.dumps(self.__context.script))

        @property
        def config(self):
            return None if self.__context is None else json.loads(json.dumps(self.__context.config))

        @property
        def manifest(self):
            return None if self.__context is None else json.loads(json.dumps(self.__context.manifest))

        def open(self, manifest: typing.Union[str, dict]):
            _context = _Context()
            _context.manifest = _parse_manifest(value = manifest)
            _size = _context.manifest["size"]
            assert isinstance(_size, int)
            assert 0 < _size
            assert _meta_limit >= _size
            assert self.__context is None
            with _open_blob_reader(
                digest = _context.manifest["digest"], source = self.__source, size = _context.manifest["size"]
            ) as _meta: _meta = json.load(_meta)
            _meta = _parse_meta(value = _meta)
            _context.layers = _meta["layers"]
            assert _context.layers
            _context.config = _meta["config"]
            assert _context.config
            with _open_blob_reader(
                digest = _context.config["digest"], source = self.__source, size = _context.config["size"]
            ) as _context.config: _context.config = json.load(_context.config)
            _environment, _script_path = _parse_config(value = _context.config)
            _context.layers = _open_layers(meta = _context.layers, source = self.__source)
            if _script_path is not None:
                try:
                    _info, _context.script = _context.layers[_script_path](_script_path)
                    assert isinstance(_info, tarfile.TarInfo)
                    assert _info.isreg()
                    assert _context.script is not None
                    with _context.script as _context.script: _context.script = _context.script.read()
                    _context.script = _parse_script(_context.script)
                    if _context.script.pop("exclude"): _context.script["path"] = _script_path
                    _environment = _rebuild_environment(
                        parent = _environment, source = _context.script.pop("environment")
                    )
                    for _body_item in _context.script["body"]: _body_item["environment"] = _rebuild_environment(
                        parent = _environment, source = _body_item.pop("environment")
                    )

                except BaseException:
                    _close_layers(layers = tuple(set(_context.layers.values())))
                    raise
            self.__context = _context
            return self

        def close(self):
            _context = self.__context
            assert isinstance(_context, _Context)
            self.__context = None
            _close_layers(layers = tuple(set(_context.layers.values())))

        def __call__(self, path: str):
            assert isinstance(path, str)
            assert path
            path = _normalize_path(value = path, drop_root = True)
            assert path.parts[0].strip(".")
            path = path.as_posix()
            assert isinstance(self.__context, _Context)
            return self.__context.layers[path](path = path)

        def __enter__(self): return self

        def __exit__(self, exception_type, exception_instance, exception_traceback):
            _context = self.__context
            if _context is None: return
            self.__context = None
            _close_layers(layers = tuple(set(_context.layers.values())))

        def __init__(self, source: _SourceReader):
            super().__init__()
            assert isinstance(source, _SourceReader)
            self.__source = source
            self.__context = None

    class _Result(object):
        Class = _Class

    return _Result


_private = _private()
try: Class = _private.Class
finally: del _private


# noinspection PyArgumentList
def make(*args, **kwargs): return Class(*args, **kwargs)
