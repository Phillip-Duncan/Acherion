"""Module discovery helpers for the visual-logic function catalog."""

from __future__ import annotations

import builtins as _builtins
import dataclasses
import functools
import importlib
import logging
import math as _math
from collections.abc import Callable, Iterable
from typing import Any

_log = logging.getLogger(__name__)


@dataclasses.dataclass(frozen=True)
class CatalogScanSpec:
    """One scan target inside a catalog module."""

    prefix: str
    attr_path: tuple[str, ...] = ()


@dataclasses.dataclass(frozen=True)
class CatalogModuleSpec:
    """Metadata for one module exposed in the visual-logic catalog."""

    key: str
    label: str
    import_path: str | None = None
    scans: tuple[CatalogScanSpec, ...] = ()
    path_prefixes: tuple[str, ...] = ()
    loader: Callable[[], Any] | None = None
    blacklist: frozenset[str] = frozenset()
    type_allowlist: frozenset[str] = frozenset()
    object_module_roots: tuple[str, ...] = ()
    gate_types_with_allowlist: bool = False


@dataclasses.dataclass(frozen=True)
class LoadedCatalogModule:
    """A discovered module paired with its catalog metadata."""

    spec: CatalogModuleSpec
    module: Any


GLOBAL_BLACKLIST: frozenset[str] = frozenset({
    'print',
    'input',
    'open',
    'exec',
    'eval',
    'compile',
    '__import__',
    'breakpoint',
    'exit',
    'quit',
    'dir',
    'vars',
    'locals',
    'globals',
    'help',
    'id',
    'callable',
    'repr',
    'ascii',
    'format',
    'memoryview',
    'copyright',
    'credits',
    'license',
})

_BUILTINS_BLACKLIST: frozenset[str] = frozenset({
    'object', 'super', 'property', 'classmethod', 'staticmethod',
    'getattr', 'setattr', 'delattr', 'hasattr',
    'iter', 'next', 'hash',
    'bytearray', 'bytes', 'complex', 'frozenset', 'memoryview', 'slice',
    'type', '__build_class__', '__loader__', '__spec__',
    '__doc__', '__package__', '__name__',
    'bin', 'oct', 'hex', 'chr', 'ord',
    'aiter', 'anext',
})

_NUMPY_BLACKLIST: frozenset[str] = frozenset({
    'deprecate',
    'deprecate_with_doc',
    'show_config',
    'get_include',
    'who',
    'lookfor',
    'source',
    'info',
    'show_runtime',
    'dtype',
    'test',
})

_COLLECTIONS_BLACKLIST: frozenset[str] = frozenset({
    'Awaitable', 'Callable', 'Container', 'Coroutine', 'Generator',
    'Hashable', 'ItemsView', 'Iterable', 'Iterator', 'KeysView',
    'Mapping', 'MappingView', 'MutableMapping', 'MutableSequence',
    'MutableSet', 'Reversible', 'Sequence', 'Set', 'Sized', 'ValuesView',
})

_PATHLIB_BLACKLIST: frozenset[str] = frozenset({
    'PurePath',
    'PurePosixPath',
    'PureWindowsPath',
    'PosixPath',
    'WindowsPath',
})

_MATPLOTLIB_BLACKLIST: frozenset[str] = frozenset({
    'test',
    'use',
    'get_backend',
    'interactive',
    'is_interactive',
    'rc_context',
    'rcdefaults',
    'rcParams',
})

_MATPLOTLIB_PYPLOT_BLACKLIST: frozenset[str] = frozenset({
    'show',
    'ion',
    'ioff',
    'pause',
    'waitforbuttonpress',
    'switch_backend',
    'get_backend',
})

_BUILTIN_TYPE_ALLOWLIST: frozenset[str] = frozenset({
    'bool', 'dict', 'enumerate', 'filter', 'float', 'int', 'list', 'map',
    'range', 'reversed', 'set', 'str', 'tuple', 'zip',
})

_COLLECTIONS_TYPE_ALLOWLIST: frozenset[str] = frozenset({
    'Counter', 'defaultdict', 'deque', 'OrderedDict', 'ChainMap',
})

_PATHLIB_TYPE_ALLOWLIST: frozenset[str] = frozenset({'Path'})

_NUMPY_TYPE_ALLOWLIST: frozenset[str] = frozenset({'ndarray'})

