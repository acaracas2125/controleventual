import pandas as pd
import streamlit as st
import requests
from io import BytesIO
import hashlib
import os

# -------------------------
# Configuración de archivos
# -------------------------
USUARIOS_FILE = "usuarios.csv"
CONSULTAS_FILE = "consultas.csv"

# -------------------------
# Funciones de seguridad
# -------------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def cargar_usuarios():
    if not os.path.exists(USUARIOS_FILE):
        # Crear archivo inicial con un usuario maestro
        df = pd.DataFrame([["maestro", hash_password("maestro123"), "maestro"]], columns=["usuario","password","rol"])
        df.to_csv(USUARIOS_FILE, index=False)
    else:
        df = pd.read_csv(USUARIOS_FILE)
    return df

def guardar_usuarios(df):
    df.to_csv(USUARIOS_FILE, index=False)

def registrar_consulta(usuario, criterio):
    if os.path.exists(CONSULTAS_FILE):
        df = pd.read_csv(CONSULTAS_FILE)
    else:
        df = pd.DataFrame(columns=["usuario","criterio"])
    df = pd.concat([df, pd.DataFrame([[usuario, criterio]], columns=["usuario","criterio"])], ignore_index=True)
    df.to_csv(CONSULTAS_FILE, index=False)

# -------------------------
# Cargar usuarios y login
# -------------------------
usuarios_df = cargar_usuarios()

st.sidebar.title("🔒 Login")
usuario_input = st.sidebar.text_input("Usuario")
password_input = st.sidebar.text_input("Contraseña", type="password")
login_btn = st.sidebar.button("Iniciar sesión")

user_rol = None

if login_btn:
    user_row = usuarios_df[usuarios_df["usuario"]==usuario_input]
    if not user_row.empty and user_row.iloc[0]["password"] == hash_password(password_input):
        st.session_state["usuario"] = usuario_input
        user_rol = user_row.iloc[0]["rol"]
        st.success(f"Bienvenido {usuario_input} ({user_rol})")
    else:
        st.error("Usuario o contraseña incorrectos")

# -------------------------
# Si no ha iniciado sesión
# -------------------------
if "usuario" not in st.session_state:
    st.stop()

# -------------------------
# Gestión de usuarios (solo maestro)
# -------------------------
if user_rol == "maestro":
    st.sidebar.subheader("Administración de usuarios")
    action = st.sidebar.selectbox("Acción", ["Agregar usuario", "Eliminar usuario", "Cambiar rol", "Cambiar contraseña"])
    
    if action == "Agregar usuario":
        nuevo_user = st.sidebar.text_input("Nuevo usuario")
        nueva_pass = st.sidebar.text_input("Contraseña", type="password")
        rol = st.sidebar.selectbox("Rol", ["usuario","maestro"])
        if st.sidebar.button("Agregar"):
            if nuevo_user in usuarios_df["usuario"].values:
                st.sidebar.error("El usuario ya existe")
            else:
                usuarios_df = pd.concat([usuarios_df, pd.DataFrame([[nuevo_user, hash_password(nueva_pass), rol]], columns=["usuario","password","rol"])], ignore_index=True)
                guardar_usuarios(usuarios_df)
                st.sidebar.success("Usuario agregado")

    elif action == "Eliminar usuario":
        eliminar_user = st.sidebar.selectbox("Usuario a eliminar", usuarios_df["usuario"].tolist())
        if st.sidebar.button("Eliminar"):
            usuarios_df = usuarios_df[usuarios_df["usuario"] != eliminar_user]
            guardar_usuarios(usuarios_df)
            st.sidebar.success("Usuario eliminado")

    elif action == "Cambiar rol":
        cambiar_user = st.sidebar.selectbox("Usuario", usuarios_df["usuario"].tolist())
        nuevo_rol = st.sidebar.selectbox("Nuevo rol", ["usuario","maestro"])
        if st.sidebar.button("Actualizar rol"):
            usuarios_df.loc[usuarios_df["usuario"]==cambiar_user,"rol"] = nuevo_rol
            guardar_usuarios(usuarios_df)
            st.sidebar.success("Rol actualizado")

    elif action == "Cambiar contraseña":
        cambiar_user = st.sidebar.selectbox("Usuario", usuarios_df["usuario"].tolist())
        nueva_pass = st.sidebar.text_input("Nueva contraseña", type="password")
        if st.sidebar.button("Actualizar contraseña"):
            usuarios_df.loc[usuarios_df["usuario"]==cambiar_user,"password"] = hash_password(nueva_pass)
            guardar_usuarios(usuarios_df)
            st.sidebar.success("Contraseña actualizada")

