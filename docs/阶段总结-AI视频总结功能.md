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

- `VideoResult.vue` 新增「AI 分析」按钮（与「立即下载」并列）
- `VideoSummary.vue` 四 Tab：摘要 / 转录 / 思维导图 / AI 问答
- `FeatureSection` AI 功能 badge 更新为「已上线」

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
| `GET /api/health` | 新增 `ai_available` 字段 |

### 转录策略

```
URL → 尝试字幕（B站 API / yt-dlp VTT）
    → 无字幕 → 下载音频 → faster-whisper 转写
    → 存入内存 Session（TTL 30 分钟）
    → DeepSeek 生成摘要 / 思维导图 / 支持问答
```

### 新增后端模块

| 文件 | 职责 |
|------|------|
| `backend/subtitles.py` | 统一字幕拉取与 VTT/SRT/JSON 解析 |
| `backend/transcriber.py` | 无字幕时音频下载 + Whisper ASR |
| `backend/summarizer.py` | DeepSeek 调用、Session 管理、SSE |

### 新增前端模块

| 文件 | 职责 |
|------|------|
| `frontend/src/api/analyze.js` | analyze / stream / chat API + SSE 消费 |
| `frontend/src/components/VideoSummary.vue` | 四 Tab 分析面板 |
| `frontend/src/components/MindMapView.vue` | markmap 思维导图渲染 |

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
| AI 多轮问答 | 通过 |
| 前端生产构建 | 通过 |

## 六、如何验收

1. 启动后端与前端（见 [本地运行指南.md](./本地运行指南.md)）
2. 配置 `backend/.env` 中的 `DEEPSEEK_API_KEY`
3. 粘贴视频链接 → 解析 → 点击 **「AI 分析」**
4. 依次查看：摘要（流式）、转录（时间戳）、思维导图（树形图）、AI 问答

**推荐测试链接：**

| 平台 | 链接 | 预期 |
|------|------|------|
| Bilibili | `https://www.bilibili.com/video/BV1GJ411x7h7` | 字幕提取 + 完整四 Tab |
| YouTube | `https://www.youtube.com/watch?v=dQw4w9WgXcQ` | 英文字幕或 Whisper 转写 |

## 七、竞品对标与差异化

| 能力 | BibiGPT / NoteGPT | 本项目 |
|------|-------------------|--------|
| 下载 + 总结一体化 | 多为独立产品 | **同一 URL 解析后可下载也可分析** |
| 思维导图 | 有 | 有（markmap 交互式） |
| AI 问答 | 有 | 有 |
| 笔记导出 | Notion / PDF 等 | 后续阶段 |
| 用户配额 / VIP 门控 | 有 | 后续阶段（第 5–6 阶段） |

## 八、已知限制

- Session 存于内存，服务重启或 30 分钟后过期，需重新分析
- 无字幕 ASR 最长 60 分钟（`WHISPER_MAX_DURATION` 可配置）
- Whisper 同时仅 1 个任务（CPU 单线程锁）
- 超长转录超 DeepSeek 上下文时会截断至 50000 字符
- YouTube 字幕偶发 429 时，yt-dlp 下载 VTT 或 Whisper 兜底
- 思维导图 Tab 若首次空白，切换 Tab 再回来即可触发重绘

## 九、待后续阶段

| 阶段 | 内容 | 状态 |
|------|------|------|
| 第 5 阶段 | SQLite + JWT 用户登录 | 待开发 |
| 第 6 阶段 | Stripe 付费 + VIP 配额门控 | 待开发 |
| 第 7 阶段 | 全链路验收 + 部署 | 待开发 |

**v1 未纳入、可后续扩展：**

- 笔记导出（Notion / Obsidian / PDF）
- 多语言字幕翻译
- 批量分析、分析历史持久化
- 免费 3 次/日 AI 配额（需用户系统）
