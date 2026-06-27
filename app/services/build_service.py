class BuildService:
    def __init__(self, db):
        self.db = db

    def list_builds(self):
        return self.db.list_builds()

    def create_build(self, name, description=None):
        return self.db.create_build(name=name, description=description)

    def get_build(self, build_id):
        return self.db.get_build(build_id)

    def update_build(self, build_id, name=None, description=None, is_active=None):
        return self.db.update_build(build_id, name=name, description=description, is_active=is_active)

    def delete_build(self, build_id):
        return self.db.delete_build(build_id)

    def save_slot(self, build_id, slot, component_id, is_locked=False, notes=None):
        if not self.db.get_build(build_id) or not self.db.get_component(component_id):
            return None
        return self.db.save_build_slot(build_id, slot, component_id, is_locked=is_locked, notes=notes)

    def update_slot(self, build_id, slot, component_id, is_locked=None, notes=None):
        if not self.db.get_build(build_id) or not self.db.get_component(component_id):
            return None
        current = self.db.get_slot(build_id, slot)
        locked = current["is_locked"] if current and is_locked is None else bool(is_locked)
        return self.db.save_build_slot(build_id, slot, component_id, is_locked=locked, notes=notes)

    def delete_slot(self, build_id, slot):
        return self.db.remove_build_slot(build_id, slot)

    def save_decision(self, build_id, slot, reason):
        target_slot = self.db.get_slot(build_id, slot)
        if not target_slot:
            return None
        return self.db.save_build_decision(target_slot["id"], reason)

    def list_decisions(self, build_id, slot=None):
        return self.db.get_build_decisions(build_id, slot=slot)

    def create_snapshot(self, build_id):
        return self.db.save_build_snapshot(build_id)

    def compare_build(self, build_id):
        return self.db.compare_build_against_latest(build_id)

    def total(self, build_id):
        return self.db.calculate_build_total(build_id)
