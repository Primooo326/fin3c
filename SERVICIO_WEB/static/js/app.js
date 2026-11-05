/* ==========================================================================
   Cliente SPA Finanzas Personales ECCI — Conectado a API REST FastAPI
   ========================================================================== */

const estadoApp = {
  strToken: localStorage.getItem("finanzas_token") || "",
  usuario: null,
  strMesSeleccionado: "Todos",
  strSeccionActual: "dashboard",
  cuentas: [],
  categoriasIngresos: [],
  categoriasGastos: [],
  catalogoCategorias: [],
  chartMensual: null,
  chartCategorias: null,
  chartReporte: null,
};

const TITULOS_SECCIONES = {
  dashboard: {
    titulo: "Resumen Financiero",
    subtitulo: "Consolidado de cuentas, ejecución presupuestal y flujo de caja",
  },
  movimientos: {
    titulo: "Movimientos y Categorías Dinámicas",
    subtitulo: "Registra ingresos y gastos asociados a tus cuentas bancarias (RF-03)",
  },
  cuentas: {
    titulo: "Cuentas Bancarias y Efectivo",
    subtitulo: "Administra tus fuentes de dinero: Ahorros, Corriente y Efectivo (RF-02)",
  },
  presupuestos: {
    titulo: "Presupuestos y Alertas Preventivas",
    subtitulo: "Control de techos mensuales con alerta automática desde el 85% (RF-04)",
  },
  metas: {
    titulo: "Metas de Ahorro Programadas",
    subtitulo: "Registra abonos progresivos y consulta tu fecha proyectada de cumplimiento (RF-05)",
  },
  reportes: {
    titulo: "Reportes Consolidados y Exportación",
    subtitulo: "Analítica por rango de fechas y descarga oficial en PDF y Excel (RF-06)",
  },
};

/* ---------- Utilidades de Formato y Seguridad ---------- */

function fmtCOP(valor) {
  const num = Number(valor || 0);
  const absFmt = new Intl.NumberFormat("es-CO", {
    maximumFractionDigits: 0,
  }).format(Math.abs(num));
  return (num < 0 ? "-$" : "$") + absFmt;
}

function escaparHtml(texto) {
  return String(texto ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function mostrarToast(mensaje, tipo = "exito") {
  const cont = document.getElementById("toastContenedor");
  const div = document.createElement("div");
  div.className = `toast ${tipo}`;
  div.textContent = mensaje;
  cont.appendChild(div);
  setTimeout(() => {
    div.remove();
  }, tipo === "advertencia" ? 6500 : 4000);
}

async function apiFetch(ruta, opciones = {}) {
  const headers = Object.assign({ "Content-Type": "application/json" }, opciones.headers || {});
  if (estadoApp.strToken) {
    headers["Authorization"] = `Bearer ${estadoApp.strToken}`;
  }
  const resp = await fetch(ruta, { ...opciones, headers });
  if (resp.status === 401 && !ruta.includes("/api/auth/login")) {
    limpiarSesionLocal();
    throw new Error("Tu sesión ha expirado. Inicia sesión nuevamente.");
  }
  const datos = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    throw new Error(datos.detail || "Error procesando la solicitud.");
  }
  return datos;
}

/* ---------- Inicialización y Salud de PostgreSQL ---------- */

document.addEventListener("DOMContentLoaded", async () => {
  inicializarFechasPorDefecto();
  await verificarSaludBackend();
  if (estadoApp.strToken) {
    try {
      const res = await apiFetch("/api/auth/perfil");
      iniciarInterfazAutenticada(res.usuario);
    } catch (_e) {
      limpiarSesionLocal();
    }
  }
});

function inicializarFechasPorDefecto() {
  const hoy = new Date().toISOString().slice(0, 10);
  const futuro = new Date(Date.now() + 180 * 86400000).toISOString().slice(0, 10);
  const inicioTrimestre = hoy.slice(0, 4) + "-09-01";

  const elMovFecha = document.getElementById("movFecha");
  const elMetaLim = document.getElementById("metaFechaLim");
  const elRepIni = document.getElementById("repFechaInicio");
  const elRepFin = document.getElementById("repFechaFin");

  if (elMovFecha) elMovFecha.value = hoy;
  if (elMetaLim) elMetaLim.value = futuro;
  if (elRepIni) elRepIni.value = inicioTrimestre;
  if (elRepFin) elRepFin.value = hoy;
}

async function verificarSaludBackend() {
  try {
    const salud = await fetch("/api/salud").then((r) => r.json());
    const bannerAuth = document.getElementById("bannerEstadoBDAuth");
    const puntoBD = document.getElementById("puntoBD");
    const textoBD = document.getElementById("textoBD");

    if (!salud.persistencia.boolConectado) {
      bannerAuth.classList.remove("oculto");
      bannerAuth.textContent = "⚠️ PostgreSQL desconectado: " + salud.persistencia.strDetalle;
      puntoBD.classList.add("error");
      textoBD.textContent = "PostgreSQL Sin Conexión";
    } else {
      bannerAuth.classList.add("oculto");
      puntoBD.classList.remove("error");
      textoBD.textContent = "PostgreSQL ACID Activo";
    }
  } catch (_err) {
    // Servidor iniciando
  }
}

/* ---------- Autenticación, Registro y Acceso Demo ---------- */

function cambiarTabAuth(tab) {
  const esLogin = tab === "login";
  document.getElementById("tabLoginBtn").classList.toggle("activo", esLogin);
  document.getElementById("tabRegistroBtn").classList.toggle("activo", !esLogin);
  document.getElementById("formLogin").classList.toggle("oculto", !esLogin);
  document.getElementById("formRegistro").classList.toggle("oculto", esLogin);
}

async function manejarLogin(ev) {
  ev.preventDefault();
  const strIdentificador = document.getElementById("loginIdentificador").value.trim();
  const strPassword = document.getElementById("loginPassword").value;
  try {
    const res = await apiFetch("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ strIdentificador, strPassword }),
    });
    guardarSesionLocal(res.strToken, res.usuario);
    mostrarToast(res.strMensaje);
    iniciarInterfazAutenticada(res.usuario);
  } catch (err) {
    mostrarToast(err.message, "error");
  }
}

