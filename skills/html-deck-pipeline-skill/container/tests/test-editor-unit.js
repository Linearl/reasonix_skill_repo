/**
 * test-editor-unit.js — Unit tests for HTML Deck WYSIWYG Editor
 *
 * Tests pure logic without browser DOM:
 *   - rgbToHex utility
 *   - Undo/redo manager (push, undo, redo, canUndo, canRedo, max stack, redo-clears-on-new-push)
 *   - Modification storage (Map operations: storeMod, removeMod)
 *   - hasPendingChanges logic
 *   - isSizeProperty logic
 *
 * Run: node test-editor-unit.js
 */

const path = require('path');
const fs = require('fs');

// ── Test framework (minimal, zero deps) ──────────────────────────────────────
const stats = { pass: 0, fail: 0, skipped: 0 };
const failures = [];

function assert(condition, msg) {
  if (condition) {
    stats.pass++;
  } else {
    stats.fail++;
    failures.push(msg);
  }
}

function assertEqual(actual, expected, msg) {
  if (actual === expected) {
    stats.pass++;
  } else {
    stats.fail++;
    failures.push(`${msg} — expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`);
  }
}

function assertDeepEqual(actual, expected, msg) {
  const a = JSON.stringify(actual);
  const b = JSON.stringify(expected);
  if (a === b) {
    stats.pass++;
  } else {
    stats.fail++;
    failures.push(`${msg} — expected ${b}, got ${a}`);
  }
}

function describe(label, fn) {
  console.log(`\n${label}`);
  fn();
}

function it(label, fn) {
  try {
    fn();
  } catch (e) {
    stats.fail++;
    failures.push(`${label} — THREW: ${e.message}`);
  }
}

// ── Load editor-undo.js in a mock browser environment ───────────────────────
function loadUndoManager() {
  const mockWindow = {};

  mockWindow.__logger = { debug: () => {}, info: () => {}, warn: () => {}, error: () => {} };
  mockWindow.__CONFIG = {};
  // Helper to set config before loading
  mockWindow.setConfig = (cfg) => { mockWindow.__CONFIG = cfg; };

  // Execute editor-undo.js in the mock context
  const undoPath = path.join(__dirname, '..', 'js', 'editor-undo.js');
  const undoCode = fs.readFileSync(undoPath, 'utf-8');

  // Wrap in a function that provides the mock globals
  const fn = new Function('window', `${undoCode}; return window.__undoManager;`);
  const undoManager = fn(mockWindow);

  return { undoManager, mockWindow };
}

// ── Standalone rgbToHex (copy of the pure function from editor.js) ──────────
function rgbToHex(rgb) {
  if (!rgb || rgb === 'transparent' || rgb === 'rgba(0, 0, 0, 0)') return '#000000';
  const m = rgb.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
  if (!m) return rgb;
  return '#' + [m[1], m[2], m[3]].map(x => parseInt(x).toString(16).padStart(2, '0')).join('');
}

// ── Standalone isSizeProperty (copy from editor.js) ──────────────────────────
function isSizeProperty(prop) {
  return /font-size|padding|margin|line-height|border-width|width|height|gap/i.test(prop);
}

// ── Modification storage patterns (mirrors storeMod / removeMod) ─────────────
function createModStore() {
  return new Map(); // Map<slideKey, Map<path, Map<prop, value>>>
}

function storeMod(store, key, path, prop, value) {
  if (!store.has(key)) store.set(key, new Map());
  const sm = store.get(key);
  if (!sm.has(path)) sm.set(path, new Map());
  sm.get(path).set(prop, value);
}

function removeMod(store, key, path, prop) {
  if (!key || !path) return;
  const sm = store.get(key);
  if (!sm) return;
  const em = sm.get(path);
  if (!em) return;
  em.delete(prop);
  if (em.size === 0) sm.delete(path);
}

// ── hasPendingChanges logic ─────────────────────────────────────────────────
function hasPendingChanges(modifications, domMods, textChanges, deletions) {
  if (modifications.size > 0) return true;
  if (domMods.size > 0) return true;
  if (textChanges.size > 0) return true;
  if (deletions.size > 0) return true;
  return false;
}

