#!/usr/bin/env bash
# OmniVid 前端构建并部署到网站根目录
set -euo pipefail

SRC_DIR="${OMNIVID_SRC:-/www/wwwroot/omnivid-src}"
WEB_ROOT="${OMNIVID_WEB:-/www/wwwroot/omnivid}"
FRONTEND_DIR="$SRC_DIR/frontend"

if [ ! -d "$FRONTEND_DIR" ]; then
  echo "错误: 未找到 $FRONTEND_DIR"
  echo "请先 git clone 或上传完整项目到 $SRC_DIR"
  exit 1
fi

if [ ! -f "$FRONTEND_DIR/.env" ]; then
  if [ -f "$FRONTEND_DIR/.env.example" ]; then
    cp "$FRONTEND_DIR/.env.example" "$FRONTEND_DIR/.env"
    echo ">>> 已创建 $FRONTEND_DIR/.env"
    echo ">>> 请编辑 VITE_SITE_URL 为你的正式域名后重新运行本脚本"
  else
    echo "错误: 缺少 frontend/.env，请设置 VITE_SITE_URL"
    exit 1
  fi
fi

# 检查 VITE_SITE_URL 是否为默认值
if grep -q 'omnivid.app' "$FRONTEND_DIR/.env" 2>/dev/null; then
  echo "警告: VITE_SITE_URL 仍为示例域名 omnivid.app，请改为你的实际域名"
fi

echo "=== 构建前端 ==="
cd "$FRONTEND_DIR"
npm install --registry=https://registry.npmmirror.com
npm run build

echo "=== 部署到 $WEB_ROOT ==="
mkdir -p "$WEB_ROOT"
rsync -a --delete "$FRONTEND_DIR/dist/" "$WEB_ROOT/"

if id www >/dev/null 2>&1; then
  chown -R www:www "$WEB_ROOT"
fi

echo ""
echo "前端已部署到 $WEB_ROOT"
echo "请在宝塔创建网站，根目录指向: $WEB_ROOT"
echo "然后配置 Nginx 反向代理，参考 deploy/nginx/omnivid.conf"
