# -*- coding: utf-8 -*-
"""Build the JSON dataset for the NMS Nutrient Ingestor web page.
Reads the authoritative CSV (effects data) + name_map (EN->ZH)
+ recipes.json (all alternative recipes) + obtain.py (bilingual acquisition
guidance for recipe-less items) -> data.json
"""
import csv, json, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from name_map import MAP, EFFECT, TYPE, ALIASES, WIKI_PAGE
from obtain import resolve as resolve_obtain
import re, unicodedata

CSV = os.path.join(os.path.dirname(__file__), "..", "NMS Nutrient Ingestor - Public - Nutrients.csv")
OUT = os.path.join(os.path.dirname(__file__), "..", "js", "data.js")
RECIPES_PATH = os.path.join(os.path.dirname(__file__), "recipes.json")
OBTAIN_RAW_PATH = os.path.join(os.path.dirname(__file__), "obtain_raw.json")


def _norm(s):
    s = unicodedata.normalize("NFKC", s).lower()
    s = re.sub(r"['\"’“”]", "", s)      # quotes
    s = re.sub(r"\(.*?\)", "", s)        # parenthetical
    s = re.sub(r"\s+", " ", s).strip()
    return s.rstrip("s")                 # naive plural


_NORMMAP = {_norm(k): k for k in MAP}


def resolve_zh(en):
    """EN ingredient name -> ZH via name_map (exact, then normalised); None if unknown."""
    if en in MAP:
        return MAP[en]
    k = _norm(en)
    if k in _NORMMAP:
        return MAP[_NORMMAP[k]]
    return None


try:
    with open(RECIPES_PATH, encoding="utf-8") as _fp:
        RECIPES = json.load(_fp)
except (FileNotFoundError, ValueError):
    RECIPES = {}

try:
    with open(OBTAIN_RAW_PATH, encoding="utf-8") as _fp:
        OBTAIN_RAW = json.load(_fp)
except (FileNotFoundError, ValueError):
    OBTAIN_RAW = {}

def num(s):
    s = s.strip().replace(",", "")
    if s == "": return 0
    try: return float(s)
    except: return 0

rows = list(csv.DictReader(open(CSV, encoding="utf-8")))
items = [r for r in rows if r["Item"].strip() and r["Effect"].strip()]

missing = [r["Item"] for r in items if r["Item"] not in MAP]
eff_missing = [r["Effect"] for r in items if r["Effect"] not in EFFECT]
typ_missing = [r["Type"] for r in items if r["Type"] not in TYPE]
print(f"items={len(items)}  missing_names={len(missing)}  missing_effects={len(set(eff_missing))}  missing_types={len(set(typ_missing))}")
if missing: print("MISSING NAMES:\n", "\n".join(missing))
if set(eff_missing): print("MISSING EFFECTS:", set(eff_missing))
if set(typ_missing): print("MISSING TYPES:", set(typ_missing))

data = []
for r in items:
    mins = int(num(r["Mins"])); secs = int(num(r["Secs"]))
    bonus = num(r["Bonus"])
    total = int(num(r["Total Sec"]))
    bonus_total = num(r["Bonus * Total Sec"])
    rc = RECIPES.get(r["Item"], {}) or {}
    # all alternative recipes (a recipe = one list of {en, zh, qty} ingredients)
    raw_variants = rc.get("recipes") or ([rc["ingredients"]] if rc.get("ingredients") else [])
    alts = []
    for variant in raw_variants:
        ings = []
        for ing in variant:
            zh = resolve_zh(ing["name"])
            ings.append({"en": ing["name"], "zh": zh or ing["name"], "qty": int(ing.get("qty", 1))})
        if ings:
            alts.append(ings)
    first = alts[0] if alts else []
    data.append({
        "en": r["Item"],
        "zh": MAP.get(r["Item"], r["Item"]),
        "type_en": r["Type"],
        "type": TYPE.get(r["Type"], r["Type"]),
        "effect_en": re.sub(r"^%\s*", "", r["Effect"]),
        "effect": EFFECT.get(r["Effect"], r["Effect"]),
        "mins": mins,
        "secs": secs,
        "bonus": bonus,
        "total": total,
        "bonus_total": bonus_total,
        "recipe": {
            "has": bool(alts),
            "variants": len(alts),
            "ingredients": first,          # first recipe (compat / display default)
            "alts": alts,                  # ALL alternative recipes
        },
        # 获取建议：无配方物品的逐物品双语指引（原料/鱼/特殊物品）；有配方为 null
        "obtain": (resolve_obtain(r["Item"], r["Type"] == "Fish", OBTAIN_RAW.get(r["Item"])) if not alts else None),
    })

# stable sort by bonus_total desc as default
data.sort(key=lambda d: (-d["bonus_total"], d["zh"]))


def slugify(en):
    s = unicodedata.normalize("NFKD", en)
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s)
    s = re.sub(r"^-+|-+$", "", s).lower()
    return s or "item"


_seen = {}
for _d in data:
    _base = slugify(_d["en"])
    if _base not in _seen:
        _seen[_base] = 1
        _d["slug"] = _base
    else:
        _seen[_base] += 1
        _d["slug"] = f"{_base}-{_seen[_base]}"

summary = {
    "count": len(data),
    "types": sorted(set(d["type"] for d in data)),
    "effects": sorted(set(d["effect"] for d in data)),
    "recipes": sum(1 for d in data if d["recipe"]["has"]),
}
# aliases/wiki：供前端 recipe 表格把"无物品页"原料解析为内链/维基外链
# （与 tools/build_site.py 的服务端渲染保持一致）
payload = {"summary": summary, "data": data, "aliases": ALIASES, "wiki": WIKI_PAGE}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
# also keep a plain JSON copy
json.dump(payload, open(os.path.join(os.path.dirname(__file__), "..", "data.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
# write as an inlineable JS global (robust for file:// and any static host)
with open(OUT, "w", encoding="utf-8") as f:
    f.write("// Auto-generated by tools/build.py — do not edit by hand.\n")
    f.write("window.NMS = ")
    f.write(json.dumps(payload, ensure_ascii=False))
    f.write(";\n")
print("wrote", OUT, os.path.getsize(OUT), "bytes")
