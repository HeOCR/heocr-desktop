(function () {
  "use strict";
  var BOOT = window.HEOCR_BOOT || { language: "en", strings: { en: {} } };
  var lang = BOOT.language in BOOT.strings ? BOOT.language : "en";
  var current = null; // the last result
  var view = "formatted";
  var working = false;
  var readingStarted;
  var elapsedTimer;
  var progress = null;
  var messageKey;
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
    if (messageKey) $("message-text").textContent = t(messageKey);
    $("about-version").textContent = t("version", { v: BOOT.version, h: BOOT.heocr, t: BOOT.tesseract });
    if (current) showChips(current);
  }

  function show(name) {
    setSaveMenu(false);
    ["start", "reading", "result", "message"].forEach(function (v) {
      $("view-" + v).classList.toggle("active", v === name);
    });
  }

  var toastTimer = null;
  function toast(text) {
    var el = $("toast");
    el.textContent = text;
    el.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { el.classList.remove("show"); }, 1600);
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
    function note(text) { var d = document.createElement("div"); d.className = "notice"; d.textContent = text; notes.appendChild(d); }
    if (!r.ocr_available) note(t("no_ocr"));
    (r.notes || []).forEach(function (n) { note(t("note_" + n)); });
    if (r.unread) note(r.unread === 1 ? t("unread_1") : t("unread_n", { n: r.unread }));
    notes.hidden = !notes.childElementCount;
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
  }

  function render(r) {
    current = r;
    $("result-name").textContent = $("work-name").textContent;
    ["doc-formatted", "doc-text", "doc-markdown"].forEach(function (id) { $(id).dir = r.direction || "auto"; });
    $("doc-formatted").innerHTML = r.html; // built by Python from the record, every text escaped
    if (r.ocr_blocks) {
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
    applyLanguage(); // fills the page and section labels inside the document
    setView("formatted");
    show("result");
  }

  function message(key) {
    messageKey = key;
    $("message-name").textContent = $("work-name").textContent;
    $("message-text").textContent = t(key);
    show("message");
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
    $("work-status").textContent = t(status, p && { done: total ? Math.min(p.done + 1, total) : p.done + 1, total: total });
    var type = $("work-name").textContent.match(/\.([^.]+)$/);
    var meta = type ? type[1].toUpperCase() : "";
    if (total) meta += (meta ? " · " : "") + (total === 1 ? t("page") : t("pages", { n: total }));
    $("work-meta").textContent = meta;
    // Fit long PDFs into one row while preserving individual segments for short readings.
    var count = Math.min(total || 1, 60);
    var done = status === "finishing" ? count : total ? Math.floor(p.done * count / total) : 0;
    var meter = $("meter");
    while (meter.childElementCount > count) meter.lastElementChild.remove();
    while (meter.childElementCount < count) meter.appendChild(document.createElement("i"));
    Array.prototype.forEach.call(meter.children, function (segment, i) {
      segment.className = i < done ? "done" : i === Math.min(done, count - 1) ? "now" : "";
    });
  }

  // -- called by Python ------------------------------------------------------------------
  window.heocr = {
    started: function (p) {
      working = true;
      current = null;
      messageKey = null;
      progress = null;
      $("work-name").textContent = p.name;
      readingStarted = Date.now();
      clearInterval(elapsedTimer);
      elapsedTimer = setInterval(showElapsed, 1000);
      showElapsed();
      showProgress(null);
      show("reading");
    },
    progress: function (p) {
      progress = p;
      showProgress(p);
    },
    finished: function (p) {
      working = false;
      clearInterval(elapsedTimer);
      if (p.kind === "cancelled") { show("start"); toast(t("cancelled")); return; }
      if (p.kind === "error") { message("error"); return; }
      if (p.kind !== "ok") { message(p.kind); return; }
      api().result().then(render);
    },
    dropFailed: function () { message("unreadable"); }
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

  function setSaveMenu(open, returnFocus) {
    document.body.classList.toggle("menu-open", open);
    $("save").setAttribute("aria-expanded", String(open));
    if (open) {
      var first = $("save-menu").querySelector("button:not([hidden])");
      if (first) first.focus();
    } else if (returnFocus) {
      $("save").focus();
    }
  }

  function bind() {
    $("open").addEventListener("click", function () { if (!working && api()) api().open_file(); });
    $("again").addEventListener("click", function () { show("start"); });
    $("message-again").addEventListener("click", function () {
      if (!working && api()) api().open_file();
    });
    $("cancel").addEventListener("click", function () { if (api()) api().cancel(); });
    $("copy").addEventListener("click", function () {
      if (!current) return;
      copyText(view === "markdown" ? current.markdown : current.text);
    });
    $("save").addEventListener("click", function () {
      setSaveMenu($("save").getAttribute("aria-expanded") !== "true");
    });
    document.addEventListener("click", function (event) {
      if (!event.target.closest(".menuwrap")) setSaveMenu(false);
    });
    $("save-menu").addEventListener("keydown", function (event) {
      if (event.key === "Escape") setSaveMenu(false, true);
    });
    document.querySelectorAll("[data-save]").forEach(function (b) {
      b.addEventListener("click", function () {
        setSaveMenu(false, true);
        if (api()) api().save(b.dataset.save).then(function (name) {
          if (name) toast(t("saved") + ": " + name);
        });
      });
    });
    document.querySelectorAll("[data-view]").forEach(function (b) {
      b.addEventListener("click", function () { setView(b.getAttribute("data-view")); });
    });
    $("lang").addEventListener("click", function () {
      lang = lang === "he" ? "en" : "he";
      applyLanguage();
      if (api()) api().set_language(lang);
    });
    $("about-open").addEventListener("click", function () {
      var pre = $("third-party");
      if (!pre.textContent && api()) api().third_party().then(function (s) { pre.textContent = s; });
      $("about").showModal();
    });
    $("about-close").addEventListener("click", function () { $("about").close(); });
    // Drag feedback only; Python receives the drop itself (with the file's full path).
    var depth = 0;
    document.addEventListener("dragenter", function (e) { e.preventDefault(); depth++; document.body.classList.add("dragging"); });
    document.addEventListener("dragleave", function () { depth = Math.max(0, depth - 1); if (!depth) document.body.classList.remove("dragging"); });
    document.addEventListener("dragover", function (e) { e.preventDefault(); });
    document.addEventListener("drop", function (e) { e.preventDefault(); depth = 0; document.body.classList.remove("dragging"); });
  }

  (BOOT.models || []).forEach(function (m) {
    var li = document.createElement("div");
    li.dir = "ltr";
    li.textContent = m.name + " — " + m.origin + " — sha256 " + m.sha256;
    $("models").appendChild(li);
  });
  applyLanguage();
  bind();
})();
