#!/usr/bin/env python3
# -*- coding: utf-8 -*-

assert "__main__" != __name__


def _private():
    import typing
    import pathlib
    import argparse

    from . import _logic as _logic_module
    from . import _oci_image as _oci_image_module
    from ... import _common as _common_module

    _Action = _common_module.Action

    _logic_routine = _logic_module.routine
    _parse_digest = _oci_image_module.digest.parse
    _make_cli_validator = _common_module.cli_validator.make
    _validate_manifest_ref = _oci_image_module.meta.validate_manifest_ref

    _name = __package__.split(".")[-1]
    _name = _name.replace("_", "-")

    class _Class(_Action):
        @property
        def name(self) -> str: return _name

        def setup_cli(self, parser: argparse.ArgumentParser):
            assert isinstance(parser, argparse.ArgumentParser)

            # noinspection PyShadowingNames
            @self.__cli_validator.decorator(key = parser.add_argument(
                "-r", "--ref", required = False, help = "ref name",
                dest = f"{self.name}/ref"
            ).dest)
            def _routine(value: typing.Optional[str]):
                if value is not None: value = _validate_manifest_ref(value = value)
                return value

            # noinspection PyShadowingNames
            @self.__cli_validator.decorator(key = parser.add_argument(
                "-d", "--digest", required = False, help = "digest",
                dest = f"{self.name}/digest"
            ).dest)
            def _routine(value: typing.Optional[str]):  # noqa: F811
                if value is not None: value = _parse_digest(value = value).value
                return value

            # noinspection PyShadowingNames
            @self.__cli_validator.decorator(key = parser.add_argument(
                "-S", "--source", required = False, help = "source (oci image)",
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
                "-D", "--destination", required = False, help = "destination (rootfs bundle)",
                dest = f"{self.name}/destination"
            ).dest)
            def _routine(value: typing.Optional[str]):  # noqa: F811
                if value is not None:
                    assert isinstance(value, str)
                    assert value
                    value, = f"{value}\r\n".splitlines()
                return value

            # noinspection PyShadowingNames
            @self.__cli_validator.decorator(key = parser.add_argument(
                "-w", "--working-directory", required = False, help = "working-directory",
                dest = f"{self.name}/working-directory"
            ).dest)
            def _routine(value: typing.Optional[str]):  # noqa: F811
                if value is not None:
                    assert isinstance(value, str)
                    assert value
                    value, = f"{value}\r\n".splitlines()
                return value

        def validate_cli(self, arguments: dict):
            assert isinstance(arguments, dict)
            self.__cli_validator(arguments, allow_unknown = True)

        def __call__(self, cli: dict):
            assert isinstance(cli, dict)
            _logic_routine(
                ref = cli[f"{self.name}/ref"],
                digest = cli[f"{self.name}/digest"],
                source = cli[f"{self.name}/source"],
                destination = cli[f"{self.name}/destination"],
                working_directory = cli[f"{self.name}/working-directory"]
            )

        def __init__(self):
            super().__init__()
            self.__cli_validator = _make_cli_validator()

    class _Result(object):
        Class = _Class

    return _Result


_private = _private()
try: Class = _private.Class
finally: del _private


# noinspection PyArgumentList
def make(*args, **kwargs): return Class(*args, **kwargs)
