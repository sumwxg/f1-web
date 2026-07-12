"""APEX F1 Live backend for a self-hosted server (Tencent Cloud / any VPS)."""
from __future__ import annotations

import json
import os
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / ".cache"
CACHE.mkdir(exist_ok=True)
HEADERS = {"User-Agent": "APEX-F1-Live/1.0 (self-hosted dashboard)"}


def cached(url: str, key: str, seconds: int = 300) -> bytes:
    path = CACHE / key
    if path.exists() and time.time() - path.stat().st_mtime < seconds:
        return path.read_bytes()
    request = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=15) as remote:
        content = remote.read()
    path.write_bytes(content)
    return content


def jolpica(year: str, endpoint: str, key: str) -> dict:
    separator = "" if endpoint.startswith(".") else "/"
    url = f"https://api.jolpi.ca/ergast/f1/{year}{separator}{endpoint}"
    return json.loads(cached(url, key).decode("utf-8"))


def rss_articles(query: str, key: str) -> list[dict]:
    url = "https://news.google.com/rss/search?" + urllib.parse.urlencode({
        "q": query + " Formula 1", "hl": "zh-CN", "gl": "CN", "ceid": "CN:zh-Hans"
    })
    root = ET.fromstring(cached(url, key, 1800))
    result = []
    for item in root.findall("./channel/item")[:8]:
        source = item.find("source")
        result.append({
            "title": item.findtext("title", "未命名报道"),
            "url": item.findtext("link", ""),
            "published": item.findtext("pubDate", ""),
            "source": source.text if source is not None else "Google News",
        })
    return result


class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    def json(self, data: dict, status: int = 200):
        raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        year = params.get("year", ["2026"])[0]
        if not re.fullmatch(r"20\d{2}", year):
            return self.json({"error": "无效赛季。"}, 400)
        try:
            if parsed.path == "/api/season":
                calendar, results, drivers, teams = (
                    jolpica(year, ".json?limit=100", f"{year}-calendar.json"),
                    jolpica(year, "results.json?limit=1000", f"{year}-results.json"),
                    jolpica(year, "driverstandings.json?limit=100", f"{year}-drivers.json"),
                    jolpica(year, "constructorstandings.json?limit=100", f"{year}-teams.json"),
                )
                return self.json({
                    "year": year, "updatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "source": "Jolpica (Ergast-compatible public API)",
                    "calendar": calendar["MRData"]["RaceTable"].get("Races", []),
                    "results": results["MRData"]["RaceTable"].get("Races", []),
                    "driverStandings": drivers["MRData"]["StandingsTable"].get("StandingsLists", [{}])[0].get("DriverStandings", []),
                    "constructorStandings": teams["MRData"]["StandingsTable"].get("StandingsLists", [{}])[0].get("ConstructorStandings", []),
                })
            if parsed.path == "/api/race":
                round_no = params.get("round", [""])[0]
                if not re.fullmatch(r"\d{1,2}", round_no):
                    return self.json({"error": "无效比赛编号。"}, 400)
                raw = jolpica(year, f"{round_no}/results.json?limit=100", f"{year}-race-{round_no}.json")
                race = raw["MRData"]["RaceTable"].get("Races", [None])[0]
                name = race.get("raceName", "Formula 1") if race else "Formula 1"
                try:
                    articles = rss_articles(f"{year} {name}", f"{year}-news-{round_no}.xml")
                except Exception:
                    articles = []
                return self.json({"year": year, "updatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "source": "Jolpica + Google News RSS", "race": race, "articles": articles})
        except Exception as error:
            return self.json({"error": "公开数据源暂不可用。", "detail": str(error)}, 502)
        return super().do_GET()

    def log_message(self, format, *args):
        print("[APEX] " + format % args)


if __name__ == "__main__":
    os.chdir(ROOT)
    port = int(os.environ.get("PORT", "8080"))
    print(f"APEX F1 Live listening on 0.0.0.0:{port}")
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
