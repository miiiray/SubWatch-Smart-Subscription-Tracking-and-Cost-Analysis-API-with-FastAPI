// app.js — Ana panel. Her istekte token'ı gönderir, sadece giriş yapan kişinin verisini gösterir.

const TOKEN_KEY = "subwatch_token";
const $ = (id) => document.getElementById(id);
let subNames = {}; // abonelik id → servis adı
let subPrices = {}; // abonelik id → { price, currency }

const CYCLE_TR = { monthly: "Aylık", yearly: "Yıllık" };
const tl = (n) => Number(n).toLocaleString("tr-TR", { style: "currency", currency: "TRY" });
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
}[c]));

// ---------- Token ----------
function getToken() {
  try { return localStorage.getItem(TOKEN_KEY); } catch (e) { return null; }
}

function clearToken() {
  try { localStorage.removeItem(TOKEN_KEY); } catch (e) {}
}

function goToLogin() {
  clearToken();
  window.location.href = "/";
}

// ---------- API yardımcı fonksiyonu (token ekler) ----------
async function api(path, options = {}) {
  const token = getToken();
  if (!token) {
    goToLogin();
    throw new Error("Giriş yapmalısın.");
  }

  const res = await fetch(path, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
  });

  // Token geçersiz ya da süresi dolmuş → giriş sayfasına dön
  if (res.status === 401) {
    goToLogin();
    throw new Error("Oturum sona erdi.");
  }

  const data = await res.json().catch(() => null);
  if (!res.ok) {
    let detail = data && data.detail;
    if (Array.isArray(detail)) detail = detail[0] && detail[0].msg;
    throw new Error(typeof detail === "string" ? detail : "Bir hata oluştu.");
  }
  return data;
}

function toast(message) {
  const el = $("toast");
  el.textContent = message;
  el.classList.add("show");
  setTimeout(() => el.classList.remove("show"), 2500);
}

// ---------- Panel ----------
async function loadDashboard() {
  const [summary, upcoming, insights, subs] = await Promise.all([
    api("/me/summary"),
    api("/me/upcoming?days=7"),
    api("/me/insights"),
    api("/subscriptions"),
  ]);
  renderSummary(summary);
  renderUpcoming(upcoming);
  renderInsights(insights);
  renderSubscriptions(subs);
}

function renderSummary(s) {
  $("statMonthly").textContent = tl(s.total_monthly);
  $("statYearly").textContent = tl(s.total_yearly);
  $("statCount").textContent = s.subscription_count;
  $("statBudget").textContent = s.over_budget
    ? `${tl(-s.budget_left)} aşıldı`
    : `${tl(s.budget_left)} kaldı`;

  const percent = s.monthly_budget > 0
    ? Math.min(100, (s.total_monthly / s.monthly_budget) * 100)
    : 100;
  const bar = $("budgetBar");
  bar.style.width = percent + "%";
  bar.classList.toggle("over", s.over_budget);

  $("rateInfo").textContent = s.rates_source === "live"
    ? "Döviz: canlı kur (Frankfurter API)"
    : "Döviz: yaklaşık kur (API'ye ulaşılamadı)";
}

function renderUpcoming(items) {
  $("upcomingList").innerHTML = items.length
    ? items.map((i) => `
        <li class="${i.days_left <= 2 ? "warning" : "info"}">
          <div class="row">
            <strong>${esc(i.service_name)}</strong>
            <span>${i.days_left === 0 ? "Bugün" : i.days_left + " gün sonra"}</span>
          </div>
          <span class="muted">${i.price} ${i.currency} · ${i.next_payment_date}</span>
        </li>`).join("")
    : `<li class="success">Önümüzdeki 7 günde ödeme yok.</li>`;
}

function renderInsights(items) {
  $("insightList").innerHTML = items
    .map((i) => `<li class="${i.level}">${esc(i.message)}</li>`)
    .join("");
}

