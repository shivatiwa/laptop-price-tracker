import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

OUTPUT_FILE = Path("data/products.json")


def scrape_amazon(playwright):
    """Scrape laptops from Amazon.in"""
    print("[AMAZON] Starting scrape...")
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    )
    page = context.new_page()

    try:
        page.goto("https://www.amazon.in/s?k=laptop", timeout=60000)
        page.wait_for_selector("div.s-main-slot", timeout=30000)
    except Exception as e:
        print(f"[AMAZON] ❌ Failed to load: {e}")
        browser.close()
        return []

    results = []
    items = page.query_selector_all("div.s-main-slot div[data-asin]")
    for item in items:
        title_el = item.query_selector("h2 span")
        price_el = item.query_selector("span.a-price-whole")
        if title_el and price_el:
            title = title_el.inner_text().strip()
            price = price_el.inner_text().replace(",", "").strip()
            if price.isdigit():
                results.append({
                    "site": "Amazon",
                    "title": title,
                    "price": int(price),
                })

    browser.close()
    print(f"[AMAZON] ✅ Found {len(results)} items")
    return results


def scrape_flipkart(playwright):
    """Scrape laptops from Flipkart.com"""
    print("[FLIPKART] Starting scrape...")
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    )
    page = context.new_page()

    try:
        page.goto("https://www.flipkart.com/search?q=laptop", timeout=60000)
        page.wait_for_selector("div._1YokD2", timeout=30000)
    except Exception as e:
        print(f"[FLIPKART] ❌ Failed to load: {e}")
        browser.close()
        return []

    results = []
    items = page.query_selector_all("div._1AtVbE")
    for item in items:
        title_el = item.query_selector("div._4rR01T")
        price_el = item.query_selector("div._30jeq3")
        if title_el and price_el:
            title = title_el.inner_text().strip()
            price_text = price_el.inner_text().replace("₹", "").replace(",", "").strip()
            if price_text.isdigit():
                results.append({
                    "site": "Flipkart",
                    "title": title,
                    "price": int(price_text),
                })

    browser.close()
    print(f"[FLIPKART] ✅ Found {len(results)} items")
    return results


def safe_scrape(scraper_func, playwright, retries=1):
    """Run a scraper with retry support"""
    for attempt in range(retries + 1):
        results = scraper_func(playwright)
        if results:
            return results
        if attempt < retries:
            print(f"[{scraper_func.__name__.upper()}] Retrying in 5s...")
            time.sleep(5)
    return []


def main():
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    all_results = []

    with sync_playwright() as p:
        amazon_results = safe_scrape(scrape_amazon, p, retries=1)
        flipkart_results = safe_scrape(scrape_flipkart, p, retries=1)
        all_results = amazon_results + flipkart_results

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    print(f"✅ Scraping complete. Saved {len(all_results)} products to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
