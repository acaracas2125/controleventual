import pandas as pd
import streamlit as st
import requests
from io import BytesIO
import hashlib
import os

# -------------------------------
# Configuración inicial
# -------------------------------
USUARIOS_FILE = "usuarios.csv"
CONSULTAS_FILE = "consultas.csv"
FILE_ID = "17O33v9JmMsItavMNm7qw4MX2Zx_K7a2f"

hojas_destino = [
    "NUEVO COSTEO", "COSTEO O.C.", "CORRES 2025", "BASE FEDERAL 2025", "BASE", "VALIDACION IMPROS", "REGISTRO REVERSOS",
    "CAMBIO DE ADSCRIPCION", "STATUS DE COMISION", "COMISIONES", "OFICIOS 2025-ENERO", "OFICIOS 2025-FEBRERO",
    "OFICIOS 2025-MARZO", "OFICIO 2025-JUNIO", "LIC. MARCELA.", "CONTRATOS", "MEMOS", "MTRA. NOELIA",
    "STATUS DE OFI. DEPÁCHADOS OLI", "COMISIONES (2)", "Hoja1 (5)", "NOMINA ACTUAL",
    "DIVERSOS", "FORMATOS DE DESC. DIV", "CHEQUES-REVERSOS", "PENSIONES Y FORMATOS"
]

columnas_condicionantes = [
    ["C", "C", "", "D", "", "E", "E"] + [""] * 14 + ["C"] + ["B", "B", "B", "B"],  # RFC
    ["E", "D", "J", "E", "", "F", "F", "D", "C", "D", "C", "C", "C", "C", "E", "E", "E", "E", "E", "E", "D", "D"] + ["C", "C", "C", "C"],  # NOMBRE
    ["AC", "I", "D", "J", "", "", "", "B", "", "B", "", "", "", "A", "", "", "", "", "", "", "", ""] + ["", "", "", ""],  # OFICIO SOLICITUD
    ["P", "V", "D,I", "W", "", "L", "L", "", "D", "", "", "", "", "", "", "", "", "", "", "", "", "G"] + ["", "", "", ""],  # ADSCRIPCION
    ["AE", "X", "", "Y", "", "M", "M"] + [""] * 14 + ["O"] + ["", "", "", ""],  # CUENTA
    [""] * 7 + ["G", "A", "G", "A", "A", "A", "F", "C", "C", "C", "C", "C", "C", "B"] + [""] + ["", "", "", ""]  # OFICIO ELABORADO
]

# -------------------------------
# Funciones auxiliares
# -------------------------------

def excel_col_to_index(col):
    col = col.upper()
    index = 0
    for char in col:
        index = index * 26 + (ord(char) - ord('A') + 1)
    return index - 1

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
        filtro = pd.Series([True]*len(df))
        for i, valor in enumerate(valores_buscar):
            if valor:
                cols_str = columnas_condicionantes[i][j]
                if not cols_str:
                    filtro &= False
                    continue
                cols = [excel_col_to_index(c.strip()) for c in cols_str.split(",")]
                cond = pd.Series([False]*len(df))
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
    if not os.path.exists(USUARIOS_FILE):
        # Crear maestro por defecto si no existe archivo
        df = pd.DataFrame([{
            "usuario": "acaracas",
            "contraseña": hash_password("prueba1234"),
            "nombre_completo": "Angel Caracas",
            "mensaje_bienvenida": "Bienvenido",
            "es_maestro": True
        }])
        df.to_csv(USUARIOS_FILE, index=False)
    else:
        df = pd.read_csv(USUARIOS_FILE)
    return df

def guardar_usuarios(df):
    df.to_csv(USUARIOS_FILE, index=False)

def verificar_usuario(usuario, password):
    df = cargar_usuarios()
    df["contraseña"] = df["contraseña"].astype(str)
    fila = df[df["usuario"]==usuario]
    if fila.empty:
        return None
    hash_pass = hash_password(password)
    if fila.iloc[0]["contraseña"] == hash_pass:
        return fila.iloc[0].to_dict()
    return None

def registrar_consulta(usuario, criterio):
    if os.path.exists(CONSULTAS_FILE):
        df = pd.read_csv(CONSULTAS_FILE)
    else:
        df = pd.DataFrame(columns=["usuario","criterio"])
    df = pd.concat([df, pd.DataFrame([{"usuario": usuario, "criterio": criterio}])], ignore_index=True)
    df.to_csv(CONSULTAS_FILE, index=False)

