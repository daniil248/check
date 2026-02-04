/**
 * NorthPak Logistics - Language Switcher & i18n
 */

const STORAGE_KEY = 'northpak-lang';
const SUPPORTED_LANGS = ['ru', 'en', 'zh'];

function getCurrentLang() {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored && SUPPORTED_LANGS.includes(stored)) return stored;
    const browserLang = (navigator.language || navigator.userLanguage || 'ru').slice(0, 2);
    return SUPPORTED_LANGS.includes(browserLang) ? browserLang : 'ru';
}

function setLang(lang) {
    if (!SUPPORTED_LANGS.includes(lang)) return;
    localStorage.setItem(STORAGE_KEY, lang);
    document.documentElement.lang = lang === 'zh' ? 'zh-CN' : lang;
    document.documentElement.dataset.lang = lang;
    applyTranslations(lang);
    updateLangButtons(lang);
}

function applyTranslations(lang) {
    const t = TRANSLATIONS[lang];
    if (!t) return;

    document.title = t.pageTitle;
    const metaDesc = document.querySelector('meta[name="description"]');
    if (metaDesc) metaDesc.content = t.metaDesc;

    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        const val = t[key];
        if (val !== undefined) el.textContent = val;
    });

    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        const val = t[key];
        if (val !== undefined) el.placeholder = val;
    });


    document.querySelectorAll('[data-i18n-title]').forEach(el => {
        const key = el.getAttribute('data-i18n-title');
        const val = t[key];
        if (val !== undefined) el.title = val;
    });

    // Select options (by data-i18n-option)
    document.querySelectorAll('[data-i18n-options]').forEach(selectEl => {
        const keys = selectEl.getAttribute('data-i18n-options').split(' ');
        selectEl.querySelectorAll('option').forEach((opt, i) => {
            if (keys[i]) opt.textContent = t[keys[i]] || opt.textContent;
        });
    });
}

function updateLangButtons(currentLang) {
    document.querySelectorAll('.lang-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.lang === currentLang);
    });
}

function initLangSwitcher() {
    const currentLang = getCurrentLang();
    setLang(currentLang);

    document.querySelectorAll('.lang-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            setLang(btn.dataset.lang);
        });
    });
}

document.addEventListener('DOMContentLoaded', initLangSwitcher);
