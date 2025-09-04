import pandas as pd
import streamlit as st
import requests
from io import BytesIO
import os
import hashlib
from datetime import datetime

# =========================
# Configuración de archivos
# =========================
USUARIOS_FILE = "usuarios.csv"
CONSULTAS_FILE = "consultas.csv"
FILE_ID = "17O33v9JmMsItavMNm7qw4MX2Zx_K7a2f"  # ID fijo de Google Drive
hojas_destino = [
    "NUEVO COSTEO", "COSTEO O.C.", "CORRES 2025", "BASE FEDERAL 2025", "BASE",
    "VALIDACION IMPROS", "REGISTRO REVERSOS", "CAMBIO DE ADSCRIPCION",
    "STATUS DE COMISION", "COMISIONES", "OFICIOS 2025-ENERO", "OFICIOS 2025-FEBRERO",
    "OFICIOS 2025-MARZO", "OFICIO 2025-JUNIO", "LIC. MARCELA.", "CONTRATOS", "MEMOS",
    "MTRA. NOELIA", "STATUS DE OFI. DEPÁCHADOS OLI", "COMISIONES (2)", "Hoja1 (5)",
    "NOMINA ACTUAL", "DIVERSOS", "FORMATOS DE DESC. DIV", "CHEQUES-REVERSOS", "PENSIONES Y FORMATOS"
]

# Matriz de columnas condicionantes (RFC, Nombre, etc.) - tu original
columnas_condicionantes = [
    ["C", "C", "", "D", "", "E", "E"] + [""] * 14 + ["C"] + ["B", "B", "B", "B"],
    ["E", "D", "J", "E", "", "F", "F", "D", "C", "D", "C", "C", "C", "C", "E", "E", "E", "E", "E", "E", "D", "D"] + ["C", "C", "C", "C"],
    ["AC", "I", "D", "J", "", "", "", "B", "", "B", "", "", "", "A", "", "", "", "", "", "", "", ""] + ["", "", "", ""],
    ["P", "V", "D,I", "W", "", "L", "L", "", "D", "", "", "", "", "", "", "", "", "", "", "", "", "G"] + ["", "", "", ""],
    ["AE", "X", "", "Y", "", "M", "M"] + [""] * 14 + ["O"] + ["", "", "", ""],
    [""] * 7 + ["G", "A", "G", "A", "A", "A", "F", "C", "C", "C", "C", "C", "C", "B"] + [""] + ["", "", "", ""]
]

# =========================
# Funciones de utilidad
# =========================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

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
    if resp.status_code != 200 or not resp.content[:2] == b'PK':
        st.error("No se pudo descargar el archivo de Google Drive o no es un Excel válido.")
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
# Login y sesión
# =========================
if "logeado" not in st.session_state:
    st.session_state["logeado"] = False
if "usuario" not in st.session_state:
    st.session_state["usuario"] = ""
if "rol" not in st.session_state:
    st.session_state["rol"] = ""

# Crear usuario maestro si no existe
if not os.path.exists(USUARIOS_FILE):
    df = pd.DataFrame([["acaracas", hash_password("prueba1234"), "maestro"]], 
                      columns=["usuario", "password", "rol"])
    df.to_csv(USUARIOS_FILE, index=False)
else:
    usuarios_df = pd.read_csv(USUARIOS_FILE)
    if "acaracas" not in usuarios_df["usuario"].values:
        usuarios_df = usuarios_df.append({
            "usuario": "acaracas",
            "password": hash_password("prueba1234"),
            "rol": "maestro"
        }, ignore_index=True)
        usuarios_df.to_csv(USUARIOS_FILE, index=False)

usuarios_df = pd.read_csv(USUARIOS_FILE)

if not st.session_state["logeado"]:
    st.title("🔒 Control de Nómina Eventual - Login")
    usuario_input = st.text_input("Usuario")
    password_input = st.text_input("Contraseña", type="password")
    login = st.button("Iniciar sesión")
    
    if login:
        user_row = usuarios_df[usuarios_df["usuario"] == usuario_input]
        if not user_row.empty and hash_password(password_input) == user_row.iloc[0]["password"]:
            st.session_state["usuario"] = usuario_input
            st.session_state["rol"] = user_row.iloc[0]["rol"]
            st.session_state["logeado"] = True
            st.success(f"Bienvenido {usuario_input}!")
        else:
            st.error("Usuario o contraseña incorrectos.")
    st.stop()

