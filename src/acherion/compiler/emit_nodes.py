"""Shared node-emission helpers for visual-logic compilation."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from acherion.catalog import plotly as _catalog_plotly
from acherion.compiler.graph import (
    _FunctionBoxGraphView,
)
from acherion.compiler.utils import (
    _arg_exprs,
    _constant_literal,
    _input_param_expr,
    _list_index_expr,
    _safe_function_name,
)
from acherion.compiler.state import EmitState
from acherion.model import AcherionNode


_EmitNodeHandler = Callable[..., bool]
_UNARY_EXPR_TEMPLATES: dict[str, str] = {
    'negate': '-({source})',
    'round': 'round({source})',
}


def _emit_function_box_node(
    *,
    state: EmitState,
    node: AcherionNode,
    params: dict[str, Any],
    function_graph: _FunctionBoxGraphView,
    indent: str,
    var_name: str,
    runtime_self_name: str | None = 'self',
    helper_as_attribute: bool = True,
) -> bool:
    """Emit code for a function_box node when present."""
    if node.kind != 'function_box':
        return False

    helper_name = _safe_function_name(
        str(params.get('function_name') or node.title or node.node_id),
        f'function_{node.node_id}',
    )
    boundary_inputs = function_graph.boundary_input_sources(
        node.node_id,
    )
    args = [
        state.source_expr(source_id)
        for source_id in boundary_inputs
    ]
    return_source_ids = function_graph.boundary_output_sources(
        node.node_id,
    )
    call_args = list(args)
    if not helper_as_attribute and runtime_self_name is not None:
        call_args = [runtime_self_name, *call_args]
    call_target = (
        f'{runtime_self_name}.{helper_name}'
        if helper_as_attribute else helper_name
    )
    call_expr = f"{call_target}({', '.join(call_args)})"
    if not return_source_ids:
        state.lines.append(f'{indent}{call_expr}')
        return True
    if len(return_source_ids) == 1:
        state.lines.append(f'{indent}{var_name} = {call_expr}')
        state.store_source(return_source_ids[0], var_name)
        return True
    tuple_var = f'{var_name}_tuple'
    state.lines.append(f'{indent}{tuple_var} = {call_expr}')
    for out_index, source_id in enumerate(return_source_ids):
        out_var = f'{var_name}_{out_index + 1}'
        state.lines.append(f'{indent}{out_var} = {tuple_var}[{out_index}]')
        state.store_source(source_id, out_var)
    return True


def _emit_constant_node(
    *,
    state: EmitState,
    node: AcherionNode,
    params: dict[str, Any],
    indent: str,
    var_name: str,
    method_owner_name: str | None = 'self',
) -> bool:
    del method_owner_name
    state.lines.append(f'{indent}{var_name} = {_constant_literal(params)}')
    state.store(node.node_id, var_name)
    return True


def _emit_callable_node(
    *,
    state: EmitState,
    node: AcherionNode,
    params: dict[str, Any],
    indent: str,
    var_name: str,
    method_owner_name: str | None = 'self',
) -> bool:
    function_path = str(params.get('function_path') or '').strip()
    call_target = function_path
    if function_path.startswith('user.'):
        helper_name = function_path.split('.', 1)[1]
        call_target = (
            f'{method_owner_name}.{helper_name}'
            if method_owner_name else helper_name
        )
    args = _arg_exprs(params, state.node_vars)
    result_var_name = var_name
    if call_target and '.' not in call_target and call_target == var_name:
        result_var_name = f'{var_name}_result'
    if call_target:
        state.lines.append(
            f"{indent}{result_var_name} = {call_target}({', '.join(args)})"
        )
    else:
        state.lines.append(
            f'{indent}{result_var_name} = None  # Set a function path.'
        )
    state.store(node.node_id, result_var_name)
    return True


def _emit_call_method_node(
    *,
    state: EmitState,
    node: AcherionNode,
    params: dict[str, Any],
    indent: str,
    var_name: str,
    method_owner_name: str | None = 'self',
) -> bool:
    del method_owner_name
    instance_id = str(params.get('instance') or '').strip()
    method_name = str(params.get('method_name') or '').strip()
    instance_expr = state.source_expr(instance_id)
    args = _arg_exprs(params, state.node_vars)
    if instance_id and method_name:
        state.lines.append(
            f"{indent}{var_name} = "
            f"{instance_expr}.{method_name}({', '.join(args)})"
        )
    else:
        state.lines.append(
            f'{indent}{var_name} = None'
            f'  # Connect instance and set method name.'
        )
    state.store(node.node_id, var_name)
    return True


def _emit_get_attribute_node(
    *,
    state: EmitState,
    node: AcherionNode,
    params: dict[str, Any],
    indent: str,
    var_name: str,
    method_owner_name: str | None = 'self',
) -> bool:
    del method_owner_name
    instance_id = str(params.get('instance') or '').strip()
    attr_name = str(params.get('attribute_name') or '').strip()
    instance_expr = state.source_expr(instance_id)
    if instance_id and attr_name:
        state.lines.append(
            f'{indent}{var_name} = {instance_expr}.{attr_name}'
        )
    else:
        state.lines.append(
            f'{indent}{var_name} = None'
            f'  # Connect instance and set attribute name.'
        )
    state.store(node.node_id, var_name)
    return True


def _emit_set_attribute_node(
    *,
    state: EmitState,
    node: AcherionNode,
    params: dict[str, Any],
    indent: str,
    var_name: str,
    method_owner_name: str | None = 'self',
) -> bool:
    del var_name, method_owner_name
    instance_id = str(params.get('instance') or '').strip()
    attr_name = str(params.get('attribute_name') or '').strip()
    instance_expr = state.source_expr(instance_id)
    value_expr = _input_param_expr(
        params,
        'value',
        state.node_vars,
    )
    if instance_id and attr_name:
        state.lines.append(
            f'{indent}{instance_expr}.{attr_name} = {value_expr}'
        )
    else:
        state.lines.append(
            f'{indent}pass'
            f'  # Connect instance and set attribute name.'
        )
    return True


def _emit_for_each_node(
    *,
    state: EmitState,
    node: AcherionNode,
    params: dict[str, Any],
    indent: str,
    var_name: str,
    method_owner_name: str | None = 'self',
) -> bool:
    del var_name, method_owner_name
    list_id = str(params.get('list') or '').strip()
    list_expr = state.source_expr(list_id)
    item_var = f'_item_{node.node_id}'
    idx_var = f'_idx_{node.node_id}'
    state.store(node.node_id, item_var)
    state.store(node.node_id, item_var, 0)
    state.store(node.node_id, idx_var, 1)
    state.lines.append(
        f'{indent}for {idx_var}, {item_var} in enumerate({list_expr}):'
    )
    return True


def _emit_collect_node(
    *,
    state: EmitState,
    node: AcherionNode,
    params: dict[str, Any],
    indent: str,
    var_name: str,
    method_owner_name: str | None = 'self',
) -> bool:
    del node, method_owner_name
    value_expr = _input_param_expr(
        params,
        'value',
        state.node_vars,
    )
    state.lines.append(f'{indent}{var_name}.append({value_expr})')
    return True


def _emit_compare_node(
    *,
    state: EmitState,
    node: AcherionNode,
    params: dict[str, Any],
    indent: str,
    var_name: str,
    method_owner_name: str | None = 'self',
) -> bool:
    del method_owner_name
    left_expr = _input_param_expr(
        params,
        'left_source',
        state.node_vars,
    )
    right_expr = _input_param_expr(
        params,
        'right_source',
        state.node_vars,
    )
    operator = str(params.get('operator') or '>')
    state.lines.append(
        f'{indent}{var_name} = ({left_expr} {operator} {right_expr})'
    )
    state.store(node.node_id, var_name)
    return True


def _emit_branch_value_node(
    *,
    state: EmitState,
    node: AcherionNode,
    params: dict[str, Any],
    indent: str,
    var_name: str,
    method_owner_name: str | None = 'self',
) -> bool:
    del method_owner_name
    cond = _input_param_expr(
        params,
        'condition_source',
        state.node_vars,
        fallback='False',
    )
    true_expr = _input_param_expr(
        params,
        'true_source',
        state.node_vars,
    )
    false_expr = _input_param_expr(
        params,
        'false_source',
        state.node_vars,
    )
    state.lines.append(
        f'{indent}{var_name} = '
        f'{true_expr} if bool({cond}) else {false_expr}'
    )
    state.store(node.node_id, var_name)
    return True


def _emit_op_arithmetic_node(
    *,
    state: EmitState,
    node: AcherionNode,
    params: dict[str, Any],
    indent: str,
    var_name: str,
    method_owner_name: str | None = 'self',
) -> bool:
    del method_owner_name
    operator = str(params.get('operator') or '+')
    left = _input_param_expr(
        params,
        'left_source',
        state.node_vars,
    )
    right = _input_param_expr(
        params,
        'right_source',
        state.node_vars,
    )
    state.lines.append(
        f'{indent}{var_name} = ({left}) {operator} ({right})'
    )
    state.store(node.node_id, var_name)
    return True


def _emit_op_unary_node(
    *,
    state: EmitState,
    node: AcherionNode,
    params: dict[str, Any],
    indent: str,
    var_name: str,
    method_owner_name: str | None = 'self',
) -> bool:
    del method_owner_name
    func = str(params.get('function') or 'abs')
    src = _input_param_expr(
        params,
        'source',
        state.node_vars,
    )
    template = _UNARY_EXPR_TEMPLATES.get(func, '{func}({source})')
    expr = template.format(func=func, source=src)
    state.lines.append(f'{indent}{var_name} = {expr}')
    state.store(node.node_id, var_name)
    return True


def _emit_op_logic_node(
    *,
    state: EmitState,
    node: AcherionNode,
    params: dict[str, Any],
    indent: str,
    var_name: str,
    method_owner_name: str | None = 'self',
) -> bool:
    del method_owner_name
    operator = str(params.get('operator') or 'and')
    left = _input_param_expr(
        params,
        'left_source',
        state.node_vars,
        fallback='False',
    )
    right = _input_param_expr(
        params,
        'right_source',
        state.node_vars,
        fallback='False',
    )
    state.lines.append(
        f'{indent}{var_name} = bool({left}) {operator} bool({right})'
    )
    state.store(node.node_id, var_name)
    return True


def _emit_op_not_node(
    *,
    state: EmitState,
    node: AcherionNode,
    params: dict[str, Any],
    indent: str,
    var_name: str,
    method_owner_name: str | None = 'self',
) -> bool:
    del method_owner_name
    src = _input_param_expr(
        params,
        'source',
        state.node_vars,
        fallback='False',
    )
    state.lines.append(f'{indent}{var_name} = not bool({src})')
    state.store(node.node_id, var_name)
    return True


def _emit_make_list_node(
    *,
    state: EmitState,
    node: AcherionNode,
    params: dict[str, Any],
    indent: str,
    var_name: str,
    method_owner_name: str | None = 'self',
) -> bool:
    del method_owner_name
    arg_count = max(0, int(params.get('arg_count', 0) or 0))
    args = _arg_exprs(
        params,
        state.node_vars,
        arg_count=arg_count,
    )
    state.lines.append(f"{indent}{var_name} = [{', '.join(args)}]")
    state.store(node.node_id, var_name)
    return True


def _emit_make_dict_node(
    *,
    state: EmitState,
    node: AcherionNode,
    params: dict[str, Any],
    indent: str,
    var_name: str,
    method_owner_name: str | None = 'self',
) -> bool:
    del method_owner_name
    arg_count = max(0, int(params.get('arg_count', 0) or 0))
    args = _arg_exprs(
        params,
        state.node_vars,
        arg_count=arg_count,
    )
    key_names = list(params.get('key_names') or [])
    entries = []
    for index, expr in enumerate(args):
        default_key = f'key_{index + 1}'
        key_name = str(
            key_names[index] if index < len(key_names) else default_key
        ).strip() or default_key
        entries.append(f'{key_name!r}: {expr}')
    state.lines.append(f"{indent}{var_name} = {{{', '.join(entries)}}}")
    state.store(node.node_id, var_name)
    return True


def _emit_list_index_node(
    *,
    state: EmitState,
    node: AcherionNode,
    params: dict[str, Any],
    indent: str,
    var_name: str,
    method_owner_name: str | None = 'self',
) -> bool:
    del method_owner_name
    src = _input_param_expr(
        params,
        'source',
        state.node_vars,
    )
    state.lines.append(
        f'{indent}{var_name} = {_list_index_expr(src, params, state.node_vars)}'
    )
    state.store(node.node_id, var_name)
    return True


def _emit_list_set_node(
    *,
    state: EmitState,
    node: AcherionNode,
    params: dict[str, Any],
    indent: str,
    var_name: str,
    method_owner_name: str | None = 'self',
) -> bool:
    del method_owner_name
    source_expr = _input_param_expr(
        params,
        'source',
        state.node_vars,
        fallback='[]',
    )
    value_expr = _input_param_expr(
        params,
        'value',
        state.node_vars,
    )
    base_var = f'{var_name}_base'
    state.lines.append(f'{indent}{base_var} = {source_expr}')
    state.lines.append(
        f'{indent}{var_name} = ('
        f'{base_var}.copy() if hasattr({base_var}, "copy") else '
        f'(list({base_var}) if isinstance({base_var}, (list, tuple, range)) '
        f'else [])'
        f')'
    )
    state.lines.append(f'{indent}try:')
    state.lines.append(
        f'{indent}    {_list_index_expr(var_name, params, state.node_vars)} = {value_expr}'
    )
    state.lines.append(f'{indent}except (IndexError, TypeError, ValueError):')
    state.lines.append(f'{indent}    pass')
    state.store(node.node_id, var_name)
    return True


def _emit_dict_get_node(
    *,
    state: EmitState,
    node: AcherionNode,
    params: dict[str, Any],
    indent: str,
    var_name: str,
    method_owner_name: str | None = 'self',
) -> bool:
    del method_owner_name
    dict_expr = _input_param_expr(
        params,
        'source',
        state.node_vars,
    )
    key_expr = _input_param_expr(
        params,
        'key',
        state.node_vars,
        fallback="''",
    )
    default_expr = _input_param_expr(
        params,
        'default',
        state.node_vars,
        fallback='None',
    )
    dict_var = f'{var_name}_dict'
    state.lines.append(f'{indent}{dict_var} = {dict_expr}')
    state.lines.append(
        f'{indent}{var_name} = '
        f'{dict_var}.get({key_expr}, {default_expr}) '
        f'if isinstance({dict_var}, dict) else {default_expr}'
    )
    state.store(node.node_id, var_name)
    return True


def _emit_dict_set_node(
    *,
    state: EmitState,
    node: AcherionNode,
    params: dict[str, Any],
    indent: str,
    var_name: str,
    method_owner_name: str | None = 'self',
) -> bool:
    del method_owner_name
    dict_expr = _input_param_expr(
        params,
        'source',
        state.node_vars,
    )
    key_expr = _input_param_expr(
        params,
        'key',
        state.node_vars,
        fallback="''",
    )
    value_expr = _input_param_expr(
        params,
        'value',
        state.node_vars,
    )
    base_var = f'{var_name}_base'
    state.lines.append(f'{indent}{base_var} = {dict_expr}')
    state.lines.append(
        f'{indent}{var_name} = '
        f'dict({base_var}) if isinstance({base_var}, dict) else {{}}'
    )
    state.lines.append(f'{indent}{var_name}[{key_expr}] = {value_expr}')
    state.store(node.node_id, var_name)
    return True


def _emit_plot_figure_node(
    *,
    state: EmitState,
    node: AcherionNode,
    params: dict[str, Any],
    indent: str,
    var_name: str,
    method_owner_name: str | None = 'self',
) -> bool:
    del method_owner_name
    figure_type = str(params.get('figure_type') or 'scatter')
    named_sources = dict(params.get('named_sources') or {})
    figure_title = str(params.get('figure_title') or '').strip()
    trace_entry = _catalog_plotly.trace_entry(figure_type)
    if trace_entry is None:
        state.lines.append(
            f'{indent}{var_name} = None  # unknown figure type'
        )
        state.store(node.node_id, var_name)
        return True
    connected: dict[str, str] = {}
    for trace_param in trace_entry.params:
        src_id = str(named_sources.get(trace_param.name) or '').strip()
        if src_id:
            connected[trace_param.name] = state.source_expr(src_id)
    gauge_min = connected.pop('gauge_axis_range_min', None)
    gauge_max = connected.pop('gauge_axis_range_max', None)
    err_y = connected.pop('error_y_array', None)
    kw_parts: list[str] = []
    if figure_type == 'line' and 'mode' not in connected:
        kw_parts.append("mode='lines'")
    for param_name, expr in connected.items():
        kw_parts.append(f'{param_name}={expr}')
    if err_y is not None:
        kw_parts.append(f"error_y=dict(type='data', array={err_y})")
    if gauge_min is not None or gauge_max is not None:
        low = gauge_min or 'None'
        high = gauge_max or 'None'
        kw_parts.append(f'gauge=dict(axis=dict(range=[{low}, {high}]))')
    kw_str = ', '.join(kw_parts)
    state.lines.extend([
        f'{indent}{var_name} = go.Figure('
        f'data=[{trace_entry.go_class}({kw_str})])',
    ])
    if figure_title:
        state.lines.append(
            f"{indent}{var_name}.update_layout(title_text={figure_title!r})"
        )
    state.store(node.node_id, var_name)
    return True


_COMPUTE_NODE_EMITTERS: dict[str, _EmitNodeHandler] = {
    'constant': _emit_constant_node,
    'call_function': _emit_callable_node,
    'custom_function': _emit_callable_node,
    'call_method': _emit_call_method_node,
    'get_attribute': _emit_get_attribute_node,
    'set_attribute': _emit_set_attribute_node,
    'for_each': _emit_for_each_node,
    'collect': _emit_collect_node,
    'compare': _emit_compare_node,
    'branch_value': _emit_branch_value_node,
    'op_arithmetic': _emit_op_arithmetic_node,
    'op_unary': _emit_op_unary_node,
    'op_logic': _emit_op_logic_node,
    'op_not': _emit_op_not_node,
    'make_list': _emit_make_list_node,
    'make_dict': _emit_make_dict_node,
    'list_index': _emit_list_index_node,
    'list_set': _emit_list_set_node,
    'dict_get': _emit_dict_get_node,
    'dict_set': _emit_dict_set_node,
    'plot_figure': _emit_plot_figure_node,
}


def _emit_common_compute_node(
    *,
    state: EmitState,
    node: AcherionNode,
    params: dict[str, Any],
    indent: str,
    var_name: str,
    method_owner_name: str | None = 'self',
) -> bool:
    """Emit code for node kinds shared by helper and top-level compilers."""
    handler = _COMPUTE_NODE_EMITTERS.get(node.kind)
    if handler is None:
        return False
    return handler(
        state=state,
        node=node,
        params=params,
        indent=indent,
        var_name=var_name,
        method_owner_name=method_owner_name,
    )
