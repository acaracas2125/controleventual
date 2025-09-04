import pandas as pd
import streamlit as st
import requests
from io import BytesIO

# =========================
# Configuración de hojas
# =========================
hojas_destino = [
    "NUEVO COSTEO", "COSTEO O.C.", "CORRES 2025", "BASE FEDERAL 2025", "BASE",
    "VALIDACION IMPROS", "REGISTRO REVERSOS", "CAMBIO DE ADSCRIPCION", "STATUS DE COMISION",
    "COMISIONES", "OFICIOS 2025-ENERO", "OFICIOS 2025-FEBRERO", "OFICIOS 2025-MARZO",
    "OFICIO 2025-JUNIO", "LIC. MARCELA.", "CONTRATOS", "MEMOS", "MTRA. NOELIA",
    "STATUS DE OFI. DEPÁCHADOS OLI", "COMISIONES (2)", "Hoja1 (5)", "NOMINA ACTUAL",
    "DIVERSOS", "FORMATOS DE DESC. DIV", "CHEQUES-REVERSOS", "PENSIONES Y FORMATOS"
]

# Columnas condicionantes (RFC, Nombre, Oficio, etc.)
columnas_condicionantes = [
    ["C", "C", "", "D", "", "E", "E"] + [""] * 14 + ["C"] + ["B", "B", "B", "B"],  # RFC
    ["E", "D", "J", "E", "", "F", "F", "D", "C", "D", "C", "C", "C", "C", "E", "E", "E", "E", "E", "E", "D", "D"] + ["C", "C", "C", "C"],  # NOMBRE
    ["AC", "I", "D", "J", "", "", "", "B", "", "B", "", "", "", "A", "", "", "", "", "", "", "", ""] + ["", "", "", ""],  # OFICIO SOLICITUD
    ["P", "V", "D,I", "W", "", "L", "L", "", "D", "", "", "", "", "", "", "", "", "", "", "", "", "G"] + ["", "", "", ""],  # ADSCRIPCION
    ["AE", "X", "", "Y", "", "M", "M"] + [""] * 14 + ["O"] + ["", "", "", ""],  # CUENTA
    [""] * 7 + ["G", "A", "G", "A", "A", "A", "F", "C", "C", "C", "C", "C", "C", "B"] + [""] + ["", "", "", ""]  # OFICIO ELABORADO
]

# =========================
# Funciones auxiliares
# =========================
def excel_col_to_index(col):
    """Convierte letra de columna Excel en índice 0-based"""
    col = col.upper()
    index = 0
    for char in col:
        index = index * 26 + (ord(char) - ord('A') + 1)
    return index - 1

def gsheet_to_excel_url(google_url: str) -> str:
    """Convierte un enlace de Google Sheets en descarga directa XLSX"""
    if "/d/" in google_url:
        file_id = google_url.split("/d/")[1].split("/")[0]
        return f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
    else:
        raise ValueError("El enlace de Google Sheets no es válido.")

@st.cache_data(show_spinner="Descargando y procesando Excel desde Google Drive...")
def cargar_datos_excel(google_url: str, hojas: list):
    """Descarga y carga un archivo Excel desde Google Drive"""
    url_excel = gsheet_to_excel_url(google_url)
    r = requests.get(url_excel)
    r.raise_for_status()
    file = BytesIO(r.content)
    xls = pd.ExcelFile(file, engine="openpyxl")
    data = {}
    for hoja in hojas:
        if hoja in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=hoja, engine="openpyxl")
            data[hoja] = df
    return data

def buscar_coincidencias(data, valores_buscar):
    """Aplica filtros de búsqueda en cada hoja"""
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
# Interfaz Streamlit
# =========================
st.title("🔎 Control de Nómina Eventual - Búsqueda")

# Entrada para enlace de Google Sheets
google_sheet_url = st.text_input(
    "Pega aquí el enlace de Google Sheets (Excel en Drive):",
    value="https://docs.google.com/spreadsheets/d/15H3ULUuPxBNo_nBHIjUdCiB1EK_ngAvZ/edit?usp=sharing"
)

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

# Botón de búsqueda
if google_sheet_url and st.button("Buscar"):
    try:
        data = cargar_datos_excel(google_sheet_url, hojas_destino)
        valores = [
            rfc.strip(), nombre.strip(), oficio_solicitud.strip(),
            adscripcion.strip(), cuenta.strip(), oficio_elaborado.strip()
        ]
        resultados = buscar_coincidencias(data, valores)

        if not resultados:
            st.info("No se encontraron coincidencias.")
        else:
            for hoja, df_res in resultados.items():
                st.subheader(f"📄 Resultados en hoja: {hoja}")
                st.dataframe(df_res, width=1500, height=180)
    except Exception as e:
        st.error(f"Error al procesar: {e}")

# =========================
# Pie de página fijo
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
