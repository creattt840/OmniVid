# OmniVid

基于 **yt-dlp** 的智能视频助理，支持 YouTube、Bilibili、抖音、TikTok 等 1800+ 平台。粘贴链接即可解析下载，并自动生成 AI 摘要、思维导图与字幕。

[![GitHub](https://img.shields.io/badge/GitHub-creattt840%2Fvideo--downloader-6366F1?style=flat&logo=github)](https://github.com/creattt840/video-downloader)

## 功能

- 视频链接解析（标题、缩略图、清晰度列表）
- 服务端代理下载 + 直链优先（移动端友好）
- 解析后自动 AI 总结（摘要 / 转录 / 思维导图 / 文章改写 / 问答）
- 笔记导出（Markdown / PDF）、字幕翻译（6 语言）
- 云端分析历史（每用户 10 条，含转录/文章/问答）、左侧汉堡侧滑菜单
- 登录用户每日 10 次 AI 分析（会员功能暂未开放）
- **本地视频上传解析**（拖拽上传 + 可选外挂字幕 + 页内预览 + AI 分析）
- 抖音无水印专用解析
- B 站专用解析（绕过 412 反爬）
- 字幕独立下载（SRT / VTT / TXT，含 Whisper 兜底）
- 柔紫 Indigo 主题响应式前端
- 平台介绍区官方品牌 Logo（YouTube / Bilibili 小电视 / TikTok / X / Instagram / Twitch）

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

### 生产构建（SEO / GEO）

```bash
cd frontend
cp .env.example .env   # 设置 VITE_SITE_URL 为正式域名
npm run build          # 生成 sitemap、robots.txt、llms.txt 等
```

详见 [SEO 与 GEO 优化指南](docs/SEO与GEO优化.md)。

## 项目结构

```
video-downloader/
├── docs/           # 需求分析 + 方案设计 + 阶段总结
├── backend/        # FastAPI + yt-dlp + AI
└── frontend/       # Vue 3 + Tailwind CSS v4
    ├── geo/            # llms.txt / llms-full.txt 源文件（GEO）
    ├── plugins/        # 构建时 SEO/GEO 生成插件
    └── public/logos/   # 平台官方品牌图标（SVG/PNG）
```

## API 文档

启动后端后访问 http://localhost:8000/docs

## 文档

- [SEO 与 GEO 优化指南](docs/SEO与GEO优化.md)
- [本地运行指南](docs/本地运行指南.md)
- [阶段总结-本地视频上传解析](docs/阶段总结-本地视频上传解析.md)
- [阶段总结-平台图标与体验优化](docs/阶段总结-平台图标与体验优化.md)
- [阶段总结-功能扩展与导航优化](docs/阶段总结-功能扩展与导航优化.md)
- [阶段总结-用户登录与VIP会员](docs/阶段总结-用户登录与VIP会员.md)
- [阶段总结-用户分析历史](docs/阶段总结-用户分析历史.md)
- [阶段总结-前端体验优化](docs/阶段总结-前端体验优化.md)
