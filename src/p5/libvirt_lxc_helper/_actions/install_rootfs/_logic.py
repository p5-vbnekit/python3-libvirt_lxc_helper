#!/usr/bin/env python3
# -*- coding: utf-8 -*-

assert "__main__" != __name__


def _private():
    import typing
    import asyncio
    import contextlib
    import concurrent.futures

    from . import _installer as _installer_module

    from ... import _common as _common_module

    _spawn_installer = _installer_module.spawn
    _make_asynchronizer = _common_module.asynchronizer.make

    @contextlib.asynccontextmanager
    async def _open_asynchronizer():
        _loop = asyncio.get_running_loop()
        assert isinstance(_loop, asyncio.AbstractEventLoop)
        with concurrent.futures.ThreadPoolExecutor() as _thread_pool:
            yield _make_asynchronizer(executor = lambda delegate: _loop.run_in_executor(_thread_pool, delegate))

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
