# Changelog

All notable changes to this project will be documented in this file.

<!-- version list -->

## v0.9.2 (2026-06-09)

### Bug Fixes

- **compiler**: Re-emit branch-local value deps for merged exec flows
  ([`2d2891d`](https://github.com/Phillip-Duncan/Acherion/commit/2d2891d58e94baf604ed94bc854784302b78d7d1))


## v0.9.1 (2026-06-08)

### Bug Fixes

- **compiler**: Bind unread exec-gated callables to None on value wires
  ([`59331bd`](https://github.com/Phillip-Duncan/Acherion/commit/59331bdf5f46e590f0ea6aac5640994cae9a3207))


## v0.9.0 (2026-06-08)

### Features

- **designer**: Add reroute nodes, draft wires, and grid-aligned pins
  ([`6229db7`](https://github.com/Phillip-Duncan/Acherion/commit/6229db7231688236dc03e5cad532727a20b80887))


## v0.8.1 (2026-06-06)

### Performance Improvements

- **graph**: Reduce redraw overhead for large node graphs
  ([`18a6dfd`](https://github.com/Phillip-Duncan/Acherion/commit/18a6dfdc59077a72ada8b58ec4c1d40d15c7c7d8))


## v0.8.0 (2026-06-04)

### Bug Fixes

- **graph**: Clear pins and compile list bounds from pin inputs
  ([`182276c`](https://github.com/Phillip-Duncan/Acherion/commit/182276ce7cdca7cb7b09c420cbf82d931e084560))

### Features

- Add else-if branching and inline pin editors
  ([`1f7237e`](https://github.com/Phillip-Duncan/Acherion/commit/1f7237eb7b00ca6b7d5f1c91f6590e20d3d26062))

- **render**: Support inline svg node icons
  ([`d59a5e0`](https://github.com/Phillip-Duncan/Acherion/commit/d59a5e0a18939cc4ea6da37558dc5601b83a8f39))


## v0.7.2 (2026-05-29)

### Bug Fixes

- **embed**: Stabilize inline node editing focus and preview updates
  ([`7a075c2`](https://github.com/Phillip-Duncan/Acherion/commit/7a075c2a7240944ceed6bef7831204cc84ba514d))


## v0.7.1 (2026-05-27)

### Bug Fixes

- **release**: Guard changelog generation and backfill v0.7.0
  ([`1cc109b`](https://github.com/Phillip-Duncan/Acherion/commit/1cc109b7673659f8035cd280ce5de88e72efe4e3))


## v0.7.0 (2026-05-27)

### Bug Fixes

- Align help title with search box top
  ([`d82acdd`](https://github.com/Phillip-Duncan/Acherion/commit/d82acdddde44b67e65a211313955c96cfbd7e68e))

### Features

- Add undo and redo history for graph edits
  ([`95f3819`](https://github.com/Phillip-Duncan/Acherion/commit/95f38190e0deafde3913180f711f60aea703dd8a))
- Add searchable help dialog and simplify workbench menus
  ([`839e152`](https://github.com/Phillip-Duncan/Acherion/commit/839e1528f49f7f3f3cd7cd1af0eab76d8956f5b1))


## v0.6.0 (2026-05-27)

### Bug Fixes

- Tighten copy/paste behavior and usability
  ([`8ef0ea3`](https://github.com/Phillip-Duncan/Acherion/commit/8ef0ea351e25bcf28a1a4b05ab98619c90f97da5))

### Features

- Add node copy/paste with cursor-aware paste
  ([`e2efd92`](https://github.com/Phillip-Duncan/Acherion/commit/e2efd92f14097d38a607d407494575b825f3d3a6))


## v0.5.3 (2026-05-11)

### Bug Fixes

- Preserve structured preview references
  ([`31f1359`](https://github.com/Phillip-Duncan/Acherion/commit/31f1359))


## v0.5.2 (2026-05-11)

### Bug Fixes

- Propagate loop item object types through runtime state
  ([`517855a`](https://github.com/Phillip-Duncan/Acherion/commit/517855a))


## v0.5.1 (2026-05-11)

### Bug Fixes

- Preserve exec flow for canonical source ids in compiler output
  ([`9a435f4`](https://github.com/Phillip-Duncan/Acherion/commit/9a435f4))


## v0.5.0 (2026-05-10)

### Features

- Add inline node control extension hooks
  ([`a319a8f`](https://github.com/Phillip-Duncan/Acherion/commit/a319a8f))


## v0.4.0 (2026-05-10)

### Features

- Add collection nodes and palette tree
  ([`33bdc10`](https://github.com/Phillip-Duncan/Acherion/commit/33bdc10))


## v0.3.1 (2026-05-10)

### Performance Improvements

- Optimize graph wire updates during drag and zoom
  ([`177351e`](https://github.com/Phillip-Duncan/Acherion/commit/177351e))


## v0.3.0 (2026-05-09)

### Features

- Add persistent workbench preferences and shared shortcut config
  ([`17533b7`](https://github.com/Phillip-Duncan/Acherion/commit/17533b7fd15b4eaac09e05adf43c8d29717bb785))


## v0.2.2 (2026-05-09)

### Bug Fixes

- Stabilize preview execution and custom function behavior
  ([`4376c49`](https://github.com/Phillip-Duncan/Acherion/commit/4376c49))


## v0.2.1 (2026-05-09)

### Bug Fixes

- Improve package presentation branding
  ([`efbe0b7`](https://github.com/Phillip-Duncan/Acherion/commit/efbe0b7281526a589e4dab9731ca71f454e734aa))


## v0.2.0 (2026-05-09)

### Features

- Add contributing guide and regression coverage
  ([`21df8fa`](https://github.com/Phillip-Duncan/Acherion/commit/21df8fa9fab76dcd1fd459a8b71d4705e6f0780f))
