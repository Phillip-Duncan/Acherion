"""End-to-end tests for top-level standalone workflows."""

from __future__ import annotations

import pytest

import acherion
import acherion.model as acherion_model
import acherion.standalone_host as acherion_standalone_host

import tests.helpers as test_helpers


pytestmark = pytest.mark.e2e


def test_constant_graph_compiles_executes_and_previews() -> None:
    graph = acherion_model.AcherionGraph(
        nodes=[
            acherion_model.AcherionNode(
                node_id='n1',
                kind='constant',
                params={
                    'value_type': 'int',
                    'number_value': 3,
                },
            )
        ]
    )

    source_code = acherion.compile_acherion_graph(graph)

    assert test_helpers.run_function_arg_names(source_code) == ['bindings']

    local_values = acherion.execute_acherion_graph(source_code)

    assert 3 in local_values.values()

    preview = acherion_standalone_host.run_standalone_acherion_preview(graph)

    assert preview.reference_values['n1'] == 3
    assert preview.reference_values['n1@0'] == 3
    assert preview.state_values['acherion.preview_value_count'] >= 1
    assert str(preview.state_values.get('hint') or '').startswith(
        'Preview ran for '
    )


def test_standalone_visible_code_hides_runtime_scaffold() -> None:
    graph = acherion_model.AcherionGraph(
        nodes=[
            acherion_model.AcherionNode(
                node_id='n1',
                kind='constant',
                params={
                    'value_type': 'bool',
                    'bool_value': True,
                },
            )
        ]
    )

    source_code = acherion.compile_acherion_graph(graph)
    visible_code = acherion_standalone_host.standalone_editor_visible_code(
        source_code
    )

    assert '_normalize_scoped_bindings' not in visible_code
    assert 'ACHERION_EXTERNAL_EVENTS' not in visible_code
    assert 'def run():' in visible_code
    assert 'bindings=None' not in visible_code


def test_standalone_runtime_exposes_catalog_module_globals() -> None:
    source_code = '''
def run(bindings=None):
    array = np.array([1, 2, 3])
    root = math.sqrt(9)
    figure = go.Figure()
    subplot = plotly.subplots.make_subplots(rows=1, cols=1)
    return {
        "array": array,
        "root": root,
        "figure": figure,
        "subplot": subplot,
    }
'''

    local_values = acherion.execute_acherion_graph(source_code)

    assert local_values['array'].tolist() == [1, 2, 3]
    assert local_values['root'] == 3.0
    assert type(local_values['figure']).__name__ == 'Figure'
    assert type(local_values['subplot']).__name__ == 'Figure'


def test_legacy_self_custom_function_runtime_runs_without_migration() -> None:
    function_path = 'user.custom_function_a3ca1e8c'
    graph = acherion_model.AcherionGraph(
        nodes=[],
        user_functions={
            function_path: {
                'label': 'custom_function_a3ca1e8c',
                'signature': 'custom_function_a3ca1e8c(x)',
                'min_args': 1,
                'max_args': 1,
                'param_names': ['x'],
                'param_types': ['int'],
                'return_type': 'int',
                'source_code': (
                    'def custom_function_a3ca1e8c(self, x):\n'
                    '    return x + 1\n'
                ),
            }
        },
    )

    source_code = acherion.compile_acherion_graph(graph)
    namespace = acherion_standalone_host.load_acherion_graph_namespace(
        source_code
    )

    assert callable(namespace['custom_function_a3ca1e8c'])
    assert namespace['custom_function_a3ca1e8c'](2) == 3