_BASE_CATALOG_MODULE_SPECS: tuple[CatalogModuleSpec, ...] = (
    CatalogModuleSpec(
        key='builtins',
        label='Python builtins',
        loader=lambda: _builtins,
        scans=(CatalogScanSpec(prefix=''),),
        blacklist=_BUILTINS_BLACKLIST,
        type_allowlist=_BUILTIN_TYPE_ALLOWLIST,
        gate_types_with_allowlist=True,
    ),
    CatalogModuleSpec(
        key='math',
        label='math',
        loader=lambda: _math,
        scans=(CatalogScanSpec(prefix='math.'),),
        path_prefixes=('math.',),
        gate_types_with_allowlist=True,
    ),
    CatalogModuleSpec(
        key='re',
        label='re (regex)',
        import_path='re',
        scans=(CatalogScanSpec(prefix='re.'),),
        path_prefixes=('re.',),
        blacklist=frozenset({'purge', 'template'}),
        gate_types_with_allowlist=True,
    ),
    CatalogModuleSpec(
        key='collections',
        label='collections',
        import_path='collections',
        scans=(CatalogScanSpec(prefix='collections.'),),
        path_prefixes=('collections.',),
        blacklist=_COLLECTIONS_BLACKLIST,
        type_allowlist=_COLLECTIONS_TYPE_ALLOWLIST,
        object_module_roots=('collections',),
        gate_types_with_allowlist=True,
    ),
    CatalogModuleSpec(
        key='pathlib',
        label='pathlib',
        import_path='pathlib',
        scans=(CatalogScanSpec(prefix='pathlib.'),),
        path_prefixes=('pathlib.',),
        blacklist=_PATHLIB_BLACKLIST,
        type_allowlist=_PATHLIB_TYPE_ALLOWLIST,
        object_module_roots=('pathlib',),
        gate_types_with_allowlist=True,
    ),
    CatalogModuleSpec(
        key='np',
        label='numpy (np)',
        import_path='numpy',
        scans=(CatalogScanSpec(prefix='np.'),),
        path_prefixes=('np.', 'numpy.'),
        blacklist=_NUMPY_BLACKLIST,
        type_allowlist=_NUMPY_TYPE_ALLOWLIST,
        object_module_roots=('numpy',),
        gate_types_with_allowlist=True,
    ),
    CatalogModuleSpec(
        key='go',
        label='plotly.graph_objects (go)',
        import_path='plotly.graph_objects',
        scans=(CatalogScanSpec(prefix='go.'),),
        path_prefixes=('go.', 'plotly.graph_objects.', 'plotly.graph_objs.'),
        object_module_roots=('plotly.graph_objects', 'plotly.graph_objs'),
    ),
    CatalogModuleSpec(
        key='px',
        label='plotly.express (px)',
        import_path='plotly.express',
        scans=(CatalogScanSpec(prefix='px.'),),
        path_prefixes=('px.', 'plotly.express.'),
        object_module_roots=('plotly.express',),
        gate_types_with_allowlist=True,
    ),
    CatalogModuleSpec(
        key='plotly.subplots',
        label='plotly.subplots',
        import_path='plotly.subplots',
        scans=(CatalogScanSpec(prefix='plotly.subplots.'),),
        path_prefixes=('plotly.subplots.',),
        object_module_roots=('plotly.subplots',),
        gate_types_with_allowlist=True,
    ),
)

_REGISTERED_CATALOG_MODULE_SPECS: dict[str, CatalogModuleSpec] = {}


def _invalidate_catalog_caches() -> None:
    """Clear catalog module/runtime caches after extension changes."""
    available_modules.cache_clear()
    _module_labels.cache_clear()
    _spec_by_key.cache_clear()
    _path_prefix_to_module.cache_clear()
    runtime_global_bindings.cache_clear()
    from acherion.catalog import runtime as _catalog_runtime

    _catalog_runtime.clear_catalog_runtime_caches()


def register_catalog_module_specs(
    specs: Iterable[CatalogModuleSpec],
    *,
    replace: bool = False,
) -> None:
    """Register host-provided catalog module specs onto Acherion."""
    base_keys = {spec.key for spec in _BASE_CATALOG_MODULE_SPECS}
    for spec in specs:
        clean_key = str(spec.key or '').strip()
        if not clean_key:
            raise ValueError('Catalog module key is required.')
        if (
            clean_key in _REGISTERED_CATALOG_MODULE_SPECS
            or clean_key in base_keys
        ) and not replace:
            raise ValueError(f'Catalog module already registered: {clean_key}')
        _REGISTERED_CATALOG_MODULE_SPECS[clean_key] = spec
    _invalidate_catalog_caches()


def catalog_module_specs() -> tuple[CatalogModuleSpec, ...]:
    """Return core plus host-registered catalog module specs."""
    specs_by_key: dict[str, CatalogModuleSpec] = {
        spec.key: spec for spec in _BASE_CATALOG_MODULE_SPECS
    }
    specs_by_key.update(_REGISTERED_CATALOG_MODULE_SPECS)
    return tuple(specs_by_key.values())