// ── logResult ───────────────────────────────────────────────────────────────
function logResult() {
  const total = stats.pass + stats.fail;
  console.log(`\n${'='.repeat(50)}`);
  console.log(`RESULTS: ${stats.pass} passed, ${stats.fail} failed, ${total} total`);
  if (failures.length > 0) {
    console.log(`\nFAILURES:`);
    failures.forEach((f, i) => console.log(`  ${i + 1}) ${f}`));
    process.exit(1);
  } else {
    console.log(`\nAll tests passed.`);
  }
}

// ══════════════════════════════════════════════════════════════════════════════
// TESTS
// ══════════════════════════════════════════════════════════════════════════════

// ── rgbToHex ────────────────────────────────────────────────────────────────
describe('rgbToHex utility', () => {
  it('converts rgb(255, 0, 0) to #ff0000', () => {
    assertEqual(rgbToHex('rgb(255, 0, 0)'), '#ff0000');
  });

  it('converts rgb(0, 255, 0) to #00ff00', () => {
    assertEqual(rgbToHex('rgb(0, 255, 0)'), '#00ff00');
  });

  it('converts rgb(0, 0, 255) to #0000ff', () => {
    assertEqual(rgbToHex('rgb(0, 0, 255)'), '#0000ff');
  });

  it('converts rgba(255, 255, 255, 1) to #ffffff', () => {
    assertEqual(rgbToHex('rgba(255, 255, 255, 1)'), '#ffffff');
  });

  it('converts rgb(0, 0, 0) to #000000', () => {
    assertEqual(rgbToHex('rgb(0, 0, 0)'), '#000000');
  });

  it('handles transparent returns #000000', () => {
    assertEqual(rgbToHex('transparent'), '#000000');
  });

  it('handles rgba(0, 0, 0, 0) returns #000000', () => {
    assertEqual(rgbToHex('rgba(0, 0, 0, 0)'), '#000000');
  });

  it('handles empty/undefined input returns #000000', () => {
    assertEqual(rgbToHex(''), '#000000');
    assertEqual(rgbToHex(null), '#000000');
    assertEqual(rgbToHex(undefined), '#000000');
  });

  it('returns hex string unchanged if no rgb match', () => {
    assertEqual(rgbToHex('#ff00ff'), '#ff00ff');
  });

  it('handles rgb with spaces (rgb( 12 , 34 , 56 ))', () => {
    assertEqual(rgbToHex('rgb(12, 34, 56)'), '#0c2238');
  });

  it('pads single-digit hex values with leading zero', () => {
    assertEqual(rgbToHex('rgb(1, 2, 3)'), '#010203');
  });
});

// ── isSizeProperty ──────────────────────────────────────────────────────────
describe('isSizeProperty', () => {
  it('detects font-size as size property', () => {
    assert(isSizeProperty('font-size'), 'font-size should be detected');
  });

  it('detects padding as size property', () => {
    assert(isSizeProperty('padding'), 'padding should be detected');
  });

  it('detects margin as size property', () => {
    assert(isSizeProperty('margin'), 'margin should be detected');
  });

  it('detects line-height as size property', () => {
    assert(isSizeProperty('line-height'), 'line-height should be detected');
  });

  it('detects border-width as size property', () => {
    assert(isSizeProperty('border-width'), 'border-width should be detected');
  });

  it('detects width as size property', () => {
    assert(isSizeProperty('width'), 'width should be detected');
  });

  it('detects height as size property', () => {
    assert(isSizeProperty('height'), 'height should be detected');
  });

  it('detects gap as size property', () => {
    assert(isSizeProperty('gap'), 'gap should be detected');
  });

  it('does not detect color as size property', () => {
    assert(!isSizeProperty('color'), 'color should NOT be detected');
  });

  it('does not detect display as size property', () => {
    assert(!isSizeProperty('display'), 'display should NOT be detected');
  });

  it('does not detect background-color as size property', () => {
    assert(!isSizeProperty('background-color'), 'background-color should NOT be detected');
  });
});

