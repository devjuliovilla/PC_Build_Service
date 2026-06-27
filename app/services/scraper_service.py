import json
import logging
import os

from chairs_scraper import DDTechGamingChairScraper
from database import DDTechDB
from scraper.browser import BrowserManager
from scraper.parser import DDTechScraper


class ScraperService:
    def __init__(self, settings, job_service):
        self.settings = settings
        self.job_service = job_service
        self.logger = logging.getLogger("ddtech.scraper")

    def queue_update(self, fallback=False, test_run=False):
        import threading

        job = self.job_service.create_job("scraper.update")
        thread = threading.Thread(
            target=self._run_update,
            args=(job["jobId"], fallback, test_run),
            daemon=True,
        )
        thread.start()
        return job

    def queue_chairs_update(self):
        import threading

        job = self.job_service.create_job("scraper.chairs.update")
        thread = threading.Thread(
            target=self._run_chairs_update,
            args=(job["jobId"],),
            daemon=True,
        )
        thread.start()
        return job

    def _run_update(self, job_id, fallback, test_run):
        self.job_service.start_job(job_id)
        db = DDTechDB(self.settings.database_path)
        browser_mgr = BrowserManager(headless=self.settings.headless, timeout_ms=self.settings.playwright_timeout)
        before_count = db.get_statistics().get("total_componentes", 0)

        self.logger.info(
            "scraper_started",
            extra={"extra_data": {"jobId": job_id, "headless": self.settings.headless, "fallback": fallback, "testRun": test_run}},
        )

        try:
            browser_mgr.start()
            scraper = DDTechScraper(browser_mgr, db)

            if test_run:
                page = browser_mgr.new_page()
                try:
                    page.goto("https://ddtech.mx/productos/componentes/procesadores", wait_until="networkidle", timeout=self.settings.playwright_timeout)
                    browser_mgr.human_delay(1500, 2500)
                    scraper._scrape_product_list_pages(page, "Procesadores")
                finally:
                    page.close()
            elif fallback:
                scraper.scrape_categories_fallback()
            else:
                success = scraper.scrape_configurator()
                if not success:
                    scraper.scrape_categories_fallback()

            latest_components = db.get_latest_components(only_in_stock=True)
            export_dir = os.path.dirname(self.settings.export_json_path)
            if export_dir:
                os.makedirs(export_dir, exist_ok=True)
            with open(self.settings.export_json_path, "w", encoding="utf-8") as file_handle:
                json.dump(latest_components, file_handle, indent=2, ensure_ascii=False)

            after_stats = db.get_statistics()
            components_updated = max(after_stats.get("total_componentes", 0) - before_count, 0)
            self.job_service.complete_job(job_id, components_updated=components_updated)

            self.logger.info(
                "scraper_finished",
                extra={
                    "extra_data": {
                        "jobId": job_id,
                        "componentsUpdated": components_updated,
                        "componentsCount": after_stats.get("total_componentes", 0),
                        "categoriesCount": len(after_stats.get("categorias", {})),
                        "duration": self.job_service.get_job(job_id).get("duration"),
                    }
                },
            )
        except Exception:
            self.job_service.fail_job(job_id, "scraper execution failed")
            self.logger.exception("scraper_failed", extra={"extra_data": {"jobId": job_id}})
        finally:
            browser_mgr.close()

    def _run_chairs_update(self, job_id):
        self.job_service.start_job(job_id)
        db = DDTechDB(self.settings.database_path)
        browser_mgr = BrowserManager(headless=self.settings.headless, timeout_ms=self.settings.playwright_timeout)
        before_count = len(db.get_latest_gaming_chairs(only_in_stock=False))

        self.logger.info(
            "chairs_scraper_started",
            extra={"extra_data": {"jobId": job_id, "headless": self.settings.headless}},
        )

        try:
            browser_mgr.start()
            scraper = DDTechGamingChairScraper(browser_mgr, db)
            scraper.scrape()

            latest_chairs = db.get_latest_gaming_chairs(only_in_stock=False)
            export_dir = os.path.dirname(self.settings.export_chairs_json_path)
            if export_dir:
                os.makedirs(export_dir, exist_ok=True)
            with open(self.settings.export_chairs_json_path, "w", encoding="utf-8") as file_handle:
                json.dump(latest_chairs, file_handle, indent=2, ensure_ascii=False)

            chairs_updated = max(len(latest_chairs) - before_count, 0)
            self.job_service.complete_job(job_id, components_updated=chairs_updated)

            self.logger.info(
                "chairs_scraper_finished",
                extra={
                    "extra_data": {
                        "jobId": job_id,
                        "componentsUpdated": chairs_updated,
                        "chairsCount": len(latest_chairs),
                        "duration": self.job_service.get_job(job_id).get("duration"),
                    }
                },
            )
        except Exception:
            self.job_service.fail_job(job_id, "chairs scraper execution failed")
            self.logger.exception("chairs_scraper_failed", extra={"extra_data": {"jobId": job_id}})
        finally:
            browser_mgr.close()
