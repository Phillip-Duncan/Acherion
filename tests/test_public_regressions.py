from acherion import (
    AcherionGraph,
    AcherionNode,
    acherion_plotly_template_payload,
    acherion_ui_colors,
    build_acherion_theme_override_css,
    build_embedded_acherion_theme_css,
    compile_acherion_graph,
    custom_function_params,
    execute_acherion_graph,
    normalize_acherion_theme_overrides,
)
from acherion.assets.js.graph import GRAPH_JS
from acherion.assets.js.viewport import VIEWPORT_JS
from acherion.catalog import modules as _catalog_modules
from acherion.catalog import runtime as _catalog_runtime
from acherion.embed.designer.interactions import _DesignerInteractionsMixin
import acherion.embed.render.editor as acherion_render_editor
import acherion.embed.render.nodes as acherion_render_nodes
from acherion.embed.render.pins import _RenderPinsMixin
from acherion.graphops.catalog import _GraphOpsCatalogMixin
from acherion.graphops.pins import _GraphOpsPinsMixin
from acherion.preview import preview_value_plotly_payload
import acherion.registry as acherion_registry
import numpy as np
import plotly.graph_objects as go
from acherion.standalone_host import (
    load_acherion_graph_namespace,
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


def test_duplicate_titled_producer_nodes_compile_to_distinct_variables() -> None:
    graph = AcherionGraph(
        nodes=[
            AcherionNode(
                node_id='c1',
                kind='constant',
                title='One',
                params={
                    'value_type': 'int',
                    'number_value': 1,
                },
            ),
            AcherionNode(
                node_id='c2',
                kind='constant',
                title='Two',
                params={
                    'value_type': 'int',
                    'number_value': 2,
                },
            ),
            AcherionNode(
                node_id='c3',
                kind='constant',
                title='Ten',
                params={
                    'value_type': 'int',
                    'number_value': 10,
                },
            ),
            AcherionNode(
                node_id='c4',
                kind='constant',
                title='Twenty',
                params={
                    'value_type': 'int',
                    'number_value': 20,
                },
            ),
            AcherionNode(
                node_id='a1',
                kind='op_arithmetic',
                title='Arithmetic',
                params={
                    'operator': '+',
                    'left_source': 'c1',
                    'right_source': 'c2',
                },
            ),
            AcherionNode(
                node_id='a2',
                kind='op_arithmetic',
                title='Arithmetic',
                params={
                    'operator': '+',
                    'left_source': 'c3',
                    'right_source': 'c4',
                },
            ),
            AcherionNode(
                node_id='m1',
                kind='make_list',
                title='Pair',
                params={
                    'arg_sources': ['a1', 'a2'],
                },
            ),
        ]
    )

    source_code = compile_acherion_graph(graph)
    local_values = execute_acherion_graph(source_code)

    assert 'arithmetic_5 = (one_1) + (two_2)' in source_code
    assert 'arithmetic_6 = (ten_3) + (twenty_4)' in source_code
    assert local_values['pair_7'] == [3, 30]


def test_dict_nodes_build_read_and_copy_update_dict_values() -> None:
    graph = AcherionGraph(
        nodes=[
            AcherionNode(
                node_id='c1',
                kind='constant',
                params={
                    'value_type': 'int',
                    'number_value': 1,
                },
            ),
            AcherionNode(
                node_id='c2',
                kind='constant',
                params={
                    'value_type': 'int',
                    'number_value': 2,
                },
            ),
            AcherionNode(
                node_id='d1',
                kind='make_dict',
                params={
                    'arg_count': 2,
                    'arg_sources': ['c1', 'c2'],
                    'key_names': ['alpha', 'beta'],
                },
            ),
            AcherionNode(
                node_id='g1',
                kind='dict_get',
                params={
                    'source': 'd1',
                    'pin_literals': {'key': 'beta'},
                },
            ),
            AcherionNode(
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

    preview = run_standalone_acherion_preview(graph)

    assert preview.reference_values['d1'] == {'alpha': 1, 'beta': 2}
    assert preview.reference_values['g1'] == 2
    assert preview.reference_values['s1'] == {
        'alpha': 1,
        'beta': 2,
        'gamma': 2,
    }
    assert preview.reference_values['d1'] == {'alpha': 1, 'beta': 2}


def test_list_nodes_get_and_copy_update_single_indices_and_slices() -> None:
    graph = AcherionGraph(
        nodes=[
            AcherionNode(
                node_id='c1',
                kind='constant',
                params={
                    'value_type': 'int',
                    'number_value': 1,
                },
            ),
            AcherionNode(
                node_id='c2',
                kind='constant',
                params={
                    'value_type': 'int',
                    'number_value': 2,
                },
            ),
            AcherionNode(
                node_id='c3',
                kind='constant',
                params={
                    'value_type': 'int',
                    'number_value': 3,
                },
            ),
            AcherionNode(
                node_id='c9',
                kind='constant',
                params={
                    'value_type': 'int',
                    'number_value': 9,
                },
            ),
            AcherionNode(
                node_id='l1',
                kind='make_list',
                params={
                    'arg_sources': ['c1', 'c2', 'c3'],
                },
            ),
            AcherionNode(
                node_id='g1',
                kind='list_index',
                params={
                    'source': 'l1',
                    'index': 1,
                },
            ),
            AcherionNode(
                node_id='s1',
                kind='list_set',
                params={
                    'source': 'l1',
                    'value': 'c9',
                    'mode': 'index',
                    'index': 1,
                },
            ),
            AcherionNode(
                node_id='r1',
                kind='make_list',
                params={
                    'arg_sources': ['c9', 'c9'],
                },
            ),
            AcherionNode(
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

    preview = run_standalone_acherion_preview(graph)

    assert preview.reference_values['g1'] == 2
    assert preview.reference_values['s1'] == [1, 9, 3]
    assert preview.reference_values['s2'] == [1, 9, 9]
    assert preview.reference_values['l1'] == [1, 2, 3]


def test_list_set_tracks_value_dependency_even_when_declared_later() -> None:
    graph = AcherionGraph(
        nodes=[
            AcherionNode(
                node_id='c1',
                kind='constant',
                params={
                    'value_type': 'int',
                    'number_value': 1,
                },
            ),
            AcherionNode(
                node_id='c2',
                kind='constant',
                params={
                    'value_type': 'int',
                    'number_value': 2,
                },
            ),
            AcherionNode(
                node_id='c3',
                kind='constant',
                params={
                    'value_type': 'int',
                    'number_value': 3,
                },
            ),
            AcherionNode(
                node_id='l1',
                kind='make_list',
                params={
                    'arg_sources': ['c1', 'c2', 'c3'],
                },
            ),
            AcherionNode(
                node_id='s1',
                kind='list_set',
                params={
                    'source': 'l1',
                    'value': 'c9',
                    'mode': 'index',
                    'index': 1,
                },
            ),
            AcherionNode(
                node_id='c9',
                kind='constant',
                params={
                    'value_type': 'int',
                    'number_value': 9,
                },
            ),
        ]
    )

    preview = run_standalone_acherion_preview(graph)

    assert preview.reference_values['s1'] == [1, 9, 3]


def test_list_index_definition_keeps_index_and_slice_defaults() -> None:
    definition = acherion_registry.get_acherion_node_definition('list_index')

    assert definition is not None
    assert definition.default_params(node_id='idx1') == {
        'source': '',
        'mode': 'index',
        'index': 0,
        'start': '',
        'stop': '',
        'step': '',
    }



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


def test_function_catalog_includes_numpy_and_plotly_modules() -> None:
    module_options = _catalog_modules.module_options()

    assert module_options['np'] == 'numpy (np)'
    assert module_options['go'] == 'plotly.graph_objects (go)'
    assert module_options['px'] == 'plotly.express (px)'
    assert module_options['plotly.subplots'] == 'plotly.subplots'

    np_options = _catalog_runtime.func_options('np')
    go_options = _catalog_runtime.func_options('go')
    px_options = _catalog_runtime.func_options('px')
    subplot_options = _catalog_runtime.func_options('plotly.subplots')

    assert 'np.array' in np_options
    assert 'go.Figure' in go_options
    assert 'px.scatter' in px_options
    assert 'plotly.subplots.make_subplots' in subplot_options


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

    local_values = execute_acherion_graph(source_code)

    assert local_values['array'].tolist() == [1, 2, 3]
    assert local_values['root'] == 3.0
    assert type(local_values['figure']).__name__ == 'Figure'
    assert type(local_values['subplot']).__name__ == 'Figure'


def test_clear_selection_shortcut_clears_selected_nodes() -> None:
    class _StubDesigner(_DesignerInteractionsMixin):
        def __init__(self) -> None:
            self._selected_node_ids = {'n1', 'n2'}
            self._selected_connection_id = None
            self.refresh_count = 0
            self.hint_updates = 0

        def refresh(self) -> None:
            self.refresh_count += 1

        def _update_hint(self) -> None:
            self.hint_updates += 1

    designer = _StubDesigner()

    class _Event:
        args = {'shortcut_id': 'clear_selection', 'key': 'Escape'}

    designer._handle_canvas_key(_Event())

    assert designer._selected_node_ids == set()
    assert designer.refresh_count == 1
    assert designer.hint_updates == 1


def test_make_dict_editor_arg_count_seeds_key_names() -> None:
    class _StubEditor(acherion_render_editor._RenderEditorMixin):
        pass

    editor = _StubEditor()
    node = AcherionNode(
        node_id='dict1',
        kind='make_dict',
        params={
            'arg_count': 0,
            'arg_sources': [],
            'key_names': [],
        },
    )

    editor._set_editor_arg_count(node, 2)
    editor._set_editor_make_dict_key(node, 1, 'beta')

    assert node.params['arg_count'] == 2
    assert node.params['arg_sources'] == ['', '']
    assert node.params['key_names'] == ['key_1', 'beta']


def test_palette_taxonomy_groups_like_nodes_together() -> None:
    sections = acherion_registry._palette_sections()
    section_map = {
        category: [item.kind for item in items]
        for category, items in sections
    }

    assert list(section_map) == [
        'math',
        'logic',
        'collections',
        'flow',
        'object',
        'composite',
        'visualization',
    ]
    assert section_map['math'] == [
        'op_arithmetic',
        'op_unary',
    ]
    assert section_map['logic'] == [
        'compare',
        'op_logic',
        'op_not',
    ]
    assert section_map['collections'] == [
        'constant',
        'make_list',
        'list_index',
        'list_set',
        'make_dict',
        'dict_get',
        'dict_set',
    ]
    assert section_map['object'] == [
        'call_function',
        'call_method',
        'get_attribute',
        'set_attribute',
    ]
    assert section_map['composite'] == [
        'custom_function',
        'function_box',
    ]
    assert section_map['visualization'] == ['plot_figure']
    assert acherion_registry._template_category_label('dict_get') == (
        'Collections'
    )
    assert acherion_registry._template_category_label('custom_function') == (
        'Functions'
    )
    assert acherion_registry._template_category_label('plot_figure') == (
        'Visualization'
    )


def test_palette_section_expansion_state_respects_search_override() -> None:
    class _StubNodes(acherion_render_nodes._RenderNodesMixin):
        def __init__(self) -> None:
            self._palette_query = ''
            self._palette_collapsed_categories: set[str] = set()

    owner = _StubNodes()

    assert owner._palette_section_expanded('collections') is True

    owner._toggle_palette_category('collections')

    assert owner._palette_section_expanded('collections') is False

    owner._palette_query = 'dict'

    assert owner._palette_section_expanded('collections') is True

    owner._palette_query = ''

    assert owner._palette_section_expanded('collections') is False


def test_list_outputs_resolve_builtin_list_methods_for_call_method() -> None:
    class _DummyOwner(_GraphOpsCatalogMixin, _GraphOpsPinsMixin):
        def __init__(self) -> None:
            self._graph = AcherionGraph(nodes=[])
            self._preview_reference_values = {}

        def _node_by_id(self, node_id: str) -> AcherionNode | None:
            for node in self._graph.nodes:
                if node.node_id == node_id:
                    return node
            return None

        @staticmethod
        def _pure_node_id(source_id: str) -> str:
            return str(source_id).split('@', 1)[0]

        @staticmethod
        def _source_pin_index(source_id: str) -> int:
            if '@' not in str(source_id):
                return 0
            return int(str(source_id).split('@', 1)[1] or 0)

    owner = _DummyOwner()
    list_node = AcherionNode(
        node_id='list1',
        kind='make_list',
        params={'arg_count': 2, 'arg_sources': ['', '']},
    )
    owner._graph.nodes.append(list_node)

    assert owner._resolve_instance_class_path('list1') == 'list'
    methods = _catalog_runtime.class_methods('list')
    assert 'append' in methods
    assert methods['append'].startswith('append(')


def test_class_attributes_include_declared_fields_without_instantiation(
    monkeypatch,
) -> None:
    class _SyntheticRecord:
        __annotations__ = {
            'title': str,
            '_private_title': str,
        }
        __slots__ = ('title', 'count', '_private_count')

        def __init__(self, title: str, count: int) -> None:
            self.title = title
            self.count = count

        @property
        def summary(self) -> str:
            return f'{self.title}:{self.count}'

        def method(self) -> str:
            return self.summary

    _catalog_runtime.class_attributes.cache_clear()
    monkeypatch.setattr(
        _catalog_runtime,
        '_class_object',
        lambda _class_path: _SyntheticRecord,
    )
    monkeypatch.setattr(
        _catalog_runtime._catalog_modules,
        'path_to_module',
        lambda _class_path: 'user',
    )

    attrs = _catalog_runtime.class_attributes('user.SyntheticRecord')

    assert 'title' in attrs
    assert 'count' in attrs
    assert 'summary' in attrs
    assert 'method' not in attrs
    assert '_private_title' not in attrs
    assert '_private_count' not in attrs


def test_clear_catalog_runtime_caches_resets_attribute_and_method_lookups(
    monkeypatch,
) -> None:
    class _FirstRecord:
        @property
        def alpha(self) -> int:
            return 1

        def ping(self) -> int:
            return 1

    class _SecondRecord:
        @property
        def beta(self) -> int:
            return 2

        def pong(self) -> int:
            return 2

    current_cls = {'value': _FirstRecord}

    _catalog_runtime.class_attributes.cache_clear()
    _catalog_runtime.class_methods.cache_clear()
    _catalog_runtime.method_func_entry.cache_clear()
    monkeypatch.setattr(
        _catalog_runtime,
        '_class_object',
        lambda _class_path: current_cls['value'],
    )

    first_attrs = _catalog_runtime.class_attributes('user.Record')
    first_method = _catalog_runtime.method_func_entry('user.Record', 'ping')

    assert 'alpha' in first_attrs
    assert first_method is not None
    assert first_method.signature.startswith('user.Record.ping(')

    current_cls['value'] = _SecondRecord
    _catalog_runtime.clear_catalog_runtime_caches()

    second_attrs = _catalog_runtime.class_attributes('user.Record')
    second_method = _catalog_runtime.method_func_entry('user.Record', 'pong')

    assert 'beta' in second_attrs
    assert 'alpha' not in second_attrs
    assert second_method is not None
    assert second_method.signature.startswith('user.Record.pong(')


def _capture_editor_number_call(monkeypatch, node: AcherionNode) -> dict[str, object]:
    calls: list[dict[str, object]] = []

    class _StubUiElement:
        def props(self, _value):
            return self

        def classes(self, _value):
            return self

    def _fake_number(*args, **kwargs):
        calls.append({'args': args, 'kwargs': kwargs})
        return _StubUiElement()

    class _StubEditor(acherion_render_editor._RenderEditorMixin):
        def __init__(self) -> None:
            self._host = None

        def _is_system_sink_node(self, _node: AcherionNode) -> bool:
            return False

    monkeypatch.setattr(
        acherion_render_editor,
        'get_acherion_node_definition',
        lambda _kind: None,
    )
    monkeypatch.setattr(
        acherion_render_editor.ui,
        'input',
        lambda *args, **kwargs: _StubUiElement(),
    )
    monkeypatch.setattr(
        acherion_render_editor.ui,
        'label',
        lambda *args, **kwargs: _StubUiElement(),
    )
    monkeypatch.setattr(acherion_render_editor.ui, 'number', _fake_number)

    _StubEditor()._render_node_config_fields(node)

    assert calls
    return calls[0]


def test_make_list_editor_uses_numeric_number_bounds(monkeypatch) -> None:
    call = _capture_editor_number_call(
        monkeypatch,
        AcherionNode(
            node_id='list',
            kind='make_list',
            params={'arg_count': 3},
        ),
    )

    kwargs = call['kwargs']

    assert kwargs['min'] == 0
    assert isinstance(kwargs['min'], int)
    assert kwargs['step'] == 1
    assert isinstance(kwargs['step'], int)


def test_sequencer_editor_uses_numeric_number_bounds(monkeypatch) -> None:
    call = _capture_editor_number_call(
        monkeypatch,
        AcherionNode(
            node_id='seq',
            kind='sequencer',
            params={'then_count': 4},
        ),
    )

    kwargs = call['kwargs']

    assert kwargs['min'] == 2
    assert isinstance(kwargs['min'], int)
    assert kwargs['max'] == 8
    assert isinstance(kwargs['max'], int)
    assert kwargs['step'] == 1
    assert isinstance(kwargs['step'], int)


def test_client_js_batches_connection_updates_in_hot_paths() -> None:
    assert (
        "return JSON.stringify(String(value ?? '')).slice(1, -1);"
        in GRAPH_JS
    )
    assert "String(pinIndex ?? '')" in GRAPH_JS
    assert 'queueConnectionUpdate(stage)' in GRAPH_JS
    assert 'stage.__oeAcherionConnectionUpdateQueued' in GRAPH_JS
    assert 'connectionPaths(stage, nodeIds)' in GRAPH_JS
    assert 'if (seen.has(path)) return;' in GRAPH_JS
    assert 'path.className ||' not in GRAPH_JS
    assert 'this.queueConnectionUpdate(stage, [nodeId]);' in GRAPH_JS
    assert 'const pinCenter = (nodeId, direction, pinIndex) => {' in GRAPH_JS
    assert 'this.queueConnectionUpdate(stage);' not in VIEWPORT_JS


def test_plot_figure_codegen_uses_shared_go_runtime_global() -> None:
    graph = AcherionGraph(
        nodes=[
            AcherionNode(
                node_id='x1',
                kind='constant',
                params={
                    'value_type': 'int',
                    'number_value': 1,
                },
            ),
            AcherionNode(
                node_id='x2',
                kind='constant',
                params={
                    'value_type': 'int',
                    'number_value': 2,
                },
            ),
            AcherionNode(
                node_id='xs',
                kind='make_list',
                title='X Values',
                params={
                    'arg_sources': ['x1', 'x2'],
                },
            ),
            AcherionNode(
                node_id='y1',
                kind='constant',
                params={
                    'value_type': 'int',
                    'number_value': 3,
                },
            ),
            AcherionNode(
                node_id='y2',
                kind='constant',
                params={
                    'value_type': 'int',
                    'number_value': 4,
                },
            ),
            AcherionNode(
                node_id='ys',
                kind='make_list',
                title='Y Values',
                params={
                    'arg_sources': ['y1', 'y2'],
                },
            ),
            AcherionNode(
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

    source_code = compile_acherion_graph(graph)

    assert 'import plotly.graph_objects as _go' not in source_code
    assert 'go.Figure(' in source_code
    assert 'go.Scatter(' in source_code

    preview = run_standalone_acherion_preview(graph)
    figure = preview.reference_values['fig']

    assert isinstance(figure, go.Figure)
    assert tuple(figure.data[0].x) == (1, 2)
    assert tuple(figure.data[0].y) == (3, 4)
    assert figure.layout.title.text == 'Demo'


def test_plotly_template_payload_matches_dark_acherion_tokens() -> None:
    template = acherion_plotly_template_payload()

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

    payload = preview_value_plotly_payload(figure)

    assert payload is not None
    assert payload['data'][0]['type'] == 'bar'
    assert payload['layout']['title']['text'] == 'Preview'
    assert payload['layout']['template']['layout']['font']['color'] == '#E7E9EA'


def test_numpy_dependency_is_available_for_array_summaries() -> None:
    value = np.array([[1, 2], [3, 4]])

    assert value.shape == (2, 2)


def test_int_typed_pin_literals_are_coerced_before_preview_runtime() -> None:
    class _DummyPinRenderer(_RenderPinsMixin):
        def __init__(self) -> None:
            self.change_count = 0

        def _notify_change(self) -> None:
            self.change_count += 1

    renderer = _DummyPinRenderer()
    node = AcherionNode(
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


def test_custom_function_parser_accepts_plain_function_signature() -> None:
    class _DummyCatalog(_GraphOpsCatalogMixin):
        pass

    data, error = _DummyCatalog()._parse_custom_function_source(
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
    class _DummyCustomFunctionOwner(_GraphOpsCatalogMixin, _GraphOpsPinsMixin):
        def __init__(self) -> None:
            self._graph = AcherionGraph(nodes=[], user_functions={})

    owner = _DummyCustomFunctionOwner()
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
        AcherionNode(
            node_id='cf1',
            kind='custom_function',
            params={'function_path': function_path},
        )
    )

    assert pins == [{'pin_id': 'value', 'label': 'result', 'type': 'any'}]


def test_new_custom_functions_get_sequential_default_names() -> None:
    class _DummyCustomFunctionOwner(_GraphOpsCatalogMixin):
        def __init__(self) -> None:
            self._graph = AcherionGraph(nodes=[], user_functions={})

    owner = _DummyCustomFunctionOwner()
    first = AcherionNode(
        node_id='cf1',
        kind='custom_function',
        title='Custom Function',
        params=custom_function_params('cf1'),
    )
    owner._ensure_custom_function_entry(first)
    owner._graph.nodes.append(first)

    second = AcherionNode(
        node_id='cf2',
        kind='custom_function',
        title='Custom Function',
        params=custom_function_params('cf2'),
    )
    owner._ensure_custom_function_entry(second)

    assert first.params['function_path'] == 'user.custom_function_1'
    assert second.params['function_path'] == 'user.custom_function_2'
    assert 'user.custom_function_1' in owner._graph.user_functions
    assert 'user.custom_function_2' in owner._graph.user_functions


def test_legacy_self_custom_function_runtime_runs_without_migration() -> None:
    function_path = 'user.custom_function_a3ca1e8c'
    graph = AcherionGraph(
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

    source_code = compile_acherion_graph(graph)
    namespace = load_acherion_graph_namespace(source_code)

    assert "return __acherion_fn(globals().get('self'), *args)" in source_code
    assert namespace['custom_function_a3ca1e8c'](2) == 3