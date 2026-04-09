const API_BASE = "/api";
const SOURCE_OPTIONS = [
  ["amazon", "Amazon"],
  ["walmart", "Walmart"],
  ["aliexpress", "AliExpress"],
  ["cj", "CJDropshipping"],
];
const INTEGRATION_LABELS = new Map([
  ["amazon", "Amazon"],
  ["walmart", "Walmart"],
  ["aliexpress", "AliExpress"],
  ["cj", "CJDropshipping"],
  ["keepa", "Keepa"],
  ["zik", "ZIK Analytics"],
  ["storeleads", "StoreLeads"],
  ["similarweb", "SimilarWeb"],
  ["pipiads", "PiPiADS"],
  ["minea", "Minea"],
]);
const INTEGRATION_ICONS = new Map([
  ["amazon", "📦"],
  ["walmart", "🏬"],
  ["aliexpress", "🇨🇳"],
  ["cj", "📋"],
  ["keepa", "📈"],
  ["zik", "🔍"],
  ["storeleads", "🏪"],
  ["similarweb", "🌐"],
  ["pipiads", "📱"],
  ["minea", "🎯"],
]);

const LABELS = {
  en: {
    "hero.title": "Research workspace",
    "hero.lede": "Read the numbers, spot movement, and make decisions from one calm screen built for daily reseller work.",
    "hero.api_base": "API base",
    "hero.status": "Status",
    "profile.label": "Profile",
    "profile.title": "Load a Telegram chat",
    "profile.chat_id": "Telegram chat ID",
    "profile.username": "Username",
    "profile.pref_lang": "Preferred language",
    "profile.load_btn": "Load profile",
    "profile.refresh_btn": "Refresh",
    "profile.summary_empty": "Load a profile to unlock analytics.",
    "profile.summary_user": "User",
    "profile.summary_chat": "Chat",
    "profile.summary_lang": "Language",
    "profile.summary_digest": "Digest",
    "profile.summary_setup": "Setup",
    "profile.digest_off": "off",
    "setup.label": "Setup",
    "setup.title": "Connect your services",
    "setup.empty": "Load a profile to see what's ready and what services to connect.",
    "setup.business_model": "Business model",
    "setup.save_btn": "Save setup",
    "setup.baseline_ready": "Core setup ready",
    "setup.baseline_missing": "Core setup incomplete",
    "setup.integrations": "Connected services",
    "setup.onboarding_done": "Setup wizard complete",
    "setup.onboarding_open": "Setup wizard still open",
    "setup.feature_gate": "Complete the core setup first to unlock this.",
    "setup.integration_configured": "connected",
    "setup.integration_missing": "not set up",
    "setup.capabilities": "What you can do right now",
    "setup.next_step_label": "Next step",
    "setup.next_step_empty": "Load a profile to see your next action.",
    "note.ready_now": "Ready now.",
    "note.add_later": "Add later",
    "note.analytics": "Watchlist and competitor tracking work now. Connect {integrations} later for deeper validation.",
    "note.discovery": "Use one query to compare competitor stores, ad traction, and related search movement.",
    "note.weekly": "Weekly signals work now. Connect {integrations} later to strengthen discovery.",
    "note.digest": "Digest works once your core setup is ready and at least one source is connected.",
    "note.notifications": "Notifications are optional. Connect only the channels you actually plan to use.",
    "analytics.label": "Analytics",
    "analytics.title": "Watchlist and competitor pulse",
    "overview.margin_floor": "Margin floor",
    "overview.watchlist_count": "Watchlist items",
    "overview.competitor_count": "Tracked sellers",
    "overview.query_count": "Tracked queries",
    "overview.best_buy": "Lowest watch buy",
    "overview.best_profit": "Best net profit target",
    "watchlist.label": "Watchlist",
    "watchlist.title": "Price history",
    "watchlist.source": "Source",
    "watchlist.product_name": "Product",
    "watchlist.buy_now": "Current buy",
    "watchlist.sell_now": "Current sell",
    "watchlist.add_btn": "Add to watchlist",
    "watchlist.empty": "No watchlist items yet.",
    "watchlist.points": "History points",
    "watchlist.target_gap": "Target spread",
    "watchlist.no_history": "Need at least one saved price point to draw a chart.",
    "watchlist.remove_btn": "Remove",
    "competitor.label": "Competitors",
    "competitor.panel_title": "Seller movement",
    "competitor.seller_input": "Seller username",
    "competitor.add_btn": "Track seller",
    "competitor.empty": "No competitors tracked yet.",
    "competitor.scan_empty": "Run a seller scan to see new items and category movement.",
    "competitor.scan_btn": "Run scan",
    "competitor.remove_btn": "Remove",
    "competitor.known_items": "Known items",
    "competitor.last_scan": "Last scan",
    "competitor.query_hint": "Optional query focus",
    "weekly.label": "Weekly report",
    "weekly.panel_title": "Category direction",
    "weekly.categories": "Categories",
    "weekly.top_products": "Top products",
    "weekly.trend_limit": "Trend keywords",
    "weekly.preview_btn": "Preview weekly report",
    "weekly.empty": "No weekly report preview yet.",
    "digest.label": "Digest preview",
    "digest.title": "Opportunity snapshot",
    "digest.empty": "No digest preview yet.",
    "digest.top": "Top results",
    "digest.limit": "Limit",
    "digest.title_label": "Title",
    "digest.preview_btn": "Preview digest",
    "tracked.label": "Tracked queries",
    "tracked.title": "Saved search table",
    "tracked.query": "Query",
    "tracked.category": "Category",
    "tracked.add_btn": "Add query",
    "tracked.reload_btn": "Reload list",
    "tracked.empty": "No tracked queries loaded yet.",
    "tracked.remove_btn": "Remove",
    "tracked.saved_query": "Saved query",
    "store_leads.label": "Store leads",
    "store_leads.title": "Saved discovery stores",
    "store_leads.empty": "No saved store leads yet.",
    "store_leads.save_btn": "Save store",
    "store_leads.remove_btn": "Remove",
    "store_leads.query": "Discovery query",
    "discovery_hub.label": "Discovery hub",
    "discovery_hub.title": "Find what is moving right now",
    "discovery_hub.query": "Product or niche",
    "discovery_hub.limit": "Results",
    "discovery_hub.run_btn": "Run discovery",
    "discovery_hub.stores_label": "Competitor stores",
    "discovery_hub.stores_title": "Where this niche is selling",
    "discovery_hub.ads_label": "Ad signals",
    "discovery_hub.ads_title": "What creatives are getting traction",
    "discovery_hub.trends_label": "Trend signals",
    "discovery_hub.trends_title": "Related search movement",
    "discovery_hub.empty_stores": "Run discovery to see competitor stores.",
    "discovery_hub.empty_ads": "Run discovery to see trending ads.",
    "discovery_hub.empty_trends": "Run discovery to see related trend signals.",
    "discovery_hub.save_query": "Save query",
    "discovery_hub.save_keyword": "Save keyword",
    "discovery_hub.watch_item": "Watch item",
    "discovery_hub.recent_label": "Recent discovery",
    "discovery_hub.recent_title": "Last research runs",
    "discovery_hub.empty_history": "Run discovery once to build your recent research history.",
    "workflow.discover": "Discover",
    "workflow.analytics": "Analytics",
    "workflow.digest": "Digest",
    "workflow.reports": "Reports",
    "settings.label": "Settings",
    "settings.title": "Operational preferences",
    "settings.min_profit": "Min profit",
    "settings.max_buy": "Max buy price",
    "settings.language": "Language",
    "settings.schedule": "Schedule",
    "settings.sources": "Sources",
    "settings.save_btn": "Save settings",
    "schedule.off": "Off",
    "schedule.daily": "Every day",
    "schedule.2days": "Every 2 days",
    "schedule.3days": "Every 3 days",
    "schedule.weekly": "Weekly",
    "calc.label": "Margin calculator",
    "calc.title": "Quick profit check",
    "calc.empty": "No calculation yet.",
    "calc.result": "Margin result",
    "calc.profit": "PROFIT",
    "calc.loss": "LOSS",
    "calc.buy_price": "Buy price",
    "calc.sell_price": "Sell price",
    "calc.shipping": "Shipping",
    "calc.packaging": "Packaging",
    "calc.platform_fee": "Platform fee",
    "calc.payment_fee": "Payment fee",
    "calc.total_fees": "Total fees",
    "calc.total_cost": "Total cost",
    "calc.net_profit": "Net profit",
    "calc.margin": "Margin",
    "calc.roi": "ROI",
    "calc.markup": "Markup",
    "calc.business_model": "Business model",
    "calc.model_us": "US arbitrage",
    "calc.model_china": "China dropshipping",
    "calc.platform": "Platform",
    "calc.run_btn": "Run calculator",
    "common.auto": "Auto",
    "common.unknown": "unknown",
    "status.ready": "Ready",
    "status.loading_profile": "Loading profile...",
    "status.profile_loaded": "Profile loaded",
    "status.saving_settings": "Saving settings...",
    "status.settings_saved": "Settings saved",
    "status.saving_query": "Saving tracked query...",
    "status.query_saved": "Tracked query saved",
    "status.removing_query": "Removing tracked query...",
    "status.query_removed": "Tracked query removed",
    "status.saving_store_lead": "Saving store lead...",
    "status.store_lead_saved": "Store lead saved",
    "status.removing_store_lead": "Removing store lead...",
    "status.store_lead_removed": "Store lead removed",
    "status.previewing_digest": "Previewing digest...",
    "status.digest_ready": "Digest preview ready",
    "status.previewing_weekly": "Previewing weekly report...",
    "status.discovery_running": "Running discovery...",
    "status.discovery_ready": "Discovery results ready",
    "status.weekly_ready": "Weekly report ready",
    "status.saving_watch": "Saving watchlist item...",
    "status.watch_saved": "Watchlist updated",
    "status.saving_competitor": "Saving competitor...",
    "status.competitor_saved": "Competitor saved",
    "status.scanning_competitor": "Scanning competitor...",
    "status.competitor_ready": "Competitor scan ready",
    "status.calculating": "Calculating margin...",
    "status.calculated": "Margin calculated",
    "error.chat_id_required": "Telegram chat ID is required",
    "error.load_profile_first": "Load a profile first",
    "error.query_required": "Query is required",
    "error.product_required": "Product name is required",
    "error.categories_required": "Add at least one category",
    "error.seller_required": "Seller username is required",
    "error.discovery_required": "Add a product or niche to run discovery",
    "notify.label": "Notifications",
    "notify.title": "Export & alerts",
    "notify.webhook_url": "Webhook URL",
    "notify.email_to": "Recipient",
    "notify.sheet_id": "Spreadsheet ID",
    "notify.send_test": "Send test",
    "notify.send_digest": "Send digest",
    "notify.export_digest": "Export digest",
    "notify.export_watchlist": "Export watchlist",
    "notify.status_idle": "Configure a channel above and click to send.",
    "notify.status_sending": "Sending...",
    "notify.status_sent": "Sent successfully!",
    "notify.status_error": "Failed to send. Check configuration.",
    "services.heading": "Recommended services",
    "services.subtext": "Connect the tools that power your research. Each service adds a capability.",
    "services.connected": "Connected",
    "services.not_connected": "Not connected",
    "services.planned": "Coming soon",
    "services.connect": "Connect",
    "services.disconnect": "Disconnect",
    "services.add_later": "Add later",
    "services.coming_soon": "Coming soon",
    "services.connect_btn": "Connect",
    "services.cancel_btn": "Cancel",
    "services.dialog_desc": "Paste your API key below. It will be encrypted and stored securely.",
    "services.saving": "Saving...",
    "services.save_success": "Connected! Service key saved securely.",
    "services.save_error": "Failed to save. Check your key and try again.",
    "services.disconnected": "Service disconnected",
    "services.disconnect_error": "Failed to disconnect",
    "footer.text": "DropAgent dashboard · analytics-first workspace · connects to /api",
  },
  ru: {
    "hero.title": "Рабочее пространство аналитики",
    "hero.lede": "Смотрите на цифры, замечайте движение и принимайте решения с одного спокойного экрана для ежедневной работы реселлера.",
    "hero.api_base": "API базовый URL",
    "hero.status": "Статус",
    "profile.label": "Профиль",
    "profile.title": "Загрузить Telegram чат",
    "profile.chat_id": "ID чата Telegram",
    "profile.username": "Имя пользователя",
    "profile.pref_lang": "Предпочтительный язык",
    "profile.load_btn": "Загрузить профиль",
    "profile.refresh_btn": "Обновить",
    "profile.summary_empty": "Загрузите профиль, чтобы открыть аналитику.",
    "profile.summary_user": "Пользователь",
    "profile.summary_chat": "Чат",
    "profile.summary_lang": "Язык",
    "profile.summary_digest": "Дайджест",
    "profile.summary_setup": "Настройка",
    "profile.digest_off": "выкл.",
    "setup.label": "Настройка",
    "setup.title": "Подключение сервисов",
    "setup.empty": "Загрузи профиль, чтобы увидеть, что готово и какие сервисы подключить.",
    "setup.business_model": "Бизнес-модель",
    "setup.save_btn": "Сохранить настройку",
    "setup.baseline_ready": "Основная настройка готова",
    "setup.baseline_missing": "Основная настройка не завершена",
    "setup.integrations": "Подключённые сервисы",
    "setup.onboarding_done": "Мастер настройки завершён",
    "setup.onboarding_open": "Мастер настройки ещё не завершён",
    "setup.feature_gate": "Сначала заверши основную настройку.",
    "setup.integration_configured": "подключено",
    "setup.integration_missing": "не настроено",
    "setup.capabilities": "Что уже доступно",
    "setup.next_step_label": "Следующий шаг",
    "setup.next_step_empty": "Загрузи профиль, чтобы увидеть следующее действие.",
    "note.ready_now": "Доступно сейчас.",
    "note.add_later": "Подключишь позже",
    "note.analytics": "Список наблюдения и конкуренты уже работают. Позже можно подключить {integrations} для более глубокой проверки.",
    "note.discovery": "Один запрос показывает магазины-конкуренты, рекламный спрос и движение поискового интереса.",
    "note.weekly": "Недельные сигналы уже работают. Позже можно подключить {integrations} для усиления поиска.",
    "note.digest": "Дайджест заработает, когда основная настройка готова и подключён хотя бы один источник.",
    "note.notifications": "Уведомления опциональны. Подключай только те каналы, которые реально будешь использовать.",
    "analytics.label": "Аналитика",
    "analytics.title": "Пульс watchlist и конкурентов",
    "overview.margin_floor": "Порог прибыли",
    "overview.watchlist_count": "Товаров в watchlist",
    "overview.competitor_count": "Конкурентов",
    "overview.query_count": "Отслеживаемых запросов",
    "overview.best_buy": "Лучшая цена закупки",
    "overview.best_profit": "Лучшая целевая прибыль",
    "watchlist.label": "Watchlist",
    "watchlist.title": "История цен",
    "watchlist.source": "Источник",
    "watchlist.product_name": "Товар",
    "watchlist.buy_now": "Текущая закупка",
    "watchlist.sell_now": "Текущая продажа",
    "watchlist.add_btn": "Добавить в watchlist",
    "watchlist.empty": "Товаров в watchlist пока нет.",
    "watchlist.points": "Точек истории",
    "watchlist.target_gap": "Целевой спред",
    "watchlist.no_history": "Нужна хотя бы одна сохранённая точка цены, чтобы показать график.",
    "watchlist.remove_btn": "Удалить",
    "competitor.label": "Конкуренты",
    "competitor.panel_title": "Движение продавцов",
    "competitor.seller_input": "Имя продавца",
    "competitor.add_btn": "Отслеживать продавца",
    "competitor.empty": "Конкуренты пока не отслеживаются.",
    "competitor.scan_empty": "Запустите скан продавца, чтобы увидеть новые товары и категории.",
    "competitor.scan_btn": "Сканировать",
    "competitor.remove_btn": "Удалить",
    "competitor.known_items": "Известных товаров",
    "competitor.last_scan": "Последний скан",
    "competitor.query_hint": "Необязательный фокус-запрос",
    "weekly.label": "Недельный отчёт",
    "weekly.panel_title": "Движение категорий",
    "weekly.categories": "Категории",
    "weekly.top_products": "Топ товаров",
    "weekly.trend_limit": "Трендовые ключи",
    "weekly.preview_btn": "Предпросмотр недельного отчёта",
    "weekly.empty": "Предпросмотра недельного отчёта пока нет.",
    "digest.label": "Предпросмотр дайджеста",
    "digest.title": "Снимок возможностей",
    "digest.empty": "Дайджест ещё не загружен.",
    "digest.top": "Топ результатов",
    "digest.limit": "Лимит",
    "digest.title_label": "Заголовок",
    "digest.preview_btn": "Предпросмотр дайджеста",
    "tracked.label": "Отслеживаемые запросы",
    "tracked.title": "Таблица сохранённых поисков",
    "tracked.query": "Запрос",
    "tracked.category": "Категория",
    "tracked.add_btn": "Добавить запрос",
    "tracked.reload_btn": "Обновить список",
    "tracked.empty": "Отслеживаемых запросов пока нет.",
    "tracked.remove_btn": "Удалить",
    "tracked.saved_query": "Сохранённый запрос",
    "store_leads.label": "Store leads",
    "store_leads.title": "Сохранённые магазины из discovery",
    "store_leads.empty": "Сохранённых store leads пока нет.",
    "store_leads.save_btn": "Сохранить магазин",
    "store_leads.remove_btn": "Удалить",
    "store_leads.query": "Запрос discovery",
    "discovery_hub.label": "Discovery hub",
    "discovery_hub.title": "Что двигается прямо сейчас",
    "discovery_hub.query": "Товар или ниша",
    "discovery_hub.limit": "Результатов",
    "discovery_hub.run_btn": "Запустить поиск",
    "discovery_hub.stores_label": "Магазины-конкуренты",
    "discovery_hub.stores_title": "Где эта ниша уже продаётся",
    "discovery_hub.ads_label": "Рекламные сигналы",
    "discovery_hub.ads_title": "Какие креативы набирают оборот",
    "discovery_hub.trends_label": "Тренд-сигналы",
    "discovery_hub.trends_title": "Связанный поисковый рост",
    "discovery_hub.empty_stores": "Запусти discovery, чтобы увидеть магазины-конкуренты.",
    "discovery_hub.empty_ads": "Запусти discovery, чтобы увидеть трендовую рекламу.",
    "discovery_hub.empty_trends": "Запусти discovery, чтобы увидеть сигналы тренда.",
    "discovery_hub.save_query": "Сохранить запрос",
    "discovery_hub.save_keyword": "Сохранить ключевое слово",
    "discovery_hub.watch_item": "Следить за товаром",
    "discovery_hub.recent_label": "Недавний discovery",
    "discovery_hub.recent_title": "Последние исследования",
    "discovery_hub.empty_history": "Запусти discovery один раз, и здесь появится история поисков.",
    "workflow.discover": "Поиск",
    "workflow.analytics": "Аналитика",
    "workflow.digest": "Дайджест",
    "workflow.reports": "Отчёты",
    "settings.label": "Настройки",
    "settings.title": "Операционные параметры",
    "settings.min_profit": "Мин. прибыль",
    "settings.max_buy": "Макс. цена покупки",
    "settings.language": "Язык",
    "settings.schedule": "Расписание",
    "settings.sources": "Источники",
    "settings.save_btn": "Сохранить настройки",
    "schedule.off": "Выкл.",
    "schedule.daily": "Каждый день",
    "schedule.2days": "Каждые 2 дня",
    "schedule.3days": "Каждые 3 дня",
    "schedule.weekly": "Еженедельно",
    "calc.label": "Калькулятор маржи",
    "calc.title": "Быстрая проверка прибыли",
    "calc.empty": "Расчёт ещё не выполнен.",
    "calc.result": "Результат расчёта",
    "calc.profit": "ПРИБЫЛЬ",
    "calc.loss": "УБЫТОК",
    "calc.buy_price": "Цена покупки",
    "calc.sell_price": "Цена продажи",
    "calc.shipping": "Доставка",
    "calc.packaging": "Упаковка",
    "calc.platform_fee": "Комиссия площадки",
    "calc.payment_fee": "Комиссия за оплату",
    "calc.total_fees": "Итого комиссии",
    "calc.total_cost": "Общая себестоимость",
    "calc.net_profit": "Чистая прибыль",
    "calc.margin": "Маржа",
    "calc.roi": "ROI",
    "calc.markup": "Наценка",
    "calc.business_model": "Бизнес-модель",
    "calc.model_us": "Арбитраж США",
    "calc.model_china": "Китайский дропшиппинг",
    "calc.platform": "Площадка",
    "calc.run_btn": "Рассчитать",
    "common.auto": "Авто",
    "common.unknown": "неизвестно",
    "status.ready": "Готов",
    "status.loading_profile": "Загрузка профиля...",
    "status.profile_loaded": "Профиль загружен",
    "status.saving_settings": "Сохранение настроек...",
    "status.settings_saved": "Настройки сохранены",
    "status.saving_query": "Сохранение запроса...",
    "status.query_saved": "Запрос сохранён",
    "status.removing_query": "Удаление запроса...",
    "status.query_removed": "Запрос удалён",
    "status.saving_store_lead": "Сохранение магазина...",
    "status.store_lead_saved": "Магазин сохранён",
    "status.removing_store_lead": "Удаление магазина...",
    "status.store_lead_removed": "Магазин удалён",
    "status.previewing_digest": "Предпросмотр дайджеста...",
    "status.digest_ready": "Дайджест готов",
    "status.previewing_weekly": "Формирование недельного отчёта...",
    "status.discovery_running": "Ищем сигналы...",
    "status.discovery_ready": "Discovery готов",
    "status.weekly_ready": "Недельный отчёт готов",
    "status.saving_watch": "Сохранение watchlist...",
    "status.watch_saved": "Watchlist обновлён",
    "status.saving_competitor": "Сохранение конкурента...",
    "status.competitor_saved": "Конкурент сохранён",
    "status.scanning_competitor": "Сканирование конкурента...",
    "status.competitor_ready": "Скан конкурента готов",
    "status.calculating": "Расчёт маржи...",
    "status.calculated": "Маржа рассчитана",
    "error.chat_id_required": "Нужен ID чата Telegram",
    "error.load_profile_first": "Сначала загрузите профиль",
    "error.query_required": "Введите запрос",
    "error.product_required": "Введите название товара",
    "error.categories_required": "Добавьте хотя бы одну категорию",
    "error.seller_required": "Необходимо имя продавца",
    "error.discovery_required": "Добавь товар или нишу для discovery",
    "notify.label": "Уведомления",
    "notify.title": "Экспорт и оповещения",
    "notify.webhook_url": "URL вебхука",
    "notify.email_to": "Получатель",
    "notify.sheet_id": "ID таблицы",
    "notify.send_test": "Тестовое",
    "notify.send_digest": "Отправить дайджест",
    "notify.export_digest": "Экспорт дайджеста",
    "notify.export_watchlist": "Экспорт watchlist",
    "notify.status_idle": "Настройте канал выше и нажмите для отправки.",
    "notify.status_sending": "Отправка...",
    "notify.status_sent": "Отправлено успешно!",
    "notify.status_error": "Ошибка отправки. Проверьте настройки.",
    "services.heading": "Рекомендуемые сервисы",
    "services.subtext": "Подключите инструменты для анализа. Каждый сервис добавляет возможности.",
    "services.connected": "Подключён",
    "services.not_connected": "Не подключён",
    "services.planned": "Скоро",
    "services.connect": "Подключить",
    "services.disconnect": "Отключить",
    "services.add_later": "Позже",
    "services.coming_soon": "Скоро",
    "services.connect_btn": "Подключить",
    "services.cancel_btn": "Отмена",
    "services.dialog_desc": "Вставьте ваш API-ключ. Он будет зашифрован и сохранён.",
    "services.saving": "Сохранение...",
    "services.save_success": "Подключено! Ключ сохранён.",
    "services.save_error": "Ошибка сохранения. Проверьте ключ.",
    "services.disconnected": "Сервис отключён",
    "services.disconnect_error": "Ошибка отключения",
    "footer.text": "DropAgent · analytics-first workspace · подключается к /api",
  },
  zh: {
    "hero.title": "研究工作台",
    "hero.lede": "在一个平静的界面里查看数字、识别变化，并为日常转卖工作做决定。",
    "hero.api_base": "API 地址",
    "hero.status": "状态",
    "profile.label": "资料",
    "profile.title": "加载 Telegram 会话",
    "profile.chat_id": "Telegram 会话 ID",
    "profile.username": "用户名",
    "profile.pref_lang": "首选语言",
    "profile.load_btn": "加载资料",
    "profile.refresh_btn": "刷新",
    "profile.summary_empty": "加载资料后即可查看分析面板。",
    "profile.summary_user": "用户",
    "profile.summary_chat": "会话",
    "profile.summary_lang": "语言",
    "profile.summary_digest": "日报",
    "profile.summary_setup": "设置",
    "profile.digest_off": "关闭",
    "setup.label": "设置",
    "setup.title": "连接您的服务",
    "setup.empty": "加载资料，查看哪些已准备就绪以及需要连接哪些服务。",
    "setup.business_model": "业务模式",
    "setup.save_btn": "保存设置",
    "setup.baseline_ready": "核心设置已就绪",
    "setup.baseline_missing": "核心设置未完成",
    "setup.integrations": "已连接服务",
    "setup.onboarding_done": "设置向导已完成",
    "setup.onboarding_open": "设置向导尚未完成",
    "setup.feature_gate": "请先完成核心设置后再使用此功能。",
    "setup.integration_configured": "已连接",
    "setup.integration_missing": "未设置",
    "setup.capabilities": "您现在能做什么",
    "setup.next_step_label": "下一步",
    "setup.next_step_empty": "加载资料后查看下一步操作。",
    "note.ready_now": "现在可用。",
    "note.add_later": "以后再连接",
    "note.analytics": "观察列表和竞争对手跟踪现在可用。以后可连接 {integrations} 做更深入的验证。",
    "note.discovery": "一次查询即可同时查看竞争店铺、广告热度和相关搜索动向。",
    "note.weekly": "每周信号现在可用。以后可连接 {integrations} 增强发现能力。",
    "note.digest": "核心设置就绪且至少连接一个来源后，日报就能工作。",
    "note.notifications": "通知是可选的。只连接你真正计划使用的渠道。",
    "analytics.label": "分析",
    "analytics.title": "Watchlist 与竞争对手动态",
    "overview.margin_floor": "最低利润门槛",
    "overview.watchlist_count": "Watchlist 商品数",
    "overview.competitor_count": "追踪卖家数",
    "overview.query_count": "追踪词数量",
    "overview.best_buy": "最低采购价",
    "overview.best_profit": "最佳目标利润",
    "watchlist.label": "Watchlist",
    "watchlist.title": "价格历史",
    "watchlist.source": "来源",
    "watchlist.product_name": "商品",
    "watchlist.buy_now": "当前采购价",
    "watchlist.sell_now": "当前售价",
    "watchlist.add_btn": "加入 watchlist",
    "watchlist.empty": "暂无 watchlist 商品。",
    "watchlist.points": "历史点数",
    "watchlist.target_gap": "目标价差",
    "watchlist.no_history": "至少需要一个已保存价格点才能绘制图表。",
    "watchlist.remove_btn": "删除",
    "competitor.label": "竞争对手",
    "competitor.panel_title": "卖家动态",
    "competitor.seller_input": "卖家用户名",
    "competitor.add_btn": "追踪卖家",
    "competitor.empty": "暂无追踪的竞争对手。",
    "competitor.scan_empty": "运行卖家扫描后可查看新商品和分类变化。",
    "competitor.scan_btn": "开始扫描",
    "competitor.remove_btn": "删除",
    "competitor.known_items": "已知商品",
    "competitor.last_scan": "上次扫描",
    "competitor.query_hint": "可选聚焦关键词",
    "weekly.label": "每周报告",
    "weekly.panel_title": "分类方向",
    "weekly.categories": "分类",
    "weekly.top_products": "热门商品数",
    "weekly.trend_limit": "趋势关键词数",
    "weekly.preview_btn": "预览每周报告",
    "weekly.empty": "暂无每周报告预览。",
    "digest.label": "日报预览",
    "digest.title": "机会快照",
    "digest.empty": "暂无日报预览。",
    "digest.top": "前几名",
    "digest.limit": "数量限制",
    "digest.title_label": "标题",
    "digest.preview_btn": "预览日报",
    "tracked.label": "追踪词",
    "tracked.title": "已保存搜索表",
    "tracked.query": "搜索词",
    "tracked.category": "分类",
    "tracked.add_btn": "添加搜索词",
    "tracked.reload_btn": "刷新列表",
    "tracked.empty": "暂无追踪词。",
    "tracked.remove_btn": "删除",
    "tracked.saved_query": "已保存搜索词",
    "store_leads.label": "店铺线索",
    "store_leads.title": "已保存的发现店铺",
    "store_leads.empty": "还没有保存的店铺线索。",
    "store_leads.save_btn": "保存店铺",
    "store_leads.remove_btn": "删除",
    "store_leads.query": "发现查询",
    "discovery_hub.label": "发现中心",
    "discovery_hub.title": "看看现在什么正在升温",
    "discovery_hub.query": "产品或细分领域",
    "discovery_hub.limit": "结果数",
    "discovery_hub.run_btn": "开始发现",
    "discovery_hub.stores_label": "竞争店铺",
    "discovery_hub.stores_title": "这个细分领域在哪些店铺在卖",
    "discovery_hub.ads_label": "广告信号",
    "discovery_hub.ads_title": "哪些创意正在获得关注",
    "discovery_hub.trends_label": "趋势信号",
    "discovery_hub.trends_title": "相关搜索动向",
    "discovery_hub.empty_stores": "运行发现后查看竞争店铺。",
    "discovery_hub.empty_ads": "运行发现后查看热门广告。",
    "discovery_hub.empty_trends": "运行发现后查看趋势信号。",
    "discovery_hub.save_query": "保存查询",
    "discovery_hub.save_keyword": "保存关键词",
    "discovery_hub.watch_item": "加入观察",
    "discovery_hub.recent_label": "最近发现",
    "discovery_hub.recent_title": "最近研究记录",
    "discovery_hub.empty_history": "先运行一次发现，这里就会显示最近的研究记录。",
    "workflow.discover": "发现",
    "workflow.analytics": "分析",
    "workflow.digest": "摘要",
    "workflow.reports": "报告",
    "settings.label": "设置",
    "settings.title": "操作偏好",
    "settings.min_profit": "最低利润",
    "settings.max_buy": "最高采购价",
    "settings.language": "语言",
    "settings.schedule": "计划",
    "settings.sources": "来源",
    "settings.save_btn": "保存设置",
    "schedule.off": "关闭",
    "schedule.daily": "每天",
    "schedule.2days": "每2天",
    "schedule.3days": "每3天",
    "schedule.weekly": "每周",
    "calc.label": "利润计算器",
    "calc.title": "快速利润检查",
    "calc.empty": "尚未进行计算。",
    "calc.result": "计算结果",
    "calc.profit": "盈利",
    "calc.loss": "亏损",
    "calc.buy_price": "采购价",
    "calc.sell_price": "售价",
    "calc.shipping": "运费",
    "calc.packaging": "包装费",
    "calc.platform_fee": "平台佣金",
    "calc.payment_fee": "支付手续费",
    "calc.total_fees": "总费用",
    "calc.total_cost": "总成本",
    "calc.net_profit": "净利润",
    "calc.margin": "利润率",
    "calc.roi": "投资回报率",
    "calc.markup": "加价倍数",
    "calc.business_model": "业务模式",
    "calc.model_us": "美国套利",
    "calc.model_china": "中国代发",
    "calc.platform": "平台",
    "calc.run_btn": "开始计算",
    "common.auto": "自动",
    "common.unknown": "未知",
    "status.ready": "就绪",
    "status.loading_profile": "加载资料中...",
    "status.profile_loaded": "资料已加载",
    "status.saving_settings": "保存设置中...",
    "status.settings_saved": "设置已保存",
    "status.saving_query": "保存搜索词中...",
    "status.query_saved": "搜索词已保存",
    "status.removing_query": "删除搜索词中...",
    "status.query_removed": "搜索词已删除",
    "status.saving_store_lead": "正在保存店铺...",
    "status.store_lead_saved": "店铺已保存",
    "status.removing_store_lead": "正在删除店铺...",
    "status.store_lead_removed": "店铺已删除",
    "status.previewing_digest": "正在预览日报...",
    "status.digest_ready": "日报预览已就绪",
    "status.previewing_weekly": "正在生成每周报告...",
    "status.discovery_running": "正在发现信号...",
    "status.discovery_ready": "发现结果已就绪",
    "status.weekly_ready": "每周报告已就绪",
    "status.saving_watch": "正在保存 watchlist...",
    "status.watch_saved": "Watchlist 已更新",
    "status.saving_competitor": "正在保存竞争对手...",
    "status.competitor_saved": "竞争对手已保存",
    "status.scanning_competitor": "正在扫描竞争对手...",
    "status.competitor_ready": "竞争对手扫描已完成",
    "status.calculating": "计算利润中...",
    "status.calculated": "计算完成",
    "error.chat_id_required": "请输入 Telegram 会话 ID",
    "error.load_profile_first": "请先加载资料",
    "error.query_required": "请输入搜索词",
    "error.product_required": "请输入商品名称",
    "error.categories_required": "请至少填写一个分类",
    "error.seller_required": "请输入卖家用户名",
    "error.discovery_required": "请输入产品或细分领域以运行发现",
    "notify.label": "通知",
    "notify.title": "导出与提醒",
    "notify.webhook_url": "Webhook URL",
    "notify.email_to": "收件人",
    "notify.sheet_id": "表格 ID",
    "notify.send_test": "测试发送",
    "notify.send_digest": "发送日报",
    "notify.export_digest": "导出日报",
    "notify.export_watchlist": "导出观察列表",
    "notify.status_idle": "配置上方通道后点击发送。",
    "notify.status_sending": "发送中...",
    "notify.status_sent": "发送成功！",
    "notify.status_error": "发送失败，请检查配置。",
    "services.heading": "推荐服务",
    "services.subtext": "连接工具以增强您的研究能力，每项服务增加一种功能。",
    "services.connected": "已连接",
    "services.not_connected": "未连接",
    "services.planned": "即将推出",
    "services.connect": "连接",
    "services.disconnect": "断开",
    "services.add_later": "稍后添加",
    "services.coming_soon": "即将推出",
    "services.connect_btn": "连接",
    "services.cancel_btn": "取消",
    "services.dialog_desc": "粘贴您的API密钥。它将被加密安全存储。",
    "services.saving": "保存中...",
    "services.save_success": "已连接！密钥已安全保存。",
    "services.save_error": "保存失败，请检查密钥并重试。",
    "services.disconnected": "服务已断开",
    "services.disconnect_error": "断开失败",
    "footer.text": "DropAgent · analytics-first workspace · 连接到 /api",
  },
};

