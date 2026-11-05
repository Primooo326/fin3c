# =============================================================================
#  Aplicación FastAPI: Servicio Web REST + SPA Responsiva (RF-01 a RF-06)
#  Universidad ECCI — Facultad de Ingeniería — Subequipo 3B
#  Capa: SERVICIO_WEB
# =============================================================================

from pathlib import Path
from typing import Optional
from urllib.parse import unquote

from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import io

from LOGICA.GestorFinanzas import GestorFinanzas
from LOGICA.Persona import Persona
from SERVICIO_WEB.dependencias import (
    INT_DURACION_SESION_SEG,
    generarTokenSesion,
    obtenerGestor,
    obtenerPersonaActual,
)

RUTA_STATIC = Path(__file__).resolve().parent / "static"

app = FastAPI(
    title="API Gestión de Finanzas Personales — Universidad ECCI",
    description=(
        "Capa de Servicio Web construida sobre el modelo de dominio POO (`LOGICA`) y "
        "persistencia relacional ACID en PostgreSQL (`PERSISTENCIA`). "
        "Proyecto Integrador PyA 2ANL 2026-2 — Equipo 3 Subequipo B."
    ),
    version="2.0.0",
)

app.mount("/static", StaticFiles(directory=str(RUTA_STATIC)), name="static")


# =============================================================================
#  Esquemas de Entrada Pydantic (Validación de Peticiones REST)
# =============================================================================

class RegistroUsuarioReq(BaseModel):
    strDocumento: str = Field(..., examples=["1023948571"], description="Documento de identidad numérico")
    strNombre: str = Field(..., examples=["Camila Rodríguez"], description="Nombre completo del titular")
    strCorreo: str = Field(..., examples=["camila@ecci.edu.co"], description="Correo electrónico único")
    strPassword: str = Field(..., min_length=6, examples=["ClaveSegura2026*"], description="Contraseña en texto plano (se cifra con PBKDF2-SHA256)")


class LoginUsuarioReq(BaseModel):
    strIdentificador: str = Field(..., examples=["juan.morales@ecci.edu.co"], description="Correo electrónico o documento")
    strPassword: str = Field(..., examples=["Demo2026*"])


class ActualizarPerfilReq(BaseModel):
    strNombre: str
    strCorreo: str
    strNuevaPassword: Optional[str] = ""


class CuentaBancariaReq(BaseModel):
    strNumeroCuenta: str = Field(..., examples=["4589-2030-9911"])
    strEntidadBancaria: str = Field(..., examples=["Bancolombia"])
    strTipoCuenta: str = Field(..., examples=["Ahorros"], description="Ahorros, Corriente o Efectivo")
    strSaldoInicial: str = Field(default="0", examples=["1500000"])


class CategoriaReq(BaseModel):
    strNombreCategoria: str = Field(..., examples=["Gimnasio y Bienestar"])
    strTipoMovimiento: str = Field(..., examples=["Gasto"], description="Ingreso o Gasto")
    strLimiteSugerido: str = Field(default="0", examples=["180000"])


class ModificarCategoriaReq(BaseModel):
    strNuevoNombre: str
    strLimiteSugerido: str = "0"


class MovimientoReq(BaseModel):
    strTipo: str = Field(..., examples=["Gasto"], description="Ingreso o Gasto")
    strDescripcion: str = Field(..., examples=["Compra supermercado mensual"])
    strMonto: str = Field(..., examples=["245000"])
    strCategoria: str = Field(..., examples=["Alimentación"])
    strFecha: str = Field(..., examples=["2026-11-05"])
    strNumeroCuenta: Optional[str] = Field(default="", examples=["4589-1029-3301"])


class PresupuestoReq(BaseModel):
    strCategoria: str = Field(..., examples=["Alimentación"])
    strLimite: str = Field(..., examples=["650000"])
    strPeriodoMesAno: str = Field(default="Todos", examples=["2026-11"])
    dblPorcentajeAlerta: float = Field(default=85.0, examples=[85.0])


class MetaAhorroReq(BaseModel):
    strNombreMeta: str = Field(..., examples=["Fondo Especialización"])
    strMontoObjetivo: str = Field(..., examples=["5000000"])
    strFechaLimite: str = Field(..., examples=["2027-06-30"])
    strAbonoInicial: str = Field(default="0", examples=["500000"])


