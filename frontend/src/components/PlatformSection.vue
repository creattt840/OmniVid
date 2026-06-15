<template>
  <section id="platforms" class="py-14 sm:py-20" aria-labelledby="platforms-heading">
    <div class="page-container">
      <div class="text-center mb-10 sm:mb-14">
        <h2 id="platforms-heading" class="section-title mb-3">
          支持全球 <span class="text-primary">1800+</span> 视频平台
        </h2>
        <p class="section-desc text-base">
          几乎覆盖所有主流视频、社交媒体平台，粘贴链接即可下载
        </p>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-5">
        <div
          v-for="platform in platforms"
          :key="platform.name"
          class="card-surface card-surface-lift overflow-hidden cursor-default"
        >
          <div
            class="h-32 sm:h-36 flex items-center justify-center"
            :class="platform.bg"
          >
            <img
              :src="platform.logo"
              :alt="platform.name"
              class="object-contain drop-shadow-sm transition-transform duration-300 group-hover:scale-105"
              :class="platform.logoClass"
              loading="lazy"
              decoding="async"
            />
          </div>
          <div class="p-5">
            <h3 class="font-bold text-text-primary text-base mb-2">
              {{ platform.name }}
            </h3>
            <p class="text-sm text-text-secondary mb-3 line-clamp-2">{{ platform.desc }}</p>
            <div class="flex flex-wrap gap-1.5">
              <span
                v-for="tag in platform.tags"
                :key="tag"
                class="text-xs text-text-secondary px-2 py-0.5 rounded-full bg-surface-muted"
              >
                # {{ tag }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <p class="text-center mt-8 text-sm text-text-muted">
        ...以及 Twitter/X、Instagram、Facebook、Vimeo、Twitch、SoundCloud 等 1800+ 平台
      </p>
    </div>
  </section>
</template>

<script setup>
const platforms = [
  {
    logo: '/logos/youtube.svg',
    logoClass: 'h-14 w-14 sm:h-16 sm:w-16',
    name: 'YouTube 视频下载',
    desc: '支持 4K/1080P 多清晰度，A/V 自动合并，字幕提取',
    tags: ['YouTube', '4K', '字幕'],
    bg: 'bg-red-50',
  },
  {
    logo: '/logos/bilibili.svg',
    logoClass: 'h-16 w-16 sm:h-[4.5rem] sm:w-[4.5rem]',
    name: 'Bilibili 哔哩哔哩',
    desc: '绕过反爬限制，720P/1080P 多清晰度，CC 字幕支持',
    tags: ['Bilibili', '1080P', 'CC字幕'],
    bg: 'bg-pink-50',
  },
  {
    logo: '/logos/tiktok.svg',
    logoClass: 'h-14 w-14 sm:h-16 sm:w-16',
    name: '抖音 / TikTok',
    desc: '无水印原画下载，短链接自动解析，移动端友好',
    tags: ['抖音', '无水印', 'TikTok'],
    bg: 'bg-gray-50',
  },
  {
    logo: '/logos/x.svg',
    logoClass: 'h-12 w-12 sm:h-14 sm:w-14',
    name: 'Twitter / X',
    desc: '推文视频、GIF 一键保存，支持多格式',
    tags: ['Twitter', 'X', 'GIF'],
    bg: 'bg-gray-50',
  },
  {
    logo: '/logos/instagram.svg',
    logoClass: 'h-14 w-14 sm:h-16 sm:w-16',
    name: 'Instagram',
    desc: 'Reels、Stories、帖子视频高清下载',
    tags: ['Instagram', 'Reels', 'Stories'],
    bg: 'bg-purple-50',
  },
  {
    logo: '/logos/twitch.svg',
    logoClass: 'h-14 w-14 sm:h-16 sm:w-16',
    name: 'Twitch / 更多',
    desc: '直播回放、VOD 剪辑，以及 1800+ 其他平台',
    tags: ['Twitch', 'VOD', '更多'],
    bg: 'bg-purple-50',
  },
]
</script>
