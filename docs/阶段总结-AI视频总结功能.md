# 阶段总结 — AI 视频总结功能（第 4 阶段）

> 完成时间：2026-06-14  
> 状态：**已完成，可验收**

## 一、本阶段目标

在已有「解析 + 下载」能力基础上，新增 AI 视频分析：用户粘贴链接并解析后，可一键生成结构化摘要、转录文本、思维导图，并支持基于视频内容的 AI 问答，帮助快速了解长视频核心内容。

## 二、已完成功能

### 2.1 转录文本获取

- **有字幕优先**：B 站 JSON 字幕、YouTube / 其他平台 VTT 字幕（yt-dlp 下载）
- **无字幕兜底**：下载音频 + faster-whisper 本地 ASR 转写
- 统一输出带时间戳的 segments：`{ start, end, text }`

### 2.2 AI 结构化摘要（DeepSeek）

- 流式 SSE 输出，参考竞品 BibiGPT 结构
- 摘要正文（200–400 字）
- 5 条核心要点
- 带时间戳的章节大纲
- 术语解释
- Markdown 思维导图数据

### 2.3 思维导图可视化

- 使用 `markmap-lib` + `markmap-view` 渲染交互式树形图
- 支持缩放、拖拽，切换 Tab 时自动适配

### 2.4 AI 问答

- 多轮对话，上下文注入转录 + 摘要
- SSE 流式回复

### 2.5 前端入口

- 解析成功后右栏自动展示 `VideoSummary`（摘要 / 转录 / 思维导图 / AI 问答）
- 左栏 `VideoResult` 保留下载与字幕导出
- `FeatureSection` AI 功能 badge 为「已上线」

> **2026-06-14 更新**：前端已重构为 OmniVid 同屏工作区，解析后自动触发 AI 分析，详见 [阶段总结-前端体验优化.md](阶段总结-前端体验优化.md)。

### 2.6 字幕独立下载（扩展）

- **解析页**：「下载字幕」按钮，无需触发 AI 分析
- **转录 Tab**：SRT / VTT / TXT 一键导出（基于已加载 segments）
- **Whisper 兜底**：无原生字幕时自动语音转写后导出
- 新增 `POST /api/subtitles/download` 接口

### 2.7 思维导图增强（扩展）

- **全屏查看**：Teleport 全屏 overlay，Esc 退出
- **导出**：PNG / SVG / Markdown 三种格式
- PNG/SVG 使用 `html-to-image` 对可见容器截图（兼容 markmap `foreignObject` 文字渲染）
- Markdown 从 markmap 树结构重建层级标题，并解码 HTML 实体

### 2.8 摘要流式体验优化

- 流式输出仅展示摘要正文，不再显示原始 JSON
- JSON 截断自动修复（`summary_parser.py`）
- SSE 缓冲区兜底，避免生成卡住

## 三、技术实现

```
前端：Vue 3 + markmap-view + SSE (fetch)
后端：FastAPI + DeepSeek (openai SDK) + faster-whisper
转录：subtitles.py（字幕）→ transcriber.py（Whisper 兜底）
AI：summarizer.py（Prompt + Session + SSE）
```

### 新增 API

| 接口 | 说明 |
|------|------|
| `POST /api/analyze` | 拉取/转写 transcript，返回 session_id |
| `GET /api/analyze/{id}/stream` | SSE 流式摘要 + 思维导图 |
| `POST /api/analyze/{id}/chat` | SSE 多轮 AI 问答 |
| `POST /api/subtitles/download` | 下载字幕文件（srt/vtt/txt，含 Whisper 兜底） |
| `GET /api/health` | 新增 `ai_available` 字段 |

### 转录策略

```
URL → 尝试字幕（B站 API / yt-dlp VTT）
    → 无字幕 → 下载音频 → faster-whisper 转写
    → 存入内存 Session（TTL 30 分钟）
    → DeepSeek 生成摘要 / 思维导图 / 支持问答
```

### 新增后端模块

| 路径 | 职责 |
|------|------|
| `app/services/ai/subtitles.py` | 统一字幕拉取与 VTT/SRT/JSON 解析、序列化导出 |
| `app/services/ai/transcriber.py` | 无字幕时音频下载 + Whisper ASR |
| `app/services/ai/summarizer.py` | DeepSeek 调用、Session 管理、SSE |
| `app/services/ai/summary_parser.py` | 流式 JSON 摘要解析与截断修复 |

### 新增前端模块

