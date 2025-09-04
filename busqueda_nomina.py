import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import hashlib
import os
from datetime import datetime

# =========================
# Configuración de archivos
# =========================
USUARIOS_FILE = "usuarios.csv"
CONSULTAS_FILE = "consultas.csv"
FILE_ID = "17O33v9JmMsItavMNm7qw4MX2Zx_K7a2f"  # Excel fijo en Google Drive

# =========================
# Funciones auxiliares
# =========================
def hash_password(password: str) -> str:
    """Genera hash de la contraseña."""
    return hashlib.sha256(password.encode()).hexdigest()

def crear_usuario_maestro():
    """Crea el usuario maestro si no existe."""
    if not os.path.exists(USUARIOS_FILE):
        df = pd.DataFrame([["acaracas", hash_password("prueba1234"), "maestro"]], 
                          columns=["usuario", "password", "rol"])
        df.to_csv(USUARIOS_FILE, index=False)

def cargar_usuarios():
    return pd.read_csv(USUARIOS_FILE)

def guardar_usuarios(df):
    df.to_csv(USUARIOS_FILE, index=False)

def registrar_consulta(usuario, criterio, hoja, filas):
    """Registra la consulta en el archivo CSV de consultas."""
    fila = {
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "usuario": usuario,
        "criterio": criterio,
        "hoja": hoja,
        "filas_resultado": filas
    }
    df = pd.DataFrame([fila])
    if os.path.exists(CONSULTAS_FILE):
        df_ant = pd.read_csv(CONSULTAS_FILE)
        df = pd.concat([df_ant, df], ignore_index=True)
    df.to_csv(CONSULTAS_FILE, index=False)

# =========================
# Inicialización
# =========================
crear_usuario_maestro()
usuarios_df = cargar_usuarios()

# =========================
# Login
# =========================
st.title("🔒 Control de Nómina Eventual - Login")

usuario_input = st.text_input("Usuario")
password_input = st.text_input("Contraseña", type="password")
login = st.button("Iniciar sesión")

if login:
    user_row = usuarios_df[usuarios_df["usuario"] == usuario_input]
    if not user_row.empty and hash_password(password_input) == user_row.iloc[0]["password"]:
        st.success(f"Bienvenido {usuario_input}!")
        rol = user_row.iloc[0]["rol"]
        st.session_state["usuario"] = usuario_input
        st.session_state["rol"] = rol
        st.session_state["logeado"] = True
    else:
        st.error("Usuario o contraseña incorrectos.")

# =========================
# App principal
# =========================
if st.session_state.get("logeado"):

    # --- Menú maestro ---
    if st.session_state["rol"] == "maestro":
        menu = st.selectbox("Menú", ["Búsqueda", "Gestionar Usuarios", "Descargar Consultas"])
    else:
        menu = "Búsqueda"

    # =========================
    # Funciones Excel
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
        if resp.status_code != 200 or not resp.content[:2] == b'PK':
            st.error("No se pudo descargar el archivo Excel de Drive.")
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
    # Menu maestro
    # =========================
    if menu == "Búsqueda":
        st.title("Control de Nómina Eventual - Búsqueda")

        # Solo maestro puede actualizar base
        if st.session_state["rol"] == "maestro":
            if st.button("Actualizar datos de base"):
                cargar_datos_drive.clear()
                st.success("Caché limpiada, próxima búsqueda descargará el archivo actualizado.")

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
            data = cargar_datos_drive(FILE_ID, hojas_destino)
            valores = [rfc.strip(), nombre.strip(), oficio_solicitud.strip(), adscripcion.strip(), cuenta.strip(), oficio_elaborado.strip()]
            resultados = buscar_coincidencias(data, valores)
            if not resultados:
                st.info("No se encontraron coincidencias.")
            else:
                for hoja, df_res in resultados.items():
                    st.subheader(f"Resultados de '{hoja}'")
                    st.dataframe(df_res, width=1500, height=180)
                    # Registrar cada consulta
                    registrar_consulta(st.session_state["usuario"], " | ".join([str(v) for v in valores]), hoja, len(df_res))

        if st.button("Limpiar"):
            st.experimental_rerun()

    elif menu == "Gestionar Usuarios" and st.session_state["rol"] == "maestro":
        st.title("Gestión de Usuarios")
        usuarios_df = cargar_usuarios()
        st.dataframe(usuarios_df)
        st.subheader("Agregar Usuario")
        nuevo_usuario = st.text_input("Usuario nuevo")
        nueva_contraseña = st.text_input("Contraseña", type="password")
        rol_usuario = st.selectbox("Rol", ["consulta", "maestro"])
        if st.button("Agregar Usuario"):
            if nuevo_usuario and nueva_contraseña:
                usuarios_df = usuarios_df.append({
                    "usuario": nuevo_usuario,
                    "password": hash_password(nueva_contraseña),
                    "rol": rol_usuario
                }, ignore_index=True)
                guardar_usuarios(usuarios_df)
                st.success("Usuario agregado correctamente.")
        st.subheader("Eliminar Usuario")
        eliminar_usuario = st.selectbox("Selecciona usuario a eliminar", usuarios_df["usuario"])
        if st.button("Eliminar Usuario"):
            if eliminar_usuario != "acaracas":  # No borrar maestro
                usuarios_df = usuarios_df[usuarios_df["usuario"] != eliminar_usuario]
                guardar_usuarios(usuarios_df)
                st.success("Usuario eliminado correctamente.")

    elif menu == "Descargar Consultas" and st.session_state["rol"] == "maestro":
        st.title("Descargar registro de consultas")
        if os.path.exists(CONSULTAS_FILE):
            st.download_button("Descargar CSV", CONSULTAS_FILE, file_name="consultas.csv")
        else:
            st.info("No hay consultas registradas aún.")

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
