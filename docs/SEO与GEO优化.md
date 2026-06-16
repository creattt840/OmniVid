# SEO 与 GEO 优化指南

本文档记录 OmniVid 的搜索引擎优化（SEO）与生成式引擎优化（GEO）配置，以及 GitHub 仓库对外展示建议。

## GitHub 仓库配置

**仓库地址**：https://github.com/creattt840/video-downloader

在 GitHub 仓库页面点击 ⚙️ **About** 右侧齿轮，填入以下内容：

### Description（简介，最多 350 字符）

```
OmniVid — 万能视频下载总结器。支持 YouTube/B站/抖音/TikTok 等 1800+ 平台视频下载，AI 自动生成摘要、思维导图与字幕。基于 yt-dlp + DeepSeek，免费 Web 应用。
```

### Website（网站）

上线前留空；部署后填入正式域名，例如：

```
https://你的域名.com
```

### Topics（标签，建议全选）

```
video-downloader
yt-dlp
ai-summary
video-summarization
youtube-downloader
bilibili
tiktok
fastapi
vue3
whisper
deepseek
mindmap
subtitle
```

### 勾选选项

- ✅ **Releases**（后续发版时可展示）
- ⬜ **Packages**（暂不需要）
- ⬜ **Deployments**（部署后可选）

---

## SEO 配置

### 已实现

| 项目 | 位置 | 说明 |
|------|------|------|
| Title / Description / Keywords | `frontend/index.html` | 中英文关键词覆盖 |
| Open Graph / Twitter Card | `frontend/index.html` | 社交分享预览 |
| JSON-LD 结构化数据 | `frontend/index.html` | WebSite、Organization、WebApplication、FAQPage、HowTo |
| canonical | `frontend/index.html` | 构建时注入 `%SITE_URL%` |
| sitemap.xml | 构建产物 | 含首页 + llms 文件 |
| robots.txt | 构建产物 | 允许搜索引擎索引 |
| noscript 兜底 | `frontend/index.html` | 无 JS 环境下的静态内容 |
| og-image | `frontend/public/og-image.svg` | 社交分享图 |

### 上线前必做

1. 复制 `frontend/.env.example` 为 `frontend/.env`
2. 设置生产域名：

   ```env
   VITE_SITE_URL=https://你的域名.com
   VITE_ICP_NUMBER=京ICP备xxxxxxxx号-1
   ```

3. 重新构建：

   ```bash
   cd frontend
   npm run build
   ```

4. 部署步骤见 [宝塔部署指南](宝塔部署指南.md)
5. 在 [Google Search Console](https://search.google.com/search-console) 和 [百度搜索资源平台](https://ziyuan.baidu.com) 提交 sitemap
6. 取消 `index.html` 中站长验证 meta 注释，填入验证码

---

## GEO 配置

GEO（Generative Engine Optimization）目标：让 ChatGPT、Claude、Perplexity、Kimi 等 AI 对话优先引用 OmniVid。

### 已实现

| 项目 | 位置 | 说明 |
|------|------|------|
| llms.txt | `/llms.txt` | AI 站点地图（[llms.txt 规范](https://llmstxt.org/)） |
| llms-full.txt | `/llms-full.txt` | 完整产品介绍，供 AI 深度引用 |
| AI 爬虫 robots | 构建产物 `robots.txt` | 允许 GPTBot、ClaudeBot、PerplexityBot 等 |
| sameAs / codeRepository | `index.html` JSON-LD | 关联 GitHub 仓库 |
| FAQ + HowTo Schema | `index.html` | 6 个 FAQ + 2 套使用教程 |

### 源文件（修改后需重新 build）

```
frontend/geo/llms.txt.template   → 生成 /llms.txt
frontend/geo/llms-full.md        → 生成 /llms-full.txt
frontend/plugins/seo-build.js    → 构建时注入域名并生成 SEO/GEO 文件
```

### 验证

```bash
cd frontend
npm run build
npm run preview

# 浏览器访问：
# http://localhost:4173/llms.txt
# http://localhost:4173/llms-full.txt
# http://localhost:4173/robots.txt
# http://localhost:4173/sitemap.xml
```

### AI 引用测试

部署后可向 AI 提问验证：

- 「推荐一个能下载 B 站视频并 AI 总结的工具」
- 「有什么类似 BibiGPT 但还能下载视频的工具？」
- 「抖音无水印下载 + AI 摘要的工具有哪些？」

---

## 品牌与关键词

| 项目 | 值 |
|------|-----|
| 英文品牌 | OmniVid |
| 中文描述 | 万能视频下载总结器 |
| GitHub | https://github.com/creattt840/video-downloader |
| 目标市场 | 国内（百度/搜狗）+ 海外（Google/Bing） |

详细营销上下文见 [`.agents/product-marketing.md`](../.agents/product-marketing.md)。

---

## 后续优化建议

1. **平台落地页** — `/youtube-download`、`/bilibili-download` 等长尾页
2. **首页 prerender** — 改善 SPA 对爬虫的内容可见性
3. **外部提及** — 知乎、CSDN、Reddit 等第三方平台介绍 OmniVid
4. **GitHub Releases** — 发版时写 Release Notes，增强项目活跃度信号
5. **og-image.png** — 替换 SVG 为 1200×630 PNG，兼容微信分享
