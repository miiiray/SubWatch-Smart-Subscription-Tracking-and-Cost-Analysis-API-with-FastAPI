const TOKEN_KEY = "subwatch_token";
const $ = (id) => document.getElementById(id);

// ---------- Token'ı tarayıcıda saklama ----------
function saveToken(token) {
  try { localStorage.setItem(TOKEN_KEY, token); } catch (e) {}
}

function getToken() {
  try { return localStorage.getItem(TOKEN_KEY); } catch (e) { return null; }
}

function showError(message) {
  $("error").textContent = message;
}

// ---------- API'ye POST isteği ----------
async function post(path, body) {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    let detail = data && data.detail;
    if (Array.isArray(detail)) detail = detail[0] && detail[0].msg;
    throw new Error(typeof detail === "string" ? detail : "Bir hata oluştu.");
  }
  return data;
}

// ---------- Sekmeler ----------
function showTab(name) {
  $("loginForm").classList.toggle("hidden", name !== "login");
  $("registerForm").classList.toggle("hidden", name !== "register");
  $("tabLogin").classList.toggle("active", name === "login");
  $("tabRegister").classList.toggle("active", name === "register");
  showError("");
}

$("tabLogin").addEventListener("click", () => showTab("login"));
$("tabRegister").addEventListener("click", () => showTab("register"));

// ---------- Giriş ----------
$("loginForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const f = new FormData(e.target);
  try {
    const data = await post("/auth/login", {
      email: f.get("email"),
      password: f.get("password"),
    });
    saveToken(data.access_token);
    window.location.href = "/app";
  } catch (err) {
    showError(err.message);
  }
});

// ---------- Kayıt (sonra otomatik giriş) ----------
$("registerForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const f = new FormData(e.target);
  const email = f.get("email");
  const password = f.get("password");
  try {
    await post("/auth/register", {
      name: f.get("name"),
      email: email,
      password: password,
      monthly_budget: Number(f.get("monthly_budget")),
    });
    const data = await post("/auth/login", { email, password });
    saveToken(data.access_token);
    window.location.href = "/app";
  } catch (err) {
    showError(err.message);
  }
});

// ---------- Zaten giriş yapılmışsa direkt panele git ----------
(async () => {
  const token = getToken();
  if (!token) return;
  const res = await fetch("/auth/me", { headers: { Authorization: `Bearer ${token}` } });
  if (res.ok) window.location.href = "/app";
})();