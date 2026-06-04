"""Pure helper utilities for visual-logic code generation."""

from __future__ import annotations

import ast
from collections.abc import Callable
import re
from typing import Any


_MISSING = object()
_ConstantLiteralBuilder = Callable[[dict[str, Any]], str]


def _source_expr(
    source_id: str | None,
    node_vars: dict[str, str],
    *,
    fallback: str = 'None',
) -> str:
    """Resolve a node reference to a generated Python expression."""
    if not source_id:
        return fallback
    return node_vars.get(str(source_id), fallback)


def _literal_expr(value: Any, *, fallback: str = 'None') -> str:
    """Return a safe Python literal expression for one stored value."""
    if value is _MISSING or value in (None, ''):
        return fallback
    if isinstance(value, bool):
        return 'True' if value else 'False'
    return repr(value)


def _pin_literal_expr(
    params: dict[str, Any],
    pin_id: str,
    *,
    fallback: str = 'None',
) -> str:
    """Return one stored literal fallback expression for an input pin."""
    raw_literals = params.get('pin_literals')
    if not isinstance(raw_literals, dict):
        return fallback
    return _literal_expr(raw_literals.get(pin_id, _MISSING), fallback=fallback)


def _param_source_id(
    params: dict[str, Any],
    pin_id: str,
) -> str:
    """Return stored source id for one input pin."""
    if pin_id.startswith('arg:'):
        arg_index = int(pin_id.split(':', 1)[1])
        arg_sources = list(params.get('arg_sources') or [])
        if arg_index >= len(arg_sources):
            return ''
        return str(arg_sources[arg_index] or '')
    if pin_id.startswith('named:'):
        param_name = pin_id.split(':', 1)[1]
        named_sources = dict(params.get('named_sources') or {})
        return str(named_sources.get(param_name) or '')
    return str(params.get(pin_id) or '')


def _input_param_expr(
    params: dict[str, Any],
    pin_id: str,
    node_vars: dict[str, str],
    *,
    fallback: str = 'None',
) -> str:
    """Return connected source expression with stored literal fallback."""
    source_id = _param_source_id(params, pin_id)
    literal_expr = _pin_literal_expr(params, pin_id, fallback=fallback)
    return _source_expr(source_id, node_vars, fallback=literal_expr)


def _arg_exprs(
    params: dict[str, Any],
    node_vars: dict[str, str],
    *,
    arg_count: int | None = None,
) -> list[str]:
    """Return positional arg expressions with stored literal fallbacks."""
    arg_sources = list(params.get('arg_sources') or [])
    max_count = len(arg_sources)
    raw_literals = params.get('pin_literals')
    if isinstance(raw_literals, dict):
        for pin_id in raw_literals:
            text = str(pin_id)
            if not text.startswith('arg:'):
                continue
            try:
                arg_index = int(text.split(':', 1)[1])
            except (TypeError, ValueError):
                continue
            max_count = max(max_count, arg_index + 1)
    if arg_count is not None:
        max_count = max(max_count, arg_count)
    if arg_count is None:
        while max_count > 0:
            pin_id = f'arg:{max_count - 1}'
            source_id = _param_source_id(params, pin_id)
            literal_expr = _pin_literal_expr(params, pin_id, fallback='')
            if source_id or literal_expr:
                break
            max_count -= 1
    return [
        _input_param_expr(
            params,
            f'arg:{index}',
            node_vars,
        )
        for index in range(max_count)
    ]


def _text_constant_literal(params: dict[str, Any]) -> str:
    return repr(str(params.get('text_value') or ''))


def _bool_constant_literal(params: dict[str, Any]) -> str:
    return 'True' if bool(params.get('bool_value')) else 'False'


def _int_constant_literal(params: dict[str, Any]) -> str:
    number_value = params.get('number_value', 0)
    try:
        return repr(int(float(number_value)))
    except (TypeError, ValueError):
        return '0'


def _dict_constant_literal(params: dict[str, Any]) -> str:
    raw = str(params.get('dict_value') or '{}').strip()
    if not raw:
        return '{}'
    try:
        parsed = ast.literal_eval(raw)
    except (SyntaxError, ValueError):
        return '{}'
    return repr(parsed) if isinstance(parsed, dict) else '{}'


