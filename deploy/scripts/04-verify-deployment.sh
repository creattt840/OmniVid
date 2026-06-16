#!/usr/bin/env bash
# OmniVid 部署验证脚本
# 用法: bash 04-verify-deployment.sh [http://你的域名或IP]
set -euo pipefail

BASE_URL="${1:-http://127.0.0.1}"
BASE_URL="${BASE_URL%/}"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

pass=0
fail=0

check_http() {
  local name="$1"
  local url="$2"
  local expect="${3:-}"
  local code
  code=$(curl -s -o /tmp/omnivid_check_body.txt -w "%{http_code}" --connect-timeout 10 "$url" || echo "000")
  if [ "$code" = "200" ]; then
    if [ -n "$expect" ] && ! grep -q "$expect" /tmp/omnivid_check_body.txt 2>/dev/null; then
      echo -e "${RED}[FAIL]${NC} $name — HTTP 200 但响应不含: $expect"
      fail=$((fail + 1))
    else
      echo -e "${GREEN}[PASS]${NC} $name — $url"
      pass=$((pass + 1))
    fi
  else
    echo -e "${RED}[FAIL]${NC} $name — HTTP $code ($url)"
    fail=$((fail + 1))
  fi
}

echo "=== OmniVid 部署验证 ==="
echo "目标: $BASE_URL"
echo ""

# 后端直连（仅本机）
if curl -s --connect-timeout 3 http://127.0.0.1:8000/api/health >/tmp/omnivid_health.json 2>/dev/null; then
  if grep -q '"status":"ok"' /tmp/omnivid_health.json || grep -q '"status": "ok"' /tmp/omnivid_health.json; then
    echo -e "${GREEN}[PASS]${NC} 后端直连 /api/health"
    pass=$((pass + 1))
    grep -q '"ffmpeg":true\|"ffmpeg": true' /tmp/omnivid_health.json && echo -e "${GREEN}       ${NC}ffmpeg: true" || echo -e "${RED}       ${NC}ffmpeg: false — 请安装 ffmpeg"
    grep -q '"ai_available":true\|"ai_available": true' /tmp/omnivid_health.json && echo -e "${GREEN}       ${NC}ai_available: true" || echo -e "${RED}       ${NC}ai_available: false — 请检查 DEEPSEEK_API_KEY"
  else
    echo -e "${RED}[FAIL]${NC} 后端 health 响应异常"
    cat /tmp/omnivid_health.json
    fail=$((fail + 1))
  fi
else
  echo -e "${RED}[FAIL]${NC} 无法连接 127.0.0.1:8000 — Python 项目可能未启动"
  fail=$((fail + 1))
fi

check_http "首页" "$BASE_URL/" "OmniVid"
check_http "API 健康检查（经 Nginx）" "$BASE_URL/api/health" '"status"'
check_http "sitemap.xml" "$BASE_URL/sitemap.xml" "<urlset"
check_http "robots.txt" "$BASE_URL/robots.txt" "Sitemap"

echo ""
echo "=== 结果 ==="
echo -e "通过: ${GREEN}$pass${NC}  失败: ${RED}$fail${NC}"
if [ "$fail" -gt 0 ]; then
  echo ""
  echo "排查建议:"
  echo "- 502/504: 检查 Python 项目是否运行、Nginx 反向代理是否指向 127.0.0.1:8000"
  echo "- /api/health 404: 未配置 /api 反向代理，见 deploy/nginx/omnivid.conf"
  echo "- 首页 404: 检查网站根目录是否有 index.html"
  exit 1
fi
echo "基础验证通过。请手动测试: B站解析、登录验证码、AI 流式摘要、本地上传。"
