document.addEventListener("DOMContentLoaded", function () {
    if (!getToken()) {
        window.location.href = "/login";
        return;
    }
    const loading = document.getElementById("cabinet-loading");
    const content = document.getElementById("cabinet-content");
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
        })
        .catch(function () {
            loading.textContent = "Ошибка загрузки";
        });

    document.getElementById("nav-logout").addEventListener("click", function (e) {
        e.preventDefault();
        clearToken();
        window.location.href = "/login";
    });
});
