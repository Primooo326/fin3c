# =============================================================================
#  Módulo Seguridad: Cifrado de contraseñas con PBKDF2-HMAC-SHA256 (RNF-01)
#  Capa: LOGICA
# =============================================================================

import hashlib
import hmac
import secrets


class Seguridad:

    STR_ALGORITMO = "pbkdf2_sha256"
    INT_ITERACIONES = 260000

    @staticmethod
    def cifrarPassword(strPassword):
        """Genera un hash seguro con sal aleatoria mediante PBKDF2-HMAC-SHA256."""
        strSalt = secrets.token_hex(16)
        bytesHash = hashlib.pbkdf2_hmac(
            "sha256",
            str(strPassword).encode("utf-8"),
            strSalt.encode("utf-8"),
            Seguridad.INT_ITERACIONES,
        )
        return f"{Seguridad.STR_ALGORITMO}${Seguridad.INT_ITERACIONES}${strSalt}${bytesHash.hex()}"

    @staticmethod
    def verificarPassword(strPasswordPlano, strPasswordHash):
        """Verifica en tiempo constante si la contraseña coincide con el hash almacenado."""
        if not strPasswordHash or "$" not in strPasswordHash:
            return False
        try:
            partes = strPasswordHash.split("$")
            if len(partes) != 4 or partes[0] != Seguridad.STR_ALGORITMO:
                return False
            intIteraciones = int(partes[1])
            strSalt = partes[2]
            strHashGuardado = partes[3]
            bytesCalculado = hashlib.pbkdf2_hmac(
                "sha256",
                str(strPasswordPlano).encode("utf-8"),
                strSalt.encode("utf-8"),
                intIteraciones,
            )
            return hmac.compare_digest(bytesCalculado.hex(), strHashGuardado)
        except (ValueError, TypeError):
            return False