const state = {
  profile: null,
  calcResult: null,
  digestPreview: null,
  weeklyPreview: null,
  competitorPreview: null,
  discoveryHub: null,
  integrationSelection: [],
  chatId: "",
  currentLang: localStorage.getItem("dropagent.lang") || "en",
};

function l(key) {
  return (LABELS[state.currentLang] || LABELS.en)[key] || LABELS.en[key] || key;
}

function qs(id) {
  return document.getElementById(id);
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

// ── Empty state helper ───────────────────────────────────────────────────────
// Renders a friendly empty state block into a container element.
// icon: SVG string or emoji (pass "" to omit)
// title: short headline
// body: one sentence explaining what this section does or how to start
// cta: optional { label, action } where action is a CSS selector to scroll to or a function
function renderEmptyState(containerId, { icon = "", title, body, cta } = {}) {
  const el = document.getElementById(containerId);
  if (!el) return;
  el.classList.add("has-empty-state");
  el.innerHTML = `
    <div class="empty-state-block" role="status">
      ${icon ? `<div class="empty-state-icon" aria-hidden="true">${icon}</div>` : ""}
      <p class="empty-state-title">${escapeHtml(title)}</p>
      <p class="empty-state-body">${escapeHtml(body)}</p>
      ${cta ? `<button type="button" class="btn btn-ghost btn-small empty-state-cta" data-cta-target="${escapeHtml(cta.target || "")}">${escapeHtml(cta.label)}</button>` : ""}
    </div>`;
  if (cta?.target) {
    el.querySelector(".empty-state-cta")?.addEventListener("click", () => {
      const target = document.getElementById(cta.target);
      if (target) target.scrollIntoView({ behavior: "smooth", block: "center" });
      const firstInput = target?.querySelector("input, select, textarea");
      if (firstInput) firstInput.focus();
    });
  }
}

// Seed empty states on page load — replaced by real data when loaded
function seedEmptyStates() {
  renderEmptyState("watchlist-analytics", {
    icon: `<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7z"/><circle cx="12" cy="12" r="3"/></svg>`,
    title: "No products being watched",
    body: "Add a product to track its buy and sell price over time. You'll see the spread widen — that's your signal.",
    cta: { label: "Add your first product", target: "watch-form" },
  });

  renderEmptyState("competitor-list", {
    icon: `<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>`,
    title: "No sellers being tracked",
    body: "Enter an eBay seller username to monitor their listings. When they add new products, you'll see it here.",
    cta: { label: "Track a seller", target: "competitor-form" },
  });

  renderEmptyState("tracked-queries", {
    icon: `<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>`,
    title: "No saved searches",
    body: "Save a product search here and DropAgent will include it in your daily digest automatically.",
    cta: { label: "Add a search", target: "track-form" },
  });

  renderEmptyState("digest-output", {
    icon: `<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>`,
    title: "No digest loaded yet",
    body: "Enter search terms above and click Preview digest to see today's best profit opportunities ranked by margin.",
    cta: { label: "Preview now", target: "digest-form" },
  });

  renderEmptyState("weekly-output", {
    icon: `<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>`,
    title: "No weekly report yet",
    body: "Enter one or more categories and run a preview. You'll see which products are rising, which are stable, and where momentum is shifting.",
    cta: { label: "Run a report", target: "weekly-form" },
  });

  renderEmptyState("competitor-output", {
    icon: `<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>`,
    title: "No scan results yet",
    body: "Track a seller first, then run a scan to see their recent listings and category movement.",
  });

  renderEmptyState("calc-output", {
    icon: `<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="2" width="16" height="20" rx="2"/><line x1="8" y1="6" x2="16" y2="6"/><line x1="8" y1="10" x2="16" y2="10"/><line x1="8" y1="14" x2="12" y2="14"/></svg>`,
    title: "Enter prices above to calculate profit",
    body: "Put in what you pay and what you'll sell for. DropAgent deducts eBay fees, shipping, and packaging — and tells you exactly what you'll make.",
  });
}

function formatCurrency(value) {
  if (value == null || Number.isNaN(Number(value))) return "—";
  return `$${Number(value).toFixed(2)}`;
}

function formatDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleDateString(state.currentLang === "zh" ? "zh-CN" : state.currentLang === "ru" ? "ru-RU" : "en-US", {
    month: "short",
    day: "numeric",
  });
}

