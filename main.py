import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN DE BASE DE DATOS ---
def conectar_db():
    return sqlite3.connect("consultoria_sistema_final_v2.db", check_same_thread=False)

def crear_tablas():
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY, usuario TEXT UNIQUE, password TEXT, rol TEXT)')
    cursor.execute('''CREATE TABLE IF NOT EXISTS clientes_tramites (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nombre TEXT, ruc TEXT, entidad TEXT, detalle_tarea TEXT, 
                        estado TEXT, usuario_id INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS declaraciones_fijas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nombre TEXT, ruc TEXT, clave TEXT, tipo_dec TEXT, 
                        celular TEXT, noveno_digito INTEGER, usuario_id INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS devoluciones_iva (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nombre TEXT, ruc TEXT, correo TEXT, celular TEXT,
                        tipo_devolucion TEXT, valor_solicitado REAL, porcentaje REAL, 
                        abono REAL, saldo REAL, usuario_id INTEGER)''')
    
    cursor.execute("INSERT OR IGNORE INTO usuarios VALUES (1, 'admin', 'admin123', 'admin')")
    conn.commit()
    conn.close()

# --- FUNCIONES DE AYUDA ---
def obtener_dia_vencimiento(digito):
    tabla = {1: 10, 2: 12, 3: 14, 4: 16, 5: 18, 6: 20, 7: 22, 8: 24, 9: 26, 0: 28}
    return tabla.get(digito, 28)

def main():
    st.set_page_config(page_title="Ashka Consultores", layout="wide")
    crear_tablas()
    
    if 'autenticado' not in st.session_state:
        st.session_state['autenticado'] = False

    if not st.session_state['autenticado']:
        login()
    else:
        menu_principal()

def login():
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        try:
            st.image("LOGO PNG PRINCIPAL ASHKA.jpg", width=250)
        except:
            st.title("🏢 ASHKA CONSULTORES")
        st.subheader("Gestión Tributaria y Laboral")
    
    st.divider()
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        user = st.text_input("Usuario")
        pw = st.text_input("Contraseña", type="password")
        if st.button("Ingresar al Sistema", use_container_width=True):
            conn = conectar_db()
            cursor = conn.cursor()
            cursor.execute("SELECT id, usuario, rol FROM usuarios WHERE usuario=? AND password=?", (user, pw))
            datos = cursor.fetchone()
            if datos:
                st.session_state.update({"autenticado": True, "user_id": datos[0], "username": datos[1], "rol": datos[2], "pagina": "🏠 Inicio"})
                st.rerun()
            else: 
                st.error("⚠️ Usuario o clave incorrectos")