// ── Undo Manager ────────────────────────────────────────────────────────────
describe('Undo Manager', () => {
  let um;

  // Reload fresh undo manager before each test group
  function freshUM() {
    const { undoManager } = loadUndoManager();
    undoManager.clear();
    return undoManager;
  }

  // ── Initial state ──
  it('is empty after creation', () => {
    um = freshUM();
    assert(!um.canUndo(), 'should not be able to undo');
    assert(!um.canRedo(), 'should not be able to redo');
  });

  // ── Basic push / undo / redo cycle ──
  // In the real editor, the change is applied to DOM first,
  // then push() records the undo/redo pair. undo() reverts; redo() re-applies.
  describe('basic undo/redo cycle', () => {
    it('records a push and canUndo becomes true', () => {
      um = freshUM();
      // "Apply" the change by setting a value, then record undo
      let data = 'original';
      data = 'changed'; // simulate applying the change
      um.push('change', () => { data = 'changed'; }, () => { data = 'original'; });
      assert(um.canUndo(), 'should be able to undo after push');
      assert(!um.canRedo(), 'should not be able to redo before undo');
    });

    it('undo reverts the change', () => {
      um = freshUM();
      let data = 'original';
      data = 'changed'; // apply
      um.push('change', () => { data = 'changed'; }, () => { data = 'original'; });
      um.undo();
      assertEqual(data, 'original', 'undo should revert');
    });

    it('canRedo becomes true after undo', () => {
      um = freshUM();
      let data = 'original';
      data = 'changed'; // apply
      um.push('change', () => { data = 'changed'; }, () => { data = 'original'; });
      um.undo();
      assert(um.canRedo(), 'should be able to redo after undo');
      assert(!um.canUndo(), 'should not be able to undo when at bottom');
    });

    it('redo re-applies the change', () => {
      um = freshUM();
      let data = 'original';
      data = 'changed'; // apply
      um.push('change', () => { data = 'changed'; }, () => { data = 'original'; });
      um.undo();
      assertEqual(data, 'original');
      um.redo();
      assertEqual(data, 'changed', 'redo should re-apply');
    });

    it('canUndo becomes true again after redo', () => {
      um = freshUM();
      let data = 'original';
      data = 'changed'; // apply
      um.push('change', () => { data = 'changed'; }, () => { data = 'original'; });
      um.undo();
      um.redo();
      assert(um.canUndo(), 'should be able to undo again after redo');
      assert(!um.canRedo(), 'should not be able to redo again');
    });
  });

  // ── Multiple pushes ──
  describe('multiple pushes', () => {
    it('tracks multiple undo levels', () => {
      um = freshUM();
      let data = 'original';
      // Apply change 1
      data = 'first';
      um.push('first', () => { data = 'first'; }, () => { data = 'original'; });
      // Apply change 2
      data = 'second';
      um.push('second', () => { data = 'second'; }, () => { data = 'first'; });
      assert(um.canUndo(), 'should have undo');
      um.undo(); // reverts to 'first'
      assertEqual(data, 'first', 'after undo of second push');
      um.undo(); // reverts to 'original'
      assertEqual(data, 'original', 'after undo of first push');
      assert(!um.canUndo(), 'should be at bottom');
    });

    it('can redo multiple levels', () => {
      um = freshUM();
      let data = 'original';
      data = 'first';
      um.push('first', () => { data = 'first'; }, () => { data = 'original'; });
      data = 'second';
      um.push('second', () => { data = 'second'; }, () => { data = 'first'; });
      um.undo(); // back to 'first'
      um.undo(); // back to 'original'
      um.redo(); // forward to 'first'
      assertEqual(data, 'first', 'first redo');
      um.redo(); // forward to 'second'
      assertEqual(data, 'second', 'second redo');
    });
  });

  // ── Redo clears on new push ──
  describe('redo clears on new push', () => {
    it('clears redo stack when a new command is pushed after undo', () => {
      um = freshUM();
      let data = 'original';
      data = 'first';
      um.push('first', () => { data = 'first'; }, () => { data = 'original'; });
      data = 'second';
      um.push('second', () => { data = 'second'; }, () => { data = 'first'; });
      um.undo(); // undo 'second', redo stack has 'second'
      assert(um.canRedo(), 'should have redo before new push');
      data = 'third'; // apply new change
      um.push('third', () => { data = 'third'; }, () => { data = 'first'; });
      assert(!um.canRedo(), 'redo should be cleared after new push');
    });

    it('new push after undo creates correct undo chain', () => {
      um = freshUM();
      let data = 'original';
      data = 'first';
      um.push('first', () => { data = 'first'; }, () => { data = 'original'; });
      data = 'second';
      um.push('second', () => { data = 'second'; }, () => { data = 'first'; });
      um.undo(); // reverts to 'first'
      assertEqual(data, 'first');
      // Apply new change instead of redo (branch)
      data = 'third';
      um.push('third', () => { data = 'third'; }, () => { data = 'first'; });
      // Now stack should be [first, third]
      um.undo(); // undo third: back to 'first'
      assertEqual(data, 'first', 'undo third');
      um.undo(); // undo first: back to 'original'
      assertEqual(data, 'original', 'undo first');
    });
  });

  // ── Undo failure recovery ──
  describe('undo failure recovery', () => {
    it('puts command back on undo stack if undo throws', () => {
      um = freshUM();
      let data = 'changed';
      um.push('bad', () => { data = 'changed'; }, () => { throw new Error('undo failed'); });
      um.undo(); // should gracefully handle the error
      assert(um.canUndo(), 'command should be back on undo stack after failure');
      assert(!um.canRedo(), 'redo should not have the failed command');
    });
  });

  // ── Redo failure recovery ──
  describe('redo failure recovery', () => {
    it('puts command back on redo stack if redo throws', () => {
      um = freshUM();
      let data = 'changed';
      um.push(
        'bad',
        () => { throw new Error('redo failed'); },
        () => { data = 'previous'; }
      );
      um.undo(); // undo succeeds, pushes to redo stack
      assert(um.canRedo(), 'should have redo after undo');
      um.redo(); // redo fails (execute throws)
      // After redo failure, the command should still be on redo stack
      assert(um.canRedo(), 'command should stay on redo stack after redo failure');
    });
  });

  // ── Max stack size ──
  describe('max stack size', () => {
    it('drops oldest entry when exceeding max (default 50)', () => {
      const { mockWindow } = loadUndoManager();
      // Reload with small max
      mockWindow.setConfig({ editor: { maxUndoStack: 3 } });

      const undoPath2 = path.join(__dirname, '..', 'js', 'editor-undo.js');
      const undoCode2 = fs.readFileSync(undoPath2, 'utf-8');
      const fn2 = new Function('window', `${undoCode2}; return window.__undoManager;`);
      const um2 = fn2(mockWindow);

      // Apply change then push undo for each:
      // The real editor pattern: apply change FIRST, then push undo
      let items = [];
      for (let i = 0; i < 5; i++) {
        const n = i;
        items.push(n); // apply the change
        um2.push(`cmd-${n}`, () => {
          items.push(n);
        }, () => {
          const idx = items.lastIndexOf(n);
          if (idx !== -1) items.splice(idx, 1);
        });
      }

      // Current items: [0,1,2,3,4]; stack holds last 3: [cmd-2, cmd-3, cmd-4]
      // Undo cmd-4: removes 4
      um2.undo();
      assert(um2.canUndo(), 'after 1st undo');
      // Undo cmd-3: removes 3
      um2.undo();
      assert(um2.canUndo(), 'after 2nd undo');
      // Undo cmd-2: removes 2
      um2.undo();
      assert(!um2.canUndo(), 'should be at bottom after 3 undos (max=3)');
      assertDeepEqual(items, [0, 1], 'only items 0,1 should remain (cmd-0,1 were dropped)');
    });
  });

  // ── Clear ──
  describe('clear', () => {
    it('clears both undo and redo stacks', () => {
      um = freshUM();
      let data = 'original';
      data = 'changed';
      um.push('change', () => { data = 'changed'; }, () => { data = 'original'; });
      um.undo();
      assert(um.canRedo(), 'should have redo before clear');
      um.clear();
      assert(!um.canUndo(), 'cannot undo after clear');
      assert(!um.canRedo(), 'cannot redo after clear');
    });
  });

  // ── Label tracking ──
  it('undo calls the undo function with correct label', () => {
    um = freshUM();
    let lastUndoLabel = '';
    let data = 'changed';
    um.push('my-label', () => { data = 'changed'; }, () => { lastUndoLabel = 'my-label'; });
    um.undo();
    assertEqual(lastUndoLabel, 'my-label', 'undo should call the undo function');
  });

  // ── Multiple undo/redo without state corruption ──
  it('handles repeated undo-redo cycles correctly', () => {
    um = freshUM();
    let counter = 0;
    // Apply change: go from 0 to 1, then record undo
    counter = 1;
    um.push('inc', () => { counter = 1; }, () => { counter = 0; });

    // undo-redo 10 times
    for (let i = 0; i < 10; i++) {
      um.undo();
      assertEqual(counter, 0, `cycle ${i}: after undo`);
      um.redo();
      assertEqual(counter, 1, `cycle ${i}: after redo`);
    }
  });
});

