# -*- coding: utf-8 -*-
"""Generate the localized, SEO-optimized static site.

Reads data.json (built by build.py, which merges tools/recipes.json) and emits:
  - index.html                       (English, primary) -> /
  - zh/index.html                    (Chinese)          -> /zh/
  - items/<slug>/index.html          (English item page) -> /items/<slug>/
  - zh/items/<slug>/index.html       (Chinese item page) -> /zh/items/<slug>/
  - vercel.json (301 redirects from the old /en/... and old Chinese /items/... URLs)
  - robots.txt, sitemap.xml, og-image.png

Each page is single-language (no mixed zh/en), carries full SEO meta
(canonical, hreflang, Open Graph, Twitter Card, JSON-LD) and is served as
static files (no build step required on the host).
"""
import json, os, sys, html, re, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from name_map import ALIASES, WIKI_PAGE  # 别名 + 维基外链（tools/name_map.py）

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://nms.ginmel.ai"  # production base URL (no trailing slash)

DATA = json.load(open(os.path.join(ROOT, "data.json"), encoding="utf-8"))
ITEMS = DATA["data"]
SUMMARY = DATA["summary"]

# ---- ingredient -> item-page resolution (mirrors build.py's _norm) ----
BY_EN = {d["en"]: d for d in ITEMS}


def _norm_name(s):
    s = unicodedata.normalize("NFKC", str(s)).lower()
    s = re.sub(r"['\"’“”]", "", s)      # quotes
    s = re.sub(r"\(.*?\)", "", s)        # parenthetical
    s = re.sub(r"\s+", " ", s).strip()
    return s


BY_NORM = {}
for _d in ITEMS:
    _k = _norm_name(_d["en"])
    BY_NORM.setdefault(_k, _d)


def resolve_ing(name):
    """EN ingredient name -> dataset item (exact, then normalised), or None.
    ALIASES（name_map.py）把维基配方里的拼写变体映射到数据集物品名。"""
    if not name:
        return None
    for cand in (name, ALIASES.get(name)):
        if not cand:
            continue
        hit = BY_EN.get(cand) or BY_NORM.get(_norm_name(cand))
        if hit:
            return hit
    return None


def wiki_url(name):
    """数据集外的原料 -> Fandom 维基页面 URL（name_map.py WIKI_PAGE），无则 None。"""
    if not name:
        return None
    return WIKI_PAGE.get(name) or WIKI_PAGE.get(ALIASES.get(name, ""))

LOCALES = {
    "en": {"base": "", "html": "en", "og_locale": "en_US", "label": "English"},
    "zh": {"base": "/zh", "html": "zh-CN", "og_locale": "zh_CN", "label": "中文"},
}

