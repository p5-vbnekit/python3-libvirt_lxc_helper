#!/usr/bin/env python3
# -*- coding: utf-8 -*-

assert "__main__" != __name__


def _private():
    import typing
    import pathlib
    import argparse

    from . import _logic as _logic_module
    from ... import _common as _common_module

    _name = __package__.split(".")[-1]
    _name = _name.replace("_", "-")

    _cli_validator_module = _common_module.cli_validator

    _routine = _logic_module.routine

    class _Class(_common_module.Action):
        @property
        def name(self) -> str: return _name

        def setup_cli(self, parser: argparse.ArgumentParser):
            assert isinstance(parser, argparse.ArgumentParser)

            # noinspection PyShadowingNames
            @self.__cli_validator.decorator(key = parser.add_argument(
                "--dry-mode", required = False, action = "store_true", help = "do not write anything",
                dest = f"{self.name}/dry-mode"
            ).dest)
            def _routine(value: bool):  # noqa: F811
                assert isinstance(value, bool)
                return value

            # noinspection PyShadowingNames
            @self.__cli_validator.decorator(key = parser.add_argument(
                "-s", "--source", required = False, help = "source (oci image)",
                dest = f"{self.name}/source"
            ).dest)
            def _routine(value: typing.Optional[str]):  # noqa: F811
                if value is not None:
                    assert isinstance(value, str)
                    assert value
                    value, = f"{value}\r\n".splitlines()
                    assert pathlib.Path(value).resolve(strict = True)
                return value

            # noinspection PyShadowingNames
            @self.__cli_validator.decorator(key = parser.add_argument(
                "-d", "--destination", required = True, help = "lxc container",
                dest = f"{self.name}/destination"
            ).dest)
            def _routine(value: str):  # noqa: F811
                assert isinstance(value, str)
                assert value
                value, = f"{value}\r\n".splitlines()
                return value

        def validate_cli(self, arguments: dict):
            assert isinstance(arguments, dict)
            self.__cli_validator(arguments, allow_unknown = True)

        def __call__(self, cli: dict):
            assert isinstance(cli, dict)
            _routine(
                dry = cli[f"{self.name}/dry-mode"],
                source = cli[f"{self.name}/source"],
                destination = cli[f"{self.name}/destination"]
            )

        def __init__(self):
            super().__init__()
            self.__cli_validator = _cli_validator_module.make()

    class _Result(object):
        Class = _Class

    return _Result


_private = _private()
try: Class = _private.Class
finally: del _private


# noinspection PyArgumentList
def make(*args, **kwargs): return Class(*args, **kwargs)
