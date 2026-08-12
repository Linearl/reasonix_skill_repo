/* editor-state.js — shared state for all editor modules */
(() => {
  'use strict';

  const state = {
    active: false,
    selectedEl: null,
    hoveredEl: null,
    panelEl: null,
    labelEl: null,
    paletteEl: null,

    multiSelected: new Set(),
    dragSource: null,
    dragPlaceholder: null,
    editingElement: null,
    editingOriginalHtml: '',
    editorIdCounter: 0,

    modifications: new Map(),
    domModifications: new Map(),
    textChanges: new Map(),
    deletions: new Map()
  };

  // Constants
  state.DRAGGABLE = '.panel, .card, .stat-card, .insight-card, .tip-box, .tip-card, ' +
    '.quote-box, .step-card, .flow-step, .highlight-box, .glass-row, .big-stat, .editor-image';

  state.COMPONENT_TEMPLATES = {
    panel: '<div class="panel"><p>新面板 — 点击编辑此文本</p></div>',
    card: '<div class="card"><strong>新卡片</strong><p>点击编辑此文本</p></div>',
    'tip-box': '<div class="tip-box">💡 提示内容</div>',
    'stat-card': '<div class="stat-card"><div class="stat-value">42</div><div class="stat-label">标签</div></div>',
    'insight-card': '<div class="insight-card">新洞察 — 点击编辑</div>',
    'quote-box': '<div class="quote-box"><blockquote>引用文字</blockquote></div>',
    'highlight-box': '<div class="highlight-box"><strong>重点</strong>内容</div>',
    image: '<div class="editor-image"><img src="" alt="图片" style="max-width:100%;max-height:60vh;border-radius:8px;display:block"><p class="editor-image-caption" style="text-align:center;font-size:var(--text-xs);color:var(--text-faint);margin-top:0.3rem">点击此处添加说明</p></div>'
  };

  window.__editorState = state;
})();
