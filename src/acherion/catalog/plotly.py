"""Plotly trace metadata for visual-logic figure nodes."""

from __future__ import annotations

from acherion.catalog import models as _catalog_models

TRACE_PARAM_TYPES: dict[str, str] = {
    'x': 'list',
    'y': 'list',
    'z': 'list',
    'values': 'list',
    'labels': 'list',
    'open': 'list',
    'high': 'list',
    'low': 'list',
    'close': 'list',
    'error_y_array': 'list',
    'measure': 'list',
    'text': 'any',
    'name': 'str',
    'mode': 'str',
    'colorscale': 'str',
    'histnorm': 'str',
    'orientation': 'str',
    'textinfo': 'str',
    'line_dash': 'str',
    'boxpoints': 'str',
    'points': 'str',
    'fillcolor': 'str',
    'line_color': 'str',
    'marker_color': 'any',
    'title_text': 'str',
    'opacity': 'float',
    'jitter': 'float',
    'hole': 'float',
    'pull': 'any',
    'zmin': 'float',
    'zmax': 'float',
    'nbinsx': 'float',
    'ncontours': 'float',
    'marker_size': 'any',
    'line_width': 'float',
    'width': 'float',
    'value': 'float',
    'reference': 'float',
    'gauge_axis_range_min': 'float',
    'gauge_axis_range_max': 'float',
    'box_visible': 'bool',
    'notched': 'bool',
    'cumulative_enabled': 'bool',
    'meanline_visible': 'bool',
}

