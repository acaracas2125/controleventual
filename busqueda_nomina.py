import pandas as pd
import streamlit as st
import requests
from io import BytesIO
import hashlib
import os

# =========================
# Configuración inicial
# =========================
USUARIOS_FILE = "usuarios.csv"
hojas_destino = [
    "NUEVO COSTEO", "COSTEO O.C.", "CORRES 2025", "BASE FEDERAL 2025", "BASE", "VALIDACION IMPROS", "REGISTRO REVERSOS",
    "CAMBIO DE ADSCRIPCION", "STATUS DE COMISION", "COMISIONES", "OFICIOS 2025-ENERO", "OFICIOS 2025-FEBRERO",
    "OFICIOS 2025-MARZO", "OFICIO 2025-JUNIO", "LIC. MARCELA.", "CONTRATOS", "MEMOS", "MTRA. NOELIA",
    "STATUS DE OFI. DEPÁCHADOS OLI", "COMISIONES (2)", "Hoja1 (5)", "NOMINA ACTUAL",
    "DIVERSOS", "FORMATOS DE DESC. DIV", "CHEQUES-REVERSOS", "PENSIONES Y FORMATOS"
]

# Columnas condicionantes (RFC y Nombre)
columnas_condicionantes = [
    ["C", "C", "", "D", "", "E", "E"] + [""] * 14 + ["C"] + ["B", "B", "B", "B"],  # RFC
    ["E", "D", "J", "E", "", "F", "F", "D", "C", "D", "C", "C", "C", "C", "E", "E", "E", "E", "E", "E", "D", "D"] + ["C", "C", "C", "C"],  # NOMBRE
    ["AC", "I", "D", "J", "", "", "", "B", "", "B", "", "", "", "A", "", "", "", "", "", "", "", ""] + ["", "", "", ""],  # OFICIO SOLICITUD
    ["P", "V", "D,I", "W", "", "L", "L", "", "D", "", "", "", "", "", "", "", "", "", "", "", "", "G"] + ["", "", "", ""],  # ADSCRIPCION
    ["AE", "X", "", "Y", "", "M", "M"] + [""] * 14 + ["O"] + ["", "", "", ""],  # CUENTA
    [""] * 7 + ["G", "A", "G", "A", "A", "A", "F", "C", "C", "C", "C", "C", "C", "B"] + [""] + ["", "", "", ""]  # OFICIO ELABORADO
]

# =========================
# Funciones de usuarios
# =========================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def crear_usuario_maestro():
    if not os.path.exists(USUARIOS_FILE):
        df = pd.DataFrame([{
            "usuario": "acaracas",
            "contraseña": hash_password("prueba1234"),
            "nombre_completo": "Angel Caracas",
            "mensaje_bienvenida": "Bienvenido",
            "es_maestro": True
        }])
        df.to_csv(USUARIOS_FILE, index=False)

def cargar_usuarios():
    crear_usuario_maestro()
    df = pd.read_csv(USUARIOS_FILE)
    # Asegurarse de que es_maestro sea booleano
    if 'es_maestro' in df.columns:
        df['es_maestro'] = df['es_maestro'].astype(bool)
    else:
        # Si no existe, agregar columna
        df['es_maestro'] = False
    return df

def guardar_usuarios(df):
    df.to_csv(USUARIOS_FILE, index=False)

def verificar_usuario(usuario, contraseña):
    df = cargar_usuarios()
    df["contraseña"] = df["contraseña"].astype(str)
    fila = df[df["usuario"] == usuario]
    if fila.empty:
        return None
    hash_pass = hash_password(contraseña)
    if fila.iloc[0]["contraseña"] == hash_pass:
        return fila.iloc[0]
    return None

# =========================
# Funciones para Excel
# =========================
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
        st.error("No se pudo descargar el archivo desde Google Drive.")
        return {}
    if not resp.content[:2] == b'PK':
        st.error("El archivo descargado no es un Excel válido.")
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
# Inicia la app
# =========================
st.title("Control de Nómina Eventual - Búsqueda")

# --- Login ---
st.subheader("Iniciar sesión")
usuario_input = st.text_input("Usuario")
password_input = st.text_input("Contraseña", type="password")
login_btn = st.button("Entrar")

