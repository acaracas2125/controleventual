import pandas as pd
import streamlit as st
import requests
from io import BytesIO

# Lista de hojas destino (incluyendo nuevas)
hojas_destino = [
    "NUEVO COSTEO", "COSTEO O.C.", "CORRES 2025", "BASE FEDERAL 2025", "BASE", "VALIDACION IMPROS", "REGISTRO REVERSOS",
    "CAMBIO DE ADSCRIPCION", "STATUS DE COMISION", "COMISIONES", "OFICIOS 2025-ENERO", "OFICIOS 2025-FEBRERO",
    "OFICIOS 2025-MARZO", "OFICIO 2025-JUNIO", "LIC. MARCELA.", "CONTRATOS", "MEMOS", "MTRA. NOELIA",
    "STATUS DE OFI. DEPÁCHADOS OLI", "COMISIONES (2)", "Hoja1 (5)", "NOMINA ACTUAL",
    "DIVERSOS", "FORMATOS DE DESC. DIV", "CHEQUES-REVERSOS", "PENSIONES Y FORMATOS"
]

# Matriz de columnas condicionantes (RFC y Nombre)
columnas_condicionantes = [
    ["C", "C", "", "D", "", "E", "E"] + [""] * 14 + ["C"] + ["B", "B", "B", "B"],  # RFC
    ["E", "D", "J", "E", "", "F", "F", "D", "C", "D", "C", "C", "C", "C", "E", "E", "E", "E", "E", "E", "D", "D"] + ["C", "C", "C", "C"],  # NOMBRE
    ["AC", "I", "D", "J", "", "", "", "B", "", "B", "", "", "", "A", "", "", "", "", "", "", "", ""] + ["", "", "", ""],  # OFICIO SOLICITUD
    ["P", "V", "D,I", "W", "", "L", "L", "", "D", "", "", "", "", "", "", "", "", "", "", "", "", "G"] + ["", "", "", ""],  # ADSCRIPCION
    ["AE", "X", "", "Y", "", "M", "M"] + [""] * 14 + ["O"] + ["", "", "", ""],  # CUENTA
    [""] * 7 + ["G", "A", "G", "A", "A", "A", "F", "C", "C", "C", "C", "C", "C", "B"] + [""] + ["", "", "", ""]  # OFICIO ELABORADO
]

# Función para convertir letra de columna a índice (A=0, B=1, etc.)
def excel_col_to_index(col):
    col = col.upper()
    index = 0
    for char in col:
        index = index * 26 + (ord(char) - ord('A') + 1)
    return index - 1  # 0-based

# Descargar y cargar Excel desde Google Drive
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

# Función de búsqueda vectorizada
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

# --- Interfaz con Streamlit ---
st.title("Control de Nómina Eventual - Búsqueda")

# Botón para actualizar datos de base
if st.button("Actualizar datos de base"):
    cargar_datos_drive.clear()
    st.success("La caché se ha limpiado. La próxima búsqueda descargará el archivo actualizado.")

# Entrada para el ID del archivo
file_id = st.text_input(
    "ID del archivo en Google Drive:",
    value="17O33v9JmMsItavMNm7qw4MX2Zx_K7a2f",
    key="file_id"
)

# Campos de búsqueda en dos columnas
col1, col2 = st.columns(2)
rfc = col1.text_input("RFC", key="rfc")
nombre = col2.text_input("NOMBRE", key="nombre")

col3, col4 = st.columns(2)
oficio_solicitud = col3.text_input("OFICIO DE SOLICITUD", key="oficio_solicitud")
adscripcion = col4.text_input("ADSCRIPCION", key="adscripcion")

col5, col6 = st.columns(2)
cuenta = col5.text_input("CUENTA", key="cuenta")
oficio_elaborado = col6.text_input("OFICIO ELABORADO", key="oficio_elaborado")

# Botón de búsqueda
if file_id and st.button("Buscar"):
    try:
        data = cargar_datos_drive(file_id, hojas_destino)
        valores = [
            rfc.strip(), nombre.strip(), oficio_solicitud.strip(),
            adscripcion.strip(), cuenta.strip(), oficio_elaborado.strip()
        ]
        resultados = buscar_coincidencias(data, valores)

        if not resultados:
            st.info("No se encontraron coincidencias.")
        else:
            for hoja, df_res in resultados.items():
                st.subheader(f"Resultados de '{hoja}'")
                # Contenedor con scroll horizontal y vertical, solo 5 filas visibles
                st.dataframe(df_res, width=1500, height=180)  # altura aprox. 5 filas
    except Exception as e:
        st.error(f"Error al procesar: {e}")

# Botón de limpiar
if st.button("Limpiar"):
    st.experimental_rerun()
import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# =========================
# Función para convertir enlace de Google Sheets/Drive a Excel
# =========================
def gsheet_to_excel_url(google_url: str) -> str:
    """
    Convierte cualquier URL de Google Sheets o Drive en un enlace de descarga directa XLSX.
    """
    if "/d/" in google_url:
        try:
            file_id = google_url.split("/d/")[1].split("/")[0]
            return f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
        except Exception:
            raise ValueError("No se pudo extraer el ID del archivo de Google Sheets.")
    else:
        raise ValueError("El enlace de Google Sheets no es válido. Debe contener '/d/'.")

# =========================
# Cargar datos desde Google Sheets con cache
# =========================
@st.cache_data
def cargar_datos_excel(google_url: str, hojas: list):
    url_excel = gsheet_to_excel_url(google_url)
    r = requests.get(url_excel)
    r.raise_for_status()
    file = BytesIO(r.content)
    data = pd.read_excel(file, sheet_name=hojas)
    return data

# =========================
# App principal
# =========================
st.title("🔎 Búsqueda en Nómina Eventual")

# Pega aquí tu enlace de Google Sheets
google_sheet_url = "https://docs.google.com/spreadsheets/d/15H3ULUuPxBNo_nBHIjUdCiB1EK_ngAvZ/edit?usp=sharing"

# Define las hojas que quieres leer
hojas_destino = ["BASE", "NUEVO COSTEO", "NOMINA ACTUAL"]

try:
    data = cargar_datos_excel(google_sheet_url, hojas_destino)
    st.success("✅ Datos cargados correctamente.")
except Exception as e:
    st.error(f"Error al cargar los datos: {e}")
    st.stop()

# Input para búsqueda
criterio = st.text_input("Escribe un CURP, RFC o Nombre:")

if criterio:
    criterio = criterio.strip().lower()
    resultados = []
    
    for hoja, df in data.items():
        df_str = df.astype(str).apply(lambda x: x.str.lower())
        coincidencias = df[df_str.apply(lambda x: x.str.contains(criterio, na=False)).any(axis=1)]
        
        if not coincidencias.empty:
            st.subheader(f"📄 Resultados en hoja: {hoja}")
            st.dataframe(coincidencias)
            resultados.append(coincidencias)
    
    if not resultados:
        st.warning("⚠️ No se encontraron coincidencias.")

# =========================
# Pie de página
# =========================
st.markdown(
    """
    <style>
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        text-align: center;
        font-size: 12px;
        color: gray;
        padding: 5px;
        background-color: #f9f9f9;
    }
    </style>
    <div class="footer">
        © Derechos Reservados. LACB  =)
    </div>
    """,
    unsafe_allow_html=True
)
