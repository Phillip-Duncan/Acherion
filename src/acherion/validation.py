"""Validation helpers for Acherion custom function nodes."""

from __future__ import annotations

import ast
import copy
import importlib
import inspect
import logging
import pathlib
import re
import types
import typing
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any

from acherion.catalog import modules as _catalog_modules
from acherion.catalog import types as _catalog_types
from acherion.code_validation import (
    CodeValidationSupport,
    collect_defined_names,
    find_undefined_load,
)


@dataclass(frozen=True)
class AcherionValidationExtension:
    """Host-registered runtime globals and reserved names for validation."""

    name: str
    protected_names: frozenset[str] = frozenset()
    runtime_globals: dict[str, Any] = field(default_factory=dict)
    runtime_global_loaders: dict[str, Callable[[], Any]] = field(
        default_factory=dict,
    )
    self_attributes: dict[str, Any] = field(default_factory=dict)


_REGISTERED_VALIDATION_EXTENSIONS: dict[str, AcherionValidationExtension] = {}

_BASE_RUNTIME_GLOBALS: dict[str, Any] = {
    'collections': importlib.import_module('collections'),
    'logging': logging,
    'pathlib': pathlib,
    're': re,
    'typing': typing,
}

_DEFAULT_VALIDATION_SELF_ATTRIBUTES: dict[str, Any] = {}


def register_acherion_validation_extension(
    extension: AcherionValidationExtension,
    *,
    replace: bool = False,
) -> None:
    """Register one host validation extension by stable name."""
    clean_name = str(extension.name or '').strip()
    if not clean_name:
        raise ValueError('Validation extension name is required.')
    if clean_name in _REGISTERED_VALIDATION_EXTENSIONS and not replace:
        raise ValueError(
            f'Validation extension already registered: {clean_name}'
        )
    _REGISTERED_VALIDATION_EXTENSIONS[clean_name] = extension
    _validation_support.cache_clear()
    _validation_runtime_globals.cache_clear()
    _validation_protected_names.cache_clear()
    _validation_self_attributes.cache_clear()


@lru_cache(maxsize=1)
def _validation_runtime_globals() -> dict[str, Any]:
    """Return merged runtime globals for custom-function validation."""
    runtime_globals = dict(_BASE_RUNTIME_GLOBALS)
    runtime_globals.update(_catalog_modules.runtime_global_bindings())
    for extension in _REGISTERED_VALIDATION_EXTENSIONS.values():
        for name, loader in extension.runtime_global_loaders.items():
            loaded = loader()
            if loaded is not None:
                runtime_globals[name] = loaded
        runtime_globals.update(extension.runtime_globals)
    runtime_globals.setdefault('logger', logging.getLogger(__name__))
    return runtime_globals


@lru_cache(maxsize=1)
def _validation_protected_names() -> frozenset[str]:
    """Return merged protected names for custom-function validation."""
    names = set(_validation_runtime_globals())
    for extension in _REGISTERED_VALIDATION_EXTENSIONS.values():
        names.update(extension.protected_names)
    return frozenset(names)


@lru_cache(maxsize=1)
def _validation_self_attributes() -> dict[str, Any]:
    """Return merged dummy-self attributes for runtime validation."""
    attrs = copy.deepcopy(_DEFAULT_VALIDATION_SELF_ATTRIBUTES)
    for extension in _REGISTERED_VALIDATION_EXTENSIONS.values():
        attrs.update(copy.deepcopy(extension.self_attributes))
    return attrs


@lru_cache(maxsize=1)
def _validation_support() -> CodeValidationSupport:
    """Return cached AST validation support for current extensions."""
    return CodeValidationSupport(
        protected_names=_validation_protected_names(),
        preimport_lines=(),
    )


@dataclass(frozen=True)
class CustomFunctionValidationResult:
    """Validation result for one custom function source snippet."""

    runtime_return_type: str = 'any'
    inferred_return_type: str = 'any'


