import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import os
import hashlib

# =========================
# Configuración de usuarios
# =========================
USUARIOS_FILE = "usuarios.csv"
CONSULTAS_FILE = "consultas.csv"
MENSAJE_FILE = "mensaje_bienvenida.txt"

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Crear usuario maestro si no existe
if not os.path.exists(USUARIOS_FILE):
    df = pd.DataFrame([["acaracas", hash_password("caracas"), "maestro", "Administrador"]],
                      columns=["usuario", "password", "rol", "nombre"])
    df.to_csv(USUARIOS_FILE, index=False)
else:
    usuarios_df = pd.read_csv(USUARIOS_FILE)
    if "acaracas" not in usuarios_df["usuario"].values:
        nuevo_usuario_df = pd.DataFrame([{
            "usuario": "acaracas",
            "password": hash_password("caracas"),
            "rol": "maestro",
            "nombre": "Administrador"
        }])
        usuarios_df = pd.concat([usuarios_df, nuevo_usuario_df], ignore_index=True)
        usuarios_df.to_csv(USUARIOS_FILE, index=False)

# =========================
# Funciones de Excel
# =========================
hojas_destino = [
    "NUEVO COSTEO", "COSTEO O.C.", "CORRES 2025", "BASE FEDERAL 2025", "BASE", "VALIDACION IMPROS", "REGISTRO REVERSOS",
    "CAMBIO DE ADSCRIPCION", "STATUS DE COMISION", "COMISIONES", "OFICIOS 2025-ENERO", "OFICIOS 2025-FEBRERO",
    "OFICIOS 2025-MARZO", "OFICIO 2025-JUNIO", "LIC. MARCELA.", "CONTRATOS", "MEMOS", "MTRA. NOELIA",
    "STATUS DE OFI. DEPÁCHADOS OLI", "COMISIONES (2)", "Hoja1 (5)", "NOMINA ACTUAL",
    "DIVERSOS", "FORMATOS DE DESC. DIV", "CHEQUES-REVERSOS", "PENSIONES Y FORMATOS"
]

columnas_condicionantes = [
    ["C", "C", "", "D", "", "E", "E"] + [""] * 14 + ["C"] + ["B", "B", "B", "B"],
    ["E", "D", "J", "E", "", "F", "F", "D", "C", "D", "C", "C", "C", "C", "E", "E", "E", "E", "E", "E", "D", "D"] + ["C", "C", "C", "C"],
    ["AC", "I", "D", "J", "", "", "", "B", "", "B", "", "", "", "A", "", "", "", "", "", "", "", ""] + ["", "", "", ""],
    ["P", "V", "D,I", "W", "", "L", "L", "", "D", "", "", "", "", "", "", "", "", "", "", "", "", "G"] + ["", "", "", ""],
    ["AE", "X", "", "Y", "", "M", "M"] + [""] * 14 + ["O"] + ["", "", "", ""],
    [""] * 7 + ["G", "A", "G", "A", "A", "A", "F", "C", "C", "C", "C", "C", "C", "B"] + [""] + ["", "", "", ""]
]

def excel_col_to_index(col):
    col = col.upper()
    index = 0
    for char in col:
        index = index * 26 + (ord(char) - ord('A') + 1)
    return index - 1

@st.cache_data(show_spinner="Descargando y procesando Excel desde Google Drive...")
def cargar_datos_drive(file_id, hojas):
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    resp = requests.get(url)
    if resp.status_code != 200:
        st.error("No se pudo descargar el archivo desde Google Drive. Verifica permisos o el ID.")
        return {}
    if not resp.content[:2] == b'PK':
        st.error("El archivo descargado no es un Excel válido. Verifica el ID o permisos.")
        return {}
    xls = pd.ExcelFile(BytesIO(resp.content), engine="openpyxl")
    data = {}
    for hoja in hojas:
        if hoja in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=hoja, engine="openpyxl")
            data[hoja] = df
    return data

def buscar_coincidencias(data, valores_buscar):
    resultados = {}
    for j, hoja in enumerate(hojas_destino):
        if hoja not in data:
            continue
        df = data[hoja]
        if df.empty:
            continue
        filtro = pd.Series([True] * len(df))
        for i, valor in enumerate(valores_buscar):
            if valor:
                cols_str = columnas_condicionantes[i][j]
                if not cols_str:
                    filtro &= False
                    continue
                cols = [excel_col_to_index(c.strip()) for c in cols_str.split(",")]
                cond = pd.Series([False] * len(df))
                for col_idx in cols:
                    if col_idx < len(df.columns):
                        cond |= df.iloc[:, col_idx].astype(str).str.upper().str.contains(valor.upper(), na=False)
                filtro &= cond
        df_filtrado = df[filtro]
        if not df_filtrado.empty:
            resultados[hoja] = df_filtrado
    return resultados

