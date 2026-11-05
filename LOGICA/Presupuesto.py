# =============================================================================
#  Clase Presupuesto: el límite de gasto mensual de una categoría (RF-04).
#  Soporta umbral de alerta configurable (por defecto 85% según RF-04).
#  Capa: LOGICA
# =============================================================================


class Presupuesto:

    STR_TODOS = "Todos"
    DBL_PORCENTAJE_ALERTA_DEFECTO = 85.0

    # ---- Constructor ---------------------------------------------------------
    def __init__(
        self,
        strCategoria,
        dblLimite,
        strPeriodoMesAno="Todos",
        dblPorcentajeAlerta=DBL_PORCENTAJE_ALERTA_DEFECTO,
    ):
        self.__strCategoria = strCategoria                      # por ejemplo "Alimentación"
        self.__dblLimite = float(dblLimite)                     # por ejemplo 600000
        self.__strPeriodoMesAno = strPeriodoMesAno or "Todos"   # por ejemplo "2026-11"
        self.__dblPorcentajeAlerta = float(dblPorcentajeAlerta) # 85.0 según RF-04

    # ---- Métodos (todos reciben la lista de movimientos y el mes) -----------
    def calcularGastado(self, listaMovimientos, strMes):
        """Suma los gastos de esta categoría en ese mes ("Todos" = todos los meses)."""
        dblGastado = 0.0
        for movimiento in listaMovimientos:
            boolTipoOk = not movimiento.esIngreso()
            boolCategoriaOk = movimiento.getStrCategoria() == self.__strCategoria
            boolMesOk = strMes == Presupuesto.STR_TODOS or movimiento.obtenerMes() == strMes
            if boolTipoOk and boolCategoriaOk and boolMesOk:
                dblGastado += movimiento.getDblMonto()
        return dblGastado

    def calcularDisponible(self, listaMovimientos, strMes):
        """Límite menos gastado (negativo si ya se pasó)."""
        return self.__dblLimite - self.calcularGastado(listaMovimientos, strMes)

    def calcularPorcentajeUso(self, listaMovimientos, strMes):
        """Gastado x 100 / límite."""
        if self.__dblLimite <= 0:
            return 0.0
        return self.calcularGastado(listaMovimientos, strMes) * 100.0 / self.__dblLimite

    def estaExcedido(self, listaMovimientos, strMes):
        """True si lo gastado supera el límite (> 100%)."""
        return self.calcularGastado(listaMovimientos, strMes) > self.__dblLimite

    def enAlertaPreventiva(self, listaMovimientos, strMes):
        """True si superó o alcanzó el porcentaje de alerta (85% RF-04) sin exceder el 100%."""
        dblUso = self.calcularPorcentajeUso(listaMovimientos, strMes)
        return dblUso >= self.__dblPorcentajeAlerta and dblUso <= 100.0

    def obtenerEstado(self, listaMovimientos, strMes):
        """Retorna 'excedido', 'alerta' o 'saludable'."""
        if self.estaExcedido(listaMovimientos, strMes):
            return "excedido"
        if self.enAlertaPreventiva(listaMovimientos, strMes):
            return "alerta"
        return "saludable"

    def generarAlertaSobrecosto(self, listaMovimientos, strMes):
        """Devuelve el mensaje de alerta si aplica (>= umbral o > 100%), o cadena vacía."""
        dblUso = self.calcularPorcentajeUso(listaMovimientos, strMes)
        strLimite = "$" + f"{self.__dblLimite:,.0f}".replace(",", ".")
        dblGastado = self.calcularGastado(listaMovimientos, strMes)
        strGastado = "$" + f"{dblGastado:,.0f}".replace(",", ".")
        if dblUso > 100.0:
            return (
                f"Sobrecosto en {self.__strCategoria}: ejecutó {strGastado} "
                f"({dblUso:.1f}% del techo de {strLimite})."
            )
        if dblUso >= self.__dblPorcentajeAlerta:
            return (
                f"Alerta preventiva en {self.__strCategoria}: alcanzó el {dblUso:.1f}% "
                f"({strGastado} de {strLimite}, umbral {self.__dblPorcentajeAlerta:.0f}%)."
            )
        return ""

    # ---- Alias exactos de la Matriz UML (Sección 4) --------------------------
    def Establecer_Presupuesto(self, dblLimite, strPeriodo):
        self.__dblLimite = float(dblLimite)
        self.__strPeriodoMesAno = strPeriodo

    def Calcular_Porcentaje_Ejecucion(self, listaMovimientos, strMes="Todos"):
        return self.calcularPorcentajeUso(listaMovimientos, strMes)

    def Generar_Alerta_Sobrecosto(self, listaMovimientos, strMes="Todos"):
        return self.generarAlertaSobrecosto(listaMovimientos, strMes)

    def toDict(self, listaMovimientos, strMes):
        dblGastado = self.calcularGastado(listaMovimientos, strMes)
        dblDisponible = self.calcularDisponible(listaMovimientos, strMes)
        dblPorcentajeUso = self.calcularPorcentajeUso(listaMovimientos, strMes)
        return {
            "strCategoria": self.__strCategoria,
            "dblLimite": round(self.__dblLimite, 2),
            "dblGastado": round(dblGastado, 2),
            "dblDisponible": round(dblDisponible, 2),
            "dblPorcentajeUso": round(dblPorcentajeUso, 1),
            "dblPorcentajeAlerta": round(self.__dblPorcentajeAlerta, 1),
            "strPeriodoMesAno": self.__strPeriodoMesAno,
            "strEstado": self.obtenerEstado(listaMovimientos, strMes),
            "strMensajeAlerta": self.generarAlertaSobrecosto(listaMovimientos, strMes),
        }

    # ---- Getters y setters ---------------------------------------------------
    def getStrCategoria(self):
        return self.__strCategoria

    def getDblLimite(self):
        return self.__dblLimite

    def setDblLimite(self, dblLimite):
        self.__dblLimite = float(dblLimite)

    def getStrPeriodoMesAno(self):
        return self.__strPeriodoMesAno

    def setStrPeriodoMesAno(self, strPeriodoMesAno):
        self.__strPeriodoMesAno = strPeriodoMesAno or "Todos"

    def getDblPorcentajeAlerta(self):
        return self.__dblPorcentajeAlerta

    def setDblPorcentajeAlerta(self, dblPorcentajeAlerta):
        self.__dblPorcentajeAlerta = float(dblPorcentajeAlerta)
