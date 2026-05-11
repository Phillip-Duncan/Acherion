"""Unit tests for source-id and render-pin helpers."""

from __future__ import annotations

import pytest

import acherion.model as acherion_model

import tests.helpers as test_helpers


pytestmark = pytest.mark.unit


def test_render_source_ids_always_use_indexed_form() -> None:
    owner = test_helpers.RenderPinsOwner()

    assert owner._full_output_source_id(
        acherion_model.AcherionNode(
            node_id='constant_1',
            kind='constant',
            params={'value_type': 'int', 'number_value': 1},
        ),
        0,
    ) == 'constant_1@0'


def test_prune_invalid_exec_connections_canonicalizes_old_plain_aliases() -> None:
    graph = acherion_model.AcherionGraph(
        nodes=[
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
                    'instance': 'm1',
                    'attribute_name': 'layout',
                    'exec_sources': ['m1'],
                },
            ),
        ]
    )
    owner = test_helpers.ConnectionsOwner(graph)

    owner._prune_invalid_exec_connections()

    assert graph.nodes[1].params['exec_sources'] == ['m1@1']


def test_int_typed_pin_literals_are_coerced_before_preview_runtime() -> None:
    renderer = test_helpers.PinLiteralRenderer()
    node = acherion_model.AcherionNode(
        node_id='call',
        kind='call_function',
        params={'pin_literals': {}},
    )

    renderer._set_pin_literal_value(
        node,
        pin_id='arg:2',
        input_kind='number',
        pin_type='int',
        value=250.0,
    )
    renderer._set_pin_literal_value(
        node,
        pin_id='arg:3',
        input_kind='number',
        pin_type='float',
        value=2,
    )

    assert node.params['pin_literals']['arg:2'] == 250
    assert isinstance(node.params['pin_literals']['arg:2'], int)
    assert node.params['pin_literals']['arg:3'] == 2.0
    assert isinstance(node.params['pin_literals']['arg:3'], float)
    assert renderer.change_count == 2