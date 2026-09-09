#!/usr/bin/env python3
"""
interfaz.py
===========
Atajo para levantar la interfaz gráfica del proyecto.

Arranca el servidor FastAPI (backend/api.py), que además sirve la
interfaz React ya compilada si existe la carpeta `frontend/dist`.

    python interfaz.py            # http://127.0.0.1:8000
    python interfaz.py --puerto 9000

Si prefieres trabajar sobre el frontend con recarga automática, usa en
su lugar dos terminales:

    Terminal 1:  python -m uvicorn backend.api:app --reload --port 8000
    Terminal 2:  cd frontend && npm run dev
"""

import argparse
import sys
import webbrowser
from pathlib import Path
from threading import Timer

RAIZ = Path(__file__).resolve().parent


def main() -> None:
    analizador = argparse.ArgumentParser(description="Interfaz web del banco distribuido.")
    analizador.add_argument("--puerto", type=int, default=8000, help="Puerto del servidor.")
    analizador.add_argument("--host", default="127.0.0.1", help="Dirección de escucha.")
    analizador.add_argument(
        "--sin-navegador", action="store_true", help="No abrir el navegador automáticamente."
    )
    argumentos = analizador.parse_args()

    try:
        import uvicorn
    except ImportError:
        print("Falta instalar las dependencias del backend:")
        print("    pip install -r backend/requirements.txt")
        sys.exit(1)

    if not (RAIZ / "frontend" / "dist").is_dir():
        print("[aviso] No se encontró 'frontend/dist'.")
        print("        Compila la interfaz con:  cd frontend && npm install && npm run build")
        print("        (o usa 'npm run dev' en paralelo para el modo desarrollo).")
        print()

    url = f"http://{argumentos.host}:{argumentos.puerto}"
    print(f"Interfaz disponible en {url}")

    if not argumentos.sin_navegador:
        Timer(1.5, lambda: webbrowser.open(url)).start()

    sys.path.insert(0, str(RAIZ))
    uvicorn.run("backend.api:app", host=argumentos.host, port=argumentos.puerto)


if __name__ == "__main__":
    main()
