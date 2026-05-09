from acherion import (
    AcherionGraph,
    AcherionNode,
    acherion_ui_colors,
    build_acherion_theme_override_css,
    build_embedded_acherion_theme_css,
    compile_acherion_graph,
    execute_acherion_graph,
    normalize_acherion_theme_overrides,
)
from acherion.standalone_host import (
    run_standalone_acherion_preview,
    standalone_editor_visible_code,
)


def test_constant_graph_compiles_executes_and_previews() -> None:
    graph = AcherionGraph(
        nodes=[
            AcherionNode(
                node_id='n1',
                kind='constant',
                params={
                    'value_type': 'int',
                    'number_value': 3,
                },
            )
        ]
    )

    source_code = compile_acherion_graph(graph)

    assert 'def run(bindings=None):' in source_code

    local_values = execute_acherion_graph(source_code)

    assert 3 in local_values.values()

    preview = run_standalone_acherion_preview(graph)

    assert preview.reference_values['n1'] == 3
    assert preview.reference_values['n1@0'] == 3
    assert preview.state_values['acherion.preview_value_count'] >= 1
    assert str(preview.state_values.get('hint') or '').startswith(
        'Preview ran for '
    )


def test_standalone_visible_code_hides_runtime_scaffold() -> None:
    graph = AcherionGraph(
        nodes=[
            AcherionNode(
                node_id='n1',
                kind='constant',
                params={
                    'value_type': 'bool',
                    'bool_value': True,
                },
            )
        ]
    )

    source_code = compile_acherion_graph(graph)
    visible_code = standalone_editor_visible_code(source_code)

    assert '_normalize_scoped_bindings' not in visible_code
    assert 'ACHERION_EXTERNAL_EVENTS' not in visible_code
    assert 'def run():' in visible_code
    assert 'bindings=None' not in visible_code


def test_theme_helpers_normalize_aliases_and_preserve_scope_contract() -> None:
    overrides = normalize_acherion_theme_overrides({
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

    colors = acherion_ui_colors({'primary': '#123456'})

    assert colors['primary'] == '#123456'
    assert colors['positive']

    override_css = build_acherion_theme_override_css(
        scope_selector='.acherion-scope',
        theme_overrides={'primary': '#123456'},
    )
    embedded_css = build_embedded_acherion_theme_css(
        scope_selector='.acherion-scope',
        theme_overrides={'primary': '#123456'},
    )

    assert '.acherion-scope {' in override_css
    assert '--oe-blue: #123456;' in override_css
    assert '.acherion-scope' in embedded_css
    assert '--oe-blue: #123456;' in embedded_css