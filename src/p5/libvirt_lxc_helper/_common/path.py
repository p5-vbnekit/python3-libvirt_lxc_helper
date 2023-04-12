#!/usr/bin/env python3
# -*- coding: utf-8 -*-

assert "__main__" != __name__


def _private():
    import typing
    import pathlib

    def _normalize(value: typing.Union[str, pathlib.PurePath], drop_root: bool = False) -> pathlib.PurePath:
        assert isinstance(drop_root, bool)

        if isinstance(value, str):
            assert value
            value, = f"{value}\r\n".splitlines()
            _type = pathlib.PurePath
            value = _type(value)
        else:
            _type = type(value)
            assert issubclass(_type, pathlib.PurePath)

        _collector = list()
        for value in value.parts:
            if "." == value: continue
            if ".." == value:
                if _collector: _collector.pop(0)
                continue
            _collector.append(value)

        value = _type(*_collector)

        if drop_root:
            _root = value.root
            if isinstance(value, pathlib.PureWindowsPath):
                _drive = value.drive
                if _root or _drive: value = value.relative_to(f"{_drive}{_root}")
            elif value.is_absolute(): value = value.relative_to("/")

        return value

    class _Result(object):
        normalize = _normalize

    return _Result


_private = _private()
try: normalize = _private.normalize
finally: del _private
