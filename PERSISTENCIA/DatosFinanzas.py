# =============================================================================
#  Módulo DatosFinanzas: Capa de Persistencia Relacional
#  Soporta PostgreSQL (ACID) como motor principal y SQLite como respaldo
#  automático si PostgreSQL no está escuchando en el puerto configurado.
#  Capa: PERSISTENCIA
# =============================================================================

import os
from pathlib import Path
import sqlite3

try:
    from dotenv import load_dotenv
    RUTA_BASE = Path(__file__).resolve().parent.parent
    load_dotenv(RUTA_BASE / ".env")
except ImportError:
    RUTA_BASE = Path(__file__).resolve().parent.parent

from LOGICA.Seguridad import Seguridad

# Conector PostgreSQL (psycopg v3 o psycopg2)
_DRIVER_PG = None
try:
    import psycopg  # type: ignore
    _DRIVER_PG = "psycopg3"
except ImportError:
    try:
        import psycopg2  # type: ignore
        _DRIVER_PG = "psycopg2"
    except ImportError:
        _DRIVER_PG = None

RUTA_SQLITE = Path(__file__).resolve().parent / "finanzas_local.db"
_esquemaInicializado = False
_motorActivo = None  # 'postgres' o 'sqlite'


class AdaptadorCursor:
    """Envuelve cursores para unificar sintaxis %s (Postgres) y ? (SQLite)."""
    def __init__(self, cursor_real, es_sqlite: bool):
        self._cur = cursor_real
        self._es_sqlite = es_sqlite

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self._cur, "close"):
            self._cur.close()

    def execute(self, sql, params=None):
        if self._es_sqlite:
            # En SQLite reemplazamos %s por ? para compatibilidad uniforme
            sql_convertido = sql.replace("%s", "?")
            if params is None:
                return self._cur.execute(sql_convertido)
            return self._cur.execute(sql_convertido, params)
        if params is None:
            return self._cur.execute(sql)
        return self._cur.execute(sql, params)

    def fetchone(self):
        return self._cur.fetchone()

    def fetchall(self):
        return self._cur.fetchall()

    def __getattr__(self, name):
        return getattr(self._cur, name)


class ConexionUnificada:
    """Administrador de contexto que proporciona una conexión y cursor uniforme."""
    def __init__(self, conn, es_sqlite: bool):
        self._conn = conn
        self._es_sqlite = es_sqlite

    def cursor(self):
        return AdaptadorCursor(self._conn.cursor(), self._es_sqlite)

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.rollback()
        else:
            self.commit()
        self._conn.close()


def obtenerParametrosConexion():
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "dbname": os.getenv("DB_NAME", "finanzas_personales_db"),
        "user": os.getenv("DB_USER", "finanzas_user"),
        "password": os.getenv("DB_PASSWORD", "finanzas_pass_2026"),
    }


def _probarConexionPostgres():
    if _DRIVER_PG is None:
        return None
    params = obtenerParametrosConexion()
    try:
        if _DRIVER_PG == "psycopg3":
            return psycopg.connect(
                host=params["host"],
                port=params["port"],
                dbname=params["dbname"],
                user=params["user"],
                password=params["password"],
                connect_timeout=2,
            )
        return psycopg2.connect(
            host=params["host"],
            port=params["port"],
            dbname=params["dbname"],
            user=params["user"],
            password=params["password"],
            connect_timeout=2,
        )
    except Exception:
        return None


def _abrirConexion():
    global _motorActivo
    conn_pg = _probarConexionPostgres()
    if conn_pg is not None:
        _motorActivo = "postgres"
        return ConexionUnificada(conn_pg, es_sqlite=False)

    _motorActivo = "sqlite"
    conn_lite = sqlite3.connect(str(RUTA_SQLITE))
    conn_lite.execute("PRAGMA foreign_keys = ON;")
    return ConexionUnificada(conn_lite, es_sqlite=True)


def verificarConexion():
    """Comprueba el estado del motor de persistencia activo."""
    try:
        inicializarBaseDatos()
        with _abrirConexion() as conn:
            with conn.cursor() as cur:
                if _motorActivo == "postgres":
                    cur.execute("SELECT version();")
                    fila = cur.fetchone()
                    return True, f"PostgreSQL conectado: {fila[0]}"
                return True, "Base de datos local SQLite activa (respaldo automático listo)"
    except Exception as exc:
        return False, str(exc)