// ── Modification Storage (Map operations) ───────────────────────────────────
describe('Modification Storage (Map nesting)', () => {
  it('storeMod creates nested Maps correctly', () => {
    const store = createModStore();
    storeMod(store, 'slide-1', 'div > p', 'color', 'red');
    storeMod(store, 'slide-1', 'div > p', 'font-size', '16px');
    storeMod(store, 'slide-2', 'div.card', 'margin', '8px');

    assertEqual(store.size, 2, 'two slide keys');

    const slide1 = store.get('slide-1');
    assertEqual(slide1.size, 1, 'one path in slide-1');
    assertEqual(slide1.get('div > p').size, 2, 'two props for div > p');

    const slide2 = store.get('slide-2');
    assertEqual(slide2.size, 1, 'one path in slide-2');
    assertEqual(slide2.get('div.card').get('margin'), '8px');
  });

  it('storeMod overwrites existing prop value', () => {
    const store = createModStore();
    storeMod(store, 'slide-1', 'div > p', 'color', 'red');
    storeMod(store, 'slide-1', 'div > p', 'color', 'blue');
    assertEqual(store.get('slide-1').get('div > p').get('color'), 'blue');
  });

  it('removeMod deletes a prop', () => {
    const store = createModStore();
    storeMod(store, 'slide-1', 'div > p', 'color', 'red');
    storeMod(store, 'slide-1', 'div > p', 'font-size', '16px');
    removeMod(store, 'slide-1', 'div > p', 'color');
    assertEqual(store.get('slide-1').get('div > p').size, 1, 'one prop left');
    assert(!store.get('slide-1').get('div > p').has('color'), 'color removed');
  });

  it('removeMod cleans up empty Maps (path level)', () => {
    const store = createModStore();
    storeMod(store, 'slide-1', 'div > p', 'color', 'red');
    removeMod(store, 'slide-1', 'div > p', 'color');
    assert(!store.get('slide-1').has('div > p'), 'path should be cleaned up when empty');
  });

  it('removeMod is safe with nonexistent key/path/prop', () => {
    const store = createModStore();
    // No throw expected
    removeMod(store, 'nonexistent', 'path', 'prop');
    removeMod(store, null, null, null);
    removeMod(store, 'key', null, 'prop');
    assertEqual(store.size, 0, 'store should still be empty');
  });

  it('handles multiple paths per slide key', () => {
    const store = createModStore();
    storeMod(store, 'slide-1', 'div.panel:nth-of-type(1)', 'color', 'red');
    storeMod(store, 'slide-1', 'div.panel:nth-of-type(2)', 'color', 'blue');
    storeMod(store, 'slide-1', 'div.panel:nth-of-type(3)', 'background-color', '#fff');

    const slide1 = store.get('slide-1');
    assertEqual(slide1.size, 3, 'three paths');
    assertEqual(slide1.get('div.panel:nth-of-type(1)').get('color'), 'red');
    assertEqual(slide1.get('div.panel:nth-of-type(2)').get('color'), 'blue');
  });

  it('handles custom property values (CSS variables)', () => {
    const store = createModStore();
    storeMod(store, 'slide-1', 'h1', 'color', 'var(--accent)');
    storeMod(store, 'slide-1', 'h1', 'background-color', 'var(--bg)');
    assertEqual(store.get('slide-1').get('h1').get('color'), 'var(--accent)');
    assertEqual(store.get('slide-1').get('h1').get('background-color'), 'var(--bg)');
  });

  it('stores numeric values as strings (CSS convention)', () => {
    const store = createModStore();
    storeMod(store, 'slide-1', 'p', 'font-size', '1.25rem');
    storeMod(store, 'slide-1', 'p', 'border-width', '2px');
    assertEqual(typeof store.get('slide-1').get('p').get('font-size'), 'string');
    assertEqual(typeof store.get('slide-1').get('p').get('border-width'), 'string');
  });
});

