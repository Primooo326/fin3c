# =============================================================================
#  Módulo dependencias: Tokens de sesión firmados HMAC-SHA256 y autenticación
#  Capa: SERVICIO_WEB
# =============================================================================

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Optional

from fastapi import Cookie, Depends, Header, HTTPException, status

from LOGICA.GestorFinanzas import GestorFinanzas

STR_CLAVE_SECRETA = os.getenv(
    "APP_SECRET_KEY", "ecci-pya-2026-subequipo3b-clave-secreta-segura-sha256"
)
INT_DURACION_SESION_SEG = 60 * 60 * 24 * 7  # 7 días


def generarTokenSesion(strDocumento: str) -> str:
    """Genera un token firmado HMAC-SHA256 compacto con expiración."""
    carga = {
        "sub": strDocumento,
        "exp": int(time.time()) + INT_DURACION_SESION_SEG,
    }
    bytesPayload = base64.urlsafe_b64encode(
        json.dumps(carga, separators=(",", ":")).encode("utf-8")
    )
    firma = hmac.new(
        STR_CLAVE_SECRETA.encode("utf-8"),
        bytesPayload,
        hashlib.sha256,
    ).hexdigest()
    return f"{bytesPayload.decode('ascii')}.{firma}"


def validarTokenSesion(strToken: str) -> Optional[str]:
    """Valida firma y expiración del token; devuelve strDocumento o None."""
    if not strToken or "." not in strToken:
        return None
    try:
        partePayload, firmaRecibida = strToken.split(".", 1)
        firmaEsperada = hmac.new(
            STR_CLAVE_SECRETA.encode("utf-8"),
            partePayload.encode("ascii"),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(firmaRecibida, firmaEsperada):
            return None
        datos = json.loads(
            base64.urlsafe_b64decode(partePayload.encode("ascii")).decode("utf-8")
        )
        if int(datos.get("exp", 0)) < int(time.time()):
            return None
        return str(datos.get("sub", ""))
    except Exception:
        return None


def obtenerGestor() -> GestorFinanzas:
    gestor = GestorFinanzas.getInstancia()
    if not gestor.asegurarCargaInicial():
        estado = gestor.getEstadoPersistencia()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=estado["strDetalle"],
        )
    return gestor


def obtenerPersonaActual(
    authorization: Optional[str] = Header(default=None),
    finanzas_token: Optional[str] = Cookie(default=None),
    gestor: GestorFinanzas = Depends(obtenerGestor),
):
    """Extrae el usuario autenticado desde Header Bearer o Cookie HttpOnly."""
    strToken = None
    if authorization and authorization.lower().startswith("bearer "):
        strToken = authorization[7:].strip()
    elif finanzas_token:
        strToken = finanzas_token

    strDocumento = validarTokenSesion(strToken or "")
    if not strDocumento:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesión expirada o no autenticada. Inicie sesión nuevamente.",
        )

    persona = gestor.buscarPersona(strDocumento)
    if persona is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El usuario de la sesión ya no existe en el sistema.",
        )
    return persona