# -------------------------------
# Inicio de sesión
# -------------------------------
st.title("Control de Nómina Eventual - Inicio de sesión")

usuario_input = st.text_input("Usuario")
password_input = st.text_input("Contraseña", type="password")
login_btn = st.button("Iniciar sesión")

if login_btn:
    usuario_info = verificar_usuario(usuario_input, password_input)
    if usuario_info:
        st.session_state["usuario_info"] = usuario_info
        st.success(f"{usuario_info['mensaje_bienvenida']}")
    else:
        st.error("Usuario o contraseña incorrectos.")

if "usuario_info" in st.session_state:
    usuario_info = st.session_state["usuario_info"]

    # -------------------------------
    # Menú maestro
    # -------------------------------
    if usuario_info["es_maestro"]:
        st.sidebar.subheader("Menú Maestro")
        menu = st.sidebar.selectbox("Opciones", ["Consulta", "Administrar Usuarios", "Descargar Consultas"])

        if menu == "Administrar Usuarios":
            st.subheader("Administración de Usuarios")
            usuarios_df = cargar_usuarios()
            
            with st.form("form_nuevo_usuario"):
                st.write("Agregar o modificar usuario")
                usuario_n = st.text_input("Usuario")
                contraseña_n = st.text_input("Contraseña", type="password")
                nombre_n = st.text_input("Nombre completo")
                mensaje_n = st.text_input("Mensaje de bienvenida")
                maestro_n = st.checkbox("Es maestro")
                submit_n = st.form_submit_button("Guardar usuario")
                if submit_n:
                    hash_pass = hash_password(contraseña_n)
                    if usuario_n in usuarios_df["usuario"].values:
                        usuarios_df.loc[usuarios_df["usuario"]==usuario_n, ["contraseña","nombre_completo","mensaje_bienvenida","es_maestro"]] = [hash_pass, nombre_n, mensaje_n, maestro_n]
                        st.success("Usuario modificado correctamente")
                    else:
                        usuarios_df = pd.concat([usuarios_df, pd.DataFrame([{
                            "usuario": usuario_n,
                            "contraseña": hash_pass,
                            "nombre_completo": nombre_n,
                            "mensaje_bienvenida": mensaje_n,
                            "es_maestro": maestro_n
                        }])], ignore_index=True)
                        st.success("Usuario agregado correctamente")
                    guardar_usuarios(usuarios_df)

            st.subheader("Usuarios existentes")
            st.dataframe(usuarios_df)

        elif menu == "Descargar Consultas":
            if os.path.exists(CONSULTAS_FILE):
                df_cons = pd.read_csv(CONSULTAS_FILE)
                st.download_button("Descargar archivo de consultas", df_cons.to_csv(index=False), "consultas.csv", "text/csv")
            else:
                st.info("Aún no se han registrado consultas.")

        elif menu == "Consulta":
            st.subheader("Consulta de Nómina")

    else:
        st.subheader("Consulta de Nómina")
    
    # -------------------------------
    # Campos de búsqueda y resultados
    # -------------------------------
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
        valores = [rfc.strip(), nombre.strip(), oficio_solicitud.strip(), adscripcion.strip(), cuenta.strip(), oficio_elaborado.strip()]
        resultados = buscar_coincidencias(data, valores)
        registrar_consulta(usuario_info["usuario"], f"RFC:{rfc}, NOMBRE:{nombre}, OFICIO:{oficio_solicitud}, ADS:{adscripcion}, CUENTA:{cuenta}, ELAB:{oficio_elaborado}")

        if not resultados:
            st.info("No se encontraron coincidencias.")
        else:
            for hoja, df_res in resultados.items():
                st.subheader(f"Resultados de '{hoja}'")
                st.dataframe(df_res, width=1500, height=180)

    if usuario_info["es_maestro"]:
        if st.button("Actualizar datos de base"):
            cargar_datos_drive.clear()
            st.success("Caché limpiada. Se descargará el archivo actualizado en la próxima búsqueda.")

    st.markdown(
        """
        <hr>
        <div style='text-align: center; font-size: 12px; color: gray;'>
            © Derechos Reservados. LACB  =)
        </div>
        """,
        unsafe_allow_html=True
    )