class AbonoMetaReq(BaseModel):
    strMontoAbono: str = Field(..., examples=["250000"])
    strNumeroCuenta: Optional[str] = Field(default="", description="Cuenta origen opcional para debitar el abono")


# =============================================================================
#  Ruta Raíz (Aplicación Web Responsiva SPA) y Estado de Salud
# =============================================================================

@app.get("/", include_in_schema=False)
def servirInterfazWeb():
    return FileResponse(str(RUTA_STATIC / "index.html"))


@app.get("/api/salud", tags=["Infraestructura"])
def consultarSaludSistema():
    gestor = GestorFinanzas.getInstancia()
    estadoBD = gestor.getEstadoPersistencia()
    cuentasDemo = []
    if estadoBD["boolDatosCargados"]:
        for p in gestor.getListaPersonas()[:3]:
            cuentasDemo.append(
                {
                    "strDocumento": p.getStrDocumento(),
                    "strNombre": p.getStrNombre(),
                    "strCorreo": p.getStrCorreo(),
                }
            )
    return {
        "strSistema": "Software de Finanzas Personales — ECCI Subequipo 3B",
        "strMesActual": gestor.obtenerMesActual(),
        "strFechaActual": gestor.obtenerFechaActual(),
        "persistencia": estadoBD,
        "usuariosDemo": cuentasDemo,
    }


# =============================================================================
#  RF-01 & RNF-01: Autenticación y Gestión de Usuarios
# =============================================================================

def _fijarCookieSesion(response: Response, strToken: str):
    response.set_cookie(
        key="finanzas_token",
        value=strToken,
        max_age=INT_DURACION_SESION_SEG,
        httponly=True,
        samesite="lax",
    )


@app.post("/api/auth/registro", tags=["RF-01 Usuarios y Seguridad"], status_code=status.HTTP_201_CREATED)
def registrarUsuario(
    datos: RegistroUsuarioReq,
    response: Response,
    gestor: GestorFinanzas = Depends(obtenerGestor),
):
    strError = gestor.registrarPersona(
        datos.strDocumento, datos.strNombre, datos.strCorreo, datos.strPassword
    )
    if strError is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=strError)

    persona = gestor.buscarPersona(datos.strDocumento)
    strToken = generarTokenSesion(persona.getStrDocumento())
    _fijarCookieSesion(response, strToken)
    return {
        "strMensaje": "Cuenta creada exitosamente con cifrado PBKDF2-SHA256.",
        "strToken": strToken,
        "usuario": persona.toDictPerfil(),
    }


@app.post("/api/auth/login", tags=["RF-01 Usuarios y Seguridad"])
def iniciarSesion(
    datos: LoginUsuarioReq,
    response: Response,
    gestor: GestorFinanzas = Depends(obtenerGestor),
):
    persona, strError = gestor.autenticarUsuario(datos.strIdentificador, datos.strPassword)
    if strError is not None or persona is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=strError)

    strToken = generarTokenSesion(persona.getStrDocumento())
    _fijarCookieSesion(response, strToken)
    return {
        "strMensaje": f"Bienvenido(a), {persona.getStrNombre()}.",
        "strToken": strToken,
        "usuario": persona.toDictPerfil(),
    }


@app.post("/api/auth/logout", tags=["RF-01 Usuarios y Seguridad"])
def cerrarSesion(response: Response):
    response.delete_cookie("finanzas_token")
    return {"strMensaje": "Sesión cerrada correctamente."}


@app.get("/api/auth/perfil", tags=["RF-01 Usuarios y Seguridad"])
def consultarPerfil(persona: Persona = Depends(obtenerPersonaActual)):
    return {"usuario": persona.toDictPerfil()}


@app.put("/api/auth/perfil", tags=["RF-01 Usuarios y Seguridad"])
def actualizarPerfil(
    datos: ActualizarPerfilReq,
    persona: Persona = Depends(obtenerPersonaActual),
    gestor: GestorFinanzas = Depends(obtenerGestor),
):
    strError = gestor.actualizarPerfilPersona(
        persona, datos.strNombre, datos.strCorreo, datos.strNuevaPassword or ""
    )
    if strError is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=strError)
    return {
        "strMensaje": "Datos personales actualizados correctamente.",
        "usuario": persona.toDictPerfil(),
    }


