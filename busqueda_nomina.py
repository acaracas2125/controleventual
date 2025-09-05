import pandas as pd
import streamlit as st
import requests
from io import BytesIO
import hashlib
import os

# =========================
# Configuración inicial
# =========================
USUARIOS_FILE = "usuarios.csv"
CSV_COLUMNS = ["usuario", "contraseña", "nombre_completo", "maestro", "mensaje_bienvenida"]

# =========================
# Funciones de usuarios
# =========================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def crear_usuario_maestro():
    if not os.path.exists(USUARIOS_FILE):
        df = pd.DataFrame(columns=CSV_COLUMNS)
        df.loc[0] = {
            "usuario": "acaracas",
            "contraseña": hash_password("caracas"),
            "nombre_completo": "Administrador Maestro",
            "maestro": True,
            "mensaje_bienvenida": "Bienvenido"
        }
        df.to_csv(USUARIOS_FILE, index=False)

def cargar_usuarios():
    crear_usuario_maestro()
    df = pd.read_csv(USUARIOS_FILE)
    # Asegurar que existan todas las columnas
    for col in CSV_COLUMNS:
        if col not in df.columns:
            if col == "maestro":
                df[col] = False
            else:
                df[col] = ""
    df["maestro"] = df["maestro"].astype(bool)
    return df

def guardar_usuarios(df):
    df.to_csv(USUARIOS_FILE, index=False)

def verificar_usuario(usuario, password):
    df = cargar_usuarios()
    df["contraseña"] = df["contraseña"].astype(str)
    hash_pass = hash_password(password)
    fila = df[df["usuario"] == usuario]
    if not fila.empty:
        fila = fila.iloc[0]
        if fila["contraseña"] == hash_pass:
            return fila.to_dict()
    return None

# =========================
# Interfaz de Login
# =========================
st.title("Control de Nómina Eventual - Login")

usuario_input = st.text_input("Usuario")
password_input = st.text_input("Contraseña", type="password")

if st.button("Iniciar sesión"):
    usuario_info = verificar_usuario(usuario_input.strip(), password_input.strip())
    if usuario_info:
        st.success(f"{usuario_info['mensaje_bienvenida']}, {usuario_info['nombre_completo']}!")
        es_maestro = usuario_info["maestro"]

        # =========================
        # Menu maestro
        # =========================
        menu = ["Búsqueda"]
        if es_maestro:
            menu.append("Administrar Usuarios")
        
        opcion = st.selectbox("Selecciona opción:", menu)

        if opcion == "Búsqueda":
            st.subheader("🔎 Búsqueda de Nómina")
            # Aquí va tu código de búsqueda actual
            st.info("Implementa aquí la funcionalidad de búsqueda que ya tienes.")
        
        if opcion == "Administrar Usuarios":
            st.subheader("👤 Administración de Usuarios")
            usuarios_df = cargar_usuarios()
            st.dataframe(usuarios_df)

            st.markdown("---")
            st.write("Agregar nuevo usuario:")
            new_user = st.text_input("Usuario")
            new_pass = st.text_input("Contraseña", type="password")
            new_name = st.text_input("Nombre completo")
            new_maestro = st.checkbox("Es maestro?")
            new_mensaje = st.text_input("Mensaje de bienvenida", value="Bienvenido")

            if st.button("Agregar usuario"):
                if new_user.strip() == "":
                    st.warning("Ingresa un nombre de usuario válido.")
                else:
                    if new_user in usuarios_df["usuario"].values:
                        st.warning("El usuario ya existe.")
                    else:
                        usuarios_df.loc[len(usuarios_df)] = {
                            "usuario": new_user,
                            "contraseña": hash_password(new_pass),
                            "nombre_completo": new_name,
                            "maestro": new_maestro,
                            "mensaje_bienvenida": new_mensaje
                        }
                        guardar_usuarios(usuarios_df)
                        st.success(f"Usuario '{new_user}' agregado correctamente.")
                        st.experimental_rerun()

            st.markdown("---")
            st.write("Eliminar usuario:")
            user_to_delete = st.selectbox("Selecciona usuario a eliminar", usuarios_df["usuario"].values)
            if st.button("Eliminar usuario"):
                if user_to_delete == "acaracas":
                    st.warning("No se puede eliminar al usuario maestro.")
                else:
                    usuarios_df = usuarios_df[usuarios_df["usuario"] != user_to_delete]
                    guardar_usuarios(usuarios_df)
                    st.success(f"Usuario '{user_to_delete}' eliminado.")
                    st.experimental_rerun()

    else:
        st.error("Usuario o contraseña incorrectos.")
