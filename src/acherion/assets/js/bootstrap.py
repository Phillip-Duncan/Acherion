"""Bootstrap JavaScript for the Acherion render surface."""

from __future__ import annotations

BOOTSTRAP_JS = """
    let observeQueued = false;
    const queueObserveAll = () => {
        if (observeQueued) return;
        observeQueued = true;
        requestAnimationFrame(() => {
            observeQueued = false;
            window.__oeAcherion?.observeAll(document);
        });
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', queueObserveAll, {
            once: true,
        });
    } else {
        queueObserveAll();
    }

    const bodyObserver = new MutationObserver(queueObserveAll);
    const observeBody = () => {
        if (!document.body) {
            requestAnimationFrame(observeBody);
            return;
        }
        bodyObserver.observe(document.body, {
            childList: true,
            subtree: true,
        });
        queueObserveAll();
    };
    observeBody();
"""

__all__ = ['BOOTSTRAP_JS']