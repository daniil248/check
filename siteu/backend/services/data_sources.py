"""
NorthPak Logistics - Источники данных по контрагентам
Открытые данные: data.egov.kz, OpenSanctions (опционально)
"""

import httpx
from typing import Optional
import os
from pathlib import Path

# Загрузка .env из backend/
_env_path = Path(__file__).resolve().parent.parent / ".env"
if _env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(_env_path)

# Ключ OpenSanctions — trial: 50 req/mo, истекает 2026-03-03
OPENSANCTIONS_API_KEY = os.getenv("OPENSANCTIONS_API_KEY", "")

# Демо-данные для проверки без внешних API
DEMO_COMPANIES = {
    "250240010778": {
        "bin": "250240010778",
        "name": "Товарищество с ограниченной ответственностью «NorthPak Logistics»",
        "name_short": "NorthPak Logistics",
        "status": "Действующее",
        "address": "081100, Жамбылская область, Шуский район, с. Толе би, ул. Гагарина, 44",
        "director": "Пак Юлия Владимировна",
        "registration_date": "2024",
        "activity": "Грузоперевозки, логистика",
        "source": "demo",
    },
    "123456789012": {
        "bin": "123456789012",
        "name": "Пример компании (демо)",
        "name_short": "Пример",
        "status": "Действующее",
        "address": "г. Алматы",
        "director": "Иванов И.И.",
        "registration_date": "2020",
        "activity": "Торговля",
        "source": "demo",
    },
}


def _normalize_bin(query: str) -> str:
    """Извлекает только цифры из запроса (БИН/ИИН)"""
    return "".join(c for c in str(query) if c.isdigit())


def search_demo(query: str) -> list[dict]:
    """
    Поиск по демо-данным (работает без API).
    Возвращает данные если запрос совпадает с БИН или названием.
    """
    query_clean = query.strip().lower()
    bin_clean = _normalize_bin(query)

    results = []
    for bin_val, company in DEMO_COMPANIES.items():
        if bin_clean and bin_val == bin_clean:
            results.append(company)
            break
        if query_clean in company["name"].lower() or query_clean in company["name_short"].lower():
            results.append(company)

    return results


async def search_opensanctions(query: str, country: str = "kz") -> list[dict]:
    """
    Поиск через OpenSanctions API (санкции, PEP, компании).
    Trial: 50 req/mo, expires 2026-03-03.
    """
    if not OPENSANCTIONS_API_KEY:
        return []

    url = "https://api.opensanctions.org/search/default"
    params = {
        "q": query,
        "schema": "Company",
        "limit": 10,
        "simple": True,  # простой синтаксис для пользовательского ввода
    }
    if country:
        params["countries"] = country.lower()

    headers = {"Authorization": f"Apikey {OPENSANCTIONS_API_KEY}"}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.get(url, params=params, headers=headers)
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            pass  # quota exceeded
        return []
    except Exception:
        return []

    results = []
    for item in data.get("results", [])[:10]:
        props = item.get("properties", {})
        name = _first(props.get("name")) or item.get("caption", "-")
        datasets = item.get("datasets", []) or []
        is_sanctioned = any("ofac" in d.lower() or "sdn" in d.lower() or "sanction" in d.lower() for d in datasets)
        addr = props.get("address") or []
        a0 = _first(addr)
        if isinstance(a0, dict):
            addr_str = a0.get("full", "") or a0.get("country", "") or "-"
        else:
            addr_str = str(a0) if a0 else "-"

        results.append({
            "bin": _first(props.get("registrationNumber")) or _first(props.get("innCode")) or "-",
            "name": name,
            "name_short": (name[:80] + "…") if len(str(name)) > 80 else name,
            "status": "В санкционных списках" if is_sanctioned else "Проверено (OpenSanctions)",
            "address": addr_str,
            "director": "-",
            "registration_date": "-",
            "activity": "-",
            "source": "opensanctions",
        })
    return results


def _first(val):
    """Первый элемент списка или значение как есть"""
    if isinstance(val, list) and val:
        return val[0]
    return val


async def search_data_egov(query: str) -> list[dict]:
    """
    Поиск через data.egov.kz (если есть подходящий датасет).
    Сейчас пробуем общие датасеты — реестр юрлиц может требовать API ключ.
    """
    bin_clean = _normalize_bin(query)
    if len(bin_clean) != 12:
        return []

    # data.egov.kz — список датасетов по Агентству статистики
    # Нужен апстрим: https://data.egov.kz/datasets/listbygovagency
    # Пока возвращаем пустой список — нужна регистрация для API ключа
    return []


async def search_counterparty(query: str, country: str = "kz") -> dict:
    """
    Главная функция поиска. Пробует все источники.
    """
    if not query or len(query.strip()) < 2:
        return {"success": False, "error": "Слишком короткий запрос", "results": []}

    results = []

    # 1. Демо (всегда работает)
    demo = search_demo(query)
    results.extend(demo)

    # 2. OpenSanctions (если есть ключ) — дополняем санкциями/PEP
    if OPENSANCTIONS_API_KEY:
        os_results = await search_opensanctions(query, country)
        # избегаем дублей по БИН/названию
        seen = {r.get("bin") or r.get("name", "") for r in results}
        for r in os_results:
            key = r.get("bin") or r.get("name", "")
            if key not in seen:
                results.append(r)
                seen.add(key)

    return {
        "success": True,
        "query": query,
        "country": country,
        "count": len(results),
        "results": results,
    }


def get_company_by_bin(bin_str: str) -> Optional[dict]:
    """Получить компанию по БИН из демо-данных"""
    bin_clean = _normalize_bin(bin_str)
    return DEMO_COMPANIES.get(bin_clean)