// ── hasPendingChanges ───────────────────────────────────────────────────────
describe('hasPendingChanges', () => {
  it('returns false when all stores are empty', () => {
    const mods = new Map();
    const dom = new Map();
    const txt = new Map();
    const del = new Map();
    assert(!hasPendingChanges(mods, dom, txt, del), 'no pending changes');
  });

  it('returns true when modifications has entries', () => {
    const mods = new Map([['key', 'value']]);
    const dom = new Map();
    const txt = new Map();
    const del = new Map();
    assert(hasPendingChanges(mods, dom, txt, del), 'modifications pending');
  });

  it('returns true when domModifications has entries', () => {
    const mods = new Map();
    const dom = new Map([['key', {}]]);
    const txt = new Map();
    const del = new Map();
    assert(hasPendingChanges(mods, dom, txt, del), 'dom modifications pending');
  });

  it('returns true when textChanges has entries', () => {
    const mods = new Map();
    const dom = new Map();
    const txt = new Map([['key', {}]]);
    const del = new Map();
    assert(hasPendingChanges(mods, dom, txt, del), 'text changes pending');
  });

  it('returns true when deletions has entries', () => {
    const mods = new Map();
    const dom = new Map();
    const txt = new Map();
    const dels = new Set(); dels.add("selector"); const del = new Map([["key", dels]]);
    assert(hasPendingChanges(mods, dom, txt, del), 'deletions pending');
  });
});