STR = {
    "zh": {
        "site_name": "无人深空 · 营养摄入器",
        "home_title": "无人深空 营养摄入器 配方表·效果表｜合成公式 · 增益效果 · 综合分",
        "home_desc": "《无人深空》营养摄入器（Nutrient Ingestor）配方表与效果表：575 种食物的合成公式（原料配方）、增益效果、加成、持续时间与「加成×时长」综合分，支持搜索、筛选与排序。",
        "item_title": "{name} · 配方与效果｜无人深空 营养摄入器",
        "item_desc": "{name}：{recipe}，增益「{effect}」+{bonus}%，持续 {time}，综合分 {score}。",
        "stat_items": "物品总数", "stat_recipes": "可合成配方", "stat_types": "物品类型", "stat_effects": "增益效果",
        "tab_recipe": "配方表", "tab_effect": "效果表",
        "search_ph": "搜索名称、效果…（例如：苹果冰淇淋、Cold Resistance）",
        "clear": "清空", "clear_aria": "清空搜索",
        "label_type": "类型", "label_effect": "效果", "label_sort": "排序",
        "all": "全部",
        "results": "条结果", "reset": "重置筛选",
        "col_name": "名称", "col_type": "类型", "col_time": "烹饪时间", "col_recipe": "合成公式",
        "col_effect": "效果", "col_bonus": "加成", "col_dur": "持续时间", "col_score": "综合分",
        "sort_name": "按名称", "sort_time": "按烹饪时间", "sort_type": "按类型",
        "sort_score": "综合分（默认）", "sort_bonus": "按加成", "sort_dur": "按时长",
        "fished": "🎣 捕捞", "recipes_unit": "种配方",
        "recipe_h": "合成公式", "recipe_h2": "原料配方",
        "effect_h": "增益效果",
        "bonus_l": "加成", "dur_l": "持续时间", "score_l": "综合分", "effect_l": "效果",
        "en_name": "英文名", "zh_name": "中文名",
        "back": "返回配方表", "lang": "语言",
        "foot_src1": "效果数据来源", "foot_src2": "中文术语来源",
        "foot_link1": "Nutrient Ingestor 数据表", "foot_link2": "无人深空中文维基",
        "foot_note": "配方表：营养摄入器可合成的物品、原料配方与烹饪时间。效果表：食用后的增益、持续时间与「加成×时长」综合分（分数越高，增益越强 / 越持久）。无配方的物品多为捕捞、采集或狩猎获得。",
        "no_recipe": "无配方",
        "gathered": "🌿 采集",
        "howto_h": "获取建议",
        "howto_fish": "🎣 钓鱼获取：在任意星球的水域（海洋、湖泊）使用鱼竿垂钓。",
        "howto_fish_sub": "不同星球的生态会产出不同的鱼种；稀有鱼只出现在特定生态。",
        "howto_gather": "🌿 采集获取：在行星表面采集对应的植物 / 资源节点，或从生物身上获取。",
        "howto_gather_sub": "基础原料，无需合成，取得后直接放入营养摄入器搭配使用。",
        "howto_general": "🧭 无需合成：直接在星球世界中获取（探索、狩猎、采集或交易）后即可食用。",
        "howto_general_sub": "来自特定生物或环境，取得后直接放入营养摄入器。",
        "howto_short_fish": "钓鱼获得",
        "howto_short_gather": "采集 / 狩猎获得",
        "howto_short_general": "在星球世界中直接获取",
        "tree_hint": "点击任意原料节点，在右侧滑出面板中逐层查看完整合成树与增益效果。「N 种 · 任选其一」分支表示替代配方——任选一组原料即可合成",
        "raw_tag": "无物品页",
        "raw_wiki_tag": "无物品页 · 维基 ↗",
        "cyc_tag": "递归，不再展开",
        "alt_unit": "种",
        "alt_pick": "任选其一",
        "alt_none": "（无）",
        "variant_all": "共 {n} 种替代配方，树中已完整展示（「N 种 · 任选其一」分支）——任选一组原料即可合成",
    },
    "en": {
        "site_name": "No Man's Sky · Nutrient Ingestor",
        "home_title": "No Man's Sky Nutrient Ingestor — Recipe & Effect Tables, Crafting Formulas",
        "home_desc": "No Man's Sky Nutrient Ingestor recipes and effects: crafting formulas (ingredients), buffs, bonus, duration and score for 575 food items, with search, filter and sort.",
        "item_title": "{name} — Recipe & Effect · No Man's Sky Nutrient Ingestor",
        "item_desc": "{name}: {recipe}, grants {effect} +{bonus}% for {time}, score {score}.",
        "stat_items": "Items", "stat_recipes": "Craftable", "stat_types": "Types", "stat_effects": "Effects",
        "tab_recipe": "Recipes", "tab_effect": "Effects",
        "search_ph": "Search name or effect… (e.g. Apple Ice Cream, Cold Resistance)",
        "clear": "Clear", "clear_aria": "Clear search",
        "label_type": "Type", "label_effect": "Effect", "label_sort": "Sort",
        "all": "All",
        "results": "results", "reset": "Reset filters",
        "col_name": "Name", "col_type": "Type", "col_time": "Cook time", "col_recipe": "Recipe",
        "col_effect": "Effect", "col_bonus": "Bonus", "col_dur": "Duration", "col_score": "Score",
        "sort_name": "By name", "sort_time": "By cook time", "sort_type": "By type",
        "sort_score": "Score (default)", "sort_bonus": "By bonus", "sort_dur": "By duration",
        "fished": "🎣 Fished", "recipes_unit": "recipes",
        "recipe_h": "Recipe", "recipe_h2": "Crafting formula",
        "effect_h": "Buff",
        "bonus_l": "Bonus", "dur_l": "Duration", "score_l": "Score", "effect_l": "Effect",
        "en_name": "EN name", "zh_name": "Chinese name",
        "back": "Back to recipes", "lang": "Language",
        "foot_src1": "Effects data source", "foot_src2": "Chinese terminology",
        "foot_link1": "Nutrient Ingestor dataset", "foot_link2": "NMS Chinese Wiki (huijiwiki)",
        "foot_note": "Recipe: items the Nutrient Ingestor can craft, their ingredient formula and cook time. Effects: the buff, duration and score (bonus × duration) — higher = stronger / longer. Items without a recipe are usually fished, gathered or hunted.",
        "no_recipe": "No recipe",
        "gathered": "🌿 Gathered",
        "howto_h": "How to get",
        "howto_fish": "🎣 Caught by fishing: use a fishing rod in any planet's waters (oceans, lakes).",
        "howto_fish_sub": "Different ecosystems yield different species; rare fish only spawn in specific habitats.",
        "howto_gather": "🌿 Gathered: harvest the matching plant / resource nodes on a planet surface, or obtain it from fauna.",
        "howto_gather_sub": "Base ingredients — no crafting needed, feed them straight to the Nutrient Ingestor.",
        "howto_general": "🧭 No crafting needed: obtain it directly in the world (explore, hunt, gather or trade), then ingest.",
        "howto_general_sub": "Sourced from specific creatures or environments; use it straight in the Nutrient Ingestor.",
        "howto_short_fish": "caught by fishing",
        "howto_short_gather": "gathered / hunted in the world",
        "howto_short_general": "obtained directly in the world",
        "tree_hint": "Click any ingredient node to slide in its full recipe tree and buff. 'N alternatives · pick any' branches are alternative recipes — any one set of ingredients works",
        "raw_tag": "no page",
        "raw_wiki_tag": "no page · wiki ↗",
        "cyc_tag": "recursion, not expanded",
        "alt_unit": "alternatives",
        "alt_pick": "pick any",
        "alt_none": "(none)",
        "variant_all": "{n} alternative recipes, all shown in the tree ('N alternatives · pick any' branches) — any one set of ingredients works",
    },
}


