import argparse
import json
import os
import sys

from app.api.app import create_app
from app.config import settings
from database import DDTechDB
from scraper.browser import BrowserManager
from scraper.parser import DDTechScraper


app = create_app()

def main():
    parser = argparse.ArgumentParser(
        description="DDTech Web Scraper & PC Component Parser para Modelos de IA"
    )
    parser.add_argument(
        "--fallback",
        action="store_true",
        help="Ignorar el configurador y hacer scraping directo de categorías principales"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Ejecutar el navegador en segundo plano (sin interfaz gráfica)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=settings.export_json_path,
        help="Ruta del archivo JSON donde se exportará la información lista para la IA"
    )
    parser.add_argument(
        "--test-run",
        action="store_true",
        help="Modo de prueba rápido: Solo scrapea una categoría rápida para verificar funcionamiento"
    )
    
    args = parser.parse_args()
    
    print("====================================================")
    print("      DDTECH PC COMPONENT WEB SCRAPER & PARSER      ")
    print("====================================================")
    print(f"Plataforma detectada: Windows (Win32 / PowerShell)")
    print(f"Modo invisible (headless): {args.headless}")
    print(f"Modo rápido de prueba: {args.test_run}")
    print(f"Ruta de salida JSON: {args.output}")
    print("====================================================\n")
    
    # 1. Inicializar la Base de Datos SQLite
    print("[PASO 1] Inicializando base de datos SQLite local...")
    db = DDTechDB(settings.database_path)
    print("[OK] Base de datos lista.")
    
    # 2. Inicializar el Administrador del Navegador
    print("\n[PASO 2] Levantando instancia segura de Playwright...")
    browser_mgr = BrowserManager(headless=args.headless, timeout_ms=settings.playwright_timeout)
    
    try:
        browser_mgr.start()
        print("[OK] Navegador listo.")
        
        # 3. Lanzar Scraper
        scraper = DDTechScraper(browser_mgr, db)
        
        if args.test_run:
            print("\n[MODO PRUEBA] Ejecutando scraping de prueba rápido en 'Procesadores'...")
            # En modo prueba, usamos el scraper directo en una sola categoría para agilizar y validar el flujo
            page = browser_mgr.new_page()
            test_url = "https://ddtech.mx/productos/componentes/procesadores"
            try:
                page.goto(test_url, wait_until="networkidle", timeout=30000)
                browser_mgr.human_delay(1500, 2500)
                # Ejecutar listado (solo la primera página para test)
                scraper._scrape_product_list_pages(page, "Procesadores")
                print("[OK] Prueba rápida completada exitosamente.")
            except Exception as e:
                print(f"[ERROR] Falló la prueba rápida: {e}")
            finally:
                page.close()
                
        elif args.fallback:
            print("\n[ESTRATEGIA] Iniciando scraping por categorías directas...")
            scraper.scrape_categories_fallback()
        else:
            print("\n[ESTRATEGIA] Iniciando scraping desde el configurador...")
            success = scraper.scrape_configurator()
            if not success:
                print("\n[AVISO] El scraping del configurador no pudo completarse. Ejecutando fallback de categorías directas...")
                scraper.scrape_categories_fallback()
                
        # 4. Exportar los datos más recientes a JSON para consumo de IA
        print("\n[PASO 4] Exportando últimos componentes en stock a JSON para la IA...")
        latest_components = db.get_latest_components(only_in_stock=True)
        
        # Crear carpeta de salida si no existe
        output_dir = os.path.dirname(args.output)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(latest_components, f, indent=2, ensure_ascii=False)
            
        print(f"[OK] Se exportaron {len(latest_components)} componentes a: {args.output}")
        
        # 5. Mostrar estadísticas globales
        stats = db.get_statistics()
        print("\n================ STATS DE LA DB ================")
        print(f"Total componentes únicos guardados: {stats['total_componentes']}")
        print(f"Total registros históricos de precios: {stats['total_registros_precios']}")
        print("Distribución por categorías de componentes:")
        for cat, count in stats["categorias"].items():
            print(f"  - {cat}: {count} artículos")
        print("================================================")
        
    except Exception as e:
        print(f"\n[CRITICAL ERROR] Ocurrió un error general en el orquestador: {e}")
        sys.exit(1)
    finally:
        print("\n[PASO 5] Cerrando navegador y guardando estado...")
        browser_mgr.close()
        print("[PROCESO FINALIZADO] Scraper cerrado correctamente.")

if __name__ == "__main__":
    main()
