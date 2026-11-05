# =============================================================================
#  Clase Persona (Usuario en UML): la dueña de sus finanzas (RF-01 a RF-06).
#  Guarda sus movimientos, cuentas bancarias, categorías personalizadas,
#  presupuestos y metas de ahorro. Mantiene 100% retrocompatibilidad.
#  Capa: LOGICA
# =============================================================================

from LOGICA.Categoria import Categoria
from LOGICA.CuentaBancaria import CuentaBancaria
from LOGICA.MetaAhorro import MetaAhorro
from LOGICA.Movimiento import Movimiento
from LOGICA.Presupuesto import Presupuesto
from LOGICA.ReporteFinanciero import ReporteFinanciero
from LOGICA.Seguridad import Seguridad


class Persona:

    STR_TODOS = "Todos"

    # ---- Constructor ---------------------------------------------------------
    def __init__(self, strDocumento, strNombre, strCorreo, strPasswordHash=""):
        self.__strDocumento = str(strDocumento).strip()
        self.__strNombre = str(strNombre).strip()
        self.__strCorreo = str(strCorreo).strip()
        self.__strPasswordHash = strPasswordHash or ""
        self.__listaMovimientos = []                 # objetos Movimiento
        self.__listaPresupuestos = []                # objetos Presupuesto
        self.__listaCuentas = []                     # objetos CuentaBancaria (RF-02)
        self.__listaCategoriasPersonalizadas = []    # objetos Categoria (RF-03)
        self.__listaMetasAhorro = []                 # objetos MetaAhorro (RF-05)

    # ---- Autenticación y Seguridad (RF-01 / RNF-01) --------------------------
    def autenticarUsuario(self, strPasswordPlano):
        """Valida la contraseña ingresada contra el hash PBKDF2-SHA256."""
        if not self.__strPasswordHash:
            return False
        return Seguridad.verificarPassword(strPasswordPlano, self.__strPasswordHash)

    def establecerPasswordPlano(self, strPasswordPlano):
        self.__strPasswordHash = Seguridad.cifrarPassword(strPasswordPlano)

    def actualizarDatos(self, strNombre, strCorreo):
        if str(strNombre).strip() == "" or "@" not in str(strCorreo):
            return False
        self.__strNombre = str(strNombre).strip()
        self.__strCorreo = str(strCorreo).strip()
        return True

    # ---- Métodos de Cuentas Bancarias (RF-02) --------------------------------
    def agregarCuenta(self, cuenta):
        existente = self.buscarCuenta(cuenta.getStrNumeroCuenta())
        if existente is None:
            self.__listaCuentas.append(cuenta)
        else:
            existente.setStrEntidadBancaria(cuenta.getStrEntidadBancaria())
            existente.setStrTipoCuenta(cuenta.getStrTipoCuenta())
            existente.setDblSaldoActual(cuenta.getDblSaldoActual())

    def buscarCuenta(self, strNumeroCuenta):
        for cuenta in self.__listaCuentas:
            if cuenta.getStrNumeroCuenta() == strNumeroCuenta:
                return cuenta
        return None

    def eliminarCuenta(self, strNumeroCuenta):
        cuenta = self.buscarCuenta(strNumeroCuenta)
        if cuenta is not None:
            self.__listaCuentas.remove(cuenta)
            return True
        return False

    def obtenerCuentaPrincipal(self):
        if len(self.__listaCuentas) > 0:
            return self.__listaCuentas[0]
        return None

    def calcularSaldoTotalCuentas(self):
        return sum(c.getDblSaldoActual() for c in self.__listaCuentas)

    def obtenerCuentasEnSobregiro(self):
        return [c for c in self.__listaCuentas if c.estaEnSobregiro()]

    # ---- Métodos de Categorías Dinámicas (RF-03) -----------------------------
    def agregarCategoriaPersonalizada(self, categoria):
        existente = self.buscarCategoriaPorId(categoria.getIntIdCategoria())
        if existente is None:
            self.__listaCategoriasPersonalizadas.append(categoria)
        else:
            existente.setStrNombreCategoria(categoria.getStrNombreCategoria())
            existente.setDblLimiteSugerido(categoria.getDblLimiteSugerido())

    def buscarCategoriaPorId(self, intIdCategoria):
        for cat in self.__listaCategoriasPersonalizadas:
            if cat.getIntIdCategoria() == int(intIdCategoria):
                return cat
        return None

    def eliminarCategoriaPersonalizada(self, intIdCategoria):
        cat = self.buscarCategoriaPorId(intIdCategoria)
        if cat is not None:
            self.__listaCategoriasPersonalizadas.remove(cat)
            return True
        return False

    def obtenerNombresCategorias(self, strTipo):
        """Combina las categorías base de Movimiento con las personalizadas del usuario."""
        if strTipo == Movimiento.STR_TIPO_INGRESO:
            listaBase = list(Movimiento.LISTA_CATEGORIAS_INGRESO)
        elif strTipo == Movimiento.STR_TIPO_GASTO:
            listaBase = list(Movimiento.LISTA_CATEGORIAS_GASTO)
        else:
            listaBase = list(Movimiento.LISTA_CATEGORIAS_INGRESO) + list(Movimiento.LISTA_CATEGORIAS_GASTO)

        for cat in self.__listaCategoriasPersonalizadas:
            if strTipo not in (Movimiento.STR_TIPO_INGRESO, Movimiento.STR_TIPO_GASTO) or cat.getStrTipoMovimiento() == strTipo:
                if cat.getStrNombreCategoria() not in listaBase:
                    listaBase.append(cat.getStrNombreCategoria())
        return listaBase

    def obtenerCatalogoCategorias(self):
        """Devuelve todas las categorías (predefinidas y personalizadas) estructuradas."""
        resultado = []
        for nombre in Movimiento.LISTA_CATEGORIAS_INGRESO:
            resultado.append(
                {
                    "intIdCategoria": 0,
                    "strNombreCategoria": nombre,
                    "strTipoMovimiento": Movimiento.STR_TIPO_INGRESO,
                    "dblLimiteSugerido": 0.0,
                    "boolPersonalizada": False,
                }
            )
        for nombre in Movimiento.LISTA_CATEGORIAS_GASTO:
            resultado.append(
                {
                    "intIdCategoria": 0,
                    "strNombreCategoria": nombre,
                    "strTipoMovimiento": Movimiento.STR_TIPO_GASTO,
                    "dblLimiteSugerido": 0.0,
                    "boolPersonalizada": False,
                }
            )
        for cat in self.__listaCategoriasPersonalizadas:
            resultado.append(cat.toDict(boolPersonalizada=True))
        return resultado

    # ---- Métodos de Movimientos (Retrocompatible + filtro cuenta) ------------
    def agregarMovimiento(self, movimiento):
        self.__listaMovimientos.append(movimiento)

    def buscarMovimiento(self, intId):
        for movimiento in self.__listaMovimientos:
            if movimiento.getIntId() == int(intId):
                return movimiento
        return None

    def eliminarMovimiento(self, intId):
        """Quita el movimiento con ese id. Devuelve True si lo encontró."""
        for movimiento in self.__listaMovimientos:
            if movimiento.getIntId() == int(intId):
                self.__listaMovimientos.remove(movimiento)
                return True
        return False

    def consultarMovimientos(self, strTipo="Todos", strMes="Todos", strCategoria="Todos", strNumeroCuenta="Todos"):
        """Filtra por tipo, mes, categoría y cuenta, y ordena del más reciente al más antiguo."""
        listaResultado = []
        for movimiento in self.__listaMovimientos:
            boolTipoOk = strTipo == Persona.STR_TODOS or movimiento.getStrTipo() == strTipo
            boolMesOk = strMes == Persona.STR_TODOS or movimiento.obtenerMes() == strMes
            boolCatOk = strCategoria == Persona.STR_TODOS or movimiento.getStrCategoria() == strCategoria
            boolCtaOk = strNumeroCuenta == Persona.STR_TODOS or movimiento.getStrNumeroCuenta() == strNumeroCuenta
            if boolTipoOk and boolMesOk and boolCatOk and boolCtaOk:
                listaResultado.append(movimiento)
        listaResultado.sort(key=lambda mov: (mov.getStrFecha(), mov.getIntId()), reverse=True)
        return listaResultado

    def obtenerMeses(self):
        """Los meses (AAAA-MM) en que hay movimientos, del más reciente al más antiguo."""
        listaMeses = []
        for movimiento in self.__listaMovimientos:
            strMes = movimiento.obtenerMes()
            if strMes not in listaMeses:
                listaMeses.append(strMes)
        listaMeses.sort(reverse=True)
        return listaMeses

    # ---- Métodos de Cálculo (todos reciben el mes, o "Todos") ----------------
    def calcularTotalIngresos(self, strMes="Todos"):
        dblTotal = 0.0
        for movimiento in self.consultarMovimientos(Movimiento.STR_TIPO_INGRESO, strMes):
            dblTotal += movimiento.getDblMonto()
        return dblTotal

    def calcularTotalGastos(self, strMes="Todos"):
        dblTotal = 0.0
        for movimiento in self.consultarMovimientos(Movimiento.STR_TIPO_GASTO, strMes):
            dblTotal += movimiento.getDblMonto()
        return dblTotal

    def calcularSaldo(self, strMes="Todos"):
        """Ingresos menos gastos del período."""
        return self.calcularTotalIngresos(strMes) - self.calcularTotalGastos(strMes)

    def calcularPorcentajeAhorro(self, strMes="Todos"):
        """Saldo x 100 / ingresos."""
        dblIngresos = self.calcularTotalIngresos(strMes)
        if dblIngresos == 0:
            return 0.0
        return self.calcularSaldo(strMes) * 100.0 / dblIngresos

    def calcularGastosPorCategoria(self, strMes="Todos"):
        """Diccionario categoría -> total gastado, de mayor a menor."""
        dicGastos = {}
        for movimiento in self.consultarMovimientos(Movimiento.STR_TIPO_GASTO, strMes):
            strCategoria = movimiento.getStrCategoria()
            dicGastos[strCategoria] = dicGastos.get(strCategoria, 0.0) + movimiento.getDblMonto()
        return dict(sorted(dicGastos.items(), key=lambda par: par[1], reverse=True))

    # ---- Métodos de Presupuesto y Alertas (RF-04) ----------------------------
    def buscarPresupuesto(self, strCategoria):
        for presupuesto in self.__listaPresupuestos:
            if presupuesto.getStrCategoria() == strCategoria:
                return presupuesto
        return None

    def definirPresupuesto(
        self,
        strCategoria,
        dblLimite,
        strPeriodoMesAno="Todos",
        dblPorcentajeAlerta=Presupuesto.DBL_PORCENTAJE_ALERTA_DEFECTO,
    ):
        """Si ya había un presupuesto de esa categoría, actualiza límite, periodo y umbral."""
        presupuesto = self.buscarPresupuesto(strCategoria)
        if presupuesto is None:
            self.__listaPresupuestos.append(
                Presupuesto(strCategoria, dblLimite, strPeriodoMesAno, dblPorcentajeAlerta)
            )
        else:
            presupuesto.setDblLimite(dblLimite)
            presupuesto.setStrPeriodoMesAno(strPeriodoMesAno)
            presupuesto.setDblPorcentajeAlerta(dblPorcentajeAlerta)

    def eliminarPresupuesto(self, strCategoria):
        presupuesto = self.buscarPresupuesto(strCategoria)
        if presupuesto is not None:
            self.__listaPresupuestos.remove(presupuesto)
            return True
        return False

    def obtenerAlertas(self, strMes):
        """Lista de textos de alerta (retrocompatible) según umbral configurado (85% RF-04) y sobregiro."""
        return [item["strMensaje"] for item in self.obtenerAlertasDetalladas(strMes)]

    def obtenerAlertasDetalladas(self, strMes):
        """Devuelve objetos estructurados de alerta (presupuestos >=85%, >100% y cuentas en sobregiro)."""
        listaAlertas = []
        for presupuesto in self.__listaPresupuestos:
            dblUso = presupuesto.calcularPorcentajeUso(self.__listaMovimientos, strMes)
            dblUmbral = presupuesto.getDblPorcentajeAlerta()
            if dblUso > 100.0:
                listaAlertas.append(
                    {
                        "strNivel": "excedido",
                        "strCategoria": presupuesto.getStrCategoria(),
                        "dblPorcentaje": round(dblUso, 1),
                        "strMensaje": presupuesto.generarAlertaSobrecosto(self.__listaMovimientos, strMes),
                    }
                )
            elif dblUso >= dblUmbral:
                listaAlertas.append(
                    {
                        "strNivel": "preventiva",
                        "strCategoria": presupuesto.getStrCategoria(),
                        "dblPorcentaje": round(dblUso, 1),
                        "strMensaje": presupuesto.generarAlertaSobrecosto(self.__listaMovimientos, strMes),
                    }
                )

        for cuenta in self.obtenerCuentasEnSobregiro():
            strSaldoAbs = "$" + f"{abs(cuenta.getDblSaldoActual()):,.0f}".replace(",", ".")
            listaAlertas.append(
                {
                    "strNivel": "sobregiro",
                    "strCategoria": cuenta.getStrEntidadBancaria(),
                    "dblPorcentaje": 100.0,
                    "strMensaje": (
                        f"Cuenta en sobregiro: {cuenta.getStrEntidadBancaria()} "
                        f"({cuenta.getStrNumeroCuenta()}) presenta saldo negativo de -{strSaldoAbs}."
                    ),
                }
            )
        return listaAlertas

    # ---- Métodos de Metas de Ahorro (RF-05) ----------------------------------
    def agregarMetaAhorro(self, meta):
        existente = self.buscarMetaAhorro(meta.getIntIdMeta())
        if existente is None:
            self.__listaMetasAhorro.append(meta)
        else:
            existente.setStrNombreMeta(meta.getStrNombreMeta())
            existente.setDblMontoObjetivo(meta.getDblMontoObjetivo())
            existente.setDblMontoAcumulado(meta.getDblMontoAcumulado())
            existente.setStrFechaLimite(meta.getStrFechaLimite())

    def buscarMetaAhorro(self, intIdMeta):
        for meta in self.__listaMetasAhorro:
            if meta.getIntIdMeta() == int(intIdMeta):
                return meta
        return None

    def eliminarMetaAhorro(self, intIdMeta):
        meta = self.buscarMetaAhorro(intIdMeta)
        if meta is not None:
            self.__listaMetasAhorro.remove(meta)
            return True
        return False

    # ---- Reportes y Resumen Consolidado (RF-06 / UML) ------------------------
    def generarReporte(self, strFechaInicio="", strFechaFin=""):
        return ReporteFinanciero(strFechaInicio, strFechaFin, self)

    def consultarResumen(self, strMes="Todos"):
        dblIng = self.calcularTotalIngresos(strMes)
        dblGas = self.calcularTotalGastos(strMes)
        dblSal = self.calcularSaldo(strMes)
        return (
            f"Usuario: {self.__strNombre} | Ingresos: ${dblIng:,.0f} | "
            f"Gastos: ${dblGas:,.0f} | Balance: ${dblSal:,.0f}"
        ).replace(",", ".")

    # Alias exactos de la Matriz UML (Usuario)
    def Autenticar_Usuario(self, strEmail, strPassword):
        if strEmail.strip().lower() != self.__strCorreo.lower():
            return False
        return self.autenticarUsuario(strPassword)

    def Actualizar_Datos(self, strNombre, strEmail):
        return self.actualizarDatos(strNombre, strEmail)

    def Consultar_Resumen(self):
        return self.consultarResumen()

    def toDictPerfil(self):
        return {
            "strDocumento": self.__strDocumento,
            "strNombre": self.__strNombre,
            "strCorreo": self.__strCorreo,
            "intCantidadCuentas": len(self.__listaCuentas),
            "intCantidadMovimientos": len(self.__listaMovimientos),
            "dblPatrimonioCuentas": round(self.calcularSaldoTotalCuentas(), 2),
        }

    # ---- Cómo se ve la persona en la lista desplegable ----------------------
    def __str__(self):
        return f"{self.__strNombre} ({self.__strDocumento})"

    # ---- Getters y setters ---------------------------------------------------
    def getStrDocumento(self):
        return self.__strDocumento

    def getStrNombre(self):
        return self.__strNombre

    def setStrNombre(self, strNombre):
        self.__strNombre = strNombre

    def getStrCorreo(self):
        return self.__strCorreo

    def setStrCorreo(self, strCorreo):
        self.__strCorreo = strCorreo

    def getStrPasswordHash(self):
        return self.__strPasswordHash

    def setStrPasswordHash(self, strPasswordHash):
        self.__strPasswordHash = strPasswordHash

    def getListaMovimientos(self):
        return self.__listaMovimientos

    def getListaPresupuestos(self):
        return self.__listaPresupuestos

    def getListaCuentas(self):
        return self.__listaCuentas

    def getListaCategoriasPersonalizadas(self):
        return self.__listaCategoriasPersonalizadas

    def getListaMetasAhorro(self):
        return self.__listaMetasAhorro
