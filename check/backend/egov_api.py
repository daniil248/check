"""
Интеграция с data.egov.kz Open Data API для поиска контрагентов.
"""
import httpx
from typing import List, Dict, Optional


BASE_URL = "https://data.egov.kz/api/v4"


async def search_egov_dataset(dataset: str, query_text: str, fields: List[str], size: int = 20) -> List[Dict]:
    """
    Универсальный поиск по набору данных data.egov.kz
    
    Args:
        dataset: Название набора данных (например, 'medorg', 'pharmacy')
        query_text: Текст для поиска
        fields: Список полей для поиска
        size: Количество результатов
    """
    # Формируем запрос для elasticsearch
    must_clauses = [{"match": {field: query_text}} for field in fields]
    
    source = {
        "size": size,
        "query": {
            "bool": {
                "should": must_clauses,
                "minimum_should_match": 1
            }
        }
    }
    
    url = f"{BASE_URL}/{dataset}/v1"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params={"source": str(source)})
            if response.status_code == 200:
                data = response.json()
                return data if isinstance(data, list) else []
            return []
    except Exception as e:
        print(f"Ошибка при запросе к {dataset}: {e}")
        return []


async def search_medical_orgs(query: str) -> List[Dict]:
    """Поиск медицинских организаций"""
    results = await search_egov_dataset(
        dataset="medorg",
        query_text=query,
        fields=["name", "address", "region"],
        size=10
    )
    
    # Преобразуем в единый формат
    normalized = []
    for item in results:
        normalized.append({
            "bin": item.get("id", ""),
            "name": item.get("name", ""),
            "name_short": item.get("name", ""),
            "status": "Действующее",
            "director": "Не указано",
            "address": item.get("address", ""),
            "country": "kz",
            "source": "data.egov.kz (medorg)",
            "geoposition": item.get("geoposition", ""),
            "region": item.get("region", "")
        })
    return normalized


async def search_pharmacies(query: str) -> List[Dict]:
    """Поиск аптек"""
    results = await search_egov_dataset(
        dataset="pharmacy",
        query_text=query,
        fields=["Name", "Address", "Region"],
        size=10
    )
    
    normalized = []
    for item in results:
        normalized.append({
            "bin": str(item.get("id", "")),
            "name": item.get("Name", ""),
            "name_short": item.get("Name", ""),
            "status": "Действующее",
            "director": "Не указано",
            "address": item.get("Address", ""),
            "country": "kz",
            "source": "data.egov.kz (pharmacy)",
            "geoposition": item.get("geoposition", ""),
            "Region": item.get("Region", "")
        })
    return normalized


async def search_notaries(query: str) -> List[Dict]:
    """Поиск нотариусов"""
    results = await search_egov_dataset(
        dataset="notaries",
        query_text=query,
        fields=["Fio", "Adres", "Oblast"],
        size=10
    )
    
    normalized = []
    for item in results:
        normalized.append({
            "bin": str(item.get("Bin", "")),
            "name": f"Нотариус {item.get('Fio', '')}",
            "name_short": item.get("Fio", ""),
            "status": "Действующее",
            "director": item.get("Fio", ""),
            "address": item.get("Adres", ""),
            "country": "kz",
            "source": "data.egov.kz (notaries)",
            "phone": item.get("Phone", ""),
            "oblast": item.get("Oblast", "")
        })
    return normalized


async def search_tsons(query: str) -> List[Dict]:
    """Поиск ЦОНов (центры обслуживания населения)"""
    results = await search_egov_dataset(
        dataset="tson",
        query_text=query,
        fields=["Name", "Address"],
        size=10
    )
    
    normalized = []
    for item in results:
        normalized.append({
            "bin": str(item.get("id", "")),
            "name": item.get("Name", ""),
            "name_short": item.get("Name", ""),
            "status": "Действующее",
            "director": "Не указано",
            "address": item.get("Address", ""),
            "country": "kz",
            "source": "data.egov.kz (tson)",
            "geoposition": item.get("Geoposition", "")
        })
    return normalized


async def search_all_egov(query: str) -> List[Dict]:
    """
    Комплексный поиск по всем доступным наборам данных data.egov.kz
    """
    import asyncio
    
    # Запускаем поиск параллельно по всем наборам
    results = await asyncio.gather(
        search_medical_orgs(query),
        search_pharmacies(query),
        search_notaries(query),
        search_tsons(query),
        return_exceptions=True
    )
    
    # Собираем все результаты
    all_results = []
    for result in results:
        if isinstance(result, list):
            all_results.extend(result)
    
    return all_results
