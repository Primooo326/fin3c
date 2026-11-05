# =============================================================================
#  Punto de Entrada Principal — Sistema de Gestión de Finanzas Personales
#  Universidad ECCI — Facultad de Ingeniería — Equipo 3 Subequipo B
# =============================================================================

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    pass

import uvicorn


if __name__ == "__main__":
    strHost = os.getenv("APP_HOST", "0.0.0.0")
    intPort = int(os.getenv("APP_PORT", "8000"))
    print("=" * 72)
    print("  SISTEMA DE GESTIÓN DE FINANZAS PERSONALES — UNIVERSIDAD ECCI")
    print(f"  Interfaz Web Responsiva : http://localhost:{intPort}")
    print(f"  Documentación API REST  : http://localhost:{intPort}/docs")
    print("=" * 72)
    uvicorn.run("SERVICIO_WEB.app:app", host=strHost, port=intPort, reload=True)
