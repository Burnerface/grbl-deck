import asyncio
import json
import re
import serial
import serial.tools.list_ports
from datetime import datetime
from typing import Optional, Set
from fastapi import WebSocket


class GrblMachine:
    def __init__(self, machine_id: str, config: dict):
        self.id = machine_id
        self.name = config.get("name", machine_id)
        self.type = config.get("type", "cnc")  # cnc | laser
        self.port = config.get("port", "")
        self.baudrate = config.get("baudrate", 115200)
        self.sim = config.get("sim", False)

        self.serial: Optional[serial.Serial] = None
        self.connected = False
        self.state = "Disconnected"
        self.position = {"x": 0.0, "y": 0.0, "z": 0.0}
        self.job = {"actif": False, "fichier": None, "progression": 0}
        self.settings = {}

        self._ws_clients: Set[WebSocket] = set()
        self._read_task: Optional[asyncio.Task] = None
        self._status_task: Optional[asyncio.Task] = None
        self._gcode_lines: list = []
        self._gcode_index: int = 0
        self._gcode_task: Optional[asyncio.Task] = None

    # ─── WebSocket clients ───────────────────────────────────────────────────

    async def add_client(self, ws: WebSocket):
        self._ws_clients.add(ws)
        # Envoyer état initial
        await self._send(ws, {"type": "status", "data": self._status_payload()})

    def remove_client(self, ws: WebSocket):
        self._ws_clients.discard(ws)

    async def _broadcast(self, message: dict):
        dead = set()
        for ws in self._ws_clients:
            try:
                await ws.send_json(message)
            except Exception:
                dead.add(ws)
        self._ws_clients -= dead

    async def _send(self, ws: WebSocket, message: dict):
        try:
            await ws.send_json(message)
        except Exception:
            pass

    # ─── Connexion ───────────────────────────────────────────────────────────

    async def connect(self):
        if self.connected:
            return
        if self.sim:
            from grbl_sim import GrblSim
            self._sim = GrblSim()
            self.connected = True
            self.state = "Idle"
            await self._broadcast({"type": "status", "data": self._status_payload()})
            await self._log("Simulateur connecté")
            self._status_task = asyncio.create_task(self._poll_status())
            return

        try:
            self.serial = serial.Serial(self.port, self.baudrate, timeout=1)
            await asyncio.sleep(2)  # attendre init GRBL
            self.serial.flushInput()
            self.connected = True
            self.state = "Idle"
            await self._broadcast({"type": "status", "data": self._status_payload()})
            await self._log(f"Connecté sur {self.port} @ {self.baudrate}")
            self._read_task = asyncio.create_task(self._read_serial())
            self._status_task = asyncio.create_task(self._poll_status())
        except Exception as e:
            await self._broadcast({"type": "error", "message": str(e)})
            raise

    async def disconnect(self):
        if self._gcode_task:
            self._gcode_task.cancel()
        if self._status_task:
            self._status_task.cancel()
        if self._read_task:
            self._read_task.cancel()
        if self.serial and self.serial.is_open:
            self.serial.close()
        self.serial = None
        self.connected = False
        self.state = "Disconnected"
        self.job = {"actif": False, "fichier": None, "progression": 0}
        await self._broadcast({"type": "status", "data": self._status_payload()})
        await self._log("Déconnecté")

    # ─── Commandes ───────────────────────────────────────────────────────────

    async def send_command(self, cmd: str):
        cmd = cmd.strip()
        if not cmd:
            return
        await self._log(f"> {cmd}")
        if self.sim:
            response = self._sim.process(cmd)
            await self._log(response)
            return
        if self.serial and self.serial.is_open:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: self.serial.write((cmd + "\n").encode()))

    async def stop(self):
        if self._gcode_task:
            self._gcode_task.cancel()
            self._gcode_task = None
        self.job = {"actif": False, "fichier": None, "progression": 0}
        await self.send_command("\x18")  # Soft reset GRBL
        await self._broadcast({"type": "status", "data": self._status_payload()})

    # ─── Exécution GCode ─────────────────────────────────────────────────────

    async def run_file(self, filepath: str, filename: str):
        if self.job["actif"]:
            raise Exception("Une tâche est déjà en cours")
        with open(filepath, "r") as f:
            lines = [l.strip() for l in f.readlines() if l.strip() and not l.startswith(";")]
        self._gcode_lines = lines
        self._gcode_index = 0
        self.job = {"actif": True, "fichier": filename, "progression": 0}
        await self._broadcast({"type": "status", "data": self._status_payload()})
        self._gcode_task = asyncio.create_task(self._execute_gcode())

    async def _execute_gcode(self):
        total = len(self._gcode_lines)
        try:
            for i, line in enumerate(self._gcode_lines):
                if not self.connected:
                    break
                await self.send_command(line)
                await asyncio.sleep(0.05)
                self.job["progression"] = int((i + 1) / total * 100)
                await self._broadcast({"type": "status", "data": self._status_payload()})
        except asyncio.CancelledError:
            pass
        finally:
            self.job = {"actif": False, "fichier": None, "progression": 0}
            await self._broadcast({"type": "status", "data": self._status_payload()})
            await self._log("Exécution terminée")

    # ─── Lecture série ───────────────────────────────────────────────────────

    async def _read_serial(self):
        loop = asyncio.get_event_loop()
        while self.connected and self.serial and self.serial.is_open:
            try:
                line = await loop.run_in_executor(None, self.serial.readline)
                line = line.decode("utf-8", errors="ignore").strip()
                if line:
                    self._parse_response(line)
                    await self._log(line)
            except Exception:
                await asyncio.sleep(0.1)

    async def _poll_status(self):
        while self.connected:
            await self.send_command("?")
            await asyncio.sleep(0.5)

    def _parse_response(self, line: str):
        # Parser status GRBL : <Idle|MPos:0.000,0.000,0.000|...>
        match = re.match(r"<(\w+)[|,].*MPos:([-\d.]+),([-\d.]+),([-\d.]+)", line)
        if match:
            self.state = match.group(1)
            self.position = {
                "x": float(match.group(2)),
                "y": float(match.group(3)),
                "z": float(match.group(4)),
            }

    # ─── Settings GRBL ───────────────────────────────────────────────────────

    async def load_settings(self):
        await self.send_command("$$")

    async def send_setting(self, key: str, value: str):
        await self.send_command(f"{key}={value}")

    # ─── Helpers ─────────────────────────────────────────────────────────────

    def _status_payload(self):
        return {
            "connected": self.connected,
            "state": self.state,
            "position": self.position,
            "job": self.job,
        }

    async def _log(self, message: str):
        entry = {
            "type": "log",
            "data": {
                "time": datetime.now().strftime("%H:%M:%S"),
                "message": message,
            }
        }
        await self._broadcast(entry)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "port": self.port,
            "baudrate": self.baudrate,
            "sim": self.sim,
            "connected": self.connected,
            "state": self.state,
        }
