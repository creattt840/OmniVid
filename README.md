# 万能视频下载器

基于 **yt-dlp** 的万能视频下载网站，支持 YouTube、Bilibili、抖音、TikTok 等 1800+ 平台。UI 参考 [ai.codefather.cn/painting](https://ai.codefather.cn/painting) 风格设计。

## 功能（第 1-3 阶段）

- 视频链接解析（标题、缩略图、清晰度列表）
- 服务端代理下载（移动端友好）
- 抖音无水印专用解析
- B 站专用解析（绕过 412 反爬）
- painting 风格响应式前端

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
├── docs/           # 需求分析 + 方案设计
├── backend/        # FastAPI + yt-dlp
└── frontend/       # Vue 3 + Tailwind CSS v4
```

## API 文档

启动后端后访问 http://localhost:8000/docs

## 免责声明

本站仅供个人学习交流使用，请勿用于商业或侵权用途。
