from . import execute


profiler = execute.profiler
execute = profiler

__all__ = [
    "execute",
]
