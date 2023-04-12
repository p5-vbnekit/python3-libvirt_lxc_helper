#!/usr/bin/env python3
# -*- coding: utf-8 -*-

assert "__main__" != __name__


def _private():
    import os
    import json
    import shutil
    import tarfile
    import tempfile
    import contextlib

    from . import meta as _meta_module
    from . import digest as _digest_module
    from . import _blob_writer as _blob_writer_module
    from . import _source_reader as _source_reader_module
    from . import _size_guarantee as _size_guarantee_module

    from .... import _common as _common_module

    _BlobWriter = _blob_writer_module.Class
    _SourceReader = _source_reader_module.Class

    _parse_digest = _digest_module.parse
    _normalize_path = _common_module.path.normalize
    _meta_blob_limit = _meta_module.blob_limit
    _make_blob_writer = _blob_writer_module.make
    _parse_manifest_ref = _meta_module.parse_manifest_ref
    _make_size_guarantee = _size_guarantee_module.make

    _layer_media_type_begin = "application/vnd.oci.image.layer.v1.tar"
    _layer_media_type_minimum_size = len(_layer_media_type_begin)

    def _make_index(digest: str, image: str):
        assert isinstance(image, str)
        assert image
        digest = _parse_digest(value = digest)
        return {
            "schemaVersion": 2,
            "manifests": [{
                "size": os.stat(os.path.join(image, digest.path)).st_size,
                "digest": digest.value,
                "mediaType": "application/vnd.oci.image.manifest.v1+json",
                "annotations": {"org.opencontainers.image.ref.name": "latest"}
            }]
        }

    def _make_layer_item(source: tarfile.TarInfo):
        assert isinstance(source, tarfile.TarInfo)
        _path = source.name
        assert isinstance(_path, str)
        if not _path: return None
        _path = _normalize_path(value = _path, drop_root = True).as_posix()
        if "." == _path: return None
        assert _path.strip(".")
        _result = tarfile.TarInfo(name = _path)
        if tarfile.DIRTYPE == source.type:
            _result.mode = 0o755
            _result.type = tarfile.DIRTYPE
        else:
            _result.mode = 0o644
            _result.type = tarfile.REGTYPE
        return _result

    def _validate_blob_writer(writer: _BlobWriter):
        assert isinstance(writer, _BlobWriter)
        return writer

    @contextlib.contextmanager
    def _open_blob_reader(digest: str, source: _SourceReader, size: int):
        assert isinstance(source, _SourceReader)
        assert isinstance(size, int)
        _path = _parse_digest(value = digest).path
        with source.open(_path) as _stream:
            with _make_size_guarantee(source = _stream, exact = size) as _guarantee: yield _guarantee

    @contextlib.contextmanager
    def _open_blob_writer(image: str):
        assert isinstance(image, str)
        assert image
        _descriptor, _temporary_path = tempfile.mkstemp(dir = image)
        with os.fdopen(_descriptor, "wb") as _stream:
            _writer = _make_blob_writer(stream = _stream)
            yield _writer
            _digest_path = os.path.join(image, _writer.digest.path)
            os.makedirs(os.path.dirname(_digest_path), exist_ok = True)
            shutil.move(_temporary_path, _digest_path)

    @contextlib.contextmanager
    def _open_layer_reader(digest: str, source: _SourceReader, size: int):
        assert isinstance(source, _SourceReader)
        assert isinstance(size, int)
        with _open_blob_reader(digest = digest, source = source, size = size) as _blob:
            with tarfile.open(mode = "r", fileobj = _blob) as _tar: yield _tar

    @contextlib.contextmanager
    def _open_layer_writer(image: str):
        with _open_blob_writer(image = image) as _blob:
            with tarfile.open(mode = "w", fileobj = _blob) as _tar: yield _tar

    def _validate_layer_media_type(value: str):
        assert isinstance(value, str)
        assert value
        assert value.startswith(_layer_media_type_begin)
        _value = value[_layer_media_type_minimum_size:]
        if not _value: return value
        assert "+" == _value[0]
        _value = _value[1:]
        assert _value in {"gzip", "bzip"}

    def _read_bundle(manifest: dict, source: _SourceReader):
        assert isinstance(manifest, dict)
        _media = manifest["mediaType"]
        assert isinstance(_media, str)
        assert "application/vnd.oci.image.manifest.v1+json" == _media
        _parse_manifest_ref(manifest = manifest)
        _size = manifest["size"]
        assert isinstance(_size, int)
        assert 0 < _size
        assert _meta_blob_limit >= _size
        with _open_blob_reader(
            digest = manifest["digest"], source = source, size = _size
        ) as _source_bundle: _meta = json.load(_source_bundle)
        assert isinstance(_meta, dict)
        _schema = _meta["schemaVersion"]
        assert isinstance(_schema, int)
        assert 2 == _schema
        _config = _meta["config"]
        assert isinstance(_config, dict)
        _media = _config["mediaType"]
        assert isinstance(_media, str)
        assert "application/vnd.oci.image.config.v1+json" == _media
        _size = _config["size"]
        assert isinstance(_size, int)
        assert 0 < _size
        assert _meta_blob_limit >= _size
        _layers = _meta["layers"]
        assert isinstance(_layers, list)
        assert _layers
        with _open_blob_reader(
            digest = _config["digest"], source = source, size = _size
        ) as _config: _config = json.load(_config)
        assert isinstance(_config, dict)
        assert _config
        return _meta, _config

    def _routine(manifest, source: _SourceReader, destination: str):
        assert isinstance(source, _SourceReader)
        assert isinstance(destination, str)
        if os.path.exists(destination):
            assert os.path.isdir(destination)
            assert not os.listdir(destination), f"directory is not empty: {destination}"
        if isinstance(manifest, bytes): manifest = json.loads(manifest.decode("utf-8"))
        elif isinstance(manifest, str): manifest = json.loads(manifest)
        elif not isinstance(manifest, dict): manifest = json.load(manifest)

        _source_meta, _destination_config = _read_bundle(manifest = manifest, source = source)

        os.makedirs(os.path.join(destination, "blobs"), exist_ok = True)

        with open(os.path.join(destination, "oci-layout"), "w") as _stream:
            json.dump({"imageLayoutVersion": "1.0.0"}, _stream)

        _destination_meta: dict = json.loads(json.dumps(_source_meta))
        _destination_meta["layers"].clear()

        with _open_blob_writer(image = destination) as _destination:
            json.dump(_destination_config, _destination)
            _destination_meta["config"]["size"] = _destination.tell()
            _destination_meta["config"]["digest"] = _destination.digest.value

        for _layer in _source_meta["layers"]:
            assert isinstance(_layer, dict)
            _validate_layer_media_type(value = _layer["mediaType"])
            with _open_layer_reader(digest = _layer["digest"], source = source, size = _layer["size"]) as _source:
                assert isinstance(_source, tarfile.TarFile)
                with _open_layer_writer(image = destination) as _destination:
                    assert isinstance(_destination, tarfile.TarFile)
                    for _source_item in _source:
                        _destination_item = _make_layer_item(source = _source_item)
                        if _destination_item is None: continue
                        _destination.addfile(_destination_item)
                _destination = _validate_blob_writer(writer = _destination.fileobj).digest
                _destination_meta["layers"].append({
                    "size": os.stat(os.path.join(destination, _destination.path)).st_size,
                    "digest": _destination.value,
                    "mediaType": "application/vnd.oci.image.layer.v1.tar"
                })

        with _open_blob_writer(image = destination) as _destination: json.dump(_destination_meta, _destination)
        _destination_meta: str = _destination.digest.value

        with open(os.path.join(destination, "index.json"), "w") as _stream:
            json.dump(_make_index(digest = _destination_meta, image = destination), _stream)

    class _Result(object):
        routine = _routine

    return _Result


_private = _private()
try: routine = _private.routine
finally: del _private