def esc(s):
    return html.escape(str(s), quote=True)


def other(l):
    return "en" if l == "zh" else "zh"


def absu(path):
    return BASE + path


def name_of(l, item):
    return item["zh"] if l == "zh" else item["en"]


def type_of(l, item):
    return item["type"] if l == "zh" else item["type_en"]


def badge_class(t_zh):
    return "b-" + t_zh if t_zh in ("食用产品", "鱼", "原料") else "b-其他"


def effect_of(l, item):
    return item["effect"] if l == "zh" else item["effect_en"]


def time_str(item):
    m, s = divmod(item["total"], 60)
    return f"{m}:{s:02d}"


def fmt(n):
    return f"{round(n):,}"


def recipe_formula(l, item):
    r = item["recipe"]
    field = "zh" if l == "zh" else "en"
    parts = [f'{esc(ing[field])} ×{ing["qty"]}' for ing in r["ingredients"]]
    sep = " ＋ " if l == "zh" else " + "
    return sep.join(parts)


def _ingredient_label(l, ing):
    field = "zh" if l == "zh" else "en"
    name = esc(ing[field])
    target = resolve_ing(ing["en"])
    if target:
        name = f'<a class="ing-link" href="{item_path(l, target["slug"])}">{name}</a>'
    else:
        w = wiki_url(ing["en"])
        if w:
            name = f'<a class="ing-link ing-extern" href="{w}" target="_blank" rel="noopener">{name}</a>'
    return name


def recipe_cell(l, item):
    r = item["recipe"]
    if not r["has"]:
        if item["type_en"] == "Fish":
            return f'<span class="recipe-na">{STR[l]["fished"]}</span>'
        if item["type"] == "原料":
            return f'<span class="recipe-na">{STR[l]["gathered"]}</span>'
        return f'<span class="recipe-na">—</span>'
    sep = " ＋ " if l == "zh" else " + "
    parts = [f'{_ingredient_label(l, i)} ×{i["qty"]}' for i in r["ingredients"]]
    html_ = f'<span class="recipe-f">{sep.join(parts)}</span>'
    if r["variants"] > 1:
        html_ += f' <span class="variants">({r["variants"]} {STR[l]["recipes_unit"]})</span>'
    return html_


def chip_class(t_zh):
    return {"食用产品": "t-food", "鱼": "t-fish", "原料": "t-raw"}.get(t_zh, "t-other")


TYPE_ICON = {"食用产品": "🍽️", "鱼": "🐟", "原料": "🌿"}


def icon_of(t_zh):
    return TYPE_ICON.get(t_zh, "🧪")


TREE_MAX_DEPTH = 8  # dataset max is 6; defensive cap


def _slots(alts):
    """Align alternative recipes into slot columns.

    The wiki lists alternative recipes as parallel lines whose ingredient
    *positions* line up (slot 1, slot 2, …). A slot where every variant
    agrees renders as one plain node; a slot with differing values renders
    as an "or" group (pick any one). Returns [{"vals": [ing|None, …]}].
    """
    if not alts:
        return []
    max_len = max(len(a) for a in alts)
    slots = []
    for i in range(max_len):
        distinct = []
        for a in alts:
            v = a[i] if i < len(a) else None
            key = (v["en"], v["qty"]) if v else None
            if all(((x["en"], x["qty"]) if x else None) != key for x in distinct):
                distinct.append(v)
        slots.append({"vals": distinct})
    return slots