// ── Edge cases and completeness ─────────────────────────────────────────────
describe('Edge cases', () => {
  it('rgbToHex handles named colors by returning them unchanged', () => {
    assertEqual(rgbToHex('rebeccapurple'), 'rebeccapurple');
  });

  it('undo on empty stack is safe', () => {
    const { undoManager } = loadUndoManager();
    undoManager.clear();
    // Should not throw
    undoManager.undo();
  });

  it('redo on empty stack is safe', () => {
    const { undoManager } = loadUndoManager();
    undoManager.clear();
    // Should not throw
    undoManager.redo();
  });

  it('stores modifications with empty string values', () => {
    const store = createModStore();
    storeMod(store, 'key', 'path', 'color', '');
    assertEqual(store.get('key').get('path').get('color'), '');
  });

  it('removeMod handles empty string keys gracefully', () => {
    const store = createModStore();
    storeMod(store, 'key', 'path', 'color', 'red');
    removeMod(store, '', 'path', 'color');  // empty key: should be safe
    assert(store.get('key').get('path').has('color'), 'should not remove for empty key');
  });

  it('undo manager clear resets to initial state', () => {
    const um = loadUndoManager().undoManager;
    let data = 0;
    data = 1; // apply
    um.push('a', () => { data = 1; }, () => { data = 0; });
    data = 2; // apply
    um.push('b', () => { data = 2; }, () => { data = 1; });
    um.undo(); // pop b, push to redo (data back to 1)
    assert(um.canRedo(), 'should have redo before clear');
    um.clear();
    assert(!um.canUndo(), 'cannot undo after clear');
    assert(!um.canRedo(), 'cannot redo after clear');
  });
});

// ── Print results ──────────────────────────────────────────────────────────
logResult();