# =============================================================================
#  Dashboard Ejecutivo Consolidado
# =============================================================================

@app.get("/api/dashboard", tags=["Dashboard y Analítica"])
def obtenerDashboard(
    mes: str = Query(default="Todos", description="Periodo AAAA-MM o 'Todos'"),
    persona: Persona = Depends(obtenerPersonaActual),
    gestor: GestorFinanzas = Depends(obtenerGestor),
):
    return gestor.obtenerDashboardResumen(persona, mes)


# =============================================================================
#  RF-02: Cuentas Bancarias
# =============================================================================

@app.get("/api/cuentas", tags=["RF-02 Cuentas Bancarias"])
def listarCuentas(persona: Persona = Depends(obtenerPersonaActual)):
    return {
        "dblSaldoConsolidado": round(persona.calcularSaldoTotalCuentas(), 2),
        "cuentas": [c.toDict() for c in persona.getListaCuentas()],
    }


@app.post("/api/cuentas", tags=["RF-02 Cuentas Bancarias"], status_code=status.HTTP_201_CREATED)
def crearCuentaBancaria(
    datos: CuentaBancariaReq,
    persona: Persona = Depends(obtenerPersonaActual),
    gestor: GestorFinanzas = Depends(obtenerGestor),
):
    strError = gestor.registrarCuentaBancaria(
        persona,
        datos.strNumeroCuenta,
        datos.strEntidadBancaria,
        datos.strTipoCuenta,
        datos.strSaldoInicial,
    )
    if strError is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=strError)
    return {
        "strMensaje": "Cuenta bancaria registrada correctamente.",
        "cuenta": persona.buscarCuenta(datos.strNumeroCuenta.strip()).toDict(),
    }


@app.delete("/api/cuentas/{strNumeroCuenta}", tags=["RF-02 Cuentas Bancarias"])
def eliminarCuentaBancaria(
    strNumeroCuenta: str,
    persona: Persona = Depends(obtenerPersonaActual),
    gestor: GestorFinanzas = Depends(obtenerGestor),
):
    strError = gestor.eliminarCuentaBancaria(persona, unquote(strNumeroCuenta))
    if strError is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=strError)
    return {"strMensaje": "Cuenta bancaria eliminada."}


# =============================================================================
#  RF-03: Categorías Dinámicas y Movimientos (Transacciones)
# =============================================================================

@app.get("/api/categorias", tags=["RF-03 Movimientos y Categorías"])
def listarCategorias(persona: Persona = Depends(obtenerPersonaActual)):
    return {
        "ingresos": persona.obtenerNombresCategorias("Ingreso"),
        "gastos": persona.obtenerNombresCategorias("Gasto"),
        "catalogo": persona.obtenerCatalogoCategorias(),
    }


@app.post("/api/categorias", tags=["RF-03 Movimientos y Categorías"], status_code=status.HTTP_201_CREATED)
def crearCategoria(
    datos: CategoriaReq,
    persona: Persona = Depends(obtenerPersonaActual),
    gestor: GestorFinanzas = Depends(obtenerGestor),
):
    strError = gestor.crearCategoriaPersonalizada(
        persona, datos.strNombreCategoria, datos.strTipoMovimiento, datos.strLimiteSugerido
    )
    if strError is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=strError)
    return {
        "strMensaje": "Categoría personalizada creada exitosamente.",
        "catalogo": persona.obtenerCatalogoCategorias(),
    }


@app.put("/api/categorias/{intIdCategoria}", tags=["RF-03 Movimientos y Categorías"])
def editarCategoria(
    intIdCategoria: int,
    datos: ModificarCategoriaReq,
    persona: Persona = Depends(obtenerPersonaActual),
    gestor: GestorFinanzas = Depends(obtenerGestor),
):
    strError = gestor.modificarCategoriaPersonalizada(
        persona, intIdCategoria, datos.strNuevoNombre, datos.strLimiteSugerido
    )
    if strError is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=strError)
    return {"strMensaje": "Categoría actualizada."}


@app.delete("/api/categorias/{intIdCategoria}", tags=["RF-03 Movimientos y Categorías"])
def borrarCategoria(
    intIdCategoria: int,
    persona: Persona = Depends(obtenerPersonaActual),
    gestor: GestorFinanzas = Depends(obtenerGestor),
):
    strError = gestor.eliminarCategoriaPersonalizada(persona, intIdCategoria)
    if strError is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=strError)
    return {"strMensaje": "Categoría personalizada eliminada."}