def _chip(l, ing, target):
    """One ingredient chip (raw / cycle / linkable) + optional recursive subtree."""
    field = "zh" if l == "zh" else "en"
    qty = int(ing.get("qty", 1))
    qty_html = f'<span class="rqty">×{qty}</span>' if qty > 1 else ""
    label = esc(ing[field])
    if target is None:
        w = wiki_url(ing["en"])
        if w:
            return (f'<a class="rchip rchip-raw rchip-extern" href="{w}" target="_blank" rel="noopener">'
                    f'<i class="ricon" aria-hidden="true">🌿</i>{label}{qty_html}'
                    f'<span class="rchip-tag">{esc(STR[l]["raw_wiki_tag"])}</span></a>'), ""
        return f'<span class="rchip rchip-raw"><i class="ricon" aria-hidden="true">🌿</i>{label}{qty_html}<span class="rchip-tag">{esc(STR[l]["raw_tag"])}</span></span>', ""
    return (f'<a class="rchip rchip-{chip_class(target["type"])}" href="{item_path(l, target["slug"])}">'
            f'<i class="ricon" aria-hidden="true">{icon_of(target["type"])}</i>{label}{qty_html}</a>'), True


def _node(l, ing, seen, depth):
    """One <li> child for a single ingredient value (or an empty slot)."""
    if ing is None:
        return f'<li class="rnode"><span class="rchip rchip-raw"><i class="ricon" aria-hidden="true">—</i>{esc(STR[l]["alt_none"])}</span></li>'
    target = resolve_ing(ing["en"])
    if target is None:
        chip, _ = _chip(l, ing, target)
        return f'<li class="rnode">{chip}</li>'
    if target["en"] in seen:
        field = "zh" if l == "zh" else "en"
        qty_html = f'<span class="rqty">×{int(ing.get("qty", 1))}</span>' if int(ing.get("qty", 1)) > 1 else ""
        chip = (f'<span class="rchip rchip-cyc"><i class="ricon" aria-hidden="true">↻</i>'
                f'{esc(ing[field])}{qty_html}<span class="rchip-tag">{esc(STR[l]["cyc_tag"])}</span></span>')
        return f'<li class="rnode">{chip}</li>'
    chip, _ = _chip(l, ing, target)
    sub = _children(l, target, seen | {target["en"]}, depth + 1)
    return f'<li class="rnode">{chip}{sub}</li>'


def _children(l, item, seen, depth):
    """One <ul> of children for `item` from its FULL set of alternative recipes.

    Slots where all variants agree → plain ingredient nodes (recursively
    expanded). Slots with alternatives → an "or" group node listing every
    choice; each choice expands recursively with the same ancestor set.
    """
    r = item["recipe"]
    if not r["has"] or depth >= TREE_MAX_DEPTH:
        return ""
    parts = []
    for slot in _slots(r.get("alts") or r.get("ingredients") and [r["ingredients"]]):
        vals = slot["vals"]
        if len(vals) == 1 and vals[0] is not None:
            parts.append(_node(l, vals[0], seen, depth))
        else:
            n = len(vals)  # include the "(none)" option when present
            inner = "".join(_node(l, v, seen, depth) for v in vals)
            label = f'{n} {STR[l]["alt_unit"]} · {STR[l]["alt_pick"]}'
            parts.append(f'<li class="rnode rnode-alt"><span class="rchip rchip-alt">'
                         f'<i class="ricon" aria-hidden="true">⑂</i>{esc(label)}</span>'
                         f'<ul class="rtree">{inner}</ul></li>')
    return f'<ul class="rtree">{"".join(parts)}</ul>'


def recipe_tree_html(l, d):
    """Full, fully-expanded recipe node tree (root = the item itself), including
    every alternative recipe as "or" branches. Server-rendered, no JS required."""
    root = (f'<span class="rchip rchip-root rchip-{chip_class(d["type"])}">'
            f'<i class="ricon" aria-hidden="true">{icon_of(d["type"])}</i>{esc(name_of(l, d))}'
            f'<span class="rchip-type">{esc(type_of(l, d))}</span></span>')
    sub = _children(l, d, {d["en"]}, 0)
    return (f'<div class="rstage"><ul class="rtree rtree-root"><li class="rnode rnode-root">{root}{sub}</li></ul></div>'
            f'<p class="tree-hint">{esc(STR[l]["tree_hint"])}</p>')


def howto(l, d):
    """Acquisition advice for items that need no crafting.

    Per-item curated text (d["obtain"], from the Fandom wiki) takes priority;
    type-generic fallbacks below. Returns (main, sub, short-for-meta)."""
    t = STR[l]
    ob = (d.get("obtain") or {}).get(l)
    if ob:
        # split main/sub at the first true sentence end (。for zh; ". "for en)
        sep = r"[。]" if l == "zh" else r"\.\s"
        m = re.match(r"^(.*?" + sep + r")(.*)$", ob, re.S)
        first = m.group(1).strip() if m else ob
        rest = m.group(2).strip() if m else ""
        short = first.rstrip("。. ")  # meta text is spliced into a longer sentence
        if rest:
            return first, rest, short
        return ob, "", short
    if d["type_en"] == "Fish":
        return t["howto_fish"], t["howto_fish_sub"], t["howto_short_fish"]
    if d["type"] == "原料":
        return t["howto_gather"], t["howto_gather_sub"], t["howto_short_gather"]
    return t["howto_general"], t["howto_general_sub"], t["howto_short_general"]


