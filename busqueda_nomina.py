import pandas as pd
import streamlit as st
import requests
from io import BytesIO
import hashlib
import os

# =========================
# Configuración de archivos
# =========================
USUARIOS_FILE = "usuarios.csv"
CONSULTAS_FILE = "consultas.csv"
MENSAJE_FILE = "mensaje_bienvenida.txt"

# Si no existen archivos, los creamos
if not os.path.exists(USUARIOS_FILE):
    # Usuario maestro por defecto
    df = pd.DataFrame([{
        "usuario": "acaracas",
        "contraseña": hashlib.sha256("prueba1234".encode()).hexdigest(),
        "nombre_completo": "Ángel Caracas",
        "rol": "maestro"
    }])
    df.to_csv(USUARIOS_FILE, index=False)

if not os.path.exists(CONSULTAS_FILE):
    pd.DataFrame(columns=["usuario","nombre_completo","criterio","hoja","fecha"]).to_csv(CONSULTAS_FILE,index=False)

if not os.path.exists(MENSAJE_FILE):
    with open(MENSAJE_FILE,"w") as f:
        f.write("Bienvenido")  # mensaje inicial

# =========================
# Funciones de seguridad y login
# =========================
def cargar_usuarios():
    return pd.read_csv(USUARIOS_FILE)

def guardar_usuarios(df):
    df.to_csv(USUARIOS_FILE, index=False)

def verificar_usuario(usuario, password):
    df = cargar_usuarios()
    df["contraseña"] = df["contraseña"].astype(str)
    hashed = hashlib.sha256(password.encode()).hexdigest()
    match = df[(df["usuario"]==usuario) & (df["contraseña"]==hashed)]
    if not match.empty:
        return match.iloc[0]  # devuelve fila con info del usuario
    return None

# =========================
# Funciones de Google Drive / Excel
# =========================
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

def excel_col_to_index(col):
    col = col.upper()
    index = 0
    for char in col:
        index = index * 26 + (ord(char) - ord('A') + 1)
    return index - 1  # 0-based

file_id = "17O33v9JmMsItavMNm7qw4MX2Zx_K7a2f"

@st.cache_data(show_spinner="Descargando Excel...")
def cargar_datos_drive(file_id, hojas):
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    resp = requests.get(url)
    if resp.status_code != 200 or not resp.content[:2] == b'PK':
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
        if df.empty: continue
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

# =========================
# Inicio de sesión
# =========================
st.title("🔒 Control de Nómina Eventual - Login")
usuario_input = st.text_input("Usuario")
password_input = st.text_input("Contraseña", type="password")
login_btn = st.button("Iniciar sesión")

if login_btn:
    usuario_info = verificar_usuario(usuario_input, password_input)
    if usuario_info is None:
        st.error("Usuario o contraseña incorrectos.")
        st.stop()
    else:
        st.session_state["usuario"] = usuario_info["usuario"]
        st.session_state["rol"] = usuario_info["rol"]
        st.session_state["nombre_completo"] = usuario_info["nombre_completo"]