@app.get("/api/movimientos", tags=["RF-03 Movimientos y Categorías"])
def listarMovimientos(
    tipo: str = Query(default="Todos"),
    mes: str = Query(default="Todos"),
    categoria: str = Query(default="Todos"),
    cuenta: str = Query(default="Todos"),
    persona: Persona = Depends(obtenerPersonaActual),
):
    movs = persona.consultarMovimientos(tipo, mes, categoria, cuenta)
    dblIng = sum(m.getDblMonto() for m in movs if m.esIngreso())
    dblGas = sum(m.getDblMonto() for m in movs if not m.esIngreso())
    return {
        "intTotalRegistros": len(movs),
        "dblSumaIngresos": round(dblIng, 2),
        "dblSumaGastos": round(dblGas, 2),
        "dblBalanceFiltro": round(dblIng - dblGas, 2),
        "movimientos": [m.toDict() for m in movs],
    }


@app.post("/api/movimientos", tags=["RF-03 Movimientos y Categorías"], status_code=status.HTTP_201_CREATED)
def registrarMovimiento(
    datos: MovimientoReq,
    persona: Persona = Depends(obtenerPersonaActual),
    gestor: GestorFinanzas = Depends(obtenerGestor),
):
    strError, strAdvertencia, mov = gestor.registrarMovimientoCompleto(
        persona,
        datos.strTipo,
        datos.strDescripcion,
        datos.strMonto,
        datos.strCategoria,
        datos.strFecha,
        datos.strNumeroCuenta or "",
    )
    if strError is not None or mov is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=strError)

    return {
        "strMensaje": "Transacción procesada y saldo de cuenta actualizado.",
        "strAdvertencia": strAdvertencia,
        "movimiento": mov.toDict(),
        "alertasActivas": persona.obtenerAlertasDetalladas(mov.obtenerMes()),
    }


@app.delete("/api/movimientos/{intId}", tags=["RF-03 Movimientos y Categorías"])
def eliminarMovimiento(
    intId: int,
    persona: Persona = Depends(obtenerPersonaActual),
    gestor: GestorFinanzas = Depends(obtenerGestor),
):
    strError = gestor.eliminarMovimiento(persona, intId)
    if strError is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=strError)
    return {"strMensaje": "Transacción anulada y saldo revertido en la cuenta asociada."}


# =============================================================================
#  RF-04: Presupuestos y Alertas (Umbral 85%)
# =============================================================================

@app.get("/api/presupuestos", tags=["RF-04 Presupuestos y Alertas"])
def listarPresupuestos(
    mes: str = Query(default="Todos"),
    persona: Persona = Depends(obtenerPersonaActual),
):
    lista = [
        p.toDict(persona.getListaMovimientos(), mes)
        for p in persona.getListaPresupuestos()
    ]
    return {
        "strMesEvaluado": mes,
        "presupuestos": lista,
        "alertas": persona.obtenerAlertasDetalladas(mes),
    }


@app.post("/api/presupuestos", tags=["RF-04 Presupuestos y Alertas"], status_code=status.HTTP_201_CREATED)
def guardarPresupuesto(
    datos: PresupuestoReq,
    persona: Persona = Depends(obtenerPersonaActual),
    gestor: GestorFinanzas = Depends(obtenerGestor),
):
    strError = gestor.definirPresupuestoCompleto(
        persona,
        datos.strCategoria,
        datos.strLimite,
        datos.strPeriodoMesAno,
        datos.dblPorcentajeAlerta,
    )
    if strError is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=strError)
    return {"strMensaje": f"Presupuesto para '{datos.strCategoria}' guardado exitosamente."}


@app.delete("/api/presupuestos/{strCategoria}", tags=["RF-04 Presupuestos y Alertas"])
def borrarPresupuesto(
    strCategoria: str,
    persona: Persona = Depends(obtenerPersonaActual),
    gestor: GestorFinanzas = Depends(obtenerGestor),
):
    strError = gestor.eliminarPresupuesto(persona, unquote(strCategoria))
    if strError is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=strError)
    return {"strMensaje": "Presupuesto eliminado."}


# =============================================================================
#  RF-05: Metas de Ahorro y Abonos Progresivos
# =============================================================================

