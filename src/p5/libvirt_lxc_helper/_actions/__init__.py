#!/usr/bin/env python3
# -*- coding: utf-8 -*-

assert "__main__" != __name__


def _private():
    from .. _common import module_helpers as _module_helpers_module

    class _Result(object):
        module_getter = _module_helpers_module.lazy_attributes.make_getter(dictionary = {
            "MakeRootfs": lambda module: module.make_rootfs.Class,
            "InstallRootfs": lambda module: module.make_rootfs.Class
        })

    return _Result


_private = _private()

__all__ = _private.module_getter.keys
__date__ = None
__author__ = None
__version__ = None
__credits__ = None
_fields = tuple()
__bases__ = tuple()


def __getattr__(name: str): return _private.module_getter(name = name)