async function loginRapidoDemo(strDocumento) {
  document.getElementById("loginIdentificador").value = strDocumento;
  document.getElementById("loginPassword").value = "Demo2026*";
  try {
    const res = await apiFetch("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ strIdentificador: strDocumento, strPassword: "Demo2026*" }),
    });
    guardarSesionLocal(res.strToken, res.usuario);
    mostrarToast(res.strMensaje);
    iniciarInterfazAutenticada(res.usuario);
  } catch (err) {
    mostrarToast(err.message, "error");
  }
}

async function manejarRegistro(ev) {
  ev.preventDefault();
  const carga = {
    strDocumento: document.getElementById("regDocumento").value.trim(),
    strNombre: document.getElementById("regNombre").value.trim(),
    strCorreo: document.getElementById("regCorreo").value.trim(),
    strPassword: document.getElementById("regPassword").value,
  };
  try {
    const res = await apiFetch("/api/auth/registro", {
      method: "POST",
      body: JSON.stringify(carga),
    });
    guardarSesionLocal(res.strToken, res.usuario);
    mostrarToast(res.strMensaje);
    iniciarInterfazAutenticada(res.usuario);
  } catch (err) {
    mostrarToast(err.message, "error");
  }
}

function guardarSesionLocal(token, usuario) {
  estadoApp.strToken = token;
  estadoApp.usuario = usuario;
  localStorage.setItem("finanzas_token", token);
}

function limpiarSesionLocal() {
  estadoApp.strToken = "";
  estadoApp.usuario = null;
  localStorage.removeItem("finanzas_token");
  document.getElementById("vistaApp").classList.add("oculto");
  document.getElementById("vistaAuth").classList.remove("oculto");
}

async function cerrarSesionApp() {
  try {
    await apiFetch("/api/auth/logout", { method: "POST" });
  } catch (_e) {
    // ignorar
  }
  cerrarModalPerfil();
  limpiarSesionLocal();
  mostrarToast("Has cerrado sesión de forma segura.");
}

/* ---------- Navegación Principal y Carga de Datos ---------- */

async function iniciarInterfazAutenticada(usuario) {
  estadoApp.usuario = usuario;
  document.getElementById("vistaAuth").classList.add("oculto");
  document.getElementById("vistaApp").classList.remove("oculto");

  actualizarCabeceraUsuario(usuario);
  await sincronizarCatalogosBase();
  await cargarDashboard();
}

function actualizarCabeceraUsuario(usuario) {
  document.getElementById("nombreUsuarioTop").textContent = usuario.strNombre;
  document.getElementById("correoUsuarioTop").textContent = usuario.strCorreo;
  const iniciales = usuario.strNombre
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0].toUpperCase())
    .join("");
  document.getElementById("avatarIniciales").textContent = iniciales || "US";
}

async function navegarSeccion(seccion) {
  estadoApp.strSeccionActual = seccion;

  document.querySelectorAll(".seccion-vista").forEach((el) => el.classList.add("oculto"));
  document.getElementById(`sec-${seccion}`).classList.remove("oculto");

  document.querySelectorAll(".nav-btn, .bottom-nav-btn").forEach((btn) => {
    btn.classList.toggle("activo", btn.dataset.seccion === seccion);
  });

  const info = TITULOS_SECCIONES[seccion];
  if (info) {
    document.getElementById("tituloSeccion").textContent = info.titulo;
    document.getElementById("subtituloSeccion").textContent = info.subtitulo;
  }

  await sincronizarCatalogosBase();

  if (seccion === "dashboard") await cargarDashboard();
  if (seccion === "movimientos") await cargarVistaMovimientos();
  if (seccion === "cuentas") await cargarVistaCuentas();
  if (seccion === "presupuestos") await cargarVistaPresupuestos();
  if (seccion === "metas") await cargarVistaMetas();
  if (seccion === "reportes") await consultarReporteConsolidado();
}

async function cambiarMesGlobal() {
  estadoApp.strMesSeleccionado = document.getElementById("selectorMesGlobal").value;
  await navegarSeccion(estadoApp.strSeccionActual);
}

