import random
import time
from playwright.sync_api import sync_playwright

class BrowserManager:
    def __init__(self, headless=False, timeout_ms=45000):
        """
        Administrador de navegación con Playwright.
        Soporta modo visible (headless=False) para mayor evasión de Cloudflare y visualización local.
        """
        self.headless = headless
        self.timeout_ms = timeout_ms
        self.playwright = None
        self.browser = None
        self.context = None

    def start(self):
        """Inicia el navegador y el contexto con configuraciones anti-bloqueo."""
        self.playwright = sync_playwright().start()
        
        # Opciones de lanzamiento
        launch_args = [
            "--disable-blink-features=AutomationControlled",
            "--start-maximized",
            "--disable-infobars"
        ]
        
        # Lanzar Chromium (el motor de Chrome/Edge)
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            args=launch_args
        )
        
        # User-Agent común y actualizado para simular un navegador real
        user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        
        # Configurar contexto de navegación imitando un dispositivo real
        self.context = self.browser.new_context(
            user_agent=user_agent,
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=1,
            is_mobile=False,
            has_touch=False,
            locale="es-MX",
            timezone_id="America/Mexico_City",
            extra_http_headers={
                "Accept-Language": "es-419,es;q=0.9,en;q=0.8",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Sec-Ch-Ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"Windows"',
                "Upgrade-Insecure-Requests": "1"
            }
        )
        
        # Script para inyectar y ocultar variables de automatización típicas de webdriver
        self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            window.chrome = {
                runtime: {}
            };
            Object.defineProperty(navigator, 'languages', {
                get: () => ['es-MX', 'es', 'en']
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
        """)
        
        return self.context

    def new_page(self):
        """Crea una nueva página dentro del contexto activo."""
        if not self.context:
            self.start()
        page = self.context.new_page()
        page.set_default_navigation_timeout(self.timeout_ms)
        page.set_default_timeout(self.timeout_ms)
        return page

    def human_delay(self, min_ms=500, max_ms=1500):
        """Genera un retraso aleatorio para imitar interacción humana."""
        delay = random.uniform(min_ms / 1000.0, max_ms / 1000.0)
        time.sleep(delay)

    def close(self):
        """Cierra de forma limpia todas las instancias abiertas del navegador."""
        try:
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
        except Exception as e:
            print(f"[ERROR] Error cerrando el navegador: {e}")