def item_path(l, slug):
    return (LOCALES[l]["base"] or "") + f"/items/{slug}/"


def home_path(l):
    return (LOCALES[l]["base"] or "") + "/"


def head(l, title, desc, zh_url, en_url, ld=None, extra_body=None):
    L = LOCALES[l]
    canonical = zh_url if l == "zh" else en_url
    og_img = absu("/og-image.png")
    ld_block = ""
    if ld:
        ld_block = "\n".join(
            f'  <script type="application/ld+json">{json.dumps(d, ensure_ascii=False)}</script>'
            for d in ld)
    return f"""<!DOCTYPE html>
<html lang="{L['html']}">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(desc)}" />
  <meta name="robots" content="index,follow" />
  <link rel="canonical" href="{canonical}" />
  <link rel="alternate" hreflang="x-default" href="{en_url}" />
  <link rel="alternate" hreflang="zh" href="{zh_url}" />
  <link rel="alternate" hreflang="en" href="{en_url}" />
  <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ctext y='.9em' font-size='90'%3E%F0%9F%8C%8C%3C/text%3E%3C/svg%3E" />
  <meta property="og:type" content="website" />
  <meta property="og:site_name" content="{esc(STR[l]['site_name'])}" />
  <meta property="og:locale" content="{L['og_locale']}" />
  <meta property="og:title" content="{esc(title)}" />
  <meta property="og:description" content="{esc(desc)}" />
  <meta property="og:url" content="{canonical}" />
  <meta property="og:image" content="{og_img}" />
  <meta property="og:image:width" content="1200" />
  <meta property="og:image:height" content="630" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{esc(title)}" />
  <meta name="twitter:description" content="{esc(desc)}" />
  <meta name="twitter:image" content="{og_img}" />
  <link rel="stylesheet" href="/style.css" />
{ld_block}
</head>
<body data-locale="{l}" data-base="{L['base'] or ''}">
"""


def hero(l, show_stats=True):
    st = ""
    if show_stats:
        st = f"""
    <div class="hero-stats">
      <div class="stat"><b>{SUMMARY['count']}</b><span>{STR[l]['stat_items']}</span></div>
      <div class="stat"><b>{SUMMARY.get('recipes', 0)}</b><span>{STR[l]['stat_recipes']}</span></div>
      <div class="stat"><b>{len(SUMMARY['types'])}</b><span>{STR[l]['stat_types']}</span></div>
      <div class="stat"><b>{len(SUMMARY['effects'])}</b><span>{STR[l]['stat_effects']}</span></div>
    </div>"""
    return f"""<header class="hero">
  <div class="hero-inner">
    <div class="brand">
      <span class="glyph" aria-hidden="true">🌌</span>
      <div>
        <h1>{esc(STR[l]['site_name'])}</h1>
        <p class="sub">{esc(STR[l]['home_desc'][:110] + '…' if len(STR[l]['home_desc'])>110 else STR[l]['home_desc'])}</p>
      </div>
    </div>
{st}
    <div class="langbar">{STR[l]['lang']} <a class="lang-btn" href="{absu(home_path(other(l)))}">{LOCALES[other(l)]['label']}</a></div>
  </div>
</header>
"""


def footer(l):
    return f"""  <footer class="foot">
    <div class="src">
      <span class="dot"></span> {STR[l]['foot_src1']}：<a href="https://docs.google.com/spreadsheets/d/1oiyYjbAX_pi2drhP0vxnjI1ZG14XB8VCmr5vSBH9N7g" target="_blank" rel="noopener">{esc(STR[l]['foot_link1'])}</a>
      <span class="dot"></span> {STR[l]['foot_src2']}：<a href="https://nms.huijiwiki.com/wiki/%E9%A6%96%E9%A1%B5" target="_blank" rel="noopener">{esc(STR[l]['foot_link2'])}</a>
    </div>
    <div class="note">{esc(STR[l]['foot_note'])}</div>
  </footer>
"""


def build_sort_options(l):
    if True:
        recipe_map = [("name", STR[l]["sort_name"]), ("time", STR[l]["sort_time"]), ("type", STR[l]["sort_type"])]
        effect_map = [("score", STR[l]["sort_score"]), ("bonus", STR[l]["sort_bonus"]), ("total", STR[l]["sort_dur"]), ("name", STR[l]["sort_name"])]
        return recipe_map, effect_map
    return [], []


