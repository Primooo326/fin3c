# =============================================================================
#  Clase ReporteFinanciero: Consolidación, Gráficos y Exportación PDF/Excel (RF-06)
#  Modelado Orientado a Objetos (Matriz de Diseño UML - Universidad ECCI)
#  Capa: LOGICA
# =============================================================================

from datetime import datetime
import io


class ReporteFinanciero:

    # ---- Constructor ---------------------------------------------------------
    def __init__(self, strFechaInicio, strFechaFin, persona):
        self.__strFechaInicio = str(strFechaInicio).strip()
        self.__strFechaFin = str(strFechaFin).strip()
        self.__persona = persona
        self.__listaMovimientosRango = []
        self.__dblTotalIngresos = 0.0
        self.__dblTotalGastos = 0.0
        self.__dblBalanceNeto = 0.0
        self.calcularBalanceNeto()

    # ---- Cálculos Consolidados -----------------------------------------------
    def _filtrarMovimientosPorRango(self):
        listaFiltrada = []
        for mov in self.__persona.getListaMovimientos():
            strFecha = mov.getStrFecha()
            boolInicioOk = (not self.__strFechaInicio) or (strFecha >= self.__strFechaInicio)
            boolFinOk = (not self.__strFechaFin) or (strFecha <= self.__strFechaFin)
            if boolInicioOk and boolFinOk:
                listaFiltrada.append(mov)
        listaFiltrada.sort(key=lambda m: (m.getStrFecha(), m.getIntId()), reverse=True)
        return listaFiltrada

    def calcularBalanceNeto(self):
        """Calcula ingresos, gastos y balance neto dentro del rango de fechas configurado."""
        self.__listaMovimientosRango = self._filtrarMovimientosPorRango()
        self.__dblTotalIngresos = sum(
            m.getDblMonto() for m in self.__listaMovimientosRango if m.esIngreso()
        )
        self.__dblTotalGastos = sum(
            m.getDblMonto() for m in self.__listaMovimientosRango if not m.esIngreso()
        )
        self.__dblBalanceNeto = self.__dblTotalIngresos - self.__dblTotalGastos
        return self.__dblBalanceNeto

    def generarGraficoConsolidado(self):
        """
        Prepara las series consolidadas por período mensual, categoría y cuenta
        listas para renderizar comparativas visuales.
        """
        dicMensual = {}
        dicGastosCat = {}
        dicIngresosCat = {}

        for mov in self.__listaMovimientosRango:
            strMes = mov.obtenerMes()
            if strMes not in dicMensual:
                dicMensual[strMes] = {"strMes": strMes, "dblIngresos": 0.0, "dblGastos": 0.0, "dblBalance": 0.0}
            if mov.esIngreso():
                dicMensual[strMes]["dblIngresos"] += mov.getDblMonto()
                dicIngresosCat[mov.getStrCategoria()] = dicIngresosCat.get(mov.getStrCategoria(), 0.0) + mov.getDblMonto()
            else:
                dicMensual[strMes]["dblGastos"] += mov.getDblMonto()
                dicGastosCat[mov.getStrCategoria()] = dicGastosCat.get(mov.getStrCategoria(), 0.0) + mov.getDblMonto()
            dicMensual[strMes]["dblBalance"] = (
                dicMensual[strMes]["dblIngresos"] - dicMensual[strMes]["dblGastos"]
            )

        listaSerieMensual = [dicMensual[k] for k in sorted(dicMensual.keys())]
        listaGastosCat = [
            {"strCategoria": k, "dblTotal": round(v, 2)}
            for k, v in sorted(dicGastosCat.items(), key=lambda x: x[1], reverse=True)
        ]
        listaIngresosCat = [
            {"strCategoria": k, "dblTotal": round(v, 2)}
            for k, v in sorted(dicIngresosCat.items(), key=lambda x: x[1], reverse=True)
        ]

        dblTasaAhorro = (
            (self.__dblBalanceNeto * 100.0 / self.__dblTotalIngresos)
            if self.__dblTotalIngresos > 0
            else 0.0
        )

        return {
            "strFechaInicio": self.__strFechaInicio,
            "strFechaFin": self.__strFechaFin,
            "dblTotalIngresos": round(self.__dblTotalIngresos, 2),
            "dblTotalGastos": round(self.__dblTotalGastos, 2),
            "dblBalanceNeto": round(self.__dblBalanceNeto, 2),
            "dblTasaAhorro": round(dblTasaAhorro, 1),
            "intCantidadMovimientos": len(self.__listaMovimientosRango),
            "serieMensual": listaSerieMensual,
            "gastosPorCategoria": listaGastosCat,
            "ingresosPorCategoria": listaIngresosCat,
            "movimientos": [m.toDict() for m in self.__listaMovimientosRango],
        }

    # ---- Exportación a PDF (ReportLab con respaldo nativo) -------------------
    def generarBytesPDF(self):
        """Genera el documento PDF consolidado del reporte financiero en memoria."""
        buffer = io.BytesIO()
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
            from reportlab.lib.units import inch
            from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                leftMargin=0.6 * inch,
                rightMargin=0.6 * inch,
                topMargin=0.6 * inch,
                bottomMargin=0.6 * inch,
            )
            estilos = getSampleStyleSheet()
            colorBosque = colors.HexColor("#064E3B")
            colorEsmeralda = colors.HexColor("#10B981")
            colorMentaSuave = colors.HexColor("#ECFDF5")

            estiloTitulo = ParagraphStyle(
                "TituloReporte",
                parent=estilos["Heading1"],
                textColor=colorBosque,
                fontSize=17,
                spaceAfter=4,
            )
            estiloSub = ParagraphStyle(
                "SubReporte",
                parent=estilos["Normal"],
                textColor=colors.HexColor("#374151"),
                fontSize=9.5,
                spaceAfter=14,
            )
            estiloSeccion = ParagraphStyle(
                "Seccion",
                parent=estilos["Heading2"],
                textColor=colorBosque,
                fontSize=12,
                spaceBefore=12,
                spaceAfter=6,
            )

            elementos = []
            elementos.append(Paragraph("REPORTE FINANCIERO CONSOLIDADO", estiloTitulo))
            elementos.append(
                Paragraph(
                    f"<b>Titular:</b> {self.__persona.getStrNombre()} ({self.__persona.getStrDocumento()}) &nbsp;|&nbsp; "
                    f"<b>Correo:</b> {self.__persona.getStrCorreo()}<br/>"
                    f"<b>Período consultado:</b> {self.__strFechaInicio or 'Inicio'} a {self.__strFechaFin or 'Actualidad'} &nbsp;|&nbsp; "
                    f"<b>Generado:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    estiloSub,
                )
            )

            # Tabla resumen ejecutivo
            datosResumen = [
                ["INDICADOR FINANCIERO", "VALOR CONSOLIDADO (COP)"],
                ["Total Ingresos en el Rango", self._fmtMoneda(self.__dblTotalIngresos)],
                ["Total Gastos en el Rango", self._fmtMoneda(self.__dblTotalGastos)],
                ["Balance Neto del Período", self._fmtMoneda(self.__dblBalanceNeto)],
                [" Patrimonio en Cuentas Bancarias", self._fmtMoneda(self.__persona.calcularSaldoTotalCuentas())],
            ]
            tablaResumen = Table(datosResumen, colWidths=[3.8 * inch, 3.2 * inch])
            tablaResumen.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colorBosque),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 10),
                        ("BACKGROUND", (0, 1), (-1, -1), colorMentaSuave),
                        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                        ("FONTNAME", (0, 3), (-1, 3), "Helvetica-Bold"),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#A7F3D0")),
                        ("TOPPADDING", (0, 0), (-1, -1), 6),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ]
                )
            )
            elementos.append(tablaResumen)
            elementos.append(Spacer(1, 10))

            # Detalle de movimientos
            elementos.append(Paragraph("Detalle de Movimientos del Período", estiloSeccion))
            filasMov = [["ID", "Fecha", "Tipo", "Categoría", "Cuenta", "Descripción", "Monto"]]
            for m in self.__listaMovimientosRango:
                filasMov.append(
                    [
                        f"#{m.getIntId()}",
                        m.getStrFecha(),
                        m.getStrTipo(),
                        m.getStrCategoria()[:18],
                        (m.getStrNumeroCuenta() or "General")[:14],
                        m.getStrDescripcion()[:32],
                        self._fmtMoneda(m.obtenerValorConSigno()),
                    ]
                )
            if len(filasMov) == 1:
                filasMov.append(["-", "-", "-", "-", "-", "Sin movimientos en este rango", "$0"])

            tablaMov = Table(
                filasMov,
                colWidths=[0.45 * inch, 0.85 * inch, 0.65 * inch, 1.15 * inch, 1.0 * inch, 1.85 * inch, 1.05 * inch],
            )
            tablaMov.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colorEsmeralda),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 8),
                        ("ALIGN", (-1, 0), (-1, -1), "RIGHT"),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F6FBF8")]),
                        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D1FAE5")),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ]
                )
            )
            elementos.append(tablaMov)
            doc.build(elementos)
            return buffer.getvalue()
        except ImportError:
            return self._generarPDFMinimoRespaldo()

    def exportarReportePDF(self, strPath):
        """Escribe el reporte PDF en una ruta física de disco (firma UML)."""
        try:
            datos = self.generarBytesPDF()
            with open(strPath, "wb") as archivo:
                archivo.write(datos)
            return True
        except OSError:
            return False

    # ---- Exportación a Excel (.xlsx con OpenPyXL) ----------------------------
    def generarBytesExcel(self):
        """Genera un libro Excel (.xlsx) multi-hoja con formato financiero."""
        from openpyxl import Workbook
        from openpyxl.styles import Alignment, Font, PatternFill

        wb = Workbook()

        # Hoja 1: Resumen Ejecutivo
        wsResumen = wb.active
        wsResumen.title = "Resumen Financiero"

        fillEncabezado = PatternFill(start_color="064E3B", end_color="064E3B", fill_type="solid")
        fillSub = PatternFill(start_color="D1FAE5", end_color="D1FAE5", fill_type="solid")
        fontBlanca = Font(color="FFFFFF", bold=True, size=11)
        fontNegrita = Font(color="064E3B", bold=True, size=11)

        wsResumen["A1"] = "SISTEMA DE GESTIÓN DE FINANZAS PERSONALES - REPORTE CONSOLIDADO"
        wsResumen["A1"].font = Font(color="064E3B", bold=True, size=13)
        wsResumen["A2"] = f"Titular: {self.__persona.getStrNombre()} ({self.__persona.getStrDocumento()})"
        wsResumen["A3"] = f"Rango: {self.__strFechaInicio or 'Inicio'} hasta {self.__strFechaFin or 'Actualidad'}"

        wsResumen.append([])
        wsResumen.append(["Indicador", "Valor (COP)"])
        for celda in wsResumen[5]:
            celda.fill = fillEncabezado
            celda.font = fontBlanca

        metricas = [
            ("Total Ingresos", self.__dblTotalIngresos),
            ("Total Gastos", self.__dblTotalGastos),
            ("Balance Neto del Período", self.__dblBalanceNeto),
            ("Saldo Consolidado en Cuentas", self.__persona.calcularSaldoTotalCuentas()),
        ]
        for nombre, valor in metricas:
            wsResumen.append([nombre, round(valor, 2)])
            filaActual = wsResumen.max_row
            wsResumen.cell(row=filaActual, column=2).number_format = "$#,##0.00"
            wsResumen.cell(row=filaActual, column=1).fill = fillSub
            wsResumen.cell(row=filaActual, column=1).font = fontNegrita

        wsResumen.column_dimensions["A"].width = 36
        wsResumen.column_dimensions["B"].width = 24

        # Hoja 2: Movimientos Detallados
        wsMov = wb.create_sheet(title="Movimientos")
        encabezadosMov = ["ID", "Fecha", "Tipo", "Categoría", "Cuenta Bancaria", "Descripción", "Monto", "Impacto Neto"]
        wsMov.append(encabezadosMov)
        for celda in wsMov[1]:
            celda.fill = fillEncabezado
            celda.font = fontBlanca
            celda.alignment = Alignment(horizontal="center")

        for m in self.__listaMovimientosRango:
            wsMov.append(
                [
                    m.getIntId(),
                    m.getStrFecha(),
                    m.getStrTipo(),
                    m.getStrCategoria(),
                    m.getStrNumeroCuenta() or "General",
                    m.getStrDescripcion(),
                    round(m.getDblMonto(), 2),
                    round(m.obtenerValorConSigno(), 2),
                ]
            )
            r = wsMov.max_row
            wsMov.cell(row=r, column=7).number_format = "$#,##0.00"
            wsMov.cell(row=r, column=8).number_format = "$#,##0.00"

        anchos = [8, 14, 12, 22, 20, 40, 18, 18]
        for idx, ancho in enumerate(anchos, start=1):
            letra = chr(64 + idx)
            wsMov.column_dimensions[letra].width = ancho

        # Hoja 3: Cuentas Bancarias y Metas
        wsCuentas = wb.create_sheet(title="Cuentas y Metas")
        wsCuentas.append(["Número Cuenta", "Entidad Bancaria", "Tipo Cuenta", "Saldo Disponible"])
        for celda in wsCuentas[1]:
            celda.fill = fillEncabezado
            celda.font = fontBlanca
        for cta in self.__persona.getListaCuentas():
            wsCuentas.append(
                [
                    cta.getStrNumeroCuenta(),
                    cta.getStrEntidadBancaria(),
                    cta.getStrTipoCuenta(),
                    round(cta.getDblSaldoActual(), 2),
                ]
            )
            wsCuentas.cell(row=wsCuentas.max_row, column=4).number_format = "$#,##0.00"

        wsCuentas.append([])
        wsCuentas.append(["Meta de Ahorro", "Objetivo", "Acumulado", "% Avance", "Fecha Límite", "Fecha Proyectada"])
        filaMetaHeader = wsCuentas.max_row
        for celda in wsCuentas[filaMetaHeader]:
            celda.fill = fillEncabezado
            celda.font = fontBlanca
        for meta in self.__persona.getListaMetasAhorro():
            wsCuentas.append(
                [
                    meta.getStrNombreMeta(),
                    round(meta.getDblMontoObjetivo(), 2),
                    round(meta.getDblMontoAcumulado(), 2),
                    round(meta.calcularProgresoPorcentual() / 100.0, 4),
                    meta.getStrFechaLimite(),
                    meta.calcularFechaProyectada(),
                ]
            )
            r = wsCuentas.max_row
            wsCuentas.cell(row=r, column=2).number_format = "$#,##0.00"
            wsCuentas.cell(row=r, column=3).number_format = "$#,##0.00"
            wsCuentas.cell(row=r, column=4).number_format = "0.0%"

        for col in ["A", "B", "C", "D", "E", "F"]:
            wsCuentas.column_dimensions[col].width = 24

        salida = io.BytesIO()
        wb.save(salida)
        return salida.getvalue()

    def _fmtMoneda(self, dblValor):
        strSigno = "-" if dblValor < 0 else ""
        return f"{strSigno}${abs(dblValor):,.0f}".replace(",", ".")

    def _generarPDFMinimoRespaldo(self):
        """Generador PDF 1.4 puro sin dependencias externas en caso de emergencia."""
        lineas = [
            "REPORTE FINANCIERO CONSOLIDADO - ECCI",
            f"Titular: {self.__persona.getStrNombre()} ({self.__persona.getStrDocumento()})",
            f"Rango: {self.__strFechaInicio} a {self.__strFechaFin}",
            f"Ingresos: {self._fmtMoneda(self.__dblTotalIngresos)}",
            f"Gastos: {self._fmtMoneda(self.__dblTotalGastos)}",
            f"Balance Neto: {self._fmtMoneda(self.__dblBalanceNeto)}",
        ]
        contenidoTxt = "BT /F1 12 Tf 50 750 Td 18 TL " + " ".join(
            f"({l}) Tj T*" for l in lineas
        ) + " ET"
        bytesContenido = contenidoTxt.encode("latin-1", errors="replace")
        pdf = (
            b"%PDF-1.4\n"
            b"1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n"
            b"2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj\n"
            b"3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>endobj\n"
            + f"4 0 obj<< /Length {len(bytesContenido)} >>stream\n".encode("ascii")
            + bytesContenido
            + b"\nendstream\nendobj\n"
            b"5 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj\n"
            b"trailer<< /Root 1 0 R >>\n%%EOF"
        )
        return pdf

    # ---- Alias exactos de la Matriz UML (Sección 4) --------------------------
    def Generar_Grafico_Consolidado(self, dtInicio, dtFin):
        self.__strFechaInicio = str(dtInicio)
        self.__strFechaFin = str(dtFin)
        self.calcularBalanceNeto()
        return self.generarGraficoConsolidado()

    def Exportar_Reporte_PDF(self, strPath):
        return self.exportarReportePDF(strPath)

    def Calcular_Balance_Neto(self):
        return self.calcularBalanceNeto()

    # ---- Getters -------------------------------------------------------------
    def getDblTotalIngresos(self):
        return self.__dblTotalIngresos

    def getDblTotalGastos(self):
        return self.__dblTotalGastos

    def getDblBalanceNeto(self):
        return self.__dblBalanceNeto
