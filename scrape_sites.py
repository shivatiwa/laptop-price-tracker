import json, re, time, urllib.parse
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

OUTPUT = Path("data/products.json")
OUTPUT.parent.mkdir(exist_ok=True)

GPU_KEYWORDS = ["4060", "4070"]
CPU_KEYWORDS = ["intel", "i5", "i7"]

def parse_price(text):
    if not text:
        return None
    s = re.sub(r"[^\d]", "", text)
    try:
        return float(s)
    except:
        return None

def matches_keywords(text):
    t = text.lower()
    return any(g in t for g in GPU_KEYWORDS) and any(c in t for c in CPU_KEYWORDS)

def scrape_amazon(p):
    query = "laptop " + " ".join(GPU_KEYWORDS)
    url = f"https://www.amazon.in/s?k={urllib.parse.quote_plus(query)}"
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(url, timeout=30000)
    page.wait_for_selector("div.s-main-slot", timeout=10000)
    html = page.content()
    browser.close()
    soup = BeautifulSoup(html, "html.parser")
    data = []
    for div in soup.select("div.s-main-slot div.s-result-item"):
        title_tag = div.select_one("h2 a span")
        if not title_tag: continue
        title = title_tag.get_text(strip=True)
        if not matches_keywords(title): continue
        price_tag = div.select_one("span.a-price-whole")
        price = parse_price(price_tag.get_text()) if price_tag else None
        mrp_tag = div.select_one("span.a-price.a-text-price span.a-offscreen")
        mrp = parse_price(mrp_tag.get_text()) if mrp_tag else price
        link_tag = div.select_one("h2 a")
        link = "https://www.amazon.in" + link_tag["href"]
        if price:
            disc = round(((mrp - price) / mrp) * 100, 2) if mrp and mrp > price else 0
            data.append({
                "site": "amazon",
                "title": title,
                "price": price,
                "mrp": mrp,
                "discount": disc,
                "link": link
            })
    return data

def scrape_flipkart(p):
    query = "laptop " + " ".join(GPU_KEYWORDS)
    url = f"https://www.flipkart.com/search?q={urllib.parse.quote_plus(query)}"
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(url, timeout=30000)
    page.wait_for_timeout(2000)
    html = page.content()
    browser.close()
    soup = BeautifulSoup(html, "html.parser")
    data = []
    for item in soup.select("div._1AtVbE"):
        title_tag = item.select_one("div._4rR01T") or item.select_one("a.s1Q9rs")
        price_tag = item.select_one("div._30jeq3")
        if not title_tag or not price_tag: continue
        title = title_tag.get_text(strip=True)
        if not matches_keywords(title): continue
        price = parse_price(price_tag.get_text())
        mrp_tag = item.select_one("div._3I9_wc")
        mrp = parse_price(mrp_tag.get_text()) if mrp_tag else price
        link_tag = item.select_one("a")
        link = "https://www.flipkart.com" + link_tag['href'] if link_tag else url
        if price:
            disc = round(((mrp - price) / mrp) * 100, 2) if mrp and mrp > price else 0
            data.append({
                "site": "flipkart",
                "title": title,
                "price": price,
                "mrp": mrp,
                "discount": disc,
                "link": link
            })
    return data

def main():
    with sync_playwright() as p:
        results = scrape_amazon(p) + scrape_flipkart(p)
    results.sort(key=lambda x: x["discount"], reverse=True)
    OUTPUT.write_text(json.dumps({
        "last_updated": int(time.time()),
        "products": results
    }, indent=2))
    print(f"Saved {len(results)} products to {OUTPUT}")

if __name__ == "__main__":
    main()