def home_rows(l):
    """Pre-render the recipe view (default) so the content is crawlable."""
    out = []
    for i, d in enumerate(ITEMS, 1):
        link = item_path(l, d["slug"])
        name_html = esc(name_of(l, d))
        out.append(
            "<tr>"
            f'<td class="idx">{i}</td>'
            f'<td class="name-cell"><a class="item-link" href="{link}">{name_html}</a></td>'
            f'<td><span class="badge {badge_class(d["type"])}">{esc(type_of(l, d))}</span></td>'
            f'<td class="num time">{time_str(d)}</td>'
            f'<td class="recipe-cell">{recipe_cell(l, d)}</td>'
            "</tr>"
        )
    return "\n".join(out)


def render_home(l):
    t = STR[l]
    en_url = absu("/"); zh_url = absu("/zh/")
    title = t["home_title"]; desc = t["home_desc"]
    ld = [{
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": t["site_name"],
        "url": absu("/"),
        "inLanguage": LOCALES[l]["html"],
        "description": desc,
    }, {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": t["site_name"],
        "numberOfItems": SUMMARY["count"],
        "itemListElement": [
            {"@type": "ListItem", "position": i, "name": name_of(l, d), "url": absu(item_path(l, d["slug"]))}
            for i, d in enumerate(ITEMS[:100], 1)
        ],
    }]
    head_html = head(l, title, desc, zh_url, en_url, ld)
    hero_html = hero(l, show_stats=True)
    rows = home_rows(l)
    rec_opts = "".join(f'<option value="{v}">{esc(label)}</option>' for v, label in build_sort_options(l)[0])
    eff_opts = "".join(f'<option value="{v}">{esc(label)}</option>' for v, label in build_sort_options(l)[1])
    types_opts = "".join(
        f'<option value="{esc(t)}">{esc(t)}</option>'
        for t in sorted(set(d["type"] for d in ITEMS))
    )
    types_opts_en = "".join(
        f'<option value="{esc(t)}">{esc(t)}</option>'
        for t in sorted(set(d["type_en"] for d in ITEMS))
    )
    types_options = types_opts if l == "zh" else types_opts_en
    effects_opts = "".join(
        f'<option value="{esc(e)}">{esc(e)}</option>'
        for e in sorted(set(d["effect"] for d in ITEMS))
    )
    effects_opts_en = "".join(
        f'<option value="{esc(e)}">{esc(e)}</option>'
        for e in sorted(set(d["effect_en"] for d in ITEMS))
    )
    effects_options = effects_opts if l == "zh" else effects_opts_en

    body = f"""{head_html}
<div class="stars" aria-hidden="true"></div>
{hero_html}
<main class="wrap">
  <section class="toolbar" aria-label="toolbar">
    <div class="tabs" role="tablist">
      <button class="tab active" data-view="recipe" role="tab" aria-selected="true">{t['tab_recipe']}</button>
      <button class="tab" data-view="effect" role="tab" aria-selected="false">{t['tab_effect']}</button>
    </div>
    <div class="controls">
      <div class="search">
        <span class="search-ico" aria-hidden="true">🔎</span>
        <input id="q" type="search" placeholder="{esc(t['search_ph'])}" autocomplete="off" />
        <button id="clear" class="clear" title="{esc(t['clear'])}" aria-label="{esc(t['clear_aria'])}">×</button>
      </div>
      <label class="select"><span class="sel-label">{t['label_type']}</span>
        <select id="ftype"><option value="">{t['all']}</option></select></label>
      <label class="select"><span class="sel-label">{t['label_effect']}</span>
        <select id="feffect"><option value="">{t['all']}</option></select></label>
      <label class="select" id="sortctl"><span class="sel-label">{t['label_sort']}</span>
        <select id="sort">{rec_opts}</select></label>
    </div>
  </section>
  <section class="resultbar">
    <span id="shown">0</span> / <span id="total">{SUMMARY['count']}</span> {t['results']}
    <button id="reset" class="reset">{t['reset']}</button>
  </section>
  <section class="tablecard">
    <div class="tablescroll">
      <table id="tbl">
        <thead><tr id="head">
          <th data-key="idx">#</th>
          <th data-key="name">{t['col_name']}</th>
          <th data-key="type">{t['col_type']}</th>
          <th data-key="time">{t['col_time']}</th>
          <th data-key="recipe">{t['col_recipe']}</th>
        </tr></thead>
        <tbody id="body">
{rows}
        </tbody>
      </table>
      <div id="empty" class="empty" hidden>
        <div class="empty-glyph" aria-hidden="true">🛰️</div>
        <p>{'没有符合条件的物品' if l=='zh' else 'No matching items'}</p>
        <small>{'试试清空搜索，或放宽类型 / 效果筛选' if l=='zh' else 'Clear the search or loosen the filters'}</small>
      </div>
    </div>
  </section>
{footer(l)}
</main>
<script src="/js/data.js"></script>
<script src="/js/app.js"></script>
</body>
</html>
"""
    return body


