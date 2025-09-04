import pandas as pd
import streamlit as st
import requests
from io import BytesIO

hojas_destino = [
    "NUEVO COSTEO", "COSTEO O.C.", "CORRES 2025", "BASE FEDERAL 2025", "BASE", "VALIDACION IMPROS", "REGISTRO REVERSOS",
    "CAMBIO DE ADSCRIPCION", "STATUS DE COMISION", "COMISIONES", "OFICIOS 2025-ENERO", "OFICIOS 2025-FEBRERO",
    "OFICIOS 2025-MARZO", "OFICIO 2025-JUNIO", "LIC. MARCELA.", "CONTRATOS", "MEMOS", "MTRA. NOELIA",
    "STATUS DE OFI. DEPÁCHADOS OLI", "COMISIONES (2)", "Hoja1 (5)", "NOMINA ACTUAL"
]

def gsheet_to_excel_url(google_url):
    file_id = google_url.split("/d/")[1].split("/")[0]
    return f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"

@st.cache_data(show_spinner=True)
def cargar_datos_csv(google_url, hojas):
    url_excel = gsheet_to_excel_url(google_url)
    
    # 📥 Descargar archivo Excel primero
    resp = requests.get(url_excel)
    if resp.status_code != 200:
        st.error("No se pudo descargar el archivo desde Google Drive. Verifica permisos o el enlace.")
        return {}
    
    xls = pd.ExcelFile(BytesIO(resp.content), engine="openpyxl")
    data = {}
    for hoja in hojas:
        if hoja in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=hoja, engine="openpyxl")
            # Convertir a CSV en memoria
            csv_buffer = BytesIO()
            df.to_csv(csv_buffer, index=False)
            csv_buffer.seek(0)
            df_csv = pd.read_csv(csv_buffer)
            data[hoja] = df_csv
    return data

# --- Ejemplo de uso ---
st.title("Prueba carga Google Sheets -> Excel -> CSV")

google_sheet_url = st.text_input(
    "Enlace de Google Sheets",
    value="https://drive.google.com/file/d/15H3ULUuPxBNo_nBHIjUdCiB1EK_ngAvZ/view"
)

if google_sheet_url:
    data = cargar_datos_csv(google_sheet_url, hojas_destino)
    if data:
        st.success("Archivo descargado y convertido a CSV en memoria.")
        st.write("Hojas cargadas:", list(data.keys()))



