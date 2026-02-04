"""
NorthPak Logistics — простой лендинг без авторизации.
"""

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="NorthPak Logistics")

# Статика
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


@app.get("/")
def index():
    return FileResponse(FRONTEND / "index.html")


# Все остальные маршруты -> главная страница
@app.get("/{path:path}")
def catch_all(path: str):
    # Перенаправляем на главную
    return RedirectResponse(url="/")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8007))
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)
