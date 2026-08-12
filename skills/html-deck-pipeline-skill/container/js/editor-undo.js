/* editor-undo.js — undo/redo Command pattern for WYSIWYG editor */
(() => {
  'use strict';

  const CONFIG = (window.__CONFIG && window.__CONFIG.editor) || {};
  const MAX_STACK = CONFIG.maxUndoStack || 50;

  const undoStack = [];
  const redoStack = [];
  let isUndoingOrRedoing = false;  // guards against recording commands during undo/redo

  const L = window.__logger || { debug: function(){}, info: function(){}, warn: function(){} };

  function push(label, executeFn, undoFn) {
    if (isUndoingOrRedoing) return;
    if (undoStack.length >= MAX_STACK) {
      undoStack.shift(); // drop oldest
    }
    undoStack.push({ label, execute: executeFn, undo: undoFn });
    redoStack.length = 0; // clear redo history on new mutation
  }

  function undo() {
    const cmd = undoStack.pop();
    if (!cmd) return;
    isUndoingOrRedoing = true;
    try {
      cmd.undo();
      redoStack.push(cmd);
      L.debug('撤销', cmd.label);
    } catch (e) {
      L.error('撤销失败', { label: cmd.label, error: e.message });
      undoStack.push(cmd); // put it back on failure
    } finally {
      isUndoingOrRedoing = false;
    }
  }

  function redo() {
    const cmd = redoStack.pop();
    if (!cmd) return;
    isUndoingOrRedoing = true;
    try {
      cmd.execute();
      undoStack.push(cmd);
      L.debug('重做', cmd.label);
    } catch (e) {
      L.error('重做失败', { label: cmd.label, error: e.message });
      redoStack.push(cmd);
    } finally {
      isUndoingOrRedoing = false;
    }
  }

  function canUndo() { return undoStack.length > 0; }
  function canRedo() { return redoStack.length > 0; }
  function clear() { undoStack.length = 0; redoStack.length = 0; }

  window.__undoManager = { push, undo, redo, canUndo, canRedo, clear };
})();
