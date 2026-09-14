# 无人深空 · 营养摄入器（Nutrient Ingestor）

《无人深空》营养摄入器 **配方表** 与 **效果表** 的交互式中文网页。

支持：

- 🔎 **搜索**：中文名 / 英文名 / 效果名（例如 `苹果`、`Apple`、`寒冷抗性`）
- 🏷️ **类型筛选**：食用产品 / 鱼 / 原料 / 其它 12 类
- ⚡ **效果筛选**：20 种增益效果
- ↕️ **排序**：按综合分（加成 × 时长）、加成、时长、名称，点击表头亦可切换方向

## 两张表

| 视图 | 内容 |
| --- | --- |
| **配方表** | 营养摄入器可生产的 575 个物品、类型与烹饪时间 |
| **效果表** | 每个物品的增益效果、加成 %、持续时间与「加成 × 时长」综合分（越高 = buff 越强 / 越持久） |

## 数据来源

- **效果数据（权威）**：[Nutrient Ingestor 数据表（Google Sheet）](https://docs.google.com/spreadsheets/d/1oiyYjbAX_pi2drhP0vxnjI1ZG14XB8VCmr5vSBH9N7g) — 575 条物品记录。
- **中文术语**：[无人深空中文维基（nms.huijiwiki.com）](https://nms.huijiwiki.com/wiki/%E9%A6%96%E9%A1%B5) 的「食用产品 / 原料 / 产品」词条。
- 鱼类（209 条）依据官方英文原名意译，页面同时展示英文原名以便对照。

## 本地运行

纯静态页面，无需构建：

```bash
python3 -m http.server 8080
# 打开 http://127.0.0.1:8080
```

或直接双击 `index.html`。

## 重新生成数据

```bash
python3 tools/build.py   # 读取 CSV + tools/name_map.py -> js/data.js 与 data.json
```

- `tools/name_map.py`：英文 → 中文名称 / 效果 / 类型 映射表。
- `js/data.js`：由 `build.py` 生成，请勿手改。

## 目录

```
index.html            页面
style.css             样式
js/data.js            数据（生成物）
js/app.js             交互逻辑
tools/build.py        数据构建脚本
tools/name_map.py     中英映射
data.json             数据（JSON 副本）
NMS Nutrient Ingestor - Public - Nutrients.csv   原始效果数据
```