# =========================
# Menú para usuarios maestros
# =========================
if st.session_state["rol"] == "maestro":
    st.sidebar.title("👑 Panel Maestro")
    menu = st.sidebar.selectbox("Opciones", ["Búsqueda", "Gestionar Usuarios", "Descargar Registro"])
    
    if menu == "Gestionar Usuarios":
        st.header("Administrar Usuarios")
        nuevo_usuario = st.text_input("Nuevo usuario")
        nueva_clave = st.text_input("Contraseña", type="password")
        rol_usuario = st.selectbox("Rol", ["consulta", "maestro"])
        if st.button("Agregar Usuario"):
            if nuevo_usuario and nueva_clave:
                if nuevo_usuario in usuarios_df["usuario"].values:
                    st.warning("El usuario ya existe.")
                else:
                    usuarios_df = usuarios_df.append({
                        "usuario": nuevo_usuario,
                        "password": hash_password(nueva_clave),
                        "rol": rol_usuario
                    }, ignore_index=True)
                    usuarios_df.to_csv(USUARIOS_FILE, index=False)
                    st.success("Usuario agregado correctamente.")
        eliminar_usuario = st.text_input("Eliminar usuario")
        if st.button("Eliminar Usuario"):
            if eliminar_usuario in usuarios_df["usuario"].values and eliminar_usuario != "acaracas":
                usuarios_df = usuarios_df[usuarios_df["usuario"] != eliminar_usuario]
                usuarios_df.to_csv(USUARIOS_FILE, index=False)
                st.success("Usuario eliminado.")
            else:
                st.warning("No se puede eliminar este usuario o no existe.")
        if st.button("Actualizar datos de base"):
            cargar_datos_drive.clear()
            st.success("La caché se ha limpiado. La próxima búsqueda descargará el archivo actualizado.")

    elif menu == "Descargar Registro":
        if os.path.exists(CONSULTAS_FILE):
            st.download_button("Descargar consultas", CONSULTAS_FILE)
        else:
            st.info("Aún no hay registros de consultas.")

else:
    menu = "Búsqueda"

# =========================
# App principal de búsqueda
# =========================
if menu == "Búsqueda":
    st.title("Control de Nómina Eventual - Búsqueda")
    
    # Campos de búsqueda
    col1, col2 = st.columns(2)
    rfc = col1.text_input("RFC", key="rfc")
    nombre = col2.text_input("NOMBRE", key="nombre")
    col3, col4 = st.columns(2)
    oficio_solicitud = col3.text_input("OFICIO DE SOLICITUD", key="oficio_solicitud")
    adscripcion = col4.text_input("ADSCRIPCION", key="adscripcion")
    col5, col6 = st.columns(2)
    cuenta = col5.text_input("CUENTA", key="cuenta")
    oficio_elaborado = col6.text_input("OFICIO ELABORADO", key="oficio_elaborado")

    if st.button("Buscar"):
        data = cargar_datos_drive(FILE_ID, hojas_destino)
        valores = [rfc.strip(), nombre.strip(), oficio_solicitud.strip(),
                   adscripcion.strip(), cuenta.strip(), oficio_elaborado.strip()]
        resultados = buscar_coincidencias(data, valores)
        
        if not resultados:
            st.info("No se encontraron coincidencias.")
        else:
            for hoja, df_res in resultados.items():
                st.subheader(f"Resultados de '{hoja}'")
                st.dataframe(df_res, width=1500, height=180)
        
        # Guardar registro de consulta
        registro = pd.DataFrame([{
            "usuario": st.session_state["usuario"],
            "fecha": datetime.now(),
            "rfc": rfc,
            "nombre": nombre,
            "oficio_solicitud": oficio_solicitud,
            "adscripcion": adscripcion,
            "cuenta": cuenta,
            "oficio_elaborado": oficio_elaborado
        }])
        if os.path.exists(CONSULTAS_FILE):
            registro.to_csv(CONSULTAS_FILE, mode="a", header=False, index=False)
        else:
            registro.to_csv(CONSULTAS_FILE, index=False)

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
