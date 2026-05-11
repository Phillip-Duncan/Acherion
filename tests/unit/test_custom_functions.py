"""Unit tests for custom-function catalog helpers."""

from __future__ import annotations

import pytest

import acherion
import acherion.model as acherion_model

import tests.helpers as test_helpers


pytestmark = pytest.mark.unit


def test_custom_function_parser_accepts_plain_function_signature() -> None:
    owner = test_helpers.CatalogPinsOwner()

    data, error = owner._parse_custom_function_source(
        'def custom_plain(x: int = 2):\n'
        '    return x + 1\n'
    )

    assert error == ''
    assert data is not None
    assert data['signature'] == 'custom_plain(x: int = 2)'
    assert data['min_args'] == 0
    assert data['max_args'] == 1
    assert data['param_names'] == ['x']
    assert data['param_types'] == ['int']


def test_custom_function_unknown_non_none_return_still_exposes_output_pin() -> None:
    owner = test_helpers.CatalogPinsOwner(
        acherion_model.AcherionGraph(nodes=[], user_functions={})
    )
    function_path = 'user.custom_function_1'
    data, error = owner._parse_custom_function_source(
        'def custom_function_1(x):\n'
        '    return x + 1\n'
    )

    assert error == ''
    assert data is not None
    assert data['return_type'] == 'any'

    owner._graph.user_functions[function_path] = data
    pins = owner._callable_output_pin_specs(
        acherion_model.AcherionNode(
            node_id='cf1',
            kind='custom_function',
            params={'function_path': function_path},
        )
    )

    assert pins == [{'pin_id': 'value', 'label': 'result', 'type': 'any'}]


def test_new_custom_functions_get_sequential_default_names() -> None:
    owner = test_helpers.CatalogPinsOwner(
        acherion_model.AcherionGraph(nodes=[], user_functions={})
    )
    first = acherion_model.AcherionNode(
        node_id='cf1',
        kind='custom_function',
        title='Custom Function',
        params=acherion.custom_function_params('cf1'),
    )
    owner._ensure_custom_function_entry(first)
    owner._graph.nodes.append(first)

    second = acherion_model.AcherionNode(
        node_id='cf2',
        kind='custom_function',
        title='Custom Function',
        params=acherion.custom_function_params('cf2'),
    )
    owner._ensure_custom_function_entry(second)

    assert first.params['function_path'] == 'user.custom_function_1'
    assert second.params['function_path'] == 'user.custom_function_2'
    assert 'user.custom_function_1' in owner._graph.user_functions
    assert 'user.custom_function_2' in owner._graph.user_functions