#!/usr/bin/env bash
# OmniVid 后端部署脚本 — 在宝塔终端以 root 或具备 sudo 权限的用户执行
set -euo pipefail

SRC_DIR="${OMNIVID_SRC:-/www/wwwroot/omnivid-src}"
API_DIR="${OMNIVID_API:-/www/wwwroot/omnivid-api}"
VENV_DIR="$API_DIR/venv"
PIP_INDEX="${PIP_INDEX:-https://pypi.tuna.tsinghua.edu.cn/simple}"

echo "=== OmniVid 后端部署 ==="
echo "源码目录: $SRC_DIR"
echo "API 目录:   $API_DIR"
echo ""

# 若源码不存在，尝试 git clone
if [ ! -d "$SRC_DIR/backend" ]; then
  echo "未找到 $SRC_DIR/backend，尝试克隆仓库..."
  mkdir -p "$(dirname "$SRC_DIR")"
  git clone https://github.com/creattt840/video-downloader.git "$SRC_DIR"
fi

# 同步 backend 到 API 目录
mkdir -p "$API_DIR"
rsync -a --delete \
  --exclude 'venv' \
  --exclude 'omnivid.db' \
  --exclude 'downloads/*' \
  --exclude '__pycache__' \
  --exclude '.env' \
  "$SRC_DIR/backend/" "$API_DIR/"

# 保留 downloads 目录
mkdir -p "$API_DIR/downloads"
touch "$API_DIR/downloads/.gitkeep"

# 创建 .env（若不存在）
if [ ! -f "$API_DIR/.env" ]; then
  cp "$API_DIR/.env.example" "$API_DIR/.env"
  echo ""
  echo ">>> 已创建 $API_DIR/.env"
  echo ">>> 请编辑以下必填项后再启动 Python 项目："
  echo "    JWT_SECRET, DEEPSEEK_API_KEY, FRONTEND_URL, SMTP_*"
  echo ""
fi

# 虚拟环境
if [ ! -d "$VENV_DIR" ]; then
  echo "创建 Python 虚拟环境..."
  python3 -m venv "$VENV_DIR"
fi

echo "安装 Python 依赖（首次可能较慢，含 faster-whisper）..."
"$VENV_DIR/bin/pip" install -U pip -i "$PIP_INDEX"
"$VENV_DIR/bin/pip" install -r "$API_DIR/requirements.txt" -i "$PIP_INDEX"
"$VENV_DIR/bin/pip" install gunicorn -i "$PIP_INDEX"

# 权限
if id www >/dev/null 2>&1; then
  chown -R www:www "$API_DIR"
  chmod 600 "$API_DIR/.env"
fi

echo ""
echo "=== 后端文件就绪 ==="
echo ""
echo "下一步（宝塔面板操作）："
echo "1. 网站 → Python 项目 → 添加 Python 项目"
echo "   项目路径: $API_DIR"
echo "   启动命令:"
echo "   $VENV_DIR/bin/uvicorn main:app --host 127.0.0.1 --port 8000 --workers 2"
echo ""
echo "2. 编辑 $API_DIR/.env 填入生产密钥"
echo ""
echo "3. 启动后验证:"
echo "   curl http://127.0.0.1:8000/api/health"
