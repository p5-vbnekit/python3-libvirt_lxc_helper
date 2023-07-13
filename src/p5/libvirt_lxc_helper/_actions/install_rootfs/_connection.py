#!/usr/bin/env python3
# -*- coding: utf-8 -*-

assert "__main__" != __name__


def _private():
    import typing
    import asyncio
    import libvirt
    import xml.etree.ElementTree

    from . import _id_map as _id_map_module

    from ... import _common as _common_module

    _Asynchronizer = _common_module.asynchronous_tools.Asynchronizer

    _make_id_map = _id_map_module.make
    _normalize_path = _common_module.path.normalize
    _make_id_map_item = _id_map_module.item.make

    def _check_domain(instance: libvirt.virDomain):
        assert isinstance(instance, libvirt.virDomain)
        instance = instance.isActive()
        assert isinstance(instance, int)
        if 0 != instance: raise RuntimeError("unexpected container activity detected")

    def _parse_id_map_element(value: xml.etree.ElementTree.Element):
        assert isinstance(value, xml.etree.ElementTree.Element)
        _start = value.attrib["start"]
        assert isinstance(_start, str)
        _start = int(_start)
        assert 0 <= _start
        _target = value.attrib["target"]
        _target = int(_target)
        assert 0 <= _target
        _count = value.attrib["count"]
        _count = int(_count)
        assert 0 < _count
        return _make_id_map_item(container = _start, host = _target, size = _count)

    def _parse_id_map(value: xml.etree.ElementTree.Element):
        assert isinstance(value, xml.etree.ElementTree.Element)
        _iterator = value.iter(tag = "idmap")
        try: value = next(_iterator)
        except StopIteration: return None
        try: next(_iterator)
        except StopIteration: pass
        else: raise OverflowError()
        _user = [_parse_id_map_element(value = _item) for _item in value.iter(tag = "uid")]
        _group = [_parse_id_map_element(value = _item) for _item in value.iter(tag = "gid")]
        if _user or _group: return _make_id_map(user = _user, group = _group)
        return None

    def _parse_filesystem(value: xml.etree.ElementTree.Element):
        assert isinstance(value, xml.etree.ElementTree.Element)
        try: _type = value.attrib["type"]
        except KeyError: return None
        if "mount" != _type: return None
        _iterator = iter(value.iter(tag = "target"))
        try: _target = next(_iterator)
        except StopIteration: raise KeyError("target")
        try: next(_iterator)
        except StopIteration: pass
        else: raise OverflowError()
        try: _target = _target.attrib["dir"]
        except KeyError: raise KeyError("target.dir")
        assert isinstance(_target, str)
        _normalized = _normalize_path(value = _target)
        assert _target == _normalized.as_posix()
        assert _normalized.is_absolute()
        _iterator = iter(value.iter(tag = "source"))
        try: _source = next(_iterator)
        except StopIteration: raise KeyError("source")
        try: next(_iterator)
        except StopIteration: pass
        else: raise OverflowError()
        try: _source = _source.attrib["dir"]
        except KeyError: raise KeyError("source.dir")
        assert isinstance(_source, str)
        _normalized = _normalize_path(value = _source)
        assert _source == _normalized.as_posix()
        assert _normalized.is_absolute()
        return _target, _source

    def _parse_description(value: str):
        assert isinstance(value, str)
        assert value
        value = xml.etree.ElementTree.fromstring(value)
        assert isinstance(value, xml.etree.ElementTree.Element)
        assert "domain" == value.tag
        assert "lxc" == value.attrib["type"]
        _id_map = _parse_id_map(value = value)
        _iterator = iter(value.iter(tag = "devices"))
        value = next(_iterator)
        try: next(_iterator)
        except StopIteration: pass
        else: raise OverflowError()
        _targets = set()
        _root_directory = None
        for _filesystem in value.iter(tag = "filesystem"):
            _filesystem = _parse_filesystem(value = _filesystem)
            if _filesystem is None: continue
            _target, _source = _filesystem
            assert _target not in _targets
            _targets.add(_target)
            if "/" == _target: _root_directory = _source
        if _root_directory is None: raise KeyError("domain.devices.filesystem.target.dir: /")
        return _id_map, _root_directory

    class _Context(object):
        def __init__(self):
            super().__init__()
            self.path = None
            self.id_map = None
            self.domain = None
            self.connection = None
            self.monitoring_task = None

    class _Helper(object):
        @property
        def asynchronizer(self): return self.__asynchronizer

        async def close_context(self, instance: _Context):
            assert isinstance(instance, _Context)

            try:
                _monitoring_task = instance.monitoring_task
                if _monitoring_task is None: return
                _monitoring_task.cancel()
                await asyncio.gather(_monitoring_task, return_exceptions = True)

            finally:
                _connection = instance.connection
                if _connection is not None: await self.__asynchronizer(instance.connection.close)

        def make_domain_monitoring_task(self, instance: libvirt.virDomain):
            assert isinstance(instance, libvirt.virDomain)

            _asynchronizer = self.__asynchronizer

            async def _coroutine():
                while True:
                    await _asynchronizer(_check_domain, instance = instance)
                    await asyncio.sleep(1 / +3.0e+0)

            return asyncio.create_task(_coroutine())

        def __init__(self, asynchronizer: _Asynchronizer):
            super().__init__()
            assert isinstance(asynchronizer, _Asynchronizer)
            self.__asynchronizer = asynchronizer

    class _Class(object):
        @property
        def path(self): return None if self.__context is None else self.__context.path

        @property
        def id_map(self): return None if self.__context is None else self.__context.id_map

        async def open(self):
            assert self.__context is None
            _context = _Context()
            try:
                _context.connection = typing.cast(
                    libvirt.virConnect, await self.__helper.asynchronizer(libvirt.open, "lxc://")
                )
                _context.domain = typing.cast(libvirt.virDomain, await self.__helper.asynchronizer(
                    _context.connection.lookupByName, self.__domain
                ))
                await self.__helper.asynchronizer(_check_domain, instance = _context.domain)
                _context.monitoring_task = self.__helper.make_domain_monitoring_task(instance = _context.domain)

                _context.id_map, _context.path = await self.__helper.asynchronizer(
                    lambda: _parse_description(value = _context.domain.XMLDesc())
                )

                assert not _context.monitoring_task.done()

                self.__context = _context

            finally:
                if self.__context is None: await self.__helper.close_context(instance = _context)

        async def close(self):
            _context = self.__context
            assert isinstance(_context, _Context)
            self.__context = None
            await self.__helper.close_context(instance = _context)

        async def __call__(self, task: asyncio.Task):
            assert isinstance(task, asyncio.Task)
            if task.done(): return await task
            _context = self.__context
            assert isinstance(_context, _Context)
            _monitoring_task = _context.monitoring_task
            await asyncio.wait((task, _monitoring_task), return_when = asyncio.FIRST_COMPLETED)
            if _monitoring_task.done(): raise RuntimeError("unexpected container activity detected")
            return await task

        async def __aenter__(self): return self

        async def __aexit__(self, exception_type, exception_instance, exception_traceback):
            _context = self.__context
            if _context is None: return
            self.__context = None
            await self.__helper.close_context(instance = _context)

        def __init__(self, domain: str, asynchronizer: _Asynchronizer):
            super().__init__()
            assert isinstance(domain, str)
            assert domain
            assert isinstance(asynchronizer, _Asynchronizer)
            _helper = _Helper(asynchronizer = asynchronizer)
            self.__helper = _helper
            self.__domain = domain
            self.__context = None

    class _Result(object):
        Class = _Class

    return _Result


_private = _private()
try: Class = _private.Class
finally: del _private


# noinspection PyArgumentList
def make(*args, **kwargs): return Class(*args, **kwargs)
