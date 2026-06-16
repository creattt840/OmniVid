/** 视频链接格式校验（提交前拦截明显非视频 URL） */

const VIDEO_HOST_PATTERNS = [
  'youtube.com',
  'youtu.be',
  'bilibili.com',
  'b23.tv',
  'bili2233.cn',
  'douyin.com',
  'iesdouyin.com',
  'tiktok.com',
  'vimeo.com',
  'twitch.tv',
  'dailymotion.com',
  'dai.ly',
  'twitter.com',
  'x.com',
  'instagram.com',
  'facebook.com',
  'fb.watch',
  'youku.com',
  'iqiyi.com',
  'v.qq.com',
  'acfun.cn',
  'ixigua.com',
  'weibo.com',
  'weibo.cn',
  'xiaohongshu.com',
  'xhslink.com',
  'reddit.com',
  'nicovideo.jp',
  'nico.ms',
  'streamable.com',
  'rumble.com',
  'kuaishou.com',
  'haokan.baidu.com',
  'mgtv.com',
  'pptv.com',
  'le.com',
  'sohu.com',
]

const VIDEO_PATH_PATTERNS = [
  /\/video\//i,
  /\/watch\b/i,
  /[?&]v=/i,
  /\/shorts\//i,
  /\/reel\//i,
  /\/embed\//i,
  /\/bv[a-z0-9]{10}/i,
  /\/av\d+/i,
  /\/share\/video\//i,
]

/** 从分享文案中提取第一个 http(s) 链接（抖音/B站复制口令等） */
export function extractVideoUrlFromText(input) {
  const text = (input || '').trim()
  if (!text) return ''

  const match = text.match(/https?:\/\/[^\s<>"']+/i)
  if (match) {
    return cleanTrailingPunctuation(match[0])
  }

  return text
}

function cleanTrailingPunctuation(url) {
  return url.replace(/[)\].,;!?'"'""''>]+$/g, '')
}

export function normalizeVideoUrl(input) {
  const extracted = extractVideoUrlFromText(input)
  if (!extracted) return ''

  let url = extracted.trim()
  if (!/^https?:\/\//i.test(url)) {
    url = `https://${url}`
  }
  return url
}

export function isHttpUrl(str) {
  try {
    const u = new URL(str)
    return u.protocol === 'http:' || u.protocol === 'https:'
  } catch {
    return false
  }
}

function hostMatchesVideoPlatform(hostname) {
  const host = (hostname || '').toLowerCase()
  return VIDEO_HOST_PATTERNS.some((pattern) => {
    return host === pattern || host.endsWith(`.${pattern}`) || host.includes(pattern)
  })
}

function pathLooksLikeVideo(pathname, search) {
  const full = `${pathname || ''}${search || ''}`
  return VIDEO_PATH_PATTERNS.some((re) => re.test(full) || re.test(pathname || ''))
}

export function isLikelyVideoUrl(input) {
  const url = normalizeVideoUrl(input)
  if (!isHttpUrl(url)) return false

  try {
    const { hostname, pathname, search } = new URL(url)
    if (hostMatchesVideoPlatform(hostname)) return true
    return pathLooksLikeVideo(pathname, search)
  } catch {
    return false
  }
}

export function getInvalidVideoUrlMessage() {
  return '请输入有效的视频链接，例如 B站、YouTube、抖音、TikTok 等平台的视频页面地址。'
}

export function isUnsupportedUrlError(message) {
  if (!message) return false
  return /unsupported url|不是有效的视频链接|无法识别为视频/i.test(message)
}