def infer_ast_expr_type(node: ast.AST | None) -> str:
    """Return best-effort type tag for one AST expression."""
    if node is None:
        return 'any'
    if isinstance(node, ast.Constant):
        value = node.value
        return _catalog_types.value_to_type_tag(value)
    if isinstance(node, ast.List):
        return 'list'
    if isinstance(node, ast.Tuple):
        return 'list'
    if isinstance(node, ast.Set):
        return 'set'
    if isinstance(node, ast.Dict):
        return 'dict'
    if isinstance(node, (ast.Compare, ast.BoolOp)):
        return 'bool'
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return 'bool'
    if isinstance(node, ast.Call):
        func_name = _call_name(node.func)
        if func_name in {'bool', 'int', 'float', 'str', 'list', 'dict', 'set'}:
            return func_name
        if func_name == 'tuple':
            return 'list'
        if func_name == 'range':
            return 'range'
        if func_name in {'np.array', 'np.asarray', 'np.zeros', 'np.ones'}:
            return _catalog_types.NDARRAY_TYPE_TAG
        if func_name in {'go.Figure', 'plotly.subplots.make_subplots'}:
            return 'Figure'
    return 'any'


def _infer_ast_return_expr_type(node: ast.AST | None) -> str:
    """Return return-type tag for one return expression."""
    if node is None:
        return ''
    if isinstance(node, ast.Constant) and node.value is None:
        return ''
    return infer_ast_expr_type(node)


def validate_custom_function_source(
    source_code: str,
) -> CustomFunctionValidationResult:
    """Validate custom function source in the current runtime context."""
    raw_source = str(source_code or '')
    if not raw_source.strip():
        raise ValueError('Custom function source is required.')
    normalized_source = raw_source.rstrip() + '\n'
    try:
        module = ast.parse(normalized_source)
    except SyntaxError as exc:
        line = exc.lineno or 0
        raise SyntaxError(
            f'Syntax error on line {line or 1}: {exc.msg}'
        ) from exc

    function_def = _extract_single_function(module)
    if function_def is None:
        raise ValueError(
            'Define exactly one top-level function in a custom function '
            'node.'
        )

    _validation_support().validate_protected_name_writes(normalized_source)

    undefined_error = _undefined_name_in_function(function_def)
    if undefined_error is not None:
        raise ValueError(undefined_error)

    try:
        runtime_globals = _validation_exec_globals()
        exec(normalized_source, runtime_globals)  # pylint: disable=exec-used
    except Exception as exc:
        raise ValueError(f'Runtime error: {exc}') from exc

    function_object = runtime_globals.get(function_def.name)
    if not callable(function_object):
        raise ValueError(
            f'Validated function {function_def.name!r} was not created.'
        )

    runtime_return_type = _validate_function_runtime(function_object)
    annotation_return_type = 'any'
    if function_def.returns is not None:
        annotation_return_type = _catalog_types.return_annotation_to_tag(
            ast.unparse(function_def.returns)
        )
    body_return_type = _infer_return_type_from_body(function_def)
    inferred_return_type = next(
        (
            type_tag
            for type_tag in (
                annotation_return_type,
                runtime_return_type,
                body_return_type,
            )
            if type_tag not in {'any', ''}
        ),
        (
            ''
            if '' in {
                annotation_return_type,
                runtime_return_type,
                body_return_type,
            }
            else 'any'
        ),
    )
    return CustomFunctionValidationResult(
        runtime_return_type=runtime_return_type,
        inferred_return_type=inferred_return_type,
    )


def _extract_single_function(module: ast.Module) -> ast.FunctionDef | None:
    if len(module.body) != 1 or not isinstance(module.body[0], ast.FunctionDef):
        return None
    return module.body[0]


def _validation_exec_globals() -> dict[str, Any]:
    """Return merged globals for one custom-function validation run."""
    return {
        '__builtins__': __builtins__,
        '__name__': '_acherion_custom_function_validation',
        **_validation_runtime_globals(),
    }


def _validation_self() -> Any:
    """Return one dummy self object for runtime validation."""
    return types.SimpleNamespace(**copy.deepcopy(_validation_self_attributes()))


def _none_dummy_value() -> Any:
    return None


def _bool_dummy_value() -> bool:
    return False


def _int_dummy_value() -> int:
    return 0


def _float_dummy_value() -> float:
    return 0.0


def _str_dummy_value() -> str:
    return ''


def _list_dummy_value() -> list[Any]:
    return []


def _dict_dummy_value() -> dict[Any, Any]:
    return {}


def _set_dummy_value() -> set[Any]:
    return set()