def menu_principal():
    st.sidebar.image("LOGO PNG PRINCIPAL ASHKA.jpg", width=120)
    st.sidebar.write(f"👤 **{st.session_state['username']}**")
    
    if st.sidebar.button("🏠 Inicio / Panel"):
        st.session_state['pagina'] = "🏠 Inicio"
        st.rerun()

    if st.sidebar.button("🚪 Salir"):
        st.session_state['autenticado'] = False
        st.rerun()

    conn = conectar_db()
    pag = st.session_state.get('pagina', "🏠 Inicio")

    # --- 🏠 INICIO / PANEL DE CONTROL ---
    if pag == "🏠 Inicio":
        st.title("Panel de Control")
        st.markdown("---")
        
        # FILA 1 DE TARJETAS
        c1, c2, c3 = st.columns(3)
        with c1:
            with st.container(border=True):
                st.write("### 🆕 Trámites")
                st.write("Registro de clientes nuevos.")
                if st.button("Abrir Trámites", use_container_width=True):
                    st.session_state['pagina'] = "Tramites"
                    st.rerun()
        
        with c2:
            with st.container(border=True):
                st.write("### 🗓️ SRI Fijos")
                st.write("Control de declaraciones mensuales.")
                if st.button("Ver Calendario", use_container_width=True):
                    st.session_state['pagina'] = "Fijos"
                    st.rerun()
        
        with c3:
            with st.container(border=True):
                st.write("### 📊 IVA")
                st.write("Cálculo de devoluciones.")
                if st.button("Ver Devoluciones", use_container_width=True):
                    st.session_state['pagina'] = "IVA"
                    st.rerun()

        # FILA 2 (SOLO PARA ADMIN)
        if st.session_state['rol'] == 'admin':
            st.write("")
            ca, cb, cc = st.columns(3)
            with ca:
                with st.container(border=True):
                    st.write("### 👥 Personal")
                    st.write("Gestionar colaboradores.")
                    if st.button("Gestionar Accesos", use_container_width=True):
                        st.session_state['pagina'] = "Usuarios"
                        st.rerun()

        st.divider()
        st.subheader("🔔 Alertas de Vencimiento SRI")
        df_fijos = pd.read_sql_query("SELECT nombre, noveno_digito, celular FROM declaraciones_fijas", conn)
        if not df_fijos.empty:
            dia_hoy = datetime.now().day
            for _, row in df_fijos.iterrows():
                vence = obtener_dia_vencimiento(row['noveno_digito'])
                if 0 <= (vence - dia_hoy) <= 3:
                    st.warning(f"⚠️ {row['nombre']} vence el día {vence}")
                    link = f"https://wa.me/593{row['celular']}?text=Hola%20{row['nombre']},%20tu%20declaración%20vence%20el%20{vence}."
                    st.link_button("📲 Notificar", link)
        else:
            st.info("No hay clientes registrados en la base fija.")

    # --- SECCIÓN TRAMITES ---
    elif pag == "Tramites":
        st.header("🆕 Registro de Trámites Rápidos")
        with st.form("f_nuevo"):
            nombre = st.text_input("Nombre Cliente")
            ruc = st.text_input("RUC")
            entidad = st.selectbox("Entidad", ["SRI", "IESS", "MUNICIPIO"])
            detalle = st.text_area("Detalle")
            if st.form_submit_button("Guardar"):
                conn.execute("INSERT INTO clientes_tramites (nombre, ruc, entidad, detalle_tarea, estado) VALUES (?,?,?,?,'Por realizar')", (nombre, ruc, entidad, detalle))
                conn.commit()
                st.success("Registrado!")

    # --- SECCIÓN FIJOS ---
    elif pag == "Fijos":
        st.header("🗓️ Clientes Fijos (SRI)")
        with st.form("f_fijos"):
            c1, c2 = st.columns(2)
            n = c1.text_input("Nombre")
            r = c1.text_input("RUC")
            cel = c2.text_input("Celular (Ej: 0999888777)")
            dig = c2.number_input("Noveno Dígito", 0, 9)
            if st.form_submit_button("Registrar"):
                conn.execute("INSERT INTO declaraciones_fijas (nombre, ruc, celular, noveno_digito) VALUES (?,?,?,?)", (n, r, cel, dig))
                conn.commit()
                st.rerun()
        df = pd.read_sql_query("SELECT * FROM declaraciones_fijas", conn)
        st.dataframe(df)

    # --- SECCIÓN IVA ---
    elif pag == "IVA":
        st.header("📊 Devoluciones de IVA")
        with st.form("f_iva"):
            c1, c2 = st.columns(2)
            nom = c1.text_input("Cliente")
            val = c1.number_input("Valor Solicitado $", min_value=0.0)
            por = c2.slider("Comisión (%)", 1, 20, 10)
            abo = c2.number_input("Abono $", min_value=0.0)
            if st.form_submit_button("Calcular Saldo"):
                saldo = (val * (por/100)) - abo
                conn.execute("INSERT INTO devoluciones_iva (nombre, valor_solicitado, porcentaje, abono, saldo) VALUES (?,?,?,?,?)", (nom, val, por, abo, saldo))
                conn.commit()
                st.success(f"Saldo pendiente: ${saldo}")
        df_iva = pd.read_sql_query("SELECT * FROM devoluciones_iva", conn)
        st.dataframe(df_iva)

    # --- SECCIÓN USUARIOS (GESTIÓN COLABORADORES) ---
    elif pag == "Usuarios":
        st.header("👥 Gestión de Colaboradores")
        with st.form("f_users"):
            nuevo_u = st.text_input("Nombre de Usuario")
            nuevo_p = st.text_input("Contraseña")
            rol = st.selectbox("Rol", ["colaborador", "admin"])
            if st.form_submit_button("Crear Usuario"):
                try:
                    conn.execute("INSERT INTO usuarios (usuario, password, rol) VALUES (?,?,?)", (nuevo_u, nuevo_p, rol))
                    conn.commit()
                    st.success(f"Usuario {nuevo_u} creado.")
                except:
                    st.error("El usuario ya existe.")
        
        st.subheader("Usuarios Actuales")
        df_u = pd.read_sql_query("SELECT usuario, rol FROM usuarios", conn)
        st.table(df_u)

    conn.close()

if __name__ == "__main__":
    main()