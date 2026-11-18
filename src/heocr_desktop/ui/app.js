(function () {
  "use strict";
  var BOOT = window.HEOCR_BOOT || { language: "en", strings: { en: {} } };
  var lang = BOOT.language in BOOT.strings ? BOOT.language : "en";
  var current = null; // the last result
  var view = "formatted";
  var working = false;

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
    $("about-version").textContent = t("version", { v: BOOT.version, h: BOOT.heocr, t: BOOT.tesseract });
    if (current) showChips(current);
  }

  function show(name) {
    ["drop", "work", "result", "message"].forEach(function (v) {
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

  function chip(text, cls) {
    var el = document.createElement("span");
    el.className = "chip" + (cls ? " " + cls : "");
    el.textContent = text;
    return el;
  }

  function showChips(r) {
    var box = $("chips");
    box.textContent = "";
    if (r.pages) box.appendChild(chip(r.pages === 1 ? t("page") : t("pages", { n: r.pages })));
    var routes = r.routes || {};
    var names = { text_layer: "route_text_layer", ocr: "route_ocr", none: "route_none" };
    var shown = false;
    Object.keys(routes).forEach(function (k) {
      var label = names[k] ? t(names[k]) : k;
      // The page count only when there is more than one page: "OCR (12)".
      box.appendChild(chip(t("route") + ": " + label + (r.pages > 1 ? " (" + routes[k] + ")" : ""), "route"));
      shown = true;
    });
    if (!shown) {
      var sources = r.sources || {};
      var office = Object.keys(sources).some(function (s) { return s !== "ocr"; });
      if (office) box.appendChild(chip(t("route") + ": " + t("route_office"), "route"));
      if (sources.ocr) box.appendChild(chip(t("route") + ": " + t("route_ocr"), "route"));
    }
    box.appendChild(chip(t("seconds", { s: r.seconds })));
    var notes = $("notes");
    notes.textContent = "";
    function note(text) { var d = document.createElement("div"); d.className = "note"; d.textContent = text; notes.appendChild(d); }
    if (r.ocr_blocks) note(t("ocr_note"));
    if (!r.ocr_available) note(t("no_ocr"));
    (r.notes || []).forEach(function (n) { note(t("note_" + n)); });
    if (r.unread) note(r.unread === 1 ? t("unread_1") : t("unread_n", { n: r.unread }));
  }

  function setView(name) {
    view = name;
    document.querySelectorAll(".tab").forEach(function (b) { b.classList.toggle("active", b.getAttribute("data-view") === name); });
    $("doc-formatted").hidden = name !== "formatted";
    $("doc-text").hidden = name !== "text";
    $("doc-markdown").hidden = name !== "markdown";
  }

  function render(r) {
    current = r;
    $("result-name").textContent = $("work-name").textContent;
    ["doc-formatted", "doc-text", "doc-markdown"].forEach(function (id) { $(id).dir = r.direction || "auto"; });
    $("doc-formatted").innerHTML = r.html; // built by Python from the record, every text escaped
    $("doc-text").textContent = r.text;
    $("doc-markdown").textContent = r.markdown;
    applyLanguage(); // fills the page and section labels inside the document
    setView("formatted");
    show("result");
    $("doc-formatted").scrollTop = 0;
  }

  function message(key) {
    $("message-name").textContent = $("work-name").textContent;
    $("message-text").textContent = t(key);
    show("message");
  }

  // -- called by Python ------------------------------------------------------------------
  window.heocr = {
    started: function (p) {
      working = true;
      current = null;
      $("work-name").textContent = p.name;
      $("meter").style.width = "0";
      $("meter").parentNode.classList.add("indeterminate");
      $("work-status").textContent = t("reading");
      show("work");
    },
    progress: function (p) {
      var meter = $("meter");
      if (p.stage === "pages" && p.total) {
        meter.parentNode.classList.remove("indeterminate");
        meter.style.width = Math.max(2, Math.round(100 * p.done / p.total)) + "%";
        $("work-status").textContent = t("page_of", { done: Math.min(p.done + 1, p.total), total: p.total });
      } else if (p.stage === "pages") {
        $("work-status").textContent = t("page_n_progress", { done: p.done + 1 });
      } else if (p.stage === "finishing") {
        meter.parentNode.classList.remove("indeterminate");
        meter.style.width = "100%";
        $("work-status").textContent = t("finishing");
      }
    },
    finished: function (p) {
      working = false;
      if (p.kind === "cancelled") { show("drop"); toast(t("cancelled")); return; }
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

  function bind() {
    $("open").addEventListener("click", function () { if (!working && api()) api().open_file(); });
    $("again").addEventListener("click", function () { show("drop"); });
    $("message-again").addEventListener("click", function () { show("drop"); });
    $("cancel").addEventListener("click", function () { if (api()) api().cancel(); });
    $("copy").addEventListener("click", function () {
      if (!current) return;
      copyText(view === "markdown" ? current.markdown : current.text);
    });
    document.querySelectorAll("[data-save]").forEach(function (b) {
      b.addEventListener("click", function () {
        api().save(b.getAttribute("data-save")).then(function (name) { if (name) toast(t("saved") + ": " + name); });
      });
    });
    document.querySelectorAll(".tab").forEach(function (b) {
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
    var li = document.createElement("li");
    li.textContent = m.name + " — " + m.origin + " — sha256 " + m.sha256;
    $("models").appendChild(li);
  });
  applyLanguage();
  bind();
})();
