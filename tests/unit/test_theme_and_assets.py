"""Unit tests for theme helpers, assets, and preview payloads."""

from __future__ import annotations

import pytest
import numpy as np
import plotly.graph_objects as go

import acherion
import acherion.preview as acherion_preview


pytestmark = pytest.mark.unit


def test_theme_helpers_normalize_aliases_and_preserve_scope_contract() -> None:
    overrides = acherion.normalize_acherion_theme_overrides({
        'primary': '#123456',
        'sidebar_panel_bg': 'rgba(1, 2, 3, 0.5)',
        '--custom-gap': '10px',
        'muted': '',
    })

    assert overrides == {
        '--oe-blue': '#123456',
        '--ach-sidebar-panel-bg': 'rgba(1, 2, 3, 0.5)',
        '--custom-gap': '10px',
    }

    colors = acherion.acherion_ui_colors({'primary': '#123456'})

    assert colors['primary'] == '#123456'
    assert colors['positive']


def test_plotly_template_payload_matches_dark_acherion_tokens() -> None:
    template = acherion.acherion_plotly_template_payload()

    assert template['layout']['paper_bgcolor'] == 'rgba(0,0,0,0)'
    assert template['layout']['font']['color'] == '#E7E9EA'
    assert template['layout']['legend']['bgcolor'] == 'rgba(22, 24, 28, 0.85)'
    assert template['layout']['colorway'][:4] == [
        '#1D9BF0',
        '#00BA7C',
        '#F4212E',
        '#FFD400',
    ]


def test_plotly_preview_payload_serializes_figure_like_values() -> None:
    figure = go.Figure(
        data=[go.Bar(x=[1, 2], y=[3, 4])],
        layout={'title': {'text': 'Preview'}},
    )

    payload = acherion_preview.preview_value_plotly_payload(figure)

    assert payload is not None
    assert payload['data'][0]['type'] == 'bar'
    assert payload['layout']['title']['text'] == 'Preview'
    assert payload['layout']['template']['layout']['font']['color'] == '#E7E9EA'


def test_numpy_dependency_is_available_for_array_summaries() -> None:
    value = np.array([[1, 2], [3, 4]])

    assert value.shape == (2, 2)