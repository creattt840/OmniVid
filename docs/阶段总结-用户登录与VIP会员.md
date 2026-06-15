# 阶段总结 - 用户登录与 VIP 会员（第 5–6 阶段）

## 1. 交付内容

### 后端

| 模块 | 文件 | 说明 |
|------|------|------|
| 数据库 | `database.py`, `models.py` | SQLite：users、memberships、usage_daily、stripe_events |
| 认证 | `auth_utils.py`, `auth_routes.py` | JWT + bcrypt 注册/登录/me |
| 会员 | `membership.py`, `deps.py` | VIP 判定、每日 AI 配额、鉴权依赖 |
| 支付 | `billing.py` | Stripe Checkout（一次性 ¥9.9）+ Webhook 验签与幂等 |
| 测试 | `test_membership.py` | 注册登录、配额、Webhook 幂等 |

### 前端

| 组件/模块 | 说明 |
|-----------|------|
| `AuthModal.vue` | 登录/注册弹窗 |
| `UserAccountMenu.vue` | Header 账号下拉菜单（VIP 状态、续费、退出） |
| `useAuth.js` | 全局登录态 |
| `api/auth.js`, `billing.js` | 认证与支付 API |

### VIP 门控

| 功能 | 免费（需登录） | VIP |
|------|----------------|-----|
| 解析/下载 | 无限 | 无限 |
| AI 总结 | 每日 3 次 | 无限 |
| 字幕翻译 / AI 改写 / PDF 导出 | 不可用 | 可用 |

## 2. 支付流程

1. 用户登录 → 点击「开通 VIP」→ 后端创建 Stripe Checkout Session
2. Stripe 托管页完成支付（测试卡 `4242...`）
3. `stripe listen` 转发 `checkout.session.completed` → 后端验签 + 幂等 → 延长 VIP 30 天
4. 用户跳回 `FRONTEND_URL`，前端刷新 `/api/auth/me` 显示 VIP

**安全要点**：仅以 Webhook 开通 VIP；`stripe_events.event_id` 唯一约束防重复处理。

## 3. 体验优化（本阶段内修复）

- 支付成功跳转端口与 `FRONTEND_URL` 对齐（preview 固定 5173）
- Webhook 处理 StripeObject 类型（修复支付成功但 VIP 未开通）
- 未登录解析后登录，AI 分析自动重试
- Header 账号区改为下拉弹窗，不再跳转定价区

## 4. 环境变量

见 `backend/.env.example` 与 `docs/本地运行指南.md` §6。

## 5. 待办（第 7 阶段）

- 生产环境 Stripe Live 密钥与 Dashboard Webhook
- 移动端会员流程验收
- Docker / Nginx 部署文档