usuario_info = None
if login_btn:
    usuario_info = verificar_usuario(usuario_input.strip(), password_input.strip())
    if usuario_info is None:
        st.error("Usuario o contraseña incorrectos.")
    else:
        st.success(f"Bienvenido {usuario_info['nombre_completo']}! {usuario_info['mensaje_bienvenida']}")

# =========================
# Si inició sesión
# =========================
if usuario_info is not None:

    # --- Menú maestro ---
    if usuario_info["es_maestro"]:
        st.subheader("Menú Maestro")
        menu = st.selectbox("Opciones", ["Búsqueda", "Gestionar Usuarios", "Actualizar base"])
    else:
        menu = st.selectbox("Opciones", ["Búsqueda"])

    # -----------------------
    # Gestión de usuarios
    # -----------------------
    if usuario_info["es_maestro"] and menu == "Gestionar Usuarios":
        st.write("### Administrar usuarios")
        usuarios_df = cargar_usuarios()

        # Agregar usuario
        st.write("#### Agregar usuario")
        new_user = st.text_input("Nombre de usuario")
        new_password = st.text_input("Contraseña", type="password")
        new_name = st.text_input("Nombre completo")
        new_message = st.text_input("Mensaje de bienvenida")
        maestro_check = st.checkbox("Es maestro")
        if st.button("Agregar usuario"):
            if new_user and new_password:
                if new_user in usuarios_df["usuario"].values:
                    st.warning("El usuario ya existe.")
                else:
                    usuarios_df.loc[len(usuarios_df)] = {
                        "usuario": new_user,
                        "contraseña": hash_password(new_password),
                        "nombre_completo": new_name,
                        "mensaje_bienvenida": new_message,
                        "es_maestro": maestro_check
                    }
                    guardar_usuarios(usuarios_df)
                    st.success("Usuario agregado.")

        # Eliminar usuario
        st.write("#### Eliminar usuario")
        del_user = st.selectbox("Selecciona usuario a eliminar", usuarios_df["usuario"])
        if st.button("Eliminar usuario"):
            if del_user == usuario_info["usuario"]:
                st.warning("No puedes eliminar tu propio usuario.")
            else:
                usuarios_df = usuarios_df[usuarios_df["usuario"] != del_user]
                guardar_usuarios(usuarios_df)
                st.success("Usuario eliminado.")

        # Editar mensaje de bienvenida
        st.write("#### Mensaje de bienvenida global")
        msg_global = st.text_area("Mensaje que verán todos los usuarios al iniciar sesión", usuario_info['mensaje_bienvenida'])
        if st.button("Actualizar mensaje global"):
            usuarios_df.loc[usuarios_df['usuario'] == usuario_info['usuario'], 'mensaje_bienvenida'] = msg_global
            guardar_usuarios(usuarios_df)
            st.success("Mensaje actualizado.")

    # -----------------------
    # Actualizar base (solo maestro)
    # -----------------------
    if usuario_info["es_maestro"] and menu == "Actualizar base":
        st.write("Actualizar datos de base")
        if st.button("Actualizar"):
            cargar_datos_drive.clear()
            st.success("Caché limpiada. Próxima búsqueda descargará Excel actualizado.")

    # -----------------------
    # Búsqueda
    # -----------------------
    if menu == "Búsqueda":
        col1, col2 = st.columns(2)
        rfc = col1.text_input("RFC")
        nombre = col2.text_input("NOMBRE")
        col3, col4 = st.columns(2)
        oficio_solicitud = col3.text_input("OFICIO DE SOLICITUD")
        adscripcion = col4.text_input("ADSCRIPCION")
        col5, col6 = st.columns(2)
        cuenta = col5.text_input("CUENTA")
        oficio_elaborado = col6.text_input("OFICIO ELABORADO")

        file_id = "17O33v9JmMsItavMNm7qw4MX2Zx_K7a2f"
        if st.button("Buscar"):
            try:
                data = cargar_datos_drive(file_id, hojas_destino)
                valores = [rfc.strip(), nombre.strip(), oficio_solicitud.strip(), adscripcion.strip(), cuenta.strip(), oficio_elaborado.strip()]
                resultados = buscar_coincidencias(data, valores)
                if not resultados:
                    st.info("No se encontraron coincidencias.")
                else:
                    for hoja, df_res in resultados.items():
                        st.subheader(f"Resultados de '{hoja}'")
                        st.dataframe(df_res, width=1500, height=180)
            except Exception as e:
                st.error(f"Error al procesar: {e}")

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

