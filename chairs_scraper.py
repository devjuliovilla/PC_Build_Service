import argparse
import json
import os
import re
from bs4 import BeautifulSoup

from database import DDTechDB
from scraper.browser import BrowserManager
from utils.normalizer import clean_price, generate_component_id


SEARCH_URL = "https://ddtech.mx/buscar?search=silla%20gamer"


def extract_chair_specs(name):
    name_lower = name.lower()
    specs = {
        "tipo": "Silla Gamer",
        "marca": "Generico"
    }

    brands = ["noblechairs", "corsair", "razer", "xzeal", "thermaltake", "cougar", "yeyian"]
    for brand in brands:
        if brand in name_lower:
            specs["marca"] = brand.capitalize() if brand != "noblechairs" else "Noblechairs"
            break

    recline = re.search(r"reclinaci[oó]n\s*(\d+)", name_lower)
    if recline:
        specs["reclinacion_grados"] = int(recline.group(1))

    if "4d" in name_lower:
        specs["brazos"] = "4D"
    elif "3d" in name_lower:
        specs["brazos"] = "3D"

    if "cuero real" in name_lower:
        specs["material"] = "Cuero real"
    elif "cuero sint" in name_lower:
        specs["material"] = "Cuero sintetico"
    elif "hibrido" in name_lower:
        specs["material"] = "Hibrido premium"

    if "clase 4" in name_lower:
        specs["piston"] = "Clase 4"

    return specs


class DDTechGamingChairScraper:
    def __init__(self, browser_manager, db):
        self.browser_manager = browser_manager
        self.db = db

    def scrape(self):
        page = self.browser_manager.new_page()
        try:
            print("\n=== [INICIANDO SCRAPING DE SILLAS GAMER] ===")
            page.goto(SEARCH_URL, wait_until="networkidle", timeout=60000)
            self.browser_manager.human_delay(1500, 2500)
            self._scrape_search_pages(page)
        finally:
            page.close()

    def _scrape_search_pages(self, page):
        page_num = 1
        while True:
            print(f"[SCRAPING SILLAS] Extrayendo resultados de la pagina {page_num}...")
            page.wait_for_selector(".product, .product-item, .box-producto, .product-box", timeout=10000)
            html = page.content()
            soup = BeautifulSoup(html, "html.parser")
            products = soup.select(".product, .product-item, .box-producto, .product-box")
            print(f"[INFO] Encontrados {len(products)} elementos en buscador.")

            saved_count = 0
            for prod in products:
                try:
                    name_elem = prod.find(["h3", "h4", "h2", "a"], class_=lambda x: x and ("title" in x or "name" in x or "nombre" in x))
                    if not name_elem:
                        links = prod.find_all("a", href=True)
                        for link in links:
                            txt = link.get_text(strip=True)
                            if len(txt) > 15:
                                name_elem = link
                                break
                    if not name_elem:
                        continue

                    name = name_elem.get_text(strip=True)
                    name_lower = name.lower()
                    if "silla gamer" not in name_lower:
                        continue

                    url_elem = prod.find("a", href=True)
                    url = url_elem["href"] if url_elem else ""
                    if url and not url.startswith("http"):
                        url = f"https://ddtech.mx{url}"
                    if not url or "/producto/" not in url:
                        continue

                    price_elem = prod.find(class_=lambda x: x and ("price" in x or "precio" in x or "cost" in x))
                    if not price_elem:
                        price_text_match = re.search(r"\$\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?", prod.get_text())
                        price_str = price_text_match.group(0) if price_text_match else "$0"
                    else:
                        price_str = price_elem.get_text(strip=True)
                    price = clean_price(price_str)
                    if price <= 0:
                        continue

                    img_elem = prod.find("img")
                    image_url = ""
                    if img_elem:
                        image_url = img_elem.get("data-src") or img_elem.get("src") or img_elem.get("lazy-src") or ""
                        if image_url and not image_url.startswith("http"):
                            image_url = f"https://ddtech.mx{image_url}"

                    text = prod.get_text().lower()
                    in_stock = not ("agotado" in text or "sin stock" in text or "no disponible" in text)

                    chair_id = generate_component_id("Sillas Gamer", name, url)
                    specs = extract_chair_specs(name)
                    self.db.save_gaming_chair(chair_id, name, url, image_url, specs)
                    self.db.save_gaming_chair_price_record(chair_id, price, in_stock)
                    saved_count += 1
                except Exception:
                    continue

            print(f"[SCRAPING SILLAS] Guardadas {saved_count} sillas en esta pagina.")

            next_button = page.query_selector("a[rel='next'], a:has-text('Siguiente'), li.next a, a:has-text('»'), .pagination .next a")
            if next_button and next_button.is_visible() and next_button.is_enabled():
                try:
                    next_button.scroll_into_view_if_needed()
                    self.browser_manager.human_delay(500, 1000)
                    with page.expect_navigation(timeout=15000):
                        next_button.click()
                    page_num += 1
                    self.browser_manager.human_delay(1500, 2500)
                except Exception:
                    break
            else:
                break


def main():
    parser = argparse.ArgumentParser(description="Scraper de sillas gamer de DDTech")
    parser.add_argument("--headless", action="store_true", help="Ejecutar navegador sin interfaz")
    parser.add_argument("--output", default="data/ddtech_gaming_chairs.json", help="Ruta JSON de exportacion")
    args = parser.parse_args()

    db = DDTechDB()
    browser_mgr = BrowserManager(headless=args.headless)

    try:
        browser_mgr.start()
        scraper = DDTechGamingChairScraper(browser_mgr, db)
        scraper.scrape()

        chairs = db.get_latest_gaming_chairs(only_in_stock=False)
        output_dir = os.path.dirname(args.output)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(chairs, f, indent=2, ensure_ascii=False)

        print(f"[OK] Se exportaron {len(chairs)} sillas a: {args.output}")
    finally:
        browser_mgr.close()


if __name__ == "__main__":
    main()
