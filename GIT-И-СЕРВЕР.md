# Git и обновление netchess.ru на сервере

## Что сделано по мобильной адаптации

- **Viewport** уже был в `index.html` — ок.
- **Бургер-меню** на экранах ≤768px: кнопка «гамбургер», выезжающая панель навигации справа, затемнённый фон (клик по фону или Escape закрывает меню).
- **Адаптация блоков:** шапка (телефон коротко, кнопка и языки сжаты), hero (заголовок и форма в колонку), услуги, статистика (2 колонки на телефоне, 1 на очень узком), блок «О компании» (детали реквизитов в колонку), контакты, шаги, футер — всё перестроено под узкие экраны.
- **Отступы:** уменьшены `padding` у `container` и секций на мобильных.
- **Формы:** `font-size: 16px` у полей ввода на мобильных, чтобы iOS не зумил при фокусе.
- **Кнопка бургера** и закрытие меню по клику на ссылку/оверлей/Escape учтены в JS.

Проверь отображение на телефоне или в DevTools (Chrome: F12 → Toggle device toolbar).

---

## Структура проекта для Git

Текущая структура (сайт netchess.ru = папка **check**):

```
PythonProject29/
├── .gitignore
├── КОМАНДЫ-НА-СЕРВЕРЕ.txt
├── GIT-И-СЕРВЕР.md          ← этот файл
├── check/                    ← сайт netchess.ru (NorthPak)
│   ├── .gitignore
│   ├── 404.html
│   ├── index.html
│   ├── logo.jpeg
│   ├── css/
│   │   └── main.css
│   ├── js/
│   │   ├── main.js
│   │   ├── translations.js
│   │   └── ...
│   ├── backend/
│   │   ├── .env.example     ← в репо; .env — НЕ коммитить
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   └── ...
│   └── ВНЕШНИЕ-API.txt
└── siteu/                    ← другой проект (не трогаем для netchess)
```

В репозитории должны быть:
- весь код и статика (html, css, js, backend);
- **не** должны попадать: `.env`, `venv/`, `__pycache__/` (уже в `.gitignore`).

---

## Заливка в Git

### Вариант A: один репозиторий на весь проект (PythonProject29)

Если репозиторий уже создан (GitHub/GitLab/другое) и привязан к папке проекта:

```powershell
cd c:\Users\Admin\PycharmProjects\PythonProject29
git status
git add .
git commit -m "Мобильная адаптация netchess.ru: бургер-меню, адаптивная вёрстка"
git push origin main
```

(замени `main` на свою ветку, если используешь другую).

### Вариант B: отдельный репозиторий только для netchess (папка check)

Если хочешь отдельный репо только для сайта netchess.ru:

1. На GitHub/GitLab создай новый репозиторий (например `netchess-ru`).
2. В папке `check` инициализируй Git и привяжи remote (один раз):

```powershell
cd c:\Users\Admin\PycharmProjects\PythonProject29\check
git init
git remote add origin https://github.com/ТВОЙ_ЛОГИН/netchess-ru.git
git add .
git commit -m "Мобильная адаптация: бургер-меню, адаптивная вёрстка"
git branch -M main
git push -u origin main
```

Тогда на сервере можно клонировать именно этот репо в `/root/check` (см. ниже).

---

## Обновление на сервере

Сервер: **92.51.44.138**, проект в **~/check** (у тебя там: 404.html, backend, css, index.html, js, logo.jpeg, siteu, …).

### Команды на сервере после `git pull` (сохраняем .env, восстанавливаем venv, сбрасываем кэш)

Выполняй по порядку. Сначала залей изменения с локальной машины (`git push`), потом зайди на сервер и:

```bash
# 1) Зайти в каталог проекта
cd ~/check

# 2) Сохранить .env на всякий случай (чтобы pull не затрёл)
cp -a backend/.env /root/check_backend_env.bak 2>/dev/null || true

# 3) Подтянуть изменения (ты сказал — делаешь git pull)
git pull origin main

# 4) Вернуть .env, если его не стало или он пустой
if [ ! -f backend/.env ] || [ ! -s backend/.env ]; then
  cp -a /root/check_backend_env.bak backend/.env 2>/dev/null
fi

# 5) Если venv пропал после pull — пересоздать и поставить зависимости
if [ ! -d backend/venv ]; then
  cd backend
  python3 -m venv venv
  source venv/bin/activate
  pip install --upgrade pip
  pip install -r requirements.txt
  cd ..
fi

# 6) Перезапуск приложения
sudo systemctl restart netchess
sudo systemctl status netchess

# 7) Жёстко обновить кэш nginx (перезагрузить конфиг)
sudo nginx -s reload
```

После этого открой сайт с телефона или в браузере и сделай **жёсткое обновление** (Ctrl+Shift+R или «Очистить кэш и жёсткая перезагрузка»), чтобы подтянулись новые CSS/JS.

Если репо у тебя клонирован не в `~/check`, а, например, в `~/repo` (и в `~/check` лежит копия содержимого **check**), тогда делай pull в каталоге репо и копируй только папку **check** в `~/check`:

```bash
cd ~/repo
git pull origin main
cp -a ~/check/backend/.env /root/check_backend_env.bak 2>/dev/null || true
rsync -av --exclude='.env' --exclude='venv' --exclude='.git' ~/repo/check/ ~/check/
[ -f /root/check_backend_env.bak ] && cp -a /root/check_backend_env.bak ~/check/backend/.env
cd ~/check/backend
[ ! -d venv ] && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
sudo systemctl restart netchess
sudo nginx -s reload
```

(в `rsync` замени `~/repo/check/` на путь к папке **check** внутри твоего клона, например если клон в `~/check` и там есть подпапка `check`, то источник — `~/check/check/`).

### Если на сервере нет Git (проект залит вручную)

Тогда обновить можно так:

1. **Залить в Git** с локальной машины (как в разделе «Заливка в Git» выше).

2. **На сервере** — первый раз настроить клонирование (если хочешь в дальнейшем делать только `git pull`):

```bash
ssh root@92.51.44.138
cd /root
# Сохрани текущий .env, если он уже настроен
cp check/backend/.env /root/check_backend_env.txt   # если файл есть
# Удали старую папку или переименуй
mv check check_old
# Клонируй репозиторий
git clone https://github.com/ТВОЙ_ЛОГИН/ИМЯ_РЕПО.git check
cd check/backend
# Верни .env
cp /root/check_backend_env.txt .env
# Обнови venv и зависимости при необходимости
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart netchess
```

Если репозиторий — весь PythonProject29 (вариант A), то клонируй его в каталог, например `repo`, и скопируй только содержимое `check` в `/root/check`, не затирая существующий `.env`:

```bash
cd /root
git clone https://github.com/ТВОЙ_ЛОГИН/ИМЯ_РЕПО.git repo
rsync -av --exclude='.env' --exclude='venv' repo/check/ /root/check/
cd /root/check/backend
sudo systemctl restart netchess
```

---

## Что тебе нужно уточнить, чтобы не накосячить

1. **Какой у тебя Git сейчас:** один общий репозиторий на весь проект или отдельный на netchess? Если репо уже есть — какой URL (origin)?
2. **Как именно проект попал на сервер:** уже через `git clone` в `/root/check` или файлы копировались вручную/по FTP? От этого зависит, делаем ли мы первый раз `git clone` или просто `git pull`.
3. **Доступ к серверу:** пароль или SSH-ключ к `root@92.51.44.138` — у тебя есть; я не имею доступа к серверу, команды нужно выполнять у себя или у того, у кого есть SSH.

После того как сделаешь `git push` и на сервере выполнишь `git pull` (или первый раз настроишь клонирование), сайт netchess.ru будет обновлён с мобильной адаптацией.