def _range_dummy_value() -> range:
    return range(0)


def _figure_dummy_value() -> Any:
    try:
        plotly_graph_objects = _validation_runtime_globals().get('go')
        if plotly_graph_objects is None:
            return None
        return plotly_graph_objects.Figure()
    except Exception:
        return None


def _ndarray_dummy_value() -> Any:
    try:
        numpy_module = _validation_runtime_globals().get('np')
        if numpy_module is None:
            return []
        return numpy_module.array([])
    except Exception:
        return []


_DUMMY_VALUE_BUILDERS: dict[str, Callable[[], Any]] = {
    'bool': _bool_dummy_value,
    'int': _int_dummy_value,
    'float': _float_dummy_value,
    'str': _str_dummy_value,
    'list': _list_dummy_value,
    'dict': _dict_dummy_value,
    'set': _set_dummy_value,
    'range': _range_dummy_value,
    'Figure': _figure_dummy_value,
    _catalog_types.NDARRAY_TYPE_TAG: _ndarray_dummy_value,
}


def _validate_function_runtime(function_object: Any) -> str:
    """Call the validated function with dummy values to catch body errors."""
    try:
        signature = inspect.signature(function_object)
    except (TypeError, ValueError):
        return 'any'

    call_args: list[Any] = []
    for index, parameter in enumerate(signature.parameters.values()):
        if parameter.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
        ):
            continue
        if index == 0 and parameter.name == 'self':
            call_args.append(_validation_self())
            continue
        call_args.append(_dummy_value_for_parameter(parameter))

    try:
        result = function_object(*call_args)
    except (NameError, ImportError, AttributeError) as exc:
        raise ValueError(f'Error in function body: {exc}') from exc
    except Exception:
        return 'any'
    return _catalog_types.return_value_to_type_tag(result)


def _dummy_value_for_parameter(parameter: inspect.Parameter) -> Any:
    """Return a safe dummy value for one runtime validation parameter."""
    if parameter.default is not inspect.Parameter.empty:
        return parameter.default
    type_tag = _catalog_types.annotation_to_tag(parameter.annotation)
    builder = _DUMMY_VALUE_BUILDERS.get(type_tag, _none_dummy_value)
    return builder()


def _infer_return_type_from_body(function_def: ast.FunctionDef) -> str:
    """Infer return type from simple return expressions in the function body."""
    discovered_types: set[str] = set()
    saw_return = False
    saw_non_none_return = False
    for node in _walk_returns(function_def):
        saw_return = True
        if node.value is not None and not (
            isinstance(node.value, ast.Constant) and node.value.value is None
        ):
            saw_non_none_return = True
        inferred_type = _infer_ast_return_expr_type(node.value)
        if inferred_type not in {'', 'any'}:
            discovered_types.add(inferred_type)
    if len(discovered_types) == 1:
        return next(iter(discovered_types))
    if saw_non_none_return and not discovered_types:
        return 'any'
    if saw_return and not discovered_types:
        return ''
    if not saw_return:
        return ''
    return 'any'


def _walk_returns(root: ast.FunctionDef):
    """Yield return nodes without descending into nested scopes."""
    queue: deque[ast.AST] = deque(ast.iter_child_nodes(root))
    while queue:
        child = queue.popleft()
        if isinstance(child, ast.Return):
            yield child
        if isinstance(
            child,
            (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda),
        ):
            continue
        queue.extend(ast.iter_child_nodes(child))


def _undefined_name_in_function(function_def: ast.FunctionDef) -> str | None:
    """Return error string when function body uses an undefined name."""
    local_names: set[str] = {'self', function_def.name}
    collect_defined_names(function_def, local_names)
    all_defined = (
        _validation_support().python_builtins
        | _validation_protected_names()
        | local_names
    )
    return find_undefined_load(
        function_def,
        all_defined,
        context_label='custom function',
    )


def _call_name(node: ast.AST) -> str:
    """Return dotted function name for a call target when simple enough."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _call_name(node.value)
        return f'{base}.{node.attr}' if base else node.attr
    return ''


__all__ = [
    'AcherionValidationExtension',
    'CustomFunctionValidationResult',
    'infer_ast_expr_type',
    'register_acherion_validation_extension',
    'validate_custom_function_source',
]


