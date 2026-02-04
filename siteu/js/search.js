/**
 * NorthPak Logistics - Поиск контрагентов
 */

// API для поиска: localhost при разработке, Render — на проде
const API_BASE = (() => {
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        return 'http://localhost:8000';
    }
    if (window.location.hostname.includes('github.io')) {
        return 'https://northpak-api.onrender.com';  // после deploy на Render
    }
    return '';
})();

const MSG_NO_API = 'API не отвечает. Задеплойте backend: Render.com → New → Blueprint → репо check, rootDir: backend. Сервис назовите northpak-api.';

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
        const res = await fetch(url);
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

        let html = `<h3>Найдено: ${data.count}</h3>`;
        data.results.forEach(c => {
            html += `
                <div class="search-result-card">
                    <div class="search-result-name">${escapeHtml(c.name_short || c.name)}</div>
                    <div class="search-result-meta">
                        <span><strong>БИН:</strong> ${escapeHtml(c.bin)}</span>
                        <span><strong>Статус:</strong> ${escapeHtml(c.status)}</span>
                        <span><strong>Руководитель:</strong> ${escapeHtml(c.director)}</span>
                        <span><strong>Адрес:</strong> ${escapeHtml(c.address)}</span>
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
