"""
NorthPak Logistics - Источники данных по контрагентам
Открытые данные: data.egov.kz, OpenSanctions (опционально)
"""

import httpx
from typing import Optional
import os
from pathlib import Path

# Загрузка .env из backend/ или из корня (Vercel)
_env_path = Path(__file__).resolve().parent.parent / ".env"
if not _env_path.exists():
    _env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if _env_path.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(_env_path)
    except ImportError:
        pass

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
    Поиск через data.egov.kz Open Data API.
    Ищем по медорганизациям, аптекам, нотариусам, ЦОНам и др.
    """
    if len(query.strip()) < 2:
        return []
    
    # Импортируем функцию поиска по всем наборам data.egov.kz
    from egov_api import search_all_egov
    
    try:
        results = await search_all_egov(query)
        return results
    except Exception as e:
        print(f"Ошибка при поиске в data.egov.kz: {e}")
        return []


async def search_counterparty(query: str, country: str = "kz") -> dict:
    """
    Главная функция поиска. Пробует все источники.
    ПРИОРИТЕТ: Платные API > Stat.gov.kz > Демо
    """
    if not query or len(query.strip()) < 2:
        return {"success": False, "error": "Слишком короткий запрос", "results": []}

    results = []
    seen = set()

    # 1. Sensus.kz API (платный, полный реестр ЮЛ)
    sensus_key = os.getenv("SENSUS_API_KEY", "")
    if sensus_key:
        try:
            from sensus_api import search_sensus_companies
            sensus_results = await search_sensus_companies(query)
            for r in sensus_results:
                key = r.get("bin") or r.get("name", "")
                if key and key not in seen:
                    results.append(r)
                    seen.add(key)
        except Exception as e:
            print(f"Sensus.kz error: {e}")

    # 2. Adata.kz API (платный, полный реестр ЮЛ)
    adata_key = os.getenv("ADATA_API_KEY", "")
    if adata_key:
        try:
            from adata_api import search_adata_companies
            adata_results = await search_adata_companies(query)
            for r in adata_results:
                key = r.get("bin") or r.get("name", "")
                if key and key not in seen:
                    results.append(r)
                    seen.add(key)
        except Exception as e:
            print(f"Adata.kz error: {e}")

    # 3. Stat.gov.kz парсинг (бесплатно, только по БИН)
    try:
        from statgov_parser import search_companies_statgov
        statgov_results = await search_companies_statgov(query)
        for r in statgov_results:
            key = r.get("bin") or r.get("name", "")
            if key and key not in seen:
                results.append(r)
                seen.add(key)
    except Exception as e:
        print(f"Stat.gov.kz error: {e}")

    # 4. Демо-данные (если ничего не нашли или для отладки)
    if not results or "northpak" in query.lower() or "250240010778" in query:
        demo = search_demo(query)
        for r in demo:
            key = r.get("bin") or r.get("name", "")
            if key and key not in seen:
                results.append(r)
                seen.add(key)

    # 5. OpenSanctions (санкции/PEP проверка)
    if OPENSANCTIONS_API_KEY:
        os_results = await search_opensanctions(query, country)
        for r in os_results:
            key = r.get("bin") or r.get("name", "")
            if key and key not in seen:
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
