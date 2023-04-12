#!/usr/bin/env python3
# -*- coding: utf-8 -*-

assert "__main__" != __name__


def _private():
    import sys
    import atexit

    from . import _cli_parser as _cli_parser_module
    from . import _any_key_waiter as _any_key_waiter_module

    from .. import _common as _common_module
    from .. import _actions as _actions_module

    _platform_info = _common_module.platform_info.make()

    _any_key_waiter = _any_key_waiter_module.make(_platform_info.nt and _platform_info.tty)

    def _generate_actions():
        for _module in (
            _actions_module.make_rootfs,
            _actions_module.install_rootfs
        ): yield _module.make()

    _actions = {_action.name: _action for _action in _generate_actions()}

    def _make_cli_parser():
        _root = _cli_parser_module.make()
        _subparsers = _root.subparsers
        for _name, _action in _actions.items(): _action.setup_cli(parser = _subparsers.add_parser(_name))
        return _root

    def _routine():
        atexit.register(_any_key_waiter)
        _cli_parser = _make_cli_parser()
        _help_message = _cli_parser.help()

        try:
            _parsed_cli = _cli_parser.parse()
            _actions[_parsed_cli["action"]].validate_cli(arguments = _parsed_cli)

        except BaseException as _exception:
            if all((
                _platform_info.tty,
                (not isinstance(_exception, SystemExit)) or (0 != _exception.code)
            )): atexit.register(lambda: print(_help_message, flush = True, file = sys.stderr))
            raise

        try:
            del _cli_parser
            _any_key_waiter.condition = _parsed_cli["wait_at_exit"]
            _actions[_parsed_cli["action"]](cli = _parsed_cli)

        except KeyboardInterrupt:
            _any_key_waiter.condition = False
            raise

    class _Result(object):
        routine = _routine

    return _Result


_private = _private()
try: routine = _private.routine
finally: del _private
