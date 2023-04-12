#!/usr/bin/env python3
# -*- coding: utf-8 -*-

assert "__main__" != __name__


def _private():
    import typing

    _delegate_type_hint = typing.Callable[[typing.Callable], typing.Awaitable]

    class _Wrapper(object):
        @property
        def target(self): return self.__target

        @property
        def delegate(self): return self.__delegate

        def __await__(self): return self.__delegate(self.__target).__await__()

        async def __aiter__(self):
            _iterator = await self.__delegate(lambda: iter(self.__target))

            class _End(Exception): pass

            def _next():
                try: return next(_iterator)
                except StopIteration: raise _End()

            while True:
                try: yield await self.__delegate(_next)
                except _End: break

        async def __aenter__(self): return await self.__delegate(self.__target.__enter__)

        async def __aexit__(self, *args, **kwargs):
            return await self.__delegate(lambda: self.__target.__exit__(*args, **kwargs))

        def __init__(self, target, delegate: _delegate_type_hint):
            super().__init__()
            self.__target = target
            self.__delegate = delegate

    class _Class(object):
        @property
        def delegate(self): return self.__delegate

        def __call__(self, target): return _Wrapper(target = target, delegate = self.__delegate)

        def __init__(self, delegate: _delegate_type_hint):
            super().__init__()
            self.__delegate = delegate

    class _Result(object):
        Class = _Class

    return _Result


_private = _private()
try: Class = _private.Class
finally: del _private


# noinspection PyArgumentList
def make(*args, **kwargs): return Class(*args, **kwargs)