async function sincronizarCatalogosBase() {
  const [resCuentas, resCategorias] = await Promise.all([
    apiFetch("/api/cuentas"),
    apiFetch("/api/categorias"),
  ]);

  estadoApp.cuentas = resCuentas.cuentas;
  estadoApp.categoriasIngresos = resCategorias.ingresos;
  estadoApp.categoriasGastos = resCategorias.gastos;
  estadoApp.catalogoCategorias = resCategorias.catalogo;

  poblarSelectoresCuentas();
  actualizarSelectCategoriasMovimiento();
  poblarSelectorCategoriasPresupuesto();
}

function poblarSelectoresCuentas() {
  const selMov = document.getElementById("movCuenta");
  const selFiltro = document.getElementById("filtroMovCuenta");
  const selAbono = document.getElementById("abonoCuentaOrigen");

  const opcionesCuentas = estadoApp.cuentas
    .map(
      (c) =>
        `<option value="${escaparHtml(c.strNumeroCuenta)}">${escaparHtml(c.strEntidadBancaria)} (${escaparHtml(c.strTipoCuenta)}) • ${fmtCOP(c.dblSaldoActual)}</option>`
    )
    .join("");

  if (selMov) selMov.innerHTML = opcionesCuentas;
  if (selFiltro) {
    const actual = selFiltro.value || "Todos";
    selFiltro.innerHTML =
      `<option value="Todos">Todas las cuentas</option>` +
      estadoApp.cuentas
        .map(
          (c) =>
            `<option value="${escaparHtml(c.strNumeroCuenta)}">${escaparHtml(c.strEntidadBancaria)} (${escaparHtml(c.strNumeroCuenta)})</option>`
        )
        .join("");
    selFiltro.value = actual;
  }
  if (selAbono) {
    selAbono.innerHTML =
      `<option value="">Abono directo (sin descontar cuenta)</option>` + opcionesCuentas;
  }
}

function actualizarSelectCategoriasMovimiento() {
  const tipo = document.getElementById("movTipo")?.value || "Gasto";
  const lista = tipo === "Ingreso" ? estadoApp.categoriasIngresos : estadoApp.categoriasGastos;
  const sel = document.getElementById("movCategoria");
  if (sel) {
    sel.innerHTML = lista
      .map((cat) => `<option value="${escaparHtml(cat)}">${escaparHtml(cat)}</option>`)
      .join("");
  }
}

function poblarSelectorCategoriasPresupuesto() {
  const sel = document.getElementById("presCategoria");
  if (sel) {
    sel.innerHTML = estadoApp.categoriasGastos
      .map((cat) => `<option value="${escaparHtml(cat)}">${escaparHtml(cat)}</option>`)
      .join("");
  }
}

/* ---------- SECCIÓN 1: DASHBOARD ---------- */

async function cargarDashboard() {
  const datos = await apiFetch(`/api/dashboard?mes=${encodeURIComponent(estadoApp.strMesSeleccionado)}`);

  // Actualizar selector de meses conservando selección
  const selMes = document.getElementById("selectorMesGlobal");
  const meses = datos.listaMesesDisponibles || [];
  selMes.innerHTML =
    `<option value="Todos">Todos los meses</option>` +
    meses.map((m) => `<option value="${escaparHtml(m)}">Período ${escaparHtml(m)}</option>`).join("");
  if (meses.includes(estadoApp.strMesSeleccionado) || estadoApp.strMesSeleccionado === "Todos") {
    selMes.value = estadoApp.strMesSeleccionado;
  } else if (meses.length > 0) {
    estadoApp.strMesSeleccionado = meses[0];
    selMes.value = meses[0];
  }

  // KPIs
  document.getElementById("kpiPatrimonio").textContent = fmtCOP(datos.kpis.dblPatrimonioCuentas);
  document.getElementById("kpiCuentasSub").textContent = `${datos.cuentas.length} fuente(s) activa(s)`;
  document.getElementById("kpiIngresos").textContent = fmtCOP(datos.kpis.dblIngresosPeriodo);
  document.getElementById("kpiGastos").textContent = fmtCOP(datos.kpis.dblGastosPeriodo);
  document.getElementById("kpiBalance").textContent = fmtCOP(datos.kpis.dblBalancePeriodo);
  document.getElementById("kpiTasaAhorro").textContent = `Tasa de ahorro: ${datos.kpis.dblPorcentajeAhorro}%`;

  // Alertas RF-04 y Sobregiros
  renderizarAlertas("contenedorAlertasDashboard", datos.alertas);

  // Cuentas resumen
  const contCuentas = document.getElementById("resumenCuentasDashboard");
  contCuentas.innerHTML = datos.cuentas
    .map(
      (c) => `
      <div style="display:flex; justify-content:space-between; align-items:center; padding:0.75rem 0.9rem; border-radius:12px; background:${c.boolSobregiro ? "#fffbeb" : "var(--bg-mint-tint)"}; border:1px solid ${c.boolSobregiro ? "var(--amber-border)" : "var(--border-sage)"};">
        <div>
          <strong style="color:var(--forest-900); font-size:0.92rem;">${escaparHtml(c.strEntidadBancaria)}</strong>
          <div style="font-size:0.77rem; color:var(--ink-muted);">${escaparHtml(c.strTipoCuenta)} • ${escaparHtml(c.strNumeroCuenta)}</div>
        </div>
        <div class="${c.boolSobregiro ? "monto-negativo" : "monto-positivo"}" style="font-size:1rem;">
          ${fmtCOP(c.dblSaldoActual)}
        </div>
      </div>`
    )
    .join("");

  // Últimos movimientos
  const contMovs = document.getElementById("ultimosMovimientosDashboard");
  if (!datos.ultimosMovimientos.length) {
    contMovs.innerHTML = `<p style="color:var(--ink-muted); font-size:0.9rem;">Aún no hay transacciones en este período.</p>`;
  } else {
    contMovs.innerHTML = `
      <table class="tabla-finanzas">
        <thead>
          <tr><th>Fecha</th><th>Categoría</th><th>Descripción</th><th style="text-align:right;">Monto</th></tr>
        </thead>
        <tbody>
          ${datos.ultimosMovimientos
            .map(
              (m) => `
            <tr>
              <td>${escaparHtml(m.strFecha)}</td>
              <td><span class="badge-tipo ${m.boolEsIngreso ? "badge-ingreso" : "badge-gasto"}">${escaparHtml(m.strCategoria)}</span></td>
              <td>${escaparHtml(m.strDescripcion)}</td>
              <td style="text-align:right;" class="${m.boolEsIngreso ? "monto-positivo" : "monto-negativo"}">
                ${fmtCOP(m.dblValorConSigno)}
              </td>
            </tr>`
            )
            .join("")}
        </tbody>
      </table>`;
  }

  renderizarGraficaMensual("graficaMensualDashboard", datos.graficas.serieMensual, "chartMensual");
  renderizarGraficaCategorias("graficaCategoriasDashboard", datos.graficas.gastosPorCategoria);
}

