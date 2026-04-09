const API_BASE = "/api";
const SOURCE_OPTIONS = [
  ["amazon", "Amazon"],
  ["walmart", "Walmart"],
];

// ── i18n ──────────────────────────────────────────────────────────────────────

const LABELS = {
  en: {
    "hero.title": "Dashboard control center",
    "hero.lede": "Load a user, tune settings, manage tracked queries, preview digests, and run the margin calculator from one simple screen.",
    "hero.api_base": "API base",
    "hero.status": "Status",
    "profile.label": "User profile",
    "profile.title": "Load a Telegram chat",
    "settings.label": "Settings",
    "settings.title": "Update user preferences",
    "tracked.label": "Tracked queries",
    "tracked.title": "Manage watch terms",
    "digest.label": "Digest preview",
    "digest.title": "Preview saved digest",
    "digest.empty": "No digest preview yet.",
    "calc.label": "Margin calculator",
    "calc.title": "Check product profit",
    "calc.empty": "No calculation yet.",
    "calc.result": "Margin Result",
    "calc.profit": "PROFIT",
    "calc.loss": "LOSS",
    "calc.buy_price": "Buy Price",
    "calc.sell_price": "Sell Price",
    "calc.shipping": "Shipping",
    "calc.packaging": "Packaging",
    "calc.platform_fee": "Platform Fee",
    "calc.payment_fee": "Payment Fee",
    "calc.total_fees": "Total Fees",
    "calc.total_cost": "Total Cost",
    "calc.net_profit": "Net Profit",
    "calc.margin": "Margin",
    "calc.roi": "ROI",
    "calc.markup": "Markup",
    "footer.text": "DropAgent dashboard · static frontend · connects to /api",
  },
  ru: {
    "hero.title": "Панель управления",
    "hero.lede": "Загрузите пользователя, настройте параметры, управляйте отслеживаемыми запросами, просматривайте дайджесты и рассчитывайте маржу — всё в одном экране.",
    "hero.api_base": "API базовый URL",
    "hero.status": "Статус",
    "profile.label": "Профиль пользователя",
    "profile.title": "Загрузить Telegram чат",
    "settings.label": "Настройки",
    "settings.title": "Обновить настройки",
    "tracked.label": "Отслеживаемые запросы",
    "tracked.title": "Управление запросами",
    "digest.label": "Предпросмотр дайджеста",
    "digest.title": "Предпросмотр сохранённого дайджеста",
    "digest.empty": "Дайджест ещё не загружен.",
    "calc.label": "Калькулятор маржи",
    "calc.title": "Рассчитать прибыль",
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
    "footer.text": "DropAgent · статичный фронтенд · подключается к /api",
  },
  zh: {
    "hero.title": "控制面板",
    "hero.lede": "加载用户、调整设置、管理追踪词、预览日报，并在一个界面内运行利润计算器。",
    "hero.api_base": "API 地址",
    "hero.status": "状态",
    "profile.label": "用户资料",
    "profile.title": "加载 Telegram 会话",
    "settings.label": "设置",
    "settings.title": "更新用户偏好",
    "tracked.label": "追踪词",
    "tracked.title": "管理追踪词",
    "digest.label": "日报预览",
    "digest.title": "预览已保存的日报",
    "digest.empty": "暂无日报预览。",
    "calc.label": "利润计算器",
    "calc.title": "计算商品利润",
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
    "footer.text": "DropAgent · 静态前端 · 连接到 /api",
  },
};

let currentLang = localStorage.getItem("dropagent.lang") || "en";

function l(key) {
  return (LABELS[currentLang] || LABELS.en)[key] || (LABELS.en[key] || key);
}

function applyLanguage(lang) {
  currentLang = lang;
  localStorage.setItem("dropagent.lang", lang);

  // Update all data-i18n elements
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.getAttribute("data-i18n");
    el.textContent = l(key);
  });

  // Update active button state
  document.querySelectorAll(".lang-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.lang === lang);
  });
}

// ── State ─────────────────────────────────────────────────────────────────────

const state = {
  profile: null,
  trackedQueries: [],
  digestPreview: null,
  calcResult: null,
  chatId: "",
};

