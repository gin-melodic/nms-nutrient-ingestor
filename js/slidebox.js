/* Slidebox — 合成树节点侧滑面板。
   点击合成节点树中的 a.rchip 时，不跳转页面，而是从右侧滑出面板加载该物品页
   （article.itemcard），并可在面板内继续点击子节点逐层深入、返回、Esc 关闭。
   无 JS 时 a.rchip 保持原生跳转（渐进增强）。 */
(function () {
  "use strict";
  if (!document.querySelector("a.rchip")) return;

  const body = document.body;
  const isZh = (body.dataset || {}).locale !== "en";
  const L = isZh
    ? {
        label: "原料详情",
        back: "返回上一个",
        close: "关闭",
        open: "在新标签页打开",
        loading: "正在加载配方页…",
        fail: "打开失败，正在跳转到该物品页…",
        full: "打开完整物品页 ↗",
      }
    : {
        label: "Ingredient detail",
        back: "Back",
        close: "Close",
        open: "Open in new tab",
        loading: "Loading recipe page…",
        fail: "Failed to load — navigating to the item page…",
        full: "Open full item page ↗",
      };

  // ---- build shell (once) ----
  const wrap = document.createElement("div");
  wrap.innerHTML =
    '<div class="sb-backdrop" hidden></div>' +
    '<aside class="sb-panel" role="dialog" aria-modal="true" aria-label="' + L.label + '">' +
      '<div class="sb-head">' +
        '<button type="button" class="sb-btn sb-back" title="' + L.back + '" aria-label="' + L.back + '" disabled>←</button>' +
        '<div class="sb-title">' + L.label + '</div>' +
        '<a class="sb-btn sb-openbtn" target="_blank" rel="noopener" href="#" title="' + L.open + '" aria-label="' + L.open + '">↗</a>' +
        '<button type="button" class="sb-btn sb-close" title="' + L.close + '" aria-label="' + L.close + '">✕</button>' +
      '</div>' +
      '<div class="sb-body"></div>' +
    '</aside>';
  body.appendChild(wrap);

  const backdrop = wrap.querySelector(".sb-backdrop");
  const panel = wrap.querySelector(".sb-panel");
  const box = wrap.querySelector(".sb-body");
  const btnBack = wrap.querySelector(".sb-back");
  const btnClose = wrap.querySelector(".sb-close");
  const btnOpen = wrap.querySelector(".sb-openbtn");
  const title = wrap.querySelector(".sb-title");

  const stack = [];
  let lastFocus = null;
  let loadId = 0;
  let opening = false;

  function open() {
    if (opening) return;
    opening = true;
    lastFocus = document.activeElement;
    body.classList.add("sb-open");
    backdrop.hidden = false;
    panel.classList.add("show");
    requestAnimationFrame(() => requestAnimationFrame(() => backdrop.classList.add("show")));
    btnClose.focus({ preventScroll: true });
  }

  function close() {
    if (!panel.classList.contains("show")) return;
    stack.length = 0;
    body.classList.remove("sb-open");
    panel.classList.remove("show");
    backdrop.classList.remove("show");
    setTimeout(() => { if (!panel.classList.contains("show")) backdrop.hidden = true; }, 340);
    if (lastFocus && lastFocus.focus) lastFocus.focus({ preventScroll: true });
  }

  function updateBack() {
    btnBack.disabled = stack.length < 2;
  }

  function show(url) {
    const id = ++loadId;
    box.classList.remove("sb-fade");
    box.innerHTML = '<div class="sb-load"><div class="sb-spin"></div>' + L.loading + "</div>";
    updateBack();
    fetch(url, { headers: { Accept: "text/html" } })
      .then(r => { if (!r.ok) throw new Error("http " + r.status); return r.text(); })
      .then(t => {
        if (id !== loadId) return;
        const doc = new DOMParser().parseFromString(t, "text/html");
        const card = doc.querySelector("article.itemcard");
        if (!card) throw new Error("no itemcard");
        box.innerHTML = "";
        box.appendChild(card.cloneNode(true));
        const nameEl = card.querySelector(".item-name");
        const name = nameEl ? nameEl.textContent : "";
        const foot = doc.createElement("p");
        foot.className = "sb-footlink";
        foot.innerHTML = '<a href="' + url + '" target="_blank" rel="noopener">' + L.full + "</a>";
        box.appendChild(foot);
        title.textContent = name ? name + " · " + L.label : L.label;
        btnOpen.href = url;
        box.scrollTop = 0;
        void box.offsetWidth; // restart the fade-in
        box.classList.add("sb-fade");
        updateBack();
      })
      .catch(() => {
        if (id !== loadId) return;
        title.textContent = L.fail;
        setTimeout(() => { if (id === loadId) window.location.assign(url); }, 600);
      });
  }

  function navigate(url) {
    if (!panel.classList.contains("show")) open();
    stack.push(url);
    show(url);
  }

  // any a.rchip click (page or inside the panel) → slidebox
  document.addEventListener("click", e => {
    const a = e.target.closest("a.rchip");
    if (!a || !a.href) return;
    e.preventDefault();
    navigate(a.href);
  });

  btnBack.addEventListener("click", () => {
    stack.pop();
    if (!stack.length) { close(); return; }
    show(stack[stack.length - 1]);
  });
  btnClose.addEventListener("click", close);
  backdrop.addEventListener("click", close);
  document.addEventListener("keydown", e => {
    if (e.key === "Escape" && panel.classList.contains("show")) close();
  });
})();
