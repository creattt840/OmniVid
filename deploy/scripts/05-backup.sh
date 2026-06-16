#!/usr/bin/env bash
# OmniVid 数据备份脚本 — 可加入宝塔计划任务（每周执行）
set -euo pipefail

API_DIR="${OMNIVID_API:-/www/wwwroot/omnivid-api}"
BACKUP_DIR="${OMNIVID_BACKUP:-/www/backup/omnivid}"
STAMP=$(date +%Y%m%d_%H%M%S)
TARGET="$BACKUP_DIR/$STAMP"

mkdir -p "$TARGET"

if [ -f "$API_DIR/omnivid.db" ]; then
  cp "$API_DIR/omnivid.db" "$TARGET/"
  echo "已备份 omnivid.db"
else
  echo "警告: 未找到 $API_DIR/omnivid.db"
fi

if [ -f "$API_DIR/.env" ]; then
  cp "$API_DIR/.env" "$TARGET/.env"
  chmod 600 "$TARGET/.env"
  echo "已备份 .env（请离线加密保存）"
fi

# 保留最近 8 份
ls -dt "$BACKUP_DIR"/*/ 2>/dev/null | tail -n +9 | xargs -r rm -rf

echo "备份完成: $TARGET"
