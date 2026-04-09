const API_BASE = "/api";
const SOURCE_OPTIONS = [
  ["amazon", "Amazon"],
  ["walmart", "Walmart"],
];

const state = {
  profile: null,
  trackedQueries: [],
  digestPreview: null,
  calcResult: null,
  chatId: "",
};

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

function showOutput(id, value) {
  const node = qs(id);
  if (!node) return;
  node.textContent = typeof value === "string" ? value : JSON.stringify(value, null, 2);
}

function toNumberOrNull(value) {
  if (value === "" || value === null || value === undefined) {
    return null;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function selectedSources() {
  return SOURCE_OPTIONS.filter(([value]) => {
    const checkbox = qs(`source-${value}`);
    return checkbox && checkbox.checked;
  }).map(([value]) => value);
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
    if (item.min_profit_threshold !== null && item.min_profit_threshold !== undefined) {
      bits.push(`Min profit: $${Number(item.min_profit_threshold).toFixed(2)}`);
    }
    if (item.max_buy_price !== null && item.max_buy_price !== undefined) {
      bits.push(`Max buy: $${Number(item.max_buy_price).toFixed(2)}`);
    }
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

  const schedule = !profile.digest_enabled
    ? "off"
    : String(profile.digest_interval_days || "off");
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
  showOutput("digest-output", "No digest preview yet.");
}

async function apiRequest(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json")
    ? await response.json()
    : { raw: await response.text() };

  if (!response.ok) {
    const message = payload?.error || `Request failed with ${response.status}`;
    throw new Error(message);
  }

  return payload;
}

async function loadProfile(chatId) {
  if (!chatId) {
    throw new Error("Telegram chat id is required");
  }

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
  if (!state.chatId) {
    throw new Error("Load a profile first");
  }

  setStatus("Saving settings...");
  const payload = {
    preferred_language: qs("language").value,
    min_profit_threshold: toNumberOrNull(qs("min-profit").value),
    max_buy_price: toNumberOrNull(qs("max-buy").value),
    enabled_sources: selectedSources(),
  };

  const scheduleValue = qs("schedule").value;
  await apiRequest(`/users/${encodeURIComponent(state.chatId)}/settings`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });

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
  if (!state.chatId) {
    throw new Error("Load a profile first");
  }

  const query = qs("track-query").value.trim();
  if (!query) {
    throw new Error("Query is required");
  }

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
  if (!state.chatId) {
    throw new Error("Load a profile first");
  }

  setStatus("Removing tracked query...");
  const params = new URLSearchParams();
  if (category) params.set("category", category);

  await apiRequest(
    `/users/${encodeURIComponent(state.chatId)}/tracked-queries/${encodeURIComponent(query)}${
      params.toString() ? `?${params}` : ""
    }`,
    { method: "DELETE" },
  );

  await loadProfile(state.chatId);
  setStatus("Tracked query removed", "success");
}

async function previewDigest(event) {
  event.preventDefault();
  if (!state.chatId) {
    throw new Error("Load a profile first");
  }

  const payload = {
    top: Number(qs("digest-top").value || 10),
    limit: Number(qs("digest-limit").value || 20),
    title: qs("digest-title").value.trim() || null,
  };

  setStatus("Previewing digest...");
  const data = await apiRequest(
    `/users/${encodeURIComponent(state.chatId)}/digest-preview`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );

  state.digestPreview = data;
  showOutput(
    "digest-output",
    data.summary || data.message || JSON.stringify(data, null, 2),
  );
  setStatus("Digest preview ready", "success");
}

async function runCalculator(event) {
  event.preventDefault();

  const payload = {
    buy_price: Number(qs("calc-buy").value),
    sell_price: Number(qs("calc-sell").value),
    shipping_cost: toNumberOrNull(qs("calc-shipping").value),
    packaging_cost: toNumberOrNull(qs("calc-packaging").value),
    model: qs("calc-model").value,
    platform: qs("calc-platform").value,
  };

  setStatus("Calculating margin...");
  const data = await apiRequest("/calc", {
    method: "POST",
    body: JSON.stringify(payload),
  });

  state.calcResult = data;
  showOutput("calc-output", data.summary || JSON.stringify(data, null, 2));
  setStatus("Margin calculated", "success");
}

function wireEvents() {
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

  qs("settings-form").addEventListener("submit", async (event) => {
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

  qs("reload-tracks").addEventListener("click", async () => {
    try {
      await loadProfile(qs("chat-id").value.trim());
    } catch (error) {
      setStatus(error.message, "error");
      setMessage(error.message, "error");
    }
  });

  qs("digest-form").addEventListener("submit", async (event) => {
    try {
      await previewDigest(event);
    } catch (error) {
      setStatus(error.message, "error");
      showOutput("digest-output", error.message);
    }
  });

  qs("calc-form").addEventListener("submit", async (event) => {
    try {
      await runCalculator(event);
    } catch (error) {
      setStatus(error.message, "error");
      showOutput("calc-output", error.message);
    }
  });
}

function bootstrap() {
  const storedChatId = localStorage.getItem("dropagent.chat_id");
  if (storedChatId) {
    qs("chat-id").value = storedChatId;
  }

  setStatus("Ready");
  wireEvents();
}

document.addEventListener("DOMContentLoaded", bootstrap);