def _number_constant_literal(params: dict[str, Any]) -> str:
    number_value = params.get('number_value', 0.0)
    try:
        return repr(float(number_value))
    except (TypeError, ValueError):
        return '0.0'


_CONSTANT_LITERAL_BUILDERS: dict[str, _ConstantLiteralBuilder] = {
    'text': _text_constant_literal,
    'bool': _bool_constant_literal,
    'int': _int_constant_literal,
    'dict': _dict_constant_literal,
}


def _constant_literal(params: dict[str, Any]) -> str:
    """Return the Python literal expression for a constant node."""
    value_type = str(params.get('value_type') or 'number')
    builder = _CONSTANT_LITERAL_BUILDERS.get(
        value_type,
        _number_constant_literal,
    )
    return builder(params)


def _optional_index_text(value: Any) -> str:
    """Return a safe integer literal string or empty for blank values."""
    if value in (None, ''):
        return ''
    try:
        return str(int(value))
    except (TypeError, ValueError):
        return ''


def _optional_positive_int_text(value: Any) -> str:
    """Return a positive integer literal string or empty for blank values."""
    text = _optional_index_text(value)
    if not text:
        return ''
    return text if int(text) > 0 else ''


def _list_index_bound_expr(
    params: dict[str, Any],
    pin_id: str,
    node_vars: dict[str, str] | None,
    *,
    fallback: str = '',
) -> str:
    """Return one list index/slice bound expression from pins or legacy params."""
    if node_vars is not None:
        raw_source = params.get(pin_id)
        source_id = (
            str(raw_source or '').strip()
            if isinstance(raw_source, str)
            else ''
        )
        if source_id and (
            source_id in node_vars
            or not _optional_index_text(source_id)
        ):
            return _source_expr(source_id, node_vars, fallback=fallback)
        raw_literals = params.get('pin_literals')
        if isinstance(raw_literals, dict) and pin_id in raw_literals:
            text = _optional_index_text(raw_literals.get(pin_id))
            return text or fallback
    text = _optional_index_text(params.get(pin_id))
    return text or fallback


def _list_index_expr(
    source_expr: str,
    params: dict[str, Any],
    node_vars: dict[str, str] | None = None,
) -> str:
    """Return Python list or ndarray indexing or slicing expression."""
    mode = str(params.get('mode') or 'index').strip()
    if mode != 'slice':
        index = _list_index_bound_expr(
            params,
            'index',
            node_vars,
            fallback='0',
        )
        return f'{source_expr}[{index}]'

    start = _list_index_bound_expr(params, 'start', node_vars)
    stop = _list_index_bound_expr(params, 'stop', node_vars)
    step = _list_index_bound_expr(params, 'step', node_vars)
    if step == '0':
        step = ''
    slice_expr = f'{start}:{stop}'
    if step:
        slice_expr += f':{step}'
    return f'{source_expr}[{slice_expr}]'


def _safe_function_name(text: str, fallback: str) -> str:
    """Convert UI labels to valid helper function names."""
    slug = re.sub(r'[^0-9a-zA-Z_]+', '_', text.strip().lower())
    slug = re.sub(r'_+', '_', slug).strip('_')
    if not slug:
        slug = fallback
    if slug[0].isdigit():
        slug = f'{fallback}_{slug}'
    return slug


def _add_missing_pass(lines: list[str]) -> list[str]:
    """Insert pass after any block header that has no indented body."""
    result: list[str] = []
    for i, line in enumerate(lines):
        result.append(line)
        if not line.rstrip().endswith(':') or not line.strip():
            continue
        j = i + 1
        while j < len(lines) and not lines[j].strip():
            j += 1
        header_indent = len(line) - len(line.lstrip())
        if j >= len(lines):
            result.append(' ' * (header_indent + 4) + 'pass')
        else:
            next_indent = len(lines[j]) - len(lines[j].lstrip())
            if next_indent <= header_indent:
                result.append(' ' * (header_indent + 4) + 'pass')
    return result