function toNumberOrNull(value) {
  if (value === "" || value == null) return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function selectedSources() {
  return SOURCE_OPTIONS.filter(([value]) => {
    const input = qs(`source-${value}`);
    return input && input.checked;
  }).map(([value]) => value);
}

function selectedIntegrations() {
  const checked = Array.from(document.querySelectorAll("[data-integration-toggle]:checked"));
  return checked.map((node) => node.value);
}

function currentSetupStatus() {
  return state.profile?.setup_status || { baseline_ready: false, baseline: [], integrations: [] };
}

function integrationConfigured(id) {
  return Boolean(currentSetupStatus().integrations?.find((item) => item.integration_id === id)?.configured);
}

function integrationSelected(id) {
  return Boolean(state.profile?.selected_integrations?.includes(id));
}

function requireBaselineReady() {
  if (!currentSetupStatus().baseline_ready) {
    throw new Error(l("setup.feature_gate"));
  }
}

function setStatus(text, kind = "idle") {
  const node = qs("api-status");
  if (!node) return;
  node.textContent = text;
  node.dataset.kind = kind;
}

function setMessage(message, kind = "muted") {
  const node = qs("profile-summary");
  if (!node) return;
  node.textContent = message;
  node.className = kind === "error" ? "summary danger" : "summary muted";
}

function template(text, values = {}) {
  return Object.entries(values).reduce(
    (result, [key, value]) => result.replaceAll(`{${key}}`, value),
    text,
  );
}

function applyLanguage(lang) {
  state.currentLang = lang;
  localStorage.setItem("dropagent.lang", lang);
  document.documentElement.lang = lang;

  document.querySelectorAll("[data-i18n]").forEach((node) => {
    node.textContent = l(node.dataset.i18n);
  });
  document.querySelectorAll(".lang-btn").forEach((btn) => {
    const isActive = btn.dataset.lang === lang;
    btn.classList.toggle("active", isActive);
    btn.setAttribute("aria-pressed", isActive ? "true" : "false");
  });

  if (state.profile) renderProfile(state.profile);
  if (state.calcResult) renderCalcResult(state.calcResult);
  if (state.digestPreview) renderTextOutput("digest-output", state.digestPreview.summary);
  if (state.weeklyPreview) renderTextOutput("weekly-output", state.weeklyPreview.summary);
  if (state.competitorPreview) renderTextOutput("competitor-output", state.competitorPreview.summary);
  if (state.discoveryHub) renderDiscoveryHub(state.discoveryHub);
}

async function apiRequest(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || `Request failed with ${response.status}`);
  }
  return payload;
}

