import pandas as pd
import streamlit as st
import requests
from io import BytesIO
import hashlib
import os
from datetime import datetime

# =========================
# CONFIGURACIÓN
# =========================
ARCHIVO_USUARIOS = "usuarios.csv"
ARCHIVO_CONSULTAS = "consultas.csv"
FILE_ID_EXCEL = "17O33v9JmMsItavMNm7qw4MX2Zx_K7a2f"

# Lista de hojas destino
hojas_destino = [
    "NUEVO COSTEO", "COSTEO O.C.", "CORRES 2025", "BASE FEDERAL 2025", "BASE", "VALIDACION IMPROS", "REGISTRO REVERSOS",
    "CAMBIO DE ADSCRIPCION", "STATUS DE COMISION", "COMISIONES", "OFICIOS 2025-ENERO", "OFICIOS 2025-FEBRERO",
    "OFICIOS 2025-MARZO", "OFICIO 2025-JUNIO", "LIC. MARCELA.", "CONTRATOS", "MEMOS", "MTRA. NOELIA",
    "STATUS DE OFI. DEPÁCHADOS OLI", "COMISIONES (2)", "Hoja1 (5)", "NOMINA ACTUAL",
    "DIVERSOS", "FORMATOS DE DESC. DIV", "CHEQUES-REVERSOS", "PENSIONES Y FORMATOS"
]

# Matriz de columnas condicionantes (RFC y Nombre)
columnas_condicionantes = [
    ["C", "C", "", "D", "", "E", "E"] + [""] * 14 + ["C"] + ["B", "B", "B", "B"],
    ["E", "D", "J", "E", "", "F", "F", "D", "C", "D", "C", "C", "C", "C", "E", "E", "E", "E", "E", "E", "D", "D"] + ["C", "C", "C", "C"],
    ["AC", "I", "D", "J", "", "", "", "B", "", "B", "", "", "", "A", "", "", "", "", "", "", "", ""] + ["", "", "", ""],
    ["P", "V", "D,I", "W", "", "L", "L", "", "D", "", "", "", "", "", "", "", "", "", "", "", "", "G"] + ["", "", "", ""],
    ["AE", "X", "", "Y", "", "M", "M"] + [""] * 14 + ["O"] + ["", "", "", ""],
    [""] * 7 + ["G", "A", "G", "A", "A", "A", "F", "C", "C", "C", "C", "C", "C", "B"] + [""] + ["", "", "", ""]
]

# =========================
# FUNCIONES
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
    if resp.status_code != 200 or not resp.content[:2] == b'PK':
        st.error("No se pudo descargar el archivo desde Google Drive.")
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

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def cargar_usuarios():
    if not os.path.exists(ARCHIVO_USUARIOS):
        # Crear CSV con usuario maestro si no existe
        df = pd.DataFrame([{
            "usuario": "acaracas",
            "contraseña": hash_password("prueba1234"),
            "nombre_completo": "Administrador Maestro",
            "maestro": True,
            "mensaje_bienvenida": "Bienvenido"
        }])
        df.to_csv(ARCHIVO_USUARIOS, index=False)
    df = pd.read_csv(ARCHIVO_USUARIOS)
    df.columns = df.columns.str.strip()
    df["maestro"] = df["maestro"].astype(bool)
    return df

def guardar_usuarios(df):
    df.to_csv(ARCHIVO_USUARIOS, index=False)

def verificar_usuario(usuario, password):
    df = cargar_usuarios()
    hash_pass = hash_password(password)
    fila = df[df["usuario"] == usuario]
    if not fila.empty and fila.iloc[0]["contraseña"] == hash_pass:
        return fila.iloc[0]
    return None

def registrar_consulta(usuario, criterios):
    fila = {
        "usuario": usuario,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "criterios": "; ".join(criterios)
    }
    if os.path.exists(ARCHIVO_CONSULTAS):
        df = pd.read_csv(ARCHIVO_CONSULTAS)
        df = pd.concat([df, pd.DataFrame([fila])], ignore_index=True)
    else:
        df = pd.DataFrame([fila])
    df.to_csv(ARCHIVO_CONSULTAS, index=False)

