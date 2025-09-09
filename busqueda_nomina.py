import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import os
import hashlib

# =========================
# Archivos
# =========================
USUARIOS_FILE = "usuarios.csv"
CONSULTAS_FILE = "consultas.csv"
MENSAJE_FILE = "mensaje.txt"
EXCEL_CACHE_FILE = "datos_cache.xlsx"  # cache local del Excel

# =========================
# Funciones
# =========================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# =========================
# Crear o corregir usuarios por defecto
# =========================
usuarios_default = pd.DataFrame([
    {
        "usuario": "acaracas",
        "password": hash_password("caracas"),
        "rol": "maestro",
        "nombre": "Administrador"
    },
    {
        "usuario": "lhernandez",
        "password": hash_password("lau"),
        "rol": "usuario",
        "nombre": "Luis Hernández"
    },
    {
        "usuario": "omperez",
        "password": hash_password("ositis"),
        "rol": "usuario",
        "nombre": "Omar Pérez"
    }
])

if not os.path.exists(USUARIOS_FILE):
    usuarios_default.to_csv(USUARIOS_FILE, index=False)
else:
    usuarios_df = pd.read_csv(USUARIOS_FILE)
    for _, row in usuarios_default.iterrows():
        if row["usuario"] not in usuarios_df["usuario"].values:
            usuarios_df = pd.concat([usuarios_df, pd.DataFrame([row])], ignore_index=True)
        else:
            usuarios_df.loc[usuarios_df["usuario"] == row["usuario"], ["password", "rol", "nombre"]] = \
                row[["password", "rol", "nombre"]].values
    usuarios_df.to_csv(USUARIOS_FILE, index=False)

# =========================
# Excel
# =========================
hojas_destino = [
    "NUEVO COSTEO", "COSTEO O.C.", "CORRES 2025", "BASE FEDERAL 2025", "BASE",
    "VALIDACION IMPROS", "REGISTRO REVERSOS", "CAMBIO DE ADSCRIPCION",
    "STATUS DE COMISION", "COMISIONES", "OFICIOS 2025-ENERO", "OFICIOS 2025-FEBRERO",
    "OFICIOS 2025-MARZO", "OFICIO 2025-JUNIO", "LIC. MARCELA.", "CONTRATOS",
    "MEMOS", "MTRA. NOELIA", "STATUS DE OFI. DEPÁCHADOS OLI", "COMISIONES (2)",
    "Hoja1 (5)", "NOMINA ACTUAL", "DIVERSOS", "FORMATOS DE DESC. DIV",
    "CHEQUES-REVERSOS", "PENSIONES Y FORMATOS"
]

def excel_col_to_index(col):
    col = col.upper()
    index = 0
    for char in col:
        index = index * 26 + (ord(char) - ord('A') + 1)
    return index - 1

@st.cache_data(show_spinner="Cargando Excel (desde cache local o Google Drive)...")
def cargar_datos_drive(file_id, hojas):
    # Si ya existe cache local, usarlo
    if os.path.exists(EXCEL_CACHE_FILE):
        xls = pd.ExcelFile(EXCEL_CACHE_FILE, engine="openpyxl")
    else:
        # Descargar de Google Drive
        url = f"https://drive.google.com/uc?export=download&id={file_id}"
        resp = requests.get(url)
        if resp.status_code != 200 or not resp.content[:2] == b'PK':
            st.error("No se pudo descargar el archivo o no es Excel válido.")
            return {}
        # Guardar archivo en cache local
        with open(EXCEL_CACHE_FILE, "wb") as f:
            f.write(resp.content)
        xls = pd.ExcelFile(BytesIO(resp.content), engine="openpyxl")

    # Leer hojas solicitadas
    data = {}
    for hoja in hojas:
        if hoja in xls.sheet_names:
            data[hoja] = pd.read_excel(xls, sheet_name=hoja, engine="openpyxl")
    return data