function sparklinePath(values, width, height) {
  if (!values.length) return "";
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = Math.max(max - min, 1);
  return values.map((value, index) => {
    const x = (index / Math.max(values.length - 1, 1)) * width;
    const y = height - ((value - min) / range) * height;
    return `${index === 0 ? "M" : "L"}${x.toFixed(2)},${y.toFixed(2)}`;
  }).join(" ");
}

function renderTextOutput(id, text) {
  const node = qs(id);
  if (!node) return;
  node.innerHTML = `<pre class="digest-pre">${escapeHtml(text)}</pre>`;
}

function renderCalcResult(data) {
  const node = qs("calc-output");
  if (!node) return;
  const profitable = data.is_profitable;
  node.innerHTML = `
    <div class="calc-result">
      <div class="calc-result-header">
        <span class="calc-result-title">${l("calc.result")}</span>
        <span class="badge ${profitable ? "badge-profit" : "badge-loss"}">${profitable ? l("calc.profit") : l("calc.loss")}</span>
      </div>
      <div class="result-grid">
        <div class="result-metric highlight">
          <span>${l("calc.net_profit")}</span>
          <strong class="${profitable ? "good" : "bad"}">${formatCurrency(data.net_profit)}</strong>
        </div>
        <div class="result-metric">
          <span>${l("calc.margin")}</span>
          <strong>${Number(data.margin_percent).toFixed(2)}%</strong>
        </div>
        <div class="result-metric">
          <span>${l("calc.roi")}</span>
          <strong>${Number(data.roi_percent).toFixed(2)}%</strong>
        </div>
        <div class="result-metric">
          <span>${l("calc.markup")}</span>
          <strong>${Number(data.markup).toFixed(2)}x</strong>
        </div>
      </div>
      <div class="result-breakdown">
        <div class="breakdown-row"><span>${l("calc.buy_price")}</span><strong>${formatCurrency(data.buy_price)}</strong></div>
        <div class="breakdown-row"><span>${l("calc.sell_price")}</span><strong>${formatCurrency(data.sell_price)}</strong></div>
        <div class="breakdown-row muted"><span>${l("calc.shipping")}</span><strong>${formatCurrency(data.shipping_cost)}</strong></div>
        <div class="breakdown-row muted"><span>${l("calc.packaging")}</span><strong>${formatCurrency(data.packaging_cost)}</strong></div>
        <div class="breakdown-row muted"><span>${l("calc.platform_fee")}</span><strong>${formatCurrency(data.platform_fee)}</strong></div>
        <div class="breakdown-row muted"><span>${l("calc.payment_fee")}</span><strong>${formatCurrency(data.payment_fee)}</strong></div>
        <div class="breakdown-divider"></div>
        <div class="breakdown-row"><span>${l("calc.total_fees")}</span><strong>${formatCurrency(data.total_fees)}</strong></div>
        <div class="breakdown-row"><span>${l("calc.total_cost")}</span><strong>${formatCurrency(data.total_cost)}</strong></div>
      </div>
    </div>
  `;
}

function renderSources(profile) {
  const container = qs("sources-list");
  container.innerHTML = "";
  const enabled = new Set(profile.enabled_sources || []);
  SOURCE_OPTIONS.forEach(([value, label]) => {
    const wrapper = document.createElement("label");
    wrapper.className = "source-option";
    wrapper.innerHTML = `
      <input id="source-${value}" type="checkbox" value="${value}" ${enabled.size ? (enabled.has(value) ? "checked" : "") : "checked"} />
      <span>${label}</span>
    `;
    container.appendChild(wrapper);
  });
}

function renderOverview(profile) {
  const watchlist = profile.watchlist_items || [];
  const tracked = profile.tracked_queries || [];
  const competitors = profile.tracked_competitors || [];
  const bestBuy = watchlist
    .map((item) => item.current_buy_price)
    .filter((value) => value != null)
    .sort((a, b) => a - b)[0];
  const bestProfit = watchlist
    .map((item) => {
      if (item.current_buy_price == null || item.current_sell_price == null) return null;
      return item.current_sell_price - item.current_buy_price;
    })
    .filter((value) => value != null)
    .sort((a, b) => b - a)[0];

  const cards = [
    [l("overview.margin_floor"), formatCurrency(profile.min_profit_threshold)],
    [l("overview.watchlist_count"), String(watchlist.length)],
    [l("overview.competitor_count"), String(competitors.length)],
    [l("overview.query_count"), String(tracked.length)],
    [l("overview.best_buy"), bestBuy != null ? formatCurrency(bestBuy) : "—"],
    [l("overview.best_profit"), bestProfit != null ? formatCurrency(bestProfit) : "—"],
  ];

  qs("overview-grid").innerHTML = cards.map(([label, value]) => `
    <article class="overview-card">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(value)}</strong>
    </article>
  `).join("");
}

function renderTrackedQueries(profile) {
  const container = qs("tracked-queries");
  const tracked = profile.tracked_queries || [];
  if (!tracked.length) {
    container.className = "data-table empty-state";
    container.textContent = l("tracked.empty");
    return;
  }

  container.className = "data-table";
  container.innerHTML = `
    <div class="table-head">
      <span>${l("tracked.query")}</span>
      <span>${l("tracked.category")}</span>
      <span>${l("settings.min_profit")}</span>
      <span>${l("settings.max_buy")}</span>
      <span></span>
    </div>
    ${tracked.map((item) => `
      <div class="table-row">
        <strong>${escapeHtml(item.query)}</strong>
        <span>${escapeHtml(item.category || "—")}</span>
        <span>${item.min_profit_threshold != null ? formatCurrency(item.min_profit_threshold) : "—"}</span>
        <span>${item.max_buy_price != null ? formatCurrency(item.max_buy_price) : "—"}</span>
        <button type="button" class="btn btn-ghost btn-small" data-remove-query="${escapeHtml(item.query)}" data-remove-category="${escapeHtml(item.category || "")}">${l("tracked.remove_btn")}</button>
      </div>
    `).join("")}
  `;
}

