class CatalogService:
    def __init__(self, db):
        self.db = db

    def get_status(self, scraper_status, version):
        stats = self.db.get_statistics()
        return {
            "components_count": stats.get("total_componentes", 0),
            "categories_count": len(stats.get("categorias", {})),
            "builds_count": stats.get("total_builds", 0),
            "last_update": stats.get("ultima_actualizacion"),
            "scraper_status": scraper_status,
            "version": version,
        }

    def list_categories(self):
        return self.db.list_categories()

    def list_components(self, category=None, query=None, only_in_stock=False, limit=250):
        return self.db.list_components(category=category, query=query, only_in_stock=only_in_stock, limit=limit)

    def get_component(self, component_id):
        return self.db.get_component(component_id)

    def get_latest_components(self, only_in_stock=False, limit=100):
        return self.db.get_latest_components_for_api(only_in_stock=only_in_stock, limit=limit)

    def get_price_history(self, component_id):
        return self.db.get_price_history_for_component(component_id)

    def list_gaming_chairs(self, query=None, only_in_stock=False, limit=250):
        return self.db.list_gaming_chairs(query=query, only_in_stock=only_in_stock, limit=limit)

    def get_gaming_chair(self, chair_id):
        return self.db.get_gaming_chair(chair_id)

    def get_latest_gaming_chairs(self, only_in_stock=False, limit=100):
        return self.db.get_latest_gaming_chairs_for_api(only_in_stock=only_in_stock, limit=limit)

    def get_gaming_chair_price_history(self, chair_id):
        return self.db.get_price_history_for_gaming_chair(chair_id)
