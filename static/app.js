// app.js — Web sitesi, bizim FastAPI endpoint'lerimize fetch ile istek atar.

const $ = (id) => document.getElementById(id);
let currentUserId = null;
let subNames = {};   // abonelik id → servis adı

const CYCLE_TR = { monthly: "Aylık", yearly: "Yıllık" };
const tl = (n) => Number(n).toLocaleString("tr-TR", { style: "currency", currency: "TRY" });
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

// ---------- API yardımcı fonksiyonu ----------
async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const detail = data && data.detail;
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

// ---------- Kullanıcılar ----------
async function loadUsers() {
  const users = await api("/users");
  const select = $("userSelect");
  select.innerHTML = users.map((u) => `<option value="${u.id}">${esc(u.name)}</option>`).join("");

  if (users.length === 0) {
    $("userFormCard").classList.remove("hidden");
    return;
  }
  if (!users.some((u) => u.id === currentUserId)) currentUserId = users[0].id;
  select.value = currentUserId;
  loadDashboard();
}

$("userSelect").addEventListener("change", (e) => {
  currentUserId = Number(e.target.value);
  loadDashboard();
});

$("newUserBtn").addEventListener("click", () => $("userFormCard").classList.toggle("hidden"));

$("userForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const f = new FormData(e.target);
  try {
    const user = await api("/users", {
      method: "POST",
      body: JSON.stringify({
        name: f.get("name"),
        email: f.get("email"),
        monthly_budget: Number(f.get("monthly_budget")),
      }),
    });
    currentUserId = user.id;
    e.target.reset();
    $("userFormCard").classList.add("hidden");
    toast("Kullanıcı oluşturuldu");
    loadUsers();
  } catch (err) {
    toast(err.message);
  }
});

// ---------- Panel (dashboard) ----------
async function loadDashboard() {
  if (!currentUserId) return;
  const id = currentUserId;
  const [summary, upcoming, insights, subs] = await Promise.all([
    api(`/users/${id}/summary`),
    api(`/users/${id}/upcoming?days=7`),
    api(`/users/${id}/insights`),
    api(`/subscriptions?user_id=${id}`),
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

  const percent = s.monthly_budget > 0 ? Math.min(100, (s.total_monthly / s.monthly_budget) * 100) : 100;
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
  $("subTable").innerHTML = subs.length
    ? subs.map((s) => `
        <tr>
          <td><strong>${esc(s.service_name)}</strong> ${s.is_trial ? '<span class="tag trial">deneme</span>' : ""}</td>
          <td><span class="tag">${esc(s.category)}</span></td>
          <td>${s.price} ${s.currency}</td>
          <td>${CYCLE_TR[s.billing_cycle] || s.billing_cycle}</td>
          <td>${s.next_payment_date}</td>
          <td class="actions">
            <button class="small ghost" onclick="logUsage(${s.id})">Kullandım</button>
            <button class="small danger" onclick="cancelSub(${s.id})">İptal</button>
          </td>
        </tr>`).join("")
    : `<tr><td colspan="6" class="muted">Henüz abonelik yok.</td></tr>`;
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
  if (!currentUserId) return toast("Önce bir kullanıcı oluştur.");
  const f = new FormData(e.target);
  const isTrial = f.get("is_trial") === "on";
  try {
    await api("/subscriptions", {
      method: "POST",
      body: JSON.stringify({
        user_id: currentUserId,
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

loadUsers().catch((err) => toast(err.message));
