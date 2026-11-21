(function () {
  "use strict";
  var BOOT = window.HEOCR_BOOT || { language: "he", strings: { he: {} } };
  var lang = BOOT.language in BOOT.strings ? BOOT.language : "he";
  var current = null; // the last result
  var view = "formatted";
  var zoom = 10;
  var working = false;
  var readingStarted;
  var elapsedTimer;
  var progress = null;
  var currentMessage;
  var readingId = 0;
  var indexRows = [];
  var activeIndexRow = null;
  document.body.classList.add(BOOT.platform === "darwin" ? "mac" : "win");

  function $(id) { return document.getElementById(id); }
  function t(key, vars) {
    var s = (BOOT.strings[lang] || {})[key];
    if (s === undefined) s = (BOOT.strings.en || {})[key] || key;
    if (vars) Object.keys(vars).forEach(function (k) { s = s.split("{" + k + "}").join(String(vars[k])); });
    return s;
  }
  function api() { return (window.pywebview && window.pywebview.api) || null; }

  function applyLanguage() {
    document.documentElement.lang = lang;
    document.documentElement.dir = lang === "he" ? "rtl" : "ltr";
    document.querySelectorAll("[data-i18n]").forEach(function (el) {
      var key = el.getAttribute("data-i18n");
      var n = el.getAttribute("data-n");
      el.textContent = t(key, n !== null ? { n: n } : null);
    });
    document.querySelectorAll("[data-label]").forEach(function (el) {
      el.setAttribute("aria-label", t(el.dataset.label));
    });
    if (working) showProgress(progress);
    if (currentMessage) localizeMessage();
    setShortcutTitles();
    $("about-version").textContent = t("version", { v: BOOT.version, h: BOOT.heocr, t: BOOT.tesseract });
    if (current) {
      showChips(current);
      indexRows.forEach(function (row) {
        if (row.pageLabel) row.label.textContent = row.target.textContent;
      });
    }
  }

  function show(name) {
    setSaveMenu(false);
    hideToast();
    ["start", "reading", "result", "message"].forEach(function (v) {
      document.body.classList.toggle("is-" + v, v === name);
    });
  }

  var toastTimer;
  function hideToast() {
    clearTimeout(toastTimer);
    if ($("toast").contains(document.activeElement) && current) $("save").focus();
    document.body.classList.remove("toast-on");
  }

  function toast(text, saved) {
    hideToast();
    $("toast-label").textContent = text;
    $("toast-name").textContent = saved ? saved.name : "";
    $("toast-name").parentElement.hidden = !saved;
    var reveal = $("toast-reveal");
    reveal.hidden = !(saved && saved.reveal);
    reveal.onclick = reveal.hidden ? null : function () {
      if (api()) api().reveal_saved(saved.reveal);
      hideToast();
    };
    document.body.classList.add("toast-on");
    toastTimer = setTimeout(hideToast, reveal.hidden ? 4000 : 8000);
  }

  function chip(text) {
    var el = document.createElement("span");
    el.className = "chip";
    el.textContent = text;
    return el;
  }

  function showChips(r) {
    var box = $("chips");
    box.textContent = "";
    if (r.pages) box.appendChild(chip(r.pages === 1 ? t("page") : t("pages", { n: r.pages })));
    var routeBox = $("routes");
    routeBox.textContent = "";
    var routes = r.routes || {};
    var names = { text_layer: "route_text_layer", ocr: "route_ocr", none: "route_none" };
    var shown = false;
    Object.keys(routes).forEach(function (k) {
      var label = names[k] ? t(names[k]) : k;
      // The page count only when there is more than one page: "OCR (12)".
      routeBox.appendChild(chip(label + (r.pages > 1 ? " (" + routes[k] + ")" : "")));
      shown = true;
    });
    if (!shown) {
      var sources = r.sources || {};
      var office = Object.keys(sources).some(function (s) { return s !== "ocr"; });
      if (office) routeBox.appendChild(chip(t("route_office")));
      if (sources.ocr) routeBox.appendChild(chip(t("route_ocr")));
    }
    box.appendChild(chip(t("seconds", { s: r.seconds })));
    $("how").hidden = !routeBox.childElementCount;
    var notes = $("notes");
    notes.textContent = "";
    function note(text, title) {
      var notice = document.createElement("div");
      notice.className = "notice";
      var body = document.createElement("p");
      if (title) {
        var strong = document.createElement("strong");
        strong.textContent = title;
        body.append(strong, " ");
      }
      body.append(text);
      notice.appendChild(body);
      notes.appendChild(notice);
    }
    if (!r.ocr_available) note(t("no_ocr"));
    (r.notes || []).forEach(function (n) { note(t("note_" + n)); });
    if (r.unread_picture_page) {
      var slots = { n: r.unread, page: r.unread_picture_page };
      note(t("unread_picture_body", slots), t("unread_picture_title", slots));
    } else if (r.unread) {
      var count = t(r.unread === 1 ? "unread_1" : "unread_n", { n: r.unread });
      note(count + " " + t("unread_details"));
    }
    notes.hidden = !notes.childElementCount;
  }

  function setIndexCurrent(row) {
    if (row === activeIndexRow) return;
    if (activeIndexRow) activeIndexRow.button.removeAttribute("aria-current");
    activeIndexRow = row;
    if (row) row.button.setAttribute("aria-current", "true");
  }

  function updateIndexCurrent() {
    if ($("index").hidden || !indexRows.length) return;
    var reader = $("reader");
    var cutoff = reader.getBoundingClientRect().top + 36;
    // Rows are in document order, so a scroll needs only a few position lookups.
    var low = 0;
    var high = indexRows.length;
    while (low < high) {
      var mid = Math.floor((low + high) / 2);
      if (indexRows[mid].target.getBoundingClientRect().top <= cutoff) low = mid + 1;
      else high = mid;
    }
    setIndexCurrent(indexRows[Math.max(0, low - 1)]);
  }

  function buildIndex() {
    var index = $("index");
    index.textContent = "";
    indexRows = [];
    activeIndexRow = null;
    var doc = $("doc-formatted");
    var sections = [];
    var section = { headings: [] };
    Array.prototype.forEach.call(doc.children, function (node) {
      if (node.classList.contains("page-break")) {
        if (section.page || section.headings.length) sections.push(section);
        section = { page: node, headings: [] };
      } else if (/^H[1-6]$/.test(node.tagName) && node.textContent.trim()) {
        section.headings.push(node);
      }
    });
    sections.push(section);
    if (sections.length === 1 && !section.headings.length) return;

    var label = document.createElement("div");
    label.className = "lab";
    label.dataset.i18n = "index";
    index.appendChild(label);
    function addRow(target, heading, number, sub) {
      var button = document.createElement("button");
      button.type = "button";
      if (sub) button.className = "sub";
      if (number) {
        var num = document.createElement("span");
        num.className = "num";
        num.textContent = number;
        button.appendChild(num);
      }
      var caption = document.createElement("span");
      caption.dir = "auto";
      caption.textContent = heading ? heading.textContent : target.textContent;
      button.appendChild(caption);
      var row = { target: target, button: button, label: caption, pageLabel: !heading };
      button.addEventListener("click", function () {
        var reader = $("reader");
        reader.scrollTop += target.getBoundingClientRect().top - reader.getBoundingClientRect().top - 22;
        setIndexCurrent(row);
      });
      indexRows.push(row);
      index.appendChild(button);
    }
    sections.forEach(function (part) {
      var headings = part.headings;
      if (part.page) addRow(part.page, headings[0], headings.length ? part.page.dataset.n : "", false);
      headings.slice(part.page ? 1 : 0).forEach(function (heading) {
        addRow(heading, heading, "", Boolean(part.page));
      });
    });
  }

  function setView(name) {
    view = name;
    document.querySelectorAll("[data-view]").forEach(function (b) {
      b.setAttribute("aria-selected", String(b.dataset.view === name));
    });
    $("doc-formatted").hidden = name !== "formatted";
    $("doc-text").hidden = name !== "text";
    $("doc-markdown").hidden = name !== "markdown";
    $("reader").scrollTop = 0;
    var hasIndex = name === "formatted" && indexRows.length > 0;
    $("index").hidden = !hasIndex;
    $("result-split").classList.toggle("has-index", hasIndex);
    if (hasIndex) setIndexCurrent(indexRows[0]);
  }

  function render(r) {
    current = r;
    $("result-name").textContent = $("work-name").textContent;
    ["doc-formatted", "doc-text", "doc-markdown"].forEach(function (id) { $(id).dir = r.direction || "auto"; });
    $("doc-formatted").innerHTML = r.html; // built by Python from the record, every text escaped
    if (r.ocr_blocks || (r.routes && r.routes.ocr)) {
      var caution = document.createElement("p");
      caution.className = "note";
      caution.dir = "auto";
      caution.dataset.i18n = "ocr_note";
      $("doc-formatted").prepend(caution);
    }
    $("doc-text").textContent = r.text;
    $("doc-markdown").textContent = r.markdown;
    // Save offers what the installed heocr can write: Word first when it can.
    var formats = r.formats || ["txt", "md", "json"];
    document.querySelectorAll("[data-save]").forEach(function (b) { b.hidden = formats.indexOf(b.getAttribute("data-save")) < 0; });
    buildIndex();
    applyLanguage(); // fills the page and section labels inside the document
    show("result");
    setView("formatted");
  }

  var messages = {
    needs_converter: { title: "m_unsupported_t", mark: "converter", body: "needs_converter" },
    unreadable: { title: "m_damaged_t", mark: "warning", body: "unreadable" },
    error: { title: "m_damaged_t", mark: "warning", body: "error" },
    empty: { title: "m_empty_t", mark: "image", body: "empty", hint: "m_empty_hint" },
    cancelled: { title: "m_cancelled_t", mark: "stopped", body: "nothing_saved", retry: true }
  };

  function localizeMessage() {
    var state = currentMessage.state;
    var progress = currentMessage.progress;
    $("message-title").textContent = t(state.title);
    $("message-text").textContent = progress ? t("m_cancelled_b", progress) : t(state.body);
    $("message-hint").textContent = state.hint ? t(state.hint) : "";
  }

  function message(kind, stopped) {
    current = null;
    var state = messages[kind] || messages.unreadable;
    currentMessage = { state: state, progress: stopped && stopped.total && stopped.done > 0 ? stopped : null };
    $("message-name").textContent = $("work-name").textContent;
    document.querySelectorAll("[data-message-mark]").forEach(function (icon) {
      icon.toggleAttribute("hidden", icon.dataset.messageMark !== state.mark);
    });
    $("message-hint").hidden = !state.hint;
    $("message-retry").hidden = !state.retry;
    $("message-again").classList.toggle("primary", !state.retry);
    localizeMessage();
    show("message");
    $("message-title").focus();
  }

  function showElapsed() {
    var seconds = Math.floor((Date.now() - readingStarted) / 1000);
    $("work-elapsed").textContent = Math.floor(seconds / 60) + ":" + String(seconds % 60).padStart(2, "0");
  }

  function showProgress(p) {
    var status = "reading";
    var total = p && p.total > 0 ? p.total : 0;
    if (p && p.stage === "pages") status = total ? "page_of" : "page_n_progress";
    if (p && p.stage === "finishing") status = "finishing";
    var label = t(status, p && { done: total ? Math.min(p.done + 1, total) : p.done + 1, total: total });
    if ($("work-status").textContent !== label) $("work-status").textContent = label;
    var type = $("work-name").textContent.match(/\.([^.]+)$/);
    var meta = type ? type[1].toUpperCase() : "";
    if (total) meta += (meta ? " · " : "") + (total === 1 ? t("page") : t("pages", { n: total }));
    $("work-meta").textContent = meta;
    // Fit long PDFs into one row while preserving individual segments for short readings.
    var count = Math.min(total || 1, 60);
    var done = status === "finishing" ? count : total ? Math.floor(p.done * count / total) : 0;
    var meter = $("meter");
    if (total) {
      meter.setAttribute("aria-valuemin", "0");
      meter.setAttribute("aria-valuemax", String(total));
      meter.setAttribute("aria-valuenow", String(p.done));
      meter.setAttribute("aria-valuetext", label);
    } else {
      ["aria-valuemin", "aria-valuemax", "aria-valuenow", "aria-valuetext"].forEach(function (attr) {
        meter.removeAttribute(attr);
      });
    }
    while (meter.childElementCount > count) meter.lastElementChild.remove();
    while (meter.childElementCount < count) meter.appendChild(document.createElement("i"));
    Array.prototype.forEach.call(meter.children, function (segment, i) {
      segment.className = i < done ? "done" : i === Math.min(done, count - 1) ? "now" : "";
    });
  }

  // -- called by Python ------------------------------------------------------------------
  window.heocr = {
    started: function (p) {
      readingId++;
      working = true;
      current = null;
      currentMessage = null;
      progress = null;
      $("work-name").textContent = p.name;
      readingStarted = Date.now();
      clearInterval(elapsedTimer);
      elapsedTimer = setInterval(showElapsed, 1000);
      showElapsed();
      showProgress(null);
      show("reading");
      $("cancel").focus();
    },
    progress: function (p) {
      progress = p;
      showProgress(p);
    },
    finished: function (p) {
      working = false;
      clearInterval(elapsedTimer);
      if (p.kind !== "ok") { message(p.kind, p.kind === "cancelled" ? p : null); return; }
      var finishedId = readingId;
      api().result().then(function (result) {
        if (readingId === finishedId && result.kind === "ok") render(result);
      });
    },
    dropFailed: function () { if (!working) message("unreadable"); }
  };

  // -- user actions ----------------------------------------------------------------------
  function copyText(text) {
    var done = function () { toast(t("copied")); };
    var fallback = function () {
      var area = document.createElement("textarea");
      area.value = text;
      area.setAttribute("readonly", "");
      area.style.position = "fixed";
      area.style.opacity = "0";
      document.body.appendChild(area);
      area.select();
      try { document.execCommand("copy"); done(); } finally { document.body.removeChild(area); }
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(done, fallback);
    } else {
      fallback();
    }
  }

  function availableFormats() {
    return Array.from($("save-menu").querySelectorAll("[data-save]:not([hidden])"));
  }

  function setSaveMenu(open, returnFocus) {
    document.body.classList.toggle("menu-open", open);
    $("save").setAttribute("aria-expanded", String(open));
    if (open) {
      var first = availableFormats()[0];
      if (first) first.focus();
    } else if (returnFocus) {
      $("save").focus();
    }
  }

  function closeFile() {
    if (working || (!current && !currentMessage)) return;
    current = null;
    currentMessage = null;
    show("start");
    $("open").focus();
  }

  function openFile() {
    if (!working && api()) api().open_file();
  }

  function saveFile(format) {
    if (!current || !api()) return;
    var result = current;
    api().save(format).then(function (saved) {
      if (saved && current === result) toast(t("saved"), saved);
    });
  }

  function copyAll() {
    if (current) copyText(view === "markdown" ? current.markdown : current.text);
  }

  function selectAll() {
    var selection = window.getSelection();
    var range = document.createRange();
    var doc = $("doc-" + view);
    $("reader").focus({ preventScroll: true });
    range.selectNodeContents(doc);
    selection.removeAllRanges();
    selection.addRange(range);
  }

  function openAbout() {
    var dialog = $("about");
    if (dialog.open) return;
    var pre = $("third-party");
    if (!pre.textContent && api()) api().third_party().then(function (s) { pre.textContent = s; });
    dialog.showModal();
    document.body.classList.add("about-open");
  }

  function setZoom(tenths) {
    if (!current) return;
    zoom = Math.max(8, Math.min(20, tenths));
    $("reader").style.setProperty("--doc-zoom", String(zoom / 10));
    $("zoom-value").textContent = zoom * 10 + "%";
    $("zoom-out").disabled = zoom === 8;
    $("zoom-in").disabled = zoom === 20;
    updateIndexCurrent();
  }

  function openProjectLink(link) {
    if (api()) api().open_project_link(link);
  }

  // Native menus and keyboard shortcuts share the web view's screen guards.
  var actions = {
    open: openFile,
    close: closeFile,
    save: function () {
      var first = availableFormats()[0];
      if (current && first) {
        setSaveMenu(false);
        saveFile(first.dataset.save);
      }
    },
    saveAs: function () { if (current) setSaveMenu(true); },
    copy: function () {
      var selected = window.getSelection().toString();
      if (selected) copyText(selected);
    },
    copyAll: copyAll,
    selectAll: function () { if (current) selectAll(); },
    formatted: function () { if (current) setView("formatted"); },
    text: function () { if (current) setView("text"); },
    markdown: function () { if (current) setView("markdown"); },
    larger: function () { setZoom(zoom + 1); },
    smaller: function () { setZoom(zoom - 1); },
    actual: function () { setZoom(10); },
    language: function () { $("lang").click(); },
    website: function () { openProjectLink("website"); },
    github: function () { openProjectLink("github"); },
    about: openAbout
  };

  window.heocr.action = function (name) {
    if (!$("about").open && Object.prototype.hasOwnProperty.call(actions, name)) actions[name]();
  };

  var mac = BOOT.platform === "darwin";
  function setShortcutTitles() {
    var mod = mac ? "⌘" : "Ctrl+";
    var shift = mac ? "⇧" : "Shift+";
    function title(id, key, shortcut) {
      $(id).title = t(key) + " (" + shortcut + ")";
    }
    title("open", "open", mod + "O");
    title("again", "open", mod + "O");
    title("copy", "copy_all", (mac ? shift + mod : mod + shift) + "C");
    title("save", "save", mod + "S");
    title("zoom-in", "zoom_in", mod + "+");
    title("zoom-out", "zoom_out", mod + "−");
    title("cancel", "cancel", "Esc");
    title("about-close", "close", "Esc");
    document.querySelectorAll("[data-view]").forEach(function (button, i) {
      button.title = button.textContent + " (" + mod + (i + 1) + ")";
    });
  }

  function keyboard(event) {
    if (event.isComposing || $("about").open) return;
    var menuOpen = document.body.classList.contains("menu-open");
    if (event.key === "Escape") {
      if (menuOpen) setSaveMenu(false, true);
      else if (working && api()) api().cancel();
      else return;
      event.preventDefault();
      return;
    }
    if (event.key === "ArrowDown" && event.target === $("save") && !menuOpen) {
      event.preventDefault();
      setSaveMenu(true);
      return;
    }
    if (menuOpen && $("save-menu").contains(event.target)) {
      var buttons = availableFormats();
      var index = buttons.indexOf(event.target);
      var next = {
        ArrowDown: (index + 1) % buttons.length,
        ArrowUp: (index + buttons.length - 1) % buttons.length,
        Home: 0,
        End: buttons.length - 1
      }[event.key];
      if (next !== undefined) {
        event.preventDefault();
        buttons[next].focus();
        return;
      }
      if (event.key === "Tab") setSaveMenu(false, true);
    }
    var modifier = mac ? event.metaKey && !event.ctrlKey : event.ctrlKey && !event.metaKey;
    if (!modifier || event.altKey) return;
    var key = event.key.toLowerCase();
    var zoomShortcut = { "+": "larger", "=": "larger", "-": "smaller", "−": "smaller", "0": "actual" }[key];
    var shortcut = zoomShortcut || (event.shiftKey ? { s: "saveAs", c: "copyAll" }[key] :
      { o: "open", s: "save", w: "close", a: "selectAll", "1": "formatted", "2": "text", "3": "markdown" }[key]);
    // The web view handles the system copy shortcut and keeps the selection's logical order.
    if (shortcut) {
      event.preventDefault();
      if (!event.repeat) window.heocr.action(shortcut);
    }
  }

  function bind() {
    $("reader").addEventListener("scroll", updateIndexCurrent, { passive: true });
    $("zoom-in").addEventListener("click", actions.larger);
    $("zoom-out").addEventListener("click", actions.smaller);
    $("open").addEventListener("click", openFile);
    $("again").addEventListener("click", openFile);
    $("message-again").addEventListener("click", openFile);
    $("message-retry").addEventListener("click", function () {
      if (!working && api()) api().retry();
    });
    $("cancel").addEventListener("click", function () { if (api()) api().cancel(); });
    $("copy").addEventListener("click", copyAll);
    $("save").addEventListener("click", function () {
      setSaveMenu($("save").getAttribute("aria-expanded") !== "true");
    });
    document.addEventListener("click", function (event) {
      if (!event.target.closest(".menuwrap")) setSaveMenu(false);
    });
    document.addEventListener("focusin", function (event) {
      if (!event.target.closest(".menuwrap")) setSaveMenu(false);
    });
    document.addEventListener("keydown", keyboard);
    document.querySelectorAll("[data-save]").forEach(function (b) {
      b.addEventListener("click", function () {
        setSaveMenu(false, true);
        saveFile(b.dataset.save);
      });
    });
    document.querySelectorAll("[data-view]").forEach(function (b) {
      b.addEventListener("click", function () { setView(b.dataset.view); });
    });
    $("lang").addEventListener("click", function () {
      lang = lang === "he" ? "en" : "he";
      applyLanguage();
      if (api()) api().set_language(lang);
    });
    $("about-open").addEventListener("click", openAbout);
    document.querySelectorAll("[data-project-link]").forEach(function (button) {
      button.addEventListener("click", function () { openProjectLink(button.dataset.projectLink); });
    });
    $("about-close").addEventListener("click", function () { $("about").close(); });
    $("about").addEventListener("close", function () { document.body.classList.remove("about-open"); });
    // The web view paints the veil; the native drop handler receives the full path.
    var depth = 0;
    function isFileDrag(event) {
      return event.dataTransfer && Array.from(event.dataTransfer.types).includes("Files");
    }
    function showDropVeil(visible) {
      document.body.classList.toggle("is-dragging", visible);
    }
    function clearDropVeil() {
      depth = 0;
      showDropVeil(false);
    }
    window.addEventListener("dragenter", function (event) {
      if (!isFileDrag(event)) return;
      event.preventDefault();
      depth++;
      showDropVeil(true);
    }, true);
    window.addEventListener("dragover", function (event) {
      // Keep links and files from navigating the app's single local page.
      event.preventDefault();
      if (isFileDrag(event)) showDropVeil(true);
    }, true);
    window.addEventListener("dragleave", function () {
      depth = Math.max(0, depth - 1);
      if (!depth) clearDropVeil();
    }, true);
    window.addEventListener("drop", function (event) {
      event.preventDefault();
      clearDropVeil();
    }, true);
    window.addEventListener("blur", clearDropVeil);
  }

  (BOOT.models || []).forEach(function (model) {
    var row = document.createElement("div");
    var label = document.createElement("span");
    label.dir = "ltr";
    label.textContent = model.name + (model.origin ? " · " + model.origin : "");
    var licence = document.createElement("span");
    licence.className = "end ltr";
    licence.textContent = model.licence;
    row.append(label, licence);
    $("models").appendChild(row);
  });
  applyLanguage();
  bind();
})();
