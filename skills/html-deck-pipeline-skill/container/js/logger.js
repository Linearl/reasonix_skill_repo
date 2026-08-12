/* logger.js — development debug logger with auto-save (IIFE, no dependencies) */
(() => {
  'use strict';

  const cfg = (window.__CONFIG && window.__CONFIG.log) || {};
  const AUTO_SAVE_MS = cfg.autoSaveIntervalMs || 30000;
  const MEMORY_MAX = cfg.maxEntriesPerFile || 2000;

  const entries = [];
  let sentIdx = 0;    // cursor: entries before this have been sent to server
  let timer = null;

  function now() {
    const d = new Date();
    return d.toISOString().replace('T', ' ').slice(0, 23);
  }

  function log(level, action, detail) {
    const entry = { ts: now(), level: level, action: action };
    if (detail !== undefined) entry.detail = detail;
    entries.push(entry);
    // Keep memory bounded
    while (entries.length > MEMORY_MAX) {
      entries.shift();
      if (sentIdx > 0) sentIdx--;
    }

    const fn = level === 'error' ? console.error : level === 'warn' ? console.warn : console.log;
    fn('[editor]', level.toUpperCase(), action, detail || '');
    return entry;
  }

  async function flushToDisk() {
    const batch = entries.slice(sentIdx);
    if (batch.length === 0) return null;

    const payload = {
      url: location.href,
      ua: navigator.userAgent.slice(0, 80),
      entries: batch
    };
    try {
      const res = await fetch('/log', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      sentIdx = entries.length;  // mark all as sent
      console.log('[logger]', 'flush', batch.length, 'entries →', data.file || 'ok');
      return data;
    } catch (err) {
      console.error('[logger] flush failed:', err);
      return { error: err.message };
    }
  }

  function startTimer() {
    if (timer) return;
    timer = setInterval(flushToDisk, AUTO_SAVE_MS);
    console.log('[logger] auto-save every', AUTO_SAVE_MS + 'ms');
  }

  function stopTimer() {
    if (timer) { clearInterval(timer); timer = null; }
  }

  const logger = {
    debug: function(action, detail) { return log('debug', action, detail); },
    info:  function(action, detail) { return log('info', action, detail); },
    warn:  function(action, detail) { return log('warn', action, detail); },
    error: function(action, detail) { return log('error', action, detail); },

    getEntries: function() { return entries.slice(); },
    count: function() { return entries.length; },
    unsent: function() { return entries.length - sentIdx; },
    clear: function() { entries.length = 0; sentIdx = 0; },

    flushToDisk: flushToDisk,
    startTimer: startTimer,
    stopTimer: stopTimer,

    saveToDisk: async function() {
      // Force flush all (even if already sent, resend for safety)
      const payload = {
        url: location.href,
        ua: navigator.userAgent.slice(0, 80),
        entries: entries.slice(),
        full: true
      };
      try {
        const res = await fetch('/log', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        sentIdx = entries.length;
        console.log('[logger]', 'full save', entries.length, 'entries →', data.file || 'ok');
        return data;
      } catch (err) {
        return { error: err.message };
      }
    }
  };

  window.__logger = logger;

  // Capture unhandled errors
  window.addEventListener('error', function(e) {
    logger.error('未捕获异常', { msg: e.message, file: e.filename, line: e.lineno, col: e.colno });
  });
  window.addEventListener('unhandledrejection', function(e) {
    logger.error('未处理的Promise拒绝', { reason: String(e.reason).slice(0, 200) });
  });

  // Auto-save before page unload
  window.addEventListener('beforeunload', function() {
    stopTimer();
    // Use sendBeacon for reliable last save
    const batch = entries.slice(sentIdx);
    if (batch.length > 0) {
      const payload = { url: location.href, ua: navigator.userAgent.slice(0, 80), entries: batch };
      navigator.sendBeacon('/log', JSON.stringify(payload));
    }
  });

  logger.info('日志系统就绪');
  startTimer();
})();
