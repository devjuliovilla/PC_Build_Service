import re
import traceback
from bs4 import BeautifulSoup
from utils.normalizer import clean_price, generate_component_id, extract_specifications

class DDTechScraper:
    def __init__(self, browser_manager, db):
        """
        Scraper para DDTech.
        browser_manager: Instancia de BrowserManager.
        db: Instancia de DDTechDB para guardar datos sobre la marcha.
        """
        self.browser_manager = browser_manager
        self.db = db

    def scrape_configurator(self):
        """
        Intenta hacer scraping navegando el configurador interactivo oficial.
        URL: https://ddtech.mx/configurador
        """
        print("\n=== [INICIANDO SCRAPING DEL CONFIGURADOR] ===")
        page = self.browser_manager.new_page()
        
        try:
            url_configurator = "https://ddtech.mx/configurador"
            print(f"[NAVEGACIÓN] Cargando configurador: {url_configurator}")
            
            # Navegar y esperar que la red se estabilice
            page.goto(url_configurator, wait_until="networkidle", timeout=45000)
            self.browser_manager.human_delay(1500, 3000)
            
            print(f"[INFO] Título de página cargada: '{page.title()}'")

            body_text = page.locator("body").inner_text().lower()
            if "404" in body_text or "página no encontrada" in body_text or "pagina no encontrada" in body_text:
                print("[WARNING] El configurador actual devuelve 404. Se usará el fallback por categorías directas.")
                return False
            
            # Tomar captura de pantalla de depuración por si acaso
            # page.screenshot(path="data/configurador_inicio.png")
            
            # Buscar botones del configurador para agregar componentes.
            # En DDTech, las filas del configurador suelen tener botones con texto 'Agregar' o '+ Agregar' o links con íconos de suma.
            # Vamos a identificar los botones en la página.
            buttons = page.query_selector_all("a:has-text('Agregar'), button:has-text('Agregar'), .btn-agregar, a:has-text('Seleccionar')")
            print(f"[INFO] Se encontraron {len(buttons)} ranuras o botones de agregar en el configurador.")
            
            if len(buttons) == 0:
                print("[WARNING] No se detectaron botones de agregar directos. Intentaremos modo alternativo por categorías directas.")
                return False
                
            # Extraer los enlaces de cada ranura para no perder el contexto al navegar
            # Usualmente los botones de DDTech llevan a un link como "/configurador/seleccion/categoria/X"
            step_urls = []
            for btn in buttons:
                href = btn.get_attribute("href")
                text = btn.inner_text().strip()
                # También podemos ver la fila para saber qué categoría es
                # Tratamos de buscar el texto de la categoría cerca del botón
                parent = btn.evaluate_handle("el => el.parentElement.parentElement")
                category_name = "Desconocida"
                if parent:
                    # Buscar textos típicos de categorías en la fila
                    parent_text = parent.as_element().inner_text()
                    for cat in ["procesador", "tarjeta madre", "memoria ram", "tarjeta de video", "fuente de poder", "gabinete", "disco duro", "ssd", "enfriamiento"]:
                        if cat in parent_text.lower():
                            category_name = cat.capitalize()
                            break
                
                if href and "/configurador/" in href:
                    full_url = href if href.startswith("http") else f"https://ddtech.mx{href}"
                    step_urls.append((category_name, full_url))
            
            print(f"[INFO] Enlaces de categorías detectados: {len(step_urls)}")
            for cat, url in step_urls:
                print(f"  - {cat}: {url}")
                
            if not step_urls:
                # Si están en botones JS sin href, los simularemos haciendo clic
                print("[INFO] Los botones no contienen enlaces directos, se procederá interactuando por clics.")
                self._scrape_by_clicking_steps(page)
            else:
                # Si obtuvimos URLs directas para cada paso de selección, navegamos a ellas una por una (más rápido y estable)
                for category, step_url in step_urls:
                    self._scrape_step_url(page, category, step_url)
                    
            return True
            
        except Exception as e:
            print(f"[ERROR] Error durante el scraping del configurador: {e}")
            traceback.print_exc()
            return False
        finally:
            page.close()

    def _scrape_step_url(self, page, category, url):
        """Navega a un paso del configurador directamente y extrae sus productos."""
        print(f"\n--- [SCRAPING CATEGORÍA: {category}] ---")
        try:
            page.goto(url, wait_until="networkidle", timeout=30000)
            self.browser_manager.human_delay(1000, 2000)
            
            # Extraer productos de este listado con paginación
            self._scrape_product_list_pages(page, category)
        except Exception as e:
            print(f"[ERROR] Error procesando paso del configurador ({category}): {e}")

    def _scrape_by_clicking_steps(self, page):
        """
        Navega haciendo clics en los botones 'Agregar' secuencialmente si no hay URLs directas.
        """
        # Obtenemos la cantidad de botones frescos
        buttons = page.query_selector_all("a:has-text('Agregar'), button:has-text('Agregar'), .btn-agregar")
        
        for i in range(len(buttons)):
            # Volver a consultar botones para evitar elementos descolgados (stale)
            buttons = page.query_selector_all("a:has-text('Agregar'), button:has-text('Agregar'), .btn-agregar")
            if i >= len(buttons):
                break
                
            btn = buttons[i]
            
            # Obtener nombre de la categoría aproximada
            parent_text = btn.evaluate("el => el.parentElement.parentElement.innerText")
            category = "Componente"
            for cat in ["procesador", "tarjeta madre", "memoria ram", "tarjeta de video", "fuente de poder", "gabinete", "disco duro", "ssd", "enfriamiento"]:
                if cat in parent_text.lower():
                    category = cat.capitalize()
                    break
            
            print(f"\n--- [ABRIENDO RANURA: {category}] ---")
            
            try:
                btn.click()
                page.wait_for_load_state("networkidle", timeout=15000)
                self.browser_manager.human_delay(1000, 2000)
                
                # Extraer lista
                self._scrape_product_list_pages(page, category)
                
                # Regresar al configurador para el siguiente paso
                # Buscamos un botón de regresar o simplemente recargamos el configurador
                back_btn = page.query_selector("a:has-text('Regresar'), button:has-text('Regresar'), a:has-text('Atrás')")
                if back_btn:
                    back_btn.click()
                    page.wait_for_load_state("networkidle", timeout=15000)
                else:
                    page.goto("https://ddtech.mx/configurador", wait_until="networkidle", timeout=20000)
                    
                self.browser_manager.human_delay(1000, 1500)
                
            except Exception as e:
                print(f"[ERROR] Error interactuando con paso {i}: {e}")
                # Forzar recarga de seguridad para no perder el ciclo
                page.goto("https://ddtech.mx/configurador", wait_until="networkidle")

    def scrape_categories_fallback(self):
        """
        Método fallback que hace scraping navegando directamente a las categorías principales
        de DDTech. Esto asegura que obtengamos datos aún si el configurador cambia su interfaz.
        """
        print("\n=== [INICIANDO SCRAPING DE CATEGORÍAS DIRECTAS (FALLBACK)] ===")
        
        categories_urls = {
            "Procesadores": "https://ddtech.mx/productos/componentes/procesadores",
            "Tarjetas Madre": "https://ddtech.mx/productos/componentes/tarjetas-madre",
            "Memorias RAM": "https://ddtech.mx/productos/componentes/memoria-ram",
            "Tarjetas de Video": "https://ddtech.mx/productos/componentes/tarjetas-de-video",
            "Fuentes de Poder": "https://ddtech.mx/productos/componentes/fuente-de-alimentacion",
            "Gabinetes": "https://ddtech.mx/productos/componentes/gabinetes",
            "Almacenamiento (SSD)": "https://ddtech.mx/productos/componentes/unidades-ssd",
            "Almacenamiento (HDD)": "https://ddtech.mx/productos/componentes/discos-duros-internos",
            "Enfriamiento": "https://ddtech.mx/productos/componentes/enf-liquidos-aio",
            "Disipadores CPU": "https://ddtech.mx/productos/componentes/disipador-cpu-aire",
            "Ventilación": "https://ddtech.mx/productos/componentes/ventilacion"
        }
        
        page = self.browser_manager.new_page()
        
        try:
            for category, url in categories_urls.items():
                print(f"\n--- [NAVEGANDO A CATEGORÍA: {category}] ---")
                print(f"URL: {url}")
                try:
                    page.goto(url, wait_until="networkidle", timeout=35000)
                    self.browser_manager.human_delay(1500, 2500)

                    final_url = page.url.rstrip("/")
                    if final_url == "https://ddtech.mx":
                        print(f"[WARNING] La categoría '{category}' redirigió al home. URL inválida o ruta cambiada: {url}")
                        continue

                    # Evita scrapear páginas ajenas si DDTech vuelve a redirigir slugs viejos a otra categoría.
                    if "/productos/componentes/" not in final_url:
                        print(f"[WARNING] La categoría '{category}' terminó fuera de componentes: {final_url}")
                        continue
                    
                    # Extraer productos con paginación
                    self._scrape_product_list_pages(page, category)
                except Exception as e:
                    print(f"[ERROR] Error scrapeando categoría {category}: {e}")
        finally:
            page.close()

    def _scrape_product_list_pages(self, page, category):
        """
        Extrae productos de la página de listado actual y gestiona la paginación.
        """
        page_num = 1
        while True:
            print(f"[SCRAPING] Extrayendo productos de la página {page_num}...")
            
            # Esperar a que los componentes del producto estén visibles
            # DDTech suele usar clases como '.product-item', '.item', '.product', o '.box-producto'
            page.wait_for_selector(".product, .product-item, .box-producto, .item, .product-box", timeout=8000)
            
            # Obtener el contenido HTML renderizado para parsear con BeautifulSoup (es más rápido para extraer texto en lote)
            html = page.content()
            soup = BeautifulSoup(html, "html.parser")
            
            # Intentar encontrar los contenedores de productos con selectores comunes
            products = soup.select(".product, .product-item, .box-producto, .product-box")
            if not products:
                # Si fallan los selectores específicos, buscar cualquier tarjeta o div que parezca un producto
                products = soup.find_all("div", class_=lambda x: x and ("product" in x or "item" in x or "box" in x))
                
            print(f"[INFO] Encontrados {len(products)} elementos en el listado de la página {page_num}.")
            
            saved_count = 0
            for prod in products:
                try:
                    # Extraer Nombre del Producto
                    # Buscamos enlaces o headers dentro del contenedor del producto
                    name_elem = prod.find(["h3", "h4", "h2", "a"], class_=lambda x: x and ("title" in x or "name" in x or "nombre" in x))
                    if not name_elem:
                        # Fallback a buscar el primer 'a' que contenga texto descriptivo largo o tenga clase relacionada
                        name_elem = prod.find("a", href=True)
                        if name_elem and len(name_elem.get_text(strip=True)) < 10:
                            # Si es muy corto, tal vez no es el título
                            name_elem = None
                            
                    if not name_elem:
                        # Si aún no lo encuentra, buscar cualquier elemento con texto
                        all_links = prod.find_all("a", href=True)
                        for link in all_links:
                            link_text = link.get_text(strip=True)
                            if len(link_text) > 15:
                                name_elem = link
                                break
                    
                    if not name_elem:
                        continue
                        
                    name = name_elem.get_text(strip=True)
                    
                    # Extraer URL del Producto
                    # Usualmente el elemento del nombre o alguna imagen tiene el href
                    url_elem = prod.find("a", href=True)
                    url = url_elem["href"] if url_elem else ""
                    if url and not url.startswith("http"):
                        url = f"https://ddtech.mx{url}"
                        
                    if not url or "/producto/" not in url:
                        # Si no contiene '/producto/', tal vez no es una ficha de producto válida
                        continue
                        
                    # Extraer Precio
                    # Buscamos clases que contengan 'price', 'precio', 'amount'
                    price_elem = prod.find(class_=lambda x: x and ("price" in x or "precio" in x or "cost" in x))
                    if not price_elem:
                        # Fallback a buscar texto con formato de moneda mexicano (ej. $3,450.00 o $ 3,450)
                        price_text_match = re.search(r"\$\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?", prod.get_text())
                        price_str = price_text_match.group(0) if price_text_match else "$0"
                    else:
                        price_str = price_elem.get_text(strip=True)
                        
                    price = clean_price(price_str)
                    
                    # Extraer Imagen
                    img_elem = prod.find("img")
                    image_url = ""
                    if img_elem:
                        # A veces las imágenes usan lazy loading ('data-src', 'lazy-src', 'src')
                        image_url = img_elem.get("data-src") or img_elem.get("src") or img_elem.get("lazy-src") or ""
                        if image_url and not image_url.startswith("http"):
                            image_url = f"https://ddtech.mx{image_url}"
                    
                    # Stock (en el configurador de DDTech todos los componentes listados suelen estar en stock)
                    # Si no, buscamos textos como 'Agotado', 'Sin stock', 'Añadir al carrito'
                    in_stock = True
                    prod_text = prod.get_text().lower()
                    if "agotado" in prod_text or "sin stock" in prod_text or "no disponible" in prod_text:
                        in_stock = False
                        
                    # Filtrar precios vacíos o nulos que a veces son basura del layout
                    if price <= 0:
                        continue

                    # Generar ID único
                    comp_id = generate_component_id(category, name, url)
                    
                    # Extraer especificaciones técnicas normalizadas para la IA
                    specs = extract_specifications(category, name)
                    
                    # Guardar en SQLite
                    self.db.save_component(
                        comp_id=comp_id,
                        category=category,
                        name=name,
                        url=url,
                        image_url=image_url,
                        specs_dict=specs
                    )
                    
                    # Guardar precio en el historial
                    self.db.save_price_record(
                        comp_id=comp_id,
                        price=price,
                        in_stock=in_stock
                    )
                    
                    saved_count += 1
                    
                except Exception as ex:
                    # Log ligero por cada error individual para no tumbar todo el scraper
                    # print(f"[DEBUG_ERROR] Error procesando un producto: {ex}")
                    continue
                    
            print(f"[SCRAPING] Procesados y guardados {saved_count} productos de esta página.")
            
            # --- MANEJO DE PAGINACIÓN ---
            # Buscar el botón 'Siguiente' o '>' en la paginación.
            # Selectores comunes de paginación de DDTech
            next_button = page.query_selector("a[rel='next'], a:has-text('Siguiente'), li.next a, a:has-text('»'), .pagination .next a")
            
            # Verificar si existe y es visible/clicable
            if next_button and next_button.is_visible() and next_button.is_enabled():
                print("[PAGINACIÓN] Botón Siguiente encontrado. Pasando a la siguiente página...")
                try:
                    # Hacer scroll hasta el botón para asegurar el clic
                    next_button.scroll_into_view_if_needed()
                    self.browser_manager.human_delay(500, 1000)
                    
                    # Hacer clic y esperar a que cambie o cargue la página
                    # Para mayor robustez, podemos esperar a que ocurra una petición de red
                    with page.expect_navigation(timeout=15000):
                        next_button.click()
                        
                    page_num += 1
                    self.browser_manager.human_delay(1500, 3000)
                except Exception as e:
                    print(f"[PAGINACIÓN] No se pudo hacer clic en Siguiente o no cargó (asumiendo fin de paginación): {e}")
                    break
            else:
                print("[PAGINACIÓN] No hay más páginas disponibles para esta categoría.")
                break
