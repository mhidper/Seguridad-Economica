from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import json
import os
from pathlib import Path

app = FastAPI()

# Directorio base
BASE_DIR = Path(__file__).parent

@app.get("/")
async def read_index():
    index_path = BASE_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return JSONResponse({"error": "index.html no encontrado. Ejecuta build_hf.py primero."}, status_code=404)

@app.get("/api/data")
async def get_data():
    data_path = BASE_DIR / "data.json"
    if data_path.exists():
        with open(data_path, "r", encoding="utf-8") as f:
            # Usamos JSONResponse para manejar el envío de datos estructurados
            return json.load(f)
    return JSONResponse({"error": "data.json no encontrado. Ejecuta build_hf.py primero."}, status_code=404)

# Si el dashboard carga otros assets locales (imágenes, fuentes, etc.)
# app.mount("/assets", StaticFiles(directory="assets"), name="assets")
