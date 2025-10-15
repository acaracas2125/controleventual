import streamlit as st
import pandas as pd
import os
import socket
import io
import numpy as np
import requests  # 🔹 para descargar desde Drive

# =========================
# LOGIN DE USUARIOS
# =========================
usuarios_defecto = pd.DataFrame([
    {"usuario":"acaracas","pasword":"cccc","nombre_completo":"Angel Caracas","maestro":True,"mensaje":"Bienvenido master"},
    {"usuario":"lhernandez","pasword":"lau","nombre_completo":"Laura Hernández Rivera","maestro":True,"mensaje":"Bienvenida Lau"},
    {"usuario":"abigail","pasword":"liz","nombre_completo":"Lizbeth Abigail Candelaria Marcos Martinez","maestro":True,"mensaje":"Bienvenida Lizbeth Abigail"},
    {"usuario":"marcos","pasword":"jefesito","nombre_completo":"Marco Antonio Alarcón Hernández","maestro":True,"mensaje":"Bienvenido Marcos"},    
    {"usuario":"omperez","pasword":"ositis","nombre_completo":"Osiris Monserrat Pérez Nieto","maestro":True,"mensaje":"Bienvenida Ositis"},
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

# =========================
# Sidebar: Usuario y configuración
# =========================
if st.session_state.get("usuario_logueado"):
    st.sidebar.success(f"Usuario activo: {st.session_state['nombre_completo']}")

# =========================
# Configuración de página y estilos
# =========================
st.set_page_config(page_title="Control (V 2.0.0)📝", page_icon="💡")
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

# =========================
# Función para obtener IP local
# =========================
def obtener_ip_local():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except:
        return "No disponible"

ip_local = obtener_ip_local()
st.markdown(f"""
<div style='position: fixed; bottom: 10px; right: 10px; 
            background-color: rgba(255,255,255,0.7); 
            padding: 5px 10px; border-radius: 5px; 
            font-size: 12px; color: black; z-index:9999;'>
    Accede desde otro equipo: http://{ip_local}:8501/
</div>
""", unsafe_allow_html=True)

def descargar_drive(url, destino):
    """Descarga un archivo de Google Drive y valida que sea Excel válido."""
    try:
        r = requests.get(url, allow_redirects=True, stream=True)
        if r.status_code == 200:
            contenido = r.content
            # Validar que no sea una página HTML (Drive devolviendo error)
            if contenido.strip().startswith(b"<!DOCTYPE html>"):
                st.warning(f"⚠️ Google Drive devolvió una página HTML para {os.path.basename(destino)}. Verifica el enlace o permisos.")
                return False
            with open(destino, "wb") as f:
                f.write(contenido)
            # Validar que el archivo tenga estructura de ZIP (xlsx)
            with open(destino, "rb") as f:
                cabecera = f.read(4)
                if cabecera != b'PK\x03\x04':
                    st.error(f"❌ Archivo corrupto o no válido: {os.path.basename(destino)}")
                    os.remove(destino)
                    return False
            return True
        else:
            st.warning(f"No se pudo descargar (código {r.status_code}): {url}")
            return False
    except Exception as e:
        st.error(f"Error descargando {url}: {e}")
        return False

# =========================
# Descarga de archivos si no existen
# =========================
carpeta = r"C:\Users\USER-PC0045\Pictures\PAGINA EVENTUAL"
os.makedirs(carpeta, exist_ok=True)

for nombre, url in urls_drive.items():
    destino = os.path.join(carpeta, nombre)
    if not os.path.exists(destino):
        st.info(f"Descargando {nombre} desde Google Drive...")
        exito = descargar_drive(url, destino)
        if not exito:
            st.error(f"No se pudo descargar correctamente {nombre}. Verifica el enlace.")


# =========================
# URLs directas de Google Drive
# =========================
urls_drive = {
    "control_nomina.xlsx": "https://drive.google.com/uc?export=download&id=17O33v9JmMsItavMNm7qw4MX2Zx_K7a2f",
    "Historico.xlsx":       "https://drive.google.com/uc?export=download&id=10KPDPXUKVF4ogCKzTugI7IbQ0HDzxS3Z",
    "CONSOLIDAR.xlsx":      "https://drive.google.com/uc?export=download&id=1jzTeF5Trhi2-zAZgzzLPZEEcBDOMyDJT",
    "PLANTILLA.xlsx":       "https://drive.google.com/uc?export=download&id=1veDSctRyAc1LewNvkamqOfRUnW5tWXQN",
    "VARIOS.xlsx":          "https://drive.google.com/uc?export=download&id=15oo1JnSuNaT9QUGplu7X8qAwHpbQ8RFa"
}

# =========================
# Descarga de archivos si no existen
# =========================
carpeta = r"C:\Users\USER-PC0045\Pictures\PAGINA EVENTUAL"
os.makedirs(carpeta, exist_ok=True)

for nombre, url in urls_drive.items():
    destino = os.path.join(carpeta, nombre)
    if not os.path.exists(destino):
        st.info(f"Descargando {nombre} desde Google Drive...")
        exito = descargar_drive(url, destino)
        if not exito:
            st.error(f"No se pudo descargar correctamente {nombre}. Verifica el enlace.")


# =========================
# Funciones de carga
# =========================
@st.cache_data
def cargar_datos(ruta):
    if not os.path.exists(ruta):
        return {}
    xls = pd.ExcelFile(ruta, engine="openpyxl")
    data = {}
    for hoja in xls.sheet_names:
        data[hoja] = pd.read_excel(xls, sheet_name=hoja, engine="openpyxl")
    return data

# =========================
# Cargar archivos automáticamente
# =========================
rutas = {
    "data_excel": os.path.join(carpeta, "control_nomina.xlsx"),
    "data_historico": os.path.join(carpeta, "Historico.xlsx"),
    "data_consolidar": os.path.join(carpeta, "CONSOLIDAR.xlsx"),
    "data_plantilla": os.path.join(carpeta, "PLANTILLA.xlsx"),
    "data_varios": os.path.join(carpeta, "VARIOS.xlsx")
}

for key, ruta in rutas.items():
    if key not in st.session_state or st.session_state[key] is None:
        st.session_state[key] = cargar_datos(ruta)

# =========================
# Mostrar resultados (ajustado)
# =========================
if "resultados" in st.session_state and st.session_state["resultados"]:
    resultados_ordenados = {}

    # Primero NOMINA ACTUAL si existe
    if "NOMINA ACTUAL" in st.session_state["resultados"]:
        resultados_ordenados["NOMINA ACTUAL"] = st.session_state["resultados"]["NOMINA ACTUAL"]

    # Luego el resto de las hojas
    for hoja, df_res in st.session_state["resultados"].items():
        if hoja != "NOMINA ACTUAL":
            resultados_ordenados[hoja] = df_res

    # =========================
    # MINI RESUMEN - NÓMINA ACTUAL (entre búsqueda y resultados)
    # =========================
    def mostrar_nomina_actual():
        df = resultados_ordenados.get("NOMINA ACTUAL")
        if df is None or df.empty:
            st.info("Mini Resumen - NOMINA ACTUAL\nFilas encontradas: 0\nNo se encontraron columnas de importe reconocibles para sumar.")
            return

        if "indice_nomina" not in st.session_state:
            st.session_state["indice_nomina"] = 0
        idx = st.session_state["indice_nomina"]
        if idx >= len(df):
            st.session_state["indice_nomina"] = len(df) - 1
            idx = st.session_state["indice_nomina"]

        fila = df.iloc[idx]

        resumen = {
            "CENTRO": fila.get("DES_JURIS", " "),
            "RFC": fila.get("RFC", ""),
            "NOMBRE": fila.get("NOMBRE", ""),
            "F. INGRESO": str(fila.get("F. INGRESO", ""))[:10],
            "CODIGO": fila.get("CODIGO", ""),
            "DESCRIPCIÓN DEL CÓDIGO": fila.get("DESCRIPCION DEL CODIGO", ""),
            "ULTIMO PAGO PROGRAMADO": fila.get("ULTIMO PAGO PROGRAMADO", ""),
            "PERCEPCIONES": fila.get("PERCEPCIONES", ""),
            "DEDUCCIONES": fila.get("DEDUCCIONES", ""),
            "NETO": fila.get("NETO", ""),
            "CLABE": fila.get("CLABE", ""),
            "NOMINA": fila.get("NOMINA", "")
        }

        def formato_pesos(valor):
            try:
                return f"${float(valor):,.2f}"
            except:
                return valor

        for key in ["PERCEPCIONES", "DEDUCCIONES", "NETO"]:
            resumen[key] = formato_pesos(resumen[key])

        st.markdown("---")
        st.markdown("<div class='resumen-box'>", unsafe_allow_html=True)
        st.markdown("<h3>🧾 Mini Resumen - Nómina Actual</h3>", unsafe_allow_html=True)

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
                if st.session_state["indice_nomina"] < len(df) - 1:
                    st.session_state["indice_nomina"] += 1
        st.markdown("</div>", unsafe_allow_html=True)

        st.subheader("Tabla completa de Nómina Actual")
        st.dataframe(df, width=900, height=250)

    # 👉 Mostrar el mini resumen justo aquí (entre búsqueda y resultados)
    mostrar_nomina_actual()

    # =========================
    # Mostrar el resto de las hojas debajo
    # =========================
    for hoja, df_res in resultados_ordenados.items():
        if hoja != "NOMINA ACTUAL":
            st.subheader(f"Resultados de '{hoja}'")
            st.dataframe(df_res, width=1500, height=180)


# =========================
# Función de búsqueda individual optimizada con NumPy
# =========================
def buscar_datos_todos_libros(todos_los_libros, valores, asunto="", columna_especifica="", valor_especifico=""):
    res = {}
    total_hojas = sum([len(libro) for libro in todos_los_libros.values()])
    progreso = st.progress(0)
    hoja_idx = 0

    valores_upper = {k: str(v).strip().upper() for k, v in valores.items() if v}

    for libro_nombre, libro_dict in todos_los_libros.items():
        for hoja, df in libro_dict.items():
            hoja_idx += 1
            progreso.progress(min(1.0, hoja_idx/total_hojas))
            if df.empty:
                continue

            df_upper = df.fillna("").astype(str).applymap(lambda x: x.strip().upper())
            mask = np.ones(len(df_upper), dtype=bool)

            # Búsqueda exacta o parcial
            if columna_especifica and valor_especifico:
                if columna_especifica in df_upper.columns:
                    mask &= df_upper[columna_especifica].str.contains(valor_especifico.strip().upper(), na=False)
                else:
                    mask &= False
            else:
                for col, val in valores_upper.items():
                    if col in df_upper.columns:
                        mask &= df_upper[col].str.contains(val, na=False)
                    else:
                        mask &= False
                if asunto and "ASUNTO" in df_upper.columns:
                    mask &= df_upper["ASUNTO"].str.contains(asunto.strip().upper(), na=False)

            df_filtrado = df[mask]
            if not df_filtrado.empty:
                prefijo = "" if libro_nombre=="CONTROL" else f"{libro_nombre} - "
                res[f"{prefijo}{hoja}"] = df_filtrado

    return res

# =========================
# Función de búsqueda masiva optimizada sin desconfigurar
# =========================
def buscar_masivo_todos_libros(todos_los_libros, df_busqueda):
    resultados_combinados = {}
    total_hojas = sum([len(libro) for libro in todos_los_libros.values()])
    hoja_idx = 0
    progreso = st.progress(0)

    df_busqueda = df_busqueda.fillna("").astype(str).applymap(lambda x: x.strip().upper())

    for libro_nombre, libro_dict in todos_los_libros.items():
        for hoja, df_hoja in libro_dict.items():
            hoja_idx += 1
            progreso.progress(min(1.0, hoja_idx/total_hojas))
            if df_hoja.empty:
                continue

            df_hoja_upper = df_hoja.fillna("").astype(str).applymap(lambda x: x.strip().upper())
            df_res_hoja = pd.DataFrame()

            for _, fila_busq in df_busqueda.iterrows():
                # Creamos máscara inicial True
                mask = np.ones(len(df_hoja_upper), dtype=bool)

                for col in df_busqueda.columns:
                    val = fila_busq[col]
                    if val != "":
                        if col in df_hoja_upper.columns:
                            mask &= df_hoja_upper[col] == val
                        else:
                            mask &= False

                # Concatenamos solo filas que cumplan toda la fila de búsqueda
                df_filtrado = df_hoja[mask]
                if not df_filtrado.empty:
                    df_res_hoja = pd.concat([df_res_hoja, df_filtrado], ignore_index=True)

            if not df_res_hoja.empty:
                resultados_combinados[f"{libro_nombre} - {hoja}"] = df_res_hoja

    return resultados_combinados

# =========================
# Pestañas
# =========================
tab1, tab2 = st.tabs(["Búsqueda Individual", "Búsqueda Masiva"])

# =========================
# Pestaña 1: Búsqueda Individual
# =========================
with tab1:
    with st.form("form_busqueda"):
        col1, col2 = st.columns(2)
        rfc = col1.text_input("RFC")
        nombre = col2.text_input("NOMBRE")
        col3, col4 = st.columns(2)
        adscripcion = col3.text_input("ADSCRIPCION")
        cuenta = col4.text_input("CUENTA")
        asunto_val = st.text_input("ASUNTO")
        col5, col6 = st.columns(2)
        columna_busqueda_val = col5.text_input("Columna")
        valor_busqueda_val = col6.text_input("Valor a buscar")

        col_btn1, col_btn2 = st.columns(2)
        buscar = col_btn1.form_submit_button("Buscar")
        limpiar = col_btn2.form_submit_button("Limpiar búsqueda")

    if limpiar:
        for key in ["rfc","nombre","adscripcion","cuenta",
                    "asunto_val","columna_busqueda_val","valor_busqueda_val","resultados"]:
            if key in st.session_state:
                del st.session_state[key]
        st.session_state.query_params = {}

    if buscar:
        valores_dict = {
            "RFC": rfc.strip(),
            "NOMBRE": nombre.strip(),
            "ADSCRIPCION": adscripcion.strip(),
            "CUENTA": cuenta.strip()
        }
        todos_los_libros = {
            "CONTROL": st.session_state["data_excel"],
            "HISTORICO": st.session_state["data_historico"],
            "CONSOLIDAR": st.session_state["data_consolidar"],
            "PLANTILLA": st.session_state["data_plantilla"],
            "VARIOS": st.session_state["data_varios"]
        }
        st.session_state["resultados"] = buscar_datos_todos_libros(
            todos_los_libros, valores_dict,
            asunto=asunto_val.strip(),
            columna_especifica=columna_busqueda_val.strip(),
            valor_especifico=valor_busqueda_val.strip()
        )
        if not st.session_state["resultados"]:
            st.info("No se encontraron coincidencias.")
        else:
            for hoja, df_res in st.session_state["resultados"].items():
                st.subheader(f"Resultados de '{hoja}'")
                st.dataframe(df_res, width=1500, height=180)

# =========================
# Pestaña 2: Búsqueda Masiva
# =========================
with tab2:
    st.subheader("Búsqueda Masiva")
    plantilla_columns = ["RFC","NOMBRE","ADSCRIPCION","CUENTA","OFICIO ELABORADO","ASUNTO"]
    plantilla_excel = io.BytesIO()
    pd.DataFrame(columns=plantilla_columns).to_excel(plantilla_excel, index=False, engine="openpyxl")
    plantilla_excel.seek(0)
    st.download_button("📥 Plantilla de busqueda masiva", plantilla_excel,
                       file_name="plantilla_busqueda.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    archivo_carga = st.file_uploader("Sube la plantilla con los criterios de búsqueda", type=["xlsx"])
    col_busq1, col_busq2 = st.columns(2)
    ejecutar_busqueda = col_busq1.button("🔍 Búsqueda masiva")
    limpiar_busqueda_mass = col_busq2.button("🧹 Limpiar búsqueda masiva")

    if archivo_carga:
        df_busqueda = pd.read_excel(archivo_carga, engine="openpyxl")
        st.session_state.df_busqueda = df_busqueda

    if limpiar_busqueda_mass:
        if "df_busqueda" in st.session_state:
            del st.session_state["df_busqueda"]
        if "resultados_mass" in st.session_state:
            del st.session_state["resultados_mass"]
        st.session_state.query_params = {}

    if ejecutar_busqueda and st.session_state.get("df_busqueda") is not None:
        todos_los_libros = {
            "CONTROL": st.session_state["data_excel"],
            "HISTORICO": st.session_state["data_historico"],
            "CONSOLIDAR": st.session_state["data_consolidar"],
            "PLANTILLA": st.session_state["data_plantilla"],
            "VARIOS": st.session_state["data_varios"]
        }
        st.session_state["resultados_mass"] = buscar_masivo_todos_libros(todos_los_libros, st.session_state.df_busqueda)
        if not st.session_state["resultados_mass"]:
            st.info("No se encontraron coincidencias.")
        else:
            for hoja, df_res in st.session_state["resultados_mass"].items():
                st.subheader(f"Resultados de '{hoja}'")
                st.dataframe(df_res, width=1500, height=180)

# =========================
# Pie de página
# =========================
st.markdown("""
    <hr>
    <div style='text-align: center; font-size: 12px; color: gray;'>
        Aviso de Privacidad                           
Con fundamento en la Ley de Transparencia y la Ley de Protección de Datos Personales en Posesión de Sujetos Obligados del Estado de Veracruz, se informa que los datos personales mostrados en este sitio tienen carácter confidencial y se utilizan exclusivamente con fines administrativos para la consulta y verificación de información de nómina del personal de los Servicios de Salud de Veracruz.     
La información no podrá ser difundida o compartida sin autorización del titular de la Unidad Administrativa, salvo disposición legal en contrario. 

© Derechos Reservados. Angel Caracas.  
    </div>
""", unsafe_allow_html=True)