function renderSubscriptions(subs) {
  subNames = Object.fromEntries(subs.map((s) => [s.id, s.service_name]));
  subPrices = Object.fromEntries(subs.map((s) => [s.id, { price: s.price, currency: s.currency }]));
  $("subTable").innerHTML = subs.length
    ? subs.map((s) => `
        <tr>
          <td><strong>${esc(s.service_name)}</strong> ${s.is_trial ? '<span class="tag trial">deneme</span>' : ""}</td>
          <td><span class="tag">${esc(s.category)}</span></td>
          <td id="price-${s.id}">${s.price} ${s.currency}</td>
          <td>${CYCLE_TR[s.billing_cycle] || s.billing_cycle}</td>
          <td>${s.next_payment_date}</td>
          <td class="actions">
            <button class="small ghost" onclick="logUsage(${s.id})">Kullandım</button>
            <button class="small ghost" onclick="updatePrice(${s.id})">Fiyat</button>
            <button class="small danger" onclick="cancelSub(${s.id})">İptal</button>
          </td>
        </tr>`).join("")
    : `<tr><td colspan="6" class="muted">Henüz abonelik yok. Aşağıdan ekleyebilirsin.</td></tr>`;
}

// ---------- Abonelik işlemleri ----------
async function logUsage(id) {
  try {
    await api(`/subscriptions/${id}/usage`, { method: "POST", body: "{}" });
    toast("Kullanım kaydedildi ✔");
    loadDashboard();
  } catch (err) {
    toast(err.message);
  }
}

// "Fiyat" butonu: fiyat hücresini küçük bir forma çevirir
function updatePrice(id) {
  const { price, currency } = subPrices[id];
  $(`price-${id}`).innerHTML = `
    <input id="priceInput-${id}" type="number" min="0.01" step="0.01" value="${price}" style="width:110px">
    ${currency}
    <button class="small" onclick="savePrice(${id})">Kaydet</button>
    <button class="small ghost" onclick="loadDashboard()">Vazgeç</button>`;
  $(`priceInput-${id}`).focus();
}

async function savePrice(id) {
  const name = subNames[id];
  const { price, currency } = subPrices[id];
  const newPrice = Number(String($(`priceInput-${id}`).value).replace(",", "."));

  if (!Number.isFinite(newPrice) || newPrice <= 0) {
    toast("Geçerli bir fiyat gir (0'dan büyük bir sayı).");
    return;
  }
  if (newPrice === price) {
    toast("Fiyat aynı, değişiklik yapılmadı.");
    loadDashboard();
    return;
  }

  try {
    await api(`/subscriptions/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ price: newPrice }),
    });
    toast(`${name}: ${price} → ${newPrice} ${currency} ✔`);
    loadDashboard();
  } catch (err) {
    toast(err.message);
  }
}

async function cancelSub(id) {
  const name = subNames[id];
  if (!confirm(`${name} aboneliğini iptal etmek istiyor musun?`)) return;
  try {
    const res = await api(`/subscriptions/${id}`, { method: "DELETE" });
    toast(res.message);
    loadDashboard();
  } catch (err) {
    toast(err.message);
  }
}

$("subForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const f = new FormData(e.target);
  const isTrial = f.get("is_trial") === "on";
  try {
    await api("/subscriptions", {
      method: "POST",
      body: JSON.stringify({
        service_name: f.get("service_name"),
        category: f.get("category"),
        price: Number(f.get("price")),
        currency: f.get("currency"),
        billing_cycle: f.get("billing_cycle"),
        next_payment_date: f.get("next_payment_date"),
        is_trial: isTrial,
        trial_end_date: isTrial && f.get("trial_end_date") ? f.get("trial_end_date") : null,
      }),
    });
    e.target.reset();
    toast("Abonelik eklendi");
    loadDashboard();
  } catch (err) {
    toast(err.message);
  }
});

// ---------- Çıkış ----------
$("logoutBtn").addEventListener("click", async () => {
  try {
    await api("/auth/logout", { method: "POST" });
  } catch (e) {
    // token zaten geçersizse de çıkış yapılmış sayılır
  }
  goToLogin();
});

// ---------- Başlangıç ----------
(async () => {
  try {
    const me = await api("/auth/me");
    $("userName").textContent = me.name;
    await loadDashboard();
  } catch (err) {
    toast(err.message);
  }
})();
