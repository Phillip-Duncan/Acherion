"""Catalog and editor-param helpers for visual-logic graph ops."""

# pyright: reportAttributeAccessIssue=false

from __future__ import annotations

import ast
import re
from typing import Any, Protocol, cast

from acherion.catalog import models as _catalog_models
from acherion.catalog import modules as _catalog_modules
from acherion.catalog import runtime as _catalog_runtime
from acherion.catalog import types as _catalog_types
from acherion.model import AcherionNode
from acherion.validation import (
    infer_ast_expr_type as _infer_custom_function_expr_type,
    validate_custom_function_source as _validate_custom_function_source,
)


class _InstancePathOwner(Protocol):
    def _node_by_id(self, node_id: str) -> AcherionNode | None:
        ...

    def _pure_node_id(self, source_id: str) -> str:
        ...

    def _source_pin_index(self, source_id: str) -> int:
        ...

    def _output_pin_specs(self, node: AcherionNode) -> list[dict[str, str]]:
        ...

    def _function_entry(self, path: str) -> Any:
        ...

    def _resolve_instance_class_path(
        self,
        source_id: str,
        _depth: int = 0,
    ) -> str:
        ...


class _GraphOpsCatalogMixin:
    """Catalog lookup and editor mutation helpers."""

    def _function_entry(self: Any, path: str) -> Any:
        """Return graph-local or built-in function catalog entry."""
        data = dict((self._graph.user_functions or {}).get(path) or {})
        if data:
            param_names = tuple(str(v) for v in (data.get('param_names') or []))
            param_types = tuple(str(v) for v in (data.get('param_types') or []))
            min_args = int(data.get('min_args') or 0)
            max_args = int(data.get('max_args') or min_args)
            label = str(data.get('label') or path.rsplit('.', 1)[-1])
            signature = str(data.get('signature') or f'{label}()')
            return_type = (
                str(data.get('return_type'))
                if 'return_type' in data
                else 'any'
            )
            return _catalog_models.FuncEntry(
                path=path,
                label=label,
                signature=signature,
                min_args=min_args,
                max_args=max_args,
                param_names=param_names,
                param_types=param_types,
                return_type=return_type,
                is_class=False,
            )
        return _catalog_runtime.catalog_entry(path)

    def _function_module_options(self: Any) -> dict[str, str]:
        """Return function-module options including extracted helpers."""
        options = _catalog_modules.module_options()
        if self._graph.user_functions:
            options['user'] = 'User functions'
        return options

    def _function_options(self: Any, module_key: str) -> dict[str, str]:
        """Return function options for a module, including user helpers."""
        if module_key == 'user':
            return {
                path: (
                    f"{str(data.get('label') or path.rsplit('.', 1)[-1])} - "
                    f"{str(data.get('signature') or path)}"
                )
                for path, data in sorted(self._graph.user_functions.items())
            }
        return _catalog_runtime.func_options(module_key)

    @staticmethod
    def _function_path_to_module(path: str) -> str:
        """Infer function module, including graph-local user helpers."""
        if path.startswith('user.'):
            return 'user'
        return _catalog_modules.path_to_module(path)

    @staticmethod
    def _sanitize_identifier(text: str, fallback: str) -> str:
        """Convert UI text into a valid Python identifier."""
        slug = re.sub(r'[^0-9a-zA-Z_]+', '_', text.strip().lower())
        slug = re.sub(r'_+', '_', slug).strip('_')
        if not slug:
            slug = fallback
        if slug[0].isdigit():
            slug = f'{fallback}_{slug}'
        return slug

    @staticmethod
    def _default_custom_function_source(function_name: str) -> str:
        """Return starter source for one custom function node."""
        return (
            f'def {function_name}(self):\n'
            '    return None\n'
        )

    @staticmethod
    def _format_custom_function_arg(
        argument: ast.arg,
        default_value: ast.AST | None,
    ) -> str:
        """Return a readable signature fragment for one argument."""
        text = argument.arg
        if argument.annotation is not None:
            text = f'{text}: {ast.unparse(argument.annotation)}'
        if default_value is not None:
            text = f'{text} = {ast.unparse(default_value)}'
        return text

    def _parse_custom_function_source(
        self: Any,
        source_code: str,
    ) -> tuple[dict[str, Any] | None, str]:
        """Parse one user-authored function definition into catalog metadata."""
        raw_source = str(source_code or '')
        if not raw_source.strip():
            return (None, 'Custom function source is required.')
        normalized_source = raw_source.rstrip() + '\n'
        try:
            module = ast.parse(normalized_source)
        except SyntaxError as exc:
            line_suffix = f' line {exc.lineno}' if exc.lineno else ''
            return (
                None,
                f'Custom function has a Python syntax error{line_suffix}: '
                f'{exc.msg}.',
            )
        if len(module.body) != 1 or not isinstance(
            module.body[0],
            ast.FunctionDef,
        ):
            return (
                None,
                'Define exactly one top-level function in a custom '
                'function node.',
            )
        function_def = module.body[0]
        if function_def.decorator_list:
            return (None, 'Custom function nodes do not support decorators.')
        if function_def.args.posonlyargs or function_def.args.kwonlyargs:
            return (
                None,
                'Custom function nodes support positional args only.',
            )
        if function_def.args.vararg is not None:
            return (None, 'Custom function nodes do not support *args yet.')
        if function_def.args.kwarg is not None:
            return (None, 'Custom function nodes do not support **kwargs.')

        positional_args = list(function_def.args.args)
        if not positional_args or positional_args[0].arg != 'self':
            return (
                None,
                'Custom function must start with def name(self, ...).',
            )

        param_args = positional_args[1:]
        defaults = list(function_def.args.defaults)
        default_start_index = len(positional_args) - len(defaults)
        signature_parts = ['self']
        param_types: list[str] = []
        for index, argument in enumerate(param_args, start=1):
            default_value = None
            if index >= default_start_index:
                default_value = defaults[index - default_start_index]
            signature_parts.append(
                self._format_custom_function_arg(argument, default_value)
            )
            param_type = 'any'
            if argument.annotation is not None:
                param_type = _catalog_types.annotation_to_tag(
                    ast.unparse(argument.annotation)
                )
            elif default_value is not None:
                param_type = _infer_custom_function_expr_type(default_value)
            param_types.append(param_type)

        return_annotation = ''
        return_type = 'any'
        if function_def.returns is not None:
            return_annotation = ast.unparse(function_def.returns)
            return_type = _catalog_types.return_annotation_to_tag(
                return_annotation
            )

        try:
            validation_result = _validate_custom_function_source(
                normalized_source,
            )
        except (SyntaxError, ValueError) as exc:
            return (None, str(exc))
        if return_type == 'any':
            return_type = validation_result.inferred_return_type

        signature = f"{function_def.name}({', '.join(signature_parts)})"
        if return_annotation:
            signature = f'{signature} -> {return_annotation}'

        min_args = max(0, len(param_args) - len(defaults))
        data = {
            'label': function_def.name,
            'signature': signature,
            'min_args': min_args,
            'max_args': len(param_args),
            'param_names': [argument.arg for argument in param_args],
            'param_types': param_types,
            'return_type': return_type,
            'source_code': normalized_source,
        }
        return (data, '')

    def _prepare_custom_function_data(
        self: Any,
        *,
        node_id: str,
        current_path: str,
        source_code: str,
    ) -> tuple[str | None, dict[str, Any] | None, str]:
        """Validate custom source and return its graph storage data."""
        data, error = self._parse_custom_function_source(source_code)
        if data is None:
            return (None, None, error)
        function_name = str(data.get('label') or '').strip()
        new_path = f'user.{function_name}'
        existing_data = dict(
            (self._graph.user_functions or {}).get(new_path) or {}
        )
        existing_owner = str(existing_data.get('owner_node_id') or '')
        if (
            new_path != current_path
            and existing_data
            and existing_owner not in {'', node_id}
        ):
            return (
                None,
                None,
                f'Custom function name "{function_name}" is already used.',
            )
        data['owner_node_id'] = node_id
        return (new_path, data, '')

    def _ensure_custom_function_entry(
        self: Any,
        node: AcherionNode,
    ) -> None:
        """Ensure a custom function node always has backing user code."""
        if node.kind != 'custom_function':
            return
        current_path = str(node.params.get('function_path') or '').strip()
        if not current_path.startswith('user.'):
            function_name = self._sanitize_identifier(
                str(node.title or ''),
                f'custom_function_{node.node_id}',
            )
            current_path = f'user.{function_name}'
            node.params['function_path'] = current_path
        node.params['module'] = 'user'
        existing_data = dict(
            (self._graph.user_functions or {}).get(current_path) or {}
        )
        if existing_data:
            if not str(existing_data.get('owner_node_id') or '').strip():
                existing_data['owner_node_id'] = node.node_id
                self._graph.user_functions[current_path] = existing_data
            return
        function_name = current_path.split('.', 1)[1]
        data, _error = self._parse_custom_function_source(
            self._default_custom_function_source(function_name)
        )
        if data is None:
            return
        data['owner_node_id'] = node.node_id
        self._graph.user_functions[current_path] = data

    def _cleanup_custom_function_entries(self: Any) -> None:
        """Drop owned user functions no longer referenced by any node."""
        referenced_paths = {
            str(node.params.get('function_path') or '').strip()
            for node in self._graph.nodes
            if str(node.params.get('function_path') or '').strip().startswith(
                'user.'
            )
        }
        self._graph.user_functions = {
            path: dict(data)
            for path, data in self._graph.user_functions.items()
            if not str((data or {}).get('owner_node_id') or '').strip()
            or path in referenced_paths
        }

    def _sync_custom_function_nodes(self: Any) -> None:
        """Ensure custom function nodes and user function storage stay aligned."""
        for node in self._graph.nodes:
            self._ensure_custom_function_entry(node)
        self._cleanup_custom_function_entries()

    def _set_param(
        self: Any,
        node: AcherionNode,
        key: str,
        value: Any,
    ) -> None:
        node.params[key] = value
        if (
            (node.kind == 'constant' and key == 'value_type')
            or (node.kind in {'op_arithmetic', 'op_logic'} and key == 'operator')
            or (node.kind == 'get_attribute' and key == 'attribute_name')
            or (node.kind == 'set_input' and key in {'target_key', 'component_kind'})
            or (node.kind == 'plot_figure' and key == 'figure_type')
        ):
            self._notify_change()
            return
        if node.kind == 'function_box' and key == 'function_name':
            self._notify_change()
            return
        self._persist_only()

    def _set_title(self: Any, node: AcherionNode, value: Any) -> None:
        node.title = str(value or '')
        if node.kind == 'function_box':
            node.params['function_name'] = self._sanitize_identifier(
                node.title,
                f'function_{node.node_id}',
            )
            self._notify_change()
            return
        self._notify_change()

    def _set_arg_count(
        self: Any,
        node: AcherionNode,
        value: Any,
    ) -> None:
        lower_bound = 0 if node.kind in {'call_function', 'make_list'} else 1
        arg_count = max(lower_bound, int(value or 0))
        if node.kind != 'make_list':
            arg_count = min(8, arg_count)
        arg_sources = list(node.params.get('arg_sources') or [])
        while len(arg_sources) < arg_count:
            arg_sources.append('')
        node.params['arg_sources'] = arg_sources[:arg_count]
        node.params['arg_count'] = arg_count
        self._notify_change()

    def _set_catalog_function(
        self: Any,
        node: AcherionNode,
        path: str,
    ) -> None:
        """Set function_path from catalog selection and sync arg_count."""
        entry = self._function_entry(path)
        node.params['function_path'] = path
        node.params['module'] = self._function_path_to_module(path)
        count = entry.min_args if entry else 1
        self._set_arg_count(node, count)

    def _set_catalog_module(
        self: Any,
        node: AcherionNode,
        module_key: str,
    ) -> None:
        """Switch module; clear function_path if it no longer belongs."""
        current_path = str(node.params.get('function_path') or '')
        if current_path not in self._function_options(module_key):
            node.params['function_path'] = ''
            node.params['arg_count'] = 1
            node.params['arg_sources'] = ['']
        node.params['module'] = module_key
        self._notify_change()

    def _resolve_instance_class_path(
        self,
        source_id: str,
        _depth: int = 0,
    ) -> str:
        """Return class path tracing back through instance-producing nodes."""
        if not source_id or _depth > 5:
            return ''
        owner = cast(_InstancePathOwner, self)
        node = owner._node_by_id(owner._pure_node_id(source_id))
        if node is None:
            return ''
        pin_index = owner._source_pin_index(source_id)
        output_specs = owner._output_pin_specs(node)
        if pin_index < len(output_specs):
            pin_type = str(output_specs[pin_index].get('type') or 'any')
            resolved_class_path = (
                _catalog_types.runtime_class_path_for_type_tag(pin_type)
            )
            if resolved_class_path:
                return resolved_class_path
        if node.kind == 'call_function':
            function_path = str(node.params.get('function_path') or '')
            entry = owner._function_entry(function_path) if function_path else None
            if entry is not None and bool(getattr(entry, 'is_class', False)):
                return function_path
        if node.kind in ('call_method', 'get_attribute'):
            instance_source = str(node.params.get('instance') or '')
            parent_class_path = owner._resolve_instance_class_path(
                instance_source,
                _depth + 1,
            )
            return parent_class_path
        return ''

    def _set_method_name(
        self: Any,
        node: AcherionNode,
        method_name: str,
        class_path: str,
    ) -> None:
        """Set method_name for call_method; pre-seed arg_sources from sig."""
        node.params['method_name'] = method_name
        entry = (
            _catalog_runtime.method_func_entry(class_path, method_name)
            if class_path else None
        )
        if entry:
            arg_sources = list(node.params.get('arg_sources') or [])
            while len(arg_sources) < entry.min_args:
                arg_sources.append('')
            node.params['arg_sources'] = arg_sources
        self._notify_change()