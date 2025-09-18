import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import os
import hashlib
import socket

# =========================
# Archivos y URLs
# =========================
USUARIOS_FILE = "usuarios_app.xlsx"  # puedes mantener local
CONSULTAS_FILE = "consultas.csv"
MENSAJE_FILE = "mensaje.txt"

# Pendientes: coloca aquí los links de Drive de cada archivo Excel
DRIVE_CONTROL = "https://docs.google.com/spreadsheets/d/15H3ULUuPxBNo_nBHIjUdCiB1EK_ngAvZ/edit?usp=drive_link&ouid=109199175635163763551&rtpof=true&sd=true"
DRIVE_HISTORICO = "https://docs.google.com/spreadsheets/d/1sg_YeF-k9M6bv3GMpwzbNRIBWf0nf_S3/edit?usp=drive_link&ouid=109199175635163763551&rtpof=true&sd=true"
DRIVE_CONSOLIDAR = "https://docs.google.com/spreadsheets/d/14xoBudN1KeCnNAm2yHiUYDLwFeBh0yA-/edit?usp=drive_link&ouid=109199175635163763551&rtpof=true&sd=true"

# =========================
# Funciones de utilidad
# =========================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def descargar_excel_drive(url):
    """Descargar Excel desde Google Drive usando el link de compartir"""
    try:
        # Extraer el file_id del URL, sin importar parámetros extras
        import re
        match = re.search(r"/d/([a-zA-Z0-9-_]+)", url)
        if not match:
            st.warning(f"No se pudo extraer el file_id del URL: {url}")
            return None
        file_id = match.group(1)
        download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        resp = requests.get(download_url)
        if resp.status_code != 200 or not resp.content[:2] == b'PK':
            st.warning(f"No se pudo descargar el archivo (HTTP {resp.status_code})")
            return None
        return BytesIO(resp.content)
    except Exception as e:
        st.warning(f"No se pudo descargar el archivo: {e}")
        return None


def cargar_hojas(xls, hojas):
    """Cargar hojas específicas de un archivo Excel (BytesIO o path)"""
    if xls is None:
        return {}
    try:
        if isinstance(xls, BytesIO):
            xls_file = pd.ExcelFile(xls, engine="openpyxl")
        else:
            xls_file = pd.ExcelFile(xls, engine="openpyxl")
        data = {}
        for hoja in hojas:
            if hoja in xls_file.sheet_names:
                data[hoja] = pd.read_excel(xls_file, sheet_name=hoja, engine="openpyxl")
        return data
    except Exception as e:
        st.warning(f"Error al descargar o leer Excel: {e}")
        return {}

def letra_a_indice(letra):
    letra = letra.upper()
    indice = 0
    for char in letra:
        indice = indice*26 + (ord(char)-ord('A')+1)
    return indice-1

# =========================
# Login de usuarios
# =========================
usuarios_default = pd.DataFrame([
    {"usuario":"acaracas","pasword":"cccc","nombre_completo":"Angel Caracas","maestro":True,"mensaje":"Bienvenido master"},
    {"usuario":"lhernandez","pasword":"lau","nombre_completo":"Laura Hernández Rivera","maestro":True,"mensaje":"Bienvenida Lau"},
    {"usuario":"omperez","pasword":"ositis","nombre_completo":"Osiris Monserrat Pérez","maestro":True,"mensaje":"Bienvenida Ositis"},
    {"usuario":"miros","pasword":"tiamo","nombre_completo":"Miroslava Jimenez Candia","maestro":True,"mensaje":"Bienvenida hermosa =)   10!"}
])

# Intentar cargar archivo de usuarios
if os.path.exists(USUARIOS_FILE):
    try:
        usuarios_excel = pd.read_excel(USUARIOS_FILE, engine="openpyxl")
        usuarios = pd.concat([usuarios_default, usuarios_excel], ignore_index=True)
    except Exception as e:
        st.error(f"No se pudo cargar el archivo de usuarios: {e}")
        usuarios = usuarios_default.copy()
else:
    usuarios = usuarios_default.copy()

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
# Variables de sesión
# =========================
for key in ["data_excel","data_historico","data_consolidar","resultados","indice_nomina"]:
    if key not in st.session_state:
        st.session_state[key] = None if key != "indice_nomina" else 0

# =========================
# Hojas de Excel
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
# Cargar archivos desde Drive
# =========================
if st.button("📂 Cargar archivos desde Drive") or st.session_state["data_excel"] is None:
    xls_control = descargar_excel_drive(DRIVE_CONTROL)
    xls_historico = descargar_excel_drive(DRIVE_HISTORICO)
    xls_consolidar = descargar_excel_drive(DRIVE_CONSOLIDAR)

    st.session_state["data_excel"] = cargar_hojas(xls_control, hojas_destino)
    st.session_state["data_historico"] = cargar_hojas(xls_historico, hoja_historico)
    st.session_state["data_consolidar"] = cargar_hojas(xls_consolidar, ["PLANTILLA"])

    st.success("Archivos cargados correctamente en memoria.")

