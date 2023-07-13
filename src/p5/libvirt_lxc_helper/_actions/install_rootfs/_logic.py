#!/usr/bin/env python3
# -*- coding: utf-8 -*-

assert "__main__" != __name__


def _private():
    import typing
    import asyncio
    import contextlib

    from . import _installer as _installer_module

    from ... import _common as _common_module

    _spawn_installer = _installer_module.spawn
    _make_thread_pool = _common_module.asynchronous_tools.thread_pool.make
    _make_asynchronizer = _common_module.asynchronous_tools.asynchronizer.make

    @contextlib.asynccontextmanager
    async def _open_asynchronizer():
        with _make_thread_pool() as _thread_pool:
            def _spawn(delegate: typing.Callable): return _thread_pool(delegate)
            _thread_pool.open()
            yield await _thread_pool(_make_asynchronizer, executor = _spawn)

    async def _coroutine(dry: bool, source: typing.Optional[str], destination: str):
        assert isinstance(destination, str)
        assert destination

        from . import _connection as _connection_module

        async with (
            _open_asynchronizer() as _asynchronizer,
            await _asynchronizer(_connection_module.make, domain = destination, asynchronizer = _asynchronizer) as _connection
        ):
            await _connection.open()
            _task = _spawn_installer(
                dry = dry, source = source, destination = _connection.path,
                id_map = _connection.id_map, asynchronizer = _asynchronizer
            )
            try: await _connection(_task)
            finally:
                if not _task.done(): _task.cancel()
                await asyncio.gather(_task, return_exceptions = True)

    def _routine(*args, **kwargs): asyncio.run(_coroutine(*args, **kwargs))

    class _Result(object):
        routine = _routine

    return _Result


_private = _private()
try: routine = _private.routine
finally: del _private
