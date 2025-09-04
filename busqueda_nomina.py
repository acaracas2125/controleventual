import pandas as pd
import streamlit as st
import requests
from io import BytesIO
import os
import hashlib
from datetime import datetime

# =========================
# Configuración inicial
# =========================
USUARIOS_FILE = "usuarios.csv"
CONSULTAS_FILE = "consultas.csv"

# Si el archivo de usuarios no existe, lo crea con el usuario maestro
if not os.path.exists(USUARIOS_FILE):
    df = pd.DataFrame([{
        "usuario": "acaracas",
        "contraseña": hashlib.sha256("prueba1234".encode()).hexdigest(),
        "nombre_completo": "Usuario Maestro",
        "mensaje_bienvenida": "Bienvenido",
        "es_maestro": True
    }])
    df.to_csv(USUARIOS_FILE, index=False)

# =========================
# Funciones de usuario
# =========================
def cargar_usuarios():
    if not os.path.exists(USUARIOS_FILE):
        # Crear el archivo con usuario maestro si no existe
        df = pd.DataFrame([{
            "usuario": "acaracas",
            "contraseña": hashlib.sha256("prueba1234".encode()).hexdigest(),
            "nombre_completo": "Usuario Maestro",
            "mensaje_bienvenida": "Bienvenido",
            "es_maestro": True
        }])
        df.to_csv(USUARIOS_FILE, index=False)
    # Forzar tipos y nombres de columnas correctos al leer
    df = pd.read_csv(USUARIOS_FILE, dtype={
        "usuario": str,
        "contraseña": str,
        "nombre_completo": str,
        "mensaje_bienvenida": str,
        "es_maestro": bool
    })
    # Asegurar que todas las columnas existan
    for col in ["usuario", "contraseña", "nombre_completo", "mensaje_bienvenida", "es_maestro"]:
        if col not in df.columns:
            if col == "es_maestro":
                df[col] = False
            else:
                df[col] = ""
    return df

def verificar_usuario(usuario, contraseña):
    df = cargar_usuarios()
    df["contraseña"] = df["contraseña"].astype(str)
    df["usuario"] = df["usuario"].astype(str)
    if usuario in df["usuario"].values:
        hash_pass = hashlib.sha256(contraseña.encode()).hexdigest()
        fila = df[df["usuario"] == usuario].iloc[0]
        if "contraseña" in fila and fila["contraseña"] == hash_pass:
            return fila.to_dict()
    return None
# =========================
# Funciones de base de datos
# =========================
hojas_destino = [
    "NUEVO COSTEO", "COSTEO O.C.", "CORRES 2025", "BASE FEDERAL 2025", "BASE",
    "VALIDACION IMPROS", "REGISTRO REVERSOS", "CAMBIO DE ADSCRIPCION", "STATUS DE COMISION",
    "COMISIONES", "OFICIOS 2025-ENERO", "OFICIOS 2025-FEBRERO", "OFICIOS 2025-MARZO",
    "OFICIO 2025-JUNIO", "LIC. MARCELA.", "CONTRATOS", "MEMOS", "MTRA. NOELIA",
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
# Interfaz de login
# =========================
st.title("Control de Nómina Eventual - Login")
usuario_input = st.text_input("Usuario")
password_input = st.text_input("Contraseña", type="password")
login_btn = st.button("Iniciar sesión")

usuario_info = None
if login_btn:
    usuario_info = verificar_usuario(usuario_input, password_input)
    if usuario_info:
        st.success(f"{usuario_info['mensaje_bienvenida']}, {usuario_info['nombre_completo']}!")
    else:
        st.error("Usuario o contraseña incorrectos")

if usuario_info:
    # =========================
    # Menú principal
    # =========================
    opciones = ["Búsqueda"]
    if usuario_info["es_maestro"]:
        opciones.append("Administrar Usuarios")
        opciones.append("Ver consultas")
    seleccion = st.sidebar.selectbox("Menú", opciones)

    # =========================
    # ID fijo del archivo
    # =========================
    file_id = "17O33v9JmMsItavMNm7qw4MX2Zx_K7a2f"

    # =========================
    # Actualizar base
    # =========================
    if seleccion == "Búsqueda":
        if usuario_info["es_maestro"]:
            if st.button("Actualizar datos de base"):
                cargar_datos_drive.clear()
                st.success("La caché se ha limpiado. La próxima búsqueda descargará el archivo actualizado.")

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
            valores = [rfc.strip(), nombre.strip(), oficio_solicitud.strip(),
                       adscripcion.strip(), cuenta.strip(), oficio_elaborado.strip()]
            resultados = buscar_coincidencias(data, valores)
            if resultados:
                for hoja, df_res in resultados.items():
                    st.subheader(f"Resultados de '{hoja}'")
                    st.dataframe(df_res, width=1500, height=180)
            else:
                st.info("No se encontraron coincidencias.")

            # Guardar consultas
            if not os.path.exists(CONSULTAS_FILE):
                pd.DataFrame(columns=["usuario","fecha","criterio"]).to_csv(CONSULTAS_FILE, index=False)
            df_cons = pd.read_csv(CONSULTAS_FILE)
            df_cons = df_cons.append({"usuario": usuario_input, "fecha": datetime.now(), "criterio": f"{rfc},{nombre},{oficio_solicitud},{adscripcion},{cuenta},{oficio_elaborado}"}, ignore_index=True)
            df_cons.to_csv(CONSULTAS_FILE, index=False)

    # =========================
    # Administrar usuarios
    # =========================
    elif seleccion == "Administrar Usuarios":
        st.subheader("Usuarios actuales")
        usuarios_df = cargar_usuarios()
        st.dataframe(usuarios_df)

        st.subheader("Agregar nuevo usuario")
        nuevo_usuario = st.text_input("Usuario")
        nueva_contraseña = st.text_input("Contraseña", type="password")
        nombre_completo = st.text_input("Nombre completo")
        mensaje_bienvenida = st.text_input("Mensaje de bienvenida")
        es_maestro = st.checkbox("Es maestro")
        if st.button("Agregar usuario"):
            if nuevo_usuario and nueva_contraseña:
                usuarios_df = usuarios_df.append({
                    "usuario": nuevo_usuario,
                    "contraseña": hashlib.sha256(nueva_contraseña.encode()).hexdigest(),
                    "nombre_completo": nombre_completo,
                    "mensaje_bienvenida": mensaje_bienvenida if mensaje_bienvenida else "Bienvenido",
                    "es_maestro": es_maestro
                }, ignore_index=True)
                guardar_usuarios(usuarios_df)
                st.success("Usuario agregado correctamente")

        st.subheader("Eliminar usuario")
        eliminar_usuario = st.selectbox("Selecciona usuario a eliminar", usuarios_df["usuario"].tolist())
        if st.button("Eliminar usuario"):
            if eliminar_usuario != "acaracas":
                usuarios_df = usuarios_df[usuarios_df["usuario"] != eliminar_usuario]
                guardar_usuarios(usuarios_df)
                st.success("Usuario eliminado")
            else:
                st.error("No se puede eliminar el usuario maestro")

    # =========================
    # Ver consultas
    # =========================
    elif seleccion == "Ver consultas":
        if os.path.exists(CONSULTAS_FILE):
            df_cons = pd.read_csv(CONSULTAS_FILE)
            st.dataframe(df_cons)
            st.download_button("Descargar CSV de consultas", CONSULTAS_FILE)
        else:
            st.info("No hay consultas registradas")

