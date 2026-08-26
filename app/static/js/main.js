/* Convert — client behaviour: theme, mobile nav, converter flow. */
(function () {
  'use strict';

  /* ------------------------------------------------------------ helpers */

  function $(id) { return document.getElementById(id); }

  function formatBytes(n) {
    if (!Number.isFinite(n)) return '';
    if (n < 1024) return n + ' B';
    if (n < 1024 * 1024) return (n / 1024).toFixed(1) + ' KB';
    return (n / (1024 * 1024)).toFixed(1) + ' MB';
  }

  function extOf(name) {
    var dot = name.lastIndexOf('.');
    return dot === -1 ? '' : name.slice(dot + 1).toLowerCase();
  }

  function escapeHtml(str) {
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
  }

  /* ------------------------------------------------ IndexedDB file store */

  var DB_NAME = 'convert-pending';
  var DB_STORE = 'files';
  var DB_KEY = 'current';

  function openDB(callback) {
    var req;
    try { req = indexedDB.open(DB_NAME, 1); } catch (e) { callback(null); return; }
    req.onupgradeneeded = function (ev) {
      var db = ev.target.result;
      if (!db.objectStoreNames.contains(DB_STORE)) {
        db.createObjectStore(DB_STORE);
      }
    };
    req.onsuccess = function (ev) { callback(ev.target.result); };
    req.onerror = function () { callback(null); };
  }

  function saveFileToDB(blob, meta, callback) {
    openDB(function (db) {
      if (!db) { callback(false); return; }
      var tx = db.transaction(DB_STORE, 'readwrite');
      tx.objectStore(DB_STORE).put({ blob: blob, meta: meta, ts: Date.now() }, DB_KEY);
      tx.oncomplete = function () { callback(true); };
      tx.onerror = function () { callback(false); };
    });
  }

  function loadFileFromDB(callback) {
    openDB(function (db) {
      if (!db) { callback(null); return; }
      var tx = db.transaction(DB_STORE, 'readonly');
      var req = tx.objectStore(DB_STORE).get(DB_KEY);
      req.onsuccess = function () { callback(req.result || null); };
      req.onerror = function () { callback(null); };
    });
  }

  function clearFileFromDB(callback) {
    openDB(function (db) {
      if (!db) { if (callback) callback(); return; }
      var tx = db.transaction(DB_STORE, 'readwrite');
      tx.objectStore(DB_STORE).delete(DB_KEY);
      tx.oncomplete = function () { if (callback) callback(); };
      tx.onerror = function () { if (callback) callback(); };
    });
  }

  function saveJobToSession(jobId) {
    try { sessionStorage.setItem('convert-job', jobId); } catch (e) {}
  }
  function loadJobFromSession() {
    try { return sessionStorage.getItem('convert-job'); } catch (e) { return null; }
  }
  function clearJobFromSession() {
    try { sessionStorage.removeItem('convert-job'); } catch (e) {}
  }

  /* -------------------------------------------------------------- theme */

  function initTheme() {
    var btn = $('theme-toggle');
    if (!btn) return;

    var root = document.documentElement;
    function isDark() {
      return root.getAttribute('data-theme') === 'dark';
    }
    function render() {
      btn.setAttribute('aria-pressed', String(isDark()));
      btn.setAttribute(
        'aria-label',
        isDark() ? 'Switch to light mode' : 'Switch to dark mode'
      );
    }
    btn.addEventListener('click', function () {
      var next = isDark() ? 'light' : 'dark';
      try {
        localStorage.setItem('convert-theme', next);
      } catch (e) { /* storage unavailable */ }
      if (next === 'dark') root.setAttribute('data-theme', 'dark');
      else root.removeAttribute('data-theme');
      render();
    });

    // Follow OS changes only while the user has no explicit choice.
    try {
      matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function (ev) {
        if (!localStorage.getItem('convert-theme')) {
          if (ev.matches) root.setAttribute('data-theme', 'dark');
          else root.removeAttribute('data-theme');
          render();
        }
      });
    } catch (e) { /* older browsers */ }

    render();
  }

  /* ---------------------------------------------------------- mobile nav */

  function initMobileNav() {
    var btn = $('menu-toggle');
    var panel = $('mobile-nav');
    if (!btn || !panel) return;

    function setOpen(open) {
      panel.hidden = !open;
      btn.setAttribute('aria-expanded', String(open));
      btn.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
      if (open) {
        var firstLink = panel.querySelector('a');
        if (firstLink) firstLink.focus();
      }
    }

    btn.addEventListener('click', function () {
      setOpen(panel.hidden);
    });
    panel.addEventListener('click', function (ev) {
      if (ev.target.closest('a')) setOpen(false);
    });
    document.addEventListener('keydown', function (ev) {
      if (ev.key === 'Escape' && !panel.hidden) {
        setOpen(false);
        btn.focus();
      }
    });
  }

  /* ------------------------------------------------------------ converter */

  function initConverter() {
    var rootEl = $('converter');
    if (!rootEl) return;

    var CATALOG = window.__CATALOG__ || [];
    var ANON_LIMIT = window.__ANON_LIMIT__ || null;

    var EXT_TO_FORMAT = {};
    [
      ['pdf', ['pdf']],
      ['docx', ['docx']], ['doc', ['doc']],
      ['rtf', ['rtf']],
      ['pptx', ['pptx']], ['ppt', ['ppt']],
      ['xlsx', ['xlsx']], ['xls', ['xls']],
      ['csv', ['csv']],
      ['txt', ['txt']],
      ['md', ['md', 'markdown']],
      ['html', ['html', 'htm']],
      ['epub', ['epub']],
      ['png', ['png']], ['jpg', ['jpg', 'jpeg']], ['webp', ['webp']],
      ['gif', ['gif']], ['bmp', ['bmp']],
      ['svg', ['svg']], ['tiff', ['tiff', 'tif']], ['ico', ['ico']],
      ['odt', ['odt']], ['ods', ['ods']], ['odp', ['odp']],
      ['json', ['json']], ['xml', ['xml']], ['yaml', ['yaml', 'yml']],
      ['ini', ['ini']], ['log', ['log']], ['sql', ['sql']],
      ['py', ['py']], ['js', ['js']], ['ts', ['ts']],
      ['java', ['java']], ['cpp', ['cpp', 'cc', 'cxx']], ['c', ['c']],
      ['go', ['go']], ['rs', ['rs']], ['rb', ['rb']],
      ['php', ['php']], ['swift', ['swift']], ['kt', ['kt']],
      ['r', ['r']], ['scala', ['scala']], ['hs', ['hs']],
      ['lua', ['lua']], ['sh', ['sh', 'bash']], ['bat', ['bat', 'cmd']],
      ['ps1', ['ps1']], ['vbs', ['vbs']], ['toml', ['toml']],
      ['cfg', ['cfg', 'conf', 'config']], ['env', ['env']],
      ['gitignore', ['gitignore']], ['makefile', ['makefile']],
      ['cmake', ['cmake']], ['gradle', ['gradle']],
      ['properties', ['properties']], ['csv-excel', ['csv']]
    ].forEach(function (pair) {
      pair[1].forEach(function (ext) { EXT_TO_FORMAT[ext] = pair[0]; });
    });

    var dropzone = $('dropzone');
    var fileInput = $('file-input');
    var fileCard = $('file-card');
    var fileNameEl = $('file-name');
    var fileSizeEl = $('file-size');
    var fileFormatEl = $('file-format');
    var removeBtn = $('remove-file');
    var targetRow = $('target-row');
    var targetSelect = $('target-select');
    var convertBtn = $('convert-btn');
    var progressWrap = $('progress-wrap');
    var progressLabel = $('progress-label');
    var progressBar = $('progress-bar');
    var progressFill = $('progress-fill');
    var progressPct = $('progress-pct');
    var resultBox = $('result');
    var resultTitle = $('result-title');
    var downloadBtn = $('download-btn');
    var errorBox = $('error-box');
    var quotaNote = $('quota-note');

    var currentFile = null;
    var currentJobId = null;
    var eventSource = null;
    var restoring = false;

    function showError(msg) {
      errorBox.innerHTML = escapeHtml(msg);
      errorBox.hidden = false;
      errorBox.focus();
    }
    function clearError() {
      errorBox.hidden = true;
      errorBox.textContent = '';
    }
    function setProgress(pct, label) {
      pct = Math.max(0, Math.min(100, Math.round(pct)));
      progressWrap.hidden = false;
      progressFill.style.width = pct + '%';
      progressPct.textContent = pct + '%';
      progressBar.setAttribute('aria-valuenow', String(pct));
      if (label) progressLabel.textContent = label;

      var steps = progressWrap.querySelectorAll('.progress-step');
      steps.forEach(function (step) {
        var stepName = step.getAttribute('data-step');
        step.classList.remove('active', 'completed');
        if (stepName === 'upload' && pct >= 5 && pct < 40) {
          step.classList.add('active');
        } else if (stepName === 'upload' && pct >= 40) {
          step.classList.add('completed');
        } else if (stepName === 'process' && pct >= 40 && pct < 90) {
          step.classList.add('active');
        } else if (stepName === 'process' && pct >= 90) {
          step.classList.add('completed');
        } else if (stepName === 'complete' && pct >= 90) {
          step.classList.add('active');
        } else if (stepName === 'complete' && pct >= 100) {
          step.classList.add('completed');
        }
      });
    }

    function refreshQuota() {
      if (!quotaNote) return;
      fetch('/api/v1/quota')
        .then(function (r) { return r.ok ? r.json() : null; })
        .then(function (q) {
          if (!q) { quotaNote.textContent = ''; return; }
          quotaNote.textContent =
            q.remaining + ' of ' + q.limit + ' free conversions left today.';
        })
        .catch(function () { quotaNote.textContent = ''; });
    }

    function populateTargets(sourceFormat, preselect) {
      targetSelect.innerHTML = '';
      var options = CATALOG.filter(function (c) {
        return c.from.indexOf(sourceFormat) !== -1 && c.location === 'server';
      }).sort(function (a, b) { return a.label.localeCompare(b.label); });

      if (!options.length) {
        showError('No server conversion available for this file type yet.');
        convertBtn.disabled = true;
        return;
      }
      options.forEach(function (c, i) {
        var opt = document.createElement('option');
        opt.value = c.to;
        opt.textContent = c.label + ' (max ' + c.maxSizeMB + ' MB)';
        if (preselect && c.to === preselect) opt.selected = true;
        else if (i === 0 && !preselect) opt.selected = true;
        targetSelect.appendChild(opt);
      });
      convertBtn.disabled = false;
      clearError();
    }

    function showFileUI(file, fmt) {
      fileNameEl.textContent = file.name;
      fileSizeEl.textContent = formatBytes(file.size);
      fileFormatEl.textContent = fmt;
      fileCard.hidden = false;
      targetRow.hidden = false;
    }

    function persistFile(file, fmt) {
      try {
        saveFileToDB(file, { name: file.name, size: file.size, format: fmt, ts: Date.now() }, function () {});
      } catch (e) { /* IndexedDB unavailable */ }
    }

    function acceptFile(file, preselectTarget) {
      clearError();
      resultBox.hidden = true;
      progressWrap.hidden = true;
      if (eventSource) { eventSource.close(); eventSource = null; }

      var ext = extOf(file.name);
      var fmt = EXT_TO_FORMAT[ext];
      if (!fmt) {
        currentFile = null;
        fileCard.hidden = true;
        targetRow.hidden = true;
        showError('Unsupported file type ".' + escapeHtml(ext) + '". We support over 50 file types including documents, spreadsheets, presentations, images, and code files.');
        return;
      }
      currentFile = file;
      showFileUI(file, fmt);
      populateTargets(fmt, preselectTarget);
      if (!restoring) persistFile(file, fmt);
    }

    function resetAll() {
      currentFile = null;
      if (eventSource) { eventSource.close(); eventSource = null; }
      currentJobId = null;
      fileInput.value = '';
      fileCard.hidden = true;
      targetRow.hidden = true;
      progressWrap.hidden = true;
      resultBox.hidden = true;
      clearError();
      clearFileFromDB();
      clearJobFromSession();
      dropzone.focus();
    }

    async function startConversion() {
      if (!currentFile || convertBtn.disabled) return;
      clearError();
      resultBox.hidden = true;
      convertBtn.disabled = true;

      var target = targetSelect.value;
      setProgress(5, 'Uploading\u2026');

      try {
        var fd = new FormData();
        fd.append('file', currentFile, currentFile.name);

        var upRes = await fetch('/api/v1/files/upload', { method: 'POST', body: fd });
        if (!upRes.ok) throw await apiError(upRes);
        var uploaded = await upRes.json();
        setProgress(20, 'Queued\u2026');

        var jobRes = await fetch('/api/v1/jobs/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            tasks: [{ operation: 'convert', input: uploaded.fileId, outputFormat: target }]
          })
        });
        if (!jobRes.ok) throw await apiError(jobRes);
        var job = await jobRes.json();
        currentJobId = job.id;
        saveJobToSession(job.id);

        listenForProgress(job.id);
      } catch (err) {
        handleError(err);
        convertBtn.disabled = false;
      }
    }

    function listenForProgress(jobId) {
      setProgress(25, 'Converting\u2026');
      eventSource = new EventSource('/api/v1/jobs/' + encodeURIComponent(jobId) + '/events');

      eventSource.addEventListener('job', function (ev) {
        var state;
        try { state = JSON.parse(ev.data); } catch (e) { return; }
        setProgress(Math.max(25, state.progress || 25), 'Converting\u2026');

        if (state.status === 'done' && state.outputs && state.outputs.length) {
          finishSuccess(state.outputs[0]);
        } else if (state.status === 'error' || state.status === 'cancelled') {
          failConversion(state);
        }
      });
      eventSource.onerror = function () {
        // Fall back to polling once if the stream drops before completion.
        eventSource.close();
        eventSource = null;
        pollUntilDone(jobId, 40);
      };
    }

    function pollUntilDone(jobId, attemptsLeft) {
      if (attemptsLeft <= 0) {
        failConversion({ error: { message: 'Timed out waiting for the conversion.' } });
        return;
      }
      fetch('/api/v1/jobs/' + encodeURIComponent(jobId))
        .then(function (r) { return r.ok ? r.json() : Promise.reject(new Error('Lost track of the job.')); })
        .then(function (state) {
          setProgress(Math.max(25, state.progress || 25), 'Converting\u2026');
          if (state.status === 'done' && state.outputs && state.outputs.length) {
            finishSuccess(state.outputs[0]);
          } else if (state.status === 'error' || state.status === 'cancelled') {
            failConversion(state);
          } else {
            setTimeout(function () { pollUntilDone(jobId, attemptsLeft - 1); }, 1000);
          }
        })
        .catch(function (err) { failConversion({ error: { message: err.message } }); });
    }

    function finishSuccess(output) {
      if (eventSource) { eventSource.close(); eventSource = null; }
      setProgress(100, 'Done.');
      downloadBtn.href = output.downloadUrl;
      downloadBtn.setAttribute('download', output.filename || '');
      resultTitle.textContent = output.filename || 'Your file';
      var resultSub = document.getElementById('result-sub');
      if (resultSub) {
        resultSub.textContent = formatBytes(output.sizeBytes) + ' \u00b7 Ready to download';
      }
      resultBox.hidden = false;
      convertBtn.disabled = false;
      downloadBtn.focus();
      clearFileFromDB();
      clearJobFromSession();
      refreshQuota();
    }

    function failConversion(state) {
      if (eventSource) { eventSource.close(); eventSource = null; }
      progressWrap.hidden = true;
      convertBtn.disabled = false;
      clearJobFromSession();
      var msg = (state.error && state.error.message) || 'The conversion failed. Try a different file or format.';
      showError(msg);
      refreshQuota();
    }

    async function apiError(res) {
      var detail = '';
      try {
        var body = await res.json();
        detail = (body.detail && body.detail.message) || body.message || body.detail || '';
        if (typeof detail === 'object') detail = JSON.stringify(detail);
      } catch (e) { /* non-JSON error */ }
      var err = new Error(detail || humanStatus(res.status));
      err.status = res.status;
      return err;
    }

    function humanStatus(status) {
      switch (status) {
        case 402: return 'Daily free limit reached. Come back tomorrow.';
        case 413: return 'That file is larger than this conversion allows.';
        case 415: return 'That file type is not supported.';
        case 429: return 'Too many requests \u2014 take a breath and try again shortly.';
        default: return 'Something went wrong (' + status + '). Please try again.';
      }
    }

    function handleError(err) {
      progressWrap.hidden = true;
      showError((err && err.message) || 'Unexpected error. Please try again.');
    }

    /* wire up */

    dropzone.addEventListener('click', function () { fileInput.click(); });
    dropzone.addEventListener('keydown', function (ev) {
      if (ev.key === 'Enter' || ev.key === ' ') {
        ev.preventDefault();
        fileInput.click();
      }
    });
    ['dragenter', 'dragover'].forEach(function (evtName) {
      dropzone.addEventListener(evtName, function (ev) {
        ev.preventDefault();
        dropzone.classList.add('dragover');
      });
    });
    ['dragleave', 'drop'].forEach(function (evtName) {
      dropzone.addEventListener(evtName, function (ev) {
        ev.preventDefault();
        dropzone.classList.remove('dragover');
      });
    });
    dropzone.addEventListener('drop', function (ev) {
      var file = ev.dataTransfer && ev.dataTransfer.files && ev.dataTransfer.files[0];
      if (file) acceptFile(file);
    });
    fileInput.addEventListener('change', function () {
      if (fileInput.files && fileInput.files[0]) acceptFile(fileInput.files[0]);
    });
    removeBtn.addEventListener('click', resetAll);
    convertBtn.addEventListener('click', startConversion);

    refreshQuota();

    /* restore file from IndexedDB after reload */
    var savedJobId = loadJobFromSession();
    loadFileFromDB(function (record) {
      if (!record || !record.blob || !record.meta) return;
      var meta = record.meta;
      var blob = record.blob;
      var restoredFile;
      try {
        restoredFile = new File([blob], meta.name, { type: blob.type || 'application/octet-stream' });
      } catch (e) { return; }
      restoring = true;
      acceptFile(restoredFile, meta.format);
      restoring = false;

      if (savedJobId) {
        currentJobId = savedJobId;
        clearError();
        resultBox.hidden = true;
        convertBtn.disabled = true;
        listenForProgress(savedJobId);
      }
    });
  }

  /* ---------------------------------------------------------------- boot */

  function init() {
    initTheme();
    initMobileNav();
    initConverter();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