def inicializarBaseDatos():
    """Crea tablas, índices y datos semilla en el motor activo."""
    global _esquemaInicializado, _motorActivo
    if _esquemaInicializado:
        return

    with _abrirConexion() as conn:
        with conn.cursor() as cur:
            if _motorActivo == "postgres":
                rutaSql = Path(__file__).resolve().parent / "schema.sql"
                cur.execute(rutaSql.read_text(encoding="utf-8"))
            else:
                _crearEsquemaSQLite(cur)

            cur.execute("SELECT COUNT(*) FROM personas;")
            intCantidad = cur.fetchone()[0]
            if intCantidad == 0:
                _insertarDatosSemilla(cur)
        conn.commit()

    _esquemaInicializado = True


def _crearEsquemaSQLite(cur):
    """Crea esquema compatible con SQLite."""
    cur.execute("""
    CREATE TABLE IF NOT EXISTS personas (
        str_documento      VARCHAR(30) PRIMARY KEY,
        str_nombre         VARCHAR(150) NOT NULL,
        str_correo         VARCHAR(150) NOT NULL UNIQUE,
        str_password_hash  VARCHAR(300) NOT NULL DEFAULT '',
        dt_fecha_registro  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS cuentas_bancarias (
        str_numero_cuenta    VARCHAR(50) NOT NULL,
        str_documento        VARCHAR(30) NOT NULL REFERENCES personas(str_documento) ON DELETE CASCADE,
        str_entidad_bancaria VARCHAR(100) NOT NULL,
        str_tipo_cuenta      VARCHAR(30) NOT NULL CHECK (str_tipo_cuenta IN ('Ahorros', 'Corriente', 'Efectivo')),
        dbl_saldo_actual     NUMERIC(16, 2) NOT NULL DEFAULT 0,
        PRIMARY KEY (str_documento, str_numero_cuenta)
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS categorias_personalizadas (
        int_id_categoria      INTEGER PRIMARY KEY,
        str_documento         VARCHAR(30) NOT NULL REFERENCES personas(str_documento) ON DELETE CASCADE,
        str_nombre_categoria  VARCHAR(80) NOT NULL,
        str_tipo_movimiento   VARCHAR(20) NOT NULL CHECK (str_tipo_movimiento IN ('Ingreso', 'Gasto')),
        dbl_limite_sugerido   NUMERIC(16, 2) NOT NULL DEFAULT 0,
        UNIQUE (str_documento, str_nombre_categoria, str_tipo_movimiento)
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS movimientos (
        int_id            INTEGER PRIMARY KEY,
        str_documento     VARCHAR(30) NOT NULL REFERENCES personas(str_documento) ON DELETE CASCADE,
        str_tipo          VARCHAR(20) NOT NULL CHECK (str_tipo IN ('Ingreso', 'Gasto')),
        str_descripcion   VARCHAR(255) NOT NULL,
        dbl_monto         NUMERIC(16, 2) NOT NULL CHECK (dbl_monto > 0),
        str_categoria     VARCHAR(80) NOT NULL,
        str_fecha         VARCHAR(10) NOT NULL,
        str_numero_cuenta VARCHAR(50) NOT NULL DEFAULT ''
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS presupuestos (
        str_documento          VARCHAR(30) NOT NULL REFERENCES personas(str_documento) ON DELETE CASCADE,
        str_categoria          VARCHAR(80) NOT NULL,
        dbl_limite             NUMERIC(16, 2) NOT NULL CHECK (dbl_limite > 0),
        str_periodo_mes_ano    VARCHAR(20) NOT NULL DEFAULT 'Todos',
        dbl_porcentaje_alerta  NUMERIC(5, 2) NOT NULL DEFAULT 85.00,
        PRIMARY KEY (str_documento, str_categoria)
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS metas_ahorro (
        int_id_meta          INTEGER PRIMARY KEY,
        str_documento        VARCHAR(30) NOT NULL REFERENCES personas(str_documento) ON DELETE CASCADE,
        str_nombre_meta      VARCHAR(120) NOT NULL,
        dbl_monto_objetivo   NUMERIC(16, 2) NOT NULL CHECK (dbl_monto_objetivo > 0),
        dbl_monto_acumulado  NUMERIC(16, 2) NOT NULL DEFAULT 0,
        str_fecha_limite     VARCHAR(10) NOT NULL,
        str_fecha_creacion   VARCHAR(10) NOT NULL
    );
    """)


