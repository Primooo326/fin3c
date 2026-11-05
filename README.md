# 🌿 Sistema de Gestión de Finanzas Personales (Escritorio & Web)

**Universidad ECCI — Facultad de Ingeniería — Tecnología en Desarrollo Informático**  
**Proyecto Integrador (`PyA 2ANL 2026-2`) — Equipo 3 Subequipo B**  
**Integrantes:** Juan Morales (`138311`) • Angel Castellanos (`149701`) • Esteban Lopez (`127063`)

---

## 1. Arquitectura en Capas Implementada

El proyecto respeta estrictamente el desacoplamiento por capas y el modelado orientado a objetos (POO) con nomenclatura húngara (`str`, `dbl`, `int`, `dt`) definido en el documento oficial:

```text
finanzas_personales_ecci/
├── .env                          # Credenciales PostgreSQL y llave HMAC de sesión
├── docker-compose.yml            # PostgreSQL 16 listo para levantar en 1 comando
├── requirements.txt              # Dependencias Python (FastAPI, Psycopg, ReportLab, OpenPyXL)
├── main.py                       # Lanzador principal del servidor web FastAPI / Uvicorn
├── LOGICA/                       # Capa de Dominio POO y Reglas de Negocio (Retrocompatible)
│   ├── Seguridad.py              # Cifrado y verificación PBKDF2-HMAC-SHA256 (RNF-01)
│   ├── Persona.py                # Clase Persona / Usuario (RF-01)
│   ├── CuentaBancaria.py         # Clase CuentaBancaria con sobregiro advertido (RF-02)
│   ├── Categoria.py              # Clase Categoria dinámica personalizable (RF-03)
│   ├── Movimiento.py             # Clase Movimiento / Transaccion (RF-03)
│   ├── Presupuesto.py            # Clase Presupuesto con umbral preventivo al 85% (RF-04)
│   ├── MetaAhorro.py             # Clase MetaAhorro con abonos y fecha proyectada (RF-05)
│   ├── ReporteFinanciero.py      # Clase ReporteFinanciero con exportación PDF y Excel (RF-06)
│   └── GestorFinanzas.py         # Controlador Fachada Singleton (Web + Ventanas Escritorio)
├── PERSISTENCIA/                 # Capa de Datos Relacional ACID en PostgreSQL
│   ├── schema.sql                # DDL de tablas, claves foráneas, índices y secuencias
│   └── DatosFinanzas.py          # Conector PostgreSQL, migración automática y datos semilla
└── SERVICIO_WEB/                 # Capa de Servicio Web REST + Interfaz Responsiva
    ├── app.py                    # Endpoints REST FastAPI (/api/*) + Swagger (/docs)
    ├── dependencias.py           # Autenticación mediante tokens firmados HMAC-SHA256
    └── static/                   # SPA Responsiva (Tema Fresh Mint & Emerald + Plus Jakarta Sans)
```

---

## 2. Cumplimiento 100% de Requerimientos

| Código | Requerimiento | Implementación |
| :--- | :--- | :--- |
| **RF-01** | Gestión de Usuarios | Registro, perfil y login por correo o documento en `Persona` y `/api/auth/*`. |
| **RF-02** | Cuentas Bancarias | Administración de cuentas **Ahorros**, **Corriente** y **Efectivo** (`CuentaBancaria.py`), con sobregiro permitido y advertencia visual inmediata. |
| **RF-03** | Movimientos y Categorías | Registro y anulación de ingresos/gastos impactando automáticamente el saldo de la cuenta asociada, más creación de **categorías personalizadas dinámicas** (`Categoria.py`). |
| **RF-04** | Presupuestos y Alertas | Techos por categoría con alerta visual preventiva automática al **85%** de ejecución y alerta roja al superar el **100%** (`Presupuesto.py`). |
| **RF-05** | Metas de Ahorro | Metas programadas con abonos progresivos, cuota mensual sugerida y cálculo automático de **fecha proyectada** según ritmo real (`MetaAhorro.py`). |
| **RF-06** | Reportes y Estadísticas | Consolidación por rango de fechas, gráficas comparativas Chart.js y descarga nativa en **PDF** (`ReportLab`) y **Excel `.xlsx`** (`OpenPyXL`). |
| **RNF-01** | Seguridad y Cifrado | Contraseñas cifradas con **PBKDF2-HMAC-SHA256** (260,000 iteraciones + sal criptográfica aleatoria) en `Seguridad.py`. |
| **RNF-03** | Usabilidad e Interfaz | Tema claro *Fresh Mint & Emerald*, fuente `Plus Jakarta Sans`, Sidebar en escritorio y barra inferior tipo App (*Bottom-Nav*) en móviles. |

---

## 3. Cómo Ejecutar el Proyecto Paso a Paso

### Paso 1: Levantar PostgreSQL
Si tienes **Docker**, levanta la base de datos lista con un solo comando desde esta carpeta:
```powershell
docker compose up -d
```
*(Si ya cuentas con un servidor PostgreSQL local o en AWS RDS/EC2, simplemente edita los valores `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER` y `DB_PASSWORD` en el archivo `.env`). Al arrancar por primera vez, el sistema crea todas las tablas automáticamente y precarga los datos de demostración del Subequipo 3B.*

### Paso 2: Instalar dependencias de Python (Python 3.11 / 3.12+)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Paso 3: Iniciar el Servicio Web
```powershell
python main.py
```

Abre en tu navegador o celular:
* **Aplicación Web Responsiva:** http://localhost:8000
* **Documentación Interactiva API REST (Swagger):** http://localhost:8000/docs

### Credenciales Demo Precargadas (Sustentación)
* **Usuario completo con alertas al 88%, sobrecosto, metas y 3 meses de historial:**
  * Identificador: `138311` o `juan.morales@ecci.edu.co`
  * Contraseña: `Demo2026*` *(o clic directo en el botón de Acceso Rápido en pantalla)*
* **Otros integrantes del equipo:** `149701` (Angel Castellanos) y `127063` (Esteban Lopez) — Contraseña: `Demo2026*`

---

## 4. Despliegue en AWS EC2 Ubuntu + Nginx (RNF-05 y RNF-06)

En una instancia **AWS EC2 `t3.small` (Ubuntu Server LTS)** con PostgreSQL en el puerto `5432`:

```bash
# Ejecutar con Gunicorn + trabajadores ASGI Uvicorn detrás de Nginx Proxy Inverso
pip install gunicorn
gunicorn SERVICIO_WEB.app:app -k uvicorn.workers.UvicornWorker --bind unix:/run/finanzas.sock --workers 3
```
Configura Nginx apuntando `proxy_pass http://unix:/run/finanzas.sock;` y habilita HTTPS con `certbot --nginx -d tu-subdominio.com`.
