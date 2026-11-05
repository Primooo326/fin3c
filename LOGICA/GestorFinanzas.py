# =============================================================================
#  Clase GestorFinanzas: Coordinador Singleton entre las vistas (Escritorio/Web)
#  y la capa de Persistencia PostgreSQL.
#  Capa: LOGICA
#
#  Conserva intactas todas las firmas clásicas (retornan None si todo salió bien
#  o el mensaje de error en texto) e incorpora operaciones completas RF-01..RF-06.
# =============================================================================

from datetime import date, datetime

from LOGICA.Categoria import Categoria
from LOGICA.CuentaBancaria import CuentaBancaria
from LOGICA.MetaAhorro import MetaAhorro
from LOGICA.Movimiento import Movimiento
from LOGICA.Persona import Persona
from LOGICA.Presupuesto import Presupuesto
from LOGICA.Seguridad import Seguridad
from PERSISTENCIA import DatosFinanzas


class GestorFinanzas:

    __instancia = None   # el único gestor de toda la aplicación

    @staticmethod
    def getInstancia():
        """Devuelve siempre el mismo gestor y sincroniza carga si aún no estaba conectado."""
        if GestorFinanzas.__instancia is None:
            GestorFinanzas.__instancia = GestorFinanzas()
        else:
            GestorFinanzas.__instancia.asegurarCargaInicial()
        return GestorFinanzas.__instancia

    # ---- Constructor ---------------------------------------------------------
    def __init__(self):
        self.__listaPersonas = []
        self.__boolDatosCargados = False
        self.__strUltimoErrorBD = ""
        self.asegurarCargaInicial()

    def asegurarCargaInicial(self):
        """Intenta cargar desde PostgreSQL si aún no se habían cargado los objetos en memoria."""
        if self.__boolDatosCargados:
            return True
        try:
            self.__cargarDatos()
            self.__boolDatosCargados = True
            self.__strUltimoErrorBD = ""
            return True
        except Exception as exc:
            self.__strUltimoErrorBD = str(exc)
            return False

    def recargarDesdePersistencia(self):
        """Fuerza la recarga completa de objetos desde PostgreSQL."""
        self.__boolDatosCargados = False
        return self.asegurarCargaInicial()

    def getEstadoPersistencia(self):
        boolOk, strDetalle = DatosFinanzas.verificarConexion()
        if boolOk and not self.__boolDatosCargados:
            self.asegurarCargaInicial()
        return {
            "boolConectado": boolOk,
            "boolDatosCargados": self.__boolDatosCargados,
            "strDetalle": strDetalle,
        }

    def __cargarDatos(self):
        """Lee las tablas relacionales de PostgreSQL e instancia el grafo de objetos POO."""
        self.__listaPersonas = []

        for tplPersona in DatosFinanzas.consultarPersonasCompletas():
            strDocumento, strNombre, strCorreo, strPasswordHash = tplPersona
            self.__listaPersonas.append(
                Persona(strDocumento, strNombre, strCorreo, strPasswordHash)
            )

        for tplCuenta in DatosFinanzas.consultarCuentasBancarias():
            strNumCta, strDocumento, strEntidad, strTipoCta, dblSaldo = tplCuenta
            persona = self.buscarPersona(strDocumento)
            if persona is not None:
                persona.agregarCuenta(
                    CuentaBancaria(strNumCta, strEntidad, strTipoCta, dblSaldo)
                )

        for tplCat in DatosFinanzas.consultarCategorias():
            intIdCat, strDocumento, strNombreCat, strTipoMov, dblLimSug = tplCat
            persona = self.buscarPersona(strDocumento)
            if persona is not None:
                persona.agregarCategoriaPersonalizada(
                    Categoria(intIdCat, strNombreCat, strTipoMov, dblLimSug)
                )

        for tplMov in DatosFinanzas.consultarMovimientosCompletos():
            intId, strDocumento, strTipo, strDescripcion, dblMonto, strCategoria, strFecha, strNumeroCuenta = tplMov
            persona = self.buscarPersona(strDocumento)
            if persona is not None:
                persona.agregarMovimiento(
                    Movimiento(
                        intId,
                        strTipo,
                        strDescripcion,
                        dblMonto,
                        strCategoria,
                        strFecha,
                        strNumeroCuenta,
                    )
                )

        for tplPres in DatosFinanzas.consultarPresupuestosCompletos():
            strDocumento, strCategoria, dblLimite, strPeriodoMesAno, dblPorcentajeAlerta = tplPres
            persona = self.buscarPersona(strDocumento)
            if persona is not None:
                persona.definirPresupuesto(
                    strCategoria, dblLimite, strPeriodoMesAno, dblPorcentajeAlerta
                )

        for tplMeta in DatosFinanzas.consultarMetasAhorro():
            intIdMeta, strDocumento, strNombreMeta, dblObjetivo, dblAcumulado, strFechaLim, strFechaCrea = tplMeta
            persona = self.buscarPersona(strDocumento)
            if persona is not None:
                persona.agregarMetaAhorro(
                    MetaAhorro(
                        intIdMeta,
                        strNombreMeta,
                        dblObjetivo,
                        dblAcumulado,
                        strFechaLim,
                        strFechaCrea,
                    )
                )

    # =========================================================================
    #  RF-01: GESTIÓN DE USUARIOS Y AUTENTICACIÓN SEGURA (PBKDF2/SHA-256)
    # =========================================================================

    def getListaPersonas(self):
        return self.__listaPersonas

    def buscarPersona(self, strDocumento):
        strDoc = str(strDocumento).strip()
        for persona in self.__listaPersonas:
            if persona.getStrDocumento() == strDoc:
                return persona
        return None

    def buscarPersonaPorCorreo(self, strCorreo):
        strBuscado = str(strCorreo).strip().lower()
        for persona in self.__listaPersonas:
            if persona.getStrCorreo().lower() == strBuscado:
                return persona
        return None

    def registrarPersona(self, strDocumento, strNombre, strCorreo, strPassword=""):
        """
        Método retrocompatible: retorna None si todo salió bien o cadena de error.
        Además crea automáticamente la cuenta 'Efectivo Principal' (RF-02) y cifra la clave.
        """
        if not self.asegurarCargaInicial():
            return self.__strUltimoErrorBD or "Base de datos PostgreSQL no disponible."

        strDocumento = str(strDocumento).strip()
        strNombre = str(strNombre).strip()
        strCorreo = str(strCorreo).strip().lower()

        if not strDocumento.isdigit():
            return "El documento debe tener solo números."
        if len(strDocumento) < 4:
            return "El documento debe tener al menos 4 dígitos."
        if self.buscarPersona(strDocumento) is not None:
            return f"Ya existe una persona registrada con el documento {strDocumento}."
        if self.buscarPersonaPorCorreo(strCorreo) is not None:
            return f"Ya existe una cuenta registrada con el correo {strCorreo}."
        if strNombre == "":
            return "El nombre completo no puede estar vacío."
        if "@" not in strCorreo or "." not in strCorreo.split("@")[-1]:
            return "El correo electrónico no es válido (ejemplo: nombre@correo.com)."

        # Si viene desde ventana clásica sin clave, asigna una clave inicial cifrada con su documento
        strClaveReal = strPassword if str(strPassword).strip() != "" else strDocumento
        if strPassword != "" and len(strPassword) < 6:
            return "La contraseña debe tener al menos 6 caracteres."

        strPasswordHash = Seguridad.cifrarPassword(strClaveReal)
        nuevaPersona = Persona(strDocumento, strNombre, strCorreo, strPasswordHash)

        # Crea cuenta Efectivo Principal inicial para uso inmediato
        strNumEfectivo = f"EFEC-{strDocumento}"
        cuentaInicial = CuentaBancaria(strNumEfectivo, "Efectivo Principal", CuentaBancaria.STR_TIPO_EFECTIVO, 0.0)
        nuevaPersona.agregarCuenta(cuentaInicial)

        DatosFinanzas.guardarPersona(strDocumento, strNombre, strCorreo, strPasswordHash)
        DatosFinanzas.guardarCuentaBancaria(
            strNumEfectivo, strDocumento, "Efectivo Principal", CuentaBancaria.STR_TIPO_EFECTIVO, 0.0
        )
        self.__listaPersonas.append(nuevaPersona)
        return None

    def autenticarUsuario(self, strIdentificador, strPassword):
        """
        Autentica por correo electrónico o número de documento.
        Retorna tupla (persona, strMensajeError).
        """
        if not self.asegurarCargaInicial():
            return None, self.__strUltimoErrorBD or "Base de datos PostgreSQL no disponible."

        strId = str(strIdentificador).strip()
        if strId == "" or str(strPassword) == "":
            return None, "Ingrese su correo o documento y su contraseña."

        persona = self.buscarPersonaPorCorreo(strId)
        if persona is None:
            persona = self.buscarPersona(strId)
        if persona is None:
            return None, "Credenciales inválidas. Verifique su correo/documento o regístrese."

        if not persona.autenticarUsuario(strPassword):
            return None, "Contraseña incorrecta."

        return persona, None

    def actualizarPerfilPersona(self, persona, strNombre, strCorreo, strNuevaPassword=""):
        if persona is None:
            return "Usuario no encontrado."
        strNombre = str(strNombre).strip()
        strCorreo = str(strCorreo).strip().lower()
        if strNombre == "":
            return "El nombre no puede estar vacío."
        if "@" not in strCorreo or "." not in strCorreo.split("@")[-1]:
            return "El correo electrónico no es válido."

        otra = self.buscarPersonaPorCorreo(strCorreo)
        if otra is not None and otra.getStrDocumento() != persona.getStrDocumento():
            return "Ese correo electrónico ya pertenece a otro usuario."

        strNuevoHash = None
        if strNuevaPassword and strNuevaPassword.strip() != "":
            if len(strNuevaPassword) < 6:
                return "La nueva contraseña debe tener mínimo 6 caracteres."
            persona.establecerPasswordPlano(strNuevaPassword)
            strNuevoHash = persona.getStrPasswordHash()

        persona.setStrNombre(strNombre)
        persona.setStrCorreo(strCorreo)
        DatosFinanzas.actualizarPersona(persona.getStrDocumento(), strNombre, strCorreo, strNuevoHash)
        return None

    # =========================================================================
    #  RF-02: CUENTAS BANCARIAS (Ahorros, Corriente, Efectivo)
    # =========================================================================

    def registrarCuentaBancaria(self, persona, strNumeroCuenta, strEntidadBancaria, strTipoCuenta, strSaldoInicial="0"):
        if persona is None:
            return "Primero autentíquese o elija una persona."

        strNum = str(strNumeroCuenta).strip()
        strEntidad = str(strEntidadBancaria).strip()
        strTipo = str(strTipoCuenta).strip()

        if strNum == "":
            return "El número o código de cuenta no puede estar vacío."
        if persona.buscarCuenta(strNum) is not None:
            return f"Ya tienes registrada la cuenta {strNum}."
        if strEntidad == "":
            return "Indique la entidad financiera u origen de los fondos."
        if strTipo not in CuentaBancaria.LISTA_TIPOS_CUENTA:
            return "El tipo de cuenta debe ser Ahorros, Corriente o Efectivo."

        dblSaldo = self.__convertirMontoConNegativo(strSaldoInicial)
        if dblSaldo is None:
            return "El saldo inicial debe ser un valor numérico válido."

        cuenta = CuentaBancaria(strNum, strEntidad, strTipo, dblSaldo)
        persona.agregarCuenta(cuenta)
        DatosFinanzas.guardarCuentaBancaria(
            strNum, persona.getStrDocumento(), strEntidad, strTipo, dblSaldo
        )
        return None

    def eliminarCuentaBancaria(self, persona, strNumeroCuenta):
        if persona is None:
            return "Primero elija una persona."
        if len(persona.getListaCuentas()) <= 1:
            return "Debe mantener al menos una fuente de dinero activa."
        if not persona.eliminarCuenta(strNumeroCuenta):
            return "No se encontró la cuenta bancaria indicada."
        DatosFinanzas.eliminarCuentaBancaria(strNumeroCuenta, persona.getStrDocumento())
        return None

    # =========================================================================
    #  RF-03: CATEGORÍAS DINÁMICAS Y MOVIMIENTOS (Con sobregiro advertido)
    # =========================================================================

    def crearCategoriaPersonalizada(self, persona, strNombreCategoria, strTipoMovimiento, strLimiteSugerido="0"):
        if persona is None:
            return "Primero elija una persona."
        strNombre = str(strNombreCategoria).strip()
        strTipo = str(strTipoMovimiento).strip()
        if strNombre == "":
            return "El nombre de la categoría no puede estar vacío."
        if strTipo not in (Movimiento.STR_TIPO_INGRESO, Movimiento.STR_TIPO_GASTO):
            return "El tipo de categoría debe ser Ingreso o Gasto."

        existentes = [c.lower() for c in persona.obtenerNombresCategorias(strTipo)]
        if strNombre.lower() in existentes:
            return f"La categoría '{strNombre}' ya existe para {strTipo.lower()}s."

        dblLimiteSug = 0.0
        if str(strLimiteSugerido).strip() not in ("", "0"):
            dblLimiteSug = self.__convertirMonto(strLimiteSugerido)
            if dblLimiteSug is None or dblLimiteSug < 0:
                return "El límite sugerido debe ser un número mayor o igual a cero."

        intIdCat = DatosFinanzas.generarIdCategoria()
        nuevaCat = Categoria(intIdCat, strNombre, strTipo, dblLimiteSug)
        persona.agregarCategoriaPersonalizada(nuevaCat)
        DatosFinanzas.guardarCategoria(
            intIdCat, persona.getStrDocumento(), strNombre, strTipo, dblLimiteSug
        )

        # Si es categoría de gasto y definió un límite sugerido > 0, crea presupuesto automáticamente
        if strTipo == Movimiento.STR_TIPO_GASTO and dblLimiteSug > 0:
            self.definirPresupuestoCompleto(persona, strNombre, dblLimiteSug, self.obtenerMesActual(), 85.0)

        return None

    def modificarCategoriaPersonalizada(self, persona, intIdCategoria, strNuevoNombre, strLimiteSugerido="0"):
        if persona is None:
            return "Primero elija una persona."
        cat = persona.buscarCategoriaPorId(intIdCategoria)
        if cat is None:
            return "Solo se pueden editar categorías personalizadas creadas por el usuario."

        strNombre = str(strNuevoNombre).strip()
        if strNombre == "":
            return "El nuevo nombre no puede estar vacío."

        dblLimiteSug = self.__convertirMonto(strLimiteSugerido) if str(strLimiteSugerido).strip() not in ("", "0") else 0.0
        if dblLimiteSug is None or dblLimiteSug < 0:
            return "El límite sugerido no es válido."

        cat.modificarCategoria(strNombre, dblLimiteSug)
        DatosFinanzas.guardarCategoria(
            cat.getIntIdCategoria(),
            persona.getStrDocumento(),
            cat.getStrNombreCategoria(),
            cat.getStrTipoMovimiento(),
            cat.getDblLimiteSugerido(),
        )
        return None

    def eliminarCategoriaPersonalizada(self, persona, intIdCategoria):
        if persona is None:
            return "Primero elija una persona."
        if not persona.eliminarCategoriaPersonalizada(intIdCategoria):
            return "Categoría personalizada no encontrada."
        DatosFinanzas.eliminarCategoria(intIdCategoria, persona.getStrDocumento())
        return None

    def registrarMovimiento(self, persona, strTipo, strDescripcion, strMonto, strCategoria, strFecha):
        """Interfaz clásica retrocompatible: devuelve None si fue exitoso o mensaje de error."""
        strError, _strAdvertencia, _mov = self.registrarMovimientoCompleto(
            persona, strTipo, strDescripcion, strMonto, strCategoria, strFecha, ""
        )
        return strError

    def registrarMovimientoCompleto(
        self,
        persona,
        strTipo,
        strDescripcion,
        strMonto,
        strCategoria,
        strFecha,
        strNumeroCuenta="",
    ):
        """
        Registra un movimiento validando categorías dinámicas y actualizando el saldo
        de la CuentaBancaria asociada. Si un gasto supera los fondos disponibles,
        permite el sobregiro (saldo negativo) y retorna una advertencia visual clara.
        Retorna: (strError, strAdvertencia, objMovimiento)
        """
        if persona is None:
            return "Primero elija una persona.", None, None

        strDescripcion = str(strDescripcion).strip()
        strFecha = str(strFecha).strip()
        strTipo = str(strTipo).strip()
        strCategoria = str(strCategoria).strip()
        strNumeroCuenta = str(strNumeroCuenta or "").strip()

        if strTipo not in (Movimiento.STR_TIPO_INGRESO, Movimiento.STR_TIPO_GASTO):
            return "El tipo debe ser Ingreso o Gasto.", None, None

        listaCategoriasValidas = persona.obtenerNombresCategorias(strTipo)
        if strCategoria not in listaCategoriasValidas:
            return f"Elija una categoría válida de {strTipo.lower()}.", None, None

        if strDescripcion == "":
            return "La descripción no puede estar vacía.", None, None

        dblMonto = self.__convertirMonto(strMonto)
        if dblMonto is None or dblMonto <= 0:
            return "El monto debe ser un número mayor que cero.", None, None

        if not self.__esFechaValida(strFecha):
            return "La fecha debe tener el formato AAAA-MM-DD, por ejemplo 2026-11-05.", None, None

        # Selección de cuenta bancaria (usa la indicada o la cuenta principal si no se especificó)
        cuentaAsociada = None
        if strNumeroCuenta != "":
            cuentaAsociada = persona.buscarCuenta(strNumeroCuenta)
            if cuentaAsociada is None:
                return f"La cuenta bancaria '{strNumeroCuenta}' no existe.", None, None
        else:
            cuentaAsociada = persona.obtenerCuentaPrincipal()
            if cuentaAsociada is not None:
                strNumeroCuenta = cuentaAsociada.getStrNumeroCuenta()

        strAdvertencia = None
        if cuentaAsociada is not None:
            if strTipo == Movimiento.STR_TIPO_GASTO and not cuentaAsociada.verificarDisponibilidad(dblMonto):
                dblSaldoPrevio = cuentaAsociada.getDblSaldoActual()
                dblSaldoResultante = dblSaldoPrevio - dblMonto
                strSaldoResTxt = "-$" + f"{abs(dblSaldoResultante):,.0f}".replace(",", ".")
                strAdvertencia = (
                    f"Advertencia de sobregiro: la cuenta {cuentaAsociada.getStrEntidadBancaria()} "
                    f"({cuentaAsociada.getStrNumeroCuenta()}) no tenía fondos suficientes y quedó en {strSaldoResTxt}."
                )

        intId = DatosFinanzas.generarIdMovimiento()
        movimiento = Movimiento(
            intId, strTipo, strDescripcion, dblMonto, strCategoria, strFecha, strNumeroCuenta
        )
        persona.agregarMovimiento(movimiento)
        DatosFinanzas.guardarMovimiento(
            intId,
            persona.getStrDocumento(),
            strTipo,
            strDescripcion,
            dblMonto,
            strCategoria,
            strFecha,
            strNumeroCuenta,
        )

        if cuentaAsociada is not None:
            movimiento.actualizarSaldoCuenta(cuentaAsociada)
            DatosFinanzas.actualizarSaldoCuenta(
                cuentaAsociada.getStrNumeroCuenta(),
                persona.getStrDocumento(),
                cuentaAsociada.getDblSaldoActual(),
            )

        return None, strAdvertencia, movimiento

    def eliminarMovimiento(self, persona, intId):
        """Elimina/anula la transacción y revierte el impacto en la cuenta bancaria asociada."""
        if persona is None:
            return "Primero elija una persona."
        movimiento = persona.buscarMovimiento(intId)
        if movimiento is None:
            return "No se encontró el movimiento."

        strNumCuenta = movimiento.getStrNumeroCuenta()
        persona.eliminarMovimiento(intId)
        DatosFinanzas.eliminarMovimiento(intId)

        if strNumCuenta:
            cuenta = persona.buscarCuenta(strNumCuenta)
            if cuenta is not None:
                movimiento.revertirSaldoCuenta(cuenta)
                DatosFinanzas.actualizarSaldoCuenta(
                    cuenta.getStrNumeroCuenta(),
                    persona.getStrDocumento(),
                    cuenta.getDblSaldoActual(),
                )
        return None

    # =========================================================================
    #  RF-04: PRESUPUESTOS Y ALERTAS PREVENTIVAS (Umbral 85% por defecto)
    # =========================================================================

    def definirPresupuesto(self, persona, strCategoria, strLimite):
        """Interfaz clásica retrocompatible."""
        return self.definirPresupuestoCompleto(
            persona, strCategoria, strLimite, self.obtenerMesActual(), 85.0
        )

    def definirPresupuestoCompleto(
        self,
        persona,
        strCategoria,
        strLimite,
        strPeriodoMesAno="Todos",
        dblPorcentajeAlerta=85.0,
    ):
        if persona is None:
            return "Primero elija una persona."

        listaGastosValidas = persona.obtenerNombresCategorias(Movimiento.STR_TIPO_GASTO)
        if strCategoria not in listaGastosValidas:
            return "Elija una categoría válida de gasto."

        dblLimite = self.__convertirMonto(strLimite)
        if dblLimite is None or dblLimite <= 0:
            return "El límite presupuestal debe ser un número mayor que cero."

        try:
            dblUmbral = float(dblPorcentajeAlerta)
            if dblUmbral < 10 or dblUmbral > 100:
                return "El porcentaje de alerta debe estar entre 10% y 100%."
        except (TypeError, ValueError):
            dblUmbral = 85.0

        persona.definirPresupuesto(strCategoria, dblLimite, strPeriodoMesAno, dblUmbral)
        DatosFinanzas.guardarPresupuesto(
            persona.getStrDocumento(), strCategoria, dblLimite, strPeriodoMesAno, dblUmbral
        )
        return None

    def eliminarPresupuesto(self, persona, strCategoria):
        if persona is None:
            return "Primero elija una persona."
        if not persona.eliminarPresupuesto(strCategoria):
            return "No se encontró el presupuesto indicado."
        DatosFinanzas.eliminarPresupuesto(persona.getStrDocumento(), strCategoria)
        return None

    # =========================================================================
    #  RF-05: METAS DE AHORRO Y ABONOS PROGRESIVOS
    # =========================================================================

    def crearMetaAhorro(self, persona, strNombreMeta, strMontoObjetivo, strFechaLimite, strAbonoInicial="0"):
        if persona is None:
            return "Primero elija una persona.", None

        strNombre = str(strNombreMeta).strip()
        strFecha = str(strFechaLimite).strip()
        if strNombre == "":
            return "El nombre o propósito de la meta no puede estar vacío.", None

        dblObjetivo = self.__convertirMonto(strMontoObjetivo)
        if dblObjetivo is None or dblObjetivo <= 0:
            return "El monto objetivo debe ser mayor que cero.", None

        dblInicial = 0.0
        if str(strAbonoInicial).strip() not in ("", "0"):
            dblInicial = self.__convertirMonto(strAbonoInicial)
            if dblInicial is None or dblInicial < 0:
                return "El abono inicial debe ser mayor o igual a cero.", None

        if not self.__esFechaValida(strFecha):
            return "La fecha límite debe tener formato AAAA-MM-DD.", None

        intIdMeta = DatosFinanzas.generarIdMetaAhorro()
        strHoy = self.obtenerFechaActual()
        meta = MetaAhorro(intIdMeta, strNombre, dblObjetivo, dblInicial, strFecha, strHoy)
        persona.agregarMetaAhorro(meta)
        DatosFinanzas.guardarMetaAhorro(
            intIdMeta, persona.getStrDocumento(), strNombre, dblObjetivo, dblInicial, strFecha, strHoy
        )
        return None, meta

    def abonarCapitalMeta(self, persona, intIdMeta, strMontoAbono, strNumeroCuenta=""):
        """
        Registra un abono a una meta de ahorro y opcionalmente descuenta el valor
        de una CuentaBancaria (permitiendo sobregiro con advertencia visual).
        Retorna: (strError, strAdvertencia, objMeta)
        """
        if persona is None:
            return "Primero elija una persona.", None, None

        meta = persona.buscarMetaAhorro(intIdMeta)
        if meta is None:
            return "No se encontró la meta de ahorro seleccionada.", None, None

        dblAbono = self.__convertirMonto(strMontoAbono)
        if dblAbono is None or dblAbono <= 0:
            return "El monto del abono debe ser mayor que cero.", None, None

        strAdvertencia = None
        strNumCta = str(strNumeroCuenta or "").strip()
        if strNumCta != "":
            cuenta = persona.buscarCuenta(strNumCta)
            if cuenta is None:
                return "La cuenta origen seleccionada no existe.", None, None
            if not cuenta.verificarDisponibilidad(dblAbono):
                dblNuevoSaldo = cuenta.getDblSaldoActual() - dblAbono
                strSaldoTxt = "-$" + f"{abs(dblNuevoSaldo):,.0f}".replace(",", ".")
                strAdvertencia = (
                    f"Advertencia de sobregiro: el abono dejó la cuenta "
                    f"{cuenta.getStrEntidadBancaria()} en {strSaldoTxt}."
                )
            cuenta.debitarSaldo(dblAbono)
            DatosFinanzas.actualizarSaldoCuenta(
                cuenta.getStrNumeroCuenta(), persona.getStrDocumento(), cuenta.getDblSaldoActual()
            )

        meta.abonarCapital(dblAbono)
        DatosFinanzas.actualizarAcumuladoMeta(
            meta.getIntIdMeta(), persona.getStrDocumento(), meta.getDblMontoAcumulado()
        )
        return None, strAdvertencia, meta

    def eliminarMetaAhorro(self, persona, intIdMeta):
        if persona is None:
            return "Primero elija una persona."
        if not persona.eliminarMetaAhorro(intIdMeta):
            return "No se encontró la meta de ahorro."
        DatosFinanzas.eliminarMetaAhorro(intIdMeta, persona.getStrDocumento())
        return None

    # =========================================================================
    #  RF-06: REPORTES Y ESTADÍSTICAS CONSOLIDADAS
    # =========================================================================

    def obtenerDashboardResumen(self, persona, strMes="Todos"):
        """Consolida KPIs, alertas RF-04, cuentas, metas y series para gráficas."""
        dblIngresos = persona.calcularTotalIngresos(strMes)
        dblGastos = persona.calcularTotalGastos(strMes)
        dblSaldoPeriodo = persona.calcularSaldo(strMes)
        dblPorcentajeAhorro = persona.calcularPorcentajeAhorro(strMes)
        dblPatrimonioCuentas = persona.calcularSaldoTotalCuentas()

        # Serie histórica de los últimos meses registrados
        mesesOrdenados = sorted(persona.obtenerMeses())
        serieMensual = []
        for m in mesesOrdenados[-6:]:
            serieMensual.append(
                {
                    "strMes": m,
                    "dblIngresos": round(persona.calcularTotalIngresos(m), 2),
                    "dblGastos": round(persona.calcularTotalGastos(m), 2),
                    "dblBalance": round(persona.calcularSaldo(m), 2),
                }
            )

        dicGastosCat = persona.calcularGastosPorCategoria(strMes)
        listaGastosCat = [
            {"strCategoria": k, "dblTotal": round(v, 2)} for k, v in dicGastosCat.items()
        ]

        return {
            "strMesConsultado": strMes,
            "listaMesesDisponibles": persona.obtenerMeses(),
            "kpis": {
                "dblPatrimonioCuentas": round(dblPatrimonioCuentas, 2),
                "dblIngresosPeriodo": round(dblIngresos, 2),
                "dblGastosPeriodo": round(dblGastos, 2),
                "dblBalancePeriodo": round(dblSaldoPeriodo, 2),
                "dblPorcentajeAhorro": round(dblPorcentajeAhorro, 1),
            },
            "alertas": persona.obtenerAlertasDetalladas(strMes),
            "cuentas": [c.toDict() for c in persona.getListaCuentas()],
            "presupuestos": [
                p.toDict(persona.getListaMovimientos(), strMes)
                for p in persona.getListaPresupuestos()
            ],
            "metasAhorro": [m.toDict() for m in persona.getListaMetasAhorro()],
            "ultimosMovimientos": [
                m.toDict() for m in persona.consultarMovimientos("Todos", strMes)[:8]
            ],
            "graficas": {
                "serieMensual": serieMensual,
                "gastosPorCategoria": listaGastosCat,
            },
        }

    # ---- Utilidades ----------------------------------------------------------
    def obtenerMesActual(self):
        """El mes de hoy en formato AAAA-MM."""
        return date.today().strftime("%Y-%m")

    def obtenerFechaActual(self):
        """La fecha de hoy en formato AAAA-MM-DD."""
        return date.today().strftime("%Y-%m-%d")

    def __convertirMonto(self, strMonto):
        """Convierte '1.250.000', '$ 1250000' o '1250000,50' en número. None si no es un número."""
        if isinstance(strMonto, (int, float)):
            return float(strMonto)
        strTexto = str(strMonto).replace("$", "").replace(" ", "").strip()
        if "," in strTexto and "." in strTexto:
            strLimpio = strTexto.replace(".", "").replace(",", ".")
        elif "," in strTexto:
            strLimpio = strTexto.replace(",", ".")
        elif strTexto.count(".") > 1:
            strLimpio = strTexto.replace(".", "")
        else:
            # Si tiene un solo punto con 3 dígitos exactos al final (ej: 600.000), se interpreta como miles COP
            partes = strTexto.split(".")
            if len(partes) == 2 and len(partes[1]) == 3 and partes[0].lstrip("-").isdigit():
                strLimpio = strTexto.replace(".", "")
            else:
                strLimpio = strTexto
        try:
            return float(strLimpio)
        except ValueError:
            return None

    def __convertirMontoConNegativo(self, strMonto):
        """Igual que __convertirMonto, permitiendo saldos iniciales negativos o cero."""
        return self.__convertirMonto(strMonto)

    def __esFechaValida(self, strFecha):
        try:
            datetime.strptime(strFecha, "%Y-%m-%d")
            return len(strFecha) == 10
        except ValueError:
            return False