function renderizarAlertas(idContenedor, alertas) {
  const cont = document.getElementById(idContenedor);
  if (!alertas || alertas.length === 0) {
    cont.innerHTML = "";
    return;
  }
  cont.innerHTML = alertas
    .map((a) => {
      const icono = a.strNivel === "excedido" ? "🚨" : a.strNivel === "sobregiro" ? "🏦" : "⚠️";
      return `
        <div class="alerta-item ${escaparHtml(a.strNivel)}">
          <span>${icono} ${escaparHtml(a.strMensaje)}</span>
          <span class="badge-tipo">${escaparHtml(a.strCategoria)}</span>
        </div>`;
    })
    .join("");
}

function renderizarGraficaMensual(idCanvas, serie, claveInstancia) {
  const ctx = document.getElementById(idCanvas);
  if (!ctx) return;
  if (estadoApp[claveInstancia]) {
    estadoApp[claveInstancia].destroy();
  }

  const etiquetas = serie.length ? serie.map((s) => s.strMes) : ["Sin datos"];
  const ingresos = serie.length ? serie.map((s) => s.dblIngresos) : [0];
  const gastos = serie.length ? serie.map((s) => s.dblGastos) : [0];

  estadoApp[claveInstancia] = new Chart(ctx, {
    type: "bar",
    data: {
      labels: etiquetas,
      datasets: [
        {
          label: "Ingresos",
          data: ingresos,
          backgroundColor: "#34d399",
          borderColor: "#10b981",
          borderWidth: 1,
          borderRadius: 8,
        },
        {
          label: "Gastos",
          data: gastos,
          backgroundColor: "#fca5a5",
          borderColor: "#ef4444",
          borderWidth: 1,
          borderRadius: 8,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "top",
          labels: { font: { family: "Plus Jakarta Sans", weight: "600" } },
        },
      },
      scales: {
        y: {
          ticks: {
            callback: (v) => fmtCOP(v),
            font: { family: "Plus Jakarta Sans" },
          },
          grid: { color: "#eaf5ee" },
        },
        x: {
          grid: { display: false },
          ticks: { font: { family: "Plus Jakarta Sans", weight: "600" } },
        },
      },
    },
  });
}

function renderizarGraficaCategorias(idCanvas, gastosPorCat) {
  const ctx = document.getElementById(idCanvas);
  if (!ctx) return;
  if (estadoApp.chartCategorias) {
    estadoApp.chartCategorias.destroy();
  }

  const etiquetas = gastosPorCat.length ? gastosPorCat.map((g) => g.strCategoria) : ["Sin gastos"];
  const valores = gastosPorCat.length ? gastosPorCat.map((g) => g.dblTotal) : [1];
  const paletaVerde = [
    "#059669",
    "#10b981",
    "#34d399",
    "#6ee7b7",
    "#a7f3d0",
    "#047857",
    "#065f46",
    "#86efac",
  ];

  estadoApp.chartCategorias = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: etiquetas,
      datasets: [
        {
          data: valores,
          backgroundColor: gastosPorCat.length ? paletaVerde : ["#e5e7eb"],
          borderWidth: 2,
          borderColor: "#ffffff",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "64%",
      plugins: {
        legend: {
          position: "right",
          labels: { font: { family: "Plus Jakarta Sans", size: 12 } },
        },
      },
    },
  });
}

/* ---------- SECCIÓN 2: MOVIMIENTOS Y CATEGORÍAS DINÁMICAS ---------- */

async function cargarVistaMovimientos() {
  const tipo = document.getElementById("filtroMovTipo").value;
  const cuenta = document.getElementById("filtroMovCuenta").value;
  const url = `/api/movimientos?tipo=${encodeURIComponent(tipo)}&mes=${encodeURIComponent(
    estadoApp.strMesSeleccionado
  )}&cuenta=${encodeURIComponent(cuenta)}`;

  const res = await apiFetch(url);
  const cont = document.getElementById("tablaMovimientosCompleta");

  if (!res.movimientos.length) {
    cont.innerHTML = `<p style="color:var(--ink-muted);">No se encontraron movimientos con los filtros actuales.</p>`;
  } else {
    cont.innerHTML = `
      <table class="tabla-finanzas">
        <thead>
          <tr>
            <th>#ID</th>
            <th>Fecha</th>
            <th>Tipo</th>
            <th>Categoría</th>
            <th>Cuenta Asociada</th>
            <th>Descripción</th>
            <th style="text-align:right;">Monto</th>
            <th style="text-align:center;">Acción</th>
          </tr>
        </thead>
        <tbody>
          ${res.movimientos
            .map(
              (m) => `
            <tr>
              <td>#${m.intId}</td>
              <td>${escaparHtml(m.strFecha)}</td>
              <td><span class="badge-tipo ${m.boolEsIngreso ? "badge-ingreso" : "badge-gasto"}">${escaparHtml(m.strTipo)}</span></td>
              <td><strong>${escaparHtml(m.strCategoria)}</strong></td>
              <td>${escaparHtml(m.strNumeroCuenta || "General")}</td>
              <td>${escaparHtml(m.strDescripcion)}</td>
              <td style="text-align:right;" class="${m.boolEsIngreso ? "monto-positivo" : "monto-negativo"}">
                ${fmtCOP(m.dblValorConSigno)}
              </td>
              <td style="text-align:center;">
                <button class="btn btn-peligro" onclick="anularMovimiento(${m.intId})">Anular</button>
              </td>
            </tr>`
            )
            .join("")}
        </tbody>
      </table>`;
  }

  // Renderizar chips de categorías personalizadas
  const personalizadas = estadoApp.catalogoCategorias.filter((c) => c.boolPersonalizada);
  const contCat = document.getElementById("listaCategoriasPersonalizadas");
  if (!personalizadas.length) {
    contCat.innerHTML = `<small style="color:var(--ink-muted);">Aún no has creado categorías personalizadas adicionales.</small>`;
  } else {
    contCat.innerHTML = personalizadas
      .map(
        (c) => `
        <span class="badge-tipo" style="display:inline-flex; align-items:center; gap:0.4rem; padding:0.35rem 0.7rem;">
          ${escaparHtml(c.strNombreCategoria)} (${escaparHtml(c.strTipoMovimiento)})
          <button type="button" style="border:none; background:transparent; cursor:pointer; color:#991b1b; font-weight:800;" onclick="eliminarCategoria(${c.intIdCategoria})" title="Eliminar">✕</button>
        </span>`
      )
      .join("");
  }
}

async function guardarMovimiento(ev) {
  ev.preventDefault();
  const carga = {
    strTipo: document.getElementById("movTipo").value,
    strNumeroCuenta: document.getElementById("movCuenta").value,
    strCategoria: document.getElementById("movCategoria").value,
    strMonto: document.getElementById("movMonto").value.trim(),
    strFecha: document.getElementById("movFecha").value,
    strDescripcion: document.getElementById("movDescripcion").value.trim(),
  };

  try {
    const res = await apiFetch("/api/movimientos", {
      method: "POST",
      body: JSON.stringify(carga),
    });
    document.getElementById("movMonto").value = "";
    document.getElementById("movDescripcion").value = "";
    mostrarToast(res.strMensaje);
    if (res.strAdvertencia) {
      mostrarToast(res.strAdvertencia, "advertencia");
    }
    await sincronizarCatalogosBase();
    await cargarVistaMovimientos();
  } catch (err) {
    mostrarToast(err.message, "error");
  }
}

async function anularMovimiento(intId) {
  try {
    const res = await apiFetch(`/api/movimientos/${intId}`, { method: "DELETE" });
    mostrarToast(res.strMensaje);
    await sincronizarCatalogosBase();
    await cargarVistaMovimientos();
  } catch (err) {
    mostrarToast(err.message, "error");
  }
}

async function guardarCategoriaPersonalizada(ev) {
  ev.preventDefault();
  const carga = {
    strNombreCategoria: document.getElementById("catNombre").value.trim(),
    strTipoMovimiento: document.getElementById("catTipo").value,
    strLimiteSugerido: document.getElementById("catLimiteSug").value.trim() || "0",
  };
  try {
    const res = await apiFetch("/api/categorias", {
      method: "POST",
      body: JSON.stringify(carga),
    });
    document.getElementById("catNombre").value = "";
    document.getElementById("catLimiteSug").value = "";
    mostrarToast(res.strMensaje);
    await sincronizarCatalogosBase();
    await cargarVistaMovimientos();
  } catch (err) {
    mostrarToast(err.message, "error");
  }
}

