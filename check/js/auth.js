/**
 * Авторизация: токен в localStorage, редирект на /login.
 */
const AUTH_TOKEN_KEY = "northpak_token";

(function takeTokenFromUrl() {
    var params = new URLSearchParams(window.location.search);
    var token = params.get("token");
    if (token) {
        localStorage.setItem(AUTH_TOKEN_KEY, token);
        var url = window.location.pathname || "/";
        if (window.history.replaceState) {
            window.history.replaceState({}, "", url);
        } else {
            window.location.search = "";
        }
    }
})();

function getToken() {
    return localStorage.getItem(AUTH_TOKEN_KEY);
}

function setToken(token) {
    localStorage.setItem(AUTH_TOKEN_KEY, token);
}

function clearToken() {
    localStorage.removeItem(AUTH_TOKEN_KEY);
}

function authHeaders() {
    const t = getToken();
    return t ? { Authorization: `Bearer ${t}` } : {};
}

/** Редирект на логин, если не авторизован (вызывать на главной). */
function requireAuth() {
    if (!getToken() && !window.location.pathname.includes("/login")) {
        window.location.href = "/login";
        return false;
    }
    return true;
}

/** Инициализация страницы логина. */
function initLoginPage() {
    const loginForm = document.getElementById("login-form");
    const registerForm = document.getElementById("register-form");
    const toggleRegister = document.getElementById("toggle-register");
    const toggleLogin = document.getElementById("toggle-login");
    const errorEl = document.getElementById("auth-error");
    const card = document.querySelector(".auth-card");

    function showError(msg) {
        errorEl.textContent = msg;
        errorEl.style.display = "block";
    }
    function hideError() {
        errorEl.style.display = "none";
    }

    if (loginForm) {
        loginForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            hideError();
            const fd = new FormData(loginForm);
            const email = fd.get("email");
            const password = fd.get("password");
            try {
                const form = new URLSearchParams({ username: email, password });
                const res = await fetch("/api/auth/login", {
                    method: "POST",
                    headers: { "Content-Type": "application/x-www-form-urlencoded" },
                    body: form,
                });
                const data = await res.json().catch(() => ({}));
                if (res.ok && data.token) {
                    setToken(data.token);
                    window.location.href = "/";
                    return;
                }
                showError(data.detail || data.error || "Ошибка входа");
            } catch (err) {
                showError("Ошибка сети");
            }
        });
    }

    if (registerForm) {
        registerForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            hideError();
            const fd = new FormData(registerForm);
            const email = fd.get("email");
            const password = fd.get("password");
            try {
                const res = await fetch("/api/auth/register", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ email, password }),
                });
                const data = await res.json().catch(() => ({}));
                if (res.ok && data.token) {
                    setToken(data.token);
                    window.location.href = "/";
                    return;
                }
                showError(data.detail || data.error || "Ошибка регистрации");
            } catch (err) {
                showError("Ошибка сети");
            }
        });
    }

    if (toggleRegister) {
        toggleRegister.addEventListener("click", (e) => {
            e.preventDefault();
            card.classList.add("show-register");
            toggleRegister.style.display = "none";
            toggleLogin.style.display = "inline";
        });
    }
    if (toggleLogin) {
        toggleLogin.addEventListener("click", (e) => {
            e.preventDefault();
            card.classList.remove("show-register");
            toggleRegister.style.display = "inline";
            toggleLogin.style.display = "none";
        });
    }
}

/** Если мы на главной (index) или кабинете — проверить токен. */
function initAuthGuard() {
    if (window.location.pathname === "/login" || window.location.pathname.endsWith("login.html")) {
        if (getToken()) {
            window.location.href = "/";
        }
        initLoginPage();
        return;
    }
    if (window.location.pathname === "/cabinet" || window.location.pathname.endsWith("cabinet.html")) {
        if (!getToken()) window.location.href = "/login";
        return;
    }
    requireAuth();
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initAuthGuard);
} else {
    initAuthGuard();
}
