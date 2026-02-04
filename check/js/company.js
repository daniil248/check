document.addEventListener("DOMContentLoaded", function () {
    if (!getToken()) {
        window.location.href = "/login";
        return;
    }
    const pathParts = window.location.pathname.split("/");
    const bin = pathParts[pathParts.length - 1];
    if (!bin) {
        window.location.href = "/";
        return;
    }
    
    const loading = document.getElementById("company-loading");
    const content = document.getElementById("company-content");
    
    fetch("/api/company/" + encodeURIComponent(bin), { headers: authHeaders() })
        .then(function (r) {
            if (r.status === 401) {
                clearToken();
                window.location.href = "/login";
                return null;
            }
            return r.json();
        })
        .then(function (data) {
            if (!data || !data.success || !data.company) {
                loading.textContent = "Компания не найдена";
                return;
            }
            loading.style.display = "none";
            content.style.display = "block";
            var c = data.company;
            document.getElementById("company-name").textContent = c.name || c.name_short;
            var status = document.getElementById("company-status");
            status.textContent = c.status;
            status.className = "company-status " + (c.status === "Действующее" ? "status-active" : "status-inactive");
            
            var html = "";
            html += "<div class='company-section'><h3>Основная информация</h3>";
            html += "<div class='company-row'><span>БИН:</span><span>" + escapeHtml(c.bin) + "</span></div>";
            html += "<div class='company-row'><span>Руководитель:</span><span>" + escapeHtml(c.director) + "</span></div>";
            html += "<div class='company-row'><span>Адрес:</span><span>" + escapeHtml(c.address) + "</span></div>";
            if (c.phone) html += "<div class='company-row'><span>Телефон:</span><span>" + escapeHtml(c.phone) + "</span></div>";
            if (c.email) html += "<div class='company-row'><span>Email:</span><span>" + escapeHtml(c.email) + "</span></div>";
            html += "</div>";
            
            document.getElementById("company-details").innerHTML = html;
        })
        .catch(function () {
            loading.textContent = "Ошибка загрузки";
        });
    
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
