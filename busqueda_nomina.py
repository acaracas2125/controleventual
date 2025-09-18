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
st.set_page_config(page_title="Control de Nómina (V 2.0.0)📝", page_icon="💡")
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
# IDs de Google Drive (poner los correctos)
# =========================
FILE_ID_EXCEL_CONTROL = "PUT_YOUR_ID_HERE"
FILE_ID_EXCEL_HISTORICO = "PUT_YOUR_ID_HERE"
FILE_ID_EXCEL_CONSOLIDAR = "PUT_YOUR_ID_HERE"

# =========================
# Funciones de descarga y carga de Excel
# =========================
@st.cache_data(show_spinner="Descargando archivos desde Drive...")
def descargar_excel_drive(file_id):
    try:
        url = f"https://drive.google.com/uc?export=download&id={file_id}"
        resp = requests.get(url)
        if resp.status_code != 200 or not resp.content[:2] == b'PK':
            st.warning(f"No se pudo descargar el archivo (HTTP {resp.status_code})")
            return None
        return BytesIO(resp.content)
    except Exception as e:
        st.error(f"Error al descargar Excel: {e}")
        return None

@st.cache_data(show_spinner="Cargando hojas de Excel...")
def cargar_hojas(xls_bytesio, hojas):
    if not xls_bytesio:
        return {}
    xls = pd.ExcelFile(xls_bytesio, engine="openpyxl")
    data = {}
    for hoja in hojas:
        if hoja in xls.sheet_names:
            data[hoja] = pd.read_excel(xls, sheet_name=hoja, engine="openpyxl")
    return data

# =========================
# Cargar archivos
# =========================
if st.button("📂 Cargar archivos desde Drive") or st.session_state["data_excel"] is None:
    xls_control = descargar_excel_drive(FILE_ID_EXCEL_CONTROL)
    xls_historico = descargar_excel_drive(FILE_ID_EXCEL_HISTORICO)
    xls_consolidar = descargar_excel_drive(FILE_ID_EXCEL_CONSOLIDAR)

    st.session_state["data_excel"] = cargar_hojas(xls_control, hojas_destino)
    st.session_state["data_historico"] = cargar_hojas(xls_historico, hoja_historico)
    st.session_state["data_consolidar"] = cargar_hojas(xls_consolidar, ["PLANTILLA"])

    st.success("Archivos cargados correctamente en memoria.")

# =========================
# Inputs de búsqueda
# =========================
st.title("Control de Nómina (V 2.0.0)")

col1,col2 = st.columns(2)
rfc = col1.text_input("RFC")
nombre = col2.text_input("NOMBRE")
col3,col4 = st.columns(2)
oficio_solicitud = col3.text_input("OFICIO DE SOLICITUD")
adscripcion = col4.text_input("ADSCRIPCION")
col5,col6 = st.columns(2)
cuenta = col5.text_input("CUENTA")
oficio_elaborado = col6.text_input("OFICIO ELABORADO")
col7 = st.text_input("ASUNTO")  # NUEVO CAMPO

col_buscar,col_limpiar = st.columns(2)
buscar = col_buscar.button("Buscar")
limpiar = col_limpiar.button("Limpiar")

if limpiar:
    for key in ["rfc","nombre","oficio_solicitud","adscripcion","cuenta","oficio_elaborado","asunto"]:
        if key in st.session_state:
            del st.session_state[key]
    st.session_state["resultados"] = None
    st.session_state["indice_nomina"] = 0

# =========================
# Función de búsqueda unificada
# =========================
def letra_a_indice(letra):
    letra = letra.upper()
    idx = 0
    for c in letra:
        idx = idx*26 + (ord(c)-ord('A')+1)
    return idx-1

def buscar_datos(data_dict, valores, asunto="", tipo="CONTROL"):
    res = {}
    for hoja, df in data_dict.items():
        if df.empty: continue
        filtro = pd.Series([True]*len(df))
        for campo, val in valores.items():
            if val:
                if tipo=="HISTORICO":
                    if campo in mapa_historico:
                        idx = letra_a_indice(mapa_historico[campo])
                        filtro &= df.iloc[:,idx].astype(str).str.upper().str.contains(val.upper(), na=False)
                elif tipo=="CONSOLIDAR":
                    col = campo if campo in df.columns else None
                    if col: filtro &= df[col].astype(str).str.upper().str.contains(val.upper(), na=False)
                else:
                    filtro &= df.astype(str).apply(lambda c: c.str.upper().str.contains(val.upper(), na=False)).any(axis=1)
        if asunto and "ASUNTO" in df.columns:
            filtro &= df["ASUNTO"].astype(str).str.upper().str.contains(asunto.upper(), na=False)
        df_filtrado = df[filtro]
        if not df_filtrado.empty:
            prefijo = "" if tipo=="CONTROL" else f"{tipo} - "
            res[f"{prefijo}{hoja}"] = df_filtrado
    return res

# =========================
# Ejecutar búsqueda
# =========================
if buscar:
    if not st.session_state["data_excel"] or not st.session_state["data_historico"] or not st.session_state["data_consolidar"]:
        st.warning("Primero carga los archivos desde Drive")
    else:
        valores_dict = {
            "RFC": rfc.strip(),
            "NOMBRE": nombre.strip(),
            "ADSCRIPCION": adscripcion.strip(),
            "CUENTA": cuenta.strip(),
            "OFICIO ELABORADO": oficio_elaborado.strip()
        }
        asunto_val = col7.strip()
        res_control = buscar_datos(st.session_state["data_excel"], valores_dict, asunto_val, tipo="CONTROL")
        res_hist = buscar_datos(st.session_state["data_historico"], valores_dict, asunto_val, tipo="HISTORICO")
        res_consol = buscar_datos(st.session_state["data_consolidar"], valores_dict, asunto_val, tipo="CONSOLIDAR")
        st.session_state["resultados"] = {**res_control, **res_hist, **res_consol}
        st.session_state["indice_nomina"]=0
        if not st.session_state["resultados"]:
            st.info("No se encontraron coincidencias.")

# =========================
# Mostrar resultados
# =========================
resultados_ordenados = {}
if st.session_state["resultados"]:
    if "NOMINA ACTUAL" in st.session_state["resultados"]:
        resultados_ordenados["NOMINA ACTUAL"] = st.session_state["resultados"]["NOMINA ACTUAL"]
    for hoja, df_res in st.session_state["resultados"].items():
        if hoja != "NOMINA ACTUAL":
            resultados_ordenados[hoja] = df_res

# Aquí puedes incluir la función mostrar_nomina_actual() tal como la tenías en tu código anterior

# =========================
# Pie de página
# =========================
st.markdown("""
    <hr>
    <div style='text-align: center; font-size: 12px; color: gray;'>
        © Derechos Reservados. Angel Caracas.
    </div>
""", unsafe_allow_html=True)
