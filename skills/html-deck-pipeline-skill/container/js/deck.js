/* deck.js — HTML Deck website skeleton (config-driven) */
(() => {
  let SLIDES = [];
  let PART_LABELS = {};
  let PART_ORDER = [];

  let currentIdx = 0;
  let currentPart = 'ch01';
  let loadedPartCss = new Set();
  let _eventHandlers = {};
  let _uiBound = false;
  let _cssReady = false;

  const deck = document.getElementById('deck');
  const progressBar = document.querySelector('#deck-progress .bar');
  const partNav = document.getElementById('part-nav');
  const deckShell = document.getElementById('deck-shell');
  const slideCounter = document.getElementById('slide-counter');

  /* ── Part CSS loading (returns Promise) ── */
  let _cssCacheBust = Date.now();

  function bumpCssCacheBust() {
    _cssCacheBust = Date.now();
  }

  function loadPartCss(part) {
    if (loadedPartCss.has(part)) return Promise.resolve();
    return new Promise(resolve => {
      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = `style/${part}.css?v=${_cssCacheBust}`;
      link.id = `css-${part}`;
      link.onload = resolve;
      link.onerror = resolve;
      document.head.appendChild(link);
      loadedPartCss.add(part);
    });
  }

  function reloadSharedCss() {
    const old = document.getElementById('css-shared');
    if (old) old.remove();
    return new Promise(resolve => {
      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = `style/shared.css?v=${_cssCacheBust}`;
      link.id = 'css-shared';
      link.onload = resolve;
      link.onerror = resolve;
      document.head.appendChild(link);
    });
  }

  function preloadAllPartCss() {
    PART_ORDER.forEach(p => loadPartCss(p));
  }

  /* ── Set part class on shell (async, waits for CSS) ── */
  async function setPart(part) {
    await loadPartCss(part);
    if (currentPart === part) return;
    PART_ORDER.forEach(p => deckShell.classList.remove(`part-${p}`));
    deckShell.classList.add(`part-${part}`);
    currentPart = part;
  }

  /* ── Auto-scale current slide to fit deck vertically (no layout change) ── */
  let _scaleRAF = 0;
  function applyAutoScale() {
    cancelAnimationFrame(_scaleRAF);
    _scaleRAF = requestAnimationFrame(() => {
      // Wait for fonts to finish loading before measuring — font reflow can
      // temporarily inflate content height by 20-40px, triggering false scale.
      // Also delay after fonts.ready: when chapter CSS loads new @font-face rules,
      // the browser needs time to match rules to DOM elements and request fonts.
      // Without this delay, fonts.ready resolves before new fonts are requested.
      Promise.resolve(document.fonts.ready).then(() => new Promise(r => setTimeout(r, 60))).then(() => {
        const slideEl = deck.querySelector('.slide.active');
        if (!slideEl) return;
        slideEl.style.transform = '';
        slideEl.style.transformOrigin = '';
        slideEl.style.overflow = '';
        void slideEl.offsetHeight;
        const clientH = slideEl.clientHeight;
        const slideTop = slideEl.getBoundingClientRect().top;
        let maxBottom = 0;
        for (const child of slideEl.children) {
          const childBottom = child.getBoundingClientRect().bottom - slideTop;
          if (childBottom > maxBottom) maxBottom = childBottom;
        }
        const padBottom = parseFloat(getComputedStyle(slideEl).paddingBottom) || 0;
        const contentH = maxBottom + padBottom;
        if (contentH > clientH + 2) {
          const scale = (clientH - 1) / contentH;
          slideEl.style.transform = `scale(${scale})`;
          slideEl.style.transformOrigin = 'top center';
          slideEl.style.overflow = 'hidden';
        } else {
          slideEl.style.overflow = '';
        }
      });
    });
  }

  /* ── Load a slide ── */
  async function loadSlide(idx, retries) {
    retries = retries || 0;
    const s = SLIDES[idx];
    if (!s) return;

    // Hide deck during transition to prevent flash of old content with new styles
    deck.style.opacity = '0';

    await setPart(s.part);
    const url = `slides/${s.part}/${s.file}`;

    try {
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const html = await res.text();

      deck.innerHTML = html;
      const slideEl = deck.querySelector('.slide');
      if (slideEl) {
        slideEl.classList.add('active');
        slideEl.dataset.slideKey = s.part + '/' + s.file;
        applyAutoScale();
      }

      // Show deck after new slide is ready
      deck.style.opacity = '';

      currentIdx = idx;
      updateProgress();
      updatePartNav();
      updateHash();
      // Editor hook: notify editor that a new slide has loaded
      if (window.__deckAPI && typeof window.__deckAPI.onSlideLoaded === 'function') {
        window.__deckAPI.onSlideLoaded();
      }
    } catch (err) {
      if (retries < 2) {
        console.warn('Retrying slide load (' + (retries + 1) + '/2): ' + url);
        await new Promise(function(r) { setTimeout(r, 500); });
        return loadSlide(idx, retries + 1);
      }
      deck.innerHTML = `<div style="display:flex;align-items:center;justify-content:center;height:100%;color:var(--risk);"><p>加载失败: ${url} — ${err.message}</p></div>`;
    }
  }

  /* ── Navigate ── */
  function next() { if (currentIdx < SLIDES.length - 1) loadSlide(currentIdx + 1); }
  function prev() { if (currentIdx > 0) loadSlide(currentIdx - 1); }

  function goToPart(part) {
    const idx = SLIDES.findIndex(s => s.part === part);
    if (idx >= 0) loadSlide(idx);
  }

  /* ── Progress bar + counter ── */
  function updateProgress() {
    const cur = currentIdx + 1;
    const total = SLIDES.length;
    const pct = (cur / total * 100).toFixed(1);
    if (progressBar) progressBar.style.width = pct + '%';
    if (slideCounter) slideCounter.textContent = String(cur).padStart(2, '0') + ' / ' + String(total).padStart(2, '0');
  }

  /* ── Part nav buttons ── */
  function buildPartNav() {
    if (!partNav) return;
    PART_ORDER.forEach(part => {
      const btn = document.createElement('button');
      btn.textContent = PART_LABELS[part];
      btn.addEventListener('click', () => goToPart(part));
      btn.dataset.part = part;
      partNav.appendChild(btn);
    });
  }

  function updatePartNav() {
    if (!partNav) return;
    partNav.querySelectorAll('button').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.part === currentPart);
    });
  }

  /* ── Hash routing ── */
  function updateHash() {
    const s = SLIDES[currentIdx];
    history.replaceState(null, '', `#${s.part}/${s.file.replace('.html','')}`);
  }

  function resolveHash() {
    const hash = window.location.hash.slice(1);
    if (!hash) return 0;
    // Match: ch03/02-feedback or ch03/2
    const parts = hash.split('/');
    if (parts.length < 2) return 0;

    const [part, slug] = parts;
    // Try by file slug first
    let idx = SLIDES.findIndex(s => s.part === part && s.file.replace('.html','') === slug);
    // Try by index within part
    if (idx < 0 && /^\d+$/.test(slug)) {
      const n = parseInt(slug, 10) - 1;
      const partSlides = SLIDES.reduce((acc, s, i) => { if (s.part === part) acc.push(i); return acc; }, []);
      if (n >= 0 && n < partSlides.length) idx = partSlides[n];
    }
    return idx >= 0 ? idx : 0;
  }

  /* ── Keyboard ── */
  function onKey(e) {
    // Don't trap if user is in an input (allow Ctrl+E regardless)
    if (e.ctrlKey && e.key === 'e') {
      e.preventDefault();
      if (window.__editor && window.__editor.toggle) window.__editor.toggle();
      return;
    }
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.isContentEditable) return;
    if (e.key === 'ArrowRight' || e.key === 'ArrowDown' || e.key === ' ') {
      e.preventDefault();
      next();
    } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
      e.preventDefault();
      prev();
    }
  }

  /* ── Config ── */
  let deckConfig = null;  // { themes: [...], fontsizes: [...] }

  async function loadConfig() {
    try {
      const res = await fetch('css/config.yaml');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const text = await res.text();
      // Minimal YAML parser for our simple structure
      deckConfig = parseSimpleYaml(text);
    } catch(e) {
      console.warn('Failed to load config.yaml, using defaults', e);
      deckConfig = {
        themes: [{ id: 'dark-theme-2', label: '暗色2', default: true }],
        fontsizes: [{ id: 'standard', label: '标准', default: true }]
      };
    }
  }

  function parseSimpleYaml(text) {
    // Parse a simple two-level YAML with list items
    const result = {};
    let section = null;
    for (const line of text.split('\n')) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith('#')) continue;
      if (!line.startsWith(' ')) {
        section = trimmed.replace(/:.*$/, '');
        result[section] = [];
      } else if (section && trimmed.startsWith('- id:')) {
        const item = {};
        item.id = trimmed.replace(/- id:\s*/, '').trim();
        result[section].push(item);
      } else if (section && trimmed.startsWith('label:')) {
        const last = result[section][result[section].length - 1];
        if (last) last.label = trimmed.replace(/label:\s*/, '').trim();
      } else if (section && trimmed.startsWith('default:')) {
        const last = result[section][result[section].length - 1];
        if (last) last.default = trimmed.replace(/default:\s*/, '').trim() === 'true';
      }
    }
    return result;
  }

  function themeIds() { return (deckConfig?.themes || []).map(t => t.id); }
  function fontsizeIds() { return (deckConfig?.fontsizes || []).map(f => f.id); }
  function themeLabel(id) { const t = (deckConfig?.themes || []).find(t => t.id === id); return t ? t.label : id; }
  function defaultThemeId() { const t = (deckConfig?.themes || []).find(t => t.default); return t ? t.id : (deckConfig?.themes || [])[0]?.id || 'dark-theme-2'; }
  function defaultFontsizeId() { const f = (deckConfig?.fontsizes || []).find(f => f.default); return f ? f.id : (deckConfig?.fontsizes || [])[0]?.id || 'standard'; }

  /* ── Theme switching ── */
  const THEME_KEY = 'deck-theme';
  const THEME_CSS = ['tokens.css'];
  const SHARED_CSS = ['css/common/base.css', 'css/common/components.css'];

  function getTheme() {
    try {
      const stored = localStorage.getItem(THEME_KEY);
      const ids = themeIds();
      if (stored && ids.includes(stored)) return stored;
    } catch(e) {}
    return defaultThemeId();
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    // Swap CSS link hrefs to point to the selected theme directory
    const links = document.querySelectorAll('link[rel="stylesheet"][href^="css/"]');
    links.forEach(link => {
      // Extract filename from current href (e.g. "css/dark-theme-2/tokens.css" → "tokens.css")
      const parts = link.href.split('/');
      const file = parts[parts.length - 1];
      if (THEME_CSS.includes(file)) {
        link.href = `css/theme/${theme}/${file}`;
      }
    });
    const sel = document.getElementById('theme-select');
    if (sel) sel.value = theme;
  }

  function onThemeChange() {
    const sel = document.getElementById('theme-select');
    if (!sel) return;
    const theme = sel.value;
    try { localStorage.setItem(THEME_KEY, theme); } catch(e) {}
    applyTheme(theme);
  }

  function initTheme() {
    applyTheme(getTheme());
  }

  /* ── Font-size switching ── */
  const FONTSIZE_KEY = 'deck-fontsize';

  function getFontSize() {
    try {
      const stored = localStorage.getItem(FONTSIZE_KEY);
      const ids = fontsizeIds();
      if (stored && ids.includes(stored)) return stored;
    } catch(e) {}
    return defaultFontsizeId();
  }

  function applyFontSize(fontsize) {
    document.documentElement.setAttribute('data-font-size', fontsize);
    const links = document.querySelectorAll('link[rel="stylesheet"][href^="css/fontsize/"]');
    links.forEach(link => {
      link.href = `css/fontsize/${fontsize}.css`;
    });
    const sel = document.getElementById('fontsize-select');
    if (sel) sel.value = fontsize;
  }

  function onFontSizeChange() {
    const sel = document.getElementById('fontsize-select');
    if (!sel) return;
    const fontsize = sel.value;
    try { localStorage.setItem(FONTSIZE_KEY, fontsize); } catch(e) {}
    applyFontSize(fontsize);
  }

  function initFontSize() {
    applyFontSize(getFontSize());
  }

  function buildSelectors() {
    const themeSel = document.getElementById('theme-select');
    if (themeSel && deckConfig?.themes) {
      themeSel.innerHTML = '';
      for (const t of deckConfig.themes) {
        const opt = document.createElement('option');
        opt.value = t.id;
        opt.textContent = t.label;
        themeSel.appendChild(opt);
      }
    }
    const fontsizeSel = document.getElementById('fontsize-select');
    if (fontsizeSel && deckConfig?.fontsizes) {
      fontsizeSel.innerHTML = '';
      for (const f of deckConfig.fontsizes) {
        const opt = document.createElement('option');
        opt.value = f.id;
        opt.textContent = f.label;
        fontsizeSel.appendChild(opt);
      }
    }
  }

  /* ── Export single static HTML ── */

  async function exportToSingleHTML() {
    const exportBtn = document.getElementById('export-btn');
    if (exportBtn) {
      exportBtn.textContent = '导出中…';
      exportBtn.disabled = true;
    }

    try {
      // 1. Fetch all CSS
      const theme = getTheme();
      const fontsize = getFontSize();
      const themeCssPaths = THEME_CSS.map(f => `css/theme/${theme}/${f}`);
      const fontsizeCssPath = `css/fontsize/${fontsize}.css`;
      const allCssParts = PART_ORDER.map(p => `style/${p}.css`);
      const cssPaths = [...SHARED_CSS, 'style/shared.css', ...themeCssPaths, fontsizeCssPath, ...allCssParts];
      const cssTexts = await Promise.all(cssPaths.map(async path => {
        try {
          const res = await fetch(path);
          return res.ok ? await res.text() : `/* ${path} not found */`;
        } catch { return `/* ${path} failed */`; }
      }));
      const allCss = cssTexts.join('\n');

      // Inject editor customizations if available
      let editorOverrides = '';
      if (window.__editor && typeof window.__editor.getCSSOverrides === 'function') {
        editorOverrides = window.__editor.getCSSOverrides();
      }

      // 2. Fetch all slides
      const slideHtmls = await Promise.all(SLIDES.map(async s => {
        try {
          const res = await fetch(`slides/${s.part}/${s.file}`);
          return res.ok ? await res.text() : `<!-- ${s.file} load failed -->`;
        } catch { return `<!-- ${s.file} load failed -->`; }
      }));

      // 3. Build the exported document
      const slidesHtml = slideHtmls.map((html, i) => {
        const s = SLIDES[i];
        // Make first slide active, rest hidden
        return html.replace(
          /class="slide\s+active"/,
          'class="slide active"'
        ).replace(
          /class="slide"/,
          i === 0 ? 'class="slide active"' : 'class="slide"'
        ).replace(
          /<section class="slide">/,
          i === 0 ? '<section class="slide active">' : '<section class="slide">'
        );
      }).join('\n');

      const title = document.title || 'HTML Deck';

      const themeNamesJson = JSON.stringify((deckConfig?.themes || []).map(t => t.id));
      const fontsizeNamesJson = JSON.stringify((deckConfig?.fontsizes || []).map(f => f.id));
      const defaultTheme = defaultThemeId();
      const defaultFontsize = defaultFontsizeId();
      const currentTheme = getTheme();
      const currentFontsize = getFontSize();

      const exportedHtml = `<!doctype html>
<html lang="zh-CN" data-theme="${currentTheme}" data-font-size="${currentFontsize}">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>${title}</title>
  <style>
${allCss}
${editorOverrides}
  </style>
  <style>
    /* Export mode: hide shell chrome, show all slides as stack */
    #part-nav, #deck-progress, #kbd-hint, #export-btn, #theme-select, #pptx-btn, #fontsize-select, #editor-toggle-btn, #slide-counter { display: none; }
    .slide .header .num { display: inline; }
    #deck-shell { display: flex; justify-content: center; align-items: center; height: 100vh; overflow: hidden; padding: 0; }
    html, body { background-color: #040812; }
    body { background-attachment: scroll; }
    .deck { width: max(100vw, calc(100vh * 16 / 9)); height: max(100vh, calc(100vw * 9 / 16)); border-radius: 0; box-shadow: none; max-width: none; }
    .slide { display: none; }
    .slide.active { display: flex; flex-direction: column; }
  </style>
</head>
<body>
  <main id="deck-shell" class="part-ch01" aria-label="${title}">
    <div class="deck" id="deck" role="region" aria-label="幻灯片">
${slidesHtml}
    </div>
  </main>
  <script>
    (() => {
      /* Theme & Fontsize */
      const THEME_KEY = 'deck-theme';
      const FONTSIZE_KEY = 'deck-fontsize';
      const THEME_NAMES = ${themeNamesJson};
      const FONTSIZE_NAMES = ${fontsizeNamesJson};
      const DEFAULT_THEME = '${defaultTheme}';
      const DEFAULT_FONTSIZE = '${defaultFontsize}';
      const SLIDE_PARTS = ${JSON.stringify(SLIDES.map(function(s) { return s.part; }))};

      function getTheme() {
        try { const v = localStorage.getItem(THEME_KEY); if (v && THEME_NAMES.includes(v)) return v; } catch(e) {}
        return document.documentElement.getAttribute('data-theme') || DEFAULT_THEME;
      }
      function getFontsize() {
        try { const v = localStorage.getItem(FONTSIZE_KEY); if (v && FONTSIZE_NAMES.includes(v)) return v; } catch(e) {}
        return document.documentElement.getAttribute('data-font-size') || DEFAULT_FONTSIZE;
      }
      document.documentElement.setAttribute('data-theme', getTheme());
      document.documentElement.setAttribute('data-font-size', getFontsize());

      /* Slides */
      const slides = Array.from(document.querySelectorAll('.slide'));
      let idx = 0;
      function show(i) {
        slides.forEach((el, j) => el.classList.toggle('active', j === i));
        slides[i]?.classList.add('active');
        // Auto-scale — wait for fonts to avoid measuring with fallback fonts
        var el = slides[i];
        if (!el) return;
        document.getElementById('deck-shell').className = SLIDE_PARTS[i] ? 'part-' + SLIDE_PARTS[i] : 'part-ch01';
        el.style.transform = '';
        el.style.transformOrigin = '';
        el.style.overflow = '';
        Promise.resolve(document.fonts.ready).then(function() {
          return new Promise(function(r) { setTimeout(r, 60); });
        }).then(function() {
          void el.offsetHeight;
          var ch = el.clientHeight;
          var st = el.getBoundingClientRect().top;
          var mb = 0;
          for (var k = 0; k < el.children.length; k++) {
            var cb = el.children[k].getBoundingClientRect().bottom - st;
            if (cb > mb) mb = cb;
          }
          var pb = parseFloat(getComputedStyle(el).paddingBottom) || 0;
          var contentH = mb + pb;
          if (contentH > ch + 2) {
            el.style.transform = 'scale(' + ((ch - 1) / contentH) + ')';
            el.style.transformOrigin = 'top center';
            el.style.overflow = 'hidden';
          }
        });
        idx = i;
      }
      function next() { if (idx < slides.length - 1) show(idx + 1); }
      function prev() { if (idx > 0) show(idx - 1); }
      document.addEventListener('keydown', e => {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.isContentEditable) return;
        if (e.key === 'ArrowRight' || e.key === 'ArrowDown' || e.key === ' ') { e.preventDefault(); next(); }
        else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') { e.preventDefault(); prev(); }
      });
      window.addEventListener('resize', () => {
        const el = slides[idx];
        if (!el) return;
        el.style.transform = '';
        el.style.overflow = '';
        Promise.resolve(document.fonts.ready).then(function() {
          return new Promise(function(r) { setTimeout(r, 60); });
        }).then(function() {
          void el.offsetHeight;
          var ch = el.clientHeight;
          var st = el.getBoundingClientRect().top;
          var mb = 0;
          for (var k = 0; k < el.children.length; k++) {
            var cb = el.children[k].getBoundingClientRect().bottom - st;
            if (cb > mb) mb = cb;
          }
          var pb = parseFloat(getComputedStyle(el).paddingBottom) || 0;
          var contentH = mb + pb;
          if (contentH > ch + 2) {
            el.style.transform = 'scale(' + ((ch - 1) / contentH) + ')';
            el.style.transformOrigin = 'top center';
            el.style.overflow = 'hidden';
          }
        });
      });
      show(0);
    })();
  <\/script>
</body>
</html>`;

      // 4. Trigger download (with save dialog when available)
      const blob = new Blob([exportedHtml], { type: 'text/html;charset=utf-8' });
      const defaultName = `${title.replace(/[\/\\:*?"<>|]/g, '-')}-export.html`;

      if (typeof window.showSaveFilePicker === 'function') {
        try {
          const handle = await window.showSaveFilePicker({
            suggestedName: defaultName,
            types: [{ description: 'HTML 文件', accept: { 'text/html': ['.html'] } }],
          });
          const writable = await handle.createWritable();
          await writable.write(blob);
          await writable.close();
        } catch (e) {
          if (e.name !== 'AbortError') throw e; // user cancelled, silently ignore
        }
      } else {
        // Fallback: blob download to default folder
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = defaultName;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      }

      if (exportBtn) {
        exportBtn.textContent = '导出 HTML';
        exportBtn.disabled = false;
      }
    } catch (err) {
      if (exportBtn) {
        exportBtn.textContent = '导出失败';
        exportBtn.disabled = false;
      }
      console.error('Export failed:', err);
    }
  }

  /* ── Export PPTX (client-side: html2canvas + pptxgenjs) ── */
  let _pptxLibsReady = false;

  async function ensurePptxLibs() {
    if (_pptxLibsReady) return;
    if (typeof html2canvas === 'undefined') {
      await new Promise((resolve, reject) => {
        const s = document.createElement('script');
        s.src = 'https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js';
        s.onload = resolve;
        s.onerror = () => reject(new Error('html2canvas load failed'));
        document.head.appendChild(s);
      });
    }
    if (typeof PptxGenJS === 'undefined') {
      await new Promise((resolve, reject) => {
        const s = document.createElement('script');
        s.src = 'https://cdn.jsdelivr.net/npm/pptxgenjs@3.12.0/dist/pptxgen.bundle.js';
        s.onload = resolve;
        s.onerror = () => reject(new Error('pptxgenjs load failed'));
        document.head.appendChild(s);
      });
    }
    _pptxLibsReady = true;
  }

  async function exportToPPTX() {
    // Show tradeoff dialog: html2canvas has known limits vs Playwright screenshots
    var usePlaywright = confirm(
      'PPTX 导出方式选择：\n\n' +
      '【推荐】Playwright 截图（高质量）\n' +
      '  使用内置技能 html-deck-to-pptx，真实浏览器渲染，\n' +
      '  渐变/mask/伪元素完整保留，画面比例精确。\n' +
      '  在终端运行截图脚本即可。\n\n' +
      '【快速】html2canvas（当前按钮）\n' +
      '  ⚠ CSS 渐变可能丢失，画面可能轻微拉伸。\n' +
      '  适合快速预览，不适合正式交付。\n\n' +
      '点击"确定"使用 html2canvas 快速导出，\n' +
      '点击"取消"查看内置技能使用说明。'
    );

    if (!usePlaywright) {
      alert(
        '使用内置技能导出高质量 PPTX：\n\n' +
        '1. 确保已安装: pip install playwright python-pptx\n' +
        '2. 运行截图: python internal-skill/html-deck-to-pptx/scripts/screenshot_slides.py\n' +
        '   或使用项目中的 _pptx_export.py 脚本\n' +
        '3. 组装 PPTX: python internal-skill/html-deck-to-pptx/scripts/create_pptx.py\n\n' +
        '详见: .github/skills/html-deck-pipeline-skill/internal-skill/html-deck-to-pptx/SKILL.md'
      );
      return;
    }

    var pptxBtn = document.getElementById('pptx-btn');
    if (pptxBtn) {
      pptxBtn.textContent = '导出中…';
      pptxBtn.disabled = true;
    }

    try {
      await ensurePptxLibs();

      const savedIdx = currentIdx;
      const slideImages = [];

      // Resolve the theme's base background color for alpha compositing
      const rootCS = getComputedStyle(document.documentElement);
      const themeBg = rootCS.getPropertyValue('--bg').trim() || '#07111f';

      // Capture each slide
      for (let i = 0; i < SLIDES.length; i++) {
        await loadSlide(i);
        await new Promise(r => setTimeout(r, 200));

        const slideEl = deck.querySelector('.slide.active');
        if (!slideEl) continue;

        // Remove auto-scale transform so html2canvas captures at natural size
        const prevTransform = slideEl.style.transform;
        const prevTransformOrigin = slideEl.style.transformOrigin;
        slideEl.style.transform = '';
        slideEl.style.transformOrigin = '';

        const rawCanvas = await html2canvas(slideEl, {
          backgroundColor: null,
          scale: 2,
          useCORS: true,
          logging: false,
        });

        // Restore auto-scale
        slideEl.style.transform = prevTransform;
        slideEl.style.transformOrigin = prevTransformOrigin;

        // Composite onto fully opaque background to eliminate alpha channel.
        // The slide CSS gradient uses transparent/rgba() stops and many component
        // backgrounds (cards, panels, quote-boxes) use semi-transparent surface
        // tokens.  html2canvas preserves that alpha in the PNG, which looks like a
        // "frosted mask" when placed over a white PPTX background.
        // By drawing the raw capture onto a solid opaque canvas, all semi-transparent
        // pixels are alpha-blended with the theme background — matching what the
        // viewer actually sees on screen.
        const comp = document.createElement('canvas');
        comp.width = rawCanvas.width;
        comp.height = rawCanvas.height;
        const ctx = comp.getContext('2d');
        ctx.fillStyle = themeBg;
        ctx.fillRect(0, 0, comp.width, comp.height);
        ctx.drawImage(rawCanvas, 0, 0);

        slideImages.push(comp.toDataURL('image/png'));
      }

      // Restore original slide
      await loadSlide(savedIdx);

      // Build PPTX
      const pptx = new PptxGenJS();
      pptx.defineLayout({ name:'CUSTOM', width:13.333, height:7.5 });
      pptx.layout = 'CUSTOM';

      slideImages.forEach((dataUrl) => {
        const s = pptx.addSlide();
        s.addImage({ data: dataUrl, x: 0, y: 0, w: 13.333, h: 7.5 });
      });

      const title = document.title || 'HTML Deck';
      const defaultName = `${title.replace(/[\/\\:*?"<>|]/g, '-')}.pptx`;

      const pptxBlob = await pptx.write({ outputType: 'blob' });

      // Try save dialog, fallback to download link
      let saved = false;
      if (typeof window.showSaveFilePicker === 'function') {
        try {
          const handle = await window.showSaveFilePicker({
            suggestedName: defaultName,
            types: [{ description: 'PowerPoint 文件', accept: { 'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['.pptx'] } }],
          });
          const writable = await handle.createWritable();
          await writable.write(pptxBlob);
          await writable.close();
          saved = true;
        } catch (e) {
          // AbortError = user cancelled; SecurityError = lost user gesture.
          // Either way, fall through to download fallback.
          if (e.name !== 'AbortError' && e.name !== 'SecurityError') {
            console.warn('showSaveFilePicker 失败，使用下载回退:', e.name);
          }
        }
      }
      if (!saved) {
        const url = URL.createObjectURL(pptxBlob);
        const a = document.createElement('a');
        a.href = url;
        a.download = defaultName;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      }

      if (pptxBtn) {
        pptxBtn.textContent = '导出 PPTX';
        pptxBtn.disabled = false;
      }
    } catch (err) {
      if (pptxBtn) {
        pptxBtn.textContent = '导出失败';
        pptxBtn.disabled = false;
      }
      console.error('PPTX export failed:', err);
    }
  }

  /* ── Multi-slide-config management ── */

  async function loadConfigList() {
    try {
      const res = await fetch('/api/configs');
      if (!res.ok) throw new Error('HTTP ' + res.status);
      const data = await res.json();
      populateConfigDropdown(data.configs, data.active);
    } catch (err) {
      console.error('Failed to load config list:', err);
    }
  }

  function populateConfigDropdown(configs, activePath) {
    var sel = document.getElementById('config-select');
    var rmBtn = document.getElementById('config-rm-btn');
    if (!sel) return;

    sel.removeEventListener('change', onConfigSwitch);
    sel.innerHTML = '';

    if (!configs || configs.length === 0) {
      var opt = document.createElement('option');
      opt.value = '';
      opt.textContent = '(没有已注册的讲稿)';
      sel.appendChild(opt);
      if (rmBtn) rmBtn.disabled = true;
      sel.addEventListener('change', onConfigSwitch);
      return;
    }

    configs.forEach(function(c) {
      var opt = document.createElement('option');
      opt.value = c.path;
      var display = c.title || c.path.split('/').pop() || c.path;
      if (display.length > 20) {
        opt.textContent = display.substring(0, 19) + '…';
      } else {
        opt.textContent = display;
      }
      opt.title = c.title + '\n' + c.path;
      if (c.path === activePath) opt.selected = true;
      sel.appendChild(opt);
    });

    if (rmBtn) {
      rmBtn.disabled = (configs.length <= 1);
      rmBtn.style.display = '';
    }
    sel.addEventListener('change', onConfigSwitch);
  }

  function syncConfigDropdown() {
    fetch('/api/configs')
      .then(function(r) { return r.json(); })
      .then(function(data) {
        var sel = document.getElementById('config-select');
        if (!sel || !data.active) return;
        for (var i = 0; i < sel.options.length; i++) {
          sel.options[i].selected = (sel.options[i].value === data.active);
        }
      })
      .catch(function() {});
  }

  async function onConfigSwitch() {
    var sel = document.getElementById('config-select');
    if (!sel || !sel.value) return;

    try {
      var res = await fetch('/api/configs/activate?path=' + encodeURIComponent(sel.value), { method: 'POST' });
      if (!res.ok) {
        var errData = await res.json().catch(function() { return {}; });
        alert('切换讲稿失败: ' + (errData.error || 'HTTP ' + res.status));
        syncConfigDropdown();
        return;
      }
      await init();
    } catch (err) {
      console.error('Config switch failed:', err);
      alert('切换讲稿失败: ' + err.message);
    }
  }

  function showAddForm() {
    document.getElementById('config-add-btn').style.display = 'none';
    document.getElementById('config-rm-btn').style.display = 'none';
    document.getElementById('config-add-form').style.display = '';
    document.getElementById('config-add-input').value = '';
    document.getElementById('config-add-input').focus();
  }

  function hideAddForm() {
    document.getElementById('config-add-btn').style.display = '';
    document.getElementById('config-rm-btn').style.display = '';
    document.getElementById('config-add-form').style.display = 'none';
  }

  async function submitAddConfig() {
    const input = document.getElementById('config-add-input');
    const path = (input.value || '').trim();
    if (!path) {
      hideAddForm();
      return;
    }

    try {
      const res = await fetch('/api/configs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: path })
      });

      const data = await res.json();

      if (!res.ok) {
        alert('添加失败: ' + (data.error || 'HTTP ' + res.status));
        hideAddForm();
        return;
      }

      hideAddForm();
      await loadConfigList();
      await init();
    } catch (err) {
      console.error('Add config failed:', err);
      alert('添加讲稿失败: ' + err.message);
      hideAddForm();
    }
  }

  function showRmConfirm() {
    const sel = document.getElementById('config-select');
    if (!sel || !sel.value) return;
    const title = sel.options[sel.selectedIndex].textContent;
    document.getElementById('config-rm-msg').textContent = '移除 "' + title + '"？（不删文件）';
    document.getElementById('config-add-btn').style.display = 'none';
    document.getElementById('config-rm-btn').style.display = 'none';
    document.getElementById('config-rm-confirm').style.display = '';
  }

  function hideRmConfirm() {
    document.getElementById('config-add-btn').style.display = '';
    document.getElementById('config-rm-btn').style.display = '';
    document.getElementById('config-rm-confirm').style.display = 'none';
  }

  async function submitRemoveConfig() {
    const sel = document.getElementById('config-select');
    if (!sel || !sel.value) return;
    const path = sel.value;

    try {
      const res = await fetch('/api/configs?path=' + encodeURIComponent(path), { method: 'DELETE' });
      if (!res.ok) {
        const errData = await res.json().catch(function() { return {}; });
        alert('移除失败: ' + (errData.error || 'HTTP ' + res.status));
        hideRmConfirm();
        return;
      }

      hideRmConfirm();
      await loadConfigList();

      const activeSel = document.getElementById('config-select');
      if (activeSel && activeSel.value) {
        await init();
      } else {
        SLIDES = [];
        PART_LABELS = {};
        PART_ORDER = [];
        deck.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:var(--text-faint);"><p>没有已注册的讲稿。点击 "+讲稿" 添加一个。</p></div>';
        if (partNav) partNav.innerHTML = '';
        if (progressBar) progressBar.style.width = '0%';
        document.title = 'HTML Deck';
      }
    } catch (err) {
      console.error('Remove config failed:', err);
      alert('移除讲稿失败: ' + err.message);
      hideRmConfirm();
    }
  }

  /* ── Init ── */
  async function init() {
    // Cleanup from previous init
    if (_eventHandlers.onKey) {
      document.removeEventListener('keydown', _eventHandlers.onKey);
    }
    if (_eventHandlers.onHashChange) {
      window.removeEventListener('hashchange', _eventHandlers.onHashChange);
    }
    if (_eventHandlers.onResize) {
      window.removeEventListener('resize', _eventHandlers.onResize);
    }
    if (_eventHandlers._shellObserver) {
      _eventHandlers._shellObserver.disconnect();
    }
    if (_eventHandlers._dprListener && _eventHandlers._dprMedia) {
      _eventHandlers._dprMedia.removeEventListener('change', _eventHandlers._dprListener);
    }

    if (partNav) partNav.innerHTML = '';

    loadedPartCss.forEach(function(part) {
      const link = document.getElementById('css-' + part);
      if (link) link.remove();
    });
    loadedPartCss = new Set();
    bumpCssCacheBust();

    SLIDES = [];
    PART_LABELS = {};
    PART_ORDER = [];
    currentIdx = 0;
    currentPart = 'ch01';

    // Load config.yaml only once
    if (!deckConfig) {
      await loadConfig();
    }

    // Bind persistent UI only once
    if (!_uiBound) {
      buildSelectors();

      const exportBtn = document.getElementById('export-btn');
      if (exportBtn) exportBtn.addEventListener('click', exportToSingleHTML);
      const themeSel = document.getElementById('theme-select');
      if (themeSel) themeSel.addEventListener('change', onThemeChange);
      const fontsizeSel = document.getElementById('fontsize-select');
      if (fontsizeSel) fontsizeSel.addEventListener('change', onFontSizeChange);
      const pptxBtn = document.getElementById('pptx-btn');
      if (pptxBtn) pptxBtn.addEventListener('click', exportToPPTX);

      const configAddBtn = document.getElementById('config-add-btn');
      if (configAddBtn) configAddBtn.addEventListener('click', showAddForm);
      const configRmBtn = document.getElementById('config-rm-btn');
      if (configRmBtn) configRmBtn.addEventListener('click', showRmConfirm);
      // Inline add-form buttons
      const configAddOk = document.getElementById('config-add-ok');
      if (configAddOk) configAddOk.addEventListener('click', submitAddConfig);
      const configAddCancel = document.getElementById('config-add-cancel');
      if (configAddCancel) configAddCancel.addEventListener('click', hideAddForm);
      const configAddInput = document.getElementById('config-add-input');
      if (configAddInput) configAddInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') submitAddConfig();
        if (e.key === 'Escape') hideAddForm();
      });
      // Inline remove-confirm buttons
      const configRmOk = document.getElementById('config-rm-ok');
      if (configRmOk) configRmOk.addEventListener('click', submitRemoveConfig);
      const configRmCancel = document.getElementById('config-rm-cancel');
      if (configRmCancel) configRmCancel.addEventListener('click', hideRmConfirm);

      // Populate config dropdown first, THEN bind change listener.
      // This prevents the change event from firing during initial population.
      await loadConfigList();
      const configSel = document.getElementById('config-select');
      if (configSel) configSel.addEventListener('change', onConfigSwitch);

      _uiBound = true;
    }

    // Fetch slides-config.json (cache-bust to prevent stale active config)
    try {
      const res = await fetch('slides-config.json?_=' + Date.now());
      if (!res.ok) throw new Error('HTTP ' + res.status);
      const config = await res.json();
      SLIDES = config.slides || [];
      PART_LABELS = config.parts || {};
      PART_ORDER = config.partOrder || Object.keys(config.parts || {});
      if (config.title) document.title = config.title;
    } catch (err) {
      console.error('Failed to load slides-config.json:', err);
      deck.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:var(--risk);"><p>加载 slides-config.json 失败: ' + err.message + '</p></div>';
      _bindNavEvents();
      return;
    }

    if (!SLIDES.length) {
      deck.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:var(--text-faint);"><p>slides-config.json 中未配置幻灯片</p></div>';
      _bindNavEvents();
      return;
    }

    initTheme();
    initFontSize();
    if (!_cssReady) { await reloadSharedCss(); _cssReady = true; }
    buildPartNav();
    const startIdx = resolveHash();
    loadSlide(startIdx);
    preloadAllPartCss();
    _bindNavEvents();

    syncConfigDropdown();

    // Expose API for editor
    window.__deckAPI = {
      getCurrentSlideKey: function() {
        const s = SLIDES[currentIdx];
        return s ? s.part + '/' + s.file : null;
      },
      getCurrentSlideEl: function() {
        return deck.querySelector('.slide.active');
      },
      applyAutoScale: applyAutoScale,
      onSlideLoaded: null,
      next: function() { if (currentIdx < SLIDES.length - 1) loadSlide(currentIdx + 1); },
      prev: function() { if (currentIdx > 0) loadSlide(currentIdx - 1); }
    };
  }

  function _bindNavEvents() {
    _eventHandlers.onKey = onKey;
    document.addEventListener('keydown', _eventHandlers.onKey);
    _eventHandlers.onHashChange = function() {
      const idx = resolveHash();
      if (idx !== currentIdx) loadSlide(idx);
    };
    window.addEventListener('hashchange', _eventHandlers.onHashChange);
    _eventHandlers.onResize = applyAutoScale;
    window.addEventListener('resize', _eventHandlers.onResize);

    // ResizeObserver on deck-shell catches layout changes from CSS re-flow
    // (e.g. when window moves between monitors with different DPI scaling)
    var shell = document.getElementById('deck-shell');
    if (shell) {
      var ro = new ResizeObserver(function() { applyAutoScale(); });
      ro.observe(shell);
      _eventHandlers._shellObserver = ro;
    }

    // matchMedia listeners for devicePixelRatio changes (monitor DPI switch)
    var dpr = window.devicePixelRatio;
    var dprMedia = window.matchMedia('(resolution: ' + dpr + 'dppx)');
    function onDprChange() {
      var newDpr = window.devicePixelRatio;
      if (newDpr !== dpr) {
        dpr = newDpr;
        // Recreate listener for new DPR value
        if (_eventHandlers._dprListener) {
          _eventHandlers._dprMedia.removeEventListener('change', _eventHandlers._dprListener);
        }
        _eventHandlers._dprMedia = window.matchMedia('(resolution: ' + dpr + 'dppx)');
        _eventHandlers._dprMedia.addEventListener('change', onDprChange);
        applyAutoScale();
      }
    }
    _eventHandlers._dprMedia = dprMedia;
    _eventHandlers._dprListener = onDprChange;
    dprMedia.addEventListener('change', onDprChange);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
