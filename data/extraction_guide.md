# ISSCC 2026 论文数据提取指南 (Metric List)

> 本文档完整描述了从 ISSCC 2026 Session PDF 中提取论文数据并构建 `papers.json` 的全流程，
> 使第三方可以独立复现整个数据提取过程。

---

## 目录

1. [ISSCC 论文 PDF 结构说明](#1-isscc-论文-pdf-结构说明)
2. [完整字段列表](#2-完整字段列表)
3. [提取方法详解](#3-提取方法详解)
4. [各 Session 论文特点](#4-各-session-论文特点)
5. [JSON Schema 定义](#5-json-schema-定义)
6. [常见陷阱与注意事项](#6-常见陷阱与注意事项)

---

## 1. ISSCC 论文 PDF 结构说明

### 1.1 PDF 文件组织

每个 Session 对应一个 PDF 文件（如 `session2.pdf`），包含该 Session 全部论文。

### 1.2 每篇论文的页面结构

每篇论文固定占 **3 页**：

| 页码 | 内容 | 布局 |
|------|------|------|
| 第 1 页 | 正文（摘要 + 全文） | 双栏排版 |
| 第 2 页 | Figure 1–4（概念/架构图） | 2×2 网格 |
| 第 3 页 | Figure 5–7（细节 + 对比 + 总结） | 2×2 网格（最后一格为 Fig.7） |

### 1.3 页眉格式

每页页眉包含 Session 和论文编号，格式为：

```
SESSION X / Session Title / X.Y
```

脚本通过正则 `SESSION\s+\d+\s*/[^/]+/\s*(\d+\.\d+)` 匹配页眉来定位论文。

### 1.4 Figure 编号惯例

| Figure | 典型内容 | 用途 |
|--------|---------|------|
| Fig.1 | 背景/动机/概念图 | 理解问题域 |
| Fig.2 | 整体架构 | 提取架构特征 |
| Fig.3 | 核心模块/数据流 | 提取创新点 |
| Fig.4 | 电路细节/算法实现 | 提取技术手段 |
| Fig.5 | 测量结果/性能曲线 | 提取性能数据 |
| Fig.6 | 对比表/benchmark | 提取性能数据 + 竞品对比 |
| Fig.7 | **Die photo + 性能总结表** | **关键指标提取来源** |

> Fig.7 是最重要的数据来源，通常包含芯片照片和一张汇总表，
> 列出 technology、die area、power、energy efficiency 等核心指标。

---

## 2. 完整字段列表

当前数据集包含 **43 篇论文**，覆盖 Session 2, 10, 18, 30, 31。

### 2A. 元数据字段（从 PDF 正文 / Session Overview 提取）

| 字段 | 类型 | 说明 | PDF 定位方法 | 示例 |
|------|------|------|-------------|------|
| `id` | string | 论文编号 `"X.Y"` | 页眉 `SESSION X / ... / X.Y` | `"31.3"` |
| `session` | int | 所属 Session 编号 | 页眉 | `2`, `10`, `18`, `30`, `31` |
| `title` | string | 英文标题（原文） | 正文第一行 / Session Overview | `"A 51.6μJ/Token Subspace-Rotation-Based Dual-Quantized Large-Language-Model Accelerator with Fused INT Pipeline"` |
| `title_zh` | string | 中文翻译标题 | 人工或 LLM 翻译 | `"51.6μJ/Token子空间旋转双量化LLM加速器：融合INT流水线"` |
| `affiliation` | string | 第一作者所属机构 | 作者行下方机构名 / Session Overview 页 | `"Southeast University"`, `"AMD"`, `"KAIST"` |
| `authors` | string | 第一作者/代表机构 | 作者行 | `"KAIST"`, `"AMD"` |
| `process_node` | string | 工艺节点 | 正文 "fabricated in Xnm" / Fig.7 表格 | `"28nm"`, `"16nm FinFET"`, `"3nm/6nm"` |
| `application` | string | 目标应用领域 | 从正文/标题推断 | `"LLM双量化推理"`, `"数据中心AI训练与推理"` |
| `target_model` | string | 评测所用模型/负载 | 正文 / Fig.6 对比表 | `"LLaMA-7B/13B"`, `"Llama 3.3 70B"`, `"N/A"` |
| `data_path` | string | 该论文数据目录路径 | 自动生成 `"data/{id}/"` | `"data/31.3/"` |

### 2B. 芯片指标字段（从 Fig.6/7 性能总结表提取）

这些字段同时存在于顶层和 `metrics` 子对象中。`metrics` 为规范化存储，顶层字段供前端快速读取。

| 字段 | 类型 | 单位 | 说明 | 提取来源 | 示例 |
|------|------|------|------|---------|------|
| `technology` | string | — | 工艺节点（metrics 内） | 正文 regex / Fig.7 | `"28nm"`, `"3nm/6nm"` |
| `die_area_mm2` | string | mm² | 芯片/核心面积 | Fig.7 die photo 标注 / 表格 | `"25"`, `"4.41"`, `"CoWoS-S"` |
| `supply_voltage` | string | V | 供电电压 | Fig.7 表格 / 正文 | `"0.72V"`, `"0.8V"` |
| `sram_kb` | string | KB/MB | 片上 SRAM 容量 | 正文 / Fig.7 | `"3.43MB SRAM"`, `"256KB"` |
| `frequency_mhz` | string | MHz | 工作频率 | Fig.7 表格 | `"500"`, `"1000"` |
| `power_mw` | string | mW | 功耗 | Fig.7 表格 | `"49.54"`, `"1000000"` (= 1000W) |
| `energy_efficiency` | string | 多种 | 能效指标 | Fig.7 / 标题 | `"127.54TFLOPS/W"`, `"51.6μJ/token"`, `"3.19pJ/b"` |
| `throughput` | string | 多种 | 吞吐量 | Fig.7 表格 | `"2.33TOPS"`, `"50Gb/s"`, `"1TFLOPS"` |
| `source_figure` | string | — | 指标来源图编号 | 自动检测（通常为最后一张图） | `"fig_7"` |

**覆盖率统计（43 篇）：**

| 字段 | 顶层有值 | metrics 内有值 | 说明 |
|------|---------|---------------|------|
| `technology` | — | ~43 | 与 `process_node` 相同 |
| `die_area_mm2` | 部分 | 部分 | 大芯片常无标准面积 |
| `supply_voltage` | 11 | 11 | 大芯片/chiplet 常不报告 |
| `frequency_mhz` | 7 | 7 | 仅数字加速器有固定频率 |
| `sram_kb` | 0 (仅 metrics) | 10 | 部分论文未提及 |
| `power_mw` | 部分 | 部分 | 单位跨度大（mW 到 kW） |
| `energy_efficiency` | ~43 | ~43 | 核心指标，几乎都有 |
| `throughput` | 0 (仅 metrics) | 20 | 约半数可提取 |

### 2C. 高层语义字段（LLM 阅读全文生成）

| 字段 | 类型 | 说明 | 生成方法 |
|------|------|------|---------|
| `title_annotation` | object | 标题术语拆解 | LLM 分析标题中每个技术术语 |
| `title_annotation.segments[]` | array | 术语片段列表 | 每段包含 `text`, `meaning`, `color`, `type` |
| `challenges` | array | 论文解决的 3–4 个关键挑战 | LLM 阅读正文提取 |
| `challenges[].text` | string | 挑战描述（中文） | — |
| `challenges[].related_idea_idx` | int | 对应 ideas 数组索引 | 建立挑战→方案映射 |
| `ideas` | array | 对应的创新解决方案 | LLM 阅读正文提取 |
| `ideas[].text` | string | 方案描述（中文） | — |
| `ideas[].type` | string | 分类标签 | 见下方类型表 |
| `ideas[].color` | string | 前端显示颜色 | 与 type 对应 |
| `innovations` | array | 创新点标签（精炼） | LLM 归纳 |
| `innovations[].tag` | string | 创新点名称（中文） | — |
| `innovations[].type` | string | 分类标签 | 见下方类型表 |
| `tags` | array of string | 搜索/筛选标签 | LLM 生成关键词 |

**类型分类体系（type 字段）：**

| type | 含义 | 颜色 | 示例 |
|------|------|------|------|
| `system` | 系统级创新 | `#3498db` (蓝) | 芯粒封装、SoC 架构 |
| `hw-arch` | 硬件架构创新 | `#e74c3c` (红) | PE 阵列、数据流、NoC |
| `hw-circuit` | 电路级创新 | `#e67e22` (橙) | 比较器、PLL、电压调节 |
| `sw` | 软件/算法创新 | `#2ecc71` (绿) | 量化、稀疏化、调度算法 |
| `co-design` | 软硬协同设计 | 无固定色 | 算法-架构联合优化 |

### 2D. 图表相关字段

| 字段 | 类型 | 说明 | 来源 |
|------|------|------|------|
| `figures` | array | 论文包含的所有图 | `scripts/extract_figures.py` |
| `figures[].num` | int | 图编号（1–7） | 按页面位置排序 |
| `figures[].caption` | string | 图标题（英文原文） | PDF 文本提取 |

**图片文件存储：**

```
images/{paper_id}/
├── fig_1.png    # 单独提取的各图
├── fig_2.png
├── ...
├── fig_7.png
├── page_1.png   # 全页截图
├── page_2.png
└── page_3.png
```

**每篇论文的数据目录：**

```
data/{paper_id}/
├── text.md        # 论文正文 markdown
├── figures.json   # 图编号 + caption 列表
└── metrics.json   # 结构化芯片指标
```

---

## 3. 提取方法详解

### 3.1 PDF → Markdown 文本提取

**脚本：** `scripts/export_markdown.py`
**依赖：** PyMuPDF (`fitz`)

**流程：**
1. 遍历 `pdfs/` 目录下的 Session PDF
2. 通过页眉正则识别每篇论文的页面范围
3. 调用 `page.get_text()` 提取纯文本
4. 输出到 `data/markdown/{paper_id}.md`

**页面识别正则：**
```python
# 匹配页眉中的论文编号
re.search(r'SESSION\s+\d+\s*/[^/]+/\s*(\d+\.\d+)', text)

# 匹配图页中的 Figure 编号（用于关联图页到对应论文）
re.findall(r'Figure\s+(\d+\.\d+)\.\d+', text)
```

### 3.2 图片提取

**脚本：** `scripts/extract_figures.py`
**依赖：** PyMuPDF (`fitz`)

**流程：**
1. 定位论文的图页（检测哪些页面含嵌入图片）
2. 调用 `page.get_images(full=True)` 获取位图列表
3. 过滤小图（< 200×200 px，排除 logo/icon）
4. 按位置排序（从上到下、从左到右），匹配 ISSCC 的 Figure 编号惯例
5. 输出到 `images/{paper_id}/fig_{n}.{ext}`

**位置排序算法：**
- 同一行判定阈值：y 坐标差 < 30 点
- 排序键：`(page, y, x)` → 先按页、再按行、再按列

**向量图 fallback：** 部分论文（如 10.3, 10.6, 10.10）使用向量图而非位图，`get_images()` 无法提取。此时需用 `page.get_pixmap()` 将整页渲染为位图后手动裁剪，或使用全页截图 `page_{n}.png`。

### 3.3 Regex 提取芯片指标

**脚本：** `scripts/extract_metrics.py`

从 `data/{paper_id}/text.md` 中用正则提取以下指标：

#### Technology / Process Node

```python
patterns = [
    r'(\d+\s*nm)\s+CMOS',
    r'fabricated\s+in\s+(\d+\s*nm)',
    r'(\d+\s*nm)\s+(?:UTBB-)?FDSOI',
    r'(\d+\s*nm)\s+FinFET',
    r'(\d+\s*nm)\s+process',
    r'(\d+\s*nm)\s+technology',
    r'TSMC\s+(\d+\s*nm)',
]
```

#### Die Area

```python
patterns = [
    r'die\s+area\s+(?:of\s+)?(\d+\.?\d*)\s*mm\s*[²2]',
    r'(\d+\.?\d*)\s*mm\s*[²2]\s+die\s+area',
    r'(\d+\.?\d*)\s*mm\s*[²2]\s+(?:core|chip|total)\s+area',
    r'occupies\s+(\d+\.?\d*)\s*mm\s*[²2]',
    r'(\d+\.?\d*)\s*[×x]\s*(\d+\.?\d*)\s*mm\s*[²2]?\s*(?:die|chip|core)',  # WxH格式
]
```

#### Supply Voltage

```python
patterns = [
    r'(\d+\.?\d*)\s*V\s+supply',
    r'supply\s+(?:voltage\s+)?(?:of\s+)?(\d+\.?\d*)\s*V',
    r'VDD\s*=\s*(\d+\.?\d*)\s*V',
    r'(\d+\.?\d*)\s*V\s+VDD',
]
# 合理范围校验: 0.3V ≤ V ≤ 5.0V
```

#### SRAM Size

```python
patterns = [
    r'(\d+\.?\d*)\s*[KkMm]B\s+(?:of\s+)?(?:on-chip\s+)?SRAM',
    r'SRAM\s+(?:of\s+)?(\d+\.?\d*)\s*[KkMm]B',
    r'(\d+\.?\d*)\s*[KkMm]B\s+(?:on-chip\s+)?memory',
]
```

#### Frequency

```python
patterns = [
    r'(\d+\.?\d*)\s*[GM]Hz\s+clock',
    r'clock\s+(?:frequency\s+)?(?:of\s+)?(\d+\.?\d*)\s*[GM]Hz',
    r'operates?\s+at\s+(?:up\s+to\s+)?(\d+\.?\d*)\s*[GM]Hz',
    r'frequency\s+(?:of\s+)?(\d+\.?\d*)\s*[GM]Hz',
]
# GHz 自动转换为 MHz: val * 1000
```

#### Power

```python
patterns = [
    r'(?:dissipating|consumes?|power\s+(?:consumption\s+)?(?:of\s+)?)\s*(\d+\.?\d*)\s*([mu]?W)',
    r'(\d+\.?\d*)\s*([mu]?W)\s+(?:power|total)',
    r'(?:total|peak|average)\s+power\s+(?:of\s+)?(\d+\.?\d*)\s*([mu]?W)',
]
# 统一转换为 mW: uW/1000, W*1000
```

#### Energy Efficiency

```python
patterns = [
    r'(\d+\.?\d*)\s*TOPS/W',
    r'(\d+\.?\d*)\s*GOPS/W',
    r'(\d+\.?\d*)\s*[pn]J/b(?:it)?',
    r'(\d+\.?\d*)\s*TFLOPS/W',
]
# 保留原始字符串（不统一单位，因为领域差异大）
```

#### Throughput

```python
patterns = [
    r'(\d+\.?\d*)\s*TOPS(?:\s|,|\.)',
    r'(\d+\.?\d*)\s*GOPS(?:\s|,|\.)',
    r'(\d+\.?\d*)\s*TFLOPS(?:\s|,|\.)',
    r'(\d+\.?\d*)\s*[GM]b/s',
]
```

### 3.4 视觉提取（Fig.7 性能表）

部分指标难以从正文 regex 可靠提取（尤其 die area、power、frequency），需要从 Fig.7 的性能总结表中读取。

**方法：**
1. **人工读图**：查看 `images/{paper_id}/fig_7.png`，手动填入 `papers.json`
2. **LLM 视觉**：将 Fig.7 图片输入多模态 LLM，要求结构化提取表格内容

**Fig.7 性能表通常包含：**
- Technology
- Die Area / Core Area
- Supply Voltage (VDD)
- On-chip SRAM
- Clock Frequency
- Peak Performance (TOPS/GOPS)
- Power Consumption
- Energy Efficiency (TOPS/W)
- 与前人工作的对比列

### 3.5 语义提取（challenges、ideas、innovations）

**工具：** LLM（如 Claude / GPT-4）
**输入：** 论文正文 (`text.md`) + 图片

**Prompt 要点：**

1. **challenges（3–4 项）**：
   - 从正文 Introduction 段落提取论文要解决的核心问题
   - 每项用一句中文概括
   - 标注 `related_idea_idx` 指向对应的 idea

2. **ideas（与 challenges 一一对应）**：
   - 从正文核心方法段落提取
   - 每项用一句中文概括
   - 标注 `type` 分类（system / hw-arch / hw-circuit / sw / co-design）
   - 标注 `color`（按 type 对应的颜色）

3. **innovations（2–3 项）**：
   - 从全文归纳最突出的创新贡献
   - 用简短中文标签 `tag` 命名
   - 标注 `type`

4. **title_annotation**：
   - 将英文标题拆分为技术术语片段
   - 每段标注 `text`（原文）、`meaning`（中文含义）、`color`、`type`

5. **tags（4–6 个）**：
   - 关键词标签，混合中英文
   - 用于前端搜索和筛选

### 3.6 数据校验

**自动校验：**
- `process_node` 与 `metrics.technology` 一致性
- `figures` 数量通常为 6–7（缺失需标注原因）
- `challenges` 与 `ideas` 数量一致
- `challenges[].related_idea_idx` 索引有效

**人工交叉比对：**
- `affiliation` 与论文作者行核对（不仅依赖 Session Overview）
- `energy_efficiency` 单位与论文领域匹配
- `die_area_mm2` 排除非数值封装描述（如 `"CoWoS-S"`）
- `power_mw` 数量级合理性（mW 级 vs. W 级 vs. kW 级）

---

## 4. 各 Session 论文特点

### Session 2: Processors（10 篇，2.1–2.10）

- **类型**：服务器/数据中心级大芯片、GPU、AI SoC
- **特点**：
  - 多使用 chiplet / 3D 堆叠封装
  - 功耗常为百瓦至千瓦级（TDP/TBP），`power_mw` 值非常大
  - `die_area_mm2` 可能为封装描述（如 `"CoWoS-S"`）而非具体面积
  - 性能指标侧重推理吞吐（tokens/s）或 FLOPS
  - 部分论文为产品发布而非学术芯片，缺少标准 die photo

### Session 10: Digital Processing（10 篇，10.1–10.10）

- **类型**：混合类型——网络处理器、PLL、电源管理、SAT solver 等
- **特点**：
  - 非标准加速器较多，指标差异大
  - 部分论文关注 PPA 而非 AI 性能
  - 向量图论文较多（10.3, 10.6, 10.10），图片提取需特殊处理
  - 能效单位多样，部分以 pJ/operation 或 Gb/s 为主

### Session 18: Domain-Specific（5 篇，18.1–18.5）

- **类型**：光互连、NPU-CIM、语音/视频/LLM 加速器
- **特点**：
  - 18.1 为硅光互连，关注 pJ/b 和 Gb/s，无标准 die photo
  - 其余为 AI 加速器，指标与 Session 31 类似
  - 应用领域跨度大（光通信到边缘 AI）

### Session 30: Compute-in-Memory（9 篇，30.1–30.9）

- **类型**：SRAM CIM / RRAM CIM / CTT CIM macro
- **特点**：
  - 核心指标为 TOPS/W 和 TFLOPS/W
  - 工艺节点偏成熟（28nm、22nm）
  - 面积通常较小（mm² 级 macro）
  - 关注精度（INT8/INT4/FP8/MXFP）与能效的权衡
  - 部分为 macro 级测试芯片而非完整 SoC

### Session 31: AI Accelerators（9 篇，31.1–31.9）

- **类型**：LLM 加速器、GenAI 加速器、视觉加速器
- **特点**：
  - 核心指标为 μJ/Token、tokens/s、TOPS/W
  - 评测模型常为 LLaMA 系列
  - 工艺节点从 55nm 到 4nm 均有
  - 关注量化（INT4/INT8）和稀疏化技术
  - 算法-硬件协同设计（co-design）论文较多

---

## 5. JSON Schema 定义

### 5.1 `papers.json` 单条记录完整 Schema

```jsonc
{
  // ===== 元数据 =====
  "id": "31.3",                          // string, 必填, 论文编号 "X.Y"
  "session": 31,                         // int, 必填, Session 编号
  "title": "A 51.6μJ/Token ...",         // string, 必填, 英文标题
  "title_zh": "51.6μJ/Token子空间...",    // string, 必填, 中文标题
  "affiliation": "Southeast University", // string, 必填, 第一作者机构
  "authors": "Southeast University",     // string, 必填, 第一作者/机构
  "process_node": "28nm",               // string, 必填, 工艺节点
  "application": "LLM双量化推理",         // string, 必填, 目标应用
  "target_model": "LLaMA-7B/13B",       // string, "N/A" if 不适用
  "data_path": "data/31.3/",            // string, 必填, 数据目录

  // ===== 顶层芯片指标（供前端快速读取）=====
  "die_area_mm2": "",                    // string, 可为空
  "power_mw": "",                        // string, 可为空
  "energy_efficiency": "51.6μJ/token",   // string, 核心指标
  "supply_voltage": "0.72V",             // string, 可选, 部分论文无此字段
  "frequency_mhz": "500",               // string, 可选, 部分论文无此字段

  // ===== 语义字段 =====
  "title_annotation": { /* 见 5.2 */ },
  "challenges": [ /* 见 5.3 */ ],
  "ideas": [ /* 见 5.4 */ ],
  "innovations": [ /* 见 5.5 */ ],
  "tags": ["LLM", "量化", "旋转", "INT", "流水线", "Hadamard"],

  // ===== 图表 =====
  "figures": [ /* 见 5.6 */ ],

  // ===== 结构化指标 =====
  "metrics": { /* 见 5.7 */ }
}
```

### 5.2 `title_annotation` 结构

```jsonc
{
  "segments": [
    {
      "text": "51.6μJ/Token",        // string, 标题中的术语原文
      "meaning": "每token能耗51.6微焦", // string, 中文含义
      "color": "#3498db",             // string, 前端显示颜色
      "type": "system"                // string, 分类: system|hw-arch|hw-circuit|sw|co-design
    }
    // ... 通常 3-5 个 segment
  ]
}
```

### 5.3 `challenges` 数组

```jsonc
[
  {
    "text": "旋转算子占用PE阵列导致性能下降",  // string, 中文描述
    "related_idea_idx": 0                     // int, 对应 ideas[] 索引
  }
  // ... 通常 3-4 项
]
```

### 5.4 `ideas` 数组

```jsonc
[
  {
    "text": "子空间Hadamard变换独立于PE实现旋转", // string, 中文描述
    "type": "hw-arch",                          // string, 分类标签
    "color": "#e74c3c"                          // string, 与 type 对应
  }
  // ... 与 challenges 数量一一对应
]
```

### 5.5 `innovations` 数组

```jsonc
[
  {
    "tag": "子空间旋转量化",     // string, 创新点名称
    "type": "sw"               // string, 分类标签
  }
  // ... 通常 2-3 项
]
```

### 5.6 `figures` 数组

```jsonc
[
  {
    "num": 1,                                      // int, 图编号
    "caption": "Rotation-based dual-quantized ..."  // string, 图标题原文
  }
  // ... 通常 6-7 项
]
```

### 5.7 `metrics` 子对象

```jsonc
{
  "technology": "28nm",               // string, 工艺节点
  "die_area_mm2": "25",              // string, 芯片面积 (mm²)
  "supply_voltage": "0.72V",         // string, 供电电压
  "sram_kb": "3.43MB SRAM",          // string, 片上SRAM
  "frequency_mhz": "500",            // string, 工作频率 (MHz)
  "power_mw": "49.54",              // string, 功耗 (mW)
  "energy_efficiency": "51.6μJ/token", // string, 能效
  "throughput": "2.33TOPS",          // string, 吞吐量
  "target_model": "LLaMA-7B",       // string, 评测模型
  "source_figure": "fig_7"           // string, 数据来源图
}
```

> 注意：`metrics` 内所有字段均为 string 类型，空值为空字符串 `""`（非 null）。
> 数值不做类型转换，保留原始表述以避免精度损失。

---

## 6. 常见陷阱与注意事项

### 6.1 Affiliation 错误

- **问题**：Session Overview 页的机构列表与论文正文作者行可能不一致
- **正确做法**：以论文正文第一页的作者行下方机构名为准
- **已知案例**：项目初期有 26 个 affiliation 错误需修复

### 6.2 Process Node 格式多样

格式不统一，需保留原始表述：

| 原文 | 存储值 | 备注 |
|------|--------|------|
| `fabricated in 28nm CMOS` | `"28nm"` | 标准格式 |
| `16nm FinFET technology` | `"16nm FinFET"` | 含工艺类型 |
| `Intel 3 process` | `"Intel 3"` | 厂商命名 |
| `3nm XCD + 6nm IOD` | `"3nm/6nm"` | 多芯粒多工艺 |
| `28nm FDSOI` | `"28nm FDSOI"` | 含衬底类型 |

### 6.3 能效单位因领域不同

| Session/领域 | 常见单位 | 示例 |
|-------------|---------|------|
| AI 加速器 | TOPS/W, GOPS/W | `"26.2TOPS/W"` |
| CIM macro | TFLOPS/W | `"127.54TFLOPS/W"` |
| LLM 加速器 | μJ/Token, tokens/s | `"51.6μJ/token"` |
| 光互连 | pJ/b, Gb/s | `"3.19pJ/b"` |
| 大芯片/GPU | 相对倍数 | `"3x gen-over-gen inference"` |

**不统一单位**，保留原始字符串。前端展示时按 Session 分组显示。

### 6.4 Die Photo 缺失

以下情况无标准 die photo：
- 硅光互连论文（18.1）：展示的是光路照片而非 CMOS die
- 大芯片产品（2.x）：展示封装照而非裸片
- Macro 级测试芯片（30.x）：die photo 可能只展示 macro 区域

### 6.5 向量图论文

论文 10.3、10.6、10.10 的 PDF 中图使用矢量绘制，`get_images()` 无法提取位图。

**处理方法：**
- 使用 `page.get_pixmap(dpi=300)` 渲染整页为 PNG
- 存储为 `page_{n}.png` 全页截图
- 不提取单独 fig，改为在全页截图中标注

### 6.6 Power 单位跨度

| 类型 | 典型功耗范围 | `power_mw` 存储 |
|------|-------------|-----------------|
| CIM macro | 0.1–50 mW | `"0.12"` – `"50"` |
| AI 加速器 | 50–5000 mW | `"49.54"` – `"5000"` |
| 大芯片 GPU | 300–1000 W | `"300000"` – `"1000000"` |

存储统一为 mW 单位的字符串，但数量级跨越 7 个量级。前端显示时需自动选择合适单位。

### 6.7 Caption 提取噪音

`figures[].caption` 从 PDF 文本流提取，可能混入正文片段：
- 图标题后紧跟的正文句子可能被误包含
- 跨栏图的 caption 可能被截断
- 建议人工检查并修剪多余文本

### 6.8 Metrics 双重存储

芯片指标同时存在于：
1. 顶层字段（`die_area_mm2`, `power_mw`, `energy_efficiency` 等）
2. `metrics` 子对象内

优先级：`metrics` 内的值更规范。顶层字段主要为向后兼容和前端快速读取。
两处值应保持一致。

---

## 附录：项目文件结构

```
isscc_accelerator/
├── pdfs/                          # 原始 Session PDF
│   ├── session2.pdf
│   └── ...
├── data/
│   ├── papers.json                # 核心数据文件（43条记录）
│   ├── extraction_guide.md        # 本文档
│   ├── markdown/                  # 论文正文 markdown
│   │   ├── 2.1.md
│   │   └── ...
│   ├── {paper_id}/                # 每篇论文的数据目录
│   │   ├── text.md                # 正文文本
│   │   ├── figures.json           # 图编号+caption
│   │   └── metrics.json           # 结构化指标
│   └── figure_stats.json          # 图片提取统计
├── images/
│   └── {paper_id}/                # 每篇论文的图片
│       ├── fig_1.png – fig_7.png  # 单独提取的图
│       └── page_1.png – page_3.png # 全页截图
├── scripts/
│   ├── export_markdown.py         # PDF→Markdown
│   ├── extract_figures.py         # 提取单独图片
│   ├── extract_images.py          # 提取全页截图
│   ├── extract_metrics.py         # Regex 提取指标
│   ├── extract_all_figures.py     # 批量图片提取
│   ├── generate_data.py           # 生成数据目录结构
│   ├── restructure_data.py        # 数据重组
│   └── update_papers_json.py      # 更新 papers.json
└── index.html                     # SPA 前端展示页
```