def iso_dur(total):
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    out = "PT"
    if h:
        out += f"{h}H"
    if m:
        out += f"{m}M"
    if s or not (h or m):
        out += f"{s}S"
    return out


def render_item(l, d):
    t = STR[l]
    slug = d["slug"]
    en_url = absu(f"/items/{slug}/"); zh_url = absu(f"/zh/items/{slug}/")
    name = name_of(l, d)
    other_name = d["en"] if l == "zh" else d["zh"]
    other_lang_label = t["en_name"] if l == "zh" else t["zh_name"]
    r = d["recipe"]
    if r["has"]:
        recipe_plain = " + ".join(f"{i['zh' if l=='zh' else 'en']}×{i['qty']}" for i in r["ingredients"])
    else:
        recipe_plain = howto(l, d)[2]
    title = t["item_title"].format(name=name)
    desc = t["item_desc"].format(
        name=name,
        recipe=recipe_plain,
        effect=effect_of(l, d), bonus=fmt(d["bonus"]),
        time=time_str(d), score=fmt(d["bonus_total"]))

    ld = [{
        "@context": "https://schema.org",
        "@type": "Recipe",
        "name": name,
        "alternateName": other_name,
        "description": desc,
        "url": zh_url if l == "zh" else en_url,
        "inLanguage": LOCALES[l]["html"],
        "recipeCategory": type_of(l, d),
        "cookTime": iso_dur(d["total"]),
        "recipeIngredient": ([f"{i['zh' if l=='zh' else 'en']} ×{i['qty']}" for i in r["ingredients"]] if r["has"] else []),
    }]

    head_html = head(l, title, desc, zh_url, en_url, ld)
    # back + switch links to the other locale's SAME item
    back_link = home_path(l)
    switch_item = absu(item_path(other(l), slug))

    if r["has"]:
        # 合成公式已用节点树完整展示，不再重复绿色的 recipe-box 公式文本
        variant_note = ""
        if r["variants"] > 1:
            variant_note = f'<p class="recipe-note">{esc(t["variant_all"].format(n=r["variants"]))}</p>'
        recipe_section = f"""    <section class="block recipe-sec">
      <h2>{esc(t['recipe_h'])}</h2>
      <div class="treewrap">{recipe_tree_html(l, d)}</div>
      {variant_note}
    </section>"""
    else:
        # 无需合成的基础物品：给出获取建议
        main_txt, sub_txt, _ = howto(l, d)
        recipe_section = f"""    <section class="block recipe-sec">
      <h2>{esc(t['howto_h'])}</h2>
      <div class="howto-box">
        <p class="howto-main">{esc(main_txt)}</p>
        <p class="howto-sub">{esc(sub_txt)}</p>
      </div>
    </section>"""

    body = f"""{head_html}
<div class="stars" aria-hidden="true"></div>
<header class="hero hero-compact">
  <div class="hero-inner">
    <div class="brand"><span class="glyph" aria-hidden="true">🌌</span>
      <div><h1>{esc(t['site_name'])}</h1>
      <p class="sub"><a href="{absu(back_link)}" class="crumb">{t['back']} →</a></p></div>
    </div>
    <div class="langbar">{t['lang']} <a class="lang-btn" href="{switch_item}">{LOCALES[other(l)]['label']}</a></div>
  </div>
</header>
<main class="wrap item-page">
  <article class="itemcard">
    <p class="item-kicker">{esc(type_of(l, d))}</p>
    <h1 class="item-name">{esc(name)}</h1>
    <p class="item-sub">{other_lang_label}：{esc(other_name)}</p>

{recipe_section}

    <section class="block effect-sec">
      <h2>{t['effect_h']}</h2>
      <div class="effect-grid">
        <div class="ef"><span>{t['effect_l']}</span><b>{esc(effect_of(l, d))}</b></div>
        <div class="ef"><span>{t['bonus_l']}</span><b>+{fmt(d['bonus'])}%</b></div>
        <div class="ef"><span>{t['dur_l']}</span><b>{time_str(d)}</b></div>
        <div class="ef"><span>{t['score_l']}</span><b>{fmt(d['bonus_total'])}</b></div>
      </div>
    </section>
  </article>
{footer(l)}
</main>
<script src="/js/data.js"></script>
<script src="/js/app.js"></script>
<script src="/js/slidebox.js"></script>
</body>
</html>
"""
    return body


def robots():
    return f"""User-agent: *
Allow: /

Sitemap: {absu('/sitemap.xml')}
"""


