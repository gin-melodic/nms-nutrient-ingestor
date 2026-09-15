# 无人深空 · 营养摄入器（No Man's Sky · Nutrient Ingestor）

《无人深空》营养摄入器（外骨骼进食科技）**配方表 · 效果表 · 合成公式** 的双语（中/英）静态网站，面向 SEO 优化。

线上地址：<https://nms.ginmel.ai/>（**英文为主域名**，中文在 `nms.ginmel.ai/zh/` 路径下）。

## 特性

- **双语 + 语言切换按钮**：英文为主（`/`），中文页使用 `/zh/` 路径，每页单一语言、不混排，右上角可一键切换（含物品页的同名对照链接）。旧英文 URL（`/en/`、`/en/items/<slug>/`）通过 `vercel.json` 301 重定向到新的英文地址；旧的中文 URL（根路径与 `/items/<slug>/`）现在直接返回英文页，中文版在 `/zh/` 对应路径，页面间经语言按钮与 hreflang 互相指向。
- **合成公式**：配方表新增「合成公式 / Recipe」列，展示每种食物的原料配方（例如 `'Apple' Ice Cream = 粘蛋奶沙司 + 冷冻块茎 + 蟹肉“苹果”`）；多配方会标注「N 种配方」；无配方物品标注「🎣 捕捞」或「无配方」。
- **节点图（物品页）**：物品详情页的「合成公式 / Recipe」区块以**完整展开的节点树**展示合成链（根 = 当前物品，向下逐级展开所有原料，全库最深 6 层），节点带类型图标与类型配色（食用 🍽️ / 鱼 🐟 / 原料 🌿）；**所有原料节点均可点击**，不跳转页面、而是从右侧**滑出 Slidebox 面板**展示该物品的完整详情（合成树 + 增益效果），并在面板内继续点击子节点逐层深入、`←` 返回、`Esc`/点遮罩关闭、`↗` 新标签页打开（`js/slidebox.js`）；无物品页的原料（如 Salt）显示「无物品页」标记，递归配方（如甜甜圈↔面团链）显示 `↻ 递归` 标记不再展开；树为纯服务端渲染（利于 SEO），无 JS 时节点保持原生跳转（渐进增强），窄屏可横向滚动。**有配方的物品不再重复显示绿色公式文本框**（节点树即完整公式），多配方物品保留「N 种配方」提示。
- **获取建议（物品页）**：**无需合成的基础物品**不再只写「无配方」，而是按类型给出获取建议——鱼 🎣 钓鱼（任意星球水域）、原料 🌿 采集（行星表面 / 生物掉落）、其余 🧭 世界中直接获取；首页配方表的无配方行同步显示「🎣 捕捞 / 🌿 采集」。
- **两个视图**：
  | 视图 | 内容 |
  | --- | --- |
  | **配方表** | 575 个物品、类型、烹饪时间、**合成公式** |
  | **效果表** | 每个物品的增益效果、加成 %、持续时间、综合分（加成 × 时长，越高 = buff 越强 / 越持久） |
- **搜索 / 筛选 / 排序**：搜索（中英名称、效果）、类型筛选（12 类）、效果筛选（20 类）、多字段排序（表头可点切换方向）。
- **物品详情页**：每个物品独立的中文页 + 英文页，含**合成节点图**（可点击原料树）、合成公式、增益、加成、时长、综合分。

## SEO

- 每页完整 `<head>`：`title`、`meta description`、`canonical`、`hreflang`（x-default / zh / en）、Open Graph（含 `og:locale`）、Twitter Card。
- **JSON-LD 结构化数据**：首页 `WebSite` + `ItemList`；物品页 `schema.org Recipe`（`recipeIngredient`、`cookTime`、`recipeCategory` 等）。
- `robots.txt`、`sitemap.xml`（1152 个 URL）、`og-image.png`。
- 首页表格内容**服务端预渲染**（不依赖 JS 即可被爬虫抓取），JS 负责交互增强。

## 数据来源

- **效果数据（权威）**：[Nutrient Ingestor 数据表（Google Sheet）](https://docs.google.com/spreadsheets/d/1oiyYjbAX_pi2drhP0vxnjI1ZG14XB8VCmr5vSBH9N7g) — 575 条物品记录。
- **合成公式**：[NMS Fandom Wiki](https://nomanssky.fandom.com/) MediaWiki API 的 `{{Cook}}/{{Craft}}` 模板（`tools/scrape_recipes.py` 抓取 → `tools/recipes.json`）。
- **中文术语**：[无人深空中文维基（nms.huijiwiki.com）](https://nms.huijiwiki.com/wiki/%E9%A6%96%E9%A1%B5) 及社区词条。

## 构建流程

```bash
# 1) （可选）重新抓取合成公式
python3 tools/scrape_recipes.py     # Fandom API -> tools/recipes.json
# 2) 数据构建：CSV + name_map + recipes.json -> js/data.js 与 data.json
python3 tools/build.py
# 3) 站点生成：data.json -> index.html(EN) / zh/ / items/(EN) / zh/items/(ZH) / vercel.json / robots.txt / sitemap.xml / og-image.png
python3 tools/build_site.py
```

## 本地运行

```bash
python3 tools/build.py && python3 tools/build_site.py   # 生成站点
python3 -m http.server 8080                              # 打开 http://127.0.0.1:8080
```

## 部署

**推荐：推送到 GitHub 自动部署。** 向 `master` 分支提交后，`.github/workflows/vercel-deploy.yml` 会自动重建站点并部署到 Vercel 生产环境（`nms.ginmel.ai`）：

```bash
python3 tools/build.py && python3 tools/build_site.py   # 本地生成
git add -A && git commit -m "…" && git push origin master  # 触发自动部署
```

仓库需配置 Secret：`VERCEL_TOKEN`（Vercel 个人访问令牌）。

> 也可在本地用 Vercel CLI 手动部署：`vercel link --yes --project nms-nutrient-ingestor --team team_…` 后 `vercel deploy --prod --yes --archive=tgz`。

## 目录

```
index.html                              英文首页（生成物，主域名）
zh/index.html                           中文首页（生成物，/zh/ 路径）
items/<slug>/index.html                 英文物品页（生成物，575 个）
zh/items/<slug>/index.html              中文物品页（生成物，575 个）
style.css                               样式
js/app.js                               交互逻辑（感知 data-locale）
js/data.js                              数据（生成物，window.NMS）
data.json                               数据（JSON 副本）
vercel.json                             旧 URL 301 重定向（生成物）
robots.txt / sitemap.xml / og-image.png SEO（生成物）
tools/build.py                          数据构建脚本
tools/build_site.py                     站点生成脚本
tools/scrape_recipes.py                 合成公式抓取脚本
tools/name_map.py                       英文 → 中文 名称 / 效果 / 类型 映射
tools/recipes.json                      抓取到的合成公式（按物品名）
NMS Nutrient Ingestor - Public - Nutrients.csv   原始效果数据
```

> 注意：`js/data.js`、`data.json`、`index.html`、`zh/`、`items/`、`vercel.json`、`robots.txt`、`sitemap.xml`、`og-image.png` 均为**生成物**，请勿手改；改动请改源头（CSV / `name_map.py` / `recipes.json` / `tools/build_site.py`）后重跑 `tools/build.py` 与 `tools/build_site.py`。
