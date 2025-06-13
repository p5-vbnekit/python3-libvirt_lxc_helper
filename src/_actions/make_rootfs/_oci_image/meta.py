#!/usr/bin/env python3
# -*- coding: utf-8 -*-

assert "__main__" != __name__


def _private():
    import json
    import typing

    from . import digest as _digest_module

    _parse_digest = _digest_module.parse

    _blob_limit = 32 * 1024 * 1024

    def _validate_manifest_ref(value: str):
        assert isinstance(value, str)
        assert value
        value, = f"{value}\r\n".splitlines()
        return value

    def _parse_manifest_ref(manifest: dict):
        assert isinstance(manifest, dict)
        try: _value = manifest["annotations"]
        except KeyError: return None
        assert isinstance(_value, dict)
        try: _value = _value["org.opencontainers.image.ref.name"]
        except KeyError: return None
        return _validate_manifest_ref(value = _value)

    def _validate_manifest(value: dict):
        assert isinstance(value, dict)
        _media = value["mediaType"]
        assert isinstance(_media, str)
        assert "application/vnd.oci.image.manifest.v1+json" == _media
        assert _parse_digest(value = value["digest"]).value
        _size = value["size"]
        assert isinstance(_size, int)
        assert 0 < _size
        _parse_manifest_ref(manifest = value)
        return value

    def _validate_bundle(value: dict):
        assert isinstance(value, dict)
        _schema = value["schemaVersion"]
        assert isinstance(_schema, int)
        assert 2 == _schema
        _config = value["config"]
        assert isinstance(_config, dict)
        _media = _config["mediaType"]
        assert isinstance(_media, str)
        assert "application/vnd.oci.image.config.v1+json" == _media
        _size = _config["size"]
        assert isinstance(_size, int)
        assert 0 < _size
        assert _blob_limit >= _size
        assert isinstance(value["layers"], list)
        return value

    def _parse_manifest(value: typing.Union[bytes, str, dict]):
        if isinstance(value, bytes): value = json.loads(value.decode("utf-8"))
        elif isinstance(value, str): value = json.loads(value)
        return _validate_manifest(value = value)

    def _parse_bundle(value: typing.Union[bytes, str, dict]):
        if isinstance(value, bytes): value = json.loads(value.decode("utf-8"))
        elif isinstance(value, str): value = json.loads(value)
        return _validate_bundle(value = value)

    class _Result(object):
        blob_limit = _blob_limit
        parse_bundle = _parse_bundle
        parse_manifest = _parse_manifest
        parse_manifest_ref = _parse_manifest_ref
        validate_bundle = _validate_bundle
        validate_manifest = _validate_manifest
        validate_manifest_ref = _validate_manifest_ref

    return _Result


_private = _private()
try:
    blob_limit = _private.blob_limit
    parse_bundle = _private.parse_bundle
    parse_manifest = _private.parse_manifest
    parse_manifest_ref = _private.parse_manifest_ref
    validate_bundle = _private.validate_bundle
    validate_manifest = _private.validate_manifest
    validate_manifest_ref = _private.validate_manifest_ref
finally: del _private
