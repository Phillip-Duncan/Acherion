"""Integration tests for collection-oriented graph compilation."""

from __future__ import annotations

import pytest

import acherion.model as acherion_model
import acherion.standalone_host as acherion_standalone_host


pytestmark = pytest.mark.integration


def test_dict_nodes_build_read_and_copy_update_dict_values() -> None:
    graph = acherion_model.AcherionGraph(
        nodes=[
            acherion_model.AcherionNode(
                node_id='c1',
                kind='constant',
                params={
                    'value_type': 'int',
                    'number_value': 1,
                },
            ),
            acherion_model.AcherionNode(
                node_id='c2',
                kind='constant',
                params={
                    'value_type': 'int',
                    'number_value': 2,
                },
            ),
            acherion_model.AcherionNode(
                node_id='d1',
                kind='make_dict',
                params={
                    'arg_count': 2,
                    'arg_sources': ['c1', 'c2'],
                    'key_names': ['alpha', 'beta'],
                },
            ),
            acherion_model.AcherionNode(
                node_id='g1',
                kind='dict_get',
                params={
                    'source': 'd1',
                    'pin_literals': {'key': 'beta'},
                },
            ),
            acherion_model.AcherionNode(
                node_id='s1',
                kind='dict_set',
                params={
                    'source': 'd1',
                    'value': 'c2',
                    'pin_literals': {'key': 'gamma'},
                },
            ),
        ]
    )

    preview = acherion_standalone_host.run_standalone_acherion_preview(graph)

    assert preview.reference_values['d1'] == {'alpha': 1, 'beta': 2}
    assert preview.reference_values['g1'] == 2
    assert preview.reference_values['s1'] == {
        'alpha': 1,
        'beta': 2,
        'gamma': 2,
    }
    assert preview.reference_values['d1'] == {'alpha': 1, 'beta': 2}


def test_list_nodes_get_and_copy_update_single_indices_and_slices() -> None:
    graph = acherion_model.AcherionGraph(
        nodes=[
            acherion_model.AcherionNode(
                node_id='c1',
                kind='constant',
                params={
                    'value_type': 'int',
                    'number_value': 1,
                },
            ),
            acherion_model.AcherionNode(
                node_id='c2',
                kind='constant',
                params={
                    'value_type': 'int',
                    'number_value': 2,
                },
            ),
            acherion_model.AcherionNode(
                node_id='c3',
                kind='constant',
                params={
                    'value_type': 'int',
                    'number_value': 3,
                },
            ),
            acherion_model.AcherionNode(
                node_id='c9',
                kind='constant',
                params={
                    'value_type': 'int',
                    'number_value': 9,
                },
            ),
            acherion_model.AcherionNode(
                node_id='l1',
                kind='make_list',
                params={
                    'arg_sources': ['c1', 'c2', 'c3'],
                },
            ),
            acherion_model.AcherionNode(
                node_id='g1',
                kind='list_index',
                params={
                    'source': 'l1',
                    'index': 1,
                },
            ),
            acherion_model.AcherionNode(
                node_id='s1',
                kind='list_set',
                params={
                    'source': 'l1',
                    'value': 'c9',
                    'mode': 'index',
                    'index': 1,
                },
            ),
            acherion_model.AcherionNode(
                node_id='r1',
                kind='make_list',
                params={
                    'arg_sources': ['c9', 'c9'],
                },
            ),
            acherion_model.AcherionNode(
                node_id='s2',
                kind='list_set',
                params={
                    'source': 'l1',
                    'value': 'r1',
                    'mode': 'slice',
                    'start': 1,
                    'stop': 3,
                    'step': 1,
                },
            ),
        ]
    )

    preview = acherion_standalone_host.run_standalone_acherion_preview(graph)

    assert preview.reference_values['g1'] == 2
    assert preview.reference_values['s1'] == [1, 9, 3]
    assert preview.reference_values['s2'] == [1, 9, 9]
    assert preview.reference_values['l1'] == [1, 2, 3]


def test_list_set_tracks_value_dependency_even_when_declared_later() -> None:
    graph = acherion_model.AcherionGraph(
        nodes=[
            acherion_model.AcherionNode(
                node_id='c1',
                kind='constant',
                params={
                    'value_type': 'int',
                    'number_value': 1,
                },
            ),
            acherion_model.AcherionNode(
                node_id='c2',
                kind='constant',
                params={
                    'value_type': 'int',
                    'number_value': 2,
                },
            ),
            acherion_model.AcherionNode(
                node_id='c3',
                kind='constant',
                params={
                    'value_type': 'int',
                    'number_value': 3,
                },
            ),
            acherion_model.AcherionNode(
                node_id='l1',
                kind='make_list',
                params={
                    'arg_sources': ['c1', 'c2', 'c3'],
                },
            ),
            acherion_model.AcherionNode(
                node_id='s1',
                kind='list_set',
                params={
                    'source': 'l1',
                    'value': 'c9',
                    'mode': 'index',
                    'index': 1,
                },
            ),
            acherion_model.AcherionNode(
                node_id='c9',
                kind='constant',
                params={
                    'value_type': 'int',
                    'number_value': 9,
                },
            ),
        ]
    )

    preview = acherion_standalone_host.run_standalone_acherion_preview(graph)

    assert preview.reference_values['s1'] == [1, 9, 3]