"""
NorthPak Logistics — продакшен API: авторизация + поиск.
Один сервер: фронт + API. Деплой на VPS, свой домен.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from urllib.parse import urlencode

from fastapi import Depends, HTTPException, Request
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
import httpx

from auth import (
    init_db,
    create_user,
    create_or_get_user_google,
    get_user_by_email,
    verify_password,
    create_access_token,
    get_current_user,
)
from services.data_sources import search_counterparty, get_company_by_bin

app = FastAPI(title="NorthPak Logistics API", docs_url="/api/docs", redoc_url="/api/redoc")

_origins = os.environ.get("ALLOWED_ORIGINS", "*")
_origins_list = [o.strip() for o in _origins.split(",") if o.strip()] if _origins != "*" else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Статика (продакшен: фронт рядом с backend)
FRONTEND = Path(__file__).resolve().parent.parent
if FRONTEND.exists():
    app.mount("/css", StaticFiles(directory=FRONTEND / "css"), name="css")
    app.mount("/js", StaticFiles(directory=FRONTEND / "js"), name="js")


@app.get("/logo.jpeg")
def logo():
    p = FRONTEND / "logo.jpeg"
    if p.exists():
        return FileResponse(p, media_type="image/jpeg")
    raise HTTPException(404)


@app.get("/favicon.ico")
def favicon():
    p = FRONTEND / "logo.jpeg"
    if p.exists():
        return FileResponse(p, media_type="image/jpeg")
    raise HTTPException(404)


@app.on_event("startup")
def startup():
    init_db()


# ——— Публичные маршруты ———
@app.get("/")
def index():
    return FileResponse(FRONTEND / "index.html")


@app.get("/login")
def login_page():
    return FileResponse(FRONTEND / "login.html")


@app.get("/cabinet")
def cabinet_page():
    return FileResponse(FRONTEND / "cabinet.html")


class RegisterBody(BaseModel):
    email: str
    password: str


@app.post("/api/auth/register")
def register(body: RegisterBody):
    email = (body.email or "").strip()
    password = body.password or ""
    if not email:
        raise HTTPException(status_code=400, detail="Укажите email")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Пароль не менее 6 символов")
    user = create_user(email, password)
    token = create_access_token({"sub": user["email"]})
    return {"ok": True, "token": token, "user": {"email": user["email"]}}


@app.post("/api/auth/login")
def login(form: OAuth2PasswordRequestForm = Depends()):
    user = get_user_by_email(form.username)
    if not user or not verify_password(form.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")
    token = create_access_token({"sub": user["email"]})
    return {"ok": True, "token": token, "user": {"email": user["email"]}}


@app.get("/api/me")
def me(user=Depends(get_current_user)):
    return {"ok": True, "user": user}


# Google OAuth (GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET в .env)
@app.get("/api/auth/google")
def google_login(request: Request):
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    if not client_id:
        raise HTTPException(status_code=503, detail="Вход через Google не настроен")
    base = str(request.base_url).rstrip("/")
    redirect_uri = f"{base}/api/auth/google/callback"
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
    }
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)
    return RedirectResponse(url)


@app.get("/api/auth/google/callback")
async def google_callback(request: Request, code: str = ""):
    if not code:
        raise HTTPException(status_code=400, detail="Нет кода от Google")
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise HTTPException(status_code=503, detail="Вход через Google не настроен")
    base = str(request.base_url).rstrip("/")
    redirect_uri = f"{base}/api/auth/google/callback"
    async with httpx.AsyncClient() as client:
        token_res = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    if token_res.status_code != 200:
        raise HTTPException(status_code=400, detail="Ошибка обмена кода Google")
    token_data = token_res.json()
    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="Нет токена от Google")
    async with httpx.AsyncClient() as client:
        user_res = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
    if user_res.status_code != 200:
        raise HTTPException(status_code=400, detail="Не удалось получить данные Google")
    profile = user_res.json()
    email = (profile.get("email") or "").strip()
    name = (profile.get("name") or "").strip()
    picture = (profile.get("picture") or "").strip()
    google_id = (profile.get("id") or "").strip()
    user = create_or_get_user_google(email=email, name=name, picture=picture, google_id=google_id)
    jwt_token = create_access_token({"sub": user["email"]})
    return RedirectResponse(url=f"/?token={jwt_token}")


# ——— Защищённые API (только для авторизованных) ———
@app.get("/api/search")
async def api_search(q: str, country: str = "kz", user=Depends(get_current_user)):
    """Поиск контрагентов (требуется авторизация)."""
    return await search_counterparty(q.strip(), country)


@app.get("/api/company/{bin_id}")
def api_company(bin_id: str, user=Depends(get_current_user)):
    company = get_company_by_bin(bin_id)
    if company:
        return {"success": True, "company": company}
    return {"success": False, "error": "Не найдено"}


@app.get("/{path:path}")
def catch_all(path: str):
    if path.startswith("api/"):
        raise HTTPException(404, detail="Not Found")
    p = FRONTEND / "404.html"
    if p.exists():
        return FileResponse(p, status_code=404)
    raise HTTPException(404)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)
