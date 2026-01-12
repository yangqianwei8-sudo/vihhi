// list_filters.js
// 通用：从 URL 初始化筛选控件；控件变化后写回 URL 并刷新；支持 reset；可配置默认值/参数白名单

(function (global) {
  function parseBoolParam(qs, key, defaultVal) {
    const v = qs.get(key);
    if (v === null) return defaultVal;
    return v === "1" || v === "true";
  }

  function setBoolParam(qs, key, checked) {
    if (checked) qs.set(key, "1");
    else qs.delete(key);
  }

  function initListFilters(options) {
    const {
      // switches: [{ id: "filterMine", param: "mine", default: true }, ...]
      switches = [],
      // checkbox:  [{ id: "filterOverdue", param: "overdue", default: false }, ...]
      checkboxes = [],
      // radios: { name: "range", param: "range", default: "" }
      radios = null,
      // reset button id
      resetId = "resetFiltersBtn",
      // when applying filters, delete page param
      resetPageParam = true,
      // additional params to clear when reset
      resetParams = [],
    } = options || {};

    const qs = new URLSearchParams(window.location.search);

    // init switches
    switches.forEach(sw => {
      const el = document.getElementById(sw.id);
      if (!el) return;
      el.checked = parseBoolParam(qs, sw.param, sw.default ?? false);
    });

    // init checkboxes
    checkboxes.forEach(cb => {
      const el = document.getElementById(cb.id);
      if (!el) return;
      el.checked = parseBoolParam(qs, cb.param, cb.default ?? false);
    });

    // init radios
    if (radios && radios.name && radios.param) {
      const v = qs.get(radios.param) ?? (radios.default ?? "");
      const target = document.querySelector(`input[name="${radios.name}"][value="${v}"]`)
        || document.querySelector(`input[name="${radios.name}"][value=""]`);
      if (target) target.checked = true;
    }

    function apply() {
      const p = new URLSearchParams(window.location.search);

      switches.forEach(sw => {
        const el = document.getElementById(sw.id);
        if (!el) return;
        setBoolParam(p, sw.param, el.checked);
      });

      checkboxes.forEach(cb => {
        const el = document.getElementById(cb.id);
        if (!el) return;
        setBoolParam(p, cb.param, el.checked);
      });

      if (radios && radios.name && radios.param) {
        const r = document.querySelector(`input[name="${radios.name}"]:checked`)?.value ?? "";
        if (r) p.set(radios.param, r);
        else p.delete(radios.param);
      }

      if (resetPageParam) p.delete("page");
      window.location.search = p.toString();
    }

    // bind listeners
    switches.forEach(sw => {
      const el = document.getElementById(sw.id);
      if (el) el.addEventListener("change", apply);
    });

    checkboxes.forEach(cb => {
      const el = document.getElementById(cb.id);
      if (el) el.addEventListener("change", apply);
    });

    if (radios && radios.name) {
      document.querySelectorAll(`input[name="${radios.name}"]`).forEach(el => {
        el.addEventListener("change", apply);
      });
    }

    const resetBtn = document.getElementById(resetId);
    if (resetBtn) {
      resetBtn.addEventListener("click", function () {
        const p = new URLSearchParams(window.location.search);

        switches.forEach(sw => p.delete(sw.param));
        checkboxes.forEach(cb => p.delete(cb.param));
        if (radios && radios.param) p.delete(radios.param);

        if (resetPageParam) p.delete("page");
        (resetParams || []).forEach(k => p.delete(k));

        window.location.search = p.toString();
      });
    }
  }

  global.initListFilters = initListFilters;
})(window);

