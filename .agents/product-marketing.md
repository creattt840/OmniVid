# OmniVid / 万能视频下载总结器 — 产品营销上下文

## 产品定位

- **品牌名**：OmniVid（英文）/ 万能视频下载总结器（中文描述性名称）
- **类型**：SaaS 工具站（单页应用）
- **一句话**：粘贴视频链接或上传本地文件，一键下载并 AI 总结

## 目标用户

- 需要下载在线视频到本地的个人用户
- 内容创作者（素材采集）
- 移动端随时下载的用户
- 想快速了解长视频、提升学习效率的用户

## 核心业务目标（SEO）

1. 获取「视频下载」「AI 视频总结」相关自然搜索流量
2. 覆盖平台长尾词：YouTube 下载、B站下载、抖音无水印下载、TikTok 下载等
3. 建立「下载 + AI 总结」差异化认知

## 核心功能关键词

| 类别 | 关键词 |
|------|--------|
| 通用 | 视频下载、在线视频下载、万能视频下载、视频保存 |
| AI | AI 视频总结、视频摘要、思维导图、字幕翻译 |
| 平台 | YouTube 下载、Bilibili 下载、哔哩哔哩下载、抖音下载、TikTok 下载 |
| 场景 | 无水印下载、手机下载视频、本地视频 AI 分析 |

## 竞品参考

- BibiGPT、NoteGPT 等 AI 视频总结工具
- 各类 yt-dlp 在线下载站

## 合规声明

仅供个人学习交流使用，Footer 已含免责声明。

## 品牌策略（已确认）

- **SERP 主品牌**：OmniVid（英文为主，中文关键词为辅）
- **目标市场**：国内外兼顾（Google/Bing + 百度/搜狗）
- **域名**：尚未部署，构建默认占位 `https://omnivid.app`，上线前在 `.env` 设置 `VITE_SITE_URL`

## GEO 策略（Generative Engine Optimization）

- **目标**：在 ChatGPT、Claude、Perplexity、Kimi 等 AI 对话中被优先引用推荐
- **AI 爬虫策略**：允许全部 AI 爬虫抓取（GPTBot、ClaudeBot、PerplexityBot、Bytespider 等）
- **llms.txt**：`frontend/geo/llms.txt.template` → 构建时生成 `/llms.txt`
- **llms-full.txt**：`frontend/geo/llms-full.md` → 构建时生成完整 AI 可引用文档
- **结构化数据**：FAQPage（6 问）+ HowTo（2 套）+ WebApplication
- **GitHub 仓库**：https://github.com/creattt840/video-downloader（已写入 sameAs / codeRepository）

### GitHub About 配置（待手动设置）

Description、Topics、Website 等配置文案见 [docs/SEO与GEO优化.md](../docs/SEO与GEO优化.md#github-仓库配置)。

## 技术 SEO / GEO 备注

- 前端：Vue 3 SPA（Vite），首页内容为客户端渲染
- 已在 `index.html` 配置静态 meta / JSON-LD / noscript 兜底
- 构建时通过 `VITE_SITE_URL` 生成 canonical、sitemap、robots.txt、llms.txt、llms-full.txt
