"""
Интеграция с Adata.kz API - полный реестр юридических лиц Казахстана.
Платный сервис, требуется токен.
"""
import httpx
import os
from typing import Optional, List, Dict


ADATA_API_KEY = os.getenv("ADATA_API_KEY", "")
ADATA_BASE_URL = "https://adata.kz/api"


async def search_adata_companies(query: str) -> List[Dict]:
    """
    Поиск компаний через Adata.kz API по названию или БИН.
    Требуется ADATA_API_KEY в .env
    """
    if not ADATA_API_KEY:
        return []
    
    # Проверяем: это БИН (12 цифр) или название
    is_bin = query.strip().isdigit() and len(query.strip()) == 12
    
    # Формируем запрос (нужно уточнить точный формат у Adata.kz)
    url = f"{ADATA_BASE_URL}/search"
    headers = {
        "Authorization": f"Bearer {ADATA_API_KEY}",
        "Content-Type": "application/json"
    }
    
    params = {
        "query": query.strip(),
        "type": "bin" if is_bin else "name",
        "limit": 20
    }
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, params=params, headers=headers)
            
            if response.status_code == 401:
                print("Adata.kz: неверный API ключ")
                return []
            
            if response.status_code != 200:
                print(f"Adata.kz API error: {response.status_code}")
                return []
            
            data = response.json()
            return normalize_adata_results(data)
    
    except Exception as e:
        print(f"Ошибка при запросе к Adata.kz: {e}")
        return []


def normalize_adata_results(data: dict) -> List[Dict]:
    """
    Преобразует ответ Adata.kz в единый формат.
    Формат зависит от их API - нужно уточнить в документации.
    """
    results = []
    
    # Предполагаемый формат ответа (нужно уточнить)
    companies = data.get("data", []) or data.get("companies", [])
    
    for company in companies:
        results.append({
            "bin": company.get("bin", ""),
            "name": company.get("name", "") or company.get("full_name", ""),
            "name_short": company.get("short_name", "") or company.get("name", ""),
            "status": company.get("status", "Неизвестно"),
            "director": company.get("director", "") or company.get("head", ""),
            "address": company.get("address", "") or company.get("legal_address", ""),
            "registration_date": company.get("registration_date", ""),
            "activity": company.get("activity", "") or company.get("oked", ""),
            "country": "kz",
            "source": "adata.kz",
            "phone": company.get("phone", ""),
            "email": company.get("email", ""),
            "tax_debt": company.get("tax_debt"),
            "employees": company.get("employees_count"),
        })
    
    return results


async def get_company_details_adata(bin_id: str) -> Optional[Dict]:
    """
    Получить детальную информацию о компании по БИН через Adata.kz
    """
    if not ADATA_API_KEY or not bin_id.strip().isdigit():
        return None
    
    url = f"{ADATA_BASE_URL}/company/{bin_id.strip()}"
    headers = {
        "Authorization": f"Bearer {ADATA_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, headers=headers)
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            company = data.get("data", {}) or data
            
            return {
                "bin": company.get("bin", ""),
                "name": company.get("name", "") or company.get("full_name", ""),
                "name_short": company.get("short_name", ""),
                "status": company.get("status", ""),
                "director": company.get("director", "") or company.get("head", ""),
                "address": company.get("address", "") or company.get("legal_address", ""),
                "registration_date": company.get("registration_date", ""),
                "activity": company.get("activity", ""),
                "phone": company.get("phone", ""),
                "email": company.get("email", ""),
                "tax_debt": company.get("tax_debt"),
                "employees": company.get("employees_count"),
                "licenses": company.get("licenses", []),
                "source": "adata.kz"
            }
    
    except Exception as e:
        print(f"Ошибка при получении детальной информации из Adata.kz: {e}")
        return None