PLOTLY_TRACES: tuple[_catalog_models.PlotlyTraceEntry, ...] = (
    _catalog_models.PlotlyTraceEntry(
        kind='scatter',
        label='Scatter',
        go_class='go.Scatter',
        params=(
            _catalog_models.TraceParam('x', 'X values', True, 'array'),
            _catalog_models.TraceParam('y', 'Y values', True, 'array'),
            _catalog_models.TraceParam('name', 'Series name', False, 'str'),
            _catalog_models.TraceParam(
                'mode',
                'Mode',
                False,
                '"markers"/"lines"/"lines+markers"',
            ),
            _catalog_models.TraceParam(
                'text', 'Hover text', False, 'str or array'
            ),
            _catalog_models.TraceParam(
                'marker_color', 'Marker colour', False, 'str or array'
            ),
            _catalog_models.TraceParam(
                'marker_size', 'Marker size', False, 'int or array'
            ),
            _catalog_models.TraceParam(
                'line_color', 'Line colour', False, 'str'
            ),
            _catalog_models.TraceParam(
                'line_width', 'Line width', False, 'float'
            ),
            _catalog_models.TraceParam(
                'opacity', 'Opacity', False, '0.0 - 1.0'
            ),
            _catalog_models.TraceParam(
                'error_y_array', 'Y error bars', False, 'array'
            ),
        ),
    ),
    _catalog_models.PlotlyTraceEntry(
        kind='line',
        label='Line',
        go_class='go.Scatter',
        params=(
            _catalog_models.TraceParam('x', 'X values', True, 'array'),
            _catalog_models.TraceParam('y', 'Y values', True, 'array'),
            _catalog_models.TraceParam('name', 'Series name', False, 'str'),
            _catalog_models.TraceParam(
                'line_color', 'Line colour', False, 'str'
            ),
            _catalog_models.TraceParam(
                'line_width', 'Line width', False, 'float'
            ),
            _catalog_models.TraceParam(
                'line_dash', 'Dash style', False, '"solid"/"dash"/"dot"'
            ),
            _catalog_models.TraceParam(
                'text', 'Hover text', False, 'str or array'
            ),
            _catalog_models.TraceParam(
                'opacity', 'Opacity', False, '0.0 - 1.0'
            ),
            _catalog_models.TraceParam(
                'error_y_array', 'Y error bars', False, 'array'
            ),
        ),
    ),
    _catalog_models.PlotlyTraceEntry(
        kind='bar',
        label='Bar',
        go_class='go.Bar',
        params=(
            _catalog_models.TraceParam('x', 'X categories', True, 'array'),
            _catalog_models.TraceParam('y', 'Y values', True, 'array'),
            _catalog_models.TraceParam('name', 'Series name', False, 'str'),
            _catalog_models.TraceParam(
                'text', 'Bar labels', False, 'str or array'
            ),
            _catalog_models.TraceParam(
                'marker_color', 'Bar colour', False, 'str or array'
            ),
            _catalog_models.TraceParam(
                'opacity', 'Opacity', False, '0.0 - 1.0'
            ),
            _catalog_models.TraceParam(
                'orientation', 'Orientation', False, '"v" or "h"'
            ),
            _catalog_models.TraceParam(
                'error_y_array', 'Y error bars', False, 'array'
            ),
            _catalog_models.TraceParam('width', 'Bar width', False, 'float'),
        ),
    ),
    _catalog_models.PlotlyTraceEntry(
        kind='histogram',
        label='Histogram',
        go_class='go.Histogram',
        params=(
            _catalog_models.TraceParam('x', 'Values', True, 'array'),
            _catalog_models.TraceParam('name', 'Series name', False, 'str'),
            _catalog_models.TraceParam('nbinsx', 'Bin count', False, 'int'),
            _catalog_models.TraceParam(
                'histnorm', 'Normalisation', False, '"probability"/"percent"/""'
            ),
            _catalog_models.TraceParam(
                'marker_color', 'Bar colour', False, 'str'
            ),
            _catalog_models.TraceParam(
                'opacity', 'Opacity', False, '0.0 - 1.0'
            ),
            _catalog_models.TraceParam(
                'cumulative_enabled', 'Cumulative', False, 'bool'
            ),
        ),
    ),
    _catalog_models.PlotlyTraceEntry(
        kind='box',
        label='Box Plot',
        go_class='go.Box',
        params=(
            _catalog_models.TraceParam('y', 'Y values', True, 'array'),
            _catalog_models.TraceParam(
                'x', 'X group labels', False, 'array or str'
            ),
            _catalog_models.TraceParam('name', 'Series name', False, 'str'),
            _catalog_models.TraceParam(
                'boxpoints', 'Show points', False, '"all"/"outliers"/False'
            ),
            _catalog_models.TraceParam('jitter', 'Jitter', False, '0.0 - 1.0'),
            _catalog_models.TraceParam(
                'marker_color', 'Box colour', False, 'str'
            ),
            _catalog_models.TraceParam(
                'line_color', 'Line colour', False, 'str'
            ),
            _catalog_models.TraceParam('notched', 'Notched', False, 'bool'),
        ),
    ),
    _catalog_models.PlotlyTraceEntry(
        kind='violin',
        label='Violin',
        go_class='go.Violin',
        params=(
            _catalog_models.TraceParam('y', 'Y values', True, 'array'),
            _catalog_models.TraceParam('x', 'X group label', False, 'str'),
            _catalog_models.TraceParam('name', 'Series name', False, 'str'),
            _catalog_models.TraceParam(
                'box_visible', 'Show box', False, 'bool'
            ),
            _catalog_models.TraceParam(
                'points', 'Show points', False, '"all"/"outliers"/False'
            ),
            _catalog_models.TraceParam(
                'meanline_visible', 'Show mean line', False, 'bool'
            ),
            _catalog_models.TraceParam('fillcolor', 'Fill colour', False, 'str'),
            _catalog_models.TraceParam(
                'line_color', 'Line colour', False, 'str'
            ),
        ),
    ),
    _catalog_models.PlotlyTraceEntry(
        kind='heatmap',
        label='Heatmap',
        go_class='go.Heatmap',
        params=(
            _catalog_models.TraceParam('z', 'Z matrix', True, '2-D array'),
            _catalog_models.TraceParam('x', 'X labels', False, 'array'),
            _catalog_models.TraceParam('y', 'Y labels', False, 'array'),
            _catalog_models.TraceParam(
                'colorscale', 'Colour scale', False, '"Viridis"/"RdBu"/...'
            ),
            _catalog_models.TraceParam('zmin', 'Z min', False, 'float'),
            _catalog_models.TraceParam('zmax', 'Z max', False, 'float'),
            _catalog_models.TraceParam('name', 'Series name', False, 'str'),
        ),
    ),
    _catalog_models.PlotlyTraceEntry(
        kind='pie',
        label='Pie',
        go_class='go.Pie',
        params=(
            _catalog_models.TraceParam(
                'values', 'Values', True, 'array of float'
            ),
            _catalog_models.TraceParam(
                'labels', 'Labels', True, 'array of str'
            ),
            _catalog_models.TraceParam('name', 'Series name', False, 'str'),
            _catalog_models.TraceParam(
                'hole', 'Donut hole', False, '0.0 - 1.0 (0 = pie)'
            ),
            _catalog_models.TraceParam(
                'textinfo', 'Text info', False, '"label+percent"/"value"/...'
            ),
            _catalog_models.TraceParam(
                'pull', 'Pull slices', False, 'float or array'
            ),
            _catalog_models.TraceParam(
                'opacity', 'Opacity', False, '0.0 - 1.0'
            ),
        ),
    ),
    _catalog_models.PlotlyTraceEntry(
        kind='scatter3d',
        label='Scatter 3D',
        go_class='go.Scatter3d',
        params=(
            _catalog_models.TraceParam('x', 'X values', True, 'array'),
            _catalog_models.TraceParam('y', 'Y values', True, 'array'),
            _catalog_models.TraceParam('z', 'Z values', True, 'array'),
            _catalog_models.TraceParam('name', 'Series name', False, 'str'),
            _catalog_models.TraceParam(
                'mode',
                'Mode',
                False,
                '"markers"/"lines"/"lines+markers"',
            ),
            _catalog_models.TraceParam(
                'marker_color', 'Marker colour', False, 'str or array'
            ),
            _catalog_models.TraceParam(
                'marker_size', 'Marker size', False, 'int or array'
            ),
            _catalog_models.TraceParam(
                'text', 'Hover text', False, 'str or array'
            ),
        ),
    ),
    _catalog_models.PlotlyTraceEntry(
        kind='surface',
        label='Surface',
        go_class='go.Surface',
        params=(
            _catalog_models.TraceParam('z', 'Z matrix', True, '2-D array'),
            _catalog_models.TraceParam('x', 'X grid', False, 'array'),
            _catalog_models.TraceParam('y', 'Y grid', False, 'array'),
            _catalog_models.TraceParam(
                'colorscale', 'Colour scale', False, '"Viridis"/"RdBu"/...'
            ),
            _catalog_models.TraceParam('name', 'Series name', False, 'str'),
            _catalog_models.TraceParam(
                'opacity', 'Opacity', False, '0.0 - 1.0'
            ),
        ),
    ),
    _catalog_models.PlotlyTraceEntry(
        kind='contour',
        label='Contour',
        go_class='go.Contour',
        params=(
            _catalog_models.TraceParam('z', 'Z matrix', True, '2-D array'),
            _catalog_models.TraceParam('x', 'X labels', False, 'array'),
            _catalog_models.TraceParam('y', 'Y labels', False, 'array'),
            _catalog_models.TraceParam(
                'colorscale', 'Colour scale', False, 'str'
            ),
            _catalog_models.TraceParam(
                'ncontours', 'Contour levels', False, 'int'
            ),
            _catalog_models.TraceParam('name', 'Series name', False, 'str'),
        ),
    ),
    _catalog_models.PlotlyTraceEntry(
        kind='waterfall',
        label='Waterfall',
        go_class='go.Waterfall',
        params=(
            _catalog_models.TraceParam('x', 'X categories', True, 'array'),
            _catalog_models.TraceParam('y', 'Delta values', True, 'array'),
            _catalog_models.TraceParam('name', 'Series name', False, 'str'),
            _catalog_models.TraceParam(
                'measure',
                'Measure types',
                False,
                'array of "relative"/"total"/"absolute"',
            ),
            _catalog_models.TraceParam('text', 'Bar labels', False, 'array'),
        ),
    ),
    _catalog_models.PlotlyTraceEntry(
        kind='candlestick',
        label='Candlestick',
        go_class='go.Candlestick',
        params=(
            _catalog_models.TraceParam('x', 'X (dates)', True, 'array'),
            _catalog_models.TraceParam('open', 'Open', True, 'array'),
            _catalog_models.TraceParam('high', 'High', True, 'array'),
            _catalog_models.TraceParam('low', 'Low', True, 'array'),
            _catalog_models.TraceParam('close', 'Close', True, 'array'),
            _catalog_models.TraceParam('name', 'Series name', False, 'str'),
        ),
    ),
    _catalog_models.PlotlyTraceEntry(
        kind='indicator',
        label='Indicator / Gauge',
        go_class='go.Indicator',
        params=(
            _catalog_models.TraceParam('value', 'Value', True, 'float'),
            _catalog_models.TraceParam('title_text', 'Title', False, 'str'),
            _catalog_models.TraceParam(
                'mode', 'Display mode', False, '"number"/"gauge"/"delta"'
            ),
            _catalog_models.TraceParam(
                'reference', 'Reference (delta)', False, 'float'
            ),
            _catalog_models.TraceParam(
                'gauge_axis_range_min', 'Gauge min', False, 'float'
            ),
            _catalog_models.TraceParam(
                'gauge_axis_range_max', 'Gauge max', False, 'float'
            ),
        ),
    ),
)

TRACE_BY_KIND: dict[str, _catalog_models.PlotlyTraceEntry] = {
    trace.kind: trace for trace in PLOTLY_TRACES
}


def trace_entry(
    figure_type: str,
) -> _catalog_models.PlotlyTraceEntry | None:
    """Return PlotlyTraceEntry for a figure type key, or None."""
    return TRACE_BY_KIND.get(figure_type)


def trace_options() -> dict[str, str]:
    """Return {kind: label} for the figure-type selector."""
    return {trace.kind: trace.label for trace in PLOTLY_TRACES}


def trace_pin_specs(figure_type: str) -> list[dict[str, str]]:
    """Return input pin specs for a plot_figure node."""
    entry = TRACE_BY_KIND.get(figure_type)
    if not entry:
        return []
    return [
        {
            'pin_id': f'named:{param.name}',
            'label': f'{"*" if param.required else ""}{param.label}',
            'hint': param.hint,
            'required': str(param.required),
            'type': TRACE_PARAM_TYPES.get(param.name, 'any'),
        }
        for param in entry.params
    ]