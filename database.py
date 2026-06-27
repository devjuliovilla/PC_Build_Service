import json
import os
import sqlite3


def _default_database_path():
    configured_path = os.getenv("DATABASE_PATH")
    if configured_path:
        return configured_path

    return os.path.join("data", "ddtech.db")


class DDTechDB:
    def __init__(self, db_path=None):
        self.db_path = db_path or _default_database_path()
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        self.init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def init_db(self):
        """Inicializa las tablas de la base de datos si no existen."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Tabla de Componentes (Datos Técnicos Estáticos)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS components (
                    id TEXT PRIMARY KEY,
                    category TEXT NOT NULL,
                    name TEXT NOT NULL,
                    url TEXT UNIQUE NOT NULL,
                    image_url TEXT,
                    specs_json TEXT,
                    last_scraped TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabla de Historial de Precios (Datos Variables)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS price_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    component_id TEXT NOT NULL,
                    price REAL NOT NULL,
                    in_stock INTEGER NOT NULL,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (component_id) REFERENCES components(id)
                )
            """)
            
            # Crear índices para acelerar búsquedas
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_price_history_comp ON price_history(component_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_price_history_date ON price_history(scraped_at)")

            # Tabla de Sillas Gamer (entidad separada del configurador de PC)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS gaming_chairs (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    url TEXT UNIQUE NOT NULL,
                    image_url TEXT,
                    specs_json TEXT,
                    last_scraped TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS gaming_chair_price_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chair_id TEXT NOT NULL,
                    price REAL NOT NULL,
                    in_stock INTEGER NOT NULL,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (chair_id) REFERENCES gaming_chairs(id)
                )
            """)

            cursor.execute("CREATE INDEX IF NOT EXISTS idx_chair_price_history_comp ON gaming_chair_price_history(chair_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_chair_price_history_date ON gaming_chair_price_history(scraped_at)")

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS builds (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active INTEGER NOT NULL DEFAULT 0
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS build_slots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    build_id INTEGER NOT NULL,
                    slot TEXT NOT NULL,
                    component_id TEXT NOT NULL,
                    is_locked INTEGER NOT NULL DEFAULT 0,
                    notes TEXT,
                    selected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (build_id) REFERENCES builds(id) ON DELETE CASCADE,
                    FOREIGN KEY (component_id) REFERENCES components(id),
                    UNIQUE(build_id, slot)
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS build_decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    build_slot_id INTEGER NOT NULL,
                    reason TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (build_slot_id) REFERENCES build_slots(id) ON DELETE CASCADE
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS build_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    build_id INTEGER NOT NULL,
                    component_id TEXT NOT NULL,
                    price REAL NOT NULL,
                    in_stock INTEGER NOT NULL,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (build_id) REFERENCES builds(id) ON DELETE CASCADE,
                    FOREIGN KEY (component_id) REFERENCES components(id)
                )
                """
            )

            cursor.execute("CREATE INDEX IF NOT EXISTS idx_builds_active ON builds(is_active)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_build_slots_build ON build_slots(build_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_build_slots_component ON build_slots(component_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_build_decisions_slot ON build_decisions(build_slot_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_build_snapshots_build ON build_snapshots(build_id)")
            
            conn.commit()

    def save_gaming_chair(self, chair_id, name, url, image_url, specs_dict):
        specs_json = json.dumps(specs_dict, ensure_ascii=False)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO gaming_chairs (id, name, url, image_url, specs_json, last_scraped)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(id) DO UPDATE SET
                    name=excluded.name,
                    image_url=excluded.image_url,
                    specs_json=excluded.specs_json,
                    last_scraped=CURRENT_TIMESTAMP
            """, (chair_id, name, url, image_url, specs_json))
            conn.commit()

    def save_gaming_chair_price_record(self, chair_id, price, in_stock):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO gaming_chair_price_history (chair_id, price, in_stock, scraped_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (chair_id, price, 1 if in_stock else 0))
            conn.commit()

    def get_latest_gaming_chairs(self, only_in_stock=True):
        query = """
            with latest_prices as (
                select
                    chair_id,
                    price,
                    in_stock,
                    scraped_at,
                    row_number() over (partition by chair_id order by scraped_at desc) as rn
                from gaming_chair_price_history
            )
            select
                gc.id,
                gc.name,
                gc.url,
                gc.image_url,
                gc.specs_json,
                lp.price,
                lp.in_stock,
                lp.scraped_at
            from gaming_chairs gc
            join latest_prices lp on gc.id = lp.chair_id
            where lp.rn = 1
        """
        if only_in_stock:
            query += " and lp.in_stock = 1"

        chairs = []
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            for row in cursor.fetchall():
                chairs.append({
                    "id": row["id"],
                    "nombre": row["name"],
                    "url": row["url"],
                    "imagen_url": row["image_url"],
                    "precio": row["price"],
                    "en_stock": bool(row["in_stock"]),
                    "fecha_precio": row["scraped_at"],
                    "especificaciones": json.loads(row["specs_json"]) if row["specs_json"] else {}
                })
        return chairs

    def save_component(self, comp_id, category, name, url, image_url, specs_dict):
        """
        Inserta o actualiza un componente. 
        Retorna True si fue insertado/actualizado correctamente.
        """
        specs_json = json.dumps(specs_dict, ensure_ascii=False)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO components (id, category, name, url, image_url, specs_json, last_scraped)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(id) DO UPDATE SET
                    category=excluded.category,
                    name=excluded.name,
                    image_url=excluded.image_url,
                    specs_json=excluded.specs_json,
                    last_scraped=CURRENT_TIMESTAMP
            """, (comp_id, category, name, url, image_url, specs_json))
            conn.commit()

    def save_price_record(self, comp_id, price, in_stock):
        """Inserta un nuevo registro de precio para un componente."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Convertimos in_stock a entero (1 o 0)
            in_stock_int = 1 if in_stock else 0
            cursor.execute("""
                INSERT INTO price_history (component_id, price, in_stock, scraped_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (comp_id, price, in_stock_int))
            conn.commit()

    def get_latest_components(self, only_in_stock=True):
        """
        Obtiene los componentes más recientes con su último precio registrado.
        """
        query = """
            with latest_prices as (
                select 
                    component_id,
                    price,
                    in_stock,
                    scraped_at,
                    row_number() over (partition by component_id order by scraped_at desc) as rn
                from price_history
            )
            select 
                c.id,
                c.category,
                c.name,
                c.url,
                c.image_url,
                c.specs_json,
                lp.price,
                lp.in_stock,
                lp.scraped_at
            from components c
            join latest_prices lp on c.id = lp.component_id
            where lp.rn = 1
        """
        if only_in_stock:
            query += " and lp.in_stock = 1"
            
        components = []
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            for row in cursor.fetchall():
                comp_data = {
                    "id": row["id"],
                    "categoria": row["category"],
                    "nombre": row["name"],
                    "url": row["url"],
                    "imagen_url": row["image_url"],
                    "precio": row["price"],
                    "en_stock": bool(row["in_stock"]),
                    "fecha_precio": row["scraped_at"],
                    "especificaciones": json.loads(row["specs_json"]) if row["specs_json"] else {}
                }
                components.append(comp_data)
        return components

    def get_price_history_for_component(self, comp_id):
        """Retorna el historial de precios para un componente ordenado por fecha."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT price, in_stock, scraped_at 
                FROM price_history 
                WHERE component_id = ? 
                ORDER BY scraped_at ASC
            """, (comp_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_statistics(self):
        """Retorna estadísticas generales de la base de datos."""
        stats = {}
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM components")
            stats["total_componentes"] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM price_history")
            stats["total_registros_precios"] = cursor.fetchone()[0]
            
            cursor.execute("SELECT category, COUNT(*) FROM components GROUP BY category")
            stats["categorias"] = {row[0]: row[1] for row in cursor.fetchall()}

            cursor.execute("SELECT COUNT(*) FROM builds")
            stats["total_builds"] = cursor.fetchone()[0]

            cursor.execute(
                "SELECT MAX(scraped_at) FROM (SELECT scraped_at FROM price_history UNION ALL SELECT scraped_at FROM gaming_chair_price_history)"
            )
            stats["ultima_actualizacion"] = cursor.fetchone()[0]
            
        return stats

    def list_categories(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT category, COUNT(*) AS total FROM components GROUP BY category ORDER BY category ASC")
            return [dict(row) for row in cursor.fetchall()]

    def list_components(self, category=None, query=None, only_in_stock=False, limit=250):
        sql = """
            WITH latest_prices AS (
                SELECT
                    component_id,
                    price,
                    in_stock,
                    scraped_at,
                    ROW_NUMBER() OVER (PARTITION BY component_id ORDER BY scraped_at DESC) AS rn
                FROM price_history
            )
            SELECT
                c.id,
                c.category,
                c.name,
                c.url,
                c.image_url,
                c.specs_json,
                c.last_scraped,
                lp.price,
                lp.in_stock,
                lp.scraped_at
            FROM components c
            LEFT JOIN latest_prices lp ON c.id = lp.component_id AND lp.rn = 1
            WHERE 1 = 1
        """
        params = []

        if category:
            sql += " AND c.category = ?"
            params.append(category)

        if query:
            sql += " AND (c.name LIKE ? OR c.category LIKE ? OR c.specs_json LIKE ?)"
            like_query = f"%{query}%"
            params.extend([like_query, like_query, like_query])

        if only_in_stock:
            sql += " AND COALESCE(lp.in_stock, 0) = 1"

        sql += " ORDER BY COALESCE(lp.scraped_at, c.last_scraped) DESC, c.name ASC LIMIT ?"
        params.append(limit)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            return [self._map_component_row(row) for row in cursor.fetchall()]

    def get_component(self, component_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                WITH latest_prices AS (
                    SELECT
                        component_id,
                        price,
                        in_stock,
                        scraped_at,
                        ROW_NUMBER() OVER (PARTITION BY component_id ORDER BY scraped_at DESC) AS rn
                    FROM price_history
                )
                SELECT
                    c.id,
                    c.category,
                    c.name,
                    c.url,
                    c.image_url,
                    c.specs_json,
                    c.last_scraped,
                    lp.price,
                    lp.in_stock,
                    lp.scraped_at
                FROM components c
                LEFT JOIN latest_prices lp ON c.id = lp.component_id AND lp.rn = 1
                WHERE c.id = ?
                """,
                (component_id,),
            )
            row = cursor.fetchone()
            return self._map_component_row(row) if row else None

    def get_latest_components_for_api(self, only_in_stock=False, limit=100):
        return self.list_components(only_in_stock=only_in_stock, limit=limit)

    def create_build(self, name, description=None):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO builds (name, description) VALUES (?, ?)",
                (name, description),
            )
            conn.commit()
            return self.get_build(cursor.lastrowid)

    def update_build(self, build_id, name=None, description=None, is_active=None):
        build = self.get_build(build_id)
        if not build:
            return None

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE builds
                SET name = ?,
                    description = ?,
                    is_active = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    name if name is not None else build["name"],
                    description if description is not None else build["description"],
                    int(is_active) if is_active is not None else int(build["is_active"]),
                    build_id,
                ),
            )
            if is_active:
                cursor.execute("UPDATE builds SET is_active = 0 WHERE id != ?", (build_id,))
            conn.commit()

        return self.get_build(build_id)

    def delete_build(self, build_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM builds WHERE id = ?", (build_id,))
            conn.commit()
            return cursor.rowcount > 0

    def list_builds(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM builds ORDER BY updated_at DESC, id DESC")
            return [self._map_build_row(row) for row in cursor.fetchall()]

    def get_build(self, build_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM builds WHERE id = ?", (build_id,))
            row = cursor.fetchone()
            if not row:
                return None
            build = self._map_build_row(row)
            build["slots"] = self.get_build_slots(build_id)
            return build

    def set_active_build(self, build_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE builds SET is_active = 0")
            cursor.execute(
                "UPDATE builds SET is_active = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (build_id,),
            )
            conn.commit()
        return self.get_build(build_id)

    def get_active_build(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM builds WHERE is_active = 1 ORDER BY updated_at DESC LIMIT 1")
            row = cursor.fetchone()
            return self.get_build(row["id"]) if row else None

    def save_build_slot(self, build_id, slot, component_id, is_locked=False, notes=None):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO build_slots (build_id, slot, component_id, is_locked, notes, selected_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(build_id, slot) DO UPDATE SET
                    component_id = excluded.component_id,
                    is_locked = excluded.is_locked,
                    notes = excluded.notes,
                    selected_at = CURRENT_TIMESTAMP
                """,
                (build_id, slot, component_id, 1 if is_locked else 0, notes),
            )
            cursor.execute("UPDATE builds SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (build_id,))
            conn.commit()
        return self.get_slot(build_id, slot)

    def remove_build_slot(self, build_id, slot):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM build_slots WHERE build_id = ? AND slot = ?", (build_id, slot))
            cursor.execute("UPDATE builds SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (build_id,))
            conn.commit()
            return cursor.rowcount > 0

    def get_build_slots(self, build_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT bs.*, c.name AS component_name, c.category AS component_category
                FROM build_slots bs
                LEFT JOIN components c ON c.id = bs.component_id
                WHERE bs.build_id = ?
                ORDER BY bs.slot ASC
                """,
                (build_id,),
            )
            return [self._map_slot_row(row) for row in cursor.fetchall()]

    def get_slot(self, build_id, slot):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT bs.*, c.name AS component_name, c.category AS component_category
                FROM build_slots bs
                LEFT JOIN components c ON c.id = bs.component_id
                WHERE bs.build_id = ? AND bs.slot = ?
                """,
                (build_id, slot),
            )
            row = cursor.fetchone()
            return self._map_slot_row(row) if row else None

    def lock_slot(self, build_id, slot):
        return self._update_slot_lock(build_id, slot, True)

    def unlock_slot(self, build_id, slot):
        return self._update_slot_lock(build_id, slot, False)

    def save_build_decision(self, build_slot_id, reason):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO build_decisions (build_slot_id, reason) VALUES (?, ?)",
                (build_slot_id, reason),
            )
            conn.commit()
            cursor.execute(
                "SELECT * FROM build_decisions WHERE id = ?",
                (cursor.lastrowid,),
            )
            return dict(cursor.fetchone())

    def get_build_decisions(self, build_id, slot=None):
        sql = """
            SELECT bd.*, bs.slot, bs.build_id
            FROM build_decisions bd
            JOIN build_slots bs ON bs.id = bd.build_slot_id
            WHERE bs.build_id = ?
        """
        params = [build_id]
        if slot:
            sql += " AND bs.slot = ?"
            params.append(slot)
        sql += " ORDER BY bd.created_at DESC, bd.id DESC"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]

    def save_build_snapshot(self, build_id):
        slots = self.get_build_slots(build_id)
        snapshot_rows = []
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for slot in slots:
                cursor.execute(
                    """
                    SELECT price, in_stock, scraped_at
                    FROM price_history
                    WHERE component_id = ?
                    ORDER BY scraped_at DESC
                    LIMIT 1
                    """,
                    (slot["component_id"],),
                )
                latest = cursor.fetchone()
                if not latest:
                    continue
                cursor.execute(
                    """
                    INSERT INTO build_snapshots (build_id, component_id, price, in_stock, scraped_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        build_id,
                        slot["component_id"],
                        latest["price"],
                        latest["in_stock"],
                        latest["scraped_at"],
                    ),
                )
                snapshot_rows.append(
                    {
                        "component_id": slot["component_id"],
                        "price": latest["price"],
                        "in_stock": bool(latest["in_stock"]),
                        "scraped_at": latest["scraped_at"],
                    }
                )
            conn.commit()
        return snapshot_rows

    def compare_build_against_latest(self, build_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT component_id, price, in_stock, scraped_at FROM build_snapshots WHERE build_id = ? ORDER BY id DESC",
                (build_id,),
            )
            snapshot_rows = cursor.fetchall()

            snapshot_by_component = {}
            for row in snapshot_rows:
                snapshot_by_component.setdefault(row["component_id"], dict(row))

        comparison = []
        for slot in self.get_build_slots(build_id):
            latest_component = self.get_component(slot["component_id"])
            snapshot = snapshot_by_component.get(slot["component_id"])
            comparison.append(
                {
                    "slot": slot["slot"],
                    "component_id": slot["component_id"],
                    "component_name": slot["component_name"],
                    "snapshot": snapshot,
                    "latest": {
                        "price": latest_component["price"] if latest_component else None,
                        "in_stock": latest_component["in_stock"] if latest_component else None,
                        "scraped_at": latest_component["scraped_at"] if latest_component else None,
                    },
                    "price_delta": (
                        (latest_component["price"] - snapshot["price"])
                        if latest_component and snapshot and latest_component["price"] is not None
                        else None
                    ),
                }
            )
        return comparison

    def calculate_build_total(self, build_id):
        total = 0.0
        items = []
        for slot in self.get_build_slots(build_id):
            component = self.get_component(slot["component_id"])
            price = component["price"] if component and component["price"] is not None else 0.0
            total += price
            items.append(
                {
                    "slot": slot["slot"],
                    "component_id": slot["component_id"],
                    "component_name": slot["component_name"],
                    "price": price,
                    "in_stock": component["in_stock"] if component else None,
                }
            )
        return {"build_id": build_id, "total": total, "currency": "MXN", "items": items}

    def _update_slot_lock(self, build_id, slot, locked):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE build_slots SET is_locked = ? WHERE build_id = ? AND slot = ?",
                (1 if locked else 0, build_id, slot),
            )
            cursor.execute("UPDATE builds SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (build_id,))
            conn.commit()
        return self.get_slot(build_id, slot)

    def _map_component_row(self, row):
        if not row:
            return None
        return {
            "id": row["id"],
            "category": row["category"],
            "name": row["name"],
            "url": row["url"],
            "image_url": row["image_url"],
            "specifications": json.loads(row["specs_json"]) if row["specs_json"] else {},
            "price": row["price"],
            "in_stock": bool(row["in_stock"]) if row["in_stock"] is not None else None,
            "scraped_at": row["scraped_at"],
            "last_scraped": row["last_scraped"],
        }

    def _map_build_row(self, row):
        return {
            "id": row["id"],
            "name": row["name"],
            "description": row["description"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "is_active": bool(row["is_active"]),
        }

    def _map_slot_row(self, row):
        return {
            "id": row["id"],
            "build_id": row["build_id"],
            "slot": row["slot"],
            "component_id": row["component_id"],
            "component_name": row["component_name"],
            "component_category": row["component_category"],
            "is_locked": bool(row["is_locked"]),
            "notes": row["notes"],
            "selected_at": row["selected_at"],
        }
