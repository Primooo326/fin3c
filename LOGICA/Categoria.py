# =============================================================================
#  Clase Categoria: Categoría dinámica personalizable de ingreso o gasto (RF-03)
#  Modelado Orientado a Objetos (Matriz de Diseño UML - Universidad ECCI)
#  Capa: LOGICA
# =============================================================================


class Categoria:

    STR_TIPO_INGRESO = "Ingreso"
    STR_TIPO_GASTO = "Gasto"

    # ---- Constructor ---------------------------------------------------------
    def __init__(self, intIdCategoria, strNombreCategoria, strTipoMovimiento, dblLimiteSugerido=0.0):
        self.__intIdCategoria = int(intIdCategoria)
        self.__strNombreCategoria = str(strNombreCategoria).strip()
        self.__strTipoMovimiento = str(strTipoMovimiento).strip()
        self.__dblLimiteSugerido = float(dblLimiteSugerido)

    # ---- Operaciones UML / Negocio -------------------------------------------
    def modificarCategoria(self, strNuevoNombre, dblNuevoLimiteSugerido=None):
        """Actualiza el nombre y opcionalmente el límite sugerido de la categoría."""
        strLimpio = str(strNuevoNombre).strip()
        if strLimpio == "":
            return False
        self.__strNombreCategoria = strLimpio
        if dblNuevoLimiteSugerido is not None and float(dblNuevoLimiteSugerido) >= 0:
            self.__dblLimiteSugerido = float(dblNuevoLimiteSugerido)
        return True

    def clasificarMovimiento(self, movimiento):
        """Asocia la categoría actual a un objeto Movimiento si coincide el tipo."""
        if movimiento is not None and movimiento.getStrTipo() == self.__strTipoMovimiento:
            movimiento.setStrCategoria(self.__strNombreCategoria)

    # Alias exactos de la Matriz UML (Sección 4 del Documento)
    def Crear_Categoria(self, strNombre, strTipo):
        if strNombre.strip() == "" or strTipo not in (Categoria.STR_TIPO_INGRESO, Categoria.STR_TIPO_GASTO):
            return False
        self.__strNombreCategoria = strNombre.strip()
        self.__strTipoMovimiento = strTipo
        return True

    def Clasificar_Movimiento(self, movimiento):
        self.clasificarMovimiento(movimiento)

    def Modificar_Categoria(self, intId, strNuevoNombre):
        if int(intId) != self.__intIdCategoria:
            return False
        return self.modificarCategoria(strNuevoNombre)

    # ---- Serialización para Servicio Web -------------------------------------
    def toDict(self, boolPersonalizada=True):
        return {
            "intIdCategoria": self.__intIdCategoria,
            "strNombreCategoria": self.__strNombreCategoria,
            "strTipoMovimiento": self.__strTipoMovimiento,
            "dblLimiteSugerido": self.__dblLimiteSugerido,
            "boolPersonalizada": boolPersonalizada,
        }

    # ---- Getters y setters ---------------------------------------------------
    def getIntIdCategoria(self):
        return self.__intIdCategoria

    def getStrNombreCategoria(self):
        return self.__strNombreCategoria

    def setStrNombreCategoria(self, strNombreCategoria):
        self.__strNombreCategoria = str(strNombreCategoria).strip()

    def getStrTipoMovimiento(self):
        return self.__strTipoMovimiento

    def setStrTipoMovimiento(self, strTipoMovimiento):
        self.__strTipoMovimiento = str(strTipoMovimiento).strip()

    def getDblLimiteSugerido(self):
        return self.__dblLimiteSugerido

    def setDblLimiteSugerido(self, dblLimiteSugerido):
        self.__dblLimiteSugerido = float(dblLimiteSugerido)
