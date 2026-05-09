"""Shared Acherion Python CodeMirror helpers."""

from __future__ import annotations

from typing import Any, Callable, Literal, cast

from nicegui import ui


def inject_python_autocomplete(editor_id: int) -> None:
    """Inject Python completion, hover, and signature help into editor."""
    _js = r"""
(async () => {
    if (!document.getElementById('oe-lsp-styles')) {
        const s = document.createElement('style');
        s.id = 'oe-lsp-styles';
        s.textContent = `
            .oe-lsp-hover {
                position: fixed; z-index: 10000;
                background: #000000; border: 1px solid #2f3336;
                border-radius: 4px; padding: 8px 12px;
                font-family: monospace; font-size: 13px;
                color: #e7e9ea; max-width: 520px; max-height: 320px;
                overflow: auto; white-space: pre-wrap;
                pointer-events: auto;
            }
            .oe-lsp-sig {
                position: fixed; z-index: 10000;
                background: #000000; border: 1px solid #2f3336;
                border-radius: 4px; padding: 4px 10px;
                font-family: monospace; font-size: 13px;
                color: #e7e9ea; max-width: 640px;
                overflow: hidden; pointer-events: none;
            }
            .oe-lsp-sig .sig-active { color: #1d9bf0; font-weight: bold; }
        `;
        document.head.appendChild(s);
    }

    const CM = await import("nicegui-codemirror");
    const el = getElement(_EID_);
    if (!el) return;
    await el.editorPromise;
    const editor = el.editor;

    function escHtml(s) {
        return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    const complete = async (ctx) => {
        if (!ctx.explicit && !ctx.matchBefore(/[\w.]/)) return null;
        const line = ctx.state.doc.lineAt(ctx.pos);
        try {
            const resp = await fetch("/api/py-completions", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    code: ctx.state.doc.toString(),
                    row: line.number - 1,
                    col: ctx.pos - line.from,
                }),
            });
            if (!resp.ok) return null;
            const { completions } = await resp.json();
            if (!completions?.length) return null;
            const word = ctx.matchBefore(/\w+/);
            const typeMap = {
                function: "function", class: "class",
                module: "namespace", keyword: "keyword",
            };
            return {
                from: word ? word.from : ctx.pos,
                validFor: /^\w*$/,
                options: completions.map(c => ({
                    label: c.name,
                    type: typeMap[c.type] ?? "variable",
                    detail: c.description || undefined,
                })),
            };
        } catch (_) { return null; }
    };

    editor.dispatch({
        effects: CM.StateEffect.appendConfig.of(
            CM.EditorState.languageData.of(() => [{ autocomplete: complete }])
        ),
    });

    let hoverEl = null, hoverTimer = null, _hoverPinned = false;
    function removeHover() {
        if (hoverEl) { hoverEl.remove(); hoverEl = null; }
        _hoverPinned = false;
    }

    editor.dom.addEventListener('mousemove', (e) => {
        clearTimeout(hoverTimer);
        hoverTimer = setTimeout(async () => {
            const pos = editor.posAtCoords({ x: e.clientX, y: e.clientY });
            if (pos == null) { removeHover(); return; }
            const doc = editor.state.doc;
            const charAt = pos < doc.length ? doc.sliceString(pos, pos + 1) : '';
            const charBefore = pos > 0 ? doc.sliceString(pos - 1, pos) : '';
            const isWord = (c) => /\w/.test(c);
            if (!isWord(charAt) && !isWord(charBefore)) { removeHover(); return; }
            const line = editor.state.doc.lineAt(pos);
            try {
                const resp = await fetch('/api/py-hover', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        code: editor.state.doc.toString(),
                        row: line.number - 1,
                        col: pos - line.from,
                    }),
                });
                if (!resp.ok) { removeHover(); return; }
                const { docs } = await resp.json();
                if (!docs?.trim()) { removeHover(); return; }
                removeHover();
                const coords = editor.coordsAtPos(pos);
                if (!coords) return;
                hoverEl = document.createElement('div');
                hoverEl.className = 'oe-lsp-hover';
                hoverEl.textContent = docs;
                hoverEl.addEventListener('mouseenter', () => { _hoverPinned = true; });
                hoverEl.addEventListener('mouseleave', () => { _hoverPinned = false; removeHover(); });
                document.body.appendChild(hoverEl);
                let top = coords.bottom + 6;
                if (top + 240 > window.innerHeight) top = coords.top - 240;
                hoverEl.style.left =
                    Math.min(coords.left, window.innerWidth - 530) + 'px';
                hoverEl.style.top = Math.max(4, top) + 'px';
            } catch (_) { removeHover(); }
        }, 420);
    });

    editor.dom.addEventListener('mouseleave', (e) => {
        clearTimeout(hoverTimer);
        if (hoverEl && hoverEl.contains(e.relatedTarget)) return;
        if (_hoverPinned) return;
        removeHover();
    });

    editor.dispatch({
        effects: CM.StateEffect.appendConfig.of(
            CM.ViewPlugin.fromClass(class {
                constructor(view) {
                    this._view = view;
                    this._timer = null;
                    this._el = null;
                }
                update(update) {
                    if (!update.docChanged && !update.selectionSet) return;
                    clearTimeout(this._timer);
                    this._timer = setTimeout(() => this._fetch(), 160);
                }
                _removeSig() {
                    if (this._el) { this._el.remove(); this._el = null; }
                }
                async _fetch() {
                    const view = this._view;
                    const pos = view.state.selection.main.head;
                    const line = view.state.doc.lineAt(pos);
                    const before = line.text.slice(0, pos - line.from);
                    const depth = [...before].reduce(
                        (d, c) => d + (c === '(' ? 1 : c === ')' ? -1 : 0), 0
                    );
                    if (depth <= 0) { this._removeSig(); return; }
                    try {
                        const resp = await fetch('/api/py-signatures', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                code: view.state.doc.toString(),
                                row: line.number - 1,
                                col: pos - line.from,
                            }),
                        });
                        if (!resp.ok) { this._removeSig(); return; }
                        const { signatures } = await resp.json();
                        if (!signatures?.length) { this._removeSig(); return; }
                        const sig = signatures[0];
                        this._removeSig();
                        const coords = view.coordsAtPos(pos);
                        if (!coords) return;
                        this._el = document.createElement('div');
                        this._el.className = 'oe-lsp-sig';
                        const ai = sig.active ?? -1;
                        if (ai >= 0 && sig.params?.length) {
                            const pre = sig.params
                                .slice(0, ai).map(escHtml).join(', ');
                            const act = escHtml(sig.params[ai] ?? '');
                            const post = sig.params
                                .slice(ai + 1).map(escHtml).join(', ');
                            this._el.innerHTML =
                                escHtml(sig.name) + '(' +
                                (pre ? pre + ', ' : '') +
                                '<span class="sig-active">' + act + '</span>' +
                                (post ? ', ' + post : '') + ')';
                        } else {
                            this._el.textContent = sig.label;
                        }
                        document.body.appendChild(this._el);
                        const h = this._el.offsetHeight || 24;
                        const top = coords.top - h - 4;
                        this._el.style.left =
                            Math.min(coords.left, window.innerWidth - 640) + 'px';
                        this._el.style.top = Math.max(4, top) + 'px';
                    } catch (_) { this._removeSig(); }
                }
                destroy() {
                    clearTimeout(this._timer);
                    this._removeSig();
                }
            })
        ),
    });
})();
"""
    ui.run_javascript(_js.replace('_EID_', str(editor_id)))


def build_python_code_editor(
    *,
    value: str,
    theme: Any,
    on_change: Callable[..., None] | None = None,
    classes: str = 'w-full oe-code-editor',
    style: str = '',
    line_wrapping: bool = True,
) -> Any:
    """Create an Acherion-managed Python CodeMirror editor."""
    editor = ui.codemirror(  # pyright: ignore[reportArgumentType]
        value=value,
        language=cast(Literal['Python'], 'Python'),
        theme=theme,
        line_wrapping=line_wrapping,
        on_change=on_change,
    )
    if classes.strip():
        editor.classes(classes)
    if style.strip():
        editor.style(style)
    ui.timer(
        0.0,
        lambda editor_id=editor.id: inject_python_autocomplete(editor_id),
        once=True,
    )
    return editor


__all__ = ['build_python_code_editor', 'inject_python_autocomplete']