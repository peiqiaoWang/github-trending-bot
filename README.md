# GitHub Trending Bot 🔥

每日自动推送 GitHub Trending 热门项目到飞书群，并生成飞书文档。

## ✨ 功能特点

- ⏰ 每天北京时间 9:00 自动推送
- 📊 展示 Top 10-15 热门项目
- 📄 **自动生成飞书文档**（可选）
- 🎨 精美飞书卡片消息
- 🔒 支持签名加密

## 🚀 快速开始

### 方式一：仅消息推送（简单）

只需配置 Webhook，即可每日推送卡片消息。

#### 1. Fork 本仓库

点击右上角 `Fork` 按钮

#### 2. 配置 Secrets

进入仓库 → `Settings` → `Secrets and variables` → `Actions` → `New repository secret`

| Name | Value | 必填 |
|------|-------|:---:|
| `FEISHU_WEBHOOK_URL` | 飞书机器人 Webhook 地址 | ✅ |
| `FEISHU_SECRET` | 签名密钥（如开启加签） | ❌ |

#### 3. 启用 Actions

进入 `Actions` 页面，启用 Workflows

---

### 方式二：消息推送 + 飞书文档（推荐）

除了卡片消息，还会自动生成详细的飞书文档。

#### 额外配置

除了上述配置，还需添加飞书应用凭证：

| Name | Value | 必填 |
|------|-------|:---:|
| `FEISHU_APP_ID` | 飞书应用 App ID | ✅ |
| `FEISHU_APP_SECRET` | 飞书应用 App Secret | ✅ |

#### 创建飞书应用

1. 访问 [飞书开放平台](https://open.feishu.cn/app)
2. 创建「企业自建应用」
3. 获取 App ID 和 App Secret
4. 开通权限：
   - `docx:document` - 创建和编辑文档
   - `docx:document:readonly` - 读取文档
5. 发布应用

---

## 📋 消息预览

推送内容包括：
- 📅 更新时间
- 🏆 Top 5 项目预览（卡片内）
- 📄 完整报告按钮（点击跳转飞书文档）
- 🌐 GitHub Trending 链接

---

## ⏰ 修改推送时间

编辑 `.github/workflows/daily-trending.yml` 中的 cron 表达式：

```yaml
schedule:
  - cron: '0 1 * * *'  # UTC 时间，对应北京时间 9:00
```

常用时间对照：

| 北京时间 | UTC Cron |
|---------|----------|
| 08:00 | `0 0 * * *` |
| 09:00 | `0 1 * * *` |
| 10:00 | `0 2 * * *` |
| 12:00 | `0 4 * * *` |
| 18:00 | `0 10 * * *` |
| 工作日 9:00 | `0 1 * * 1-5` |

---

## 🧪 本地测试

```bash
# 安装依赖
pip install -r requirements.txt

# 设置环境变量
export FEISHU_WEBHOOK_URL="your_webhook_url"
# 可选
export FEISHU_APP_ID="your_app_id"
export FEISHU_APP_SECRET="your_app_secret"

# 运行
python scripts/fetch_trending.py
```

---

## 📁 项目结构

```
github-trending-bot/
├── .github/
│   └── workflows/
│       └── daily-trending.yml    # GitHub Actions 配置
├── scripts/
│   └── fetch_trending.py         # 主程序
├── requirements.txt              # Python 依赖
└── README.md                     # 说明文档
```

---

## 🔧 环境变量说明

| 变量名 | 说明 | 必填 |
|--------|------|:---:|
| `FEISHU_WEBHOOK_URL` | 飞书群机器人 Webhook 地址 | ✅ |
| `FEISHU_SECRET` | Webhook 签名密钥 | ❌ |
| `FEISHU_APP_ID` | 飞书应用 App ID | ❌ |
| `FEISHU_APP_SECRET` | 飞书应用 App Secret | ❌ |

---

## 📄 License

MIT
