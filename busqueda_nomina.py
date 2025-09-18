import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import os
import socket

# =========================
# LOGIN DE USUARIOS
# =========================
usuarios_defecto = pd.DataFrame([
    {"usuario":"acaracas","pasword":"cccc","nombre_completo":"Angel Caracas","maestro":True,"mensaje":"Bienvenido master"},
    {"usuario":"lhernandez","pasword":"lau","nombre_completo":"Laura Hernández Rivera","maestro":True,"mensaje":"Bienvenida Lau"},
    {"usuario":"adrian","pasword":"adrian","nombre_completo":"Adrian","maestro":True,"mensaje":"Bienvenido"},	
    {"usuario":"omperez","pasword":"ositis","nombre_completo":"Osiris Monserrat Pérez nieto","maestro":True,"mensaje":"Bienvenida Ositis"},
    {"usuario":"miros","pasword":"tiamo","nombre_completo":"Miroslava Jimenez Candia","maestro":True,"mensaje":"Bienvenida hermosa =)   10!"}
])

ruta_usuarios = r"C:\Users\USER-PC0045\Pictures\PAGINA EVENTUAL\usuarios_app.xlsx"
if os.path.exists(ruta_usuarios):
    try:
        usuarios_excel = pd.read_excel(ruta_usuarios, engine="openpyxl")
        usuarios = pd.concat([usuarios_defecto, usuarios_excel], ignore_index=True)
    except Exception as e:
        st.error(f"No se pudo cargar el archivo de usuarios: {e}")
        usuarios = usuarios_defecto.copy()
else:
    usuarios = usuarios_defecto.copy()

if "usuario_logueado" not in st.session_state:
    st.session_state["usuario_logueado"] = None

if st.session_state["usuario_logueado"] is None:
    st.title("Login de la App")
    usuario_input = st.text_input("Usuario")
    password_input = st.text_input("Contraseña", type="password")
    boton_login = st.button("Entrar")
    if boton_login:
        fila = usuarios[(usuarios["usuario"]==usuario_input) & (usuarios["pasword"]==password_input)]
        if not fila.empty:
            st.session_state["usuario_logueado"] = fila.iloc[0]["usuario"]
            st.session_state["nombre_completo"] = fila.iloc[0]["nombre_completo"]
            st.session_state["maestro"] = fila.iloc[0]["maestro"]
            st.session_state["mensaje_usuario"] = fila.iloc[0]["mensaje"]
            st.success(f"{fila.iloc[0]['mensaje']} {fila.iloc[0]['nombre_completo']}")
        else:
            st.error("Usuario o contraseña incorrectos")
    st.stop()
else:
    if st.session_state["usuario_logueado"]:
        st.sidebar.success(f"Usuario activo: {st.session_state['nombre_completo']}")
        if st.sidebar.button("🔒 Cerrar sesión"):
            for key in ["usuario_logueado", "nombre_completo", "maestro", "mensaje_usuario"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.experimental_rerun()

# =========================
# Configuración de página y estilos
# =========================
st.set_page_config(page_title="Control de Nómina (V 2.1.0)📝", page_icon="💡")
st.markdown("""
<style>
body {background-color: #2F2F2F;}
input, textarea {background-color: white; color: black;}
.resumen-box {background-color:#FFF; border-radius:6px; padding:6px; margin-bottom:6px; font-family:Arial, sans-serif; font-size:12px;}
.resumen-box h3 {text-align:center; margin-bottom:4px; color:#006400; font-size:14px;}
.resumen-grid {display:grid; grid-template-columns:1fr 2fr; row-gap:2px; column-gap:6px;}
.campo {font-weight:bold;color:#000;}
.valor {color:#0D47A1;font-weight:bold;}
</style>
""", unsafe_allow_html=True)

def obtener_ip_local():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip_local = s.getsockname()[0]
        s.close()
        return ip_local
    except:
        return "No disponible"

ip_local = obtener_ip_local()
st.markdown(f"""
<div style='position: fixed; bottom: 10px; right: 10px; 
            background-color: rgba(255,255,255,0.7); 
            padding: 5px 10px; border-radius: 5px; 
            font-size: 12px; color: black; z-index:9999;'>
    Accede desde otro equipo: http://127.0.0.1:8501/
</div>
""", unsafe_allow_html=True)

# =========================
# Variables de sesión
# =========================
for key in ["data_excel","data_historico","data_consolidar","resultados","indice_nomina"]:
    if key not in st.session_state:
        st.session_state[key] = None if key != "indice_nomina" else 0

# =========================
# Rutas y hojas
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
hoja_historico = ["trabajando"]
mapa_historico = {"RFC":"D","NOMBRE":"E","ADSCRIPCION":"V"}

# =========================
# Función para descargar Excel de Drive
# =========================
@st.cache_data(show_spinner="Cargando Excel desde Drive...")
def descargar_excel_drive(file_id, cache_local):
    """
    Descarga un Excel desde Google Drive y lo guarda en cache local
    """
    if os.path.exists(cache_local):
        xls = pd.ExcelFile(cache_local, engine="openpyxl")
    else:
        url = f"https://drive.google.com/uc?export=download&id={file_id}"
        resp = requests.get(url)
        if resp.status_code != 200 or not resp.content[:2] == b'PK':
            st.error("No se pudo descargar el archivo o no es Excel válido.")
            return {}
        with open(cache_local, "wb") as f:
            f.write(resp.content)
        xls = pd.ExcelFile(BytesIO(resp.content), engine="openpyxl")
    return xls

# =========================
# IDs y cache (completa con tus enlaces)
# =========================
EXCEL_CACHE_FILE = r"C:\Users\USER-PC0045\Pictures\PAGINA EVENTUAL\control_nomina_cache.xlsx"
HISTORICO_CACHE_FILE = r"C:\Users\USER-PC0045\Pictures\PAGINA EVENTUAL\historico_cache.xlsx"
CONSOLIDAR_CACHE_FILE = r"C:\Users\USER-PC0045\Pictures\PAGINA EVENTUAL\consolidar_cache.xlsx"

FILE_ID_CONTROL = "TU_FILE_ID_CONTROL"
FILE_ID_HISTORICO = "TU_FILE_ID_HISTORICO"
FILE_ID_CONSOLIDAR = "TU_FILE_ID_CONSOLIDAR"

xls_control = descargar_excel_drive(FILE_ID_CONTROL, EXCEL_CACHE_FILE)
xls_historico = descargar_excel_drive(FILE_ID_HISTORICO, HISTORICO_CACHE_FILE)
xls_consolidar = descargar_excel_drive(FILE_ID_CONSOLIDAR, CONSOLIDAR_CACHE_FILE)

# =========================
# Función para cargar datos de hojas
# =========================
def cargar_hojas(xls, hojas):
    data = {}
    for hoja in hojas:
        if hoja in xls.sheet_names:
            data[hoja] = pd.read_excel(xls, sheet_name=hoja, engine="openpyxl")
    return data

st.session_state["data_excel"] = cargar_hojas(xls_control, hojas_destino)
st.session_state["data_historico"] = cargar_hojas(xls_historico, hoja_historico)
st.session_state["data_consolidar"] = cargar_hojas(xls_consolidar, ["PLANTILLA"])

# =========================
# Aquí continuarías con toda la lógica de búsqueda y mostrar resultados
# =========================
# (igual que tu versión de intranet, con inputs, filtros, mostrar_nomina_actual, etc.)
