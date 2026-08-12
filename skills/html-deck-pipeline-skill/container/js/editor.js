/* editor.js — WYSIWYG style editor for HTML Deck (IIFE, no dependencies) */
(() => {
  'use strict';

  /* ---- Logger helper ---- */
  const L = window.__logger || { debug: function(){}, info: function(){}, warn: function(){}, error: function(){}, saveToDisk: async function(){return{}} };

  /* ==
     State
     ================================================================ */
  const S = window.__editorState;  // textChanges: Map<slideKey, Map<selector, newHtml>>
  // deletions: Map<slideKey, Set<selector>>  — elements removed from slides
  const U = window.__undoManager;  // { push, undo, redo, canUndo, canRedo, clear }

  /* ---- Undo helpers ---- */

  function storeMod(key, path, prop, value) {
    if (!S.modifications.has(key)) S.modifications.set(key, new Map());
    const sm = S.modifications.get(key);
    if (!sm.has(path)) sm.set(path, new Map());
    sm.get(path).set(prop, value);
  }

  function removeMod(key, path, prop) {
    if (!key || !path) return;
    const sm = S.modifications.get(key);
    if (!sm) return;
    const em = sm.get(path);
    if (!em) return;
    em.delete(prop);
    if (em.size === 0) sm.delete(path);
  }

  function rerenderIfSelected(el) {
    if (S.selectedEl === el) renderPanel(el);
  }

  function updateUndoRedoBtns() {
    const undoBtn = document.querySelector('.editor-undo-btn');
    const redoBtn = document.querySelector('.editor-redo-btn');
    if (undoBtn) undoBtn.style.opacity = (U && U.canUndo()) ? '1' : '0.4';
    if (redoBtn) redoBtn.style.opacity = (U && U.canRedo()) ? '1' : '0.4';
  }

  /* ==
     EditorShell — lifecycle
     ================================================================ */

  function init() {
    const btn = document.getElementById('editor-toggle-btn');
    if (btn) {
      btn.addEventListener('click', toggle);
    }
  }

  function toggle() {
    if (S.active) {
      deactivate();
    } else {
      activate();
    }
  }

  function activate() {
    S.active = true;
    L.info('编辑器激活');
    createPanel();
    createPalette();
    updateUndoRedoBtns();
    makeDraggable();
    const deck = document.getElementById('deck');
    deck.addEventListener('click', onDeckClick, true);
    deck.addEventListener('mouseover', onDeckHover, true);
    deck.addEventListener('mouseout', onDeckHoverOut, true);
    deck.addEventListener('dragstart', onDragStart, true);
    deck.addEventListener('dragover', onDragOver, true);
    deck.addEventListener('drop', onDrop, true);
    deck.addEventListener('dragend', onDragEnd, true);
    deck.addEventListener('dblclick', onDeckDblClick, true);
    document.addEventListener('keydown', onEditorKey);
    const btn = document.getElementById('editor-toggle-btn');
    if (btn) { btn.classList.add('active'); btn.textContent = '编辑中…'; }
  }

  function deactivate() {
    // If there are pending changes, show custom confirm dialog
    if (hasPendingChanges()) {
      showExitConfirmDialog().then(choice => {
        if (choice === 'save') {
          saveToServer();
          L.info('退出编辑模式（已保存）');
        } else {
          L.info('退出编辑模式（放弃修改）');
        }
        doDeactivate();
      });
    } else {
      L.info('退出编辑模式（无修改）');
      doDeactivate();
    }
  }

  function doDeactivate() {
    S.active = false;
    if (U) U.clear();
    deselectElement();
    clearMultiSelect();
    removePanel();
    removePalette();
    clearDraggable();
    const deck = document.getElementById('deck');
    deck.removeEventListener('click', onDeckClick, true);
    deck.removeEventListener('mouseover', onDeckHover, true);
    deck.removeEventListener('mouseout', onDeckHoverOut, true);
    deck.removeEventListener('dragstart', onDragStart, true);
    deck.removeEventListener('dragover', onDragOver, true);
    deck.removeEventListener('drop', onDrop, true);
    deck.removeEventListener('dragend', onDragEnd, true);
    deck.removeEventListener('dblclick', onDeckDblClick, true);
    document.removeEventListener('keydown', onEditorKey);
    const btn = document.getElementById('editor-toggle-btn');
    if (btn) { btn.classList.remove('active'); btn.textContent = '编辑样式'; }
    const dialog = document.getElementById('editor-exit-dialog');
    if (dialog) dialog.remove();
  }

  function showExitConfirmDialog() {
    return new Promise((resolve) => {
      // Remove any existing dialog
      const existing = document.getElementById('editor-exit-dialog');
      if (existing) existing.remove();

      const cssN = S.modifications.size;
      const domN = S.domModifications.size;
      const txtN = S.textChanges.size;
      const delN = S.deletions.size;
      let summary = '';
      if (cssN) summary += cssN + ' 项样式修改<br>';
      if (domN) summary += domN + ' 项DOM修改<br>';
      if (txtN) summary += txtN + ' 项文本编辑<br>';
      if (delN) summary += delN + ' 项删除<br>';

      const dialog = document.createElement('div');
      dialog.id = 'editor-exit-dialog';
      dialog.innerHTML =
        '<div class="editor-dialog-backdrop"></div>' +
        '<div class="editor-dialog">' +
          '<h3 style="margin:0 0 0.5rem;font-size:var(--text-md)">退出编辑模式</h3>' +
          '<p style="margin:0 0 0.5rem;color:var(--text-sec);font-size:var(--text-sm);line-height:1.5">' +
            '有未保存的修改：</p>' +
          '<div style="margin-bottom:0.8rem;font-size:var(--text-xs);color:var(--text-faint);line-height:1.6">' +
            summary +
          '</div>' +
          '<p style="margin:0 0 0.8rem;color:var(--text-sec);font-size:var(--text-sm)">是否保存到文件？</p>' +
          '<div class="editor-dialog-actions">' +
            '<button class="editor-dialog-btn secondary" data-action="discard">不保存，直接退出</button>' +
            '<button class="editor-dialog-btn primary" data-action="save">保存并退出</button>' +
            '<button class="editor-dialog-btn cancel" data-action="cancel" style="margin-left:auto">取消</button>' +
          '</div>' +
        '</div>';
      document.body.appendChild(dialog);

      const resolveAndClose = (action) => {
        dialog.remove();
        document.removeEventListener('keydown', keyHandler);
        resolve(action);
      };

      const keyHandler = (e) => {
        if (e.key === 'Escape') resolveAndClose('cancel');
        if (e.key === 'Enter') resolveAndClose('save');
      };
      document.addEventListener('keydown', keyHandler);

      dialog.querySelector('[data-action="save"]').addEventListener('click', () => resolveAndClose('save'));
      dialog.querySelector('[data-action="discard"]').addEventListener('click', () => resolveAndClose('discard'));
      dialog.querySelector('[data-action="cancel"]').addEventListener('click', () => resolveAndClose('cancel'));
      dialog.querySelector('.editor-dialog-backdrop').addEventListener('click', () => resolveAndClose('cancel'));

      // Animate in
      requestAnimationFrame(() => dialog.classList.add('open'));
    });
  }

  /* ==
     Panel DOM
     ================================================================ */

  function createPanel() {
    if (S.panelEl) return;
    S.panelEl = document.createElement('div');
    S.panelEl.id = 'editor-panel';
    S.panelEl.innerHTML =
      '<div class="editor-header">' +
        '<h3>🎨 元素编辑器</h3>' +
        '<button class="editor-close" title="关闭编辑器 (Ctrl+E)">✕</button>' +
      '</div>' +
      '<div class="editor-body" id="editor-body">' +
        '<div class="editor-empty">点击幻灯片中的元素<br>以编辑其样式<br><small style="color:var(--text-faint)">按住 Shift 点击可多选</small></div>' +
      '</div>' +
      '<div class="editor-footer" id="editor-footer">' +
        '<div class="editor-actions" style="margin-top:0;gap:0.3rem">' +
          '<button class="editor-btn editor-undo-btn" title="撤销 (Ctrl+Z)" style="flex:0.5;font-size:var(--text-xs)">↩ 撤销</button>' +
          '<button class="editor-btn editor-redo-btn" title="重做 (Ctrl+Y)" style="flex:0.5;font-size:var(--text-xs)">↪ 重做</button>' +
          '<button class="editor-btn" data-action="save" style="background:var(--accent);color:#000;font-weight:700;flex:2">💾 保存到文件</button>' +
        '</div>' +
      '</div>';
    document.body.appendChild(S.panelEl);

    // Close button
    S.panelEl.querySelector('.editor-close').addEventListener('click', deactivate);

    // Footer buttons
    S.panelEl.querySelector('.editor-undo-btn').addEventListener('click', () => { if (U) { U.undo(); updateUndoRedoBtns(); } });
    S.panelEl.querySelector('.editor-redo-btn').addEventListener('click', () => { if (U) { U.redo(); updateUndoRedoBtns(); } });
    S.panelEl.querySelector('.editor-btn[data-action="save"]').addEventListener('click', saveToServer);

    // Slide-in animation
    requestAnimationFrame(() => S.panelEl.classList.add('open'));

    // Resize handle
    const handle = document.createElement('div');
    handle.className = 'editor-resize-handle';
    S.panelEl.appendChild(handle);
    let resizing = false;
    handle.addEventListener('mousedown', (e) => {
      resizing = true;
      e.preventDefault();
    });
    document.addEventListener('mousemove', (e) => {
      if (!resizing) return;
      const w = Math.max(240, Math.min(600, window.innerWidth - e.clientX));
      S.panelEl.style.width = w + 'px';
    });
    document.addEventListener('mouseup', () => { resizing = false; });
  }

  function removePanel() {
    if (S.panelEl) { S.panelEl.remove(); S.panelEl = null; }
  }

  /* ==
     ElementPicker
     ================================================================ */

  function onDeckClick(e) {
    if (!S.active) return;
    // If editing text, finish on click outside
    if (S.editingElement && !S.editingElement.contains(e.target)) {
      finishTextEdit();
    }
    // Ignore clicks on editor UI
    if (e.target.closest('#editor-panel') || e.target.closest('#editor-el-label')) return;

    const slide = document.querySelector('.slide.active');
    if (!slide) return;

    // Find the innermost meaningful element within the slide
    let target = e.target;
    while (target && target !== slide && target !== document.body) {
      // Skip the slide shell itself
      if (target === slide) break;
      // Select this element if it's a direct or nested child of .slide
      if (slide.contains(target) && target !== slide) {
        e.stopPropagation();
        e.preventDefault();
        if (e.shiftKey) {
          onShiftClick(target);
        } else {
          selectElement(target);
        }
        return;
      }
      target = target.parentElement;
    }
    // Clicked slide background — deselect
    clearMultiSelect();
    deselectElement();
  }

  function onDeckDblClick(e) {
    if (!S.active) return;
    const slide = document.querySelector('.slide.active');
    if (!slide) return;
    // Find a text-containing element
    let target = e.target;
    while (target && target !== slide && target !== document.body) {
      if (target === slide) break;
      if (slide.contains(target) && target !== slide && isTextElement(target)) {
        e.stopPropagation();
        e.preventDefault();
        startTextEdit(target);
        return;
      }
      target = target.parentElement;
    }
  }

  function isTextElement(el) {
    const textTags = ['H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'P', 'STRONG', 'EM', 'SPAN', 'LI', 'BLOCKQUOTE', 'A'];
    // Only elements that contain direct text (not complex containers)
    if (textTags.includes(el.tagName)) return true;
    // Also allow divs that are simple text wrappers
    if (el.tagName === 'DIV' && el.children.length === 0 && el.textContent.trim()) return true;
    return false;
  }

  function startTextEdit(el) {
    if (S.editingElement === el) return;
    finishTextEdit();
    S.editingElement = el;
    S.editingOriginalHtml = el.innerHTML;
    el.contentEditable = 'true';
    el.classList.add('editor-editing');
    el.focus();
    // Select all text
    const range = document.createRange();
    range.selectNodeContents(el);
    const sel = window.getSelection();
    sel.removeAllRanges();
    sel.addRange(range);
    showTextToolbar(el);
  }

  function finishTextEdit() {
    if (!S.editingElement) return;
    const el = S.editingElement;
    const oldHtml = S.editingOriginalHtml;
    const newHtml = el.innerHTML;
    el.contentEditable = 'false';
    el.classList.remove('editor-editing');

    if (newHtml !== oldHtml) {
      const key = getSlideKey();
      const path = computePath(el);
      if (key && path) {
        if (!S.textChanges.has(key)) S.textChanges.set(key, new Map());
        S.textChanges.get(key).set(path, newHtml);
      }
      // Record undo
      if (U && key && path) {
        U.push(
          '编辑文本',
          // redo
          () => {
            el.innerHTML = newHtml;
            if (key && path) {
              if (!S.textChanges.has(key)) S.textChanges.set(key, new Map());
              S.textChanges.get(key).set(path, newHtml);
            }
          },
          // undo
          () => {
            el.innerHTML = oldHtml;
            if (key && path && S.textChanges.has(key)) {
              if (oldHtml === (el.getAttribute('data-orig-html') || '')) {
                S.textChanges.get(key).delete(path);
              } else {
                S.textChanges.get(key).set(path, oldHtml);
              }
            }
          }
        );
      }
    }
    S.editingElement = null;
    S.editingOriginalHtml = '';
    hideTextToolbar();
  }

  /* ==
     Rich Text Toolbar
     ================================================================ */

  function showTextToolbar(el) {
    hideTextToolbar();
    const bar = document.createElement('div');
    bar.id = 'editor-text-toolbar';
    bar.innerHTML =
      '<button data-cmd="bold" title="粗体 (Ctrl+B)"><b>B</b></button>' +
      '<button data-cmd="italic" title="斜体 (Ctrl+I)"><i>I</i></button>' +
      '<button data-cmd="underline" title="下划线 (Ctrl+U)"><u>U</u></button>' +
      '<button data-cmd="strikeThrough" title="删除线"><s>S</s></button>' +
      '<span class="sep"></span>' +
      '<input type="color" data-cmd="foreColor" title="文字颜色" value="#ffffff">' +
      '<input type="color" data-cmd="hiliteColor" title="高亮背景" value="#000000">';
    document.body.appendChild(bar);

    bar.querySelectorAll('button').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        document.execCommand(btn.dataset.cmd, false, null);
        el.focus();
      });
    });
    bar.querySelectorAll('input[type="color"]').forEach(input => {
      input.addEventListener('input', () => {
        document.execCommand(input.dataset.cmd, false, input.value);
        el.focus();
      });
    });

    positionTextToolbar(el);
    bar.classList.add('visible');
  }

  function positionTextToolbar(el) {
    const bar = document.getElementById('editor-text-toolbar');
    if (!bar) return;
    const rect = el.getBoundingClientRect();
    bar.style.left = Math.max(4, rect.left + rect.width / 2) + 'px';
    bar.style.top = Math.max(4, rect.top - 44) + 'px';
  }

  function hideTextToolbar() {
    const bar = document.getElementById('editor-text-toolbar');
    if (bar) bar.remove();
  }

  function onDeckHover(e) {
    if (!S.active) return;
    const slide = document.querySelector('.slide.active');
    if (!slide) return;
    let target = e.target;
    if (target === slide || !slide.contains(target)) return;
    if (target.closest('#editor-panel') || target.closest('#editor-el-label')) return;
    if (S.hoveredEl && S.hoveredEl !== target) {
      S.hoveredEl.classList.remove('editor-hover');
    }
    S.hoveredEl = target;
    S.hoveredEl.classList.add('editor-hover');
  }

  function onDeckHoverOut(e) {
    if (S.hoveredEl) {
      S.hoveredEl.classList.remove('editor-hover');
      S.hoveredEl = null;
    }
  }

  function selectElement(el) {
    if (S.selectedEl === el) return;
    deselectElement();
    clearMultiSelect();
    const tag = el.tagName.toLowerCase();
    const cls = Array.from(el.classList).filter(c => c !== 'editor-selected' && c !== 'editor-hover').join('.');
    L.debug('选中元素', (cls ? tag + '.' + cls : tag));
    S.selectedEl = el;
    el.classList.add('editor-selected');
    updateElLabel(el);
    renderPanel(el);
  }

  function deselectElement() {
    if (S.selectedEl) {
      S.selectedEl.classList.remove('editor-selected');
      S.selectedEl = null;
    }
    if (S.labelEl) { S.labelEl.classList.remove('visible'); }
    setPanelEmpty();
  }

  function onEditorKey(e) {
    if (S.editingElement) {
      if (e.key === 'Escape') {
        // Cancel edit: restore original and clean up
        S.editingElement.innerHTML = S.editingOriginalHtml;
        S.editingElement.contentEditable = 'false';
        S.editingElement.classList.remove('editor-editing');
        S.editingElement = null;
        S.editingOriginalHtml = '';
        e.stopPropagation();
        return;
      } else if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        finishTextEdit();
        return;
      }
      return;
    }

    // Undo/Redo shortcuts
    if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) {
      e.preventDefault();
      if (U && U.canUndo()) { U.undo(); updateUndoRedoBtns(); }
      return;
    }
    if ((e.ctrlKey || e.metaKey) && (e.key === 'y' || (e.key === 'z' && e.shiftKey))) {
      e.preventDefault();
      if (U && U.canRedo()) { U.redo(); updateUndoRedoBtns(); }
      return;
    }

    if (e.key === 'Escape') {
      deselectElement();
      clearMultiSelect();
    }
  }

  /* ==
     Element Label
     ================================================================ */

  function updateElLabel(el) {
    if (!S.labelEl) {
      S.labelEl = document.createElement('div');
      S.labelEl.id = 'editor-el-label';
      document.body.appendChild(S.labelEl);
    }
    const tag = el.tagName.toLowerCase();
    const cls = Array.from(el.classList).filter(c => c !== 'editor-selected' && c !== 'editor-hover').slice(0, 3).join('.');
    S.labelEl.textContent = cls ? tag + '.' + cls : tag;
    positionLabel(el);
    S.labelEl.classList.add('visible');
  }

  function positionLabel(el) {
    if (!S.labelEl) return;
    const rect = el.getBoundingClientRect();
    S.labelEl.style.left = Math.max(4, rect.left) + 'px';
    S.labelEl.style.top = Math.max(4, rect.top - 28) + 'px';
  }

  /* ==
     CSS Path Computation
     ================================================================ */

  function computePath(el) {
    const slide = el.closest('.slide');
    if (!slide) return null;
    const parts = [];
    let cur = el;
    while (cur && cur !== slide) {
      const tag = cur.tagName.toLowerCase();
      let selector = tag;
      if (cur.classList.length) {
        const cls = Array.from(cur.classList)
          .filter(c => c !== 'editor-selected' && c !== 'editor-hover' && c !== 'slide' && c !== 'active')
          .slice(0, 2);
        if (cls.length) selector += '.' + cls.join('.');
      }
      // nth-of-type for uniqueness
      const parent = cur.parentElement;
      if (parent) {
        const siblings = Array.from(parent.children).filter(c => c.tagName === cur.tagName);
        if (siblings.length > 1) {
          const idx = siblings.indexOf(cur) + 1;
          selector += ':nth-of-type(' + idx + ')';
        }
      }
      parts.unshift(selector);
      cur = cur.parentElement;
    }
    return parts.join(' > ');
  }

  /* ==
     Drag-to-rearrange (HTML5 DnD within grid containers)
     ================================================================ */

  function makeDraggable() {
    const slide = document.querySelector('.slide.active');
    if (!slide) return;
    slide.querySelectorAll(S.DRAGGABLE).forEach(el => {
      el.setAttribute('draggable', 'true');
      el.style.cursor = 'grab';
      if (!el.dataset.editorId) {
        el.dataset.editorId = 'eid-' + (++S.editorIdCounter);
      }
    });
  }

  function clearDraggable() {
    document.querySelectorAll('[draggable="true"]').forEach(el => {
      el.removeAttribute('draggable');
      el.style.cursor = '';
    });
  }

  function onDragStart(e) {
    if (!S.active) return;
    const target = e.target.closest(S.DRAGGABLE);
    if (!target) { e.preventDefault(); return; }
    S.dragSource = target;
    target.style.opacity = '0.4';
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', '');
  }

  function onDragOver(e) {
    if (!S.active || !S.dragSource) return;
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    const target = e.target.closest(S.DRAGGABLE);
    if (!target || target === S.dragSource) return;
    const parent = target.parentElement;
    // Only allow reorder within the same parent
    if (parent !== S.dragSource.parentElement) return;

    // Show placeholder: insert a thin bar before/after target based on mouse position
    const rect = target.getBoundingClientRect();
    const midY = rect.top + rect.height / 2;
    removePlaceholder();
    S.dragPlaceholder = document.createElement('div');
    S.dragPlaceholder.className = 'editor-drag-placeholder';
    S.dragPlaceholder.style.cssText =
      'height:4px;background:var(--brand, #89f0ff);border-radius:2px;margin:2px 0;transition:all 100ms ease;';
    if (e.clientY < midY) {
      target.parentElement.insertBefore(S.dragPlaceholder, target);
    } else {
      target.parentElement.insertBefore(S.dragPlaceholder, target.nextSibling);
    }
  }

  function onDrop(e) {
    if (!S.active || !S.dragSource) return;
    e.preventDefault();
    if (S.dragPlaceholder && S.dragPlaceholder.parentElement) {
      S.dragPlaceholder.parentElement.insertBefore(S.dragSource, S.dragPlaceholder);
      saveDomOrder(S.dragSource.parentElement);
    }
    removePlaceholder();
  }

  function onDragEnd() {
    if (S.dragSource) {
      S.dragSource.style.opacity = '';
      S.dragSource = null;
    }
    removePlaceholder();
    // Re-apply auto-scale
    requestAnimationFrame(() => {
      if (window.__deckAPI && window.__deckAPI.applyAutoScale) {
        window.__deckAPI.applyAutoScale();
      }
    });
  }

  function removePlaceholder() {
    if (S.dragPlaceholder && S.dragPlaceholder.parentElement) {
      S.dragPlaceholder.parentElement.removeChild(S.dragPlaceholder);
    }
    S.dragPlaceholder = null;
  }

  function saveDomOrder(parent) {
    const key = getSlideKey();
    if (!key) return;
    const parentPath = computePath(parent);
    if (!parentPath) return;
    // Save order as text fingerprints (stable across reloads)
    const order = Array.from(parent.children)
      .filter(c => c.matches(S.DRAGGABLE))
      .map(c => (c.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 60));
    if (!S.domModifications.has(key)) S.domModifications.set(key, { appended: [], reordered: {} });
    if (order.length > 1) {
      S.domModifications.get(key).reordered[parentPath] = order;
    }
  }

  /* ==
     Add-card palette
     ================================================================ */

  function createPalette() {
    const footer = document.getElementById('editor-footer');
    if (!footer || S.paletteEl) return;
    S.paletteEl = document.createElement('div');
    S.paletteEl.id = 'editor-palette';
    S.paletteEl.innerHTML =
      '<button class="palette-toggle" title="添加组件">+ 添加组件</button>' +
      '<div class="palette-menu">' +
        Object.keys(S.COMPONENT_TEMPLATES).map(type =>
          '<button class="palette-item" data-type="' + type + '">' +
            '<span class="palette-icon">' + componentIcon(type) + '</span>' +
            '<span>' + type + '</span>' +
          '</button>'
        ).join('') +
      '</div>';
    footer.appendChild(S.paletteEl);

    S.paletteEl.querySelector('.palette-toggle').addEventListener('click', () => {
      S.paletteEl.classList.toggle('open');
    });
    S.paletteEl.querySelectorAll('.palette-item').forEach(btn => {
      btn.addEventListener('click', () => {
        insertComponent(btn.dataset.type);
        S.paletteEl.classList.remove('open');
      });
    });
  }

  function removePalette() {
    if (S.paletteEl) { S.paletteEl.remove(); S.paletteEl = null; }
  }

  function componentIcon(type) {
    const icons = { panel: '▦', card: '▣', 'tip-box': '💡', 'stat-card': '📊',
                    'insight-card': '🔍', 'quote-box': '"', 'highlight-box': '✦', image: '🖼' };
    return icons[type] || '□';
  }

  function insertComponent(type, imageUrl) {
    const slide = document.querySelector('.slide.active');
    if (!slide) return;
    const template = S.COMPONENT_TEMPLATES[type];
    if (!template) return;

    // For image type, prompt for URL if not provided
    if (type === 'image' && !imageUrl) {
      const url = prompt('请输入图片 URL:', 'https://');
      if (!url || url === 'https://') return;
      imageUrl = url;
    }

    // Find the slide body (or slide itself) to append to
    const body = slide.querySelector('.slide-body') || slide;
    const temp = document.createElement('div');
    temp.innerHTML = template;
    const el = temp.firstElementChild;
    // Set image src if applicable
    if (type === 'image' && imageUrl) {
      const img = el.querySelector('img');
      if (img) img.src = imageUrl;
    }
    body.appendChild(el);

    // Store in dom modifications (use outerHTML for images to capture src)
    const key = getSlideKey();
    const storedTemplate = type === 'image' ? el.outerHTML : template;
    if (key) {
      if (!S.domModifications.has(key)) S.domModifications.set(key, { appended: [], reordered: {} });
      S.domModifications.get(key).appended.push(storedTemplate);
    }

    // Record undo
    if (U) {
      const appendIdx = body.children.length - 1; // index of appended element in body
      const finalStoredTemplate = storedTemplate;
      U.push(
        '添加 ' + type,
        // redo
        () => {
          body.appendChild(el);
          if (key) {
            if (!S.domModifications.has(key)) S.domModifications.set(key, { appended: [], reordered: {} });
            S.domModifications.get(key).appended.push(finalStoredTemplate);
          }
          if (el.matches(S.DRAGGABLE)) { el.setAttribute('draggable', 'true'); el.style.cursor = 'grab'; }
          maybeAutoScale();
        },
        // undo
        () => {
          el.remove();
          if (key && S.domModifications.has(key)) {
            const dm = S.domModifications.get(key);
            const idx = dm.appended.lastIndexOf(finalStoredTemplate);
            if (idx !== -1) dm.appended.splice(idx, 1);
          }
          maybeAutoScale();
        }
      );
    }

    // Make the new element draggable if it matches
    if (el.matches(S.DRAGGABLE)) {
      el.setAttribute('draggable', 'true');
      el.style.cursor = 'grab';
    }

    selectElement(el);
    maybeAutoScale();
  }

  /* ==
     Multi-select + Align / Distribute
     ================================================================ */

  function onShiftClick(el) {
    if (S.multiSelected.has(el)) {
      S.multiSelected.delete(el);
      el.classList.remove('editor-multi-selected');
    } else {
      S.multiSelected.add(el);
      el.classList.add('editor-multi-selected');
    }
    renderMultiAlignUI();
  }

  function clearMultiSelect() {
    S.multiSelected.forEach(el => el.classList.remove('editor-multi-selected'));
    S.multiSelected.clear();
    const bar = document.getElementById('editor-align-bar');
    if (bar) bar.remove();
  }

  function renderMultiAlignUI() {
    const existing = document.getElementById('editor-align-bar');
    if (existing) existing.remove();
    if (S.multiSelected.size < 2) return;

    const bar = document.createElement('div');
    bar.id = 'editor-align-bar';
    bar.innerHTML =
      '<span style="font-size:var(--text-xs);color:var(--text-faint);margin-right:0.4rem">' +
        S.multiSelected.size + ' 个已选</span>' +
      '<button data-align="justify-start" title="水平左对齐">⟵ 左齐</button>' +
      '<button data-align="justify-center" title="水平居中">⟷ 居中</button>' +
      '<button data-align="justify-end" title="水平右对齐">⟶ 右齐</button>' +
      '<span style="margin:0 0.3rem;color:var(--border-subtle)">|</span>' +
      '<button data-align="align-start" title="垂直顶对齐">⇧ 顶齐</button>' +
      '<button data-align="align-center" title="垂直居中">⇕ 中齐</button>' +
      '<button data-align="align-end" title="垂直底对齐">⇩ 底齐</button>' +
      '<span style="margin:0 0.3rem;color:var(--border-subtle)">|</span>' +
      '<button data-dist="h-between" title="水平分散对齐">⇶ 水平分散</button>' +
      '<button data-dist="v-between" title="垂直分散对齐">⇳ 垂直分散</button>' +
      '<button data-dist="gap+" title="增大间距">⊕ 间距+</button>' +
      '<button data-dist="gap-" title="减小间距">⊖ 间距−</button>' +
      '<button class="clear-multi" style="margin-left:auto">✕</button>';
    document.body.appendChild(bar);

    bar.querySelectorAll('button[data-align]').forEach(btn => {
      btn.addEventListener('click', () => alignMultiSelected(btn.dataset.align));
    });
    bar.querySelectorAll('button[data-dist]').forEach(btn => {
      btn.addEventListener('click', () => distributeMultiSelected(btn.dataset.dist));
    });
    bar.querySelector('.clear-multi').addEventListener('click', clearMultiSelect);
  }

  function alignMultiSelected(key) {
    const [axis, value] = key.split('-');
    const cssProp = axis === 'justify' ? 'justify-self' : 'align-self';
    const oldValues = new Map();
    S.multiSelected.forEach(el => {
      oldValues.set(el, el.style.getPropertyValue(cssProp));
      el.style[cssProp] = value;
    });

    // Record undo
    if (U) {
      const n = S.multiSelected.size;
      U.push(
        '对齐 ' + n + ' 个元素',
        // redo
        () => {
          S.multiSelected.forEach(el => { el.style[cssProp] = value; });
        },
        // undo
        () => {
          S.multiSelected.forEach(el => {
            const old = oldValues.get(el);
            if (old) el.style[cssProp] = old;
            else el.style.removeProperty(cssProp);
          });
        }
      );
    }
  }

  const DIST_CYCLE_H = ['space-between', 'space-around', 'space-evenly', 'start'];
  const DIST_CYCLE_V = ['space-between', 'space-around', 'space-evenly', 'start'];

  function distributeMultiSelected(what) {
    const parents = new Set();
    S.multiSelected.forEach(el => parents.add(el.parentElement));
    const oldStyles = new Map();

    parents.forEach(parent => {
      const old = {};
      if (what === 'h-between' || what === 'v-between') {
        old.justifyContent = parent.style.justifyContent;
        old.alignContent = parent.style.alignContent;
        old.flexWrap = parent.style.flexWrap;
      } else {
        old.gap = parent.style.gap;
      }
      oldStyles.set(parent, old);

      if (what === 'h-between') {
        const cur = getComputedStyle(parent).justifyContent;
        const idx = DIST_CYCLE_H.indexOf(cur);
        const next = DIST_CYCLE_H[(idx + 1) % DIST_CYCLE_H.length];
        parent.style.justifyContent = next;
      } else if (what === 'v-between') {
        const cur = getComputedStyle(parent).alignContent;
        const idx = DIST_CYCLE_V.indexOf(cur === 'normal' ? 'start' : cur);
        const next = DIST_CYCLE_V[(idx + 1) % DIST_CYCLE_V.length];
        parent.style.alignContent = next;
        if (next !== 'start') {
          const display = getComputedStyle(parent).display;
          if (display === 'flex' || display === 'inline-flex') {
            parent.style.flexWrap = 'wrap';
          }
        }
      } else if (what === 'gap+') {
        const gap = parseFloat(getComputedStyle(parent).gap) || parseFloat(getComputedStyle(parent).rowGap) || 12;
        parent.style.gap = Math.round((gap + 4) * 100) / 100 + 'px';
      } else if (what === 'gap-') {
        const gap = parseFloat(getComputedStyle(parent).gap) || parseFloat(getComputedStyle(parent).rowGap) || 12;
        parent.style.gap = Math.max(0, Math.round((gap - 4) * 100) / 100) + 'px';
      }
    });

    // Record undo
    if (U) {
      U.push(
        '分布调整',
        // redo: re-apply by running distribute again with same 'what'
        () => {
          // We can't re-run directly since it cycles. Instead, re-apply the current styles.
          parents.forEach(parent => {
            const cs = getComputedStyle(parent);
            S.multiSelected.forEach(el => {
              if (el.parentElement === parent) {
                if (what === 'h-between') parent.style.justifyContent = cs.justifyContent;
                else if (what === 'v-between') { parent.style.alignContent = cs.alignContent; parent.style.flexWrap = cs.flexWrap; }
                else parent.style.gap = cs.gap;
              }
            });
          });
        },
        // undo
        () => {
          oldStyles.forEach((old, parent) => {
            if (old.justifyContent !== undefined) parent.style.justifyContent = old.justifyContent;
            if (old.alignContent !== undefined) parent.style.alignContent = old.alignContent;
            if (old.flexWrap !== undefined) parent.style.flexWrap = old.flexWrap;
            if (old.gap !== undefined) parent.style.gap = old.gap;
          });
        }
      );
    }
  }

  /* ==
     StyleEngine
     ================================================================ */

  function getSlideKey() {
    if (window.__deckAPI && window.__deckAPI.getCurrentSlideKey) {
      return window.__deckAPI.getCurrentSlideKey();
    }
    return null;
  }

  function applyChange(prop, value) {
    if (!S.selectedEl) return;
    const el = S.selectedEl;
    const oldVal = el.style.getPropertyValue(prop);
    if (oldVal === value) return;

    L.debug('修改样式', { prop, value });
    el.style.setProperty(prop, value);

    // Store modification
    const key = getSlideKey();
    if (!key) return;
    const path = computePath(el);
    if (!path) return;
    storeMod(key, path, prop, value);

    // Record undo
    if (U) {
      U.push(
        '修改 ' + prop,
        // redo
        () => {
          el.style.setProperty(prop, value);
          storeMod(key, path, prop, value);
          rerenderIfSelected(el);
          if (isSizeProperty(prop)) maybeAutoScale();
        },
        // undo
        () => {
          if (oldVal) el.style.setProperty(prop, oldVal);
          else el.style.removeProperty(prop);
          removeMod(key, path, prop);
          rerenderIfSelected(el);
          if (isSizeProperty(prop)) maybeAutoScale();
        }
      );
    }

    // Trigger auto-scale if size-related
    if (isSizeProperty(prop)) maybeAutoScale();
  }

  function maybeAutoScale() {
    requestAnimationFrame(() => {
      if (window.__deckAPI && window.__deckAPI.applyAutoScale) {
        window.__deckAPI.applyAutoScale();
      }
    });
  }

  function isSizeProperty(prop) {
    return /font-size|padding|margin|line-height|border-width|width|height|gap/i.test(prop);
  }

  function resetPropertyGroup(groupName) {
    if (!S.selectedEl) return;
    const el = S.selectedEl;
    const key = getSlideKey();
    const path = computePath(el);
    const groups = {
      color: ['color', 'background-color', 'border-color'],
      typo: ['font-size', 'font-weight', 'line-height'],
      spacing: ['padding-top', 'padding-right', 'padding-bottom', 'padding-left',
                'margin-top', 'margin-right', 'margin-bottom', 'margin-left'],
      border: ['border-width', 'border-radius', 'border-style'],
      size: ['width', 'height', 'min-width', 'max-width', 'min-height', 'max-height']
    };
    const props = groups[groupName] || [];
    const oldValues = {};
    props.forEach(p => { oldValues[p] = el.style.getPropertyValue(p); });
    props.forEach(p => el.style.removeProperty(p));
    if (key && path) props.forEach(p => removeMod(key, path, p));

    // Record undo
    if (U) {
      U.push(
        '重置 ' + groupName,
        () => { props.forEach(p => { el.style.removeProperty(p); removeMod(key, path, p); }); rerenderIfSelected(el); },
        () => { Object.entries(oldValues).forEach(([p, v]) => { if (v) { el.style.setProperty(p, v); storeMod(key, path, p, v); } }); rerenderIfSelected(el); }
      );
    }

    renderPanel(el);
  }

  function resetElement() {
    if (!S.selectedEl) return;
    const el = S.selectedEl;
    const key = getSlideKey();
    const path = computePath(el);
    const props = ['color', 'background-color', 'border-color', 'font-size', 'font-weight',
                   'line-height', 'padding-top', 'padding-right', 'padding-bottom', 'padding-left',
                   'margin-top', 'margin-right', 'margin-bottom', 'margin-left',
                   'border-width', 'border-radius', 'border-style',
                   'width', 'height', 'min-width', 'max-width', 'min-height', 'max-height'];
    const oldValues = {};
    const oldCustomVars = [];
    for (let i = el.style.length - 1; i >= 0; i--) {
      const name = el.style[i];
      if (name.startsWith('--')) { oldCustomVars.push({ name: name, value: el.style.getPropertyValue(name) }); }
    }
    props.forEach(p => { oldValues[p] = el.style.getPropertyValue(p); el.style.removeProperty(p); });
    oldCustomVars.forEach(v => el.style.removeProperty(v.name));

    if (key && path) {
      if (S.modifications.has(key)) S.modifications.get(key).delete(path);
    }

    // Record undo
    if (U) {
      U.push(
        '重置元素',
        () => { props.forEach(p => el.style.removeProperty(p)); oldCustomVars.forEach(v => el.style.removeProperty(v.name)); if (key && path) { if (S.modifications.has(key)) S.modifications.get(key).delete(path); } rerenderIfSelected(el); },
        () => { Object.entries(oldValues).forEach(([p, v]) => { if (v) { el.style.setProperty(p, v); storeMod(key, path, p, v); } }); oldCustomVars.forEach(v => el.style.setProperty(v.name, v.value)); rerenderIfSelected(el); }
      );
    }

    renderPanel(el);
  }

  function resetSlide() {
    const key = getSlideKey();
    if (key) S.modifications.delete(key);
    // Reload slide to get original HTML
    if (window.__deckAPI && window.__deckAPI.getCurrentSlideEl) {
      const idx = window.__deckAPI.getCurrentIdx ? window.__deckAPI.getCurrentIdx() : 0;
      // Trigger re-fetch via deck's loadSlide indirectly
      location.reload();
    }
  }

  /* ==
     Modification persistence across navigation
     ================================================================ */

  function onSlideLoaded() {
    deselectElement();
    clearMultiSelect();
    const key = getSlideKey();
    if (!key) return;

    const slide = document.querySelector('.slide.active');
    if (!slide) return;

    // Restore style S.modifications for this slide
    const slideMods = S.modifications.get(key);
    if (slideMods) {
      for (const [path, props] of slideMods) {
        try {
          const el = slide.querySelector(path);
          if (el) {
            for (const [prop, value] of props) {
              el.style.setProperty(prop, value);
            }
          }
        } catch (e) {
          // Selector failed — keep S.modifications but skip restore
        }
      }
    }

    // Restore DOM S.modifications (appended elements + reordering)
    const domMods = S.domModifications.get(key);
    if (domMods) {
      // Restore appended elements
      if (domMods.appended && domMods.appended.length) {
        const body = slide.querySelector('.slide-body') || slide;
        domMods.appended.forEach(template => {
          const temp = document.createElement('div');
          temp.innerHTML = template;
          const el = temp.firstElementChild;
          body.appendChild(el);
        });
      }
      // Restore element order
      if (domMods.reordered) {
        for (const [parentPath, childFingerprints] of Object.entries(domMods.reordered)) {
          try {
            const parent = slide.querySelector(parentPath);
            if (!parent || !childFingerprints.length) continue;
            // Match children by text fingerprint
            const draggableChildren = Array.from(parent.children).filter(c => c.matches(S.DRAGGABLE));
            if (draggableChildren.length !== childFingerprints.length) continue;
            const childMap = new Map();
            draggableChildren.forEach(el => {
              const fp = (el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 60);
              childMap.set(fp, el);
            });
            // Check all fingerprints found
            if (childFingerprints.some(fp => !childMap.has(fp))) continue;
            // Append in saved order
            childFingerprints.forEach(fp => {
              const el = childMap.get(fp);
              if (el) parent.appendChild(el);
            });
          } catch (e) { /* skip */ }
        }
      }
    }

    // Remove deleted elements (before re-enabling draggable)
    const delSet = S.deletions.get(key);
    if (delSet) {
      delSet.forEach(selector => {
        try {
          const el = slide.querySelector(selector);
          if (el) el.remove();
        } catch (e) { /* skip */ }
      });
    }

    // Re-enable draggable on all elements
    makeDraggable();
  }

  /* ==
     PropertyPanel — Rendering
     ================================================================ */

  function renderPanel(el) {
    const body = document.getElementById('editor-body');
    if (!body) return;

    const cs = getComputedStyle(el);
    const tag = el.tagName.toLowerCase();
    const cls = Array.from(el.classList).filter(c => c !== 'editor-selected' && c !== 'editor-hover').join('.');

    const html =
      '<div style="margin-bottom:0.6rem;font-size:var(--text-xs);color:var(--text-faint);">' +
        '已选中 <span style="color:var(--accent);font-weight:700">' + (cls ? tag + '.' + cls : tag) + '</span>' +
      '</div>' +
      renderColorSection(el, cs) +
      renderTypoSection(el, cs) +
      renderSpacingSection(el, cs) +
      renderBorderSection(el, cs) +
      renderSizeSection(el, cs) +
      renderLayoutSection(el) +
      renderActions();
    body.innerHTML = html;
    bindControls(el);
  }

  function setPanelEmpty() {
    const body = document.getElementById('editor-body');
    if (body) {
      body.innerHTML = '<div class="editor-empty">点击元素 → 编辑样式<br>双击文字 → 编辑文本<br>Shift+点击 → 多选对齐<br><small style="color:var(--text-faint)">点击容器可切换布局</small></div>';
    }
  }

  /* ---- Color section ---- */

  function renderColorSection(el, cs) {
    const curColor = el.style.color || rgbToHex(cs.color);
    const curBg = el.style.backgroundColor || rgbToHex(cs.backgroundColor);
    const curBdColor = el.style.borderColor || rgbToHex(cs.borderColor);
    const isTransparentBg = cs.backgroundColor === 'rgba(0, 0, 0, 0)' || cs.backgroundColor === 'transparent';

    return '' +
      '<div class="editor-section">' +
        '<div class="editor-section-header" data-section="color">' +
          '<span>颜色</span>' +
          '<button class="editor-reset-group" data-reset="color" title="重置颜色">↩</button>' +
          '<span class="arrow">▾</span>' +
        '</div>' +
        '<div class="editor-section-body">' +
          '<div class="editor-row">' +
            '<span class="editor-label">文字颜色</span>' +
            '<input class="editor-color-input" type="color" data-prop="color" value="' + curColor + '">' +
            '<input class="editor-hex-input" type="text" data-prop="color-hex" value="' + curColor + '">' +
          '</div>' +
          '<div class="editor-row">' +
            '<span class="editor-label">背景色</span>' +
            '<input class="editor-color-input" type="color" data-prop="background-color" value="' + (isTransparentBg ? '#000000' : curBg) + '">' +
            '<input class="editor-hex-input" type="text" data-prop="background-color-hex" value="' + (isTransparentBg ? 'transparent' : curBg) + '">' +
          '</div>' +
          '<div class="editor-swatch-row">' + renderSwatches() + '</div>' +
        '</div>' +
      '</div>';
  }

  function renderSwatches() {
    const tokens = ['--text', '--text-sec', '--accent', '--brand', '--ok', '--warn', '--risk', '--info', '--bg'];
    const rootCS = getComputedStyle(document.documentElement);
    return tokens.map(t => {
      const val = rootCS.getPropertyValue(t).trim();
      return '<span class="editor-swatch" title="' + t + '" data-var="' + t + '" style="background:' + val + '"></span>';
    }).join('');
  }

  /* ---- Typography section ---- */

  function renderTypoSection(el, cs) {
    // Convert computed px to rem (1rem = 16px)
    const rootFS = parseFloat(getComputedStyle(document.documentElement).fontSize) || 16;
    const fsPx = parseFloat(cs.fontSize) || rootFS;
    const fsRem = Math.round(fsPx / rootFS * 100) / 100;
    const fw = cs.fontWeight || '400';
    const lhNum = parseFloat(cs.lineHeight);
    const lh = isNaN(lhNum) ? 1.5 : Math.round(lhNum * 100) / 100;

    return '' +
      '<div class="editor-section">' +
        '<div class="editor-section-header" data-section="typo">' +
          '<span>排版</span>' +
          '<button class="editor-reset-group" data-reset="typo" title="重置排版">↩</button>' +
          '<span class="arrow">▾</span>' +
        '</div>' +
        '<div class="editor-section-body">' +
          '<div class="editor-row">' +
            '<span class="editor-label">字号</span>' +
            '<input class="editor-range" type="range" data-prop="font-size" min="0.5" max="2.5" step="0.05" value="' + fsRem + '">' +
            '<span class="editor-value-display">' + fsRem.toFixed(2) + 'rem</span>' +
          '</div>' +
          '<div class="editor-row">' +
            '<span class="editor-label">字重</span>' +
            '<select class="editor-select" data-prop="font-weight">' +
              ['300', '400', '500', '600', '700', '800', '900'].map(w =>
                '<option value="' + w + '"' + (fw === w ? ' selected' : '') + '>' + w + '</option>'
              ).join('') +
            '</select>' +
          '</div>' +
          '<div class="editor-row">' +
            '<span class="editor-label">行高</span>' +
            '<input class="editor-range" type="range" data-prop="line-height" min="1" max="2.5" step="0.05" value="' + lh + '">' +
            '<span class="editor-value-display">' + lh.toFixed(2) + '</span>' +
          '</div>' +
        '</div>' +
      '</div>';
  }

  /* ---- Spacing section ---- */

  function renderSpacingSection(el, cs) {
    const pad = ['padding-top', 'padding-right', 'padding-bottom', 'padding-left']
      .map(p => Math.round(parseFloat(cs.getPropertyValue(p))));
    const mar = ['margin-top', 'margin-right', 'margin-bottom', 'margin-left']
      .map(p => Math.round(parseFloat(cs.getPropertyValue(p))));

    const padLabels = ['上', '右', '下', '左'];
    const padProps = ['padding-top', 'padding-right', 'padding-bottom', 'padding-left'];
    const marProps = ['margin-top', 'margin-right', 'margin-bottom', 'margin-left'];

    return '' +
      '<div class="editor-section">' +
        '<div class="editor-section-header" data-section="spacing">' +
          '<span>间距</span>' +
          '<button class="editor-reset-group" data-reset="spacing" title="重置间距">↩</button>' +
          '<span class="arrow">▾</span>' +
        '</div>' +
        '<div class="editor-section-body">' +
          '<div style="font-size:var(--text-xs);color:var(--text-faint);margin-bottom:0.3rem;">Padding</div>' +
          padLabels.map((label, i) =>
            '<div class="editor-row">' +
              '<span class="editor-label">' + label + '</span>' +
              '<input class="editor-number" type="number" data-prop="' + padProps[i] + '" value="' + pad[i] + '" min="0" max="120">' +
              '<span style="font-size:var(--text-xs);color:var(--text-faint)">px</span>' +
            '</div>'
          ).join('') +
          '<div style="font-size:var(--text-xs);color:var(--text-faint);margin:0.5rem 0 0.3rem;">Margin</div>' +
          padLabels.map((label, i) =>
            '<div class="editor-row">' +
              '<span class="editor-label">' + label + '</span>' +
              '<input class="editor-number" type="number" data-prop="' + marProps[i] + '" value="' + mar[i] + '" min="0" max="120">' +
              '<span style="font-size:var(--text-xs);color:var(--text-faint)">px</span>' +
            '</div>'
          ).join('') +
        '</div>' +
      '</div>';
  }

  /* ---- Border section ---- */

  function renderBorderSection(el, cs) {
    const bw = Math.round(parseFloat(cs.borderWidth) || 0);
    const br = Math.round(parseFloat(cs.borderRadius) || 0);
    const bs = cs.borderStyle || 'none';

    return '' +
      '<div class="editor-section">' +
        '<div class="editor-section-header" data-section="border">' +
          '<span>边框</span>' +
          '<button class="editor-reset-group" data-reset="border" title="重置边框">↩</button>' +
          '<span class="arrow">▾</span>' +
        '</div>' +
        '<div class="editor-section-body">' +
          '<div class="editor-row">' +
            '<span class="editor-label">宽度</span>' +
            '<input class="editor-range" type="range" data-prop="border-width" min="0" max="10" step="1" value="' + bw + '">' +
            '<span class="editor-value-display">' + bw + 'px</span>' +
          '</div>' +
          '<div class="editor-row">' +
            '<span class="editor-label">圆角</span>' +
            '<input class="editor-range" type="range" data-prop="border-radius" min="0" max="48" step="2" value="' + br + '">' +
            '<span class="editor-value-display">' + br + 'px</span>' +
          '</div>' +
          '<div class="editor-row">' +
            '<span class="editor-label">样式</span>' +
            '<select class="editor-select" data-prop="border-style">' +
              ['none', 'solid', 'dashed', 'dotted', 'double'].map(s =>
                '<option value="' + s + '"' + (bs === s ? ' selected' : '') + '>' + s + '</option>'
              ).join('') +
            '</select>' +
          '</div>' +
        '</div>' +
      '</div>';
  }

  /* ---- Actions ---- */

  /* ---- Size section ---- */

  function renderSizeSection(el, cs) {
    const w = el.style.width || (cs.width !== 'auto' ? Math.round(parseFloat(cs.width)) + 'px' : '');
    const h = el.style.height || (cs.height !== 'auto' ? Math.round(parseFloat(cs.height)) + 'px' : '');
    const mw = el.style.minWidth || (cs.minWidth !== 'auto' && cs.minWidth !== '0px' ? Math.round(parseFloat(cs.minWidth)) + 'px' : '');
    const mh = el.style.minHeight || (cs.minHeight !== 'auto' && cs.minHeight !== '0px' ? Math.round(parseFloat(cs.minHeight)) + 'px' : '');

    function sizeRow(label, prop, val) {
      return '<div class="editor-row">' +
        '<span class="editor-label">' + label + '</span>' +
        '<input class="editor-number" type="number" data-prop="' + prop + '" value="' + (val ? parseFloat(val) : '') + '" min="0" max="2000" placeholder="auto">' +
        '<span style="font-size:var(--text-xs);color:var(--text-faint)">px</span>' +
      '</div>';
    }

    return '' +
      '<div class="editor-section">' +
        '<div class="editor-section-header" data-section="size">' +
          '<span>尺寸</span>' +
          '<button class="editor-reset-group" data-reset="size" title="重置尺寸">↩</button>' +
          '<span class="arrow">▾</span>' +
        '</div>' +
        '<div class="editor-section-body">' +
          sizeRow('宽度', 'width', w) +
          sizeRow('高度', 'height', h) +
          sizeRow('最小宽', 'min-width', mw) +
          sizeRow('最大宽', 'max-width', el.style.maxWidth ? parseFloat(el.style.maxWidth) : '') +
        '</div>' +
      '</div>';
  }

  function isContainer(el) {
    return el.querySelectorAll(S.DRAGGABLE).length > 0;
  }

  function getLayoutContainer(el) {
    // If el itself is a container, use it
    if (isContainer(el)) return el;
    // If el is a draggable child, use its parent (if parent is a container)
    if (el.matches(S.DRAGGABLE)) {
      const parent = el.parentElement;
      if (parent && isContainer(parent)) return parent;
    }
    return null;
  }

  function renderLayoutSection(el) {
    const container = getLayoutContainer(el);
    if (!container) return '';

    const cs = getComputedStyle(container);
    const containerTag = container.tagName.toLowerCase();
    const containerCls = Array.from(container.classList).filter(c => c !== 'editor-selected' && c !== 'editor-hover').join('.');
    const display = cs.display;
    const gridCols = cs.gridTemplateColumns;
    // Determine current layout mode
    let currentMode = 'stack';
    if (display === 'grid' || display === 'inline-grid') {
      const cols = gridCols.split(' ').filter(s => s.trim() && s !== 'none').length;
      if (cols >= 4) currentMode = 'quad';
      else if (cols >= 3) currentMode = 'triple';
      else if (cols >= 2) currentMode = 'dual';
      else currentMode = 'stack';
    } else if (display === 'flex' || display === 'inline-flex') {
      const wrap = cs.flexWrap;
      const dir = cs.flexDirection;
      currentMode = (dir === 'row' || dir === 'row-reverse') ? 'flex-row' : 'stack';
    }

    const opts = [
      { value: 'stack', label: '纵向堆叠', css: 'display:flex;flex-direction:column;' },
      { value: 'flex-row', label: '横向排列', css: 'display:flex;flex-direction:row;flex-wrap:wrap;gap:0.75rem;' },
      { value: 'dual', label: '双列网格', css: 'display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:0.75rem;' },
      { value: 'triple', label: '三列网格', css: 'display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:0.75rem;' },
      { value: 'quad', label: '四列网格', css: 'display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:0.75rem;' },
    ];

    const secTitle = container === el ? '容器布局' : '容器布局（.' + (containerCls || containerTag) + '）';
    const gapVal = Math.round((parseFloat(cs.gap) || parseFloat(cs.rowGap) || 12) * 100) / 100;

    return '' +
      '<div class="editor-section">' +
        '<div class="editor-section-header" data-section="layout">' +
          '<span>' + secTitle + '</span>' +
          '<span class="arrow">▾</span>' +
        '</div>' +
        '<div class="editor-section-body">' +
          '<div class="editor-row">' +
            '<span class="editor-label">模式</span>' +
            '<select class="editor-select" data-prop="layout-mode">' +
              opts.map(o => '<option value="' + o.value + '"' + (currentMode === o.value ? ' selected' : '') + '>' + o.label + '</option>').join('') +
            '</select>' +
          '</div>' +
          '<div class="editor-row">' +
            '<span class="editor-label">间距</span>' +
            '<input class="editor-number" type="number" data-prop="layout-gap" value="' + gapVal + '" min="0" max="80" step="2">' +
            '<span style="font-size:var(--text-xs);color:var(--text-faint)">px</span>' +
          '</div>' +
        '</div>' +
      '</div>';
  }

  function applyLayoutMode(el, mode) {
    const container = getLayoutContainer(el);
    if (!container) return;
    const modes = {
      stack: 'display:flex;flex-direction:column;grid-template-columns:none;',
      'flex-row': 'display:flex;flex-direction:row;flex-wrap:wrap;',
      dual: 'display:grid;grid-template-columns:repeat(2,minmax(0,1fr));',
      triple: 'display:grid;grid-template-columns:repeat(3,minmax(0,1fr));',
      quad: 'display:grid;grid-template-columns:repeat(4,minmax(0,1fr));',
    };
    const css = modes[mode] || modes.stack;
    const key = getSlideKey();
    const path = computePath(container);
    const oldProps = {};

    css.split(';').filter(Boolean).forEach(decl => {
      const [prop, val] = decl.split(':');
      const p = prop.trim();
      const v = val.trim();
      oldProps[p] = container.style.getPropertyValue(p);
      container.style.setProperty(p, v);
      if (key && path) storeMod(key, path, p, v);
    });

    // Record undo
    if (U && key && path) {
      U.push(
        '切换布局 → ' + mode,
        // redo
        () => {
          Object.entries({ display: modes[mode] }).forEach(([k, v]) => {});
          css.split(';').filter(Boolean).forEach(decl => {
            const [prop, val] = decl.split(':');
            const p = prop.trim();
            container.style.setProperty(p, val.trim());
            storeMod(key, path, p, val.trim());
          });
          maybeAutoScale();
          rerenderIfSelected(el);
        },
        // undo
        () => {
          Object.keys(oldProps).forEach(p => {
            if (oldProps[p]) container.style.setProperty(p, oldProps[p]);
            else container.style.removeProperty(p);
            removeMod(key, path, p);
          });
          maybeAutoScale();
          rerenderIfSelected(el);
        }
      );
    }

    maybeAutoScale();
  }

  function renderActions() {
    return '' +
      '<div class="editor-actions">' +
        '<button class="editor-btn" data-action="clone-el">📋 复制元素</button>' +
        '<button class="editor-btn" data-action="reset-el">重置元素</button>' +
        '<button class="editor-btn danger" data-action="reset-slide">重置本页</button>' +
      '</div>' +
      '<div class="editor-actions">' +
        '<button class="editor-btn danger" data-action="delete-el" style="border-color:var(--risk);color:var(--risk)">🗑 删除元素</button>' +
      '</div>';
  }

  /* ==
     PropertyPanel — Control Binding
     ================================================================ */

  function bindControls(el) {
    const body = document.getElementById('editor-body');
    if (!body) return;

    // Section collapse toggle
    body.querySelectorAll('.editor-section-header').forEach(header => {
      header.addEventListener('click', () => {
        header.parentElement.classList.toggle('collapsed');
      });
    });

    // Color inputs
    body.querySelectorAll('.editor-color-input').forEach(input => {
      input.addEventListener('input', () => {
        const prop = input.dataset.prop;
        applyChange(prop, input.value);
        // Sync hex input
        const hexInput = body.querySelector('[data-prop="' + prop + '-hex"]');
        if (hexInput) hexInput.value = input.value;
      });
    });

    // Hex inputs
    body.querySelectorAll('.editor-hex-input').forEach(input => {
      input.addEventListener('change', () => {
        const prop = input.dataset.prop.replace('-hex', '');
        let val = input.value.trim();
        // Validate hex
        if (/^#[0-9a-fA-F]{3,6}$/.test(val)) {
          applyChange(prop, val);
          const colorInput = body.querySelector('.editor-color-input[data-prop="' + prop + '"]');
          if (colorInput) colorInput.value = val;
        } else if (val === 'transparent') {
          applyChange(prop, 'transparent');
        }
      });
    });

    // Swatches
    body.querySelectorAll('.editor-swatch').forEach(swatch => {
      swatch.addEventListener('click', () => {
        const varName = swatch.dataset.var;
        const prop = getActiveColorProp(body);
        if (prop) applyChange(prop, 'var(' + varName + ')');
        // Update display
        if (S.selectedEl) renderPanel(S.selectedEl);
      });
    });

    // Range inputs
    body.querySelectorAll('.editor-range').forEach(input => {
      const update = () => {
        const prop = input.dataset.prop;
        const val = parseFloat(input.value);
        const unit = prop === 'line-height' ? '' : 'rem';
        applyChange(prop, val + unit);
        // Update display
        const display = input.parentElement.querySelector('.editor-value-display');
        if (display) display.textContent = val.toFixed(2) + (unit || '');
        if (prop === 'font-size') {
          const shortDisplay = input.parentElement.querySelector('.editor-value-display');
          if (shortDisplay) shortDisplay.textContent = val.toFixed(2) + 'rem';
        }
      };
      input.addEventListener('input', update);
    });

    // Select inputs
    body.querySelectorAll('.editor-select').forEach(select => {
      select.addEventListener('change', () => {
        if (select.dataset.prop === 'layout-mode') {
          applyLayoutMode(el, select.value);
        } else {
          applyChange(select.dataset.prop, select.value);
        }
      });
    });

    // Number inputs
    body.querySelectorAll('.editor-number').forEach(input => {
      input.addEventListener('change', () => {
        const prop = input.dataset.prop;
        if (prop === 'layout-gap') {
          const container = getLayoutContainer(el);
          if (container) {
            container.style.setProperty('gap', input.value + 'px');
            // Also store via applyChange for persistence
            const key = getSlideKey();
            const path = computePath(container);
            if (key && path) {
              if (!S.modifications.has(key)) S.modifications.set(key, new Map());
              const slideMods = S.modifications.get(key);
              if (!slideMods.has(path)) slideMods.set(path, new Map());
              slideMods.get(path).set('gap', input.value + 'px');
            }
          }
          requestAnimationFrame(() => {
            if (window.__deckAPI && window.__deckAPI.applyAutoScale) {
              window.__deckAPI.applyAutoScale();
            }
          });
        } else {
          applyChange(prop, input.value + 'px');
        }
      });
    });

    // Action buttons
    body.querySelectorAll('.editor-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const action = btn.dataset.action;
        if (action === 'clone-el') duplicateSelectedElement();
        else if (action === 'reset-el') resetElement();
        else if (action === 'reset-slide') resetSlide();
        else if (action === 'save') saveToServer();
        else if (action === 'delete-el') deleteSelectedElement();
      });
    });

    // Per-section reset buttons
    body.querySelectorAll('.editor-reset-group').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation(); // don't toggle collapse
        const group = btn.dataset.reset;
        if (group) resetPropertyGroup(group);
      });
    });
  }

  function getActiveColorProp(body) {
    // Find which color section the user is editing (last focused color/hex input)
      if (S.active) return S.active.dataset.prop.replace('-hex', '');
    return 'color'; // default
  }

  /* ==
     Utility: rgb → hex
     ================================================================ */

  function rgbToHex(rgb) {
    if (!rgb || rgb === 'transparent' || rgb === 'rgba(0, 0, 0, 0)') return '#000000';
    const m = rgb.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
    if (!m) return rgb; // already hex or named
    return '#' + [m[1], m[2], m[3]].map(x => parseInt(x).toString(16).padStart(2, '0')).join('');
  }

  function deleteSelectedElement() {
    if (!S.selectedEl) return;
    L.info('删除元素', computePath(S.selectedEl));
    const el = S.selectedEl;
    const key = getSlideKey();
    const path = computePath(el);
    const parent = el.parentElement;
    const nextSibling = el.nextSibling;
    const savedHTML = el.outerHTML;
    const savedMulti = [];
    // Save multi-selected elements too
    S.multiSelected.forEach(msel => {
      savedMulti.push({ el: msel, parent: msel.parentElement, next: msel.nextSibling, html: msel.outerHTML, path: computePath(msel) });
    });

    // Perform deletion
    const deletedPaths = [];
    if (key && path) {
      if (!S.deletions.has(key)) S.deletions.set(key, new Set());
      S.deletions.get(key).add(path);
      deletedPaths.push(path);
      if (S.modifications.has(key)) { S.modifications.get(key).delete(path); }
      if (S.textChanges.has(key)) { S.textChanges.get(key).delete(path); }
    }
    S.multiSelected.forEach(msel => {
      const mp = computePath(msel);
      if (key && mp) { S.deletions.get(key).add(mp); deletedPaths.push(mp); }
      msel.remove();
    });
    clearMultiSelect();
    el.remove();
    deselectElement();

    // Record undo
    if (U && key) {
      U.push(
        '删除元素',
        // redo
        () => {
          if (!S.deletions.has(key)) S.deletions.set(key, new Set());
          deletedPaths.forEach(p => S.deletions.get(key).add(p));
          savedMulti.forEach(m => m.el.remove());
          el.remove();
          deselectElement();
          maybeAutoScale();
        },
        // undo
        () => {
          // Re-insert main element
          if (nextSibling && nextSibling.parentElement === parent) {
            parent.insertBefore(el, nextSibling);
          } else {
            parent.appendChild(el);
          }
          // Re-insert multi elements
          savedMulti.forEach(m => {
            if (m.next && m.next.parentElement === m.parent) {
              m.parent.insertBefore(m.el, m.next);
            } else {
              m.parent.appendChild(m.el);
            }
          });
          // Clean up deletions
          if (S.deletions.has(key)) {
            deletedPaths.forEach(p => S.deletions.get(key).delete(p));
          }
          maybeAutoScale();
        }
      );
    }

    maybeAutoScale();
  }

  function duplicateSelectedElement() {
    if (!S.selectedEl) return;
    const el = S.selectedEl;
    const clone = el.cloneNode(true);
    // Clear editor-specific classes from clone
    clone.classList.remove('editor-selected', 'editor-hover', 'editor-multi-selected', 'editor-editing');
    clone.removeAttribute('contenteditable');
    clone.removeAttribute('draggable');
    clone.style.cursor = '';

    // Insert clone after the original
    const parent = el.parentElement;
    const nextSibling = el.nextSibling;
    if (nextSibling) {
      parent.insertBefore(clone, nextSibling);
    } else {
      parent.appendChild(clone);
    }

    L.info('复制元素', computePath(el));

    // Track in domModifications
    const key = getSlideKey();
    const cloneOuterHTML = clone.outerHTML;
    if (key) {
      if (!S.domModifications.has(key)) S.domModifications.set(key, { appended: [], reordered: {} });
      S.domModifications.get(key).appended.push(cloneOuterHTML);
    }

    // Record undo
    if (U) {
      U.push(
        '复制元素',
        // redo: re-insert clone
        () => {
          if (nextSibling && nextSibling.parentElement === parent) {
            parent.insertBefore(clone, nextSibling);
          } else {
            parent.appendChild(clone);
          }
          if (key) {
            if (!S.domModifications.has(key)) S.domModifications.set(key, { appended: [], reordered: {} });
            S.domModifications.get(key).appended.push(cloneOuterHTML);
          }
          if (clone.matches(S.DRAGGABLE)) { clone.setAttribute('draggable', 'true'); clone.style.cursor = 'grab'; }
          maybeAutoScale();
        },
        // undo: remove clone
        () => {
          clone.remove();
          if (key && S.domModifications.has(key)) {
            const dm = S.domModifications.get(key);
            const idx = dm.appended.lastIndexOf(cloneOuterHTML);
            if (idx !== -1) dm.appended.splice(idx, 1);
          }
          maybeAutoScale();
        }
      );
    }

    // Make clone draggable
    if (clone.matches(S.DRAGGABLE)) {
      clone.setAttribute('draggable', 'true');
      clone.style.cursor = 'grab';
    }

    selectElement(clone);
    maybeAutoScale();
  }

  /* ==
     Export & Persist
     ================================================================ */

  function getCSSOverrides() {
    if (S.modifications.size === 0) return '';

    let css = '\n/* ===== Editor Customizations ===== */\n';
    for (const [slideKey, slideMods] of S.modifications) {
      for (const [path, props] of slideMods) {
        css += '[data-slide-key="' + slideKey + '"] ' + path + ' {\n';
        for (const [prop, value] of props) {
          css += '  ' + prop + ': ' + value + ' !important;\n';
        }
        css += '}\n';
      }
    }
    return css;
  }

  function buildSavePayload() {
    // CSS overrides: grouped by slide key
    const cssRules = [];
    for (const [slideKey, slideMods] of S.modifications) {
      for (const [path, props] of slideMods) {
        if (props.size === 0) continue;
        const rule = { slideKey: slideKey, selector: path, props: {} };
        for (const [prop, value] of props) {
          rule.props[prop] = value;
        }
        cssRules.push(rule);
      }
    }

    // DOM changes: appended elements + reordering
    const domChanges = {};
    for (const [slideKey, domMod] of S.domModifications) {
      const entry = domChanges[slideKey] = {};
      if (domMod.appended && domMod.appended.length) {
        entry.appended = domMod.appended.slice();
      }
      if (domMod.reordered && Object.keys(domMod.reordered).length) {
        entry.reordered = {};
        for (const [parentPath, fingerprints] of Object.entries(domMod.reordered)) {
          entry.reordered[parentPath] = fingerprints.slice();
        }
      }
    }

    // Text changes
    const textMods = {};
    for (const [slideKey, slideChanges] of S.textChanges) {
      const entries = textMods[slideKey] = {};
      for (const [selector, newHtml] of slideChanges) {
        entries[selector] = newHtml;
      }
    }

    // Deletions
    const delPayload = {};
    for (const [slideKey, selectors] of S.deletions) {
      delPayload[slideKey] = Array.from(selectors);
    }

    return { cssRules: cssRules, domChanges: domChanges, textChanges: textMods, deletions: delPayload };
  }

  function hasPendingChanges() {
    if (S.modifications.size > 0) return true;
    if (S.domModifications.size > 0) return true;
    if (S.textChanges.size > 0) return true;
    if (S.deletions.size > 0) return true;
    return false;
  }

  async function saveToServer() {
    const payload = buildSavePayload();
    const cssN = payload.cssRules.length;
    const domN = Object.keys(payload.domChanges).length;
    const txtN = Object.keys(payload.S.textChanges).length;
    const delN = Object.keys(payload.S.deletions).length;
    if (!cssN && !domN && !txtN && !delN) {
      showSaveStatus('没有需要保存的修改');
      return;
    }

    L.info('保存到文件', `CSS:${cssN} DOM:${domN} Text:${txtN} Del:${delN}`);
    try {
      const res = await fetch('/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        const data = await res.json();
        showSaveStatus('✅ ' + (data.message || '保存成功'));
        // Clear S.modifications after successful save — changes now live in files
        S.modifications.clear();
        S.domModifications.clear();
        S.textChanges.clear();
        S.deletions.clear();
      } else {
        const err = await res.json().catch(() => ({ error: 'Unknown error' }));
        showSaveStatus('❌ 保存失败: ' + (err.error || res.status));
        L.error('保存失败', { status: res.status, error: err.error });
      }
    } catch (err) {
      showSaveStatus('❌ 网络错误: ' + err.message);
      L.error('保存网络错误', err.message);
    }
  }

  function showSaveStatus(msg) {
    const body = document.getElementById('editor-body');
    if (!body) return;
    const existing = body.querySelector('.editor-save-status');
    if (existing) existing.remove();
    const el = document.createElement('div');
    el.className = 'editor-save-status';
    el.style.cssText = 'margin-bottom:0.6rem;padding:0.35rem 0.6rem;border-radius:6px;' +
      'font-size:var(--text-xs);' +
      'background:' + (msg.startsWith('✅') ? 'rgba(86,210,160,0.12)' : msg.startsWith('❌') ? 'rgba(255,143,159,0.12)' : 'rgba(255,255,255,0.04)') + ';' +
      'color:' + (msg.startsWith('✅') ? 'var(--ok,#56d2a0)' : msg.startsWith('❌') ? 'var(--risk,#ff8f9f)' : 'var(--text-faint)') + ';';
    el.textContent = msg;
    body.insertBefore(el, body.firstChild);
    setTimeout(() => el.remove(), 4000);
  }

  /* ==
     Bootstrap — wait for deck API
     ================================================================ */

  function bootstrap() {
    if (window.__deckAPI) {
      init();
      // Hook into deck's slide-loaded callback to restore S.modifications
      const origOnSlideLoaded = window.__deckAPI.onSlideLoaded;
      window.__deckAPI.onSlideLoaded = function() {
        if (origOnSlideLoaded) origOnSlideLoaded();
        // Restore S.modifications after a brief delay (deck needs to settle)
        setTimeout(onSlideLoaded, 100);
      };
    } else {
      // Deck not ready yet — retry
      setTimeout(bootstrap, 100);
    }
  }

  // Expose public API
  window.__editor = {
    toggle: toggle,
    isActive: function() { return S.active; },
    getCSSOverrides: getCSSOverrides,
    getModifications: function() { return S.modifications; },
    getDomModifications: function() { return S.domModifications; },
    getDeletions: function() { return S.deletions; }
  };

  // Start
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bootstrap);
  } else {
    bootstrap();
  }
})();
