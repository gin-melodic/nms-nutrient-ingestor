# -*- coding: utf-8 -*-
"""Scrape "how to obtain" details for every recipe-less NMS item.

Source: No Man's Sky Fandom wiki (MediaWiki API). For each item in data.json
that has no crafting recipe (fish / raw ingredients / special items) we pull:

  - the ``==Source==`` section text (where the item comes from: planet biome,
    creatures, byproduct feeding, refining, trade terminals, …),
  - ``{{PoC-Refine…}}`` refine recipes if present (e.g. Salt),
  - for fish: ``{{FishingCon|…}}`` (biome / time / weather) and
    ``{{FishingBait|rarity,size,condition}}`` (bait attributes that attract it).

Writes tools/obtain_raw.json:
    { "<Item EN name>": {
        "page": "<resolved Fandom page title>" | "",
        "source": "<cleaned source text>" | "",
        "refine": [{"name","qty"}, ...],
        "fish": {"biome","time","weather","bait_rarity","bait_size","bait_condition"} | null
    } }

One-time (re-runnable) step; output feeds the bilingual curation in
tools/obtain.py via tools/build.py. Uses a worker pool + retries + backoff.
"""
import urllib.request, urllib.parse, json, re, time, os
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
API = "https://nomanssky.fandom.com/api.php"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "obtain_raw.json")


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


def clean_wt(s):
    """Strip wikimarkup down to readable text (keep link labels, drop templates/files)."""
    if not s:
        return ""
    s = re.sub(r"<gallery>.*?</gallery>", "", s, flags=re.S)
    s = re.sub(r"\[\[File:.*?\]\]", "", s, flags=re.S)
    s = re.sub(r"\[\[Category:.*?\]\]", "", s, flags=re.S)
    s = re.sub(r"\[\[[^\]|]*\|([^\]]*)\]\]", r"\1", s)   # [[Page|Label]] -> Label
    s = re.sub(r"\[\[([^\]]*)\]\]", r"\1", s)             # [[Page]] -> Page
    s = re.sub(r"\{\{[^{}]*\}\}", " ", s)                  # simple templates
    s = re.sub(r"''+", "", s)
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{2,}", "\n", s)
    return s.strip()


def parse_recipe_line(seg):
    """Parse one recipe/refine line like 'Chlorine,1;2;0.24%Salt Production'."""
    ings = []
    for f in seg.split(";"):
        f = f.strip()
        m = re.match(r"^(.*),(\d+)$", f)
        if m and m.group(1).strip():
            ings.append({"name": m.group(1).strip(), "qty": int(m.group(2))})
    return ings


def template_params(wt, name):
    """Find {{name|…}} and return {key: value} (case-insensitive keys)."""
    m = re.search(r"\{\{\s*" + re.escape(name) + r"\b(.*?)\}\}", wt, re.S)
    if not m:
        return None
    out = {}
    for part in m.group(1).split("|"):
        part = part.strip()
        if not part:
            continue
        if "=" in part:
            k, v = part.split("=", 1)
            out[k.strip().lower()] = v.strip()
        else:
            out.setdefault("pos", part)
    return out


def extract(wt, is_fish):
    res = {"source": "", "refine": [], "fish": None}
    # Source section (heading may be 'Source', ' Source', '= Source', …)
    m = re.search(r"^\s*=+\s*Source\s*=*\s*$(.*?)(?=\n\s*=+|\Z)", wt, re.S | re.I | re.M)
    if m:
        res["source"] = clean_wt(m.group(1))
    # refine recipes
    for m in re.finditer(r"\{\{\s*PoC-?Refine\b(.*?)\}\}", wt, re.S | re.I):
        for s in re.split(r"[\n\|]", m.group(1)):
            s = s.strip()
            if not s:
                continue
            ings = parse_recipe_line(s)
            if ings:
                res["refine"].extend(ings)
    # fishing data — fish pages only (the {{FishingBait}} template on
    # raw-ingredient pages describes what the bait *attracts*, not how to
    # obtain the item)
    fc = fb = None
    if is_fish:
        fc = template_params(wt, "FishingCon")
        fb = template_params(wt, "FishingBait")
    if fc is not None or fb is not None:
        def _num(v):
            try:
                return int(float(v))
            except (TypeError, ValueError):
                return None
        res["fish"] = {
            "biome": (fc or {}).get("biome", "") if fc else "",
            "time": (fc or {}).get("time", "") if fc else "",
            "weather": (fc or {}).get("weather", "") if fc else "",
            "any": bool((fc or {}).get("pos", "") == "any") if fc else False,
            "bait_rarity": _num((fb or {}).get("rarity")) if fb else None,
            "bait_size": _num((fb or {}).get("size")) if fb else None,
            "bait_condition": (fb or {}).get("condition", "") if fb else "",
        }
    return res


def process(name, is_fish):
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
    if not wt:
        return name, {"page": "", "source": "", "refine": [], "fish": None}
    return name, {"page": used, **extract(wt, is_fish)}


def main():
    data = json.load(open(os.path.join(ROOT, "data.json"), encoding="utf-8"))["data"]
    targets = [(d["en"], d["type_en"] == "Fish") for d in data if not d["recipe"]["has"]]
    out, done = {}, 0
    with ThreadPoolExecutor(max_workers=6) as ex:
        futs = {ex.submit(process, n, f): n for n, f in targets}
        for f in as_completed(futs):
            name, res = f.result()
            out[name] = res
            done += 1
            if done % 25 == 0:
                print(f"  {done}/{len(targets)}", flush=True)
    with open(OUT, "w", encoding="utf-8") as fp:
        json.dump(out, fp, ensure_ascii=False, indent=1)

    # ---- analysis ----
    with_page = [k for k, v in out.items() if v["page"]]
    with_src = [k for k, v in out.items() if v["source"]]
    with_fish = [k for k, v in out.items() if v["fish"]]
    print("=" * 48)
    print(f"targets={len(out)}  with_page={len(with_page)}  "
          f"with_source={len(with_src)}  with_fishing_data={len(with_fish)}")
    print("no page:", sorted(k for k in out if not out[k]["page"]))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