def _insertarDatosSemilla(cur):
    """Carga datos de demostración realistas para el Subequipo 3B (Universidad ECCI)."""
    strHashDemo = Seguridad.cifrarPassword("Demo2026*")

    # 1. Integrantes del Subequipo 3B
    listaPersonasDemo = [
        ("138311", "Juan Morales", "juan.morales@ecci.edu.co", strHashDemo),
        ("149701", "Angel Castellanos", "angel.castellanos@ecci.edu.co", strHashDemo),
        ("127063", "Esteban Lopez", "esteban.lopez@ecci.edu.co", strHashDemo),
    ]
    for tplPersona in listaPersonasDemo:
        cur.execute(
            """
            INSERT INTO personas (str_documento, str_nombre, str_correo, str_password_hash)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (str_documento) DO NOTHING;
            """,
            tplPersona,
        )

    # 2. Cuentas Bancarias
    listaCuentasDemo = [
        ("4589-1029-3301", "138311", "Bancolombia", "Ahorros", 4280000.00),
        ("8810-4420-9912", "138311", "Davivienda", "Corriente", 1150000.00),
        ("EFEC-138311", "138311", "Efectivo Principal", "Efectivo", 320000.00),
        ("EFEC-149701", "149701", "Efectivo Principal", "Efectivo", 850000.00),
        ("3012-7741-0098", "149701", "Nequi / Bancolombia", "Ahorros", 2100000.00),
        ("EFEC-127063", "127063", "Efectivo Principal", "Efectivo", 640000.00),
    ]
    for tplCuenta in listaCuentasDemo:
        cur.execute(
            """
            INSERT INTO cuentas_bancarias
            (str_numero_cuenta, str_documento, str_entidad_bancaria, str_tipo_cuenta, dbl_saldo_actual)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (str_documento, str_numero_cuenta) DO NOTHING;
            """,
            tplCuenta,
        )

    # 3. Categorías personalizadas dinámicas
    listaCategoriasDemo = [
        (1, "138311", "Freelance Desarrollo", "Ingreso", 0.00),
        (2, "138311", "Suscripciones Cloud", "Gasto", 150000.00),
    ]
    for tplCat in listaCategoriasDemo:
        cur.execute(
            """
            INSERT INTO categorias_personalizadas
            (int_id_categoria, str_documento, str_nombre_categoria, str_tipo_movimiento, dbl_limite_sugerido)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING;
            """,
            tplCat,
        )

    # 4. Movimientos históricos
    listaMovimientosDemo = [
        ("138311", "Ingreso", "Nómina mensual septiembre", 3800000.00, "Salario", "2026-09-01", "4589-1029-3301"),
        ("138311", "Ingreso", "Soporte módulo backend", 650000.00, "Honorarios", "2026-09-14", "8810-4420-9912"),
        ("138311", "Gasto", "Canon de arrendamiento septiembre", 1200000.00, "Vivienda", "2026-09-03", "4589-1029-3301"),
        ("138311", "Gasto", "Mercado mensual familiar", 490000.00, "Alimentación", "2026-09-08", "4589-1029-3301"),
        ("138311", "Gasto", "Energía, agua y fibra óptica", 235000.00, "Servicios", "2026-09-12", "8810-4420-9912"),
        ("138311", "Gasto", "Transporte universidad y oficina", 180000.00, "Transporte", "2026-09-19", "EFEC-138311"),
        ("138311", "Ingreso", "Nómina mensual octubre", 3800000.00, "Salario", "2026-10-01", "4589-1029-3301"),
        ("138311", "Ingreso", "Rendimientos CDT trimestral", 320000.00, "Inversiones", "2026-10-15", "4589-1029-3301"),
        ("138311", "Gasto", "Canon de arrendamiento octubre", 1200000.00, "Vivienda", "2026-10-02", "4589-1029-3301"),
        ("138311", "Gasto", "Supermercado y proteínas", 540000.00, "Alimentación", "2026-10-10", "4589-1029-3301"),
        ("138311", "Gasto", "Servicios públicos e internet", 240000.00, "Servicios", "2026-10-14", "8810-4420-9912"),
        ("138311", "Gasto", "Libros técnicos y curso AWS", 290000.00, "Educación", "2026-10-21", "8810-4420-9912"),
        ("138311", "Ingreso", "Nómina mensual desarrollo de software", 3800000.00, "Salario", "2026-11-01", "4589-1029-3301"),
        ("138311", "Ingreso", "Consultoría API REST cliente externo", 950000.00, "Freelance Desarrollo", "2026-11-03", "8810-4420-9912"),
        ("138311", "Gasto", "Canon de arrendamiento noviembre", 1200000.00, "Vivienda", "2026-11-02", "4589-1029-3301"),
        ("138311", "Gasto", "Mercado quincenal y víveres (88% del tope)", 528000.00, "Alimentación", "2026-11-03", "4589-1029-3301"),
        ("138311", "Gasto", "Energía, fibra óptica e internet móvil", 245000.00, "Servicios", "2026-11-04", "8810-4420-9912"),
        ("138311", "Gasto", "Recarga movilidad urbana", 165000.00, "Transporte", "2026-11-04", "EFEC-138311"),
        ("138311", "Gasto", "Salidas fin de semana y cine (excede tope)", 280000.00, "Entretenimiento", "2026-11-05", "EFEC-138311"),
        ("138311", "Gasto", "Servidor AWS EC2 t3.small y dominio", 92000.00, "Suscripciones Cloud", "2026-11-05", "8810-4420-9912"),
        ("149701", "Ingreso", "Salario mensual noviembre", 3200000.00, "Salario", "2026-11-01", "3012-7741-0098"),
        ("149701", "Gasto", "Mercado y alimentación", 420000.00, "Alimentación", "2026-11-03", "EFEC-149701"),
    ]
    for idx, tplMov in enumerate(listaMovimientosDemo, start=1):
        cur.execute(
            """
            INSERT INTO movimientos
            (int_id, str_documento, str_tipo, str_descripcion, dbl_monto, str_categoria, str_fecha, str_numero_cuenta)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
            """,
            (idx, tplMov[0], tplMov[1], tplMov[2], tplMov[3], tplMov[4], tplMov[5], tplMov[6]),
        )

    # 5. Presupuestos (Umbral de alerta al 85% según RF-04)
    listaPresupuestosDemo = [
        ("138311", "Vivienda", 1300000.00, "2026-11", 85.0),
        ("138311", "Alimentación", 600000.00, "2026-11", 85.0),
        ("138311", "Servicios", 350000.00, "2026-11", 85.0),
        ("138311", "Transporte", 250000.00, "2026-11", 85.0),
        ("138311", "Entretenimiento", 250000.00, "2026-11", 85.0),
        ("138311", "Suscripciones Cloud", 150000.00, "2026-11", 85.0),
    ]
    for tplPres in listaPresupuestosDemo:
        cur.execute(
            """
            INSERT INTO presupuestos
            (str_documento, str_categoria, dbl_limite, str_periodo_mes_ano, dbl_porcentaje_alerta)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (str_documento, str_categoria) DO NOTHING;
            """,
            tplPres,
        )

    # 6. Metas de Ahorro (RF-05)
    listaMetasDemo = [
        (1, "138311", "Fondo de Emergencia (6 Meses)", 6000000.00, 3900000.00, "2027-04-30", "2026-06-01"),
        (2, "138311", "Workstation Portátil Desarrollo", 4500000.00, 3825000.00, "2026-12-20", "2026-07-15"),
        (3, "138311", "Derechos de Grado e Inmersión ECCI", 2500000.00, 950000.00, "2027-06-15", "2026-09-01"),
    ]
    for tplMeta in listaMetasDemo:
        cur.execute(
            """
            INSERT INTO metas_ahorro
            (int_id_meta, str_documento, str_nombre_meta, dbl_monto_objetivo, dbl_monto_acumulado, str_fecha_limite, str_fecha_creacion)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
            """,
            tplMeta,
        )