# =========================
# Interfaz Streamlit
# =========================
st.title("Control de Nómina Eventual - Búsqueda")

# Login
st.sidebar.title("🔑 Iniciar sesión")
usuario_input = st.sidebar.text_input("Usuario")
password_input = st.sidebar.text_input("Contraseña", type="password")
login_btn = st.sidebar.button("Entrar")

usuarios_df = pd.read_csv(USUARIOS_FILE)
usuario_valido = False
rol_usuario = None
nombre_usuario = ""

if login_btn:
    hash_input = hash_password(password_input)
    match = usuarios_df[(usuarios_df["usuario"] == usuario_input) & (usuarios_df["password"] == hash_input)]
    if not match.empty:
        usuario_valido = True
        rol_usuario = match.iloc[0]["rol"]
        nombre_usuario = match.iloc[0]["nombre"]
        # Cargar mensaje de bienvenida
        if os.path.exists(MENSAJE_FILE):
            with open(MENSAJE_FILE, "r", encoding="utf-8") as f:
                mensaje_bienvenida = f.read()
        else:
            mensaje_bienvenida = "Bienvenido"
        st.success(f"{mensaje_bienvenida}, {nombre_usuario} ({rol_usuario})")
    else:
        st.error("Usuario o contraseña incorrectos.")

if not login_btn or not usuario_valido:
    st.stop()

# ID fijo del archivo
file_id = "17O33v9JmMsItavMNm7qw4MX2Zx_K7a2f"

# Botón actualizar datos solo para maestro
if rol_usuario == "maestro":
    if st.button("Actualizar datos de base"):
        cargar_datos_drive.clear()
        st.success("Caché limpiada. La próxima búsqueda descargará el archivo actualizado.")

# =========================
# Administración de usuarios (solo maestro)
# =========================
if rol_usuario == "maestro":
    st.sidebar.subheader("👥 Administración de usuarios")
    st.sidebar.text("Agregar / Eliminar usuarios")

    # Agregar usuario
    with st.sidebar.expander("Agregar usuario"):
        nuevo_usuario = st.text_input("Usuario")
        nueva_contraseña = st.text_input("Contraseña", type="password")
        rol_nuevo = st.selectbox("Rol", ["usuario", "maestro"])
        nombre_nuevo = st.text_input("Nombre completo")
        if st.button("Agregar"):
            if nuevo_usuario and nueva_contraseña:
                hash_pass = hash_password(nueva_contraseña)
                nuevo_df = pd.DataFrame([{
                    "usuario": nuevo_usuario,
                    "password": hash_pass,
                    "rol": rol_nuevo,
                    "nombre": nombre_nuevo
                }])
                usuarios_df = pd.concat([usuarios_df, nuevo_df], ignore_index=True)
                usuarios_df.to_csv(USUARIOS_FILE, index=False)
                st.success(f"Usuario {nuevo_usuario} agregado")

    # Eliminar usuario
    with st.sidebar.expander("Eliminar usuario"):
        usuario_eliminar = st.selectbox("Selecciona usuario", usuarios_df["usuario"].tolist())
        if st.button("Eliminar"):
            usuarios_df = usuarios_df[usuarios_df["usuario"] != usuario_eliminar]
            usuarios_df.to_csv(USUARIOS_FILE, index=False)
            st.success(f"Usuario {usuario_eliminar} eliminado")

    # Mensaje de bienvenida editable
    with st.sidebar.expander("Mensaje de bienvenida"):
        nuevo_mensaje = st.text_area("Mensaje para los usuarios", value=mensaje_bienvenida)
        if st.button("Guardar mensaje"):
            with open(MENSAJE_FILE, "w", encoding="utf-8") as f:
                f.write(nuevo_mensaje)
            st.success("Mensaje actualizado")

# =========================
# Campos de búsqueda
# =========================
col1, col2 = st.columns(2)
rfc = col1.text_input("RFC", key="rfc")
nombre = col2.text_input("NOMBRE", key="nombre")
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
        valores = [rfc.strip(), nombre.strip(), oficio_solicitud.strip(), adscripcion.strip(), cuenta.strip(), oficio_elaborado.strip()]
        resultados = buscar_coincidencias(data, valores)

        # Guardar consultas
        consulta = {
            "usuario": usuario_input,
            "criterios": str(valores)
        }
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
