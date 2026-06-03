"""Integration tests for execution-flow code generation."""

from __future__ import annotations

import pytest

import acherion
import acherion.catalog.models as acherion_catalog_models
import acherion.catalog.runtime as acherion_catalog_runtime
import acherion.model as acherion_model

import tests.helpers as test_helpers


pytestmark = pytest.mark.integration


def test_else_if_branch_routes_to_first_matching_condition() -> None:
    graph = acherion_model.AcherionGraph(
        nodes=[
            acherion_model.AcherionNode(
                node_id='cond1',
                kind='constant',
                params={
                    'value_type': 'bool',
                    'bool_value': False,
                },
            ),
            acherion_model.AcherionNode(
                node_id='cond2',
                kind='constant',
                params={
                    'value_type': 'bool',
                    'bool_value': False,
                },
            ),
            acherion_model.AcherionNode(
                node_id='branch',
                kind='else_if_branch',
                params={
                    'condition_count': 3,
                    'condition:0': 'cond1',
                    'condition:1': 'cond2',
                    'pin_literals': {
                        'condition:1': True,
                        'condition:2': True,
                    },
                    'exec_sources': ['external_event:run'],
                },
            ),
            acherion_model.AcherionNode(
                node_id='label_if',
                kind='constant',
                params={
                    'value_type': 'text',
                    'text_value': 'if',
                },
            ),
            acherion_model.AcherionNode(
                node_id='label_elif2',
                kind='constant',
                params={
                    'value_type': 'text',
                    'text_value': 'elif2',
                },
            ),
            acherion_model.AcherionNode(
                node_id='label_elif3',
                kind='constant',
                params={
                    'value_type': 'text',
                    'text_value': 'elif3',
                },
            ),
            acherion_model.AcherionNode(
                node_id='label_else',
                kind='constant',
                params={
                    'value_type': 'text',
                    'text_value': 'else',
                },
            ),
            acherion_model.AcherionNode(
                node_id='mark_if',
                kind='custom_function',
                params={
                    'function_path': 'user.mark',
                    'module': 'user',
                    'arg_count': 1,
                    'arg_sources': ['label_if'],
                    'exec_sources': ['branch@0'],
                },
            ),
            acherion_model.AcherionNode(
                node_id='mark_elif2',
                kind='custom_function',
                params={
                    'function_path': 'user.mark',
                    'module': 'user',
                    'arg_count': 1,
                    'arg_sources': ['label_elif2'],
                    'exec_sources': ['branch@1'],
                },
            ),
            acherion_model.AcherionNode(
                node_id='mark_elif3',
                kind='custom_function',
                params={
                    'function_path': 'user.mark',
                    'module': 'user',
                    'arg_count': 1,
                    'arg_sources': ['label_elif3'],
                    'exec_sources': ['branch@2'],
                },
            ),
            acherion_model.AcherionNode(
                node_id='mark_else',
                kind='custom_function',
                params={
                    'function_path': 'user.mark',
                    'module': 'user',
                    'arg_count': 1,
                    'arg_sources': ['label_else'],
                    'exec_sources': ['branch@3'],
                },
            ),
        ],
        user_functions={
            'user.mark': {
                'label': 'mark',
                'signature': 'mark(value)',
                'min_args': 1,
                'max_args': 1,
                'param_names': ['value'],
                'param_types': ['str'],
                'return_type': 'dict',
                'source_code': (
                    'def mark(value):\n'
                    '    return {"branch": value}\n'
                ),
            },
        },
    )

    source_code = acherion.compile_acherion_graph(graph)
    local_values = acherion.execute_acherion_graph(source_code)

    assert source_code.count('elif bool(') == 2
    assert any(value == {'branch': 'elif3'} for value in local_values.values())
    assert not any(value == {'branch': 'if'} for value in local_values.values())
    assert not any(value == {'branch': 'elif2'} for value in local_values.values())
    assert not any(value == {'branch': 'else'} for value in local_values.values())


def test_exec_chain_accepts_plain_exec_source_alias_for_object_nodes() -> None:
    graph = acherion_model.AcherionGraph(
        nodes=[
            acherion_model.AcherionNode(
                node_id='f1',
                kind='call_function',
                params={
                    'function_path': 'go.Figure',
                    'module': 'go',
                    'arg_count': 0,
                    'arg_sources': [],
                    'exec_sources': ['external_event:run'],
                },
            ),
            acherion_model.AcherionNode(
                node_id='m1',
                kind='call_method',
                params={
                    'instance': 'f1',
                    'method_name': 'update_layout',
                    'arg_sources': [],
                    'exec_sources': ['f1@1'],
                },
            ),
            acherion_model.AcherionNode(
                node_id='a1',
                kind='get_attribute',
                params={
                    'instance': 'f1',
                    'attribute_name': 'layout',
                    'exec_sources': ['m1'],
                },
            ),
        ]
    )

    source_code = acherion.compile_acherion_graph(graph)

    assert test_helpers.run_has_assigned_method_call(
        source_code,
        'update_layout',
    )
    assert test_helpers.run_has_assigned_attribute_read(source_code, 'layout')


