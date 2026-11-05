-- =============================================================================
-- Esquema Relacional PostgreSQL - Sistema de Gestión de Finanzas Personales
-- Universidad ECCI - Proyecto Integrador PyA 2ANL 2026-2 (Subequipo 3B)
-- Garantiza integridad referencial y transaccionalidad ACID
-- =============================================================================

CREATE TABLE IF NOT EXISTS personas (
    str_documento      VARCHAR(30) PRIMARY KEY,
    str_nombre         VARCHAR(150) NOT NULL,
    str_correo         VARCHAR(150) NOT NULL UNIQUE,
    str_password_hash  VARCHAR(300) NOT NULL DEFAULT '',
    dt_fecha_registro  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cuentas_bancarias (
    str_numero_cuenta    VARCHAR(50) NOT NULL,
    str_documento        VARCHAR(30) NOT NULL REFERENCES personas(str_documento) ON DELETE CASCADE,
    str_entidad_bancaria VARCHAR(100) NOT NULL,
    str_tipo_cuenta      VARCHAR(30) NOT NULL CHECK (str_tipo_cuenta IN ('Ahorros', 'Corriente', 'Efectivo')),
    dbl_saldo_actual     NUMERIC(16, 2) NOT NULL DEFAULT 0,
    PRIMARY KEY (str_documento, str_numero_cuenta)
);

CREATE SEQUENCE IF NOT EXISTS categorias_id_seq START WITH 1 INCREMENT BY 1;

CREATE TABLE IF NOT EXISTS categorias_personalizadas (
    int_id_categoria      INTEGER PRIMARY KEY DEFAULT nextval('categorias_id_seq'),
    str_documento         VARCHAR(30) NOT NULL REFERENCES personas(str_documento) ON DELETE CASCADE,
    str_nombre_categoria  VARCHAR(80) NOT NULL,
    str_tipo_movimiento   VARCHAR(20) NOT NULL CHECK (str_tipo_movimiento IN ('Ingreso', 'Gasto')),
    dbl_limite_sugerido   NUMERIC(16, 2) NOT NULL DEFAULT 0,
    UNIQUE (str_documento, str_nombre_categoria, str_tipo_movimiento)
);

CREATE SEQUENCE IF NOT EXISTS movimientos_id_seq START WITH 1 INCREMENT BY 1;

CREATE TABLE IF NOT EXISTS movimientos (
    int_id            INTEGER PRIMARY KEY DEFAULT nextval('movimientos_id_seq'),
    str_documento     VARCHAR(30) NOT NULL REFERENCES personas(str_documento) ON DELETE CASCADE,
    str_tipo          VARCHAR(20) NOT NULL CHECK (str_tipo IN ('Ingreso', 'Gasto')),
    str_descripcion   VARCHAR(255) NOT NULL,
    dbl_monto         NUMERIC(16, 2) NOT NULL CHECK (dbl_monto > 0),
    str_categoria     VARCHAR(80) NOT NULL,
    str_fecha         VARCHAR(10) NOT NULL,
    str_numero_cuenta VARCHAR(50) NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS presupuestos (
    str_documento          VARCHAR(30) NOT NULL REFERENCES personas(str_documento) ON DELETE CASCADE,
    str_categoria          VARCHAR(80) NOT NULL,
    dbl_limite             NUMERIC(16, 2) NOT NULL CHECK (dbl_limite > 0),
    str_periodo_mes_ano    VARCHAR(20) NOT NULL DEFAULT 'Todos',
    dbl_porcentaje_alerta  NUMERIC(5, 2) NOT NULL DEFAULT 85.00,
    PRIMARY KEY (str_documento, str_categoria)
);

CREATE SEQUENCE IF NOT EXISTS metas_ahorro_id_seq START WITH 1 INCREMENT BY 1;

CREATE TABLE IF NOT EXISTS metas_ahorro (
    int_id_meta          INTEGER PRIMARY KEY DEFAULT nextval('metas_ahorro_id_seq'),
    str_documento        VARCHAR(30) NOT NULL REFERENCES personas(str_documento) ON DELETE CASCADE,
    str_nombre_meta      VARCHAR(120) NOT NULL,
    dbl_monto_objetivo   NUMERIC(16, 2) NOT NULL CHECK (dbl_monto_objetivo > 0),
    dbl_monto_acumulado  NUMERIC(16, 2) NOT NULL DEFAULT 0,
    str_fecha_limite     VARCHAR(10) NOT NULL,
    str_fecha_creacion   VARCHAR(10) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_movimientos_persona_fecha ON movimientos(str_documento, str_fecha DESC);
CREATE INDEX IF NOT EXISTS idx_cuentas_persona ON cuentas_bancarias(str_documento);
CREATE INDEX IF NOT EXISTS idx_metas_persona ON metas_ahorro(str_documento);
