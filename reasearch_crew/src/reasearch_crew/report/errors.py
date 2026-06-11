from __future__ import annotations


class TypesetError(RuntimeError):
    """A local typesetting subprocess (pandoc / xelatex) failed.

    Keeps consumer error-handling uniform: the typesetting steps never leak a
    raw subprocess.CalledProcessError. The network path has the gateway's five
    exception classes; the local path has just this one.
    """