# =============================================================================
#  PERSONAS / USUARIOS
# =============================================================================

def consultarPersonas():
    inicializarBaseDatos()
    with _abrirConexion() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT str_documento, str_nombre, str_correo FROM personas ORDER BY str_nombre ASC;"
            )
            return [(r[0], r[1], r[2]) for r in cur.fetchall()]


def consultarPersonasCompletas():
    inicializarBaseDatos()
    with _abrirConexion() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT str_documento, str_nombre, str_correo, str_password_hash FROM personas ORDER BY str_nombre ASC;"
            )
            return [(r[0], r[1], r[2], r[3] or "") for r in cur.fetchall()]


def guardarPersona(strDocumento, strNombre, strCorreo, strPasswordHash=""):
    inicializarBaseDatos()
    with _abrirConexion() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO personas (str_documento, str_nombre, str_correo, str_password_hash)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (str_documento) DO UPDATE SET
                    str_nombre = EXCLUDED.str_nombre,
                    str_correo = EXCLUDED.str_correo,
                    str_password_hash = CASE
                        WHEN EXCLUDED.str_password_hash <> '' THEN EXCLUDED.str_password_hash
                        ELSE personas.str_password_hash
                    END;
                """,
                (strDocumento, strNombre, strCorreo, strPasswordHash),
            )
        conn.commit()


def actualizarPersona(strDocumento, strNombre, strCorreo, strPasswordHash=None):
    inicializarBaseDatos()
    with _abrirConexion() as conn:
        with conn.cursor() as cur:
            if strPasswordHash is not None and strPasswordHash != "":
                cur.execute(
                    """
                    UPDATE personas
                    SET str_nombre = %s, str_correo = %s, str_password_hash = %s
                    WHERE str_documento = %s;
                    """,
                    (strNombre, strCorreo, strPasswordHash, strDocumento),
                )
            else:
                cur.execute(
                    """
                    UPDATE personas
                    SET str_nombre = %s, str_correo = %s
                    WHERE str_documento = %s;
                    """,
                    (strNombre, strCorreo, strDocumento),
                )
        conn.commit()


# =============================================================================
#  CUENTAS BANCARIAS (RF-02)
# =============================================================================

def consultarCuentasBancarias():
    inicializarBaseDatos()
    with _abrirConexion() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT str_numero_cuenta, str_documento, str_entidad_bancaria, str_tipo_cuenta, dbl_saldo_actual
                FROM cuentas_bancarias
                ORDER BY str_entidad_bancaria ASC, str_numero_cuenta ASC;
                """
            )
            return [(r[0], r[1], r[2], r[3], float(r[4])) for r in cur.fetchall()]


