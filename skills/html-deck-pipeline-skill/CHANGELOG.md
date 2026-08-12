# Changelog

## v1.2.0 (2026-05-20) — Multi-Monitor & Layout Polish

### Added
- **DPI/multi-monitor adaptation** — `ResizeObserver` on `#deck-shell` + `matchMedia` listener for `devicePixelRatio` changes; deck auto-scales when window moves between monitors with different DPI scaling
- **Multi-config management UI** — config-select dropdown, +config/-config buttons for registering/removing slide decks at runtime
- **Prev/Next navigation buttons** in kbd-hint bar
- **`style/shared.css`** support — cross-chapter shared stylesheet link in index.html
- **CSS cache busting** — `_cssCacheBust` timestamp appended to part CSS and shared.css URLs for cache-free reloads
- **`slide-counter` overlay** repositioned inside `deck-wrap` for better z-stacking

### Changed
- **deck.js** — `setPart()` returns Promise (awaits CSS load); `reloadSharedCss()` returns Promise; added `_eventHandlers` tracking and `_uiBound` guard; `preloadAllPartCss()` optimization; **PPTX button now shows tradeoff dialog** (html2canvas limits vs Playwright recommendation); **export HTML fix** — `#deck-shell` uses flexbox centering + `.deck` uses `max-width: calc(100vh * 16 / 9)` to enforce 16:9 aspect ratio; inline JS preserves exported theme/fontsize attributes via HTML attribute fallback + `SLIDE_PARTS` array with `#deck-shell` class switching for part-specific CSS
- **html-deck-to-pptx SKILL.md** — added timing guidance (800-1000ms per slide, wait for fade-in animation + fonts); updated default viewport to 1600×900; documented html2canvas limitations
- **base.css** — added `deck-wrap` wrapper with `max-width: 1600px` constraint for better layout on ultra-wide displays
- **index.html** — restructured with `deck-wrap`, config management buttons, prev/next buttons, `style/shared.css` link, `editor.css` link
- **serve.py** — multi-target support with config registration/removal endpoints; improved error handling for missing `slides-config.json`

## v1.1.0 (2026-05-14) — Editor Enhancement Release

### Added
- **WYSIWYG style editor** with property panel (color, typography, spacing, border, size)
- **Undo/redo system** (Ctrl+Z/Y) with Command pattern, covering 8 mutation types
- **Element drag-to-rearrange** within grid containers (HTML5 Drag and Drop)
- **Add-component palette** (panel, card, tip-box, stat-card, insight-card, quote-box, highlight-box, image)
- **Multi-select** (Shift+click) with align and distribute controls
- **Text editing** (double-click → contentEditable) with rich text toolbar (bold/italic/underline/strikethrough/color)
- **Element clone/duplicate** button
- **Custom exit confirm dialog** with pending change summary
- **Debug logger** system (`logger.js`) with auto-save and log rotation
- **Config injection** — serve.py injects `window.__CONFIG` from `config.json`
- **serve.py `--watch` mode** — SSE-based hot-reload on file changes
- **Theme token validation** script (`scripts/validate_tokens.py`) with WCAG contrast checks
- **Automated test suite** — 106 unit tests + E2E Playwright tests
- New reference: `20-container-engine-spec.md`

### Changed
- Refactored editor.js to use shared state via `window.__editorState` (from `editor-state.js`)
- Expanded `config.json` with editor, components, and server sections
- Cleaned up examples/ — removed stale CSS directories

## v1.0.0 — Initial Release

### Core
- Six-stage pipeline: 问询 (A) → 架构 (B) → 分镜 (C) → 生成 (D) → 验收 (E) → 归档 (F)
- Container engine: serve.py + deck.js + CSS 3-layer architecture
- 4 themes (dark, dark-2, light, qclaw) × 3 fontsize schemes
- Hash routing, keyboard navigation, auto-scale
- Single-file HTML export + PPTX export
- Style contract creation mode
- 19 reference documents, templates, helper scripts
