#!/usr/bin/env python3
# -*- coding: utf-8 -*-

assert "__main__" == __name__


def _private():
    import os
    import setuptools
    import setuptools.command.build_py

    def _make_long_description():
        with open(os.path.join(os.path.dirname(__file__), "README.md"), "r") as _stream: return _stream.read()

    def _make_packages():
        _packages = setuptools.find_namespace_packages(where = "src")
        _packages.remove("p5")
        return _packages

    class _Generators(object):
        @classmethod
        def get(cls): return tuple()

    class _Commands(object):
        @staticmethod
        def build_py():
            # noinspection PyShadowingNames
            class _Result(setuptools.command.build_py.build_py):
                def run(self):
                    # noinspection PyNoneFunctionAssignment
                    _original_result = super().run()
                    for _generator in _Generators.get(): _generator(command_interface = self)
                    return _original_result

                def get_outputs(self, *args, **kwargs):
                    _original_result = super().get_outputs(*args, **kwargs)
                    return (type(_original_result))((*_original_result, *[os.path.join(self.build_lib, _generated.path) for _generated in _Generators.get()]))

            return _Result

    def _routine(): setuptools.setup(
        name = "p5.libvirt_lxc_helper",
        url = "https://github.com/p5-vbnekit/p5-python3-libvirt_lxc_helper",
        license = "CC0",
        version = "0.0.0",
        author = "Nikita Pushchin",
        author_email = "vbnekit@gmail.com",
        description = "libvirt_lxc helper tool",
        long_description = _make_long_description(),
        long_description_content_type = "text/markdown",
        package_dir = {"": "src"},
        packages = _make_packages(),
        cmdclass = {
            "build_py": _Commands.build_py()
        },
        entry_points = {
            "console_scripts": (
                "p5-libvirt_lxc_helper=p5.libvirt_lxc_helper:entry_point",
            ),
        },
        install_requires = ("python-magic", ),
        setup_requires = ("wheel", )
    )

    class _Result(object):
        routine = _routine

    return _Result


try: _private().routine()
finally: del _private
