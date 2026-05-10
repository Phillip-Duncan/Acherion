"""Runtime introspection helpers for the visual-logic function catalog."""

from __future__ import annotations

import dataclasses
import functools
import inspect
import types
from typing import Any

from acherion.catalog import models as _catalog_models
from acherion.catalog import modules as _catalog_modules
from acherion.catalog import types as _catalog_types


def _object_matches_module_roots(
    obj: Any,
    roots: tuple[str, ...],
) -> bool:
    """Return True when object module matches one allowed root."""
    if not roots:
        return True
    obj_module = str(getattr(obj, '__module__', '') or '')
    if not obj_module:
        return True
    return any(
        obj_module == root or obj_module.startswith(f'{root}.')
        for root in roots
    )


def _is_useful_callable(
    name: str,
    obj: Any,
    spec: _catalog_modules.CatalogModuleSpec,
) -> bool:
    """Return True if *obj* is worth including in the catalog."""
    module_key = spec.key
    if not callable(obj):
        return False
    if name.startswith('_'):
        return False
    if isinstance(obj, types.ModuleType):
        return False
    if isinstance(obj, type) and issubclass(obj, BaseException):
        return False
    if isinstance(obj, type):
        if spec.gate_types_with_allowlist:
            return name in spec.type_allowlist
    if module_key.startswith('sp.'):
        type_name = type(obj).__name__
        if type_name.endswith('_gen') or 'rv_' in type_name:
            return False
        obj_module = getattr(obj, '__module__', '') or ''
        if obj_module and not obj_module.startswith('scipy'):
            return False
    if not _object_matches_module_roots(obj, spec.object_module_roots):
        return False
    return True


def _annotation_text(annotation: Any) -> str:
    """Return a readable annotation string for signatures."""
    if annotation is inspect.Parameter.empty:
        return ''
    try:
        text = inspect.formatannotation(annotation)
    except Exception:  # pylint: disable=broad-except
        text = str(annotation)
    return text.replace('typing.', '').replace('collections.abc.', '')


def _parameter_type_tag(parameter: inspect.Parameter) -> str:
    """Return best-effort type tag for one callable parameter."""
    param_type = _catalog_types.annotation_to_tag(parameter.annotation)
    if (
        param_type == 'any'
        and parameter.default is not inspect.Parameter.empty
        and parameter.default is not None
    ):
        inferred_from_default = _catalog_types.value_to_type_tag(
            parameter.default
        )
        if inferred_from_default in {
            'bool', 'int', 'float', 'str', 'list', 'dict', 'set', 'range',
        }:
            param_type = inferred_from_default
    return param_type


def _format_parameter(parameter: inspect.Parameter) -> str:
    """Return readable signature text for one parameter."""
    if parameter.kind == inspect.Parameter.VAR_POSITIONAL:
        text = f'*{parameter.name}'
    elif parameter.kind == inspect.Parameter.VAR_KEYWORD:
        text = f'**{parameter.name}'
    else:
        text = parameter.name
    annotation_text = _annotation_text(parameter.annotation)
    if annotation_text:
        text = f'{text}: {annotation_text}'
    if (
        parameter.default is not inspect.Parameter.empty
        and parameter.kind
        not in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        )
    ):
        text = f'{text} = {parameter.default!r}'
    return text


def _signature_metadata(
    signature: inspect.Signature,
    *,
    skip_bound_first: bool = False,
) -> tuple[list[str], list[str], int, int | None, list[str]]:
    """Return names, types, min/max counts, and display params."""
    positional_params: list[str] = []
    param_types: list[str] = []
    display_params: list[str] = []
    min_args = 0
    has_var = False
    skipped_first = False
    for parameter in signature.parameters.values():
        if (
            skip_bound_first
            and not skipped_first
            and parameter.name in {'self', 'cls'}
            and parameter.kind
            in (
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
            )
        ):
            skipped_first = True
            continue
        skipped_first = True
        if parameter.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ):
            has_var = True
            display_params.append(_format_parameter(parameter))
            continue
        if parameter.kind == inspect.Parameter.KEYWORD_ONLY:
            display_params.append(_format_parameter(parameter))
            continue
        positional_params.append(parameter.name)
        param_types.append(_parameter_type_tag(parameter))
        display_params.append(_format_parameter(parameter))
        if parameter.default is inspect.Parameter.empty:
            min_args += 1
    max_args: int | None = None if has_var else len(positional_params)
    return positional_params, param_types, min_args, max_args, display_params