# -------------------------
# Lista de hojas y columnas
# -------------------------
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
        index = index * 26 + (ord(char)-ord('A')+1)
    return index-1

@st.cache_data(show_spinner="Descargando y procesando Excel...")
def cargar_datos_drive(file_id, hojas):
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    resp = requests.get(url)
    if resp.status_code != 200 or not resp.content[:2] == b'PK':
        st.error("Error al descargar Excel")
        return {}
    xls = pd.ExcelFile(BytesIO(resp.content), engine="openpyxl")
    data = {}
    for hoja in hojas:
        if hoja in xls.sheet_names:
            data[hoja] = pd.read_excel(xls, sheet_name=hoja, engine="openpyxl")
    return data

def buscar_coincidencias(data, valores_buscar):
    resultados = {}
    for j, hoja in enumerate(hojas_destino):
        if hoja not in data: continue
        df = data[hoja]
        if df.empty: continue
        filtro = pd.Series([True]*len(df))
        for i, valor in enumerate(valores_buscar):
            if valor:
                cols_str = columnas_condicionantes[i][j]
                if not cols_str: filtro &= False; continue
                cols = [excel_col_to_index(c.strip()) for c in cols_str.split(",")]
                cond = pd.Series([False]*len(df))
                for col_idx in cols:
                    if col_idx < len(df.columns):
                        cond |= df.iloc[:,col_idx].astype(str).str.upper().str.contains(valor.upper(), na=False)
                filtro &= cond
        df_filtrado = df[filtro]
        if not df_filtrado.empty:
            resultados[hoja] = df_filtrado
    return resultados

# -------------------------
# App principal
# -------------------------
st.title("Control de Nómina Eventual - Búsqueda")

# Botón actualizar solo para maestro
file_id = "17O33v9JmMsItavMNm7qw4MX2Zx_K7a2f"
if user_rol == "maestro":
    if st.button("Actualizar datos de base"):
        cargar_datos_drive.clear()
        st.success("Caché limpiada. Próxima búsqueda descargará datos nuevos.")

# Campos de búsqueda
col1, col2 = st.columns(2)
rfc = col1.text_input("RFC")
nombre = col2.text_input("NOMBRE")
col3, col4 = st.columns(2)
oficio_solicitud = col3.text_input("OFICIO DE SOLICITUD")
adscripcion = col4.text_input("ADSCRIPCION")
col5, col6 = st.columns(2)
cuenta = col5.text_input("CUENTA")
oficio_elaborado = col6.text_input("OFICIO ELABORADO")

if st.button("Buscar"):
    data = cargar_datos_drive(file_id, hojas_destino)
    valores = [rfc.strip(), nombre.strip(), oficio_solicitud.strip(), adscripcion.strip(), cuenta.strip(), oficio_elaborado.strip()]
    resultados = buscar_coincidencias(data, valores)
    registrar_consulta(st.session_state["usuario"], "|".join([str(v) for v in valores]))
    if not resultados:
        st.info("No se encontraron coincidencias.")
    else:
        for hoja, df_res in resultados.items():
            st.subheader(f"Resultados en hoja: {hoja}")
            st.dataframe(df_res, width=1500, height=180)

# Botón limpiar
if st.button("Limpiar"):
    st.experimental_rerun()

# -------------------------
# Pie de página
# -------------------------
st.markdown("""
<hr>
<div style='text-align: center; font-size: 12px; color: gray;'>
© Derechos Reservados. LACB  =)
</div>
""", unsafe_allow_html=True)
