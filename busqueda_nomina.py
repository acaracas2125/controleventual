import pandas as pd
import streamlit as st

# Lista de hojas destino
hojas_destino = [
    "NUEVO COSTEO", "COSTEO O.C.", "CORRES 2025", "BASE FEDERAL 2025", "BASE", "VALIDACION IMPROS", "REGISTRO REVERSOS",
    "CAMBIO DE ADSCRIPCION", "STATUS DE COMISION", "COMISIONES", "OFICIOS 2025-ENERO", "OFICIOS 2025-FEBRERO",
    "OFICIOS 2025-MARZO", "OFICIO 2025-JUNIO", "LIC. MARCELA.", "CONTRATOS", "MEMOS", "MTRA. NOELIA",
    "STATUS DE OFI. DEPÁCHADOS OLI", "COMISIONES (2)", "Hoja1 (5)", "NOMINA ACTUAL"
]

# Matriz de columnas condicionantes
# (se agregó la última columna para "NOMINA ACTUAL")
columnas_condicionantes = [
    ["C", "C", "", "D", "", "E", "E"] + [""] * 14 + ["C"],  # RFC
    ["E", "D", "J", "E", "", "F", "F", "D", "C", "D", "C", "C", "C", "C", "E", "E", "E", "E", "E", "E", "D", "D"],  # NOMBRE
    ["AC", "I", "D", "J", "", "", "", "B", "", "B", "", "", "", "A", "", "", "", "", "", "", "", ""],  # OFICIO SOLICITUD
    ["P", "V", "D,I", "W", "", "L", "L", "", "D", "", "", "", "", "", "", "", "", "", "", "", "", "G"],  # ADSCRIPCION
    ["AE", "X", "", "Y", "", "M", "M"] + [""] * 14 + ["O"],  # CUENTA
    [""] * 7 + ["G", "A", "G", "A", "A", "A", "F", "C", "C", "C", "C", "C", "C", "B"] + [""]  # OFICIO ELABORADO
]

# Función para convertir letra de columna a índice (A=0, B=1, etc.)
def excel_col_to_index(col):
    col = col.upper()
    index = 0
    for char in col:
        index = index * 26 + (ord(char) - ord('A') + 1)
    return index - 1  # 0-based

# Cargar datos de Excel (solo hojas necesarias)
@st.cache_data
def cargar_datos(archivo, hojas):
    data = {}
    for hoja in hojas:
        try:
            df = pd.read_excel(archivo, sheet_name=hoja, engine="openpyxl")
            data[hoja] = df
        except Exception:
            pass
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

# Interfaz web con Streamlit
st.title("Control de Nómina Eventual - Búsqueda")

# Ruta al archivo Excel
archivo_excel = st.text_input(
    "Ruta al archivo Excel",
    value=r"C:\Users\USER-PC0045\Pictures\PAGINA EVENTUAL\control_nomina.xlsx"
)

# Entradas de búsqueda
rfc = st.text_input("RFC")
nombre = st.text_input("NOMBRE")
oficio_solicitud = st.text_input("OFICIO DE SOLICITUD")
adscripcion = st.text_input("ADSCRIPCION")
cuenta = st.text_input("CUENTA")
oficio_elaborado = st.text_input("OFICIO ELABORADO")

if archivo_excel and st.button("Buscar"):
    try:
        data = cargar_datos(archivo_excel, hojas_destino)
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
                st.dataframe(df_res.head(200))  # muestra máximo 200 filas
    except Exception as e:
        st.error(f"Error al cargar el archivo: {e}")

if st.button("Limpiar"):
    st.experimental_rerun()