@functools.lru_cache(maxsize=1)
def _module_labels() -> dict[str, str]:
    """Return cached module labels keyed by catalog module key."""
    return {spec.key: spec.label for spec in catalog_module_specs()}


@functools.lru_cache(maxsize=1)
def _spec_by_key() -> dict[str, CatalogModuleSpec]:
    """Return cached catalog specs keyed by module key."""
    return {spec.key: spec for spec in catalog_module_specs()}


@functools.lru_cache(maxsize=1)
def _path_prefix_to_module() -> tuple[tuple[str, str], ...]:
    """Return cached path-prefix map for module inference."""
    return tuple(
        sorted(
            (
                (prefix, spec.key)
                for spec in catalog_module_specs()
                for prefix in spec.path_prefixes
            ),
            key=lambda item: len(item[0]),
            reverse=True,
        )
    )


def _load_catalog_module(spec: CatalogModuleSpec) -> Any | None:
    """Load one catalog module object from import path or loader."""
    loader = spec.loader
    try:
        module_obj = (
            loader()
            if loader is not None
            else importlib.import_module(str(spec.import_path))
        )
    except ImportError:
        if spec.import_path:
            _log.debug('%s not available; omitted from catalog', spec.import_path)
        return None
    return module_obj


@functools.lru_cache(maxsize=1)
def available_modules() -> tuple[LoadedCatalogModule, ...]:
    """Return loaded catalog modules discovered from registered specs."""
    loaded: list[LoadedCatalogModule] = []
    for spec in catalog_module_specs():
        module_obj = _load_catalog_module(spec)
        if module_obj is None:
            continue
        loaded.append(LoadedCatalogModule(spec=spec, module=module_obj))
    return tuple(loaded)


def resolve_attr_path(root: Any, attr_path: str | tuple[str, ...]) -> Any | None:
    """Resolve dotted or segmented attribute paths from a root object."""
    if not attr_path:
        return root
    if isinstance(attr_path, str):
        parts = tuple(part for part in attr_path.split('.') if part)
    else:
        parts = attr_path
    current = root
    for part in parts:
        try:
            current = getattr(current, part)
        except AttributeError:
            return None
    return current


def scan_targets(
    loaded_module: LoadedCatalogModule,
) -> tuple[tuple[Any, str], ...]:
    """Return module objects and path prefixes to scan for one module."""
    targets: list[tuple[Any, str]] = []
    for scan in loaded_module.spec.scans:
        target = resolve_attr_path(loaded_module.module, scan.attr_path)
        if target is None:
            continue
        targets.append((target, scan.prefix))
    return tuple(targets)


def module_options() -> dict[str, str]:
    """Return {module_key: display_label} for the module selector."""
    return dict(_module_labels())


@functools.lru_cache(maxsize=1)
def runtime_global_bindings() -> dict[str, Any]:
    """Return runtime globals derived from registered catalog modules."""
    bindings: dict[str, Any] = {}
    for loaded_module in available_modules():
        spec = loaded_module.spec
        bindings.setdefault(spec.key, loaded_module.module)
        if spec.import_path:
            root_name = str(spec.import_path).split('.', 1)[0]
            try:
                bindings.setdefault(
                    root_name,
                    importlib.import_module(root_name),
                )
            except ImportError:
                continue
    return bindings


def path_to_module(path: str) -> str:
    """Infer module key from a function or class path."""
    for prefix, module_key in _path_prefix_to_module():
        if path.startswith(prefix):
            return module_key
    return 'builtins'


def strip_module_prefix(module_key: str, path: str) -> str:
    """Strip the registered path prefix for *module_key* from *path*."""
    spec = catalog_module_spec(module_key)
    if spec is None:
        return path
    for prefix in spec.path_prefixes:
        if path.startswith(prefix):
            return path[len(prefix):]
    return path


def catalog_module_object(module_key: str) -> Any | None:
    """Return the loaded module object for a module key, if available."""
    for loaded_module in available_modules():
        if loaded_module.spec.key == module_key:
            return loaded_module.module
    return None


def catalog_module_spec(module_key: str) -> CatalogModuleSpec | None:
    """Return one catalog module spec by module key."""
    return _spec_by_key().get(module_key)


__all__ = [
    'CatalogModuleSpec',
    'CatalogScanSpec',
    'GLOBAL_BLACKLIST',
    'LoadedCatalogModule',
    'available_modules',
    'catalog_module_object',
    'catalog_module_spec',
    'catalog_module_specs',
    'module_options',
    'path_to_module',
    'register_catalog_module_specs',
    'resolve_attr_path',
    'runtime_global_bindings',
    'scan_targets',
    'strip_module_prefix',
]