async function eliminarCategoria(intIdCategoria) {
  try {
    const res = await apiFetch(`/api/categorias/${intIdCategoria}`, { method: "DELETE" });
    mostrarToast(res.strMensaje);
    await sincronizarCatalogosBase();
    await cargarVistaMovimientos();
  } catch (err) {
    mostrarToast(err.message, "error");
  }
}

/* ---------- SECCIÓN 3: CUENTAS BANCARIAS ---------- */

async function cargarVistaCuentas() {
  const res = await apiFetch("/api/cuentas");
  estadoApp.cuentas = res.cuentas;
  const grid = document.getElementById("gridTarjetasCuentas");

  grid.innerHTML = res.cuentas
    .map(
      (c) => `
      <article class="cuenta-tarjeta ${c.boolSobregiro ? "sobregiro" : ""}">
        <div style="display:flex; justify-content:space-between; align-items:flex-start;">
          <div>
            <span class="badge-tipo">${escaparHtml(c.strTipoCuenta)}</span>
            <h3 style="margin-top:0.55rem; color:var(--forest-900); font-size:1.12rem;">
              ${escaparHtml(c.strEntidadBancaria)}
            </h3>
            <small style="color:var(--ink-muted);">N.° ${escaparHtml(c.strNumeroCuenta)}</small>
          </div>
          <button class="btn btn-peligro" onclick="borrarCuenta('${encodeURIComponent(c.strNumeroCuenta)}')">Eliminar</button>
        </div>
        <div>
          <div style="font-size:0.76rem; color:var(--ink-muted); font-weight:700; text-transform:uppercase;">
            Saldo Disponible Actual
          </div>
          <div class="kpi-valor ${c.boolSobregiro ? "monto-negativo" : ""}" style="margin:0.2rem 0 0;">
            ${fmtCOP(c.dblSaldoActual)}
          </div>
          ${
            c.boolSobregiro
              ? `<small style="color:var(--amber-text); font-weight:700;">⚠️ Cuenta en sobregiro autorizado</small>`
              : `<small style="color:var(--emerald-700); font-weight:600;">✓ Fondos verificados</small>`
          }
        </div>
      </article>`
    )
    .join("");
}

async function guardarCuentaBancaria(ev) {
  ev.preventDefault();
  const carga = {
    strNumeroCuenta: document.getElementById("ctaNumero").value.trim(),
    strEntidadBancaria: document.getElementById("ctaEntidad").value.trim(),
    strTipoCuenta: document.getElementById("ctaTipo").value,
    strSaldoInicial: document.getElementById("ctaSaldo").value.trim() || "0",
  };
  try {
    const res = await apiFetch("/api/cuentas", {
      method: "POST",
      body: JSON.stringify(carga),
    });
    document.getElementById("ctaNumero").value = "";
    document.getElementById("ctaEntidad").value = "";
    document.getElementById("ctaSaldo").value = "0";
    mostrarToast(res.strMensaje);
    await sincronizarCatalogosBase();
    await cargarVistaCuentas();
  } catch (err) {
    mostrarToast(err.message, "error");
  }
}

async function borrarCuenta(strNumCodificado) {
  try {
    const res = await apiFetch(`/api/cuentas/${strNumCodificado}`, { method: "DELETE" });
    mostrarToast(res.strMensaje);
    await sincronizarCatalogosBase();
    await cargarVistaCuentas();
  } catch (err) {
    mostrarToast(err.message, "error");
  }
}

/* ---------- SECCIÓN 4: PRESUPUESTOS Y ALERTAS 85% ---------- */

async function cargarVistaPresupuestos() {
  const res = await apiFetch(`/api/presupuestos?mes=${encodeURIComponent(estadoApp.strMesSeleccionado)}`);
  renderizarAlertas("contenedorAlertasPresupuestos", res.alertas);

  const grid = document.getElementById("gridPresupuestos");
  if (!res.presupuestos.length) {
    grid.innerHTML = `<div class="card"><p style="color:var(--ink-muted);">Aún no has configurado techos presupuestales.</p></div>`;
    return;
  }

  grid.innerHTML = res.presupuestos
    .map((p) => {
      const ancho = Math.min(100, Math.max(0, p.dblPorcentajeUso));
      const claseBarra =
        p.strEstado === "excedido" ? "excedido" : p.strEstado === "alerta" ? "alerta" : "";
      const etiquetaEstado =
        p.strEstado === "excedido"
          ? "🚨 Sobrecosto (>100%)"
          : p.strEstado === "alerta"
          ? `⚠️ Alerta Preventiva (≥${p.dblPorcentajeAlerta}%)`
          : "✅ Ejecución Saludable";

      return `
        <article class="card" style="margin-bottom:0;">
          <div style="display:flex; justify-content:space-between; align-items:flex-start;">
            <div>
              <h3 style="color:var(--forest-900); font-size:1.08rem;">${escaparHtml(p.strCategoria)}</h3>
              <small style="color:var(--ink-muted); font-weight:600;">${etiquetaEstado}</small>
            </div>
            <button class="btn btn-peligro" onclick="eliminarPresupuesto('${encodeURIComponent(p.strCategoria)}')">Quitar</button>
          </div>

          <div class="progreso-barra-fondo">
            <div class="progreso-barra-relleno ${claseBarra}" style="width:${ancho}%;"></div>
          </div>

          <div style="display:flex; justify-content:space-between; font-size:0.84rem; font-weight:700;">
            <span>Ejecutado: ${fmtCOP(p.dblGastado)} (${p.dblPorcentajeUso}%)</span>
            <span>Tope: ${fmtCOP(p.dblLimite)}</span>
          </div>
          <div style="margin-top:0.35rem; font-size:0.8rem; color:var(--ink-muted);">
            Disponible restante: <strong>${fmtCOP(p.dblDisponible)}</strong>
          </div>
        </article>`;
    })
    .join("");
}