def _introspect_entry(
    path: str,
    fn: Any,
    module_key: str = '',
) -> _catalog_models.FuncEntry | None:
    """Build a FuncEntry by introspecting callable *fn* at *path*."""
    label = path.rsplit('.', 1)[-1]
    return_type = 'any'
    try:
        signature = inspect.signature(fn)
        (
            positional_params,
            param_types,
            min_args,
            max_args,
            display_params,
        ) = _signature_metadata(signature)
        signature_text = f'{path}({", ".join(display_params)})'
        return_annotation_text = _annotation_text(signature.return_annotation)
        if return_annotation_text:
            signature_text = f'{signature_text} -> {return_annotation_text}'
        ann = _catalog_types.return_annotation_to_tag(
            signature.return_annotation
        )
        return_type = ann
    except (ValueError, TypeError):
        positional_params = []
        param_types = []
        min_args = 1
        max_args = None
        signature_text = f'{path}(...)'
    # For class callables the return annotation of __init__/__new__ is never
    # the class itself.  Derive the type tag from the class name instead.
    if inspect.isclass(fn) and return_type in ('any', 'object'):
        class_tag = _catalog_types.RETURN_TYPE_MAP.get(fn.__name__)
        return_type = class_tag if class_tag else 'object'
    return _catalog_models.FuncEntry(
        path=path,
        label=label,
        signature=signature_text,
        min_args=min_args,
        max_args=max_args,
        param_names=tuple(positional_params),
        param_types=tuple(param_types),
        return_type=return_type,
        is_class=inspect.isclass(fn),
    )


def _scan_module(
    loaded_module: _catalog_modules.LoadedCatalogModule,
    module: Any,
    prefix: str,
) -> list[_catalog_models.FuncEntry]:
    """Return FuncEntry list for all useful public callables in *module*."""
    module_blacklist = loaded_module.spec.blacklist
    entries: list[_catalog_models.FuncEntry] = []
    for name in sorted(dir(module)):
        if name in _catalog_modules.GLOBAL_BLACKLIST:
            continue
        if name in module_blacklist or name.startswith('_'):
            continue
        try:
            obj = getattr(module, name)
        except AttributeError:
            continue
        if not _is_useful_callable(name, obj, loaded_module.spec):
            continue
        entry = _introspect_entry(
            f'{prefix}{name}',
            obj,
            loaded_module.spec.key,
        )
        if entry is not None:
            entries.append(entry)
    return entries


@functools.lru_cache(maxsize=1)
def _build_catalog() -> dict[str, list[_catalog_models.FuncEntry]]:
    """Discover catalog entries by introspecting loaded catalog globals."""
    catalog: dict[str, list[_catalog_models.FuncEntry]] = {}
    for loaded_module in _catalog_modules.available_modules():
        entries: list[_catalog_models.FuncEntry] = []
        for target, prefix in _catalog_modules.scan_targets(loaded_module):
            entries.extend(_scan_module(loaded_module, target, prefix))
        catalog[loaded_module.spec.key] = entries
    return catalog


def clear_catalog_runtime_caches() -> None:
    """Clear cached catalog runtime lookups after module registration."""
    _build_catalog.cache_clear()
    class_methods.cache_clear()
    class_attributes.cache_clear()
    method_func_entry.cache_clear()


def catalog_entry(path: str) -> _catalog_models.FuncEntry | None:
    """Return the FuncEntry for a given path, or None if not found."""
    for entries in _build_catalog().values():
        for entry in entries:
            if entry.path == path:
                return entry
    return None


def class_options(module_key: str) -> dict[str, str]:
    """Return {path: label} dict for class or type entries in *module_key*."""
    return {
        entry.path: entry.label
        for entry in _build_catalog().get(module_key, [])
        if entry.is_class
    }


def func_options(module_key: str) -> dict[str, str]:
    """Return {func.path: 'label - signature'} for functions in a module."""
    return {
        entry.path: (
            f'{entry.label} - {entry.signature}'
            + (' - class' if entry.is_class else '')
        )
        for entry in _build_catalog().get(module_key, [])
    }


def _class_object(class_path: str) -> type | None:
    """Return the runtime class object for *class_path*, or None."""
    if class_path in {_catalog_types.NDARRAY_TYPE_TAG, 'numpy.ndarray'}:
        np_module = _catalog_modules.catalog_module_object('np')
        ndarray_cls = getattr(np_module, 'ndarray', None) if np_module else None
        return ndarray_cls if isinstance(ndarray_cls, type) else None
    entry = catalog_entry(class_path)
    if entry is None or not entry.is_class:
        return None
    module_key = _catalog_modules.path_to_module(class_path)
    module_obj = _catalog_modules.catalog_module_object(module_key)
    if module_obj is None:
        return None
    attr_path = _catalog_modules.strip_module_prefix(module_key, class_path)
    obj = _catalog_modules.resolve_attr_path(module_obj, attr_path)
    return obj if isinstance(obj, type) else None


@functools.lru_cache(maxsize=256)
def class_methods(class_path: str) -> dict[str, str]:
    """Return {method_name: signature_label} for public callable members."""
    cls = _class_object(class_path)
    if cls is None:
        return {}
    result: dict[str, str] = {}
    for name in sorted(dir(cls)):
        if name.startswith('_'):
            continue
        try:
            obj = getattr(cls, name)
        except AttributeError:
            continue
        if not callable(obj):
            continue
        try:
            signature = inspect.signature(obj)
            _positional, _types, _min_args, _max_args, display_params = (
                _signature_metadata(signature, skip_bound_first=True)
            )
            label = f'{name}({", ".join(display_params)})'
            return_annotation_text = _annotation_text(
                signature.return_annotation
            )
            if return_annotation_text:
                label = f'{label} -> {return_annotation_text}'
        except (ValueError, TypeError):
            label = name
        result[name] = label
    return result


