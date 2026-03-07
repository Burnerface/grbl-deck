import json
import os
import uuid
from typing import Dict, Optional
from grbl_machine import GrblMachine

MACHINES_FILE = "data/machines.json"
FILES_DIR = "data/files"


class MachineManager:
    def __init__(self):
        self.machines: Dict[str, GrblMachine] = {}
        os.makedirs(FILES_DIR, exist_ok=True)
        self._load()

    # ─── Persistance ─────────────────────────────────────────────────────────

    def _load(self):
        if not os.path.exists(MACHINES_FILE):
            # Machine simulateur par défaut
            default = {
                "machine_1": {
                    "name": "Laser Simulateur",
                    "type": "laser",
                    "port": "",
                    "baudrate": 115200,
                    "sim": True,
                }
            }
            self._save_json(default)

        with open(MACHINES_FILE, "r") as f:
            data = json.load(f)

        for mid, config in data.items():
            self.machines[mid] = GrblMachine(mid, config)

    def _save(self):
        data = {}
        for mid, m in self.machines.items():
            data[mid] = {
                "name": m.name,
                "type": m.type,
                "port": m.port,
                "baudrate": m.baudrate,
                "sim": m.sim,
            }
        self._save_json(data)

    def _save_json(self, data: dict):
        os.makedirs(os.path.dirname(MACHINES_FILE), exist_ok=True)
        with open(MACHINES_FILE, "w") as f:
            json.dump(data, f, indent=2)

    # ─── CRUD machines ───────────────────────────────────────────────────────

    def list(self):
        return [m.to_dict() for m in self.machines.values()]

    def get(self, machine_id: str) -> Optional[GrblMachine]:
        return self.machines.get(machine_id)

    def add(self, config: dict) -> GrblMachine:
        mid = f"machine_{uuid.uuid4().hex[:8]}"
        machine = GrblMachine(mid, config)
        self.machines[mid] = machine
        self._save()
        return machine

    def update(self, machine_id: str, config: dict) -> Optional[GrblMachine]:
        m = self.machines.get(machine_id)
        if not m:
            return None
        m.name = config.get("name", m.name)
        m.type = config.get("type", m.type)
        m.port = config.get("port", m.port)
        m.baudrate = config.get("baudrate", m.baudrate)
        m.sim = config.get("sim", m.sim)
        self._save()
        return m

    def delete(self, machine_id: str) -> bool:
        if machine_id not in self.machines:
            return False
        del self.machines[machine_id]
        self._save()
        return True

    # ─── Fichiers GCode ──────────────────────────────────────────────────────

    def files_dir(self, machine_id: str) -> str:
        d = os.path.join(FILES_DIR, machine_id)
        os.makedirs(d, exist_ok=True)
        return d

    def list_files(self, machine_id: str) -> list:
        d = self.files_dir(machine_id)
        files = []
        for f in os.listdir(d):
            if f.endswith((".gcode", ".nc", ".gc", ".ngc", ".txt")):
                path = os.path.join(d, f)
                files.append({
                    "name": f,
                    "size": os.path.getsize(path),
                    "modified": os.path.getmtime(path),
                })
        return sorted(files, key=lambda x: x["modified"], reverse=True)

    def file_path(self, machine_id: str, filename: str) -> str:
        return os.path.join(self.files_dir(machine_id), filename)

    def delete_file(self, machine_id: str, filename: str) -> bool:
        path = self.file_path(machine_id, filename)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False
