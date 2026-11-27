#!/usr/bin/env python3
"""Fetch the latest press releases from the Egyptian Ministry of Finance site
(mof.gov.eg) and write news.json. Titles and dates are copied as published.
If the site cannot be reached, the existing news.json is left untouched."""
import json, re, sys, html, time, datetime, urllib.request

BASE = "https://mof.gov.eg"
UA = {"User-Agent": "Mozilla/5.0 (compatible; site-news-sync)"}
LIMIT = 8

def get(url):
    for i in range(3):
        try:
            req = urllib.request.Request(url, headers=UA)
            return urllib.request.urlopen(req, timeout=25).read().decode("utf-8", "replace")
        except Exception as e:
            err = e
            time.sleep(3)
    raise err

def clean(s):
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip()

def scrape(lang):
    page = get(f"{BASE}/{lang}/media/press-releases")
    ids = []
    for m in re.finditer(rf'href="(/{lang}/media/press-releases/news-(\d+))"', page):
        if m.group(1) not in [i[0] for i in ids]:
            ids.append((m.group(1), int(m.group(2))))
    ids.sort(key=lambda x: -x[1])
    items = []
    for path, _ in ids[:LIMIT]:
        art = get(BASE + path)
        h1 = re.search(r'<meta property="og:title" content="([^"]*)"', art)
        d = re.search(r'<time[^>]*dateTime="(\d{4}-\d{2}-\d{2})"', art)
        if not (h1 and d):
            continue
        items.append({"title": clean(h1.group(1)), "date": d.group(1), "url": BASE + path})
    items.sort(key=lambda x: x["date"], reverse=True)
    return items

def main():
    out = {"source": "Ministry of Finance, Arab Republic of Egypt (mof.gov.eg)",
           "source_url": {"ar": BASE + "/ar/media/press-releases", "en": BASE + "/en/media/press-releases"},
           "updated": datetime.datetime.utcnow().strftime("%Y-%m-%d"), "ar": [], "en": []}
    try:
        out["ar"] = scrape("ar")
    except Exception as e:
        print("ar failed:", e)
    try:
        out["en"] = scrape("en")
    except Exception as e:
        print("en failed:", e)
    if not out["ar"] and not out["en"]:
        print("nothing fetched; keeping previous file"); return 0
    json.dump(out, open("news.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("ok", len(out["ar"]), len(out["en"]))
    return 0

if __name__ == "__main__":
    sys.exit(main())
