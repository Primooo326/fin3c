# =============================================================================
#  Clase CuentaBancaria: Fuente de dinero (Ahorros, Corriente o Efectivo) (RF-02)
#  Modelado Orientado a Objetos (Matriz de Diseño UML - Universidad ECCI)
#  Capa: LOGICA
# =============================================================================


class CuentaBancaria:

    STR_TIPO_AHORROS = "Ahorros"
    STR_TIPO_CORRIENTE = "Corriente"
    STR_TIPO_EFECTIVO = "Efectivo"
    LISTA_TIPOS_CUENTA = [STR_TIPO_AHORROS, STR_TIPO_CORRIENTE, STR_TIPO_EFECTIVO]

    # ---- Constructor ---------------------------------------------------------
    def __init__(self, strNumeroCuenta, strEntidadBancaria, strTipoCuenta, dblSaldoActual=0.0):
        self.__strNumeroCuenta = str(strNumeroCuenta).strip()
        self.__strEntidadBancaria = str(strEntidadBancaria).strip()
        self.__strTipoCuenta = str(strTipoCuenta).strip()
        self.__dblSaldoActual = float(dblSaldoActual)

    # ---- Métodos Operacionales -----------------------------------------------
    def acreditarSaldo(self, dblMonto):
        """Incrementa el saldo actual de la cuenta bancaria."""
        dblValor = float(dblMonto)
        if dblValor <= 0:
            return False
        self.__dblSaldoActual += dblValor
        return True

    def debitarSaldo(self, dblMonto):
        """
        Descuenta fondos de la cuenta bancaria.
        Permite sobregiro controlado (saldo negativo) si el usuario registra gastos
        antes de cargar su saldo inicial, activando el estado de sobregiro.
        """
        dblValor = float(dblMonto)
        if dblValor <= 0:
            return False
        self.__dblSaldoActual -= dblValor
        return True

    def verificarDisponibilidad(self, dblMonto):
        """Devuelve True si el saldo disponible cubre el monto consultado."""
        return self.__dblSaldoActual >= float(dblMonto)

    def obtenerSaldo(self):
        """Retorna el saldo disponible actual."""
        return self.__dblSaldoActual

    def estaEnSobregiro(self):
        """True cuando la cuenta se encuentra con saldo negativo (< 0)."""
        return self.__dblSaldoActual < 0

    def consultarEstadoCuenta(self):
        strSigno = "-" if self.__dblSaldoActual < 0 else ""
        strSaldo = f"{strSigno}${abs(self.__dblSaldoActual):,.0f}".replace(",", ".")
        return f"{self.__strEntidadBancaria} ({self.__strTipoCuenta} • {self.__strNumeroCuenta}): {strSaldo}"

    # Alias exactos de la Matriz UML (Sección 4 del Documento)
    def Acreditar_Saldo(self, dblMonto):
        return self.acreditarSaldo(dblMonto)

    def Debitar_Saldo(self, dblMonto):
        return self.debitarSaldo(dblMonto)

    def Verificar_Disponibilidad(self, dblMonto):
        return self.verificarDisponibilidad(dblMonto)

    def Obtener_Saldo(self):
        return self.obtenerSaldo()

    # ---- Serialización para Servicio Web -------------------------------------
    def toDict(self):
        return {
            "strNumeroCuenta": self.__strNumeroCuenta,
            "strEntidadBancaria": self.__strEntidadBancaria,
            "strTipoCuenta": self.__strTipoCuenta,
            "dblSaldoActual": round(self.__dblSaldoActual, 2),
            "boolSobregiro": self.estaEnSobregiro(),
            "strResumen": self.consultarEstadoCuenta(),
        }

    def __str__(self):
        return self.consultarEstadoCuenta()

    # ---- Getters y setters ---------------------------------------------------
    def getStrNumeroCuenta(self):
        return self.__strNumeroCuenta

    def getStrEntidadBancaria(self):
        return self.__strEntidadBancaria

    def setStrEntidadBancaria(self, strEntidadBancaria):
        self.__strEntidadBancaria = str(strEntidadBancaria).strip()

    def getStrTipoCuenta(self):
        return self.__strTipoCuenta

    def setStrTipoCuenta(self, strTipoCuenta):
        self.__strTipoCuenta = str(strTipoCuenta).strip()

    def getDblSaldoActual(self):
        return self.__dblSaldoActual

    def setDblSaldoActual(self, dblSaldoActual):
        self.__dblSaldoActual = float(dblSaldoActual)
