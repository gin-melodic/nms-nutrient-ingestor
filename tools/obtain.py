# -*- coding: utf-8 -*-
"""Bilingual acquisition (获取方式) guidance for recipe-less items.

Sources:
  - RAW: hand-curated per-item text (bilingual), based on the "Source"
    sections of No Man's Sky Fandom wiki pages (raw dump: tools/obtain_raw.json).
  - Fish: generated from structured {{FishingCon}} / {{FishingBait}} data in
    tools/obtain_raw.json (biome / time / weather / bait rarity+size bonuses).

Public API:
    resolve(en_name, is_fish, entry) -> {"en": str, "zh": str} | None
      en_name : dataset item name (EN, exact)
      is_fish : True when the dataset types the item as "Fish"
      entry   : the item's record from tools/obtain_raw.json (or None)
Returns None when no per-item guidance is available (caller falls back to
the generic per-type how-to text).
"""

# --------------------------------------------------------------------------
# Curated raw-ingredient / special-item guidance (key = dataset EN name)
# --------------------------------------------------------------------------
RAW = {
    # ---- wild plants (planet class) ----
    "Jade Peas": {
        "zh": "在有毒星球（toxic）的水域或地表采集野生植物获得。",
        "en": "Harvested from wild plants on toxic planets."},
    "Fireberry": {
        "zh": "在焦土星球（scorched）上采集野生植物获得。",
        "en": "Harvested from wild plants on scorched planets."},
    "Aloe Flesh": {
        "zh": "在荒芜星球（barren）上采集野生植物获得。",
        "en": "Harvested from wild plants on barren planets."},
    "Grahberry": {
        "zh": "在辐射星球（irradiated）上采集野生植物获得。",
        "en": "Harvested from wild plants on irradiated planets."},
    "Impulse Beans": {
        "zh": "在肥沃星球（lush）上采集野生植物获得。",
        "en": "Harvested from wild plants on lush planets."},
    "Frozen Tubers": {
        "zh": "在冰冻星球（frozen）上采集野生植物获得。",
        "en": "Harvested from wild plants on frozen planets."},
    "Hexaberry": {
        "zh": "在异域星球（exotic）上采集野生植物获得；异域星球的部分生物（含异常生物）也能采集到。",
        "en": "Harvested from wild plants on exotic planets; some fauna there (including anomalous creatures) also yield it."},
    "Heptaploid Wheat": {
        "zh": "几乎所有星球（除死亡星球外）的野生植物上均可采集。",
        "en": "Harvested from wild plants on virtually all (non-dead) planets."},
    "Pulpy Roots": {
        "zh": "几乎所有星球（除死亡星球外）的野生植物上均可采集。",
        "en": "Harvested from wild plants on virtually all (non-dead) planets."},
    "Sweetroot": {
        "zh": "几乎所有星球（除死亡星球外）的野生植物上均可采集。",
        "en": "Harvested from wild plants on virtually all (non-dead) planets."},
    "Bone Cheese": {
        "zh": "基础原料：在星球地表采集野生原料或从生物身上获取。",
        "en": "A base raw ingredient gathered from planet surfaces or creatures."},

    # ---- animal byproducts: feed creatures, then gather ----
    "Crab 'Apple'": {
        "zh": "对蜘蛛形或蟹形生物（Bos、Conokinis、Bosaquatica）投喂生物颗粒（Creature Pellets）后，从其身上采集。",
        "en": "Gathered from spider- or crab-like creatures (Bos, Conokinis, Bosaquatica) after feeding them Creature Pellets."},
    "Warm Proto-Milk": {
        "zh": "对双足人形生物（Mogara，原型人）投喂生物颗粒后，从其乳袋中采集。",
        "en": "Gathered from the milk sacs of bipedal humanoid creatures (Mogara) after feeding them Creature Pellets."},
    "Sticky Honey": {
        "zh": "对团块生物（Lok）投喂生物颗粒后采集；部分星球的植物也含有。",
        "en": "Gathered from blob-type creatures (Lok) after feeding them Creature Pellets; some plants also contain it."},
    "Syrupy Nectar": {
        "zh": "对花形生物（Floradae）投喂生物颗粒后采集，或将其击杀（cull）获得。",
        "en": "Gathered from flower-type creatures (Floradae) after feeding them Creature Pellets, or obtained by culling them."},
    "Leopard-Fruit": {
        "zh": "对猫科生物（Felidae、Felihex）投喂生物颗粒后采集。",
        "en": "Gathered from cat-like creatures (Felidae, Felihex) after feeding them Creature Pellets."},
    "Foraged Mushrooms": {
        "zh": "对龟形或鼹鼠形生物（Talpidae）投喂生物颗粒后采集；此类生物无法手动投喂，建议使用自动喂食装置。",
        "en": "Gathered from turtle- or mole-like creatures (Talpidae) after feeding them Creature Pellets; an automated feeding setup is recommended since they cannot be fed manually."},
    "Tall Eggs": {
        "zh": "对巨像（Anastomus，水栖双足大型生物）投喂生物颗粒后采集。",
        "en": "Gathered from striders (Anastomus) after feeding them Creature Pellets."},
    "Fresh milk": {
        "zh": "对牛形生物（Ungulatis、Hexungulatis）投喂生物颗粒后采集；无脂肪圆臀可与啮齿类（Procavya）区分。",
        "en": "Gathered from cow-like creatures (Ungulatis, Hexungulatis) after feeding them Creature Pellets; tell them apart from rodents (Procavya) by the lack of fat round bottoms."},
    "Giant Egg": {
        "zh": "对双足龙（Rangifae）投喂生物颗粒后采集。",
        "en": "Gathered from diplos (Rangifae) after feeding them Creature Pellets."},
    "Chewy Wires": {
        "zh": "对机器人形生物（Mechanoceris、Structurae）投喂离子电池（Ion Batteries）后采集。",
        "en": "Gathered from robotic creatures (Mechanoceris, Structurae) after feeding them Ion Batteries."},
    "Bone Nuggets": {
        "zh": "对大型甲壳生物（Osteofelidae）或原型滚动者（Protosphaeridae）投喂生物颗粒后采集。",
        "en": "Gathered from large shelled creatures (Osteofelidae) and protorollers (Protosphaeridae) after feeding them Creature Pellets."},
    "Creature Egg": {
        "zh": "对三角龙形生物（Theroma）投喂生物颗粒后采集。",
        "en": "Gathered from triceratops-like creatures (Theroma) after feeding them Creature Pellets."},
    "Wild Milk": {
        "zh": "对羚羊形生物（Tetraceris、Reococcyx）或啮齿类（Procavya）投喂生物颗粒后采集。",
        "en": "Gathered from antelope-like creatures (Tetraceris, Reococcyx) and rodents (Procavya) after feeding them Creature Pellets."},
    "Craw Milk": {
        "zh": "对大型蝴蝶（Rhopalocera）、飞虫（Bosoptera）或原型飞虫（Protocaeli）投喂生物颗粒后采集。",
        "en": "Gathered from large butterflies (Rhopalocera), flying beetles (Bosoptera) or protoflyers (Protocaeli) after feeding them Creature Pellets."},
    "Fiendish Roe": {
        "zh": "在异域星球上，对滚轮形异常生物（Anomalous）投喂生物颗粒后采集。",
        "en": "Gathered from roller-type anomalous creatures (Anomalous) on exotic planets after feeding them Creature Pellets."},
    "Regis Grease": {
        "zh": "对双足暴龙形生物（Tyranocae）投喂生物颗粒后采集。",
        "en": "Gathered from bipedal t-rex-like creatures (Tyranocae) after feeding them Creature Pellets."},

    # ---- obtained by killing creatures ----
    "Dirty Meat": {
        "zh": "击杀犁地虫（Prionterrae）或原型挖掘者（Prototerrae）获得。",
        "en": "Obtained by killing ploughs (Prionterrae) or protodiggers (Prototerrae)."},
    "Feline Liver": {
        "zh": "击杀猫科生物（Felidae、Felihex）获得。",
        "en": "Obtained by killing cat-like creatures (Felidae, Felihex)."},
    "Raw Steak": {
        "zh": "击杀陆生牛形生物（Ungulatis、Hexungulatis）获得。",
        "en": "Obtained by killing terrestrial cow-like creatures (Ungulatis, Hexungulatis)."},
    "Meaty Wings": {
        "zh": "击杀鸟类（Agnelis）、飞蜥（Cycromys）或大型蝴蝶（Rhopalocera）获得。",
        "en": "Obtained by killing bird-like creatures (Agnelis), flying lizards (Cycromys) or large butterflies (Rhopalocera)."},
    "Lumpy Brainstem": {
        "zh": "击杀原型滚动者（Protosphaeridae）获得。",
        "en": "Obtained by killing protorollers (Protosphaeridae)."},
    "Strider Sausage": {
        "zh": "击杀巨像（Anastomus）获得。",
        "en": "Obtained by killing striders (Anastomus)."},
    "Scaly Meat": {
        "zh": "击杀双足暴龙形生物（Tyranocae）获得。",
        "en": "Obtained by killing bipedal t-rex-like creatures (Tyranocae)."},
    "Salty Chunks": {
        "zh": "击杀鱼类（Ictaloris）或鲨鱼（Prionace）获得。",
        "en": "Obtained by killing fish (Ictaloris) or sharks (Prionace)."},
    "Crystal Flesh": {
        "zh": "击杀 Osteofelidae 属大型甲壳生物获得。",
        "en": "Obtained by killing large shelled creatures of the Osteofelidae genus."},
    "Offal Sac": {
        "zh": "击杀团块生物（Lok）获得。",
        "en": "Obtained by killing blob-like creatures (Lok)."},
    "ProtoSausage": {
        "zh": "击杀双足人形生物（Mogara，原型人）获得。",
        "en": "Obtained by killing bipedal humanoid creatures (Mogara)."},
    "Scooped Innards": {
        "zh": "击杀龟形或鼹鼠形生物（Talpidae）获得。",
        "en": "Obtained by killing turtle- or mole-like creatures (Talpidae)."},
    "Crunchy Wings": {
        "zh": "击杀飞虫（Bosoptera）或原型飞虫（Protocaeli）获得。",
        "en": "Obtained by killing flying beetles (Bosoptera) or protoflyers (Protocaeli)."},
    "Rancid Flesh": {
        "zh": "击杀生物恐怖（Biological Horror）获得。",
        "en": "Rewarded by killing Biological Horrors."},
    "Juicy Thorax": {
        "zh": "击杀节肢生物（Arthropodae）获得。",
        "en": "Obtained by killing Arthropodae."},
    "Latticed Sinew": {
        "zh": "击杀穴居生物（Burrowing Creatures）获得。",
        "en": "Obtained by killing Burrowing Creatures."},
    "Diplo Chunks": {
        "zh": "击杀双足龙（Rangifae）获得。",
        "en": "Obtained by killing Rangifae-based diplos."},
    "Leg Meat": {
        "zh": "击杀蜘蛛形或蟹形生物（Bos、Conokinis、Bosaquatica）获得。",
        "en": "Obtained by killing spider- or crab-like creatures (Bos, Conokinis, Bosaquatica)."},
    "Juicy Grub": {
        "zh": "从多汁幼虫（Juicy Grub）身上直接采集获得。",
        "en": "Harvested directly from Juicy Grubs."},

    # ---- fossils / special drops ----
    "Fossilised [Something]": {
        "zh": "作为化石类物品从星球地表收集；详见维基「Collecting Fossils」页面。",
        "en": "Collected as a fossil from planet surfaces; see the 'Collecting Fossils' wiki page for details."},
    "Hadal Core": {
        "zh": "击杀深渊噩梦（Abyssal Horror）或采集诱人标本（Alluring Specimen，每次采集可能触发深渊噩梦）获得；也可在废弃飞船容器、水下遗物和可疑包裹中找到。",
        "en": "Dropped by Abyssal Horrors or harvested from Alluring Specimens (each harvest risks spawning an Abyssal Horror); also found in derelict freighter containers, submerged relics and suspicious packs."},
    "Hypnotic Eye": {
        "zh": "击杀深渊噩梦（Abyssal Horror）后尽快拾取（数秒内不拾取会消失）；也可在废弃飞船容器中找到，或拆除活体飞船上的「嫁接之眼」升级（得 2 个）。",
        "en": "Drops when an Abyssal Horror is killed (pick it up within a few seconds); also found in derelict freighter containers, and scrapping a Grafted Eyes upgrade on your living ship yields 2."},
    "Larval Core": {
        "zh": "用飞船武器摧毁低语之卵（Whispering Eggs）获得（不会刷出生物恐怖）；也可在巢穴附近建基地围堵采集。",
        "en": "Harvested by destroying Whispering Eggs with starship weapons (spawns no Biological Horrors); bases near the nests can also wall in and harvest them."},
    "GekNip": {
        "zh": "在受损容器、巨石奖励或交易站商人处获得；也可能是护卫舰远征奖励，或脉冲引擎漫游商人处购得。",
        "en": "Found in damaged containers or as monolith rewards, bought from trading post NPCs, or awarded from frigate expeditions and Pulse-Engine wandering traders."},
    "Nip Nip Buds": {
        "zh": "主要通过星球采集获得；也可在不法星系、空间站废品商人、废弃飞船容器、枢纽任务奖励或星球黑市（纳币购买）等途径获得。",
        "en": "Primarily harvested from planets; also available in outlaw systems, from space station scrap dealers, derelict freighter containers, Nexus mission rewards and black-market traders."},
    "Flesh Rope": {
        "zh": "在感染星球的泰坦蠕虫洞穴（Titan Worm Burrow）中，从巨型泰坦蠕虫身上采集；泰坦蠕虫现身极短暂，仅特定事件时较易获得。",
        "en": "Gathered from giant Titan Worms in Titan Worm Burrows on infested planets; they are rarely spotted and only for a few seconds, so events are the reliable source."},
}

