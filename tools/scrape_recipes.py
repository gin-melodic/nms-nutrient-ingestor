# -*- coding: utf-8 -*-
"""Scrape crafting recipes (合成公式) for every NMS Nutrient Ingestor item.

Source: No Man's Sky Fandom wiki (MediaWiki API), which documents each item's
crafting recipe via the {{Cook}} / {{Craft}} templates in its Source section.

The wiki lists every alternative recipe as a separate template line, e.g.
    {{Cook|Warm Proto-Milk,1;1;2.5%Churn|Craw Milk,1;1;2.5%Churn}}
All variants are captured.

Reads data.json (the 575-item dataset) and writes tools/recipes.json:
    { "<Item EN name>": {
        "title": "<resolved Fandom page title>",
        "has_recipe": bool,
        "variants":   <int number of alternative recipes>,
        "recipes": [ [{"name": "<EN ingredient>", "qty": <int>}, ...], ... ]
    } }

Re-runnable one-time build step. Uses a small worker pool + retries + backoff
to be polite to the API.
"""
import urllib.request, urllib.parse, json, re, time, os
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
API = "https://nomanssky.fandom.com/api.php"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recipes.json")


def get(url, tries=4):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(1.0 * (i + 1))
    raise last


def fetch_wikitext(title):
    url = (f"{API}?action=parse&page={urllib.parse.quote(title)}"
           "&format=json&prop=wikitext&redirects=1")
    d = json.loads(get(url))
    return d.get("parse", {}).get("wikitext", {}).get("*", "")


def opensearch(q):
    url = f"{API}?action=opensearch&search={urllib.parse.quote(q)}&limit=5&format=json"
    d = json.loads(get(url))
    return d[1] if len(d) > 1 else []


def parse_recipe_line(seg):
    """Parse one recipe variant like 'Viscous Custard,1;Frozen Tubers,1;...;1;2.5%X'."""
    ings = []
    for f in seg.split(";"):
        f = f.strip()
        m = re.match(r"^(.*),(\d+)$", f)
        if m and m.group(1).strip():
            ings.append({"name": m.group(1).strip(), "qty": int(m.group(2))})
    return ings


def extract(wt):
    """Return ALL alternative recipes (each a list of {name, qty})."""
    m = re.search(r"\{\{(Cook|Craft)\b(.*?)\}\}", wt, re.S)
    if not m:
        return {"has_recipe": False, "recipes": [], "variants": 0}
    recipes = []
    for s in re.split(r"[\n\|]", m.group(2)):
        s = s.strip()
        if not s or s.startswith("blueprint"):
            continue
        ings = parse_recipe_line(s)
        if ings:
            recipes.append(ings)
    return {"has_recipe": bool(recipes), "recipes": recipes, "variants": len(recipes)}


def process(name):
    title, wt, used = name, "", ""
    try:
        wt = fetch_wikitext(name)
        used = name
    except Exception:  # noqa: BLE001
        wt = ""
    if not wt:  # fallback: opensearch the closest page
        try:
            for h in opensearch(name):
                try:
                    wt = fetch_wikitext(h)
                    used = h
                    break
                except Exception:  # noqa: BLE001
                    continue
        except Exception:  # noqa: BLE001
            pass
    return name, {"title": used, **extract(wt)}


def main():
    data = json.load(open(os.path.join(ROOT, "data.json"), encoding="utf-8"))["data"]
    names = [d["en"] for d in data]
    out, done = {}, 0
    with ThreadPoolExecutor(max_workers=6) as ex:
        futs = {ex.submit(process, n): n for n in names}
        for f in as_completed(futs):
            name, res = f.result()
            out[name] = res
            done += 1
            if done % 100 == 0:
                print(f"  {done}/{len(names)}", flush=True)
    with open(OUT, "w", encoding="utf-8") as fp:
        json.dump(out, fp, ensure_ascii=False, indent=1)

    # ---- analysis ----
    with_recipe = [k for k, v in out.items() if v["has_recipe"]]
    ings = set()
    for v in out.values():
        for r in v.get("recipes", []):
            for ing in r:
                ings.add(ing["name"])
    multiv = [(k, v["variants"]) for k, v in out.items() if v["variants"] > 1]
    try:
        import sys
        sys.path.insert(0, os.path.join(ROOT, "tools"))
        from name_map import MAP
        keys = set(MAP.keys())
        missing = sorted(x for x in ings if x not in keys)
        print(f"ingredients: {len(ings)} unique, {len(missing)} not yet in name_map")
    except Exception:  # noqa: BLE001
        missing = []
    print("=" * 48)
    print(f"total={len(out)}  with_recipe={len(with_recipe)}  "
          f"without={len(out) - len(with_recipe)}")
    print(f"multi_variant_items={len(multiv)}  "
          f"max_variants={max((v for _, v in multiv), default=0)}")
    print(f"unique_ingredients={len(ings)}")
    if missing:
        print("missing_zh:", missing)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