| 文件 | 职责 |
|------|------|
| `frontend/src/api/analyze.js` | analyze / stream / chat API + SSE 消费 |
| `frontend/src/api/video.js` | 新增 `downloadSubtitles` |
| `frontend/src/components/VideoSummary.vue` | 四 Tab 分析面板 + 转录导出 |
| `frontend/src/components/MindMapView.vue` | markmap 渲染 + 全屏 + 导出 |
| `frontend/src/utils/mindmapExport.js` | 思维导图 PNG/SVG/Markdown 导出 |
| `frontend/src/utils/subtitleExport.js` | 转录 Tab 前端字幕格式转换 |

## 四、环境配置

复制 `backend/.env.example` 为 `backend/.env` 并填写：

```env
DEEPSEEK_API_KEY=sk-xxx
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
WHISPER_MODEL=small
WHISPER_MAX_DURATION=3600
```

> `.env` 已在 `.gitignore` 中，请勿提交到 Git。

首次使用 Whisper 会自动下载约 500MB 的 `small` 模型；无字幕视频转写耗时较长，属正常现象。

## 五、验证情况

| 测试项 | 结果 |
|--------|------|
| B 站字幕提取（BV1GJ411x7h7） | 通过，44 条 segments |
| YouTube 字幕提取（dQw4w9WgXcQ） | 通过，61 条英文字幕 |
| YouTube Whisper 兜底（音乐视频） | 通过，关闭 vad_filter 后可转写 |
| DeepSeek 流式摘要 + SSE | 通过 |
| markmap 思维导图渲染 | 通过 |
| 思维导图全屏 + PNG/SVG/Markdown 导出 | 通过 |
| 字幕独立下载（B 站 / YouTube） | 通过 |
| 转录 Tab SRT/VTT/TXT 导出 | 通过 |
| 摘要流式展示（非 JSON 原文） | 通过 |
| AI 多轮问答 | 通过 |
| 前端生产构建 | 通过 |

## 六、如何验收

1. 启动后端与前端（见 [本地运行指南.md](./本地运行指南.md)）
2. 配置 `backend/.env` 中的 `DEEPSEEK_API_KEY`
3. 粘贴视频链接 → 解析 → 右栏自动开始 **AI 分析**（需登录）
4. 依次查看：摘要（流式）、转录（时间戳）、思维导图（树形图）、AI 问答
5. 点击 **「下载字幕」** 导出 SRT 文件
6. 思维导图 Tab → **全屏** / **下载**（PNG、SVG、Markdown）
7. 转录 Tab → 导出 SRT / VTT / TXT

**推荐测试链接：**

| 平台 | 链接 | 预期 |
|------|------|------|
| Bilibili | `https://www.bilibili.com/video/BV1GJ411x7h7` | 字幕提取 + 完整四 Tab |
| YouTube | `https://www.youtube.com/watch?v=dQw4w9WgXcQ` | 英文字幕或 Whisper 转写 |

## 七、竞品对标与差异化

| 能力 | BibiGPT / NoteGPT | 本项目 |
|------|-------------------|--------|
| 下载 + 总结一体化 | 多为独立产品 | **同一 URL 解析后可下载也可分析** |
| 思维导图 | 有 | 有（markmap 交互式 + 全屏 + 导出） |
| 字幕下载 | 有（SRT/VTT/TXT） | 有（含 Whisper 兜底） |
| AI 问答 | 有 | 有 |
| 笔记导出 | Notion / PDF 等 | 思维导图 Markdown / PNG / SVG |
| 用户配额 / VIP 门控 | 有 | 登录每日 10 次；VIP 暂未开放 |

## 八、已知限制

- Session 存于内存，服务重启或 30 分钟后过期，需重新分析
- 无字幕 ASR 最长 60 分钟（`WHISPER_MAX_DURATION` 可配置）
- Whisper 同时仅 1 个任务（CPU 单线程锁）
- 超长转录超 DeepSeek 上下文时会截断至 50000 字符
- YouTube 字幕偶发 429 时，yt-dlp 下载 VTT 或 Whisper 兜底
- 思维导图 Tab 切换时会自动 `fit()` 适配尺寸

## 九、待后续阶段

| 阶段 | 内容 | 状态 |
|------|------|------|
| 第 5–7 阶段 | 用户登录、云端历史、每日配额 | 已完成 |
| 第 8 阶段 | 部署与移动端验收 | 待开发 |

**v1 未纳入、可后续扩展：**

- 笔记同步（Notion / Obsidian）
- 批量分析
- VIP 会员重新开放

**已实现（后续阶段）：**

- 多语言字幕翻译、云端分析历史
- 摘要 Markdown/PDF 导出、AI 改写文章、章节导航、直链下载优化
- 本地视频文件上传解析
- 后端工程化分层结构（见 `docs/阶段总结-后端工程化重构.md`）