def sitemap():
    from datetime import date
    today = date.today().isoformat()
    urls = [
        (absu("/"), "1.0"),       # English (primary)
        (absu("/zh/"), "0.9"),    # Chinese
    ]
    for d in ITEMS:
        urls.append((absu(f"/items/{d['slug']}/"), "0.8"))        # English
        urls.append((absu(f"/zh/items/{d['slug']}/"), "0.7"))     # Chinese
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
             f'xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for u, p in urls:
        lines.append(f"  <url><loc>{u}</loc><lastmod>{today}</lastmod><priority>{p}</priority></url>")
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


def og_image():
    try:
        from PIL import Image, ImageDraw
    except Exception as e:  # noqa: BLE001
        print("  (skipping og-image:", e, ")")
        return
    W, H = 1200, 630
    img = Image.new("RGB", (W, H), "#0b1020")
    dr = ImageDraw.Draw(img)
    # subtle "stars"
    import random
    random.seed(7)
    for _ in range(220):
        x, y = random.randint(0, W), random.randint(0, H)
        r = random.randint(1, 2)
        dr.ellipse([x, y, x + r, y + r], fill="#3a4straight" if False else (70, 90, 150))
    dr.rectangle([0, 0, W, 96], fill="#141d33")
    dr.text((56, 30), "🌌  No Man's Sky · Nutrient Ingestor", fill="#eaf0ff")
    dr.text((56, 250), "Nutrient Ingestor", fill="#ffffff")
    dr.text((56, 330), "配方表 · 效果表 · 合成公式", fill="#9fb4ff")
    dr.text((56, 400), "575 items  ·  recipes  ·  effects  ·  score", fill="#c7d2fe")
    dr.text((56, 540), "nms.ginmel.ai", fill="#7f8db8")
    out = os.path.join(ROOT, "og-image.png")
    img.save(out)
    print("  og-image.png", os.path.getsize(out), "bytes")


def vercel_config():
    """301 redirects from the previous URL scheme (2026-09):
      - old English home   /en/     → /
      - old English items  /en/items/<slug>/ → /items/<slug>/  （新英文页）
    旧中文 URL（根路径与 /items/<slug>/）现在直接返回英文页（200），
    中文版位于 /zh/ 与 /zh/items/<slug>/，由 hreflang 互相指向。"""
    # NOTE:
    # - Vercel 59.x 的 vercel.json schema 不接受 `type: "301"`，改用 `statusCode`（301，利于 SEO）。
    # - Vercel 的 redirect 规则优先于静态文件：因此 /items/<slug>/ 必须留给新英文页（200），
    #   不能同时作为旧中文页的 301 源。旧中文 URL 现在直接返回英文页（页面内含中文切换），
    #   中文版在 /zh/items/<slug>/ 由 hreflang 指向。
    # - Vercel 59.x 为 path-to-regexp v8 语法：:splat 只匹配单段、:splat+ 匹配多段，
    #   且带尾斜杠的请求需源串同样带尾斜杠才匹配（/en/... 物品页因此用逐条精确规则）。
    redirects = [
        {"source": "/en", "destination": "/", "statusCode": 301},
        {"source": "/en/", "destination": "/", "statusCode": 301},
    ]
    redirects += [
        {"source": f"/en/items/{d['slug']}/", "destination": f"/items/{d['slug']}/", "statusCode": 301}
        for d in ITEMS
    ]
    redirects += [
        {"source": "/en/:splat+", "destination": "/:splat+", "statusCode": 301},
        {"source": "/en/:splat+/", "destination": "/:splat+/", "statusCode": 301},
    ]
    return json.dumps({"version": 2, "redirects": redirects}, ensure_ascii=False, indent=2) + "\n"


def main():
    print("building site…")
    # home pages (English primary at root, Chinese under /zh/)
    write(os.path.join(ROOT, "index.html"), render_home("en"))
    write(os.path.join(ROOT, "zh", "index.html"), render_home("zh"))

    # item pages (directory-style: items/<slug>/index.html EN, zh/items/<slug>/index.html ZH)
    for d in ITEMS:
        write(os.path.join(ROOT, "items", d["slug"], "index.html"), render_item("en", d))
        write(os.path.join(ROOT, "zh", "items", d["slug"], "index.html"), render_item("zh", d))

    # meta files
    write(os.path.join(ROOT, "robots.txt"), robots())
    write(os.path.join(ROOT, "sitemap.xml"), sitemap())
    write(os.path.join(ROOT, "vercel.json"), vercel_config())
    og_image()
    print(f"done. {SUMMARY['count']} items → {SUMMARY['count']*2+2} pages + robots + sitemap + vercel.json + og-image")


def write(path, content):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


if __name__ == "__main__":
    main()
