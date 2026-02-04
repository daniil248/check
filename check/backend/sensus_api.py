"""
Интеграция с Sensus.kz API - проверка контрагентов Казахстана.
Платный сервис, требуется токен. Документация: https://api.sensus.kz/
"""
import httpx
import os
from typing import Optional, List, Dict


SENSUS_API_KEY = os.getenv("SENSUS_API_KEY", "")
SENSUS_BASE_URL = "https://api.sensus.kz/api/v1"


async def search_sensus_companies(query: str) -> List[Dict]:
    """
    Поиск компаний через Sensus.kz API.
    Требуется SENSUS_API_KEY в .env
    """
    if not SENSUS_API_KEY:
        return []
    
    # Определяем тип запроса: БИН или название
    is_bin = query.strip().isdigit() and len(query.strip()) == 12
    
    url = f"{SENSUS_BASE_URL}/search"
    headers = {
        "Authorization": f"Bearer {SENSUS_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "query": query.strip(),
        "country": "kz",
        "limit": 20
    }
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            
            if response.status_code == 401:
                print("Sensus.kz: неверный API ключ")
                return []
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            return normalize_sensus_results(data)
    
    except Exception as e:
        print(f"Ошибка при запросе к Sensus.kz: {e}")
        return []


def normalize_sensus_results(data: dict) -> List[Dict]:
    """Преобразует ответ Sensus.kz в единый формат"""
    results = []
    companies = data.get("results", []) or data.get("data", [])
    
    for company in companies:
        results.append({
            "bin": company.get("bin", "") or company.get("code", ""),
            "name": company.get("name", "") or company.get("fullName", ""),
            "name_short": company.get("shortName", "") or company.get("name", ""),
            "status": company.get("status", "Неизвестно"),
            "director": company.get("director", "") or company.get("head", ""),
            "address": company.get("address", ""),
            "registration_date": company.get("registrationDate", ""),
            "activity": company.get("activity", ""),
            "country": "kz",
            "source": "sensus.kz",
            "phone": company.get("phone", ""),
            "email": company.get("email", ""),
        })
    
    return results


async def get_company_details_sensus(bin_id: str) -> Optional[Dict]:
    """Получить детальную информацию о компании по БИН"""
    if not SENSUS_API_KEY or not bin_id.strip().isdigit():
        return None
    
    url = f"{SENSUS_BASE_URL}/company/{bin_id.strip()}"
    headers = {
        "Authorization": f"Bearer {SENSUS_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, headers=headers)
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            company = data.get("data", {})
            
            return {
                "bin": company.get("bin", ""),
                "name": company.get("name", ""),
                "name_short": company.get("shortName", ""),
                "status": company.get("status", ""),
                "director": company.get("director", ""),
                "address": company.get("address", ""),
                "registration_date": company.get("registrationDate", ""),
                "activity": company.get("activity", ""),
                "phone": company.get("phone", ""),
                "email": company.get("email", ""),
                "source": "sensus.kz"
            }
    
    except Exception as e:
        print(f"Ошибка при получении детальной информации из Sensus.kz: {e}")
        return None
