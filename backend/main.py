import os
import shutil
from typing import Optional

import serial.tools.list_ports
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from machine_manager import MachineManager

app = FastAPI(title="GRBLDeck API", version="2.0.0")
manager = MachineManager()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Modèles ─────────────────────────────────────────────────────────────────

class MachineConfig(BaseModel):
    name: str
    type: str = "cnc"
    port: str = ""
    baudrate: int = 115200
    sim: bool = False


class CommandBody(BaseModel):
    command: str


class SettingBody(BaseModel):
    key: str
    value: str


# ─── WebSocket ───────────────────────────────────────────────────────────────

@app.websocket("/ws/{machine_id}")
async def websocket_endpoint(websocket: WebSocket, machine_id: str):
    machine = manager.get(machine_id)
    if not machine:
        await websocket.close(code=4004)
        return

    await websocket.accept()
    await machine.add_client(websocket)

    try:
        while True:
            # On maintient la connexion ouverte, on peut recevoir des messages
            data = await websocket.receive_json()
            # Commandes via WS (optionnel, pour la console rapide)
            if data.get("type") == "command":
                await machine.send_command(data["command"])
    except WebSocketDisconnect:
        machine.remove_client(websocket)
    except Exception:
        machine.remove_client(websocket)


# ─── Machines CRUD ───────────────────────────────────────────────────────────

@app.get("/machines")
def get_machines():
    return manager.list()


@app.post("/machines")
def create_machine(config: MachineConfig):
    m = manager.add(config.dict())
    return m.to_dict()


@app.put("/machines/{machine_id}")
def update_machine(machine_id: str, config: MachineConfig):
    m = manager.update(machine_id, config.dict())
    if not m:
        raise HTTPException(404, "Machine introuvable")
    return m.to_dict()


@app.delete("/machines/{machine_id}")
def delete_machine(machine_id: str):
    if not manager.delete(machine_id):
        raise HTTPException(404, "Machine introuvable")
    return {"ok": True}


# ─── Connexion ───────────────────────────────────────────────────────────────

@app.post("/machines/{machine_id}/connect")
async def connect(machine_id: str):
    m = manager.get(machine_id)
    if not m:
        raise HTTPException(404, "Machine introuvable")
    await m.connect()
    return {"ok": True}


@app.post("/machines/{machine_id}/disconnect")
async def disconnect(machine_id: str):
    m = manager.get(machine_id)
    if not m:
        raise HTTPException(404, "Machine introuvable")
    await m.disconnect()
    return {"ok": True}


# ─── Commandes ───────────────────────────────────────────────────────────────

@app.post("/machines/{machine_id}/command")
async def send_command(machine_id: str, body: CommandBody):
    m = manager.get(machine_id)
    if not m:
        raise HTTPException(404, "Machine introuvable")
    await m.send_command(body.command)
    return {"ok": True}


@app.post("/machines/{machine_id}/stop")
async def stop(machine_id: str):
    m = manager.get(machine_id)
    if not m:
        raise HTTPException(404, "Machine introuvable")
    await m.stop()
    return {"ok": True}


# ─── Exécution GCode ─────────────────────────────────────────────────────────

@app.post("/machines/{machine_id}/run/{filename}")
async def run_file(machine_id: str, filename: str):
    m = manager.get(machine_id)
    if not m:
        raise HTTPException(404, "Machine introuvable")
    path = manager.file_path(machine_id, filename)
    if not os.path.exists(path):
        raise HTTPException(404, "Fichier introuvable")
    await m.run_file(path, filename)
    return {"ok": True}


# ─── Fichiers ────────────────────────────────────────────────────────────────

@app.get("/machines/{machine_id}/files")
def list_files(machine_id: str):
    return manager.list_files(machine_id)


@app.post("/machines/{machine_id}/upload")
async def upload_file(machine_id: str, file: UploadFile = File(...)):
    m = manager.get(machine_id)
    if not m:
        raise HTTPException(404, "Machine introuvable")
    path = manager.file_path(machine_id, file.filename)
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"ok": True, "name": file.filename}


@app.get("/machines/{machine_id}/files/{filename}/content")
def file_content(machine_id: str, filename: str):
    path = manager.file_path(machine_id, filename)
    if not os.path.exists(path):
        raise HTTPException(404, "Fichier introuvable")
    with open(path, "r") as f:
        return {"content": f.read()}


@app.delete("/machines/{machine_id}/files/{filename}")
def delete_file(machine_id: str, filename: str):
    if not manager.delete_file(machine_id, filename):
        raise HTTPException(404, "Fichier introuvable")
    return {"ok": True}


# ─── Settings GRBL ───────────────────────────────────────────────────────────

@app.post("/machines/{machine_id}/settings/load")
async def load_settings(machine_id: str):
    m = manager.get(machine_id)
    if not m:
        raise HTTPException(404, "Machine introuvable")
    await m.load_settings()
    return {"ok": True}


@app.post("/machines/{machine_id}/settings")
async def send_setting(machine_id: str, body: SettingBody):
    m = manager.get(machine_id)
    if not m:
        raise HTTPException(404, "Machine introuvable")
    await m.send_setting(body.key, body.value)
    return {"ok": True}


# ─── Ports série ─────────────────────────────────────────────────────────────

@app.get("/ports")
def list_ports():
    ports = [p.device for p in serial.tools.list_ports.comports()]
    return ports


# ─── Caméras ─────────────────────────────────────────────────────────────────

@app.get("/cameras")
def list_cameras():
    # Retourne une liste de URLs de caméras configurées
    # Pour l'instant : vide, à configurer via settings
    return []
