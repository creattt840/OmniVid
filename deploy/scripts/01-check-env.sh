#!/usr/bin/env bash
# OmniVid 环境检查脚本 — 在宝塔终端执行
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

pass=0
fail=0

check() {
  local name="$1"
  local cmd="$2"
  if eval "$cmd" >/dev/null 2>&1; then
    echo -e "${GREEN}[PASS]${NC} $name"
    pass=$((pass + 1))
    return 0
  else
    echo -e "${RED}[FAIL]${NC} $name"
    fail=$((fail + 1))
    return 1
  fi
}

warn() {
  echo -e "${YELLOW}[WARN]${NC} $1"
}

echo "=== OmniVid 环境检查 ==="
echo ""

# Python 3.10+
if command -v python3 >/dev/null 2>&1; then
  py_ver=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
  if python3 -c 'import sys; exit(0 if sys.version_info >= (3, 10) else 1)'; then
    echo -e "${GREEN}[PASS]${NC} Python $py_ver (>= 3.10)"
    pass=$((pass + 1))
  else
    echo -e "${RED}[FAIL]${NC} Python $py_ver (需要 >= 3.10)"
    fail=$((fail + 1))
  fi
else
  echo -e "${RED}[FAIL]${NC} python3 未安装"
  fail=$((fail + 1))
fi

check "ffmpeg" "ffmpeg -version"
check "nginx" "nginx -v"

if command -v node >/dev/null 2>&1; then
  node_ver=$(node -v | sed 's/v//' | cut -d. -f1)
  if [ "$node_ver" -ge 18 ] 2>/dev/null; then
    echo -e "${GREEN}[PASS]${NC} Node.js $(node -v) (>= 18)"
    pass=$((pass + 1))
  else
    echo -e "${RED}[FAIL]${NC} Node.js $(node -v) (需要 >= 18，若在本地构建前端可忽略)"
    fail=$((fail + 1))
  fi
else
  warn "Node.js 未安装（若只在本地构建前端可忽略）"
fi

if command -v git >/dev/null 2>&1; then
  echo -e "${GREEN}[PASS]${NC} git $(git --version | head -1)"
  pass=$((pass + 1))
else
  warn "git 未安装（可用文件管理器上传代码代替）"
fi

echo ""
echo "=== 端口监听（可选）==="
if command -v ss >/dev/null 2>&1; then
  ss -tlnp 2>/dev/null | grep -E ':80 |:443 |:8000 ' || warn "80/443/8000 端口可能尚未监听（部署完成后应有 80 和 8000）"
elif command -v netstat >/dev/null 2>&1; then
  netstat -tlnp 2>/dev/null | grep -E ':80 |:443 |:8000 ' || true
fi

echo ""
echo "=== 结果 ==="
echo -e "通过: ${GREEN}$pass${NC}  失败: ${RED}$fail${NC}"
if [ "$fail" -gt 0 ]; then
  echo ""
  echo "请按 docs/宝塔部署指南.md 阶段 2 安装缺失组件后重试。"
  exit 1
fi
echo "环境检查通过，可继续部署后端。"
exit 0
