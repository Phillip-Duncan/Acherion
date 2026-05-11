"""Integration tests for plotly-oriented code generation."""

from __future__ import annotations

import pytest
import plotly.graph_objects as go

import acherion
import acherion.model as acherion_model
import acherion.standalone_host as acherion_standalone_host

import tests.helpers as test_helpers


pytestmark = pytest.mark.integration


def test_plot_figure_codegen_uses_shared_go_runtime_global() -> None:
    graph = acherion_model.AcherionGraph(
        nodes=[
            acherion_model.AcherionNode(
                node_id='x1',
                kind='constant',
                params={
                    'value_type': 'int',
                    'number_value': 1,
                },
            ),
            acherion_model.AcherionNode(
                node_id='x2',
                kind='constant',
                params={
                    'value_type': 'int',
                    'number_value': 2,
                },
            ),
            acherion_model.AcherionNode(
                node_id='xs',
                kind='make_list',
                title='X Values',
                params={
                    'arg_sources': ['x1', 'x2'],
                },
            ),
            acherion_model.AcherionNode(
                node_id='y1',
                kind='constant',
                params={
                    'value_type': 'int',
                    'number_value': 3,
                },
            ),
            acherion_model.AcherionNode(
                node_id='y2',
                kind='constant',
                params={
                    'value_type': 'int',
                    'number_value': 4,
                },
            ),
            acherion_model.AcherionNode(
                node_id='ys',
                kind='make_list',
                title='Y Values',
                params={
                    'arg_sources': ['y1', 'y2'],
                },
            ),
            acherion_model.AcherionNode(
                node_id='fig',
                kind='plot_figure',
                title='Figure',
                params={
                    'figure_type': 'scatter',
                    'named_sources': {
                        'x': 'xs',
                        'y': 'ys',
                    },
                    'figure_title': 'Demo',
                },
            ),
        ]
    )

    source_code = acherion.compile_acherion_graph(graph)

    assert test_helpers.run_contains_call(source_code, 'Figure')
    assert test_helpers.run_contains_call(source_code, 'Scatter')

    preview = acherion_standalone_host.run_standalone_acherion_preview(graph)
    figure = preview.reference_values['fig']

    assert isinstance(figure, go.Figure)
    assert tuple(figure.data[0].x) == (1, 2)
    assert tuple(figure.data[0].y) == (3, 4)
    assert figure.layout.title.text == 'Demo'