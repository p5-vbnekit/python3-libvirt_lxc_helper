#!/usr/bin/env python3
# -*- coding: utf-8 -*-

assert "__main__" != __name__


def _private():
    from . import module_helpers as _module_helpers_module

    _make_lazy_getter = _module_helpers_module.lazy_attributes.make_getter

    class _Result(object):
        lazy_getter = _make_lazy_getter(dictionary = {
            "Action": lambda module: module.action.Class,
            "CliValidator": lambda module: module.cli_validator.Class,
            "PlatformInfo": lambda module: module.platform_info.Class,
            "Asynchronizer": lambda module: module.asynchronizer.Class
        })

    return _Result


_private = _private()

__all__ = _private.lazy_getter.keys
__date__ = None
__author__ = None
__version__ = None
__credits__ = None
_fields = tuple()
__bases__ = tuple()


def __getattr__(name: str): return _private.lazy_getter(name = name)
