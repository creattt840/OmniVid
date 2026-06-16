# 阶段总结 - 用户登录与 VIP 会员（第 5–6 阶段）

## 1. 交付内容

### 后端

| 模块 | 路径 | 说明 |
|------|------|------|
| 数据库 | `app/db/connection.py`, `app/db/models.py` | SQLite：users、memberships、usage_daily、stripe_events |
| 认证 | `app/core/security/jwt.py`, `app/api/auth.py` | JWT + bcrypt 注册/登录/me |
| 会员 | `app/services/membership.py`, `app/core/dependencies.py` | VIP 判定、每日 AI 配额、鉴权依赖 |
| 支付 | `app/api/billing.py` | Stripe Checkout（一次性 ¥9.9）+ Webhook 验签与幂等 |
| 测试 | `tests/test_membership.py` | 注册登录、配额、Webhook 幂等 |

### 前端

| 组件/模块 | 说明 |
|-----------|------|
| `AuthModal.vue` | 登录/注册弹窗（邮箱验证码、密码/验证码登录、忘记密码） |
| `UserAccountMenu.vue` | Header 账号下拉菜单（VIP 状态、续费、退出） |
| `useAuth.js` | 全局登录态 |
| `api/auth.js`, `billing.js` | 认证与支付 API |

### VIP 门控

| 功能 | 免费（需登录） | VIP |
|------|----------------|-----|
| 解析/下载 | 无限 | 无限 |
| AI 总结 | 每日 10 次 | 暂未开放更高额度 |
| 字幕翻译 / AI 改写 / PDF 导出 | 登录可用 | 暂未开放 |

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

## 5. 待办（第 8 阶段）

- 生产环境 Stripe Live 密钥与 Dashboard Webhook（会员重新开放时）
- 移动端验收
- Docker / Nginx 部署文档

---

## 6. 策略变更（2026-06）

> 详见 `docs/阶段总结-用户分析历史.md`

| 项目 | 原策略 | 当前策略 |
|------|--------|----------|
| 每日 AI 配额 | 免费 3 次 / VIP 无限 | **登录用户统一 10 次/日** |
| VIP 支付 | Stripe 开通 | **暂未开放** |
| 改写/翻译/PDF | VIP 专属 | **登录即可用** |

> 邮箱验证码注册/登录/找回密码见 [`docs/阶段总结-邮箱验证码登录.md`](阶段总结-邮箱验证码登录.md)。
| 分析历史 | localStorage | **云端按用户 10 条** |