def test_exec_chain_accepts_canonical_pin_zero_exec_source_ids() -> None:
    graph = acherion_model.AcherionGraph(
        nodes=[
            acherion_model.AcherionNode(
                node_id='figure',
                kind='call_function',
                params={
                    'function_path': 'go.Figure',
                    'module': 'go',
                    'arg_count': 0,
                    'arg_sources': [],
                    'exec_sources': ['external_event:run'],
                },
            ),
            acherion_model.AcherionNode(
                node_id='value',
                kind='constant',
                params={
                    'value_type': 'text',
                    'text_value': 'Updated title',
                },
            ),
            acherion_model.AcherionNode(
                node_id='setter',
                kind='set_attribute',
                params={
                    'instance': 'figure',
                    'attribute_name': 'layout',
                    'value': 'value',
                    'exec_sources': ['figure@1'],
                },
            ),
            acherion_model.AcherionNode(
                node_id='getter',
                kind='get_attribute',
                params={
                    'instance': 'figure',
                    'attribute_name': 'layout',
                    'exec_sources': ['setter@0'],
                },
            ),
        ]
    )

    source_code = acherion.compile_acherion_graph(graph)

    assert test_helpers.run_contains_call(source_code, 'Figure')
    assert test_helpers.run_has_attribute_write(source_code, 'layout')
    assert test_helpers.run_has_assigned_attribute_read(source_code, 'layout')


