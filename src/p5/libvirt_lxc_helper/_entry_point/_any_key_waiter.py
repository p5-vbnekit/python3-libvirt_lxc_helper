#!/usr/bin/env python3
# -*- coding: utf-8 -*-

assert "__main__" != __name__


def _private():
    import sys

    from .. import _common as _common_module

    _platform_info = _common_module.platform_info.make()

    def _routine():
        _prompt_state = False

        try:
            if _platform_info.nt:
                import msvcrt
                _prompt_state = True
                print("press any key for exit", end = "", flush = True, file = sys.stderr)
                msvcrt.getch()
                return

            import termios
            _descriptor = sys.stdin.fileno()

            try:
                _old_tty_attributes = termios.tcgetattr(_descriptor)
                _new_tty_attributes = termios.tcgetattr(_descriptor)
                _new_tty_attributes[3] = _new_tty_attributes[3] & ~termios.ICANON & ~termios.ECHO
                termios.tcsetattr(_descriptor, termios.TCSANOW, _new_tty_attributes)
            except termios.error: return

            _prompt_state = True
            print("press any key for exit", end = "", flush = True, file = sys.stderr)

            try: sys.stdin.read(1)
            except IOError: pass
            finally: termios.tcsetattr(_descriptor, termios.TCSAFLUSH, _old_tty_attributes)
        finally:
            if _prompt_state: print("", flush = True, file = sys.stderr)

    class _Class(object):
        @property
        def condition(self): return self.__condition

        @condition.setter
        def condition(self, value: bool):
            assert isinstance(value, bool)
            if value: assert _platform_info.tty
            self.__condition = value

        def __call__(self):
            if self.__condition: _routine()

        def __init__(self, condition: bool = False):
            assert isinstance(condition, bool)
            if condition: assert _platform_info.tty
            super().__init__()
            self.__condition = condition

    class _Result(object):
        Class = _Class

    return _Result


_private = _private()
try: Class = _private.Class
finally: del _private


# noinspection PyArgumentList
def make(*args, **kwargs): return Class(*args, **kwargs)
