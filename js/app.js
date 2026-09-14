/* 无人深空 · 营养摄入器 — 交互逻辑 */
(function () {
  "use strict";
  const NMS = window.NMS || { summary: {}, data: [] };
  const DATA = NMS.data || [];
  const TYPES = NMS.summary && NMS.summary.types ? NMS.summary.types : [...new Set(DATA.map(d => d.type))].sort();
  const EFFECTS = NMS.summary && NMS.summary.effects ? NMS.summary.effects : [...new Set(DATA.map(d => d.effect))].sort();

  // ---- DOM ----
  const $ = s => document.querySelector(s);
  const el = {
    statCount: $("#stat-count"), statTypes: $("#stat-types"), statEffects: $("#stat-effects"),
    tabs: document.querySelectorAll(".tab"),
    q: $("#q"), clear: $("#clear"),
    ftype: $("#ftype"), feffect: $("#feffect"), effctl: $("#effctl"),
    sort: $("#sort"),
    shown: $("#shown"), total: $("#total"), reset: $("#reset"),
    head: $("#head"), body: $("#body"), empty: $("#empty"),
  };

  // ---- state ----
  const state = { view: "recipe", q: "", type: "", effect: "", sort: "score", dir: "desc" };

  // ---- helpers ----
  const badgeClass = t => (t === "食用产品" || t === "鱼" || t === "原料") ? "b-" + t : "b-其他";
  const fmt = n => (Math.round(n)).toLocaleString("en-US");
  const timeStr = d => {
    const m = Math.floor(d.total / 60), s = d.total % 60;
    return m + ":" + String(s).padStart(2, "0");
  };
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

  // ---- columns per view ----
  const COLUMNS = {
    recipe: [
      { key: "idx", label: "#", sortable: false },
      { key: "name", label: "名称", sortable: true },
      { key: "type", label: "类型", sortable: true },
      { key: "time", label: "烹饪时间", sortable: true },
    ],
    effect: [
      { key: "idx", label: "#", sortable: false },
      { key: "name", label: "名称", sortable: true },
      { key: "effect", label: "效果", sortable: true },
      { key: "bonus", label: "加成", sortable: true, right: true },
      { key: "time", label: "持续时间", sortable: true, right: true },
      { key: "score", label: "综合分", sortable: true, right: true },
    ],
  };

  const SORT_LABEL = {
    recipe: { name: "按名称", time: "按烹饪时间", type: "按类型" },
    effect: { score: "综合分（默认）", bonus: "按加成", total: "按时长", name: "按名称" },
  };

  const SORT_GET = {
    name: d => d.zh,
    type: d => d.type + "\u0001" + d.zh,
    time: d => d.total,
    bonus: d => d.bonus,
    total: d => d.total,
    score: d => d.bonus_total,
  };

  // ---- init stats ----
  el.statCount.textContent = DATA.length;
  el.statTypes.textContent = TYPES.length;
  el.statEffects.textContent = EFFECTS.length;
  el.total.textContent = DATA.length;

  // ---- init filters ----
  TYPES.forEach(t => { const o = document.createElement("option"); o.value = t; o.textContent = t; el.ftype.appendChild(o); });
  EFFECTS.forEach(t => { const o = document.createElement("option"); o.value = t; o.textContent = t; el.feffect.appendChild(o); });

  function buildSortOptions() {
    const map = SORT_LABEL[state.view];
    el.sort.innerHTML = "";
    Object.entries(map).forEach(([val, label]) => {
      const o = document.createElement("option");
      o.value = val; o.textContent = label;
      if (val === state.sort) o.selected = true;
      el.sort.appendChild(o);
    });
  }

  // ---- view switching ----
  function setView(view) {
    state.view = view;
    state.effect = "";
    el.feffect.value = "";
    el.effctl.style.display = view === "effect" ? "flex" : "none";
    state.sort = view === "effect" ? "score" : "name";
    state.dir = view === "effect" ? "desc" : "asc";
    el.tabs.forEach(t => {
      const on = t.dataset.view === view;
      t.classList.toggle("active", on);
      t.setAttribute("aria-selected", on);
    });
    buildSortOptions();
    render();
  }

  // ---- filter + sort ----
  function currentList() {
    const q = state.q.trim().toLowerCase();
    let list = DATA.filter(d => {
      if (state.type && d.type !== state.type) return false;
      if (state.effect && d.effect !== state.effect) return false;
      if (q) {
        const hay = (d.zh + " " + d.en + " " + d.effect + " " + d.effect_en + " " + d.type).toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });
    const get = SORT_GET[state.sort] || SORT_GET.name;
    list.sort((a, b) => {
      let x = get(a), y = get(b);
      if (typeof x === "string") {
        const c = x.localeCompare(y, "zh-Hans-CN");
        return state.dir === "desc" ? -c : c;
      }
      return state.dir === "desc" ? y - x : x - y;
    });
    return list;
  }

  // ---- render ----
  function render() {
    const list = currentList();
    const cols = COLUMNS[state.view];
    // header
    el.head.innerHTML = cols.map(c => {
      const sorted = c.key === state.sort && c.sortable;
      const arr = sorted ? (state.dir === "desc" ? "↓" : "↑") : "";
      return `<th data-key="${c.key}" class="${sorted ? "sorted" : ""} ${c.right ? "num" : ""}">${esc(c.label)}<span class="arr">${arr}</span></th>`;
    }).join("");
    el.head.querySelectorAll("th").forEach(th => {
      if (th.dataset.key && th.dataset.key !== "idx") {
        th.addEventListener("click", () => toggleSort(th.dataset.key));
      }
    });
    // rows
    el.body.innerHTML = list.map((d, i) => {
      const c = i + 1;
      let cells = `<td class="idx">${c}</td>`;
      if (state.view === "recipe") {
        cells += `<td class="name-cell"><div class="zh">${esc(d.zh)}</div><div class="en">${esc(d.en)}</div></td>`;
        cells += `<td><span class="badge ${badgeClass(d.type)}">${esc(d.type)}</span></td>`;
        cells += `<td class="num time">${timeStr(d)}</td>`;
      } else {
        cells += `<td class="name-cell"><div class="zh">${esc(d.zh)}</div><div class="en">${esc(d.en)}</div></td>`;
        cells += `<td class="effect-cell"><div class="zh">${esc(d.effect)}</div><div class="en">${esc(d.effect_en)}</div></td>`;
        cells += `<td class="num">${fmt(d.bonus)}<span style="color:var(--muted2)">%</span></td>`;
        cells += `<td class="num time">${timeStr(d)}</td>`;
        cells += `<td class="num big">${fmt(d.bonus_total)}</td>`;
      }
      return `<tr>${cells}</tr>`;
    }).join("");
    el.shown.textContent = list.length;
    el.empty.hidden = list.length > 0;
  }

  function toggleSort(key) {
    if (key === "time") key = state.view === "recipe" ? "time" : "total";
    if (key === state.sort) {
      state.dir = state.dir === "desc" ? "asc" : "desc";
    } else {
      state.sort = key;
      state.dir = (key === "name" || key === "type") ? "asc" : "desc";
    }
    if (SORT_LABEL[state.view][state.sort]) { /* ok */ }
    el.sort.value = state.sort;
    render();
  }

  // ---- events ----
  el.tabs.forEach(t => t.addEventListener("click", () => setView(t.dataset.view)));
  el.q.addEventListener("input", () => {
    state.q = el.q.value;
    el.clear.classList.toggle("show", !!el.q.value);
    render();
  });
  el.clear.addEventListener("click", () => { el.q.value = ""; state.q = ""; el.clear.classList.remove("show"); el.q.focus(); render(); });
  el.ftype.addEventListener("change", () => { state.type = el.ftype.value; render(); });
  el.feffect.addEventListener("change", () => { state.effect = el.feffect.value; render(); });
  el.sort.addEventListener("change", () => {
    state.sort = el.sort.value;
    state.dir = (state.sort === "name" || state.sort === "type") ? "asc" : "desc";
    render();
  });
  el.reset.addEventListener("click", () => {
    state.q = ""; state.type = ""; state.effect = "";
    el.q.value = ""; el.ftype.value = ""; el.feffect.value = ""; el.clear.classList.remove("show");
    state.sort = state.view === "effect" ? "score" : "name";
    state.dir = state.view === "effect" ? "desc" : "asc";
    el.sort.value = state.sort;
    render();
  });

  // ---- boot ----
  setView("recipe");
})();
