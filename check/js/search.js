/**
 * NorthPak Logistics - Поиск контрагентов
 */

// API: на своём домене и Vercel — тот же хост (один сервер). Локально — отдельный порт.
const API_BASE = (() => {
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        return 'http://localhost:8000';
    }
    return '';  // свой домен или Vercel: фронт и API на одном сервере
})();

const MSG_NO_API = 'Сервис временно недоступен. Проверьте подключение или обратитесь к администратору.';

async function doSearch(query, country) {
    const container = document.getElementById('search-results');
    if (!container) return;

    container.style.display = 'block';

    const base = API_BASE || window.location.origin;
    if (!base) {
        container.innerHTML = `<div class="search-results-error">${MSG_NO_API}</div>`;
        return;
    }
    const url = `${base}/api/search?q=${encodeURIComponent(query)}&country=${country}`;

    container.innerHTML = '<div class="search-results-loading">Поиск...</div>';

    try {
        const headers = {};
        if (typeof authHeaders === "function") {
            Object.assign(headers, authHeaders());
        }
        const res = await fetch(url, { headers });
        if (res.status === 401 && typeof clearToken === "function") {
            clearToken();
            window.location.href = "/login";
            return;
        }
        const text = await res.text();
        let data;
        try {
            data = JSON.parse(text);
        } catch (_) {
            throw new Error(MSG_NO_API);
        }

        if (!data.success) {
            container.innerHTML = `<div class="search-results-error">${data.error || 'Ошибка поиска'}</div>`;
            return;
        }

        if (!data.results || data.results.length === 0) {
            container.innerHTML = '<div class="search-results-empty">По запросу ничего не найдено</div>';
            return;
        }

        let html = `<div class="search-results-header"><h3>Найдено: ${data.count}</h3></div>`;
        data.results.forEach(c => {
            const statusClass = c.status === 'Действующее' ? 'status-active' : 'status-inactive';
            html += `
                <div class="search-result-card">
                    <div class="search-result-header">
                        <div class="search-result-name">${escapeHtml(c.name_short || c.name)}</div>
                        <span class="search-result-status ${statusClass}">${escapeHtml(c.status)}</span>
                    </div>
                    <div class="search-result-bin">БИН: <strong>${escapeHtml(c.bin)}</strong></div>
                    <div class="search-result-meta">
                        <div class="search-result-row">
                            <span class="meta-label">Руководитель:</span>
                            <span class="meta-value">${escapeHtml(c.director)}</span>
                        </div>
                        <div class="search-result-row">
                            <span class="meta-label">Адрес:</span>
                            <span class="meta-value">${escapeHtml(c.address)}</span>
                        </div>
                    </div>
                    <div class="search-result-actions">
                        <a href="/company/${encodeURIComponent(c.bin)}" class="result-detail-btn">Подробнее</a>
                    </div>
                </div>
            `;
        });
        container.innerHTML = html;
    } catch (err) {
        container.innerHTML = `<div class="search-results-error">${err.message}</div>`;
    }
}

function escapeHtml(s) {
    const div = document.createElement('div');
    div.textContent = s || '';
    return div.innerHTML;
}

function initSearch() {
    const form = document.querySelector('.search-form');
    const examples = document.querySelectorAll('.example-link[data-search]');

    if (form) {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            const input = form.querySelector('input[name="search"]');
            const select = form.querySelector('select[name="country"]');
            const query = input?.value?.trim();
            const country = select?.value || 'kz';
            if (query) doSearch(query, country);
        });
    }

    examples.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const query = link.getAttribute('data-search');
            const select = document.querySelector('.search-select');
            if (query) {
                const input = document.querySelector('.search-input');
                if (input) input.value = query;
                doSearch(query, select?.value || 'kz');
            }
        });
    });
}

document.addEventListener('DOMContentLoaded', initSearch);
