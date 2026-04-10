<div align="center">

# DropAgent

eBay satıcıları üçün süni intellekt əsaslı dropshipping köməkçisi. Bazarları skan edir, marjin hesablayır, Telegram vasitəsilə günlük xülasə göndərir və trendləri izləyir — hamısı bir Docker yığımında, öz serverinizdə.

[English](./README.md) · [Русский](./README.ru.md) · [中文](./README.zh.md) · **Azərbaycan**

<br/>

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram_Bot-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![eBay](https://img.shields.io/badge/eBay_API-E53238?style=for-the-badge&logo=ebay&logoColor=white)
![Amazon](https://img.shields.io/badge/Amazon_PA--API-FF9900?style=for-the-badge&logo=amazon&logoColor=white)
![pytest](https://img.shields.io/badge/pytest-384_passing-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white)

</div>

<br/>

## Nə edə bilir

| Funksiya | Təsvir |
|---|---|
| **Günlük xülasə** | Amazon, Walmart, AliExpress, CJ skan edilir → eBay satış qiymətləri ilə müqayisə → xalis mənfəətə görə sıralanır |
| **Marjin kalkulyatoru** | Alış qiyməti, satış qiyməti, çatdırılma, qablaşdırma → eBay komissiyası (13%), ödəniş komissiyası → xalis mənfəət, marjin %, ROI |
| **Trend aşkarlaması** | Google Trends + Reddit skaneri — yüksələn axtarış sözlərini və erkən hype siqnallarını tapır |
| **Elan generatoru** | eBay üçün optimallaşdırılmış başlıq, təsvir, bulet nöqtələri, kateqoriya və xüsusiyyətlər — toplu rejim dəstəklənir |
| **Rəqib izləyicisi** | eBay satıcılarını izlə, elanlarını müşahidə et, yeni məhsul əlavə edildikdə bildiriş al |
| **Məhsul izlənilmə siyahısı** | Məhsul üzrə qiymət tarixi, alış qiyməti düşdükdə və ya satış qiyməti artdıqda xəbərdarlıq |
| **Həftəlik hesabat** | Kateqoriyalar üzrə ən yaxşı məhsullar və trend istiqaməti (yüksəlir / sabit / düşür) |
| **Bildirişlər** | Telegram (əsas), Email, Discord webhook, Google Sheets ixracı |
| **Veb lövhəsi** | Marjin kalkulyatoru, xülasə önizləməsi, analitika, parametrlər — PWA, oflayn işləyir |
| **Çoxdilli** | English · Русский · 中文 — bot və lövhədə tam i18n dəstəyi |
| **Çox istifadəçili** | Hər istifadəçi üçün ayrı profil, parametrlər və tarix — öz serverinizdə, SaaS yoxdur |

<br/>

## Dəstəklənən biznes modelləri

**Model 1 — ABŞ Pərakəndə Arbitrajı**
Amazon, Walmart, Target, Costco, BestBuy-dan al → eBay-da sat. Fokus: qiymət fərqi, sürətli ABŞ çatdırılması, hər məhsulda $5–30 marjin.

**Model 2 — Çin Dropshipping**
AliExpress, CJDropshipping-dən al → eBay və ya Shopify-da sat. Fokus: yüksək qiymət artımı, trend məhsullar, 3–10x marjin.

<br/>

## Sürətli başlanğıc

```bash
git clone https://github.com/Efsirr/dropagent.git
cd dropagent
cp .env.example .env
# .env faylında API açarlarınızı doldurun
docker compose up --build
```

Lövhə `http://localhost:8000` ünvanında açılır.
`TELEGRAM_BOT_TOKEN` təyin edildikdən sonra bot avtomatik işə düşür.

<br/>

## Telegram əmrləri

| Əmr | Təsvir |
|---|---|
| `/calc 25 49.99` | Sürətli marjin hesablaması |
| `/digest` | Bu günün xülasəsini çalışdır və göndər |
| `/trends electronics` | Kateqoriyada yüksələn açar sözlər |
| `/listing AirPods Pro` | eBay elanı yarat |
| `/watchlist` | İzlənilən məhsulları idarə et |
| `/competitor` | eBay satıcılarını izlə |
| `/weekly electronics` | Kateqoriya üzrə həftəlik hesabat |
| `/settings` | Parametrləri yenilə |
| `/language` | Dili dəyişdir: EN / RU / ZH |

<br/>

## CLI alətləri

```bash
python3 calc.py 25 49.99                        # marjin kalkulyatoru
python3 digest.py --query "airpods pro"          # günlük xülasə
python3 trends.py --category electronics         # trend skanı
python3 weekly_report.py --category electronics  # həftəlik hesabat
python3 -m bot.main                              # Telegram botu
python3 -m dashboard.backend.server              # veb lövhəsi
```

<br/>

## Layihə strukturu

```
dropagent/
├── agent/          # Əsas məntiq: skaner, analizator, trendlər, elanlar, rəqiblər
│   └── sources/    # Bazar adapterləri: Amazon, Walmart, AliExpress, CJ
├── bot/            # Telegram botu, işləyicilər, klaviaturalar, onboarding
├── dashboard/      # Veb lövhəsi — FastAPI backend + vanilla JS frontend (PWA)
├── db/             # SQLAlchemy modellər, Alembic miqrasiyalar
├── i18n/           # Tərcümə faylları EN / RU / ZH
├── tests/          # 383 test
├── docker-compose.yml
├── Dockerfile
└── .env.example
```

<br/>

## Tələb olunan API açarları

| Xidmət | Haradan almaq | Tələb olunur |
|---|---|---|
| Telegram Bot Token | [@BotFather](https://t.me/BotFather) | **Bəli** |
| eBay App ID | [developer.ebay.com](https://developer.ebay.com) | Skan üçün |
| Amazon PA-API | [affiliate-program.amazon.com](https://affiliate-program.amazon.com) | Model 1 |
| Walmart API | [developer.walmart.com](https://developer.walmart.com) | Model 1 |
| AliExpress API | [AliExpress Open Platform](https://developers.aliexpress.com) | Model 2 |
| CJDropshipping API | [app.cjdropshipping.com](https://app.cjdropshipping.com) | Model 2 |

<br/>

## Texnologiyalar

- **Python 3.9+**, asinxron HTTP üçün `httpx`
- **SQLAlchemy 2.0** + Alembic miqrasiyalar (standart SQLite, PostgreSQL dəstəklənir)
- **pytrends** Google Trends üçün, **PRAW** Reddit üçün
- **Vanilla JS** lövhəsi — freymvorksuz, build addımı yoxdur
- **Docker Compose** — hər şeyi bir əmrlə işə salır

<br/>

