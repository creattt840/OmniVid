# OmniVid 部署资源

本目录包含宝塔面板上线所需的脚本、Nginx 配置与检查清单。

## 快速开始

1. 阅读 [docs/宝塔部署指南.md](../docs/宝塔部署指南.md)
2. 按 [checklist.md](checklist.md) 逐步勾选
3. 在服务器上依次执行：

```bash
cd /www/wwwroot
git clone https://github.com/creattt840/video-downloader.git omnivid-src

bash omnivid-src/deploy/scripts/01-check-env.sh
bash omnivid-src/deploy/scripts/02-setup-backend.sh
# 编辑 /www/wwwroot/omnivid-api/.env
# 宝塔创建 Python 项目并启动

bash omnivid-src/deploy/scripts/03-build-frontend.sh
# 宝塔创建网站 + 配置 Nginx（见 nginx/omnivid.conf）

bash omnivid-src/deploy/scripts/04-verify-deployment.sh http://你的IP或域名
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `checklist.md` | 人工确认点 A～H |
| `env.production.example` | 后端 `.env` 生产模板 |
| `nginx/omnivid.conf` | 完整 Nginx 片段（非宝塔 include 结构） |
| `nginx/baota-proxy-api.conf` | 宝塔反向代理 include 文件（**必改**，替换自动生成配置） |
| `nginx/baota-server-snippet.conf` | 宝塔站点主配置需添加的片段 |
| `scripts/01-check-env.sh` | 环境检查 |
| `scripts/02-setup-backend.sh` | 后端 venv + 依赖 |
| `scripts/03-build-frontend.sh` | 前端 build + 部署 |
| `scripts/04-verify-deployment.sh` | 自动化验证 |

## 本地 Windows 构建前端

```powershell
cd frontend
copy .env.example .env
# 编辑 VITE_SITE_URL、VITE_ICP_NUMBER
npm install
npm run build
# 将 dist/ 上传到服务器 /www/wwwroot/omnivid/
```
