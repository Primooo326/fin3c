# =============================================================================
#  Clase MetaAhorro: Objetivo de ahorro con abonos y proyección de fecha (RF-05)
#  Modelado Orientado a Objetos (Matriz de Diseño UML - Universidad ECCI)
#  Capa: LOGICA
# =============================================================================

from datetime import date, datetime, timedelta
import math


class MetaAhorro:

    # ---- Constructor ---------------------------------------------------------
    def __init__(
        self,
        intIdMeta,
        strNombreMeta,
        dblMontoObjetivo,
        dblMontoAcumulado=0.0,
        strFechaLimite="",
        strFechaCreacion="",
    ):
        self.__intIdMeta = int(intIdMeta)
        self.__strNombreMeta = str(strNombreMeta).strip()
        self.__dblMontoObjetivo = float(dblMontoObjetivo)
        self.__dblMontoAcumulado = float(dblMontoAcumulado)
        self.__strFechaLimite = str(strFechaLimite).strip()
        self.__strFechaCreacion = str(strFechaCreacion).strip() or date.today().strftime("%Y-%m-%d")

    # ---- Operaciones de Negocio (RF-05) --------------------------------------
    def abonarCapital(self, dblMonto):
        """Suma un abono progresivo al capital acumulado de la meta."""
        dblValor = float(dblMonto)
        if dblValor <= 0:
            return False
        self.__dblMontoAcumulado += dblValor
        return True

    def calcularProgresoPorcentual(self):
        """Retorna el porcentaje de avance hacia el monto objetivo (0 a 100+)."""
        if self.__dblMontoObjetivo <= 0:
            return 0.0
        return (self.__dblMontoAcumulado * 100.0) / self.__dblMontoObjetivo

    def calcularMontoFaltante(self):
        """Monto restante para alcanzar el 100% de la meta."""
        return max(0.0, self.__dblMontoObjetivo - self.__dblMontoAcumulado)

    def estaCompletada(self):
        return self.__dblMontoAcumulado >= self.__dblMontoObjetivo

    def calcularDiasRestantes(self):
        try:
            dtLimite = datetime.strptime(self.__strFechaLimite, "%Y-%m-%d").date()
            return (dtLimite - date.today()).days
        except ValueError:
            return 0

    def calcularCuotaMensualSugerida(self):
        """Ahorro mensual necesario desde hoy para cumplir antes de la fecha límite."""
        dblFaltante = self.calcularMontoFaltante()
        if dblFaltante <= 0:
            return 0.0
        intDias = self.calcularDiasRestantes()
        if intDias <= 0:
            return dblFaltante
        dblMeses = max(1.0, intDias / 30.0)
        return dblFaltante / dblMeses

    def calcularFechaProyectada(self):
        """
        Calcula la fecha estimada de cumplimiento según el ritmo histórico de abonos (RF-05).
        Si ya se completó retorna 'Completada'; si aún no hay abonos retorna 'Sin ritmo aún'.
        """
        if self.estaCompletada():
            return date.today().strftime("%Y-%m-%d")
        if self.__dblMontoAcumulado <= 0:
            return "Pendiente primer abono"

        try:
            dtCreacion = datetime.strptime(self.__strFechaCreacion, "%Y-%m-%d").date()
        except ValueError:
            dtCreacion = date.today() - timedelta(days=30)

        intDiasTranscurridos = max(1, (date.today() - dtCreacion).days)
        dblRitmoDiario = self.__dblMontoAcumulado / intDiasTranscurridos
        if dblRitmoDiario <= 0:
            return "Pendiente primer abono"

        intDiasFaltantes = int(math.ceil(self.calcularMontoFaltante() / dblRitmoDiario))
        # Límite razonable de proyección a 20 años para evitar desbordamiento de fechas
        intDiasFaltantes = min(intDiasFaltantes, 365 * 20)
        dtProyectada = date.today() + timedelta(days=intDiasFaltantes)
        return dtProyectada.strftime("%Y-%m-%d")

    # ---- Alias exactos de la Matriz UML (Sección 4) --------------------------
    def Crear_Meta(self, strNombre, dblObjetivo, dtFecha):
        self.__strNombreMeta = str(strNombre).strip()
        self.__dblMontoObjetivo = float(dblObjetivo)
        self.__strFechaLimite = str(dtFecha).strip()

    def Abonar_Capital(self, dblMonto):
        return self.abonarCapital(dblMonto)

    def Calcular_Progreso_Porcentual(self):
        return self.calcularProgresoPorcentual()

    # ---- Serialización para Servicio Web -------------------------------------
    def toDict(self):
        dblProgreso = self.calcularProgresoPorcentual()
        return {
            "intIdMeta": self.__intIdMeta,
            "strNombreMeta": self.__strNombreMeta,
            "dblMontoObjetivo": round(self.__dblMontoObjetivo, 2),
            "dblMontoAcumulado": round(self.__dblMontoAcumulado, 2),
            "dblMontoFaltante": round(self.calcularMontoFaltante(), 2),
            "dblProgresoPorcentual": round(dblProgreso, 1),
            "strFechaLimite": self.__strFechaLimite,
            "strFechaCreacion": self.__strFechaCreacion,
            "strFechaProyectada": self.calcularFechaProyectada(),
            "intDiasRestantes": self.calcularDiasRestantes(),
            "dblCuotaMensualSugerida": round(self.calcularCuotaMensualSugerida(), 2),
            "boolCompletada": self.estaCompletada(),
        }

    # ---- Getters y setters ---------------------------------------------------
    def getIntIdMeta(self):
        return self.__intIdMeta

    def getStrNombreMeta(self):
        return self.__strNombreMeta

    def setStrNombreMeta(self, strNombreMeta):
        self.__strNombreMeta = str(strNombreMeta).strip()

    def getDblMontoObjetivo(self):
        return self.__dblMontoObjetivo

    def setDblMontoObjetivo(self, dblMontoObjetivo):
        self.__dblMontoObjetivo = float(dblMontoObjetivo)

    def getDblMontoAcumulado(self):
        return self.__dblMontoAcumulado

    def setDblMontoAcumulado(self, dblMontoAcumulado):
        self.__dblMontoAcumulado = float(dblMontoAcumulado)

    def getStrFechaLimite(self):
        return self.__strFechaLimite

    def setStrFechaLimite(self, strFechaLimite):
        self.__strFechaLimite = str(strFechaLimite).strip()

    def getStrFechaCreacion(self):
        return self.__strFechaCreacion