function renderWatchlist(profile) {
  const container = qs("watchlist-analytics");
  const items = profile.watchlist_items || [];
  if (!items.length) {
    container.className = "analytics-stack empty-state";
    container.textContent = l("watchlist.empty");
    return;
  }

  container.className = "analytics-stack";
  container.innerHTML = items.map((item) => {
    const buySeries = (item.price_history || []).map((point) => point.buy_price).filter((value) => value != null);
    const sellSeries = (item.price_history || []).map((point) => point.sell_price).filter((value) => value != null);
    const lineValues = buySeries.length ? buySeries : sellSeries;
    const spread = item.current_buy_price != null && item.current_sell_price != null
      ? item.current_sell_price - item.current_buy_price
      : null;
    const chart = lineValues.length
      ? `
        <svg class="mini-chart" viewBox="0 0 240 76" role="img" aria-label="${escapeHtml(item.product_name)} chart">
          <path class="chart-line" d="${sparklinePath(lineValues, 240, 76)}"></path>
        </svg>
      `
      : `<div class="mini-chart-empty">${l("watchlist.no_history")}</div>`;

    return `
      <article class="analytics-card">
        <div class="analytics-card-head">
          <div>
            <strong>${escapeHtml(item.product_name)}</strong>
            <span>${escapeHtml(item.source)}</span>
          </div>
          <button type="button" class="btn btn-ghost btn-small" data-remove-watch="${item.item_id}">${l("watchlist.remove_btn")}</button>
        </div>
        ${chart}
        <div class="analytics-meta">
          <span>${l("watchlist.buy_now")}: <strong>${formatCurrency(item.current_buy_price)}</strong></span>
          <span>${l("watchlist.sell_now")}: <strong>${formatCurrency(item.current_sell_price)}</strong></span>
          <span>${l("watchlist.points")}: <strong>${(item.price_history || []).length}</strong></span>
          <span>${l("watchlist.target_gap")}: <strong>${spread != null ? formatCurrency(spread) : "—"}</strong></span>
        </div>
      </article>
    `;
  }).join("");
}

function renderCompetitors(profile) {
  const container = qs("competitor-list");
  const items = profile.tracked_competitors || [];
  if (!items.length) {
    container.className = "analytics-stack empty-state";
    container.textContent = l("competitor.empty");
    return;
  }

  container.className = "analytics-stack";
  container.innerHTML = items.map((item) => `
    <article class="analytics-card analytics-card-compact">
      <div class="analytics-card-head">
        <div>
          <strong>${escapeHtml(item.label || item.seller_username)}</strong>
          <span>${escapeHtml(item.seller_username)}</span>
        </div>
        <div class="inline-actions">
          <button type="button" class="btn btn-ghost btn-small" data-scan-competitor="${item.competitor_id}">${l("competitor.scan_btn")}</button>
          <button type="button" class="btn btn-ghost btn-small" data-remove-competitor="${item.competitor_id}">${l("competitor.remove_btn")}</button>
        </div>
      </div>
      <div class="analytics-meta">
        <span>${l("competitor.known_items")}: <strong>${item.known_item_count}</strong></span>
        <span>${l("competitor.last_scan")}: <strong>${item.last_scan_at ? formatDate(item.last_scan_at) : "—"}</strong></span>
      </div>
    </article>
  `).join("");
}

function renderStoreLeads(profile) {
  const container = qs("store-leads-list");
  if (!container) return;
  const items = profile.saved_store_leads || [];
  if (!items.length) {
    container.className = "analytics-stack empty-state";
    container.textContent = l("store_leads.empty");
    return;
  }

  container.className = "analytics-stack";
  container.innerHTML = items.map((item) => `
    <article class="analytics-card analytics-card-compact">
      <div class="analytics-card-head">
        <div>
          <strong>${escapeHtml(item.merchant_name || item.domain)}</strong>
          <span>${escapeHtml(item.domain)}</span>
        </div>
        <button type="button" class="btn btn-ghost btn-small" data-remove-store-lead="${item.store_lead_id}">${l("store_leads.remove_btn")}</button>
      </div>
      <div class="analytics-meta">
        <span>${l("store_leads.query")}: <strong>${escapeHtml(item.niche_query || "—")}</strong></span>
        <span>Visits: <strong>${item.estimated_visits != null ? formatCompact(item.estimated_visits) : "—"}</strong></span>
        <span>Sales: <strong>${item.estimated_sales_monthly_usd != null ? formatCurrency(item.estimated_sales_monthly_usd) : "—"}</strong></span>
      </div>
    </article>
  `).join("");
}

function renderDiscoveryHistory(profile) {
  const container = qs("discovery-history");
  if (!container) return;
  const items = profile.discovery_runs || [];
  if (!items.length) {
    container.className = "analytics-stack empty-state";
    container.textContent = l("discovery_hub.empty_history");
    return;
  }

  container.className = "analytics-stack";
  container.innerHTML = items.map((item) => `
    <article class="analytics-card analytics-card-compact">
      <div class="analytics-card-head">
        <div>
          <strong>${escapeHtml(item.query)}</strong>
          <span>${item.created_at ? formatDate(item.created_at) : "—"}</span>
        </div>
      </div>
      <div class="analytics-meta">
        <span>Stores: <strong>${item.store_count ?? 0}</strong></span>
        <span>Ads: <strong>${item.ad_count ?? 0}</strong></span>
        <span>Trends: <strong>${item.trend_count ?? 0}</strong></span>
        <span>Limit: <strong>${item.result_limit ?? "—"}</strong></span>
      </div>
      ${item.summary ? `<div class="summary muted">${escapeHtml(item.summary)}</div>` : ""}
    </article>
  `).join("");
}

function renderDiscoveryList(id, items, emptyIcon, emptyText, summaryHtml, formatter) {
  const node = qs(id);
  if (!node) return;
  if (!items || !items.length) {
    node.className = "analytics-stack empty-state";
    node.innerHTML = `<span class="empty-state-icon">${emptyIcon}</span>${emptyText}`;
    return;
  }
  node.className = "analytics-stack";
  const bar = summaryHtml ? `<div class="discovery-summary">${summaryHtml}</div>` : "";
  node.innerHTML = bar + items.map(formatter).join("");
}

function formatCompact(n) {
  if (n == null) return "—";
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + "M";
  if (n >= 1_000) return (n / 1_000).toFixed(1) + "K";
  return n.toLocaleString();
}

function scoreBadge(score, label) {
  if (score == null) return "";
  const tier = score >= 5000 ? "hot" : score >= 1000 ? "warm" : "cool";
  const icon = tier === "hot" ? "🔥" : tier === "warm" ? "⚡" : "💡";
  return `<span class="score-badge score-badge-${tier}">${icon} ${label || score}</span>`;
}

function trendBadge(score) {
  if (score == null) return "";
  const tier = score >= 80 ? "hot" : score >= 50 ? "warm" : "cool";
  const icon = tier === "hot" ? "📈" : tier === "warm" ? "↗" : "→";
  return `<span class="score-badge score-badge-${tier}">${icon} ${score}</span>`;
}

