<div align="center">

# DropAgent

ИИ-ассистент для дропшиппинга на eBay. Сканирует маркетплейсы, рассчитывает маржу, доставляет ежедневные дайджесты через Telegram и отслеживает тренды — всё в одном Docker-стеке на вашем сервере.

[English](./README.md) · **Русский** · [中文](./README.zh.md) · [Azərbaycan](./README.az.md)

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

## Что умеет

| Функция | Описание |
|---|---|
| **Ежедневный дайджест** | Сканирует Amazon, Walmart, AliExpress, CJ → сравнивает с ценами продаж на eBay → ранжирует по чистой прибыли |
| **Калькулятор маржи** | Цена покупки, продажи, доставка, упаковка → комиссия eBay (13%), комиссия платёжной системы → чистая прибыль, маржа %, ROI |
| **Анализ трендов** | Google Trends + Reddit-сканер для поиска растущих запросов и ранних сигналов хайпа |
| **Генератор объявлений** | Оптимизированный заголовок, описание, буллеты, категория и характеристики для eBay — есть пакетный режим |
| **Трекер конкурентов** | Мониторинг продавцов на eBay, отслеживание объявлений, уведомления о новых товарах |
| **Список отслеживания** | История цен по товару, уведомление при падении цены покупки или росте цены продажи |
| **Еженедельный отчёт** | Топ товаров по категориям с направлением тренда (растёт / стабильно / падает) |
| **Уведомления** | Telegram (основной), Email, Discord webhook, экспорт в Google Sheets |
| **Веб-дашборд** | Калькулятор маржи, превью дайджеста, аналитика, настройки — PWA, работает офлайн |
| **Мультиязычность** | English · Русский · 中文 — полная локализация бота и дашборда |
| **Мультипользовательность** | Отдельные профили, настройки и история для каждого пользователя — self-hosted, без SaaS |

<br/>

## Поддерживаемые бизнес-модели

**Модель 1 — Арбитраж в США**
Закупка на Amazon, Walmart, Target, Costco, BestBuy → продажа на eBay. Фокус: ценовые разрывы, быстрая доставка по США, маржа $5–30 за товар.

**Модель 2 — Дропшиппинг из Китая**
Закупка на AliExpress, CJDropshipping → продажа на eBay или Shopify. Фокус: высокая наценка, трендовые товары, маржа 3–10x.

<br/>

## Быстрый старт

```bash
git clone https://github.com/Efsirr/dropagent.git
cd dropagent
cp .env.example .env
# Заполните API-ключи в .env
docker compose up --build
```

Дашборд откроется на `http://localhost:8000`.
Бот запустится автоматически после установки `TELEGRAM_BOT_TOKEN`.

<br/>

## Команды Telegram

| Команда | Описание |
|---|---|
| `/calc 25 49.99` | Быстрый расчёт маржи |
| `/digest` | Запустить и получить сегодняшний дайджест |
| `/trends electronics` | Растущие запросы в категории |
| `/listing AirPods Pro` | Сгенерировать объявление для eBay |
| `/watchlist` | Управление отслеживаемыми товарами |
| `/competitor` | Отслеживать продавцов на eBay |
| `/weekly electronics` | Еженедельный отчёт по категории |
| `/settings` | Обновить настройки |
| `/language` | Сменить язык: EN / RU / ZH |

<br/>

## CLI-инструменты

```bash
python3 calc.py 25 49.99                        # калькулятор маржи
python3 digest.py --query "airpods pro"          # ежедневный дайджест
python3 trends.py --category electronics         # сканирование трендов
python3 weekly_report.py --category electronics  # еженедельный отчёт
python3 -m bot.main                              # Telegram-бот
python3 -m dashboard.backend.server              # веб-дашборд
```

<br/>

## Структура проекта

```
dropagent/
├── agent/          # Основная логика: сканер, анализатор, тренды, объявления, конкуренты
│   └── sources/    # Адаптеры маркетплейсов: Amazon, Walmart, AliExpress, CJ
├── bot/            # Telegram-бот, обработчики, клавиатуры, онбординг
├── dashboard/      # Веб-дашборд — FastAPI бэкенд + vanilla JS фронтенд (PWA)
├── db/             # SQLAlchemy модели, Alembic миграции
├── i18n/           # Переводы EN / RU / ZH
├── tests/          # 282 теста
├── docker-compose.yml
├── Dockerfile
└── .env.example
```

<br/>

## Необходимые API-ключи

| Сервис | Где получить | Обязателен |
|---|---|---|
| Telegram Bot Token | [@BotFather](https://t.me/BotFather) | **Да** |
| eBay App ID | [developer.ebay.com](https://developer.ebay.com) | Для сканирования |
| Amazon PA-API | [affiliate-program.amazon.com](https://affiliate-program.amazon.com) | Модель 1 |
| Walmart API | [developer.walmart.com](https://developer.walmart.com) | Модель 1 |
| AliExpress API | [AliExpress Open Platform](https://developers.aliexpress.com) | Модель 2 |
| CJDropshipping API | [app.cjdropshipping.com](https://app.cjdropshipping.com) | Модель 2 |

<br/>

## Технологии

- **Python 3.9+** с `httpx` для асинхронных HTTP-запросов
- **SQLAlchemy 2.0** + Alembic миграции (SQLite по умолчанию, PostgreSQL поддерживается)
- **pytrends** для Google Trends, **PRAW** для Reddit
- **Vanilla JS** дашборд — без фреймворков, без сборщика
- **Docker Compose** — одна команда для запуска всего стека

<br/>

