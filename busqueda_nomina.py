# =========================
# IDs de archivos en Google Drive
# =========================
FILE_ID_EXCEL_CONTROL = "15H3ULUuPxBNo_nBHIjUdCiB1EK_ngAvZ"       # Archivo principal
FILE_ID_EXCEL_HISTORICO = "1sg_YeF-k9M6bv3GMpwzbNRIBWf0nf_S3"    # Histórico
FILE_ID_EXCEL_CONSOLIDAR = "14xoBudN1KeCnNAm2yHiUYDLwFeBh0yA-"    # Consolidar

# =========================
# Función para descargar Excel desde Drive
# =========================
import requests
from io import BytesIO
import pandas as pd
import streamlit as st
import os

EXCEL_CACHE_DIR = r"C:\Users\USER-PC0045\Pictures\PAGINA EVENTUAL"  # Puedes cambiar a tu carpeta local

def descargar_excel_drive(file_id, nombre_cache):
    """
    Descarga archivo de Google Drive usando file_id y guarda cache local
    """
    ruta_cache = os.path.join(EXCEL_CACHE_DIR, nombre_cache)
    if os.path.exists(ruta_cache):
        try:
            xls = pd.ExcelFile(ruta_cache, engine="openpyxl")
            return xls
        except:
            os.remove(ruta_cache)  # Borra cache corrupta

    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    try:
        resp = requests.get(url)
        if resp.status_code != 200 or not resp.content[:2] == b'PK':
            st.warning(f"No se pudo descargar el archivo (HTTP {resp.status_code})")
            return None
        with open(ruta_cache, "wb") as f:
            f.write(resp.content)
        xls = pd.ExcelFile(BytesIO(resp.content), engine="openpyxl")
        return xls
    except Exception as e:
        st.warning(f"Error al descargar o leer Excel: {e}")
        return None

# =========================
# Función para cargar hojas de un Excel
# =========================
def cargar_hojas(xls, hojas):
    data = {}
    if not xls:
        return data
    for hoja in hojas:
        if hoja in xls.sheet_names:
            data[hoja] = pd.read_excel(xls, sheet_name=hoja, engine="openpyxl")
    return data

# =========================
# Descargar y cargar todos los archivos
# =========================
xls_control = descargar_excel_drive(FILE_ID_EXCEL_CONTROL, "control_nomina.xlsx")
xls_historico = descargar_excel_drive(FILE_ID_EXCEL_HISTORICO, "historico.xlsx")
xls_consolidar = descargar_excel_drive(FILE_ID_EXCEL_CONSOLIDAR, "consolidar.xlsx")

st.session_state["data_excel"] = cargar_hojas(xls_control, hojas_destino)
st.session_state["data_historico"] = cargar_hojas(xls_historico, hoja_historico)
st.session_state["data_consolidar"] = cargar_hojas(xls_consolidar, ["PLANTILLA"])

st.success("Archivos cargados correctamente en memoria.")
