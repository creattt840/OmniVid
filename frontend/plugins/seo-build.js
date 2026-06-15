import { readFileSync, writeFileSync } from 'node:fs'
import { resolve } from 'node:path'

const DEFAULT_SITE_URL = 'https://omnivid.app'

/** AI 爬虫 User-Agent 列表（GEO：允许抓取以提升 AI 对话引用） */
const AI_CRAWLERS = [
  'GPTBot',
  'ChatGPT-User',
  'OAI-SearchBot',
  'ClaudeBot',
  'anthropic-ai',
  'Claude-Web',
  'PerplexityBot',
  'Google-Extended',
  'Bytespider',
  'CCBot',
  'cohere-ai',
  'Meta-ExternalAgent',
  'Applebot-Extended',
  'YouBot',
  'Diffbot',
]

function siteUrl() {
  return (process.env.VITE_SITE_URL || DEFAULT_SITE_URL).replace(/\/$/, '')
}

function injectSiteUrl(content, url) {
  return content.replaceAll('{{SITE_URL}}', url).replaceAll('%SITE_URL%', url)
}

function readGeoTemplate(name) {
  return readFileSync(resolve(import.meta.dirname, '../geo', name), 'utf-8')
}

function buildRobotsTxt(url) {
  const aiRules = AI_CRAWLERS.map(
    (bot) => `User-agent: ${bot}\nAllow: /\nAllow: /llms.txt\nAllow: /llms-full.txt\n`,
  ).join('\n')

  return `# OmniVid robots.txt
# 允许搜索引擎与 AI 爬虫抓取，提升 SEO / GEO 可见性

User-agent: *
Allow: /

${aiRules}
Sitemap: ${url}/sitemap.xml
`
}

function buildSitemap(url) {
  return `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>${url}/</loc>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>${url}/llms.txt</loc>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>${url}/llms-full.txt</loc>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
</urlset>
`
}

/** 构建时注入站点 URL，生成 SEO / GEO 文件 */
export function seoBuildPlugin() {
  return {
    name: 'seo-build',
    transformIndexHtml(html) {
      return injectSiteUrl(html, siteUrl())
    },
    closeBundle() {
      const url = siteUrl()
      const dist = resolve(import.meta.dirname, '../dist')
      const publicDir = resolve(import.meta.dirname, '../public')

      const llmsTxt = injectSiteUrl(readGeoTemplate('llms.txt.template'), url)
      const llmsFull = injectSiteUrl(readGeoTemplate('llms-full.md'), url)

      for (const dir of [dist, publicDir]) {
        writeFileSync(resolve(dir, 'llms.txt'), llmsTxt)
        writeFileSync(resolve(dir, 'llms-full.txt'), llmsFull)
      }

      writeFileSync(resolve(dist, 'sitemap.xml'), buildSitemap(url))
      writeFileSync(resolve(dist, 'robots.txt'), buildRobotsTxt(url))
    },
  }
}