def buscar_coincidencias(data, valores_buscar):
    resultados = {}
    for hoja, df in data.items():
        if df.empty:
            continue
        filtro = pd.Series([True] * len(df))
        for valor in valores_buscar:
            if valor:
                cond = df.astype(str).apply(lambda col: col.str.upper().str.contains(valor.upper(), na=False))
                filtro &= cond.any(axis=1)
        df_filtrado = df[filtro]
        if not df_filtrado.empty:
            resultados[hoja] = df_filtrado
    return resultados

# =========================
# Interfaz Streamlit
# =========================
st.title("Control de Nómina Eventual - Búsqueda")

usuarios_df = pd.read_csv(USUARIOS_FILE)

# =========================
# Manejo de sesión
# =========================
if "logueado" not in st.session_state:
    st.session_state.logueado = False
    st.session_state.usuario = None
    st.session_state.rol = None

# =========================
# Login
# =========================
st.sidebar.title("🔑 Iniciar sesión")

if not st.session_state.logueado:
    usuario_input = st.sidebar.text_input("Usuario", key="usuario_login")
    password_input = st.sidebar.text_input("Contraseña", type="password", key="password_login")
    login_btn = st.sidebar.button("Entrar")

    if login_btn:
        hash_input = hash_password(password_input)
        match = usuarios_df[
            (usuarios_df["usuario"] == usuario_input) &
            (usuarios_df["password"] == hash_input)
        ]
        if not match.empty:
            st.session_state.logueado = True
            st.session_state.usuario = match.iloc[0]["usuario"]
            st.session_state.rol = match.iloc[0]["rol"]
            st.session_state.nombre = match.iloc[0]["nombre"]
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos.")

