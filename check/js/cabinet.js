document.addEventListener("DOMContentLoaded", function () {
    if (!getToken()) {
        window.location.href = "/login";
        return;
    }
    const loading = document.getElementById("cabinet-loading");
    const content = document.getElementById("cabinet-content");
    const historyLoading = document.getElementById("history-loading");
    const historyContent = document.getElementById("history-content");
    
    fetch("/api/me", { headers: authHeaders() })
        .then(function (r) {
            if (r.status === 401) {
                clearToken();
                window.location.href = "/login";
                return null;
            }
            return r.json();
        })
        .then(function (data) {
            if (!data || !data.user) return;
            loading.style.display = "none";
            content.style.display = "block";
            var u = data.user;
            document.getElementById("cabinet-email").textContent = u.email;
            document.getElementById("cabinet-name").textContent = u.name || u.email;
            var avatar = document.getElementById("cabinet-avatar");
            if (u.picture) {
                var img = document.createElement("img");
                img.src = u.picture;
                img.alt = "";
                img.className = "cabinet-avatar-img";
                avatar.appendChild(img);
            } else {
                avatar.textContent = (u.name || u.email || "?").charAt(0).toUpperCase();
            }
            loadHistory();
        })
        .catch(function () {
            loading.textContent = "Ошибка загрузки";
        });

    function loadHistory() {
        fetch("/api/search-history", { headers: authHeaders() })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                historyLoading.style.display = "none";
                historyContent.style.display = "block";
                if (!data.history || data.history.length === 0) {
                    historyContent.innerHTML = "<p class='history-empty'>История поисков пуста</p>";
                    return;
                }
                var html = "";
                data.history.forEach(function (item) {
                    var date = new Date(item.created_at).toLocaleString("ru-RU");
                    html += "<div class='history-item'>";
                    html += "<span class='history-query'>" + escapeHtml(item.query) + "</span>";
                    html += "<span class='history-country'>" + item.country.toUpperCase() + "</span>";
                    html += "<span class='history-count'>" + item.results_count + " результатов</span>";
                    html += "<span class='history-date'>" + date + "</span>";
                    html += "</div>";
                });
                historyContent.innerHTML = html;
            });
    }

    function escapeHtml(s) {
        var div = document.createElement("div");
        div.textContent = s || "";
        return div.innerHTML;
    }

    var logoutBtn = document.getElementById("nav-logout");
    if (logoutBtn) {
        logoutBtn.addEventListener("click", function (e) {
            e.preventDefault();
            clearToken();
            window.location.href = "/login";
        });
    }
});