# =========================
# INTERFAZ
# =========================
st.title("Control de Nómina Eventual - Login")

# --- LOGIN ---
usuario_input = st.text_input("Usuario")
password_input = st.text_input("Contraseña", type="password")
if st.button("Iniciar sesión"):
    usuario_info = verificar_usuario(usuario_input.strip(), password_input.strip())
    if usuario_info is None:
        st.error("Usuario o contraseña incorrectos.")
        st.stop()
    else:
        st.success(f"{usuario_info['mensaje_bienvenida']}, {usuario_info['nombre_completo']}!")

        # --- MENÚ ---
        menu = ["Buscar nómina"]
        if usuario_info["maestro"]:
            menu.append("Administrar usuarios")
            menu.append("Actualizar datos de base")
        opcion = st.selectbox("Menú", menu)

        # --- ACTUALIZAR DATOS BASE ---
        if opcion == "Actualizar datos de base" and usuario_info["maestro"]:
            cargar_datos_drive.clear()
            st.success("La caché se ha limpiado. La próxima búsqueda descargará el archivo actualizado.")

        # --- ADMINISTRAR USUARIOS ---
        if opcion == "Administrar usuarios" and usuario_info["maestro"]:
            st.subheader("Administración de usuarios")
            df_usuarios = cargar_usuarios()
            st.dataframe(df_usuarios)
            # Agregar nuevo usuario
            st.markdown("### Agregar nuevo usuario")
            nuevo_usuario = st.text_input("Usuario")
            nueva_contraseña = st.text_input("Contraseña", type="password")
            nombre_completo = st.text_input("Nombre completo")
            mensaje_bienvenida = st.text_input("Mensaje de bienvenida", value="Bienvenido")
            maestro = st.checkbox("Maestro")
            if st.button("Agregar usuario"):
                if nuevo_usuario and nueva_contraseña:
                    df_usuarios = pd.concat([df_usuarios, pd.DataFrame([{
                        "usuario": nuevo_usuario,
                        "contraseña": hash_password(nueva_contraseña),
                        "nombre_completo": nombre_completo,
                        "maestro": maestro,
                        "mensaje_bienvenida": mensaje_bienvenida
                    }])], ignore_index=True)
                    guardar_usuarios(df_usuarios)
                    st.success("Usuario agregado.")
            # Eliminar usuario
            st.markdown("### Eliminar usuario")
            usuario_eliminar = st.selectbox("Selecciona usuario", df_usuarios["usuario"])
            if st.button("Eliminar usuario"):
                df_usuarios = df_usuarios[df_usuarios["usuario"] != usuario_eliminar]
                guardar_usuarios(df_usuarios)
                st.success("Usuario eliminado.")

        # --- BUSQUEDA NÓMINA ---
        if opcion == "Buscar nómina":
            st.subheader("Buscar en las hojas de nómina")
            rfc = st.text_input("RFC")
            nombre = st.text_input("NOMBRE")
            oficio_solicitud = st.text_input("OFICIO DE SOLICITUD")
            adscripcion = st.text_input("ADSCRIPCION")
            cuenta = st.text_input("CUENTA")
            oficio_elaborado = st.text_input("OFICIO ELABORADO")
            criterios = [rfc, nombre, oficio_solicitud, adscripcion, cuenta, oficio_elaborado]
            if st.button("Buscar"):
                data = cargar_datos_drive(FILE_ID_EXCEL, hojas_destino)
                resultados = buscar_coincidencias(data, criterios)
                registrar_consulta(usuario_info["usuario"], criterios)
                if not resultados:
                    st.info("No se encontraron coincidencias.")
                else:
                    for hoja, df_res in resultados.items():
                        st.subheader(f"Resultados de '{hoja}'")
                        st.dataframe(df_res, width=1500, height=180)

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