def guardarCuentaBancaria(strNumeroCuenta, strDocumento, strEntidadBancaria, strTipoCuenta, dblSaldoActual):
    inicializarBaseDatos()
    with _abrirConexion() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO cuentas_bancarias
                (str_numero_cuenta, str_documento, str_entidad_bancaria, str_tipo_cuenta, dbl_saldo_actual)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (str_documento, str_numero_cuenta) DO UPDATE SET
                    str_entidad_bancaria = EXCLUDED.str_entidad_bancaria,
                    str_tipo_cuenta = EXCLUDED.str_tipo_cuenta,
                    dbl_saldo_actual = EXCLUDED.dbl_saldo_actual;
                """,
                (strNumeroCuenta, strDocumento, strEntidadBancaria, strTipoCuenta, float(dblSaldoActual)),
            )
        conn.commit()


def actualizarSaldoCuenta(strNumeroCuenta, strDocumento, dblNuevoSaldo):
    inicializarBaseDatos()
    with _abrirConexion() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE cuentas_bancarias
                SET dbl_saldo_actual = %s
                WHERE str_numero_cuenta = %s AND str_documento = %s;
                """,
                (float(dblNuevoSaldo), strNumeroCuenta, strDocumento),
            )
        conn.commit()


def eliminarCuentaBancaria(strNumeroCuenta, strDocumento):
    inicializarBaseDatos()
    with _abrirConexion() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM cuentas_bancarias WHERE str_numero_cuenta = %s AND str_documento = %s;",
                (strNumeroCuenta, strDocumento),
            )
        conn.commit()


# =============================================================================
#  CATEGORÍAS PERSONALIZADAS (RF-03)
# =============================================================================

def generarIdCategoria():
    inicializarBaseDatos()
    with _abrirConexion() as conn:
        with conn.cursor() as cur:
            if _motorActivo == "postgres":
                cur.execute("SELECT nextval('categorias_id_seq');")
            else:
                cur.execute("SELECT COALESCE(MAX(int_id_categoria), 0) + 1 FROM categorias_personalizadas;")
            intId = int(cur.fetchone()[0])
        conn.commit()
        return intId


