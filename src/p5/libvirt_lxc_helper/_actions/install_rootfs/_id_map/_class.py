#!/usr/bin/env python3
# -*- coding: utf-8 -*-

assert "__main__" != __name__


def _private():
    import typing

    from . import item as _item_module
    from . import _range as _range_module

    _Item = _item_module.Class
    _Range = _range_module.Class

    _make_item = _item_module.make
    _make_range = _range_module.make

    class _CollisionError(Exception): pass

    def _make_range_text(value: _Range):
        assert isinstance(value, _Range)
        return f"{value.offset}:{value.last}"

    def _make_collision_text(first: _Range, second: _Range):
        return format(" | ".join(_make_range_text(value = _item) for _item in (first, second)))

    def _is_compatible(first: _Range, second: _Range):
        assert isinstance(first, _Range)
        assert isinstance(second, _Range)
        if first.last < second.offset: return True
        return second.last < first.offset

    def _check_collision(first: _Item, second: _Item):
        assert isinstance(first, _Item)
        assert isinstance(second, _Item)

        try:
            _first = _make_range(offset = first.host, size = first.size)
            _second = _make_range(offset = second.host, size = second.size)
            if not _is_compatible(first = _first, second = _second): raise _CollisionError(
                f"host: {_make_collision_text(first = _first, second = _second)}"
            )

        finally:
            _first = _make_range(offset = first.container, size = first.size)
            _second = _make_range(offset = second.container, size = second.size)
            if not _is_compatible(first = _first, second = _second): raise _CollisionError(
                f"container: {_make_collision_text(first = _first, second = _second)}"
            )

    def _validate_items(value: typing.Iterable[_Item]):
        _collector = list()

        for _first in value:
            for _second in value:
                if _first is not _second: _check_collision(first = _first, second = _second)
            _collector.append(_first)

        _collector.sort(key = lambda _item: _item.container)

        return tuple(_collector)

    def _map(value: int, collector: typing.Iterable[_Item]):
        assert isinstance(value, int)
        assert 0 <= value
        for _candidate in collector:
            assert isinstance(_candidate, _Item)
            _first = _candidate.container
            _last = _first + _candidate.size - 1
            if value < _first: continue
            if value > _last: continue
            return _candidate.host + (value - _first)
        raise KeyError(value)

    class _Class(object):
        Item = _Item

        def user(self, value: int):
            assert isinstance(value, int)
            try: return self.__user_cache[value]
            except KeyError: pass
            _value = _map(value = value, collector = self.__user)
            self.__user_cache[value] = _value
            return _value

        def group(self, value: int):
            assert isinstance(value, int)
            try: return self.__group_cache[value]
            except KeyError: pass
            _value = _map(value = value, collector = self.__group)
            self.__group_cache[value] = _value
            return _value

        def __init__(self, user: typing.Iterable[_Item], group: typing.Iterable[_Item]):
            super().__init__()
            user = _validate_items(value = user)
            group = _validate_items(value = group)
            self.__user = user
            self.__group = group
            self.__user_cache = dict()
            self.__group_cache = dict()

    class _Result(object):
        Item = _Item
        Class = _Class

    return _Result


_private = _private()

try: Class = _private.Class
finally: del _private


# noinspection PyArgumentList
def make(*args, **kwargs): return Class(*args, **kwargs)