async function guardarPresupuesto(ev) {
  ev.preventDefault();
  const carga = {
    strCategoria: document.getElementById("presCategoria").value,
    strLimite: document.getElementById("presLimite").value.trim(),
    strPeriodoMesAno: estadoApp.strMesSeleccionado,
    dblPorcentajeAlerta: Number(document.getElementById("presUmbral").value || 85),
  };
  try {
    const res = await apiFetch("/api/presupuestos", {
      method: "POST",
      body: JSON.stringify(carga),
    });
    document.getElementById("presLimite").value = "";
    mostrarToast(res.strMensaje);
    await cargarVistaPresupuestos();
  } catch (err) {
    mostrarToast(err.message, "error");
  }
}

async function eliminarPresupuesto(strCatCodificada) {
  try {
    const res = await apiFetch(`/api/presupuestos/${strCatCodificada}`, { method: "DELETE" });
    mostrarToast(res.strMensaje);
    await cargarVistaPresupuestos();
  } catch (err) {
    mostrarToast(err.message, "error");
  }
}

/* ---------- SECCIÓN 5: METAS DE AHORRO ---------- */

async function cargarVistaMetas() {
  const res = await apiFetch("/api/metas");
  const grid = document.getElementById("gridMetasAhorro");

  if (!res.metas.length) {
    grid.innerHTML = `<div class="card"><p style="color:var(--ink-muted);">Crea tu primera meta de ahorro arriba para proyectar tu fecha de logro.</p></div>`;
    return;
  }

  grid.innerHTML = res.metas
    .map((m) => {
      const ancho = Math.min(100, Math.max(0, m.dblProgresoPorcentual));
      return `
        <article class="card" style="margin-bottom:0; display:flex; flex-direction:column; justify-content:space-between; gap:0.85rem;">
          <div>
            <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:0.5rem;">
              <h3 style="color:var(--forest-900); font-size:1.08rem;">🌱 ${escaparHtml(m.strNombreMeta)}</h3>
              <button class="btn btn-peligro" onclick="borrarMeta(${m.intIdMeta})">✕</button>
            </div>
            <small style="color:var(--ink-muted);">Fecha límite: <strong>${escaparHtml(m.strFechaLimite)}</strong> • Proyectada: <strong>${escaparHtml(m.strFechaProyectada)}</strong></small>

            <div class="progreso-barra-fondo" style="margin-top:0.75rem;">
              <div class="progreso-barra-relleno" style="width:${ancho}%;"></div>
            </div>

            <div style="display:flex; justify-content:space-between; font-size:0.86rem; font-weight:700;">
              <span style="color:var(--emerald-700);">${fmtCOP(m.dblMontoAcumulado)} (${m.dblProgresoPorcentual}%)</span>
              <span>Meta: ${fmtCOP(m.dblMontoObjetivo)}</span>
            </div>
            <div style="font-size:0.8rem; color:var(--ink-muted); margin-top:0.35rem;">
              Faltan <strong>${fmtCOP(m.dblMontoFaltante)}</strong> • Cuota mensual sugerida: <strong>${fmtCOP(m.dblCuotaMensualSugerida)}</strong>
            </div>
          </div>

          <button class="btn btn-primario btn-bloque" data-id="${m.intIdMeta}" data-nombre="${escaparHtml(m.strNombreMeta)}" onclick="abrirModalAbono(this.dataset.id, this.dataset.nombre)">
            + Abonar Capital a esta Meta
          </button>
        </article>`;
    })
    .join("");
}

async function guardarMetaAhorro(ev) {
  ev.preventDefault();
  const carga = {
    strNombreMeta: document.getElementById("metaNombre").value.trim(),
    strMontoObjetivo: document.getElementById("metaObjetivo").value.trim(),
    strAbonoInicial: document.getElementById("metaAbonoIni").value.trim() || "0",
    strFechaLimite: document.getElementById("metaFechaLim").value,
  };
  try {
    const res = await apiFetch("/api/metas", {
      method: "POST",
      body: JSON.stringify(carga),
    });
    document.getElementById("metaNombre").value = "";
    document.getElementById("metaObjetivo").value = "";
    document.getElementById("metaAbonoIni").value = "0";
    mostrarToast(res.strMensaje);
    await cargarVistaMetas();
  } catch (err) {
    mostrarToast(err.message, "error");
  }
}

