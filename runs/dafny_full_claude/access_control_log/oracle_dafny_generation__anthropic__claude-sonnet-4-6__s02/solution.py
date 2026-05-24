# Dafny program compiled into Python and adapted for SlopBench imports.
import module_ as _dafny_module
from module_ import *  # noqa: F403


def _specoracle_alias_dafny_symbols(namespace):
    for obj in list(namespace.values()):
        if not isinstance(obj, type):
            continue
        original_init = getattr(obj, "__init__", None)
        constructor = getattr(obj, "ctor__", None)
        if callable(original_init) and callable(constructor):
            def __init__(self, *args, __orig=original_init, __ctor=constructor, **kwargs):
                __orig(self)
                if args or kwargs:
                    __ctor(self, *args, **kwargs)

            obj.__init__ = __init__
        for name in list(vars(obj)):
            if "__" in name and not name.startswith("__"):
                setattr(obj, name.replace("__", "_"), getattr(obj, name))

    default = namespace.get("default__")
    if default is not None:
        for name in dir(default):
            if name.startswith("_"):
                continue
            attr = getattr(default, name)
            if callable(attr):
                namespace[name.replace("__", "_")] = attr


_specoracle_alias_dafny_symbols(globals())