@app.get("/api/metas", tags=["RF-05 Metas de Ahorro"])
def listarMetasAhorro(persona: Persona = Depends(obtenerPersonaActual)):
    metas = [m.toDict() for m in persona.getListaMetasAhorro()]
    dblTotalObj = sum(m["dblMontoObjetivo"] for m in metas)
    dblTotalAcum = sum(m["dblMontoAcumulado"] for m in metas)
    return {
        "dblTotalObjetivo": round(dblTotalObj, 2),
        "dblTotalAcumulado": round(dblTotalAcum, 2),
        "metas": metas,
    }


@app.post("/api/metas", tags=["RF-05 Metas de Ahorro"], status_code=status.HTTP_201_CREATED)
def crearMeta(
    datos: MetaAhorroReq,
    persona: Persona = Depends(obtenerPersonaActual),
    gestor: GestorFinanzas = Depends(obtenerGestor),
):
    strError, meta = gestor.crearMetaAhorro(
        persona,
        datos.strNombreMeta,
        datos.strMontoObjetivo,
        datos.strFechaLimite,
        datos.strAbonoInicial,
    )
    if strError is not None or meta is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=strError)
    return {"strMensaje": "Meta de ahorro creada exitosamente.", "meta": meta.toDict()}


@app.post("/api/metas/{intIdMeta}/abonar", tags=["RF-05 Metas de Ahorro"])
def abonarMeta(
    intIdMeta: int,
    datos: AbonoMetaReq,
    persona: Persona = Depends(obtenerPersonaActual),
    gestor: GestorFinanzas = Depends(obtenerGestor),
):
    strError, strAdvertencia, meta = gestor.abonarCapitalMeta(
        persona, intIdMeta, datos.strMontoAbono, datos.strNumeroCuenta or ""
    )
    if strError is not None or meta is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=strError)
    return {
        "strMensaje": "Abono registrado en tu meta de ahorro.",
        "strAdvertencia": strAdvertencia,
        "meta": meta.toDict(),
    }


@app.delete("/api/metas/{intIdMeta}", tags=["RF-05 Metas de Ahorro"])
def borrarMeta(
    intIdMeta: int,
    persona: Persona = Depends(obtenerPersonaActual),
    gestor: GestorFinanzas = Depends(obtenerGestor),
):
    strError = gestor.eliminarMetaAhorro(persona, intIdMeta)
    if strError is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=strError)
    return {"strMensaje": "Meta de ahorro eliminada."}


# =============================================================================
#  RF-06: Reportes Consolidados y Exportación a PDF / Excel
# =============================================================================

@app.get("/api/reportes", tags=["RF-06 Reportes y Estadísticas"])
def consultarReporteRango(
    fechaInicio: str = Query(default="", description="Fecha inicial AAAA-MM-DD"),
    fechaFin: str = Query(default="", description="Fecha final AAAA-MM-DD"),
    persona: Persona = Depends(obtenerPersonaActual),
):
    reporte = persona.generarReporte(fechaInicio, fechaFin)
    return reporte.generarGraficoConsolidado()


@app.get("/api/reportes/pdf", tags=["RF-06 Reportes y Estadísticas"])
def descargarReportePDF(
    fechaInicio: str = Query(default=""),
    fechaFin: str = Query(default=""),
    persona: Persona = Depends(obtenerPersonaActual),
):
    reporte = persona.generarReporte(fechaInicio, fechaFin)
    bytesPdf = reporte.generarBytesPDF()
    nombreArchivo = f"Reporte_Financiero_{persona.getStrDocumento()}.pdf"
    return StreamingResponse(
        io.BytesIO(bytesPdf),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{nombreArchivo}"'},
    )


@app.get("/api/reportes/excel", tags=["RF-06 Reportes y Estadísticas"])
def descargarReporteExcel(
    fechaInicio: str = Query(default=""),
    fechaFin: str = Query(default=""),
    persona: Persona = Depends(obtenerPersonaActual),
):
    reporte = persona.generarReporte(fechaInicio, fechaFin)
    bytesXlsx = reporte.generarBytesExcel()
    nombreArchivo = f"Reporte_Financiero_{persona.getStrDocumento()}.xlsx"
    return StreamingResponse(
        io.BytesIO(bytesXlsx),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{nombreArchivo}"'},
    )
