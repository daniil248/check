"""
NorthPak Logistics - API для проверки контрагентов
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.data_sources import search_counterparty, get_company_by_bin

app = FastAPI(title="NorthPak Logistics API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"service": "NorthPak Logistics", "api": "search", "docs": "/docs"}


@app.get("/api/search")
async def api_search(q: str, country: str = "kz"):
    """Поиск контрагентов по названию, БИН, ФИО"""
    return await search_counterparty(q.strip(), country)


@app.get("/api/company/{bin_id}")
def api_company(bin_id: str):
    """Получить данные по БИН"""
    company = get_company_by_bin(bin_id)
    if company:
        return {"success": True, "company": company}
    return {"success": False, "error": "Не найдено"}


if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
