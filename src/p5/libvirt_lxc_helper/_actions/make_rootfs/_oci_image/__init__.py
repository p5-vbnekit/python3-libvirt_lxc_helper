#!/usr/bin/env python3
# -*- coding: utf-8 -*-

assert "__main__" != __name__


def _private():
    from .... _common import module_helpers as _module_helpers_module

    class _Result(object):
        module_getter = _module_helpers_module.lazy_attributes.make_getter(dictionary = {
            "Digest": lambda module: module.digest.Class,
            "Class": lambda module: getattr(module, "_class").Class,
            "make": lambda module: getattr(module, "_class").make
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
