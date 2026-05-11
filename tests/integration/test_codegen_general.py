"""Integration tests for general code-generation flows."""

from __future__ import annotations

import ast

import pytest

import acherion
import acherion.model as acherion_model

import tests.helpers as test_helpers


pytestmark = pytest.mark.integration


def test_duplicate_titled_producer_nodes_compile_to_distinct_variables() -> None:
    graph = acherion_model.AcherionGraph(
        nodes=[
            acherion_model.AcherionNode(
                node_id='c1',
                kind='constant',
                title='One',
                params={
                    'value_type': 'int',
                    'number_value': 1,
                },
            ),
            acherion_model.AcherionNode(
                node_id='c2',
                kind='constant',
                title='Two',
                params={
                    'value_type': 'int',
                    'number_value': 2,
                },
            ),
            acherion_model.AcherionNode(
                node_id='c3',
                kind='constant',
                title='Ten',
                params={
                    'value_type': 'int',
                    'number_value': 10,
                },
            ),
            acherion_model.AcherionNode(
                node_id='c4',
                kind='constant',
                title='Twenty',
                params={
                    'value_type': 'int',
                    'number_value': 20,
                },
            ),
            acherion_model.AcherionNode(
                node_id='a1',
                kind='op_arithmetic',
                title='Arithmetic',
                params={
                    'operator': '+',
                    'left_source': 'c1',
                    'right_source': 'c2',
                },
            ),
            acherion_model.AcherionNode(
                node_id='a2',
                kind='op_arithmetic',
                title='Arithmetic',
                params={
                    'operator': '+',
                    'left_source': 'c3',
                    'right_source': 'c4',
                },
            ),
            acherion_model.AcherionNode(
                node_id='m1',
                kind='make_list',
                title='Pair',
                params={
                    'arg_sources': ['a1', 'a2'],
                },
            ),
        ]
    )

    source_code = acherion.compile_acherion_graph(graph)
    local_values = acherion.execute_acherion_graph(source_code)
    add_targets = test_helpers.run_binop_assignment_targets(source_code, ast.Add)

    assert len(add_targets) == 2
    assert len(set(add_targets)) == 2
    assert any(value == [3, 30] for value in local_values.values())