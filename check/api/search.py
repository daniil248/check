"""Vercel serverless — поиск. Всё в одном файле, без импортов."""
from http.server import BaseHTTPRequestHandler
import json
import asyncio
from urllib.parse import urlparse, parse_qs
import os

DEMO = {
    "250240010778": {
        "bin": "250240010778",
        "name": "ТОО «NorthPak Logistics»",
        "name_short": "NorthPak Logistics",
        "status": "Действующее",
        "address": "081100, Жамбылская обл., Шуский р-н, с. Толе би, ул. Гагарина, 44",
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


def search_demo(q: str):
    q = q.strip().lower()
    bin_clean = "".join(c for c in q if c.isdigit())
    out = []
    for b, c in DEMO.items():
        if bin_clean and b == bin_clean:
            out.append(c)
            break
        if q in c["name"].lower() or q in c["name_short"].lower():
            out.append(c)
    return out


async def search_os(q: str, country: str):
    key = os.environ.get("OPENSANCTIONS_API_KEY", "")
    if not key:
        return []
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                "https://api.opensanctions.org/search/default",
                params={"q": q, "schema": "Company", "limit": 5, "countries": country.lower()},
                headers={"Authorization": f"Apikey {key}"},
            )
            r.raise_for_status()
            data = r.json()
    except Exception:
        return []
    out = []
    for item in data.get("results", [])[:5]:
        p = item.get("properties", {})
        name = (p.get("name") or [item.get("caption", "-")])[0] if isinstance(p.get("name"), list) else p.get("name") or item.get("caption", "-")
        out.append({
            "bin": (p.get("registrationNumber") or p.get("innCode") or ["-"])[0] if isinstance(p.get("registrationNumber"), list) else p.get("registrationNumber") or "-",
            "name": name,
            "name_short": name[:80] if len(str(name)) > 80 else name,
            "status": "Проверено (OpenSanctions)",
            "address": "-",
            "director": "-",
            "registration_date": "-",
            "activity": "-",
            "source": "opensanctions",
        })
    return out


def run_search(q: str, country: str):
    if not q or len(q.strip()) < 2:
        return {"success": False, "error": "Слишком короткий запрос", "results": []}
    results = search_demo(q)
    os_res = asyncio.run(search_os(q, country))
    seen = {r.get("bin", "") for r in results}
    for r in os_res:
        if r.get("bin") not in seen:
            results.append(r)
            seen.add(r.get("bin", ""))
    return {"success": True, "query": q, "country": country, "count": len(results), "results": results}


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        q = (params.get("q") or params.get("search") or [""])[0].strip()
        country = (params.get("country") or ["kz"])[0].strip() or "kz"

        try:
            result = run_search(q, country)
            body = json.dumps(result, ensure_ascii=False).encode("utf-8")
            code = 200
        except Exception as e:
            body = json.dumps({"success": False, "error": str(e)}, ensure_ascii=False).encode("utf-8")
            code = 500

        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)
