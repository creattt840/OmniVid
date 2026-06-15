# OmniVid

基于 **yt-dlp** 的智能视频助理，支持 YouTube、Bilibili、抖音、TikTok 等 1800+ 平台。粘贴链接即可解析下载，并自动生成 AI 摘要、思维导图与字幕。

## 功能

- 视频链接解析（标题、缩略图、清晰度列表）
- 服务端代理下载 + 直链优先（移动端友好）
- 解析后自动 AI 总结（摘要 / 转录 / 思维导图 / 文章改写 / 问答）
- 笔记导出（Markdown / PDF）、字幕翻译（6 语言）
- 分析历史（localStorage）、左侧汉堡侧滑菜单
- **本地视频上传解析**（拖拽上传 + 可选外挂字幕 + 页内预览 + AI 分析）
- 抖音无水印专用解析
- B 站专用解析（绕过 412 反爬）
- 字幕独立下载（SRT / VTT / TXT，含 Whisper 兜底）
- 柔紫 Indigo 主题响应式前端

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- ffmpeg（YouTube 等 A/V 合并，可选但推荐）

### 后端

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

浏览器访问 http://localhost:5173

## 项目结构

```
video-downloader/
├── docs/           # 需求分析 + 方案设计 + 阶段总结
├── backend/        # FastAPI + yt-dlp + AI
└── frontend/       # Vue 3 + Tailwind CSS v4
```

## API 文档

启动后端后访问 http://localhost:8000/docs

## 文档

- [本地运行指南](docs/本地运行指南.md)
- [阶段总结-本地视频上传解析](docs/阶段总结-本地视频上传解析.md)
- [阶段总结-功能扩展与导航优化](docs/阶段总结-功能扩展与导航优化.md)
- [阶段总结-前端体验优化](docs/阶段总结-前端体验优化.md)
