/* 无人深空 · 营养摄入器 — 交互逻辑 (locale-aware)
   Reads the page's data-locale (zh/en) and data-base, renders that language
   only, and links every item to its localized item page. */
(function () {
  "use strict";
  const NMS = window.NMS || { summary: {}, data: [] };
  const DATA = NMS.data || [];

  // ---- locale + base path from the page ----
  const b = (document.body && document.body.dataset) || {};
  const LOCALE = b.locale || "zh";
  const BASE = b.base || "";
  const isZh = LOCALE === "zh";

  const L = isZh
    ? {
        all: "全部", fished: "🎣 捕捞", gathered: "🌿 采集", na: "—",
        variants: n => n + " 种配方",
        colName: "名称", colType: "类型", colTime: "烹饪时间", colRecipe: "合成公式",
        colEffect: "效果", colBonus: "加成", colDur: "持续时间", colScore: "综合分",
        sort: { name: "按名称", time: "按烹饪时间", type: "按类型", score: "综合分（默认）", bonus: "按加成", total: "按时长" },
      }
    : {
        all: "All", fished: "🎣 Fished", gathered: "🌿 Gathered", na: "—",
        variants: n => n + " recipes",
        colName: "Name", colType: "Type", colTime: "Cook time", colRecipe: "Recipe",
        colEffect: "Effect", colBonus: "Bonus", colDur: "Duration", colScore: "Score",
        sort: { name: "By name", time: "By cook time", type: "By type", score: "Score (default)", bonus: "By bonus", total: "By duration" },
      };

  // ---- DOM ----
  const $ = s => document.querySelector(s);
  // Item detail pages have no table: nothing to do here.
  if (!document.getElementById("head") || !document.getElementById("body")) return;
  const el = {
    tabs: document.querySelectorAll(".tab"),
    q: $("#q"), clear: $("#clear"),
    ftype: $("#ftype"), feffect: $("#feffect"),
    sort: $("#sort"),
    shown: $("#shown"), total: $("#total"), reset: $("#reset"),
    head: $("#head"), body: $("#body"), empty: $("#empty"),
  };

  const state = { view: "recipe", q: "", type: "", effect: "", sort: "name", dir: "asc" };

  // ---- helpers ----
  const badgeClass = t => (t === "食用产品" || t === "鱼" || t === "原料") ? "b-" + t : "b-其他";
  const fmt = n => Math.round(n).toLocaleString(isZh ? "zh-CN" : "en-US");
  const timeStr = d => { const m = Math.floor(d.total / 60), s = d.total % 60; return m + ":" + String(s).padStart(2, "0"); };
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

  const nameOf = d => (isZh ? d.zh : d.en);
  const typeOf = d => (isZh ? d.type : d.type_en);
  const effectOf = d => (isZh ? d.effect : d.effect_en);
  const itemHref = d => BASE + "/items/" + d.slug + "/";

  // ingredient name -> dataset item (mirrors tools/build.py _norm), for clickable recipe cells
  const norm = s => String(s).normalize("NFKC").toLowerCase()
    .replace(/['"''""]/g, "").replace(/\(.*?\)/g, "").replace(/\s+/g, " ").trim();
  const EXACT = {};
  const NORM = {};
  DATA.forEach(d => {
    if (!EXACT[d.en]) EXACT[d.en] = d;
    const k = norm(d.en);
    if (k && !NORM[k]) NORM[k] = d;
  });
  // aliases/wiki 来自 tools/name_map.py（build.py 注入）：
  // ALIASES 把维基配方拼写变体映射到数据集物品；WIKI 是数据集外原料的 Fandom 维基页
  const ALIAS = NMS.aliases || {};
  const WIKI = NMS.wiki || {};
  const resolveIng = n => EXACT[n] || EXACT[ALIAS[n]] || NORM[norm(n)] || NORM[norm(ALIAS[n])] || null;
  const wikiUrl = n => WIKI[n] || WIKI[ALIAS[n]] || "";

  function recipeCell(d) {
    const r = d.recipe || { has: false, variants: 0, ingredients: [] };
    if (!r.has) {
      const na = d.type_en === "Fish" ? L.fished : (d.type === "原料" ? L.gathered : L.na);
      return `<span class="recipe-na">${na}</span>`;
    }
    const field = isZh ? "zh" : "en";
    const sep = isZh ? " ＋ " : " + ";
    const parts = r.ingredients.map(i => {
      const t = resolveIng(i.en);
      const w = t ? "" : wikiUrl(i.en);
      const name = t
        ? `<a class="ing-link" href="${BASE}/items/${t.slug}/">${esc(i[field])}</a>`
        : w
          ? `<a class="ing-link ing-extern" href="${w}" target="_blank" rel="noopener">${esc(i[field])}</a>`
          : esc(i[field]);
      return name + " ×" + i.qty;
    });
    let html = `<span class="recipe-f">${parts.join(sep)}</span>`;
    if (r.variants > 1) html += ` <span class="variants">(${L.variants(r.variants)})</span>`;
    return html;
  }

  // ---- columns per view ----
  const COLUMNS = {
    recipe: [
      { key: "idx", label: "#", sortable: false },
      { key: "name", label: L.colName, sortable: true },
      { key: "type", label: L.colType, sortable: true },
      { key: "time", label: L.colTime, sortable: true },
      { key: "recipe", label: L.colRecipe, sortable: false },
    ],
    effect: [
      { key: "idx", label: "#", sortable: false },
      { key: "name", label: L.colName, sortable: true },
      { key: "effect", label: L.colEffect, sortable: true },
      { key: "bonus", label: L.colBonus, sortable: true, right: true },
      { key: "total", label: L.colDur, sortable: true, right: true },
      { key: "score", label: L.colScore, sortable: true, right: true },
    ],
  };

  const SORT_GET = {
    name: d => nameOf(d),
    type: d => typeOf(d) + "\u0001" + nameOf(d),
    time: d => d.total,
    bonus: d => d.bonus,
    total: d => d.total,
    score: d => d.bonus_total,
  };

  // ---- populate locale-aware filters ----
  [...new Set(DATA.map(d => typeOf(d)))].sort((a, b) => a.localeCompare(b)).forEach(t => {
    const o = document.createElement("option"); o.value = t; o.textContent = t; el.ftype.appendChild(o);
  });
  [...new Set(DATA.map(d => effectOf(d)))].sort((a, b) => a.localeCompare(b)).forEach(t => {
    const o = document.createElement("option"); o.value = t; o.textContent = t; el.feffect.appendChild(o);
  });
  if (el.total) el.total.textContent = DATA.length;

  function buildSortOptions() {
    const keys = state.view === "recipe" ? ["name", "time", "type"] : ["score", "bonus", "total", "name"];
    el.sort.innerHTML = "";
    keys.forEach(val => {
      const o = document.createElement("option");
      o.value = val; o.textContent = L.sort[val];
      if (val === state.sort) o.selected = true;
      el.sort.appendChild(o);
    });
  }

  function setView(view) {
    state.view = view;
    state.effect = ""; el.feffect.value = "";
    state.sort = view === "effect" ? "score" : "name";
    state.dir = view === "effect" ? "desc" : "asc";
    el.tabs.forEach(t => { const on = t.dataset.view === view; t.classList.toggle("active", on); t.setAttribute("aria-selected", on); });
    buildSortOptions();
    render();
  }

  function currentList() {
    const q = state.q.trim().toLowerCase();
    let list = DATA.filter(d => {
      if (state.type && typeOf(d) !== state.type) return false;
      if (state.effect && effectOf(d) !== state.effect) return false;
      if (q) {
        const hay = (d.zh + " " + d.en + " " + d.effect + " " + d.effect_en + " " + d.type + " " + d.type_en).toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });
    const get = SORT_GET[state.sort] || SORT_GET.name;
    list.sort((a, b) => {
      const x = get(a), y = get(b);
      if (typeof x === "string") { const c = x.localeCompare(y, isZh ? "zh-Hans-CN" : "en"); return state.dir === "desc" ? -c : c; }
      return state.dir === "desc" ? y - x : x - y;
    });
    return list;
  }

  function render() {
    const list = currentList();
    const cols = COLUMNS[state.view];
    el.head.innerHTML = cols.map(c => {
      const sorted = c.key === state.sort && c.sortable;
      const arr = sorted ? (state.dir === "desc" ? "↓" : "↑") : "";
      return `<th data-key="${c.key}" class="${sorted ? "sorted" : ""} ${c.right ? "num" : ""}">${esc(c.label)}<span class="arr">${arr}</span></th>`;
    }).join("");
    el.head.querySelectorAll("th").forEach(th => {
      if (th.dataset.key && th.dataset.key !== "idx" && th.dataset.key !== "recipe") {
        th.addEventListener("click", () => toggleSort(th.dataset.key));
      }
    });
    el.body.innerHTML = list.map((d, i) => {
      const c = i + 1;
      let cells = `<td class="idx">${c}</td>`;
      cells += `<td class="name-cell"><a class="item-link" href="${itemHref(d)}">${esc(nameOf(d))}</a></td>`;
      if (state.view === "recipe") {
        cells += `<td><span class="badge ${badgeClass(d.type)}">${esc(typeOf(d))}</span></td>`;
        cells += `<td class="num time">${timeStr(d)}</td>`;
        cells += `<td class="recipe-cell">${recipeCell(d)}</td>`;
      } else {
        cells += `<td class="effect-cell">${esc(effectOf(d))}</td>`;
        cells += `<td class="num">${fmt(d.bonus)}<span style="color:var(--muted2)">%</span></td>`;
        cells += `<td class="num time">${timeStr(d)}</td>`;
        cells += `<td class="num big">${fmt(d.bonus_total)}</td>`;
      }
      return `<tr>${cells}</tr>`;
    }).join("");
    el.shown.textContent = list.length;
    if (el.empty) el.empty.hidden = list.length > 0;
  }

  function toggleSort(key) {
    if (key === state.sort) state.dir = state.dir === "desc" ? "asc" : "desc";
    else { state.sort = key; state.dir = (key === "name" || key === "type") ? "asc" : "desc"; }
    el.sort.value = state.sort;
    render();
  }

  // ---- events ----
  el.tabs.forEach(t => t.addEventListener("click", () => setView(t.dataset.view)));
  el.q.addEventListener("input", () => { state.q = el.q.value; el.clear.classList.toggle("show", !!el.q.value); render(); });
  el.clear.addEventListener("click", () => { el.q.value = ""; state.q = ""; el.clear.classList.remove("show"); el.q.focus(); render(); });
  el.ftype.addEventListener("change", () => { state.type = el.ftype.value; render(); });
  el.feffect.addEventListener("change", () => { state.effect = el.feffect.value; render(); });
  el.sort.addEventListener("change", () => { state.sort = el.sort.value; state.dir = (state.sort === "name" || state.sort === "type") ? "asc" : "desc"; render(); });
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
