#!/usr/bin/env python3
# -*- coding: utf-8 -*-

assert "__main__" != __name__


def _private():
    import io
    import json
    import shlex
    import magic
    import typing

    try: import yaml as _yaml_module
    except ImportError: _yaml_module = None

    def _get_magic(source: typing.Union[str, bytes]):
        if isinstance(source, str): source = source.strip().encode("utf-8")
        assert isinstance(source, bytes)
        assert source
        source = source.strip()
        assert source
        return magic.from_buffer(source, mime = True)

    def _parse_environment_payload(value: typing.Union[dict, list]):
        if isinstance(value, dict): value = [value]
        else: assert isinstance(value, list)
        _collector = dict()
        for value in value:
            assert isinstance(value, dict)
            for _key, value in value.items():
                assert _key not in _collector
                if not isinstance(value, (str, bool)):
                    assert isinstance(value, (int, float))
                    value = str(value)
                _collector[_key] = value
        return _collector

    def _parse_environment(value: typing.Union[bool, list, dict]):
        if isinstance(value, bool): return {"inherit": value, "payload": dict()}
        if isinstance(value, list): return {"inherit": True, "payload": _parse_environment_payload(value = value)}

        assert isinstance(value, dict)
        value = value.copy()
        _may_payload = dict()

        try: _inherit = value.pop("inherit")
        except KeyError: _inherit = None
        else:
            if not isinstance(_inherit, bool):
                _may_payload["inherit"] = str(_inherit)
                _inherit = None

        try: _payload = value.pop("payload")
        except KeyError: _payload = None
        else:
            if not isinstance(_payload, (list, dict)):
                _may_payload["payload"] = str(_payload)
                _payload = None

        if (_payload is None) and (_inherit is None):
            _may_payload.update(value)
            return {"inherit": True, "payload": _parse_environment_payload(value = _may_payload)}

        try: assert not value
        except AssertionError: raise ValueError(value.keys())

        try: assert not _may_payload
        except AssertionError: raise ValueError(_may_payload.keys())

        return {
            "inherit": True if _inherit is None else _inherit,
            "payload": dict() if _payload is None else _parse_environment_payload(value = _payload)
        }

    def _parse_body_command(value: typing.Union[str, list]):
        if isinstance(value, str):
            assert value
            value, = f"{value}\r\n".splitlines()
            value = shlex.split(value, comments = False, posix = True)
            assert value
            return value

        assert isinstance(value, list)
        assert isinstance(value[0], str) and bool(value[0])
        for _item in value: assert isinstance(_item, str)
        return value

    def _parse_body_item(value: typing.Union[str, list, dict]):
        if isinstance(value, (str, list)): return {
            "command": _parse_body_command(value = value), "environment": _parse_environment(value = True)
        }

        assert isinstance(value, dict)
        value = value.copy()

        _command = _parse_body_command(value.pop("command"))

        try: _environment = value.pop("environment")
        except KeyError: _environment = True
        _environment = _parse_environment(value = _environment)

        try: _input = value.pop("input")
        except KeyError: _input = None
        else: assert isinstance(_input, str)

        try: assert not value
        except AssertionError: raise ValueError(value.keys())

        _value = {"command": _command, "environment": _environment}
        if _input: _value["input"] = _input

        return _value

    def _parse_body(value: list):
        assert isinstance(value, list)
        return tuple([_parse_body_item(value = value) for value in value])

    def _parse_parts(
        body: list,
        exclude: bool,
        environment: typing.Union[bool, dict]
    ):
        body = _parse_body(value = body)
        assert isinstance(exclude, bool)
        environment = _parse_environment(value = environment)
        return dict(body = body, exclude = exclude, environment = environment)

    def _parse(value: typing.Union[bytes, str, dict]):
        if not isinstance(value, dict):
            _magic = _get_magic(source = value)
            if isinstance(value, bytes): value = value.decode("utf-8")
            if "application/json" == _magic: value = json.loads(value)
            else:
                assert _yaml_module is not None
                _generator = _yaml_module.safe_load_all(io.StringIO(value))
                value = next(_generator)
                try: next(_generator)
                except StopIteration: pass
                else: raise OverflowError()
            assert isinstance(value, dict)

        _value = {"body": list(), "exclude": True, "environment": True}
        _value.update(value)

        return _parse_parts(**_value)

    class _Result(object):
        parse = _parse

    return _Result


_private = _private()
try: parse = _private.parse
finally: del _private