def consultarCategorias():
    inicializarBaseDatos()
    with _abrirConexion() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT int_id_categoria, str_documento, str_nombre_categoria, str_tipo_movimiento, dbl_limite_sugerido
                FROM categorias_personalizadas
                ORDER BY int_id_categoria ASC;
                """
            )
            return [(int(r[0]), r[1], r[2], r[3], float(r[4])) for r in cur.fetchall()]


def guardarCategoria(intIdCategoria, strDocumento, strNombreCategoria, strTipoMovimiento, dblLimiteSugerido=0.0):
    inicializarBaseDatos()
    with _abrirConexion() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO categorias_personalizadas
                (int_id_categoria, str_documento, str_nombre_categoria, str_tipo_movimiento, dbl_limite_sugerido)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (int_id_categoria) DO UPDATE SET
                    str_nombre_categoria = EXCLUDED.str_nombre_categoria,
                    dbl_limite_sugerido = EXCLUDED.dbl_limite_sugerido;
                """,
                (int(intIdCategoria), strDocumento, strNombreCategoria, strTipoMovimiento, float(dblLimiteSugerido)),
            )
        conn.commit()


def eliminarCategoria(intIdCategoria, strDocumento):
    inicializarBaseDatos()
    with _abrirConexion() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM categorias_personalizadas WHERE int_id_categoria = %s AND str_documento = %s;",
                (int(intIdCategoria), strDocumento),
            )
        conn.commit()


# =============================================================================
#  MOVIMIENTOS / TRANSACCIONES (RF-03)
# =============================================================================

def generarIdMovimiento():
    inicializarBaseDatos()
    with _abrirConexion() as conn:
        with conn.cursor() as cur:
            if _motorActivo == "postgres":
                cur.execute("SELECT nextval('movimientos_id_seq');")
            else:
                cur.execute("SELECT COALESCE(MAX(int_id), 0) + 1 FROM movimientos;")
            intId = int(cur.fetchone()[0])
        conn.commit()
        return intId


def consultarMovimientos():
    inicializarBaseDatos()
    with _abrirConexion() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT int_id, str_documento, str_tipo, str_descripcion, dbl_monto, str_categoria, str_fecha
                FROM movimientos
                ORDER BY str_fecha DESC, int_id DESC;
                """
            )
            return [(int(r[0]), r[1], r[2], r[3], float(r[4]), r[5], r[6]) for r in cur.fetchall()]


def consultarMovimientosCompletos():
    inicializarBaseDatos()
    with _abrirConexion() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT int_id, str_documento, str_tipo, str_descripcion, dbl_monto,
                       str_categoria, str_fecha, str_numero_cuenta
                FROM movimientos
                ORDER BY str_fecha DESC, int_id DESC;
                """
            )
            return [(int(r[0]), r[1], r[2], r[3], float(r[4]), r[5], r[6], r[7] or "") for r in cur.fetchall()]


def guardarMovimiento(intId, strDocumento, strTipo, strDescripcion, dblMonto, strCategoria, strFecha, strNumeroCuenta=""):
    inicializarBaseDatos()
    with _abrirConexion() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO movimientos
                (int_id, str_documento, str_tipo, str_descripcion, dbl_monto, str_categoria, str_fecha, str_numero_cuenta)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                """,
                (int(intId), strDocumento, strTipo, strDescripcion, float(dblMonto), strCategoria, strFecha, strNumeroCuenta or ""),
            )
        conn.commit()


def eliminarMovimiento(intId):
    inicializarBaseDatos()
    with _abrirConexion() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM movimientos WHERE int_id = %s;", (int(intId),))
        conn.commit()


# =============================================================================
#  PRESUPUESTOS (RF-04)
# =============================================================================

def consultarPresupuestos():
    inicializarBaseDatos()
    with _abrirConexion() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT str_documento, str_categoria, dbl_limite FROM presupuestos ORDER BY str_categoria ASC;"
            )
            return [(r[0], r[1], float(r[2])) for r in cur.fetchall()]


def consultarPresupuestosCompletos():
    inicializarBaseDatos()
    with _abrirConexion() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT str_documento, str_categoria, dbl_limite, str_periodo_mes_ano, dbl_porcentaje_alerta
                FROM presupuestos
                ORDER BY str_categoria ASC;
                """
            )
            return [(r[0], r[1], float(r[2]), r[3] or "Todos", float(r[4])) for r in cur.fetchall()]