def _class_can_be_called_without_args(
    class_path: str,
    cls: type,
) -> bool:
    """Return True when instance scanning is safe to attempt for *cls*."""
    if _catalog_modules.path_to_module(class_path) == 'builtins':
        return False
    try:
        signature = inspect.signature(cls)
    except (ValueError, TypeError):
        return True
    for parameter in signature.parameters.values():
        if parameter.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ):
            continue
        if parameter.default is inspect.Parameter.empty:
            return False
    return True


def _declared_public_attribute_names(cls: type) -> tuple[str, ...]:
    """Return declared public attribute names for one class."""
    names: dict[str, None] = {}
    if dataclasses.is_dataclass(cls):
        try:
            for field in dataclasses.fields(cls):
                field_name = str(field.name or '').strip()
                if field_name and not field_name.startswith('_'):
                    names.setdefault(field_name, None)
        except TypeError:
            pass
    namedtuple_fields = getattr(cls, '_fields', ())
    if isinstance(namedtuple_fields, tuple):
        for field_name in namedtuple_fields:
            clean_name = str(field_name or '').strip()
            if clean_name and not clean_name.startswith('_'):
                names.setdefault(clean_name, None)
    for klass in reversed(cls.__mro__):
        annotations = getattr(klass, '__annotations__', None)
        if isinstance(annotations, dict):
            for field_name in annotations:
                clean_name = str(field_name or '').strip()
                if clean_name and not clean_name.startswith('_'):
                    names.setdefault(clean_name, None)
        raw_slots = getattr(klass, '__slots__', ())
        if isinstance(raw_slots, str):
            slot_names = (raw_slots,)
        else:
            try:
                slot_names = tuple(raw_slots or ())
            except TypeError:
                slot_names = ()
        for slot_name in slot_names:
            clean_name = str(slot_name or '').strip()
            if clean_name and not clean_name.startswith('_'):
                names.setdefault(clean_name, None)
    return tuple(names)


@functools.lru_cache(maxsize=256)
def class_attributes(class_path: str) -> dict[str, str]:
    """Return {attr_name: attr_name} for non-callable public members."""
    cls = _class_object(class_path)
    if cls is None:
        return {}
    result: dict[str, str] = {
        name: name for name in _declared_public_attribute_names(cls)
    }
    if _class_can_be_called_without_args(class_path, cls):
        try:
            instance = cls()
            try:
                instance_items = vars(instance).items()
            except TypeError:
                instance_items = ()
            for name, value in instance_items:
                if name.startswith('_'):
                    continue
                if not callable(value):
                    result[name] = name
        except Exception:  # pylint: disable=broad-except
            pass
    for name in sorted(dir(cls)):
        if name.startswith('_') or name in result:
            continue
        raw = None
        for klass in cls.__mro__:
            if name in klass.__dict__:
                raw = klass.__dict__[name]
                break
        if isinstance(raw, property):
            result[name] = name
            continue
        try:
            obj = getattr(cls, name)
        except AttributeError:
            continue
        if not callable(obj):
            result[name] = name
    return result


@functools.lru_cache(maxsize=512)
def method_func_entry(
    class_path: str,
    method_name: str,
) -> _catalog_models.FuncEntry | None:
    """Return FuncEntry for *method_name* on *class_path*."""
    cls = _class_object(class_path)
    if cls is None or not method_name:
        return None
    fn = getattr(cls, method_name, None)
    if fn is None or not callable(fn):
        return None
    try:
        signature = inspect.signature(fn)
        (
            positional_params,
            param_types,
            min_args,
            max_args,
            display_params,
        ) = _signature_metadata(signature, skip_bound_first=True)
        signature_text = (
            f'{class_path}.{method_name}'
            f'({", ".join(display_params)})'
        )
        return_type = _catalog_types.return_annotation_to_tag(
            signature.return_annotation
        )
        return_annotation_text = _annotation_text(signature.return_annotation)
        if return_annotation_text:
            signature_text = f'{signature_text} -> {return_annotation_text}'
    except (ValueError, TypeError):
        positional_params = []
        param_types = []
        min_args = 0
        max_args = None
        signature_text = f'{class_path}.{method_name}(...)'
        return_type = 'any'
    return _catalog_models.FuncEntry(
        path=f'{class_path}.{method_name}',
        label=method_name,
        signature=signature_text,
        min_args=min_args,
        max_args=max_args,
        param_names=tuple(positional_params),
        param_types=tuple(param_types),
        return_type=return_type,
        is_class=False,
    )