else:
    st.sidebar.success(f"Conectado como {st.session_state.usuario} ({st.session_state.rol})")
    if st.sidebar.button("Cerrar sesión"):
        st.session_state.clear()
        st.rerun()

    # =========================
    # Administración de usuarios (solo maestro)
    # =========================
    if st.session_state.rol == "maestro":
        st.sidebar.subheader("👥 Administración de usuarios")
        menu_admin = st.sidebar.selectbox(
            "Selecciona acción", ["--", "Agregar usuario", "Eliminar usuario", "Editar usuario", "Editar mensaje bienvenida"]
        )

        if menu_admin == "Agregar usuario":
            nuevo_usuario = st.sidebar.text_input("Usuario nuevo")
            nuevo_password = st.sidebar.text_input("Contraseña", type="password")
            nuevo_rol = st.sidebar.selectbox("Rol", ["usuario", "maestro"])
            nuevo_nombre = st.sidebar.text_input("Nombre completo")
            if st.sidebar.button("Guardar nuevo usuario"):
                if nuevo_usuario and nuevo_password:
                    df_nuevo = pd.DataFrame([[nuevo_usuario, hash_password(nuevo_password), nuevo_rol, nuevo_nombre]],
                                            columns=["usuario","password","rol","nombre"])
                    usuarios_df = pd.concat([usuarios_df, df_nuevo], ignore_index=True)
                    usuarios_df.to_csv(USUARIOS_FILE, index=False)
                    st.sidebar.success("Usuario agregado correctamente")

        elif menu_admin == "Eliminar usuario":
            seleccionar_usuario = st.sidebar.selectbox("Selecciona usuario a eliminar", usuarios_df["usuario"])
            if st.sidebar.button("Eliminar"):
                usuarios_df = usuarios_df[usuarios_df["usuario"] != seleccionar_usuario]
                usuarios_df.to_csv(USUARIOS_FILE, index=False)
                st.sidebar.success("Usuario eliminado")

        elif menu_admin == "Editar usuario":
            seleccionar_usuario = st.sidebar.selectbox("Selecciona usuario a editar", usuarios_df["usuario"])
            nueva_password = st.sidebar.text_input("Nueva contraseña", type="password")
            nuevo_rol = st.sidebar.selectbox("Nuevo rol", ["usuario", "maestro"])
            nuevo_nombre = st.sidebar.text_input("Nuevo nombre completo")
            if st.sidebar.button("Guardar cambios"):
                if nueva_password:
                    usuarios_df.loc[usuarios_df["usuario"] == seleccionar_usuario, "password"] = hash_password(nueva_password)
                usuarios_df.loc[usuarios_df["usuario"] == seleccionar_usuario, "rol"] = nuevo_rol
                if nuevo_nombre:
                    usuarios_df.loc[usuarios_df["usuario"] == seleccionar_usuario, "nombre"] = nuevo_nombre
                usuarios_df.to_csv(USUARIOS_FILE, index=False)
                st.sidebar.success("Usuario actualizado")

        elif menu_admin == "Editar mensaje bienvenida":
            mensaje_bienvenida = ""
            if os.path.exists(MENSAJE_FILE):
                with open(MENSAJE_FILE, "r", encoding="utf-8") as f:
                    mensaje_bienvenida = f.read()
            nuevo_mensaje = st.sidebar.text_input("Mensaje de bienvenida", value=mensaje_bienvenida)
            if st.sidebar.button("Guardar mensaje"):
                with open(MENSAJE_FILE, "w", encoding="utf-8") as f:
                    f.write(nuevo_mensaje)
                st.sidebar.success("Mensaje actualizado")

    # =========================
    # Campos de búsqueda (solo si logueado)
    # =========================
    st.title("🔍 Buscar en Nómina")

    file_id = "17O33v9JmMsItavMNm7qw4MX2Zx_K7a2f"

    # Botón actualizar datos solo para maestro
    if st.session_state.rol == "maestro":
        if st.button("Actualizar datos de base"):
            if os.path.exists(EXCEL_CACHE_FILE):
                os.remove(EXCEL_CACHE_FILE)   # borra cache local
            cargar_datos_drive.clear()        # borra cache de streamlit
            st.success("Caché borrado. La próxima búsqueda descargará el archivo actualizado desde Drive.")

    # Inputs de búsqueda
    col1, col2 = st.columns(2)
    rfc = col1.text_input("RFC", key="rfc")
    nombre = col2.text_input("NOMBRE", key="nombre_busqueda")
    col3, col4 = st.columns(2)
    oficio_solicitud = col3.text_input("OFICIO DE SOLICITUD", key="oficio_solicitud")
    adscripcion = col4.text_input("ADSCRIPCION", key="adscripcion")
    col5, col6 = st.columns(2)
    cuenta = col5.text_input("CUENTA", key="cuenta")
    oficio_elaborado = col6.text_input("OFICIO ELABORADO", key="oficio_elaborado")

    # Botón buscar
    if st.button("Buscar"):
        try:
            data = cargar_datos_drive(file_id, hojas_destino)
            valores = [rfc.strip(), nombre.strip(), oficio_solicitud.strip(),
                       adscripcion.strip(), cuenta.strip(), oficio_elaborado.strip()]
            resultados = buscar_coincidencias(data, valores)

            # Guardar consultas
            consulta = {"usuario": st.session_state.usuario, "criterios": str(valores)}
            if os.path.exists(CONSULTAS_FILE):
                consultas_df = pd.read_csv(CONSULTAS_FILE)
                nuevo_df = pd.DataFrame([consulta])
                consultas_df = pd.concat([consultas_df, nuevo_df], ignore_index=True)
            else:
                consultas_df = pd.DataFrame([consulta])
            consultas_df.to_csv(CONSULTAS_FILE, index=False)

            if not resultados:
                st.info("No se encontraron coincidencias.")
            else:
                for hoja, df_res in resultados.items():
                    st.subheader(f"Resultados de '{hoja}'")
                    st.dataframe(df_res, width=1500, height=180)
        except Exception as e:
            st.error(f"Error al procesar: {e}")

    # Limpiar
    if st.button("Limpiar"):
        st.experimental_rerun()

    # =========================
    # Pie de página
    # =========================
    st.markdown(
        """
        <hr>
        <div style='text-align: center; font-size: 12px; color: gray;'>
            © Derechos Reservados. LACB  =)
        </div>
        """,
        unsafe_allow_html=True
    )
