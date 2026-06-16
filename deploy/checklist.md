# OmniVid 上线检查清单

按顺序勾选，每完成一个「确认点」再进入下一阶段。详细步骤见 [宝塔部署指南](../docs/宝塔部署指南.md)。

## 确认点 A — 上线前准备

- [ ] 阿里云安全组已放行：**22（SSH）、80、443、8888（宝塔）**
- [ ] 宝塔面板能正常登录
- [ ] 已持有 **DeepSeek API Key**
- [ ] 已配置 **QQ 邮箱 SMTP 授权码**（不是 QQ 登录密码）
- [ ] 已生成 **JWT_SECRET**（64 位 hex）：
  ```powershell
  python -c "import secrets; print(secrets.token_hex(32))"
  ```
- [ ] 服务器配置：建议 **2 核 4GB+ 内存、40GB+ 磁盘**

**验证命令（本地）：** 无服务器命令，人工确认即可。

---

## 确认点 B — 域名与备案（方案一 IP 内测可跳过）

> 选择 **IP 内测、不备案** 时，本节全部跳过，直接做确认点 C。

- [ ] 已在阿里云购买域名并完成**实名认证**
- [ ] 已提交 **ICP 备案**（记录备案订单号：____________）
- [ ] 已确定最终域名：`________________.com`

---

## 确认点 C — 运行环境

在宝塔 **终端** 执行：

```bash
bash /www/wwwroot/omnivid-src/deploy/scripts/01-check-env.sh
```

- [ ] Python 3.10+ 已安装
- [ ] ffmpeg 已安装
- [ ] Nginx 已安装
- [ ] Node.js 18+ 已安装（若在服务器构建前端）
- [ ] 腾讯云/阿里云 **防火墙** 与宝塔 **安全** 均已放行 80、443

---

## 确认点 D — 后端部署

```bash
bash /www/wwwroot/omnivid-src/deploy/scripts/02-setup-backend.sh
# 编辑 /www/wwwroot/omnivid-api/.env 后重启 Python 项目
curl http://127.0.0.1:8000/api/health
```

- [ ] Python 项目状态为「运行中」
- [ ] 返回 `"status":"ok"`
- [ ] `"ffmpeg": true`
- [ ] `"ai_available": true`

---

## 确认点 E — 前端部署

```bash
bash /www/wwwroot/omnivid-src/deploy/scripts/03-build-frontend.sh
```

- [ ] `/www/wwwroot/omnivid/index.html` 存在
- [ ] 浏览器访问 `http://服务器IP/` 能看到 OmniVid 首页

---

## 确认点 F — Nginx 反向代理

1. 宝塔 → 网站 → 反向代理 → 开启**高级功能** → 代理目录 `/api`
2. 将 [deploy/nginx/baota-proxy-api.conf](nginx/baota-proxy-api.conf) 替换宝塔自动生成的 api 配置
3. 将 [deploy/nginx/baota-server-snippet.conf](nginx/baota-server-snippet.conf) 合并到站点主配置
4. 重载 Nginx

```bash
bash /www/wwwroot/omnivid-src/deploy/scripts/04-verify-deployment.sh http://你的IP或域名
```

- [ ] `/api/health` 通过域名/IP 可访问
- [ ] B 站链接解析成功
- [ ] 邮箱验证码能收到
- [ ] AI 摘要能流式生成

---

## 确认点 G — 备案通过后 HTTPS（方案一 IP 内测可跳过）

> IP 内测阶段不需要 HTTPS。以后正式上线再回来做本节。

- [ ] DNS A 记录指向服务器 IP
- [ ] SSL 证书已部署（Let's Encrypt 或阿里云免费证书）
- [ ] 已开启 **强制 HTTPS**
- [ ] `FRONTEND_URL` 与 `VITE_SITE_URL` 已改为 `https://你的域名`
- [ ] 前端已重新 `npm run build` 并覆盖 `/www/wwwroot/omnivid/`
- [ ] 页脚已显示 ICP 备案号（构建时设置 `VITE_ICP_NUMBER`）

---

## 确认点 H — 上线后运维

- [ ] 宝塔计划任务：每周备份 `omnivid.db` 与 `.env`
- [ ] 访问 `https://域名/sitemap.xml` 正常
- [ ] 已提交 sitemap 到 Google Search Console / 百度搜索资源平台
- [ ] GitHub 仓库 About 已填入正式网站 URL