def test_exec_chain_continues_after_exec_only_call_method(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _fake_catalog_entry(
        path: str,
    ) -> acherion_catalog_models.FuncEntry | None:
        if path == 'pkg.Widget':
            return acherion_catalog_models.FuncEntry(
                path='pkg.Widget',
                label='Widget',
                signature='Widget()',
                min_args=0,
                max_args=0,
                param_names=(),
                param_types=(),
                return_type='object',
                is_class=True,
            )
        return None

    def _fake_method_func_entry(
        class_path: str,
        method_name: str,
    ) -> acherion_catalog_models.FuncEntry | None:
        if class_path == 'pkg.Widget' and method_name == 'mutate':
            return acherion_catalog_models.FuncEntry(
                path='pkg.Widget.mutate',
                label='mutate',
                signature='mutate()',
                min_args=0,
                max_args=0,
                param_names=(),
                param_types=(),
                return_type='',
                is_class=False,
            )
        return None

    monkeypatch.setattr(
        acherion_catalog_runtime,
        'catalog_entry',
        _fake_catalog_entry,
    )
    monkeypatch.setattr(
        acherion_catalog_runtime,
        'method_func_entry',
        _fake_method_func_entry,
    )

    graph = acherion_model.AcherionGraph(
        nodes=[
            acherion_model.AcherionNode(
                node_id='obj',
                kind='call_function',
                params={
                    'function_path': 'pkg.Widget',
                    'module': 'pkg',
                    'arg_count': 0,
                    'arg_sources': [],
                    'exec_sources': ['external_event:run'],
                },
            ),
            acherion_model.AcherionNode(
                node_id='m1',
                kind='call_method',
                params={
                    'instance': 'obj',
                    'method_name': 'mutate',
                    'arg_sources': [],
                    'exec_sources': ['obj@1'],
                },
            ),
            acherion_model.AcherionNode(
                node_id='a1',
                kind='get_attribute',
                params={
                    'instance': 'obj',
                    'attribute_name': 'value',
                    'exec_sources': ['m1@0'],
                },
            ),
        ]
    )

    source_code = acherion.compile_acherion_graph(graph)

    assert test_helpers.run_contains_call(source_code, 'Widget')
    assert test_helpers.run_contains_call(source_code, 'mutate')
    assert test_helpers.run_has_assigned_attribute_read(source_code, 'value')


def test_exec_chain_continues_after_exec_only_method_on_method_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _fake_catalog_entry(
        path: str,
    ) -> acherion_catalog_models.FuncEntry | None:
        if path == 'pkg.Widget':
            return acherion_catalog_models.FuncEntry(
                path='pkg.Widget',
                label='Widget',
                signature='Widget()',
                min_args=0,
                max_args=0,
                param_names=(),
                param_types=(),
                return_type='object',
                is_class=True,
            )
        return None

    def _fake_method_func_entry(
        class_path: str,
        method_name: str,
    ) -> acherion_catalog_models.FuncEntry | None:
        if class_path == 'pkg.Widget' and method_name == 'items':
            return acherion_catalog_models.FuncEntry(
                path='pkg.Widget.items',
                label='items',
                signature='items()',
                min_args=0,
                max_args=0,
                param_names=(),
                param_types=(),
                return_type='list',
                is_class=False,
            )
        if class_path == 'list' and method_name == 'append':
            return acherion_catalog_models.FuncEntry(
                path='list.append',
                label='append',
                signature='append(object)',
                min_args=1,
                max_args=1,
                param_names=('object',),
                param_types=('any',),
                return_type='',
                is_class=False,
            )
        return None

    monkeypatch.setattr(
        acherion_catalog_runtime,
        'catalog_entry',
        _fake_catalog_entry,
    )
    monkeypatch.setattr(
        acherion_catalog_runtime,
        'method_func_entry',
        _fake_method_func_entry,
    )

    graph = acherion_model.AcherionGraph(
        nodes=[
            acherion_model.AcherionNode(
                node_id='obj',
                kind='call_function',
                params={
                    'function_path': 'pkg.Widget',
                    'module': 'pkg',
                    'arg_count': 0,
                    'arg_sources': [],
                    'exec_sources': ['external_event:run'],
                },
            ),
            acherion_model.AcherionNode(
                node_id='items',
                kind='call_method',
                params={
                    'instance': 'obj',
                    'method_name': 'items',
                    'arg_sources': [],
                    'exec_sources': ['obj@1'],
                },
            ),
            acherion_model.AcherionNode(
                node_id='value',
                kind='constant',
                params={
                    'value_type': 'int',
                    'number_value': 7,
                },
            ),
            acherion_model.AcherionNode(
                node_id='append',
                kind='call_method',
                params={
                    'instance': 'items',
                    'method_name': 'append',
                    'arg_sources': ['value'],
                    'exec_sources': ['items@1'],
                },
            ),
            acherion_model.AcherionNode(
                node_id='a1',
                kind='get_attribute',
                params={
                    'instance': 'obj',
                    'attribute_name': 'value',
                    'exec_sources': ['append@0'],
                },
            ),
        ]
    )

    source_code = acherion.compile_acherion_graph(graph)

    assert test_helpers.run_has_assigned_method_call(source_code, 'items')
    assert test_helpers.run_has_assigned_method_call(source_code, 'append')
    assert test_helpers.run_has_assigned_attribute_read(source_code, 'value')


def test_exec_chain_continues_after_exec_only_call_method_on_for_each_item(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _fake_catalog_entry(
        path: str,
    ) -> acherion_catalog_models.FuncEntry | None:
        if path == 'pkg.make_widgets':
            return acherion_catalog_models.FuncEntry(
                path='pkg.make_widgets',
                label='make_widgets',
                signature='pkg.make_widgets()',
                min_args=0,
                max_args=0,
                param_names=(),
                param_types=(),
                return_type='list[pkg.Widget]',
                is_class=False,
            )
        if path == 'pkg.Widget':
            return acherion_catalog_models.FuncEntry(
                path='pkg.Widget',
                label='Widget',
                signature='pkg.Widget()',
                min_args=0,
                max_args=0,
                param_names=(),
                param_types=(),
                return_type='pkg.Widget',
                is_class=True,
            )
        return None

    def _fake_method_func_entry(
        class_path: str,
        method_name: str,
    ) -> acherion_catalog_models.FuncEntry | None:
        if class_path == 'pkg.Widget' and method_name == 'mutate':
            return acherion_catalog_models.FuncEntry(
                path='pkg.Widget.mutate',
                label='mutate',
                signature='mutate()',
                min_args=0,
                max_args=0,
                param_names=(),
                param_types=(),
                return_type='',
                is_class=False,
            )
        return None

    monkeypatch.setattr(
        acherion_catalog_runtime,
        'catalog_entry',
        _fake_catalog_entry,
    )
    monkeypatch.setattr(
        acherion_catalog_runtime,
        'method_func_entry',
        _fake_method_func_entry,
    )

    graph = acherion_model.AcherionGraph(
        nodes=[
            acherion_model.AcherionNode(
                node_id='widgets',
                kind='call_function',
                params={
                    'function_path': 'pkg.make_widgets',
                    'module': 'pkg',
                    'arg_count': 0,
                    'arg_sources': [],
                    'exec_sources': ['external_event:run'],
                },
            ),
            acherion_model.AcherionNode(
                node_id='loop',
                kind='for_each',
                params={
                    'list': 'widgets',
                    'exec_sources': ['widgets@1'],
                },
            ),
            acherion_model.AcherionNode(
                node_id='mutate',
                kind='call_method',
                params={
                    'instance': 'loop@0',
                    'method_name': 'mutate',
                    'arg_sources': [],
                    'exec_sources': ['loop@2'],
                },
            ),
            acherion_model.AcherionNode(
                node_id='value',
                kind='get_attribute',
                params={
                    'instance': 'loop@0',
                    'attribute_name': 'value',
                    'exec_sources': ['mutate@0'],
                },
            ),
        ]
    )

    source_code = acherion.compile_acherion_graph(graph)

    assert test_helpers.run_contains_call(source_code, 'mutate')
    assert test_helpers.run_has_assigned_attribute_read(source_code, 'value')