// ── DOM helpers ───────────────────────────────────────────────────────────────

function qs(id) {
  return document.getElementById(id);
}

function setStatus(text, kind = "idle") {
  const status = qs("api-status");
  if (status) {
    status.textContent = text;
    status.dataset.kind = kind;
  }
}

function setMessage(message, kind = "muted") {
  const box = qs("profile-summary");
  if (!box) return;
  box.textContent = message;
  box.className = kind === "error" ? "summary danger" : "summary muted";
}

function toNumberOrNull(value) {
  if (value === "" || value === null || value === undefined) return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function selectedSources() {
  return SOURCE_OPTIONS.filter(([value]) => {
    const checkbox = qs(`source-${value}`);
    return checkbox && checkbox.checked;
  }).map(([value]) => value);
}

// ── Renderers ─────────────────────────────────────────────────────────────────

function renderCalcResult(data) {
  const node = qs("calc-output");
  if (!node) return;

  const profitable = data.is_profitable;
  const badge = profitable ? l("calc.profit") : l("calc.loss");
  const badgeClass = profitable ? "badge-profit" : "badge-loss";

  const fmtUSD = (v) => `$${Number(v).toFixed(2)}`;
  const fmtPct = (v) => `${Number(v).toFixed(2)}%`;

  node.innerHTML = `
    <div class="calc-result">
      <div class="calc-result-header">
        <span class="calc-result-title">${l("calc.result")}</span>
        <span class="badge ${badgeClass}">${badge}</span>
      </div>

      <div class="result-grid">
        <div class="result-metric highlight">
          <span>${l("calc.net_profit")}</span>
          <strong class="${profitable ? "good" : "bad"}">${fmtUSD(data.net_profit)}</strong>
        </div>
        <div class="result-metric highlight">
          <span>${l("calc.margin")}</span>
          <strong class="${profitable ? "good" : "bad"}">${fmtPct(data.margin_percent)}</strong>
        </div>
        <div class="result-metric highlight">
          <span>${l("calc.roi")}</span>
          <strong>${fmtPct(data.roi_percent)}</strong>
        </div>
        <div class="result-metric highlight">
          <span>${l("calc.markup")}</span>
          <strong>${Number(data.markup).toFixed(2)}x</strong>
        </div>
      </div>

      <div class="result-breakdown">
        <div class="breakdown-row">
          <span>${l("calc.buy_price")}</span><span>${fmtUSD(data.buy_price)}</span>
        </div>
        <div class="breakdown-row">
          <span>${l("calc.sell_price")}</span><span>${fmtUSD(data.sell_price)}</span>
        </div>
        <div class="breakdown-divider"></div>
        <div class="breakdown-row muted">
          <span>${l("calc.shipping")}</span><span>${fmtUSD(data.shipping_cost)}</span>
        </div>
        <div class="breakdown-row muted">
          <span>${l("calc.packaging")}</span><span>${fmtUSD(data.packaging_cost)}</span>
        </div>
        <div class="breakdown-row muted">
          <span>${l("calc.platform_fee")} (${data.platform})</span><span>${fmtUSD(data.platform_fee)}</span>
        </div>
        <div class="breakdown-row muted">
          <span>${l("calc.payment_fee")}</span><span>${fmtUSD(data.payment_fee)}</span>
        </div>
        <div class="breakdown-divider"></div>
        <div class="breakdown-row">
          <span>${l("calc.total_fees")}</span><span>${fmtUSD(data.total_fees)}</span>
        </div>
        <div class="breakdown-row">
          <span>${l("calc.total_cost")}</span><span>${fmtUSD(data.total_cost)}</span>
        </div>
      </div>
    </div>
  `;
}

function renderDigestResult(data) {
  const node = qs("digest-output");
  if (!node) return;

  const text = data.summary || data.message || JSON.stringify(data, null, 2);
  node.innerHTML = `<pre class="digest-pre">${escapeHtml(text)}</pre>`;
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function renderSources(profile) {
  const container = qs("sources-list");
  container.innerHTML = "";
  const enabled = new Set(profile?.enabled_sources || []);
  SOURCE_OPTIONS.forEach(([value, label]) => {
    const wrapper = document.createElement("label");
    wrapper.className = "source-option";
    const input = document.createElement("input");
    input.type = "checkbox";
    input.id = `source-${value}`;
    input.value = value;
    input.checked = enabled.size ? enabled.has(value) : value === "amazon" || value === "walmart";
    const text = document.createElement("span");
    text.textContent = label;
    wrapper.append(input, text);
    container.appendChild(wrapper);
  });
}

function renderTrackedQueries(profile) {
  const container = qs("tracked-queries");
  const tracked = profile?.tracked_queries || [];
  state.trackedQueries = tracked;
  container.innerHTML = "";

  if (!tracked.length) {
    container.className = "list empty-state";
    container.textContent = "No tracked queries loaded yet.";
    return;
  }

  container.className = "list";
  tracked.forEach((item) => {
    const row = document.createElement("div");
    row.className = "tracked-item";
    const meta = document.createElement("div");
    meta.className = "tracked-meta";
    const title = document.createElement("strong");
    title.textContent = item.query;
    const details = document.createElement("span");
    const bits = [];
    if (item.category) bits.push(`Category: ${item.category}`);
    if (item.min_profit_threshold != null) bits.push(`Min profit: $${Number(item.min_profit_threshold).toFixed(2)}`);
    if (item.max_buy_price != null) bits.push(`Max buy: $${Number(item.max_buy_price).toFixed(2)}`);
    details.textContent = bits.length ? bits.join(" · ") : "Saved query";
    meta.append(title, details);
    const removeBtn = document.createElement("button");
    removeBtn.type = "button";
    removeBtn.className = "btn btn-ghost";
    removeBtn.textContent = "Remove";
    removeBtn.addEventListener("click", () => removeTrackedQuery(item.query, item.category));
    row.append(meta, removeBtn);
    container.appendChild(row);
  });
}

function renderProfile(profile) {
  state.profile = profile;
  state.chatId = profile.telegram_chat_id || "";
  qs("chat-id").value = profile.telegram_chat_id || "";
  qs("username").value = profile.username || "";
  qs("preferred-language").value = profile.preferred_language || "en";
  qs("min-profit").value = profile.min_profit_threshold ?? "";
  qs("max-buy").value = profile.max_buy_price ?? "";
  const schedule = !profile.digest_enabled ? "off" : String(profile.digest_interval_days || "off");
  qs("schedule").value = schedule;
  renderSources(profile);
  renderTrackedQueries(profile);
  const parts = [
    `User: ${profile.username || "unknown"}`,
    `Chat: ${profile.telegram_chat_id}`,
    `Language: ${profile.preferred_language || "en"}`,
    `Digest: ${profile.digest_enabled ? `on every ${profile.digest_interval_days} day(s)` : "off"}`,
  ];
  setMessage(parts.join(" · "));

  // Reset outputs
  const digestNode = qs("digest-output");
  if (digestNode) digestNode.innerHTML = `<span class="muted">${l("digest.empty")}</span>`;
}

// ── API ───────────────────────────────────────────────────────────────────────

async function apiRequest(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json")
    ? await response.json()
    : { raw: await response.text() };
  if (!response.ok) {
    throw new Error(payload?.error || `Request failed with ${response.status}`);
  }
  return payload;
}

async function loadProfile(chatId) {
  if (!chatId) throw new Error("Telegram chat id is required");
  const username = qs("username").value.trim();
  const preferredLanguage = qs("preferred-language").value.trim();
  const params = new URLSearchParams();
  if (username) params.set("username", username);
  if (preferredLanguage) params.set("preferred_language", preferredLanguage);
  setStatus("Loading profile...");
  const profile = await apiRequest(
    `/users/${encodeURIComponent(chatId)}${params.toString() ? `?${params}` : ""}`,
    { method: "GET" },
  );
  localStorage.setItem("dropagent.chat_id", chatId);
  renderProfile(profile);
  setStatus("Profile loaded", "success");
}

async function saveSettings(event) {
  event.preventDefault();
  if (!state.chatId) throw new Error("Load a profile first");
  setStatus("Saving settings...");
  await apiRequest(`/users/${encodeURIComponent(state.chatId)}/settings`, {
    method: "PATCH",
    body: JSON.stringify({
      preferred_language: qs("language").value,
      min_profit_threshold: toNumberOrNull(qs("min-profit").value),
      max_buy_price: toNumberOrNull(qs("max-buy").value),
      enabled_sources: selectedSources(),
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
  setStatus("Settings saved", "success");
}

async function addTrackedQuery(event) {
  event.preventDefault();
  if (!state.chatId) throw new Error("Load a profile first");
  const query = qs("track-query").value.trim();
  if (!query) throw new Error("Query is required");
  setStatus("Saving tracked query...");
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
  setStatus("Tracked query saved", "success");
}

async function removeTrackedQuery(query, category) {
  if (!state.chatId) throw new Error("Load a profile first");
  setStatus("Removing tracked query...");
  const params = new URLSearchParams();
  if (category) params.set("category", category);
  await apiRequest(
    `/users/${encodeURIComponent(state.chatId)}/tracked-queries/${encodeURIComponent(query)}${params.toString() ? `?${params}` : ""}`,
    { method: "DELETE" },
  );
  await loadProfile(state.chatId);
  setStatus("Tracked query removed", "success");
}

async function previewDigest(event) {
  event.preventDefault();
  if (!state.chatId) throw new Error("Load a profile first");
  setStatus("Previewing digest...");
  const data = await apiRequest(`/users/${encodeURIComponent(state.chatId)}/digest-preview`, {
    method: "POST",
    body: JSON.stringify({
      top: Number(qs("digest-top").value || 10),
      limit: Number(qs("digest-limit").value || 20),
      title: qs("digest-title").value.trim() || null,
    }),
  });
  state.digestPreview = data;
  renderDigestResult(data);
  setStatus("Digest preview ready", "success");
}

async function runCalculator(event) {
  event.preventDefault();
  setStatus("Calculating margin...");
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
  setStatus("Margin calculated", "success");
}

// ── Events ────────────────────────────────────────────────────────────────────

function wireEvents() {
  // Language switcher
  document.querySelectorAll(".lang-btn").forEach((btn) => {
    btn.addEventListener("click", () => applyLanguage(btn.dataset.lang));
  });

  qs("profile-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    try { await loadProfile(qs("chat-id").value.trim()); }
    catch (e) { setStatus(e.message, "error"); setMessage(e.message, "error"); }
  });

  qs("refresh-profile").addEventListener("click", async () => {
    try { await loadProfile(qs("chat-id").value.trim()); }
    catch (e) { setStatus(e.message, "error"); setMessage(e.message, "error"); }
  });

  qs("settings-form").addEventListener("submit", async (event) => {
    try { await saveSettings(event); }
    catch (e) { setStatus(e.message, "error"); setMessage(e.message, "error"); }
  });

  qs("track-form").addEventListener("submit", async (event) => {
    try { await addTrackedQuery(event); }
    catch (e) { setStatus(e.message, "error"); setMessage(e.message, "error"); }
  });

  qs("reload-tracks").addEventListener("click", async () => {
    try { await loadProfile(qs("chat-id").value.trim()); }
    catch (e) { setStatus(e.message, "error"); setMessage(e.message, "error"); }
  });

  qs("digest-form").addEventListener("submit", async (event) => {
    try { await previewDigest(event); }
    catch (e) {
      setStatus(e.message, "error");
      const node = qs("digest-output");
      if (node) node.innerHTML = `<span class="bad">${escapeHtml(e.message)}</span>`;
    }
  });

  qs("calc-form").addEventListener("submit", async (event) => {
    try { await runCalculator(event); }
    catch (e) {
      setStatus(e.message, "error");
      const node = qs("calc-output");
      if (node) node.innerHTML = `<span class="bad">${escapeHtml(e.message)}</span>`;
    }
  });
}

// ── Boot ──────────────────────────────────────────────────────────────────────

function bootstrap() {
  const storedChatId = localStorage.getItem("dropagent.chat_id");
  if (storedChatId) qs("chat-id").value = storedChatId;

  applyLanguage(currentLang);
  setStatus("Ready");
  wireEvents();
}

document.addEventListener("DOMContentLoaded", bootstrap);