function abrirModalAbono(intIdMeta, nombreMeta) {
  document.getElementById("abonoIdMeta").value = intIdMeta;
  document.getElementById("tituloModalAbono").textContent = `Abonar a: ${nombreMeta}`;
  document.getElementById("abonoMonto").value = "";
  poblarSelectoresCuentas();
  document.getElementById("modalAbonoMeta").classList.remove("oculto");
}

function cerrarModalAbono() {
  document.getElementById("modalAbonoMeta").classList.add("oculto");
}

async function confirmarAbonoMeta(ev) {
  ev.preventDefault();
  const intIdMeta = document.getElementById("abonoIdMeta").value;
  const carga = {
    strMontoAbono: document.getElementById("abonoMonto").value.trim(),
    strNumeroCuenta: document.getElementById("abonoCuentaOrigen").value,
  };
  try {
    const res = await apiFetch(`/api/metas/${intIdMeta}/abonar`, {
      method: "POST",
      body: JSON.stringify(carga),
    });
    cerrarModalAbono();
    mostrarToast(res.strMensaje);
    if (res.strAdvertencia) {
      mostrarToast(res.strAdvertencia, "advertencia");
    }
    await sincronizarCatalogosBase();
    await cargarVistaMetas();
  } catch (err) {
    mostrarToast(err.message, "error");
  }
}

async function borrarMeta(intIdMeta) {
  try {
    const res = await apiFetch(`/api/metas/${intIdMeta}`, { method: "DELETE" });
    mostrarToast(res.strMensaje);
    await cargarVistaMetas();
  } catch (err) {
    mostrarToast(err.message, "error");
  }
}

/* ---------- SECCIÓN 6: REPORTES CONSOLIDADOS Y EXPORTACIÓN PDF / EXCEL ---------- */

async function consultarReporteConsolidado(ev) {
  if (ev) ev.preventDefault();
  const ini = document.getElementById("repFechaInicio").value;
  const fin = document.getElementById("repFechaFin").value;
  const res = await apiFetch(
    `/api/reportes?fechaInicio=${encodeURIComponent(ini)}&fechaFin=${encodeURIComponent(fin)}`
  );

  document.getElementById("repKpiIngresos").textContent = fmtCOP(res.dblTotalIngresos);
  document.getElementById("repKpiGastos").textContent = fmtCOP(res.dblTotalGastos);
  document.getElementById("repKpiBalance").textContent = fmtCOP(res.dblBalanceNeto);

  renderizarGraficaMensual("graficaReporteRango", res.serieMensual, "chartReporte");
}

async function descargarArchivoReporte(formato) {
  const ini = document.getElementById("repFechaInicio").value;
  const fin = document.getElementById("repFechaFin").value;
  const endpoint = formato === "pdf" ? "/api/reportes/pdf" : "/api/reportes/excel";
  const url = `${endpoint}?fechaInicio=${encodeURIComponent(ini)}&fechaFin=${encodeURIComponent(fin)}`;

  try {
    const resp = await fetch(url, {
      headers: estadoApp.strToken ? { Authorization: `Bearer ${estadoApp.strToken}` } : {},
    });
    if (!resp.ok) throw new Error("No fue posible generar el archivo exportable.");
    const blob = await resp.blob();
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download =
      formato === "pdf" ? "Reporte_Financiero_ECCI.pdf" : "Reporte_Financiero_ECCI.xlsx";
    document.body.appendChild(link);
    link.click();
    link.remove();
    mostrarToast(`Reporte ${formato.toUpperCase()} generado y descargado correctamente.`);
  } catch (err) {
    mostrarToast(err.message, "error");
  }
}

/* ---------- MODAL DE PERFIL ---------- */

function abrirModalPerfil() {
  if (!estadoApp.usuario) return;
  document.getElementById("perfilDocumento").value = estadoApp.usuario.strDocumento;
  document.getElementById("perfilNombre").value = estadoApp.usuario.strNombre;
  document.getElementById("perfilCorreo").value = estadoApp.usuario.strCorreo;
  document.getElementById("perfilPassword").value = "";
  document.getElementById("modalPerfil").classList.remove("oculto");
}

function cerrarModalPerfil() {
  document.getElementById("modalPerfil").classList.add("oculto");
}

async function guardarCambiosPerfil(ev) {
  ev.preventDefault();
  const carga = {
    strNombre: document.getElementById("perfilNombre").value.trim(),
    strCorreo: document.getElementById("perfilCorreo").value.trim(),
    strNuevaPassword: document.getElementById("perfilPassword").value,
  };
  try {
    const res = await apiFetch("/api/auth/perfil", {
      method: "PUT",
      body: JSON.stringify(carga),
    });
    estadoApp.usuario = res.usuario;
    actualizarCabeceraUsuario(res.usuario);
    cerrarModalPerfil();
    mostrarToast(res.strMensaje);
  } catch (err) {
    mostrarToast(err.message, "error");
  }
}
