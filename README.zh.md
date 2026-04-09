<div align="center">

# DropAgent

面向 eBay 卖家的 AI 驱动代发货助手。扫描多个平台、计算利润率、通过 Telegram 发送每日摘要并追踪市场趋势——一键 Docker 部署，完全自托管。

[English](./README.md) · [Русский](./README.ru.md) · **中文** · [Azərbaycan](./README.az.md)

<br/>

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram_Bot-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![eBay](https://img.shields.io/badge/eBay_API-E53238?style=for-the-badge&logo=ebay&logoColor=white)
![Amazon](https://img.shields.io/badge/Amazon_PA--API-FF9900?style=for-the-badge&logo=amazon&logoColor=white)
![pytest](https://img.shields.io/badge/pytest-282_passing-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white)

</div>

<br/>

## 功能概览

| 功能 | 说明 |
|---|---|
| **每日摘要** | 扫描 Amazon、Walmart、AliExpress、CJ → 与 eBay 已售价格对比 → 按净利润排名 |
| **利润计算器** | 进货价、售价、运费、包装费 → eBay 手续费（13%）、支付手续费 → 净利润、利润率、ROI |
| **趋势检测** | Google Trends + Reddit 扫描器，发现上升搜索词和早期爆款信号 |
| **Listing 生成器** | 生成 eBay 优化标题、描述、卖点列表、分类建议和商品属性——支持批量模式 |
| **竞争对手追踪** | 监控指定 eBay 卖家、追踪其在售商品、新品上架时即时提醒 |
| **商品监控列表** | 商品价格历史记录，进货价下降或售价上涨时自动提醒 |
| **周报** | 按品类展示热门商品及趋势方向（上升 / 稳定 / 下降） |
| **通知推送** | Telegram（主要）、Email、Discord Webhook、导出至 Google Sheets |
| **网页仪表盘** | 利润计算器、摘要预览、数据分析、设置——PWA，支持离线使用 |
| **多语言** | English · Русский · 中文——机器人和仪表盘完整国际化 |
| **多用户** | 每位用户独立档案、设置和历史记录——自托管，无 SaaS |

<br/>

## 支持的商业模式

**模式一 — 美国零售套利**
从 Amazon、Walmart、Target、Costco、BestBuy 采购 → 在 eBay 出售。重点：价格差、美国本土快速发货，每件利润 $5–30。

**模式二 — 中国代发货**
从 AliExpress、CJDropshipping 采购 → 在 eBay 或 Shopify 出售。重点：高加价、爆款商品，利润 3–10 倍。

<br/>

## 快速开始

```bash
git clone https://github.com/Efsirr/dropagent.git
cd dropagent
cp .env.example .env
# 在 .env 中填写您的 API 密钥
docker compose up --build
```

仪表盘地址：`http://localhost:8000`
设置好 `TELEGRAM_BOT_TOKEN` 后，机器人将自动启动。

<br/>

## Telegram 命令

| 命令 | 说明 |
|---|---|
| `/calc 25 49.99` | 快速利润计算 |
| `/digest` | 运行并发送今日摘要 |
| `/trends electronics` | 查看品类上升关键词 |
| `/listing AirPods Pro` | 生成 eBay Listing |
| `/watchlist` | 管理监控商品 |
| `/competitor` | 追踪 eBay 卖家 |
| `/weekly electronics` | 品类周报 |
| `/settings` | 更新偏好设置 |
| `/language` | 切换语言：EN / RU / ZH |

<br/>

## 命令行工具

```bash
python3 calc.py 25 49.99                        # 利润计算器
python3 digest.py --query "airpods pro"          # 每日摘要
python3 trends.py --category electronics         # 趋势扫描
python3 weekly_report.py --category electronics  # 周报
python3 -m bot.main                              # Telegram 机器人
python3 -m dashboard.backend.server              # 网页仪表盘
```

<br/>

## 项目结构

```
dropagent/
├── agent/          # 核心逻辑：扫描器、分析器、趋势、Listing 生成、竞争对手
│   └── sources/    # 平台适配器：Amazon、Walmart、AliExpress、CJ
├── bot/            # Telegram 机器人、处理器、键盘、引导流程
├── dashboard/      # 网页仪表盘——FastAPI 后端 + 原生 JS 前端（PWA）
├── db/             # SQLAlchemy 模型，Alembic 迁移
├── i18n/           # 翻译文件 EN / RU / ZH
├── tests/          # 282 个测试
├── docker-compose.yml
├── Dockerfile
└── .env.example
```

<br/>

## 所需 API 密钥

| 服务 | 获取地址 | 是否必须 |
|---|---|---|
| Telegram Bot Token | [@BotFather](https://t.me/BotFather) | **必须** |
| eBay App ID | [developer.ebay.com](https://developer.ebay.com) | 扫描功能 |
| Amazon PA-API | [affiliate-program.amazon.com](https://affiliate-program.amazon.com) | 模式一 |
| Walmart API | [developer.walmart.com](https://developer.walmart.com) | 模式一 |
| AliExpress API | [AliExpress Open Platform](https://developers.aliexpress.com) | 模式二 |
| CJDropshipping API | [app.cjdropshipping.com](https://app.cjdropshipping.com) | 模式二 |

<br/>

## 技术栈

- **Python 3.9+**，使用 `httpx` 处理异步 HTTP 请求
- **SQLAlchemy 2.0** + Alembic 迁移（默认 SQLite，支持 PostgreSQL）
- **pytrends** 用于 Google Trends，**PRAW** 用于 Reddit
- **原生 JS** 仪表盘——无框架，无构建步骤
- **Docker Compose**——一条命令启动全部服务

<br/>

