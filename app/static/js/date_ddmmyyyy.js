// static/js/date_ddmmyyyy.js
// Fecha manual DD/MM/AAAA + selector de calendario nativo (ícono a la derecha).

(function () {
  function onlyDigits(s) {
    return (s || "").replace(/\D/g, "");
  }

  function formatDigits(digits) {
    var d = (digits || "").slice(0, 8); // DDMMAAAA
    if (d.length <= 2) return d;
    if (d.length <= 4) return d.slice(0, 2) + "/" + d.slice(2);
    return d.slice(0, 2) + "/" + d.slice(2, 4) + "/" + d.slice(4);
  }

  function cursorPosFromDigitsCount(n) {
    if (n <= 2) return n;
    if (n <= 4) return n + 1;
    return n + 2;
  }

  function normalize(value) {
    var v = (value || "").trim();
    if (!v) return { value: "", valid: true };

    var digits = onlyDigits(v);
    if (digits.length !== 8) {
      return { value: formatDigits(digits), valid: false };
    }

    v = formatDigits(digits);

    if (!/^(0[1-9]|[12][0-9]|3[01])\/(0[1-9]|1[0-2])\/\d{4}$/.test(v)) {
      return { value: v, valid: false };
    }

    var parts = v.split("/");
    var d = parseInt(parts[0], 10);
    var mo = parseInt(parts[1], 10);
    var y = parseInt(parts[2], 10);

    var dt = new Date(y, mo - 1, d);
    var ok = dt.getFullYear() === y && dt.getMonth() === (mo - 1) && dt.getDate() === d;
    return { value: v, valid: ok };
  }

  // DD/MM/AAAA -> YYYY-MM-DD (para precargar el <input type="date">)
  function toISO(ddmmaaaa) {
    var m = (ddmmaaaa || "").match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
    if (!m) return "";
    return m[3] + "-" + m[2] + "-" + m[1];
  }

  // YYYY-MM-DD -> DD/MM/AAAA (al elegir fecha en el calendario nativo)
  function fromISO(isoValue) {
    var m = (isoValue || "").match(/^(\d{4})-(\d{2})-(\d{2})$/);
    if (!m) return "";
    return m[3] + "/" + m[2] + "/" + m[1];
  }

  function lockToNumbers(inp) {
    inp.addEventListener("keydown", function (e) {
      var k = e.key;
      if (e.ctrlKey || e.metaKey) return;

      var allowed = [
        "Backspace", "Delete", "Tab", "Enter", "Escape",
        "ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown",
        "Home", "End"
      ];
      if (allowed.indexOf(k) >= 0) return;
      if (/^\d$/.test(k)) return;
      if (k === "/" || k === "-") return;

      e.preventDefault();
    });

    inp.addEventListener("input", function () {
      var raw = inp.value || "";
      var pos = inp.selectionStart != null ? inp.selectionStart : raw.length;

      var digitsBeforeCursor = onlyDigits(raw.slice(0, pos)).length;
      var digits = onlyDigits(raw);

      var formatted = formatDigits(digits);
      inp.value = formatted;

      var newPos = cursorPosFromDigitsCount(digitsBeforeCursor);
      newPos = Math.max(0, Math.min(formatted.length, newPos));
      try {
        inp.setSelectionRange(newPos, newPos);
      } catch (err) {}

      inp.setCustomValidity("");
    });
  }

  // Envuelve el input con .datewrap + ícono + <input type="date"> oculto
  function attachCalendarPicker(inp) {
    if (inp.dataset.somaCalendarInit === "1") return;
    inp.dataset.somaCalendarInit = "1";

    var wrap = document.createElement("span");
    wrap.className = "datewrap";
    inp.parentNode.insertBefore(wrap, inp);
    wrap.appendChild(inp);

    var icon = document.createElement("span");
    icon.className = "date-icon";
    icon.innerHTML =
      '<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">' +
      '<rect x="3" y="5" width="18" height="16" rx="2" stroke="currentColor" stroke-width="2"/>' +
      '<path d="M3 9h18M8 3v4M16 3v4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>' +
      '</svg>';
    wrap.appendChild(icon);

    var native = document.createElement("input");
    native.type = "date";
    native.className = "date-native";
    native.tabIndex = -1;
    wrap.appendChild(native);

    native.addEventListener("focus", function () {
      var iso = toISO(inp.value);
      if (iso) native.value = iso;
      if (native.showPicker) {
        try { native.showPicker(); } catch (err) {}
      }
    });

    native.addEventListener("change", function () {
      var formatted = fromISO(native.value);
      if (formatted) {
        inp.value = formatted;
        inp.setCustomValidity("");
      }
    });
  }

  function initInput(inp) {
    if (!inp || inp.dataset.somaDateInit === "1") return;
    inp.dataset.somaDateInit = "1";

    lockToNumbers(inp);
    attachCalendarPicker(inp);

    inp.addEventListener("blur", function () {
      var r = normalize(inp.value);
      inp.value = r.value;
      inp.setCustomValidity(r.valid ? "" : "Fecha inválida. Usa DD/MM/AAAA.");
    });
  }

  function initAll(root) {
    var scope = root || document;
    var inputs = scope.querySelectorAll("input.date-manual");
    inputs.forEach(initInput);
  }

  function attachFormValidation() {
    document.querySelectorAll("form").forEach(function (form) {
      if (form.dataset.somaDateForm === "1") return;
      form.dataset.somaDateForm = "1";

      form.addEventListener("submit", function (e) {
        var firstInvalid = null;
        form.querySelectorAll("input.date-manual").forEach(function (inp) {
          var r = normalize(inp.value);
          inp.value = r.value;
          if (!r.valid) {
            inp.setCustomValidity("Fecha inválida. Usa DD/MM/AAAA.");
            if (!firstInvalid) firstInvalid = inp;
          } else {
            inp.setCustomValidity("");
          }
        });

        if (firstInvalid) {
          e.preventDefault();
          firstInvalid.reportValidity();
          firstInvalid.focus();
        }
      });
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    initAll(document);
    attachFormValidation();

    window.SOMA_initDateWraps = initAll;
    window.SOMA_initDateInputs = initAll;
  });
})();