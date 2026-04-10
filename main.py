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
                        nombre TEXT, ruc TEXT UNIQUE, entidad TEXT, detalle_tarea TEXT, 
                        estado TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS declaraciones_fijas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nombre TEXT, ruc TEXT UNIQUE, clave TEXT, tipo_dec TEXT, 
                        celular TEXT, noveno_digito INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS devoluciones_iva (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nombre TEXT, ruc TEXT, correo TEXT, celular TEXT,
                        tipo_devolucion TEXT, valor_solicitado REAL, porcentaje REAL, 
                        abono REAL, saldo REAL)''')
    cursor.execute("INSERT OR IGNORE INTO usuarios VALUES (1, 'admin', 'admin123', 'admin')")
    conn.commit()
    conn.close()

def obtener_dia_vencimiento(digito):
    tabla = {1: 10, 2: 12, 3: 14, 4: 16, 5: 18, 6: 20, 7: 22, 8: 24, 9: 26, 0: 28}
    return tabla.get(digito, 28)

def main():
    st.set_page_config(page_title="Ashka Consultores", layout="wide")
    crear_tablas()
    if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False
    if not st.session_state['autenticado']:
        login()
    else:
        menu_principal()

def login():
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        try: st.image("LOGO PNG PRINCIPAL ASHKA.jpg", width=250)
        except: st.title("🏢 ASHKA CONSULTORES")
    st.divider()
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        user = st.text_input("Usuario")
        pw = st.text_input("Contraseña", type="password")
        if st.button("Ingresar al Sistema", use_container_width=True):
            conn = conectar_db(); cursor = conn.cursor()
            cursor.execute("SELECT id, usuario, rol FROM usuarios WHERE usuario=? AND password=?", (user, pw))
            datos = cursor.fetchone()
            if datos:
                st.session_state.update({"autenticado": True, "user_id": datos[0], "username": datos[1], "rol": datos[2], "pagina": "🏠 Inicio"})
                st.rerun()
            else: st.error("⚠️ Usuario o clave incorrectos")

def menu_principal():
    st.sidebar.image("LOGO PNG PRINCIPAL ASHKA.jpg", width=120)
    if st.sidebar.button("🏠 Ir al Inicio"):
        st.session_state['pagina'] = "🏠 Inicio"
        st.rerun()
    if st.sidebar.button("🚪 Cerrar Sesión"):
        st.session_state['autenticado'] = False
        st.rerun()

    conn = conectar_db()
    pag = st.session_state.get('pagina', "🏠 Inicio")

    # --- BOTÓN DE REGRESAR GENERAL ---
    if pag != "🏠 Inicio":
        if st.button("⬅️ Regresar al Menú Principal"):
            st.session_state['pagina'] = "🏠 Inicio"
            st.rerun()

    # --- 🏠 INICIO ---
    if pag == "🏠 Inicio":
        st.title(f"Bienvenido, {st.session_state['username']}")
        c1, c2, c3 = st.columns(3)
        with c1:
            with st.container(border=True):
                st.write("### 🆕 Trámites")
                if st.button("Abrir Trámites", key="btn_t"): st.session_state['pagina'] = "Tramites"; st.rerun()
        with c2:
            with st.container(border=True):
                st.write("### 🗓️ SRI Fijos")
                if st.button("Ver Calendario", key="btn_f"): st.session_state['pagina'] = "Fijos"; st.rerun()
        with c3:
            with st.container(border=True):
                st.write("### 📊 IVA")
                if st.button("Ver Devoluciones", key="btn_i"): st.session_state['pagina'] = "IVA"; st.rerun()
        
        if st.session_state['rol'] == 'admin':
            st.write("")
            ca, cb, cc = st.columns(3)
            with ca:
                with st.container(border=True):
                    st.write("### 👥 Personal")
                    if st.button("Gestionar Accesos"): st.session_state['pagina'] = "Usuarios"; st.rerun()

    # --- SECCIÓN TRAMITES (CON BUSCADOR) ---
    elif pag == "Tramites":
        st.header("Gestión de Clientes y Trámites")
        busqueda = st.text_input("🔍 Buscar Cliente por RUC o Nombre")
        if busqueda:
            res = pd.read_sql_query(f"SELECT * FROM clientes_tramites WHERE ruc LIKE '%{busqueda}%' OR nombre LIKE '%{busqueda}%'", conn)
            if not res.empty:
                st.success("Cliente encontrado en la base de datos:")
                st.dataframe(res)
            else:
                st.warning("El cliente no existe. Regístrelo abajo:")

        with st.form("form_tramite", clear_on_submit=True):
            st.subheader("Registrar Nuevo Trámite")
            col1, col2 = st.columns(2)
            n = col1.text_input("Nombre Completo")
            r = col1.text_input("RUC / Cédula")
            ent = col2.selectbox("Entidad", ["SRI", "IESS", "MUNICIPIO", "BIESS"])
            det = col2.text_area("Tarea a realizar")
            if st.form_submit_button("Guardar Cliente y Trámite"):
                try:
                    conn.execute("INSERT INTO clientes_tramites (nombre, ruc, entidad, detalle_tarea, estado) VALUES (?,?,?,?,'Por realizar')", (n, r, ent, det))
                    conn.commit(); st.success("✅ Guardado con éxito")
                except: st.error("⚠️ Este RUC ya está registrado.")

    # --- SECCIÓN IVA (COMPLETA) ---
    elif pag == "IVA":
        st.header("Plantilla de Devoluciones IVA")
        with st.form("form_iva", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            nom = c1.text_input("Nombre del Cliente")
            ced = c1.text_input("Cédula / RUC")
            cor = c2.text_input("Correo Electrónico")
            cel = c2.text_input("Número de Celular")
            tipo = c3.selectbox("Tipo de Devolución", ["Adulto Mayor", "Discapacidad", "Impuesto a la Renta", "Exportadores"])
            val = c3.number_input("Valor Solicitado $", min_value=0.0)
            por = st.slider("Porcentaje de Comisión (%)", 1, 25, 10)
            abo = st.number_input("Abono Inicial $", min_value=0.0)
            
            if st.form_submit_button("💾 Guardar y Calcular"):
                comision_total = val * (por / 100)
                saldo_pend = comision_total - abo
                conn.execute("INSERT INTO devoluciones_iva (nombre, ruc, correo, celular, tipo_devolucion, valor_solicitado, porcentaje, abono, saldo) VALUES (?,?,?,?,?,?,?,?,?)",
                             (nom, ced, cor, cel, tipo, val, por, abo, saldo_pend))
                conn.commit()
                st.success(f"✅ Guardado. Saldo pendiente del cliente: ${saldo_pend:.2f}")

        st.subheader("Historial de Devoluciones")
        st.dataframe(pd.read_sql_query("SELECT * FROM devoluciones_iva", conn), use_container_width=True)

    # --- SECCIÓN USUARIOS ---
    elif pag == "Usuarios":
        st.header("Gestión de Colaboradores")
        with st.form("f_u", clear_on_submit=True):
            u = st.text_input("Usuario")
            p = st.text_input("Clave")
            r = st.selectbox("Rol", ["colaborador", "admin"])
            if st.form_submit_button("Crear Acceso"):
                conn.execute("INSERT INTO usuarios (usuario, password, rol) VALUES (?,?,?)", (u,p,r))
                conn.commit(); st.success("Usuario Creado")
    
    conn.close()

if __name__ == "__main__":
    main()