# =========================
# Inputs de búsqueda
# =========================
st.title("Control de Nómina Eventual")

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
# Función unificada de búsqueda
# =========================
def buscar_datos(data_dict, valores, asunto="", tipo="CONTROL"):
    res = {}
    for hoja, df in data_dict.items():
        if df.empty:
            continue
        filtro = pd.Series([True]*len(df))
        for campo, val in valores.items():
            if val:
                if tipo == "HISTORICO":
                    if campo in mapa_historico:
                        idx = letra_a_indice(mapa_historico[campo])
                        filtro &= df.iloc[:,idx].astype(str).str.upper().str.contains(val.upper(), na=False)
                elif tipo == "CONSOLIDAR":
                    if campo == "RFC":
                        col = "RFC" if "RFC" in df.columns else df.columns[3]
                    elif campo == "NOMBRE":
                        col = "FUNCION / NOMBRE" if "FUNCION / NOMBRE" in df.columns else df.columns[4]
                    elif campo == "ADSCRIPCION":
                        col = "ADSCRIPCION NOMINAL" if "ADSCRIPCION NOMINAL" in df.columns else df.columns[21]
                    else:
                        col = campo if campo in df.columns else None
                    if col:
                        filtro &= df[col].astype(str).str.upper().str.contains(val.upper(), na=False)
                else:  # CONTROL
                    cond = df.astype(str).apply(lambda c: c.str.upper().str.contains(val.upper(), na=False))
                    filtro &= cond.any(axis=1)
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
        st.warning("Primero carga los archivos")
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

def mostrar_nomina_actual():
    df = resultados_ordenados.get("NOMINA ACTUAL")
    if df is None or df.empty: 
        return
    idx = st.session_state["indice_nomina"]
    if idx >= len(df): st.session_state["indice_nomina"] = len(df)-1; idx = st.session_state["indice_nomina"]

    fila = df.iloc[idx]
    resumen = {
        "CENTRO": fila.get("CENTRO",""),
        "RFC": fila.get("RFC",""),
        "NOMBRE": fila.get("NOMBRE",""),
        "F. INGRESO": str(fila.get("F. INGRESO",""))[:10],
        "CODIGO": fila.get("CODIGO",""),
        "DESCRIPCIÓN DEL CODIGO": fila.get("DESCRIPCION DEL CODIGO",""),
        "ULTIMO PAGO PROGRAMADO": fila.get("ULTIMO PAGO PROGRAMADO",""),
        "PERCEPCIONES": fila.get("PERCEPCIONES",""),
        "DEDUCCIONES": fila.get("DEDUCCIONES",""),
        "NETO": fila.get("NETO",""),
        "CLABE": fila.get("CLABE",""),
        "NOMINA": fila.get("NOMINA","")
    }

    def formato_pesos(valor):
        try:
            return f"${float(valor):,.2f}"
        except:
            return valor

    for key in ["PERCEPCIONES","DEDUCCIONES","NETO"]:
        resumen[key] = formato_pesos(resumen[key])

    st.markdown("<div class='resumen-box'>", unsafe_allow_html=True)
    st.markdown("<h3> Resumen de trabajador Quincena Actual</h3>", unsafe_allow_html=True)
    cols_html = "<div class='resumen-grid'>"
    for campo, valor in resumen.items():
        cols_html += f"<div class='campo'>{campo}:</div><div class='valor'>{valor}</div>"
    cols_html += "</div>"
    st.markdown(cols_html, unsafe_allow_html=True)

    col_prev, col_next = st.columns(2)
    with col_prev:
        if st.button("⬅️ Anterior", key="prev"):
            if st.session_state["indice_nomina"] > 0:
                st.session_state["indice_nomina"] -= 1
    with col_next:
        if st.button("Siguiente ➡️", key="next"):
            if st.session_state["indice_nomina"] < len(df)-1:
                st.session_state["indice_nomina"] += 1
    st.markdown("</div>", unsafe_allow_html=True)

    st.subheader("Tabla completa de Nómina Actual")
    st.dataframe(df, width=900, height=250)

if resultados_ordenados:
    mostrar_nomina_actual()
    for hoja, df_res in resultados_ordenados.items():
        if hoja != "NOMINA ACTUAL":
            st.subheader(f"Resultados de '{hoja}'")
            st.dataframe(df_res, width=1500, height=180)

# =========================
# Pie de página
# =========================
st.markdown("""
    <hr>
    <div style='text-align: center; font-size: 12px; color: gray;'>
        © Derechos Reservados. Angel Caracas.
    </div>
""", unsafe_allow_html=True)



