# GRBLDeck v2

Interface web multi-machines pour contrôleurs GRBL (CNC / Laser).

## Stack
- **Frontend** : Vue 3 + Vite + Pinia + Vuetify 3
- **Backend** : FastAPI + pyserial + WebSocket
- **Deploy** : Docker Compose

## Lancement

```bash
docker compose up -d --build
```

Frontend : http://localhost:5173  
Backend API : http://localhost:8086

## Dev local (sans Docker)

**Backend :**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8086
```

**Frontend :**
```bash
cd frontend
npm install
npm run dev
```

## Architecture
- Chaque machine a son propre WebSocket `/ws/{machine_id}`
- Le backend pousse les mises à jour (status, logs, position) en temps réel
- Zéro polling HTTP — toutes les mises à jour passent par WebSocket