# --------------------------------------------------------------------------
# Fish guidance, generated from {{FishingCon}}/{{FishingBait}} data
# --------------------------------------------------------------------------
BIOME_ZH = {
    "frozen": "冰冻", "lush": "肥沃", "barren": "荒芜", "scorched": "焦土",
    "irradiated": "辐射", "toxic": "有毒", "mega exotic": "超异域",
    "Gas Giant": "气态巨行星", "waterworld": "水世界",
}
TIME_ZH = {"night": "夜间", "day": "白天", "storm": "风暴天气"}


def _bait_phrase(f):
    r, s = f.get("bait_rarity"), f.get("bait_size")
    zh, en = [], []
    if r is not None:
        zh.append(f"稀有度加成约 {r}%")
        en.append(f"~{r}% catch-rarity improvement")
    if s is not None:
        zh.append(f"体型加成约 {s}%")
        en.append(f"~{s}% catch-size improvement")
    if not zh:
        return None, None
    return "推荐鱼饵：" + "、".join(zh), "Bait: use a lure with " + " and ".join(en)


def fish_text(entry):
    """Bilingual fishing guidance for one fish, or None when the page gave
    no structured data."""
    f = entry.get("fish") or {}
    if not any([f.get("biome"), f.get("time"), f.get("weather"), f.get("any"),
                f.get("bait_rarity") is not None, f.get("bait_size") is not None]):
        return None
    where_zh = f"{BIOME_ZH.get(f['biome'], f['biome'])}星球" if f.get("biome") else "任意星球"
    where_en = f"on {' '.join(w.capitalize() for w in f['biome'].split())} planets" if f.get("biome") else "on any planet"
    when_zh, when_en = [], []
    if f.get("time") in TIME_ZH:
        when_zh.append(TIME_ZH[f["time"]])
        when_en.append({"night": "at night", "day": "during the day", "storm": "during storms"}[f["time"]])
    if f.get("weather") == "storm" and f.get("time") != "storm":
        when_zh.append("风暴天气")
        when_en.append("during storms")
    zh = f"用鱼竿在{where_zh}的水域钓鱼即可钓获" + ("（" + "、".join(when_zh) + "）" if when_zh else "") + "。"
    en = f"Caught by fishing in water {where_en}" + (f" ({', '.join(when_en)})" if when_en else "") + "."
    bz, be = _bait_phrase(f)
    if bz:
        zh += bz + "。"
        en += " " + be + "."
    return {"zh": zh, "en": en}


def resolve(en_name, is_fish, entry):
    """Pick the guidance for a recipe-less item. See module docstring."""
    if en_name in RAW:
        return RAW[en_name]
    if is_fish and entry:
        return fish_text(entry)
    return None