# =========================
# Si está logueado
# =========================
if "usuario" in st.session_state:
    # Mensaje de bienvenida editable por maestro
    with open(MENSAJE_FILE,"r") as f:
        mensaje_bienvenida = f.read()
    if st.session_state["rol"] == "maestro":
        st.subheader("Panel Maestro")
        st.text_area("Mensaje de bienvenida para todos los usuarios", value=mensaje_bienvenida, key="mensaje_bienvenida")
        if st.button("Actualizar mensaje de bienvenida"):
            with open(MENSAJE_FILE,"w") as f:
                f.write(st.session_state["mensaje_bienvenida"])
            st.success("Mensaje actualizado.")

        # Gestión de usuarios
        st.markdown("### Gestión de Usuarios")
        usuarios_df = cargar_usuarios()
        st.dataframe(usuarios_df[["usuario","nombre_completo","rol"]])

        # Agregar usuario
        st.markdown("#### Agregar Usuario")
        nuevo_usuario = st.text_input("Usuario")
        nueva_contra = st.text_input("Contraseña", type="password")
        nombre_completo = st.text_input("Nombre completo")
        rol_usuario = st.selectbox("Rol", ["usuario","maestro"])
        if st.button("Agregar usuario"):
            if nuevo_usuario and nueva_contra:
                hashed = hashlib.sha256(nueva_contra.encode()).hexdigest()
                usuarios_df = pd.concat([usuarios_df, pd.DataFrame([{
                    "usuario":nuevo_usuario,
                    "contraseña":hashed,
                    "nombre_completo":nombre_completo,
                    "rol":rol_usuario
                }])], ignore_index=True)
                guardar_usuarios(usuarios_df)
                st.success("Usuario agregado correctamente.")
                st.experimental_rerun()
            else:
                st.error("Debe ingresar usuario y contraseña.")

        # Eliminar usuario
        st.markdown("#### Eliminar Usuario")
        usuario_eliminar = st.selectbox("Seleccionar usuario a eliminar", usuarios_df["usuario"])
        if st.button("Eliminar usuario"):
            if usuario_eliminar != "acaracas":
                usuarios_df = usuarios_df[usuarios_df["usuario"] != usuario_eliminar]
                guardar_usuarios(usuarios_df)
                st.success("Usuario eliminado correctamente.")
                st.experimental_rerun()
            else:
                st.error("No se puede eliminar al usuario maestro.")

        # Botón para actualizar base solo para maestro
        if st.button("Actualizar datos de base"):
            cargar_datos_drive.clear()
            st.success("Caché limpiada, próxima búsqueda descargará archivo actualizado.")

    else:
        st.success(f"{mensaje_bienvenida}, {st.session_state['nombre_completo']}!")

    # =========================
    # Búsqueda de datos
    # =========================
    st.markdown("---")
    st.subheader("Control de Nómina Eventual - Búsqueda")

    col1, col2 = st.columns(2)
    rfc = col1.text_input("RFC", key="rfc")
    nombre = col2.text_input("NOMBRE", key="nombre")
    col3, col4 = st.columns(2)
    oficio_solicitud = col3.text_input("OFICIO DE SOLICITUD", key="oficio_solicitud")
    adscripcion = col4.text_input("ADSCRIPCION", key="adscripcion")
    col5, col6 = st.columns(2)
    cuenta = col5.text_input("CUENTA", key="cuenta")
    oficio_elaborado = col6.text_input("OFICIO ELABORADO", key="oficio_elaborado")

    buscar_btn = st.button("Buscar")
    if buscar_btn:
        try:
            data = cargar_datos_drive(file_id, hojas_destino)
            valores = [rfc.strip(), nombre.strip(), oficio_solicitud.strip(),
                       adscripcion.strip(), cuenta.strip(), oficio_elaborado.strip()]
            resultados = buscar_coincidencias(data, valores)

            # Guardar en consultas.csv
            for hoja, df_res in resultados.items():
                for idx, row in df_res.iterrows():
                    df_cons = pd.read_csv(CONSULTAS_FILE)
                    df_cons = pd.concat([df_cons, pd.DataFrame([{
                        "usuario": st.session_state["usuario"],
                        "nombre_completo": st.session_state["nombre_completo"],
                        "criterio": ", ".join([v for v in valores if v]),
                        "hoja": hoja,
                        "fecha": pd.Timestamp.now()
                    }])], ignore_index=True)
                    df_cons.to_csv(CONSULTAS_FILE,index=False)

            if not resultados:
                st.info("No se encontraron coincidencias.")
            else:
                for hoja, df_res in resultados.items():
                    st.subheader(f"Resultados de '{hoja}'")
                    st.dataframe(df_res, width=1500, height=180)
        except Exception as e:
            st.error(f"Error al procesar: {e}")

    # Maestro puede descargar consultas
    if st.session_state["rol"] == "maestro":
        st.markdown("---")
        st.markdown("### Descarga de consultas")
        st.download_button("Descargar consultas.csv", CONSULTAS_FILE, file_name="consultas.csv")

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