def guardarPresupuesto(strDocumento, strCategoria, dblLimite, strPeriodoMesAno="Todos", dblPorcentajeAlerta=85.0):
    inicializarBaseDatos()
    with _abrirConexion() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO presupuestos
                (str_documento, str_categoria, dbl_limite, str_periodo_mes_ano, dbl_porcentaje_alerta)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (str_documento, str_categoria) DO UPDATE SET
                    dbl_limite = EXCLUDED.dbl_limite,
                    str_periodo_mes_ano = EXCLUDED.str_periodo_mes_ano,
                    dbl_porcentaje_alerta = EXCLUDED.dbl_porcentaje_alerta;
                """,
                (strDocumento, strCategoria, float(dblLimite), strPeriodoMesAno, float(dblPorcentajeAlerta)),
            )
        conn.commit()


def eliminarPresupuesto(strDocumento, strCategoria):
    inicializarBaseDatos()
    with _abrirConexion() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM presupuestos WHERE str_documento = %s AND str_categoria = %s;",
                (strDocumento, strCategoria),
            )
        conn.commit()


# =============================================================================
#  METAS DE AHORRO (RF-05)
# =============================================================================

def generarIdMetaAhorro():
    inicializarBaseDatos()
    with _abrirConexion() as conn:
        with conn.cursor() as cur:
            if _motorActivo == "postgres":
                cur.execute("SELECT nextval('metas_ahorro_id_seq');")
            else:
                cur.execute("SELECT COALESCE(MAX(int_id_meta), 0) + 1 FROM metas_ahorro;")
            intId = int(cur.fetchone()[0])
        conn.commit()
        return intId


def consultarMetasAhorro():
    inicializarBaseDatos()
    with _abrirConexion() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT int_id_meta, str_documento, str_nombre_meta, dbl_monto_objetivo,
                       dbl_monto_acumulado, str_fecha_limite, str_fecha_creacion
                FROM metas_ahorro
                ORDER BY str_fecha_limite ASC, int_id_meta ASC;
                """
            )
            return [
                (int(r[0]), r[1], r[2], float(r[3]), float(r[4]), r[5], r[6])
                for r in cur.fetchall()
            ]


def guardarMetaAhorro(intIdMeta, strDocumento, strNombreMeta, dblMontoObjetivo, dblMontoAcumulado, strFechaLimite, strFechaCreacion):
    inicializarBaseDatos()
    with _abrirConexion() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO metas_ahorro
                (int_id_meta, str_documento, str_nombre_meta, dbl_monto_objetivo,
                 dbl_monto_acumulado, str_fecha_limite, str_fecha_creacion)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (int_id_meta) DO UPDATE SET
                    str_nombre_meta = EXCLUDED.str_nombre_meta,
                    dbl_monto_objetivo = EXCLUDED.dbl_monto_objetivo,
                    dbl_monto_acumulado = EXCLUDED.dbl_monto_acumulado,
                    str_fecha_limite = EXCLUDED.str_fecha_limite;
                """,
                (
                    int(intIdMeta),
                    strDocumento,
                    strNombreMeta,
                    float(dblMontoObjetivo),
                    float(dblMontoAcumulado),
                    strFechaLimite,
                    strFechaCreacion,
                ),
            )
        conn.commit()


def actualizarAcumuladoMeta(intIdMeta, strDocumento, dblNuevoAcumulado):
    inicializarBaseDatos()
    with _abrirConexion() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE metas_ahorro
                SET dbl_monto_acumulado = %s
                WHERE int_id_meta = %s AND str_documento = %s;
                """,
                (float(dblNuevoAcumulado), int(intIdMeta), strDocumento),
            )
        conn.commit()


def eliminarMetaAhorro(intIdMeta, strDocumento):
    inicializarBaseDatos()
    with _abrirConexion() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM metas_ahorro WHERE int_id_meta = %s AND str_documento = %s;",
                (int(intIdMeta), strDocumento),
            )
        conn.commit()
