"""JavaScript fragments for Acherion asset bundles."""

from __future__ import annotations

from acherion.assets.js.bootstrap import BOOTSTRAP_JS
from acherion.assets.js.core import CORE_JS
from acherion.assets.js.graph import GRAPH_JS
from acherion.assets.js.sidebar import SIDEBAR_JS
from acherion.assets.js.viewport import VIEWPORT_JS


def _build_client_js() -> str:
	"""Return the compiled JavaScript bundle for the designer workbench."""
	object_body = '\n'.join((
		CORE_JS,
		SIDEBAR_JS,
		VIEWPORT_JS,
		GRAPH_JS,
	))
	return """
(() => {
	if (window.__oeAcherion) return;
	window.__oeAcherion = {
__ACH_OBJECT_BODY__
	};

__ACH_BOOTSTRAP__
})();
""".replace(
		'__ACH_OBJECT_BODY__',
		object_body.rstrip(),
	).replace(
		'__ACH_BOOTSTRAP__',
		BOOTSTRAP_JS.rstrip(),
	)


CLIENT_JS = _build_client_js()

__all__ = ['CLIENT_JS']