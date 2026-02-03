# NorthPak Logistics — Сайт проверки контрагентов

Многоязычный лендинг (RU | EN | 中文) с поиском по открытым данным.

## Структура проекта

```
siteu/
├── index.html          # Главная страница
├── logo.jpeg           # Логотип
├── css/style.css       # Стили
├── js/
│   ├── translations.js # Переводы (RU, EN, ZH)
│   ├── app.js          # Переключение языков
│   └── search.js       # Поиск контрагентов
└── backend/            # API для поиска
    ├── main.py         # FastAPI
    ├── requirements.txt
    └── services/
        └── data_sources.py  # Источники данных
```

## Запуск с поиском (локально)

**Терминал 1 — Backend:**
```bash
cd siteu/backend
pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

**Терминал 2 — Фронтенд:**
```bash
cd siteu
python -m http.server 8080
```

Откройте http://localhost:8080 — поиск по БИН 250240010778 и NorthPak работает.

## Источники данных

- **Демо** — встроенные данные (NorthPak, пример) — работает без настроек
- **OpenSanctions** — санкции, PEP. Trial: 50 req/мес, до 2026-03-03
  - Скопируйте `backend/.env.example` → `backend/.env` и вставьте ключ
  - Или: `set OPENSANCTIONS_API_KEY=ваш_ключ`

## Языки

- **RU** | **EN** | **中文** — переключатель в шапке

## GitHub Pages

Фронтенд (без поиска) — скопируйте в корень репо. Для поиска нужен отдельный хостинг backend (Railway, Render и т.п.).
