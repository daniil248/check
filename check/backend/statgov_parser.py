"""
Парсинг stat.gov.kz (Бюро национальной статистики РК) для поиска по БИН.
ВРЕМЕННОЕ РЕШЕНИЕ - работает без API ключа.
"""
import httpx
from typing import Optional, List, Dict
import re


async def search_statgov_by_bin(bin_id: str) -> Optional[Dict]:
    """
    Поиск компании по БИН на stat.gov.kz
    Парсит публичную страницу поиска.
    """
    if not bin_id.strip().isdigit() or len(bin_id.strip()) != 12:
        return None
    
    # URL публичного поиска
    url = f"https://stat.gov.kz/ru/juridical/by/bin/"
    
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            # Делаем запрос с БИН
            response = await client.post(
                url,
                data={"bin": bin_id.strip()},
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "User-Agent": "Mozilla/5.0"
                }
            )
            
            if response.status_code != 200:
                return None
            
            html = response.text
            
            # Парсим HTML (упрощенный вариант)
            company_data = parse_statgov_html(html, bin_id.strip())
            return company_data
    
    except Exception as e:
        print(f"Ошибка при парсинге stat.gov.kz: {e}")
        return None


def parse_statgov_html(html: str, bin_id: str) -> Optional[Dict]:
    """
    Парсит HTML ответ от stat.gov.kz
    ВНИМАНИЕ: Это временное решение, структура может измениться
    """
    # Ищем базовую информацию
    # Нужно проверить реальную структуру HTML
    
    if "не найден" in html.lower() or "not found" in html.lower():
        return None
    
    # Примерный парсинг (нужно уточнить по реальному HTML)
    name_match = re.search(r'<td[^>]*>Наименование[^<]*</td>\s*<td[^>]*>([^<]+)</td>', html, re.IGNORECASE)
    address_match = re.search(r'<td[^>]*>Адрес[^<]*</td>\s*<td[^>]*>([^<]+)</td>', html, re.IGNORECASE)
    status_match = re.search(r'<td[^>]*>Статус[^<]*</td>\s*<td[^>]*>([^<]+)</td>', html, re.IGNORECASE)
    director_match = re.search(r'<td[^>]*>Руководитель[^<]*</td>\s*<td[^>]*>([^<]+)</td>', html, re.IGNORECASE)
    
    if not name_match:
        return None
    
    return {
        "bin": bin_id,
        "name": name_match.group(1).strip() if name_match else "",
        "name_short": name_match.group(1).strip()[:80] if name_match else "",
        "status": status_match.group(1).strip() if status_match else "Неизвестно",
        "director": director_match.group(1).strip() if director_match else "",
        "address": address_match.group(1).strip() if address_match else "",
        "country": "kz",
        "source": "stat.gov.kz (парсинг)",
    }


async def search_companies_statgov(query: str) -> List[Dict]:
    """
    Поиск компаний на stat.gov.kz
    Работает только по точному БИН (12 цифр)
    """
    query_clean = "".join(c for c in query if c.isdigit())
    
    if len(query_clean) != 12:
        return []
    
    result = await search_statgov_by_bin(query_clean)
    return [result] if result else []