function renderDiscoveryHub(data) {
  const stores = data.store_report?.stores || [];
  const ads = data.ad_report?.ads || [];
  const trends = data.trend_report?.keywords || [];

  // ── Stores ──
  const storeAvg = stores.length
    ? stores.reduce((s, st) => s + (st.avg_price_usd || 0), 0) / stores.length
    : 0;
  const storeSummary = stores.length
    ? `<strong>${stores.length}</strong> store${stores.length > 1 ? "s" : ""} · avg price <strong>${formatCurrency(storeAvg)}</strong>`
    : "";

  renderDiscoveryList(
    "discovery-stores", stores, "🏪",
    l("discovery_hub.empty_stores"), storeSummary,
    (store) => `
      <article class="discovery-card">
        <div class="discovery-card-head">
          <div>
            <strong>${escapeHtml(store.merchant_name || store.domain || "Store")}</strong>
            <div class="subtitle">
              ${store.platform ? `<span class="platform-tag">${escapeHtml(store.platform)}</span> ` : ""}${escapeHtml(store.domain || "")}${store.country_code ? ` · ${store.country_code}` : ""}
            </div>
          </div>
          ${store.rank ? `<span class="score-badge score-badge-cool">#${formatCompact(store.rank)}</span>` : ""}
        </div>
        <div class="discovery-metrics">
          <span>Visits <strong>${formatCompact(store.estimated_visits)}</strong></span>
          <span>Sales/mo <strong>${store.estimated_sales_monthly_usd != null ? formatCurrency(store.estimated_sales_monthly_usd) : "—"}</strong></span>
          <span>Avg price <strong>${store.avg_price_usd != null ? formatCurrency(store.avg_price_usd) : "—"}</strong></span>
          <span>Products <strong>${formatCompact(store.product_count)}</strong></span>
        </div>
        <div class="discovery-actions">
          <button
            type="button"
            class="btn-xs btn-xs-accent"
            data-save-store="${escapeHtml(store.domain || "")}"
            data-store-name="${escapeHtml(store.merchant_name || "")}"
            data-store-query="${escapeHtml(data.query || "")}"
            data-store-visits="${store.estimated_visits ?? ""}"
            data-store-sales="${store.estimated_sales_monthly_usd ?? ""}"
            data-store-avg-price="${store.avg_price_usd ?? ""}"
          >${l("store_leads.save_btn")}</button>
        </div>
      </article>
    `,
  );

  // ── Ads ──
  const topScore = ads.length ? Math.max(...ads.map(a => a.trend_score || 0)) : 0;
  const adSummary = ads.length
    ? `<strong>${ads.length}</strong> ad${ads.length > 1 ? "s" : ""} · top score <strong>${formatCompact(topScore)}</strong>`
    : "";

  renderDiscoveryList(
    "discovery-ads", ads, "📢",
    l("discovery_hub.empty_ads"), adSummary,
    (ad) => `
      <article class="discovery-card">
        <div class="discovery-card-head">
          <div>
            <strong>${escapeHtml(ad.title || "Untitled ad")}</strong>
            <div class="subtitle">${escapeHtml(ad.advertiser || "Unknown advertiser")}</div>
          </div>
          ${scoreBadge(ad.trend_score, formatCompact(ad.trend_score))}
        </div>
        <div class="discovery-metrics">
          <span>❤️ <strong>${formatCompact(ad.total_likes)}</strong></span>
          <span>💬 <strong>${formatCompact(ad.total_comments)}</strong></span>
          <span>🔁 <strong>${formatCompact(ad.total_shares)}</strong></span>
          <span>📅 <strong>${ad.days_running || 0}d</strong></span>
        </div>
        <div class="discovery-actions">
          ${ad.landing_page ? `<a href="${escapeHtml(ad.landing_page)}" target="_blank" rel="noopener" class="btn-xs">View page ↗</a>` : ""}
          <button
            type="button"
            class="btn-xs"
            data-watch-product="${escapeHtml(ad.title || data.query || "")}"
            data-watch-url="${escapeHtml(ad.landing_page || "")}"
          >${l("discovery_hub.watch_item")}</button>
          <button type="button" class="btn-xs btn-xs-accent" data-save-query="${escapeHtml(data.query || "")}" data-save-category="ad-discovery">${l("discovery_hub.save_query")}</button>
        </div>
      </article>
    `,
  );

  // ── Trends ──
  const avgScore = trends.length
    ? Math.round(trends.reduce((s, t) => s + (t.score || 0), 0) / trends.length)
    : 0;
  const trendSummary = trends.length
    ? `<strong>${trends.length}</strong> keyword${trends.length > 1 ? "s" : ""} · avg score <strong>${avgScore}</strong>`
    : "";

  renderDiscoveryList(
    "discovery-trends", trends, "📊",
    l("discovery_hub.empty_trends"), trendSummary,
    (item) => `
      <article class="discovery-card">
        <div class="discovery-card-head">
          <div>
            <strong>${escapeHtml(item.keyword || "—")}</strong>
            <div class="subtitle">${escapeHtml(item.category || data.query || "trend")}</div>
          </div>
          ${trendBadge(item.score)}
        </div>
        <div class="discovery-actions">
          <button type="button" class="btn-xs btn-xs-accent" data-save-query="${escapeHtml(item.keyword || data.query || "")}" data-save-category="${escapeHtml(item.category || data.query || "trend")}">${l("discovery_hub.save_keyword")}</button>
        </div>
      </article>
    `,
  );
}



function renderProfileSummary(profile) {
  const digestStatus = profile.digest_enabled ? `${profile.digest_interval_days}d` : l("profile.digest_off");
  const setupStatus = profile.onboarding_completed ? l("setup.onboarding_done") : l("setup.onboarding_open");
  setMessage(
    [
      `${l("profile.summary_user")}: ${profile.username || l("common.unknown")}`,
      `${l("profile.summary_chat")}: ${profile.telegram_chat_id}`,
      `${l("profile.summary_lang")}: ${profile.preferred_language || "en"}`,
      `${l("profile.summary_digest")}: ${digestStatus}`,
      `${l("profile.summary_setup")}: ${setupStatus}`,
    ].join(" · "),
  );
}

function renderFeatureNotes(profile) {
  const analyticsBoosters = [
    ["keepa", "Keepa"],
    ["storeleads", "StoreLeads"],
    ["similarweb", "SimilarWeb"],
  ]
    .filter(([id]) => !(integrationConfigured(id) || integrationSelected(id)))
    .map(([, label]) => label);
  const weeklyBoosters = [
    ["pipiads", "PiPiADS"],
    ["minea", "Minea"],
    ["storeleads", "StoreLeads"],
  ]
    .filter(([id]) => !(integrationConfigured(id) || integrationSelected(id)))
    .map(([, label]) => label);

  qs("analytics-note").textContent = analyticsBoosters.length
    ? template(l("note.analytics"), { integrations: analyticsBoosters.join(", ") })
    : l("note.ready_now");
  qs("discovery-note").textContent = l("note.discovery");
  qs("weekly-note").textContent = weeklyBoosters.length
    ? template(l("note.weekly"), { integrations: weeklyBoosters.join(", ") })
    : l("note.ready_now");
  qs("digest-note").textContent = l("note.digest");
  qs("notify-note").textContent = l("note.notifications");
}

function renderSetup(profile) {
  const summary = qs("setup-summary");
  const nextStep = qs("setup-next-step");
  const baselineList = qs("baseline-list");
  const integrationList = qs("integration-list");
  const capabilityList = qs("capability-list");
  const setupStatus = profile.setup_status || { baseline_ready: false, baseline: [], integrations: [] };
  state.integrationSelection = [...(profile.selected_integrations || [])];
  qs("setup-business-model").value = profile.business_model || "us_arbitrage";

  summary.className = setupStatus.baseline_ready ? "summary success" : "summary danger";
  summary.textContent = [
    setupStatus.baseline_ready ? l("setup.baseline_ready") : l("setup.baseline_missing"),
    `${l("setup.integrations")}: ${(profile.selected_integrations || []).join(", ") || "—"}`,
  ].join(" · ");
  nextStep.className = "summary";
  nextStep.textContent = `${l("setup.next_step_label")}: ${profile.next_step || "—"}`;

  baselineList.className = "analytics-stack";
  baselineList.innerHTML = (setupStatus.baseline || []).map((item) => `
    <div class="table-row">
      <strong>${escapeHtml(item.label)}</strong>
      <span>${escapeHtml(item.purpose)}</span>
      <span>${item.configured ? l("setup.integration_configured") : l("setup.integration_missing")}</span>
      <span>${escapeHtml(item.env_var)}</span>
    </div>
  `).join("");

  integrationList.innerHTML = (setupStatus.integrations || [])
    .filter((item) => item.recommended_for === "all" || item.recommended_for === profile.business_model)
    .map((item) => {
      const icon = INTEGRATION_ICONS.get(item.integration_id) || "🔗";
      const isConnected = item.configured;
      const isPlanned = item.status === "planned";
      const badgeClass = isConnected ? "connected" : isPlanned ? "planned" : "not-connected";
      const badgeText = isConnected
        ? l("services.connected")
        : isPlanned
          ? l("services.planned")
          : l("services.not_connected");
      const hint = state.integrationHints?.[item.integration_id] || "";

      return `
        <div class="service-card ${isConnected ? "connected" : ""}">
          <div class="service-card-header">
            <span class="service-card-icon">${icon}</span>
            <span class="service-card-title">${escapeHtml(item.label)}</span>
            <span class="service-card-badge ${badgeClass}">${badgeText}</span>
          </div>
          <div class="service-card-value">${escapeHtml(item.value)}</div>
          ${hint ? `<div class="service-card-hint">${escapeHtml(hint)}</div>` : ""}
          <div class="service-card-actions">
            ${isConnected
              ? `<button type="button" class="btn btn-disconnect" data-disconnect="${escapeHtml(item.integration_id)}">${l("services.disconnect")}</button>`
              : isPlanned
                ? `<button type="button" class="btn btn-later" disabled>${l("services.coming_soon")}</button>`
                : `<button type="button" class="btn btn-connect" data-connect="${escapeHtml(item.integration_id)}" data-connect-label="${escapeHtml(item.label)}">${l("services.connect")}</button>
                   <button type="button" class="btn btn-later" data-later="${escapeHtml(item.integration_id)}">${l("services.add_later")}</button>`
            }
          </div>
        </div>
      `;
    }).join("");

  capabilityList.className = "analytics-stack";
  capabilityList.innerHTML = `
    <div class="table-head">
      <span>${l("setup.capabilities")}</span>
      <span></span>
      <span></span>
      <span></span>
      <span></span>
    </div>
    ${(profile.capabilities || []).map((item) => `
      <div class="table-row">
        <strong>${escapeHtml(item.label)}</strong>
        <span>${escapeHtml(item.summary)}</span>
        <span>${escapeHtml(item.status)}</span>
        <span>${escapeHtml((item.suggested_integrations || []).map((id) => INTEGRATION_LABELS.get(id) || id).join(", ") || "—")}</span>
        <span></span>
      </div>
    `).join("")}
  `;
}

function applyFeatureGates(profile) {
  const baselineReady = Boolean(profile.setup_status?.baseline_ready);
  ["digest-form", "weekly-form", "track-form", "watch-form", "competitor-form", "discovery-form"].forEach((formId) => {
    const form = qs(formId);
    if (!form) return;
    form.querySelectorAll("button, input, select").forEach((node) => {
      if (node.id === "chat-id" || node.id === "username" || node.id === "preferred-language") return;
      if (!baselineReady && formId !== "calc-form") {
        if (node.tagName === "BUTTON") node.disabled = true;
      } else if (node.tagName === "BUTTON") {
        node.disabled = false;
      }
    });
  });
}

function renderProfile(profile) {
  state.profile = profile;
  state.chatId = profile.telegram_chat_id || "";
  qs("chat-id").value = profile.telegram_chat_id || "";
  qs("username").value = profile.username || "";
  qs("preferred-language").value = profile.preferred_language || "";
  qs("language").value = profile.preferred_language || "en";
  qs("setup-business-model").value = profile.business_model || "us_arbitrage";
  qs("min-profit").value = profile.min_profit_threshold ?? "";
  qs("max-buy").value = profile.max_buy_price ?? "";
  qs("schedule").value = profile.digest_enabled ? String(profile.digest_interval_days) : "off";
  renderSources(profile);
  renderOverview(profile);
  renderProfileSummary(profile);
  renderSetup(profile);
  renderFeatureNotes(profile);
  renderTrackedQueries(profile);
  renderWatchlist(profile);
  renderCompetitors(profile);
  renderStoreLeads(profile);
  renderDiscoveryHistory(profile);
  applyFeatureGates(profile);
}

async function loadProfile(chatId) {
  if (!chatId) throw new Error(l("error.chat_id_required"));
  setStatus(l("status.loading_profile"));
  const username = qs("username").value.trim();
  const preferredLanguage = qs("preferred-language").value.trim();
  const params = new URLSearchParams();
  if (username) params.set("username", username);
  if (preferredLanguage) params.set("preferred_language", preferredLanguage);
  const profile = await apiRequest(`/users/${encodeURIComponent(chatId)}${params.toString() ? `?${params}` : ""}`);
  localStorage.setItem("dropagent.chat_id", chatId);
  renderProfile(profile);
  setStatus(l("status.profile_loaded"), "success");
}

async function saveSettings(event) {
  event.preventDefault();
  if (!state.chatId) throw new Error(l("error.load_profile_first"));
  setStatus(l("status.saving_settings"));
  await apiRequest(`/users/${encodeURIComponent(state.chatId)}/settings`, {
    method: "PATCH",
    body: JSON.stringify({
      preferred_language: qs("language").value,
      business_model: qs("setup-business-model").value,
      min_profit_threshold: toNumberOrNull(qs("min-profit").value),
      max_buy_price: toNumberOrNull(qs("max-buy").value),
      enabled_sources: selectedSources(),
      selected_integrations: selectedIntegrations(),
      onboarding_completed: true,
    }),
  });
  const scheduleValue = qs("schedule").value;
  await apiRequest(`/users/${encodeURIComponent(state.chatId)}/schedule`, {
    method: "PATCH",
    body: JSON.stringify({
      enabled: scheduleValue !== "off",
      interval_days: scheduleValue === "off" ? null : Number(scheduleValue),
    }),
  });
  await loadProfile(state.chatId);
  setStatus(l("status.settings_saved"), "success");
}

async function addTrackedQuery(event) {
  event.preventDefault();
  if (!state.chatId) throw new Error(l("error.load_profile_first"));
  const query = qs("track-query").value.trim();
  if (!query) throw new Error(l("error.query_required"));
  setStatus(l("status.saving_query"));
  await apiRequest(`/users/${encodeURIComponent(state.chatId)}/tracked-queries`, {
    method: "POST",
    body: JSON.stringify({
      query,
      category: qs("track-category").value.trim() || null,
      min_profit_threshold: toNumberOrNull(qs("track-min-profit").value),
      max_buy_price: toNumberOrNull(qs("track-max-buy").value),
    }),
  });
  qs("track-query").value = "";
  qs("track-category").value = "";
  qs("track-min-profit").value = "";
  qs("track-max-buy").value = "";
  await loadProfile(state.chatId);
  setStatus(l("status.query_saved"), "success");
}

async function removeTrackedQuery(query, category) {
  if (!state.chatId) throw new Error(l("error.load_profile_first"));
  setStatus(l("status.removing_query"));
  const params = new URLSearchParams();
  if (category) params.set("category", category);
  await apiRequest(`/users/${encodeURIComponent(state.chatId)}/tracked-queries/${encodeURIComponent(query)}${params.toString() ? `?${params}` : ""}`, {
    method: "DELETE",
  });
  await loadProfile(state.chatId);
  setStatus(l("status.query_removed"), "success");
}

async function saveDiscoveryQuery(query, category) {
  if (!state.chatId) throw new Error(l("error.load_profile_first"));
  const normalizedQuery = (query || "").trim();
  if (!normalizedQuery) throw new Error(l("error.query_required"));
  setStatus(l("status.saving_query"));
  await apiRequest(`/users/${encodeURIComponent(state.chatId)}/tracked-queries`, {
    method: "POST",
    body: JSON.stringify({
      query: normalizedQuery,
      category: (category || "").trim() || null,
      min_profit_threshold: null,
      max_buy_price: null,
    }),
  });
  await loadProfile(state.chatId);
  setStatus(l("status.query_saved"), "success");
}

async function saveStoreLead({ domain, merchantName, nicheQuery, estimatedVisits, estimatedSalesMonthlyUsd, avgPriceUsd }) {
  if (!state.chatId) throw new Error(l("error.load_profile_first"));
  const normalizedDomain = (domain || "").trim();
  if (!normalizedDomain) throw new Error("domain is required");
  setStatus(l("status.saving_store_lead"));
  await apiRequest(`/users/${encodeURIComponent(state.chatId)}/store-leads`, {
    method: "POST",
    body: JSON.stringify({
      domain: normalizedDomain,
      merchant_name: (merchantName || "").trim() || null,
      niche_query: (nicheQuery || "").trim() || null,
      source_integration: "storeleads",
      estimated_visits: toNumberOrNull(estimatedVisits),
      estimated_sales_monthly_usd: toNumberOrNull(estimatedSalesMonthlyUsd),
      avg_price_usd: toNumberOrNull(avgPriceUsd),
    }),
  });
  await loadProfile(state.chatId);
  setStatus(l("status.store_lead_saved"), "success");
}

async function removeStoreLead(storeLeadId) {
  if (!state.chatId) throw new Error(l("error.load_profile_first"));
  setStatus(l("status.removing_store_lead"));
  await apiRequest(`/users/${encodeURIComponent(state.chatId)}/store-leads/${storeLeadId}`, {
    method: "DELETE",
  });
  await loadProfile(state.chatId);
  setStatus(l("status.store_lead_removed"), "success");
}

async function saveDiscoveryWatchItem(productName, productUrl = "") {
  if (!state.chatId) throw new Error(l("error.load_profile_first"));
  const normalizedName = (productName || "").trim();
  if (!normalizedName) throw new Error(l("error.product_required"));
  const source = state.profile?.business_model === "china_dropshipping" ? "aliexpress" : "amazon";
  setStatus(l("status.saving_watch"));
  await apiRequest(`/users/${encodeURIComponent(state.chatId)}/watchlist`, {
    method: "POST",
    body: JSON.stringify({
      source,
      product_name: normalizedName,
      product_url: (productUrl || "").trim() || null,
      notes: "Saved from Discovery Hub",
    }),
  });
  await loadProfile(state.chatId);
  setStatus(l("status.watch_saved"), "success");
}

async function addWatchlistItem(event) {
  event.preventDefault();
  if (!state.chatId) throw new Error(l("error.load_profile_first"));
  const productName = qs("watch-product").value.trim();
  if (!productName) throw new Error(l("error.product_required"));
  setStatus(l("status.saving_watch"));
  await apiRequest(`/users/${encodeURIComponent(state.chatId)}/watchlist`, {
    method: "POST",
    body: JSON.stringify({
      source: qs("watch-source").value,
      product_name: productName,
      current_buy_price: toNumberOrNull(qs("watch-buy").value),
      current_sell_price: toNumberOrNull(qs("watch-sell").value),
    }),
  });
  qs("watch-product").value = "";
  qs("watch-buy").value = "";
  qs("watch-sell").value = "";
  await loadProfile(state.chatId);
  setStatus(l("status.watch_saved"), "success");
}

async function removeWatchlistItem(itemId) {
  if (!state.chatId) throw new Error(l("error.load_profile_first"));
  await apiRequest(`/users/${encodeURIComponent(state.chatId)}/watchlist/${itemId}`, { method: "DELETE" });
  await loadProfile(state.chatId);
  setStatus(l("status.watch_saved"), "success");
}

async function addCompetitor(event) {
  event.preventDefault();
  if (!state.chatId) throw new Error(l("error.load_profile_first"));
  const seller = qs("competitor-seller").value.trim();
  if (!seller) throw new Error(l("error.seller_required"));
  setStatus(l("status.saving_competitor"));
  await apiRequest(`/users/${encodeURIComponent(state.chatId)}/competitors`, {
    method: "POST",
    body: JSON.stringify({ seller_username: seller }),
  });
  qs("competitor-seller").value = "";
  await loadProfile(state.chatId);
  setStatus(l("status.competitor_saved"), "success");
}

async function removeCompetitor(competitorId) {
  if (!state.chatId) throw new Error(l("error.load_profile_first"));
  await apiRequest(`/users/${encodeURIComponent(state.chatId)}/competitors/${competitorId}`, { method: "DELETE" });
  await loadProfile(state.chatId);
  setStatus(l("status.competitor_saved"), "success");
}

async function scanCompetitor(competitorId) {
  if (!state.chatId) throw new Error(l("error.load_profile_first"));
  setStatus(l("status.scanning_competitor"));
  const data = await apiRequest(`/users/${encodeURIComponent(state.chatId)}/competitors/${competitorId}/scan`, {
    method: "POST",
    body: JSON.stringify({}),
  });
  state.competitorPreview = data;
  renderTextOutput("competitor-output", data.summary || JSON.stringify(data, null, 2));
  await loadProfile(state.chatId);
  setStatus(l("status.competitor_ready"), "success");
}

async function previewWeekly(event) {
  event.preventDefault();
  if (!state.chatId) throw new Error(l("error.load_profile_first"));
  requireBaselineReady();
  const categories = qs("weekly-categories").value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
  if (!categories.length) throw new Error(l("error.categories_required"));
  setStatus(l("status.previewing_weekly"));
  const data = await apiRequest("/weekly-report-preview", {
    method: "POST",
    body: JSON.stringify({
      categories,
      sources: state.profile?.enabled_sources || [],
      top_products: Number(qs("weekly-top-products").value || 5),
      trend_limit: Number(qs("weekly-trend-limit").value || 5),
    }),
  });
  state.weeklyPreview = data;
  renderTextOutput("weekly-output", data.summary || JSON.stringify(data, null, 2));
  setStatus(l("status.weekly_ready"), "success");
}

async function previewDigest(event) {
  event.preventDefault();
  if (!state.chatId) throw new Error(l("error.load_profile_first"));
  requireBaselineReady();
  setStatus(l("status.previewing_digest"));
  const data = await apiRequest(`/users/${encodeURIComponent(state.chatId)}/digest-preview`, {
    method: "POST",
    body: JSON.stringify({
      top: Number(qs("digest-top").value || 10),
      limit: Number(qs("digest-limit").value || 20),
      title: qs("digest-title").value.trim() || null,
    }),
  });
  state.digestPreview = data;
  renderTextOutput("digest-output", data.summary || JSON.stringify(data, null, 2));
  setStatus(l("status.digest_ready"), "success");
}

async function runDiscoveryHub(event) {
  event.preventDefault();
  if (!state.chatId) throw new Error(l("error.load_profile_first"));
  requireBaselineReady();
  const query = qs("discovery-query").value.trim();
  if (!query) throw new Error(l("error.discovery_required"));
  setStatus(l("status.discovery_running"));

  // Show shimmer loading state
  const layoutEl = document.querySelector(".discovery-layout");
  if (layoutEl) layoutEl.classList.add("discovery-loading");
  ["discovery-stores", "discovery-ads", "discovery-trends"].forEach((id) => {
    const node = qs(id);
    if (node) { node.className = "analytics-stack"; node.innerHTML = ""; }
  });

  try {
    const data = await apiRequest(`/users/${encodeURIComponent(state.chatId)}/discovery-hub`, {
      method: "POST",
      body: JSON.stringify({
        query,
        limit: Number(qs("discovery-limit").value || 5),
      }),
    });
    state.discoveryHub = data;
    if (state.profile && Array.isArray(data.recent_runs)) {
      state.profile.discovery_runs = data.recent_runs;
      renderDiscoveryHistory(state.profile);
    }
    renderDiscoveryHub(data);
    setStatus(l("status.discovery_ready"), "success");
  } finally {
    if (layoutEl) layoutEl.classList.remove("discovery-loading");
  }
}

async function runCalculator(event) {
  event.preventDefault();
  setStatus(l("status.calculating"));
  const data = await apiRequest("/calc", {
    method: "POST",
    body: JSON.stringify({
      buy_price: Number(qs("calc-buy").value),
      sell_price: Number(qs("calc-sell").value),
      shipping_cost: toNumberOrNull(qs("calc-shipping").value),
      packaging_cost: toNumberOrNull(qs("calc-packaging").value),
      model: qs("calc-model").value,
      platform: qs("calc-platform").value,
    }),
  });
  state.calcResult = data;
  renderCalcResult(data);
  setStatus(l("status.calculated"), "success");
}

function wireEvents() {
  document.querySelectorAll(".lang-btn").forEach((btn) => {
    btn.addEventListener("click", () => applyLanguage(btn.dataset.lang));
  });

  // ── Workflow nav: smooth scroll + active tab tracking ──
  const workflowTabs = document.querySelectorAll(".workflow-tab");
  const sectionIds = ["section-discover", "section-analytics", "section-digest", "section-reports"];

  workflowTabs.forEach((tab) => {
    tab.addEventListener("click", (e) => {
      e.preventDefault();
      const targetId = tab.dataset.section;
      const el = document.getElementById(targetId);
      if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
      workflowTabs.forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
    });
  });

  // IntersectionObserver to track which section is visible
  if ("IntersectionObserver" in window) {
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            workflowTabs.forEach((t) => t.classList.remove("active"));
            const match = document.querySelector(`.workflow-tab[data-section="${entry.target.id}"]`);
            if (match) match.classList.add("active");
          }
        }
      },
      { rootMargin: "-40% 0px -50% 0px", threshold: 0 },
    );
    sectionIds.forEach((id) => {
      const el = document.getElementById(id);
      if (el) observer.observe(el);
    });
  }

  qs("profile-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      await loadProfile(qs("chat-id").value.trim());
    } catch (error) {
      setStatus(error.message, "error");
      setMessage(error.message, "error");
    }
  });

  qs("refresh-profile").addEventListener("click", async () => {
    try {
      await loadProfile(qs("chat-id").value.trim());
    } catch (error) {
      setStatus(error.message, "error");
      setMessage(error.message, "error");
    }
  });

  qs("refresh-profile-secondary").addEventListener("click", async () => {
    try {
      await loadProfile(qs("chat-id").value.trim());
    } catch (error) {
      setStatus(error.message, "error");
      setMessage(error.message, "error");
    }
  });

  qs("settings-form").addEventListener("submit", async (event) => {
    try {
      await saveSettings(event);
    } catch (error) {
      setStatus(error.message, "error");
      setMessage(error.message, "error");
    }
  });

  qs("setup-form").addEventListener("submit", async (event) => {
    try {
      await saveSettings(event);
    } catch (error) {
      setStatus(error.message, "error");
      setMessage(error.message, "error");
    }
  });

  qs("track-form").addEventListener("submit", async (event) => {
    try {
      await addTrackedQuery(event);
    } catch (error) {
      setStatus(error.message, "error");
      setMessage(error.message, "error");
    }
  });

  qs("watch-form").addEventListener("submit", async (event) => {
    try {
      await addWatchlistItem(event);
    } catch (error) {
      setStatus(error.message, "error");
      setMessage(error.message, "error");
    }
  });

  qs("competitor-form").addEventListener("submit", async (event) => {
    try {
      await addCompetitor(event);
    } catch (error) {
      setStatus(error.message, "error");
      setMessage(error.message, "error");
    }
  });

  qs("weekly-form").addEventListener("submit", async (event) => {
    try {
      await previewWeekly(event);
    } catch (error) {
      setStatus(error.message, "error");
      renderTextOutput("weekly-output", error.message);
    }
  });

  qs("digest-form").addEventListener("submit", async (event) => {
    try {
      await previewDigest(event);
    } catch (error) {
      setStatus(error.message, "error");
      renderTextOutput("digest-output", error.message);
    }
  });

  qs("discovery-form").addEventListener("submit", async (event) => {
    try {
      await runDiscoveryHub(event);
    } catch (error) {
      setStatus(error.message, "error");
      ["discovery-stores", "discovery-ads", "discovery-trends"].forEach((id) => {
        const node = qs(id);
        if (node) {
          node.className = "analytics-stack empty-state";
          node.textContent = error.message;
        }
      });
    }
  });

  qs("calc-form").addEventListener("submit", async (event) => {
    try {
      await runCalculator(event);
    } catch (error) {
      setStatus(error.message, "error");
      renderTextOutput("calc-output", error.message);
    }
  });

  document.addEventListener("click", async (event) => {
    const removeQueryBtn = event.target.closest("[data-remove-query]");
    if (removeQueryBtn) {
      try {
        await removeTrackedQuery(removeQueryBtn.dataset.removeQuery, removeQueryBtn.dataset.removeCategory || "");
      } catch (error) {
        setStatus(error.message, "error");
      }
      return;
    }

    const saveQueryBtn = event.target.closest("[data-save-query]");
    if (saveQueryBtn) {
      try {
        await saveDiscoveryQuery(saveQueryBtn.dataset.saveQuery || "", saveQueryBtn.dataset.saveCategory || "");
      } catch (error) {
        setStatus(error.message, "error");
      }
      return;
    }

    const saveStoreBtn = event.target.closest("[data-save-store]");
    if (saveStoreBtn) {
      try {
        await saveStoreLead({
          domain: saveStoreBtn.dataset.saveStore || "",
          merchantName: saveStoreBtn.dataset.storeName || "",
          nicheQuery: saveStoreBtn.dataset.storeQuery || "",
          estimatedVisits: saveStoreBtn.dataset.storeVisits || "",
          estimatedSalesMonthlyUsd: saveStoreBtn.dataset.storeSales || "",
          avgPriceUsd: saveStoreBtn.dataset.storeAvgPrice || "",
        });
      } catch (error) {
        setStatus(error.message, "error");
      }
      return;
    }

    const watchProductBtn = event.target.closest("[data-watch-product]");
    if (watchProductBtn) {
      try {
        await saveDiscoveryWatchItem(
          watchProductBtn.dataset.watchProduct || "",
          watchProductBtn.dataset.watchUrl || "",
        );
      } catch (error) {
        setStatus(error.message, "error");
      }
      return;
    }

    const removeWatchBtn = event.target.closest("[data-remove-watch]");
    if (removeWatchBtn) {
      try {
        await removeWatchlistItem(removeWatchBtn.dataset.removeWatch);
      } catch (error) {
        setStatus(error.message, "error");
      }
      return;
    }

    const scanCompetitorBtn = event.target.closest("[data-scan-competitor]");
    if (scanCompetitorBtn) {
      try {
        await scanCompetitor(scanCompetitorBtn.dataset.scanCompetitor);
      } catch (error) {
        setStatus(error.message, "error");
        renderTextOutput("competitor-output", error.message);
      }
      return;
    }

    const removeCompetitorBtn = event.target.closest("[data-remove-competitor]");
    if (removeCompetitorBtn) {
      try {
        await removeCompetitor(removeCompetitorBtn.dataset.removeCompetitor);
      } catch (error) {
        setStatus(error.message, "error");
      }
      return;
    }

    const removeStoreLeadBtn = event.target.closest("[data-remove-store-lead]");
    if (removeStoreLeadBtn) {
      try {
        await removeStoreLead(removeStoreLeadBtn.dataset.removeStoreLead);
      } catch (error) {
        setStatus(error.message, "error");
      }
    }
  });

  // ── Notification panel ──

  function setNotifyStatus(msgKey, cls = "") {
    const el = document.getElementById("notify-status");
    if (!el) return;
    el.textContent = l(msgKey);
    el.className = "summary " + cls;
  }

  async function notifyAction(endpoint, body) {
    setNotifyStatus("notify.status_sending", "muted");
    try {
      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error(`${res.status}`);
      setNotifyStatus("notify.status_sent", "success");
    } catch {
      setNotifyStatus("notify.status_error", "error");
    }
  }

  // Discord buttons
  const btnDiscordTest = document.getElementById("btn-discord-test");
  const btnDiscordDigest = document.getElementById("btn-discord-digest");
  if (btnDiscordTest) {
    btnDiscordTest.addEventListener("click", () => {
      const url = document.getElementById("discord-webhook")?.value;
      if (!url) return setNotifyStatus("notify.status_error", "error");
      notifyAction("/notify/discord/test", { webhook_url: url });
    });
  }
  if (btnDiscordDigest) {
    btnDiscordDigest.addEventListener("click", () => {
      const url = document.getElementById("discord-webhook")?.value;
      if (!url) return setNotifyStatus("notify.status_error", "error");
      notifyAction("/notify/discord/digest", {
        webhook_url: url,
        chat_id: state.chatId,
      });
    });
  }

  // Email buttons
  const btnEmailTest = document.getElementById("btn-email-test");
  const btnEmailDigest = document.getElementById("btn-email-digest");
  if (btnEmailTest) {
    btnEmailTest.addEventListener("click", () => {
      const to = document.getElementById("email-to")?.value;
      if (!to) return setNotifyStatus("notify.status_error", "error");
      notifyAction("/notify/email/test", { to_addr: to });
    });
  }
  if (btnEmailDigest) {
    btnEmailDigest.addEventListener("click", () => {
      const to = document.getElementById("email-to")?.value;
      if (!to) return setNotifyStatus("notify.status_error", "error");
      notifyAction("/notify/email/digest", {
        to_addr: to,
        chat_id: state.chatId,
      });
    });
  }

  // Google Sheets buttons
  const btnSheetsDigest = document.getElementById("btn-sheets-digest");
  const btnSheetsWatchlist = document.getElementById("btn-sheets-watchlist");
  if (btnSheetsDigest) {
    btnSheetsDigest.addEventListener("click", () => {
      const sid = document.getElementById("sheets-id")?.value;
      if (!sid) return setNotifyStatus("notify.status_error", "error");
      notifyAction("/export/sheets/digest", {
        spreadsheet_id: sid,
        chat_id: state.chatId,
      });
    });
  }
  if (btnSheetsWatchlist) {
    btnSheetsWatchlist.addEventListener("click", () => {
      const sid = document.getElementById("sheets-id")?.value;
      if (!sid) return setNotifyStatus("notify.status_error", "error");
      notifyAction("/export/sheets/watchlist", {
        spreadsheet_id: sid,
        chat_id: state.chatId,
      });
    });
  }
}

// ── Connect-services panel (API-backed) ──────────────────────────────

let _connectingService = null;
let _connectingLabel = "";

const SERVICE_SUCCESS_COPY = {
  amazon: "Amazon connected. Source prices and product matching are now available.",
  walmart: "Walmart connected. Source prices and stock checks are now available.",
  aliexpress: "AliExpress connected. China-model sourcing is now available.",
  cj: "CJDropshipping connected. Supplier catalog and fulfillment coverage added.",
  keepa: "Keepa connected. Amazon price history can be added to product checks.",
  zik: "ZIK connected. eBay sell-through rates and competition depth unlocked.",
  storeleads: "StoreLeads connected. Competitor store discovery is now available.",
  similarweb: "SimilarWeb connected. Traffic intelligence for competitor validation added.",
  pipiads: "PiPiADS connected. TikTok ad spy for viral product discovery enabled.",
  minea: "Minea connected. Cross-platform ad intelligence now available.",
};

function openConnectDialog(integrationId, label) {
  _connectingService = integrationId;
  _connectingLabel = label;
  const dialog = document.getElementById("secret-dialog");
  const title = document.getElementById("secret-dialog-title");
  const desc = document.getElementById("secret-dialog-desc");
  const input = document.getElementById("secret-input");
  const status = document.getElementById("secret-status");

  title.textContent = `${l("services.connect")} ${label}`;
  desc.textContent = l("services.dialog_desc");
  input.value = "";
  status.textContent = "";
  status.className = "summary muted";

  if (dialog.showModal) {
    dialog.showModal();
  }
  input.focus();
}

function closeConnectDialog() {
  _connectingService = null;
  const dialog = document.getElementById("secret-dialog");
  const input = document.getElementById("secret-input");
  input.value = "";
  if (dialog.close) dialog.close();
}

async function submitConnectSecret(event) {
  event.preventDefault();
  if (!_connectingService || !state.chatId) return;

  const input = document.getElementById("secret-input");
  const status = document.getElementById("secret-status");
  const key = input.value.trim();
  if (!key) return;

  status.textContent = l("services.saving");
  status.className = "summary muted";

  try {
    await apiRequest(`/users/${state.chatId}/integrations/${_connectingService}/secret`, {
      method: "PUT",
      body: JSON.stringify({ api_key: key }),
    });

    input.value = "";
    const successCopy = SERVICE_SUCCESS_COPY[_connectingService] || l("services.save_success");
    status.textContent = successCopy;
    status.className = "summary success";
    status.setAttribute("role", "status");

    // Reload profile to refresh integration status
    setTimeout(async () => {
      closeConnectDialog();
      await loadProfile(state.chatId);
    }, 1200);
  } catch (error) {
    status.textContent = l("services.save_error");
    status.className = "summary danger";
    status.setAttribute("role", "alert");
  }
}

async function disconnectService(integrationId) {
  if (!state.chatId) return;
  try {
    await apiRequest(`/users/${state.chatId}/integrations/${integrationId}/secret`, {
      method: "DELETE",
    });
    await loadProfile(state.chatId);
    setStatus(l("services.disconnected"), "success");
  } catch (error) {
    setStatus(l("services.disconnect_error"), "error");
  }
}

function wireConnectServices() {
  // Connect button — open dialog
  document.addEventListener("click", (event) => {
    const connectBtn = event.target.closest("[data-connect]");
    if (connectBtn) {
      const id = connectBtn.dataset.connect;
      const label = connectBtn.dataset.connectLabel || id;
      openConnectDialog(id, label);
      return;
    }

    const disconnectBtn = event.target.closest("[data-disconnect]");
    if (disconnectBtn) {
      disconnectService(disconnectBtn.dataset.disconnect);
      return;
    }
  });

  // Dialog form submit
  const secretForm = document.getElementById("secret-form");
  if (secretForm) {
    secretForm.addEventListener("submit", submitConnectSecret);
  }

  // Dialog cancel button
  const secretCancel = document.getElementById("secret-cancel");
  if (secretCancel) {
    secretCancel.addEventListener("click", closeConnectDialog);
  }
}

function boot() {
  applyLanguage(state.currentLang);
  wireEvents();
  wireConnectServices();
  seedEmptyStates();
  setStatus(l("status.ready"));
  const rememberedChatId = localStorage.getItem("dropagent.chat_id");
  if (rememberedChatId) {
    qs("chat-id").value = rememberedChatId;
    loadProfile(rememberedChatId).catch(() => {
      setStatus(l("status.ready"));
    });
  }
}

boot();

// ── PWA: register service worker ──
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker
      .register("./sw.js")
      .then((reg) => console.log("[SW] registered:", reg.scope))
      .catch((err) => console.warn("[SW] registration failed:", err));
  });
}

// ── Workflow nav active state (Intersection Observer) ──────────────────────
function initWorkflowNav() {
  const tabs = document.querySelectorAll(".workflow-tab[data-nav]");
  if (!tabs.length) return;

  const anchors = Array.from(tabs).map((tab) =>
    document.getElementById(tab.dataset.nav)
  ).filter(Boolean);

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const id = entry.target.id;
          tabs.forEach((tab) => {
            const isActive = tab.dataset.nav === id;
            tab.classList.toggle("active", isActive);
            tab.setAttribute("aria-current", isActive ? "true" : "false");
          });
        }
      });
    },
    { rootMargin: "-10% 0px -85% 0px", threshold: 0 }
  );

  anchors.forEach((anchor) => observer.observe(anchor));
}

initWorkflowNav();
