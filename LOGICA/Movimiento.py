# =============================================================================
#  Clase Movimiento (Transaccion en UML): un ingreso o un gasto de una persona.
#  Mantiene 100% compatibilidad con la versión base y añade vínculo con cuenta.
#  Capa: LOGICA
# =============================================================================


class Movimiento:

    # ---- Constantes de la clase ---------------------------------------------
    STR_TIPO_INGRESO = "Ingreso"
    STR_TIPO_GASTO = "Gasto"

    LISTA_CATEGORIAS_INGRESO = [
        "Salario",
        "Ventas",
        "Honorarios",
        "Inversiones",
        "Otros ingresos",
    ]

    LISTA_CATEGORIAS_GASTO = [
        "Alimentación",
        "Transporte",
        "Vivienda",
        "Servicios",
        "Salud",
        "Educación",
        "Entretenimiento",
        "Otros gastos",
    ]

    # ---- Constructor ---------------------------------------------------------
    def __init__(
        self,
        intId,
        strTipo,
        strDescripcion,
        dblMonto,
        strCategoria,
        strFecha,
        strNumeroCuenta="",
    ):
        self.__intId = int(intId)                       # número único del movimiento
        self.__strTipo = strTipo                        # "Ingreso" o "Gasto"
        self.__strDescripcion = strDescripcion          # qué fue
        self.__dblMonto = float(dblMonto)               # siempre positivo
        self.__strCategoria = strCategoria              # Salario, Vivienda, ...
        self.__strFecha = strFecha                      # AAAA-MM-DD
        self.__strNumeroCuenta = strNumeroCuenta or ""  # Cuenta bancaria asociada (RF-02)

    # ---- Métodos -------------------------------------------------------------
    def esIngreso(self):
        """True si el movimiento es un ingreso."""
        return self.__strTipo == Movimiento.STR_TIPO_INGRESO

    def obtenerValorConSigno(self):
        """El monto positivo si es ingreso y negativo si es gasto."""
        if self.esIngreso():
            return self.__dblMonto
        return -self.__dblMonto

    def obtenerMes(self):
        """Los primeros 7 caracteres de la fecha, por ejemplo 2026-11."""
        return self.__strFecha[:7]

    def mostrarInfo(self):
        """Una línea de texto con todos los datos."""
        strMonto = "$" + f"{self.__dblMonto:,.0f}".replace(",", ".")
        strCuentaTxt = f" | Cta: {self.__strNumeroCuenta}" if self.__strNumeroCuenta else ""
        return (
            f"#{self.__intId} | {self.__strFecha} | {self.__strTipo} | "
            f"{self.__strCategoria} | {self.__strDescripcion} | {strMonto}{strCuentaTxt}"
        )

    # ---- Métodos equivalentes del Diagrama UML (Transaccion) -----------------
    def procesarTransaccion(self, dblMonto, strTipo):
        if float(dblMonto) <= 0 or strTipo not in (Movimiento.STR_TIPO_INGRESO, Movimiento.STR_TIPO_GASTO):
            return False
        self.__dblMonto = float(dblMonto)
        self.__strTipo = strTipo
        return True

    def actualizarSaldoCuenta(self, cuentaBancaria):
        """Aplica el impacto contable de la transacción sobre una CuentaBancaria."""
        if cuentaBancaria is None:
            return
        if self.esIngreso():
            cuentaBancaria.acreditarSaldo(self.__dblMonto)
        else:
            cuentaBancaria.debitarSaldo(self.__dblMonto)

    def revertirSaldoCuenta(self, cuentaBancaria):
        """Revierte el impacto contable cuando se elimina/anula la transacción."""
        if cuentaBancaria is None:
            return
        if self.esIngreso():
            cuentaBancaria.debitarSaldo(self.__dblMonto)
        else:
            cuentaBancaria.acreditarSaldo(self.__dblMonto)

    def obtenerDetalle(self):
        return self.mostrarInfo()

    # Alias exactos de la Matriz UML
    def Procesar_Transaccion(self, dblMonto, strTipo):
        return self.procesarTransaccion(dblMonto, strTipo)

    def Actualizar_Saldo_Cuenta(self, cuentaBancaria=None):
        self.actualizarSaldoCuenta(cuentaBancaria)

    def Obtener_Detalle(self):
        return self.obtenerDetalle()

    def toDict(self):
        return {
            "intId": self.__intId,
            "strTipo": self.__strTipo,
            "strDescripcion": self.__strDescripcion,
            "dblMonto": round(self.__dblMonto, 2),
            "dblValorConSigno": round(self.obtenerValorConSigno(), 2),
            "strCategoria": self.__strCategoria,
            "strFecha": self.__strFecha,
            "strMes": self.obtenerMes(),
            "strNumeroCuenta": self.__strNumeroCuenta,
            "boolEsIngreso": self.esIngreso(),
        }

    # ---- Getters y setters ---------------------------------------------------
    def getIntId(self):
        return self.__intId

    def getStrTipo(self):
        return self.__strTipo

    def setStrTipo(self, strTipo):
        self.__strTipo = strTipo

    def getStrDescripcion(self):
        return self.__strDescripcion

    def setStrDescripcion(self, strDescripcion):
        self.__strDescripcion = strDescripcion

    def getDblMonto(self):
        return self.__dblMonto

    def setDblMonto(self, dblMonto):
        self.__dblMonto = float(dblMonto)

    def getStrCategoria(self):
        return self.__strCategoria

    def setStrCategoria(self, strCategoria):
        self.__strCategoria = strCategoria

    def getStrFecha(self):
        return self.__strFecha

    def setStrFecha(self, strFecha):
        self.__strFecha = strFecha

    def getStrNumeroCuenta(self):
        return self.__strNumeroCuenta

    def setStrNumeroCuenta(self, strNumeroCuenta):
        self.__strNumeroCuenta = strNumeroCuenta or ""
