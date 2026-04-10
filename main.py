import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN DE BASE DE DATOS ---
def conectar_db():
    return sqlite3.connect("consultoria_sistema_final.db", check_same_thread=False)

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

# --- FUNCIONES DE AYUDA (Lógica SRI) ---
def obtener_dia_vencimiento(digito):
    tabla = {1: 10, 2: 12, 3: 14, 4: 16, 5: 18, 6: 20, 7: 22, 8: 24, 9: 26, 0: 28}
    return tabla.get(digito, 28)

# --- VISTAS ---
def login():
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        try:
            st.image("LOGO PNG PRINCIPAL ASHKA.jpg", width=250)
        except:
            st.title("🏛️ ASHKA CONSULTORES")
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
    # Sidebar minimalista
    st.sidebar.image("LOGO PNG PRINCIPAL ASHKA.jpg", width=120)
    st.sidebar.write(f"👤 **{st.session_state['username']}** ({st.session_state['rol']})")
    
    if st.sidebar.button("🏠 Panel Principal"):
        st.session_state['pagina'] = "🏠 Inicio"
        st.rerun()

    if st.sidebar.button("🚪 Cerrar Sesión"):
        st.session_state['autenticado'] = False
        st.rerun()

    conn = conectar_db()
    pag = st.session_state.get('pagina', "🏠 Inicio")

    # --- PANTALLA DE INICIO (ESTILO LEXIS / TARJETAS) ---
    if pag == "🏠 Inicio":
        st.title("Panel de Control")
        st.markdown("---")
        
        c1, c2, c3 = st.columns(3)
        
        with c1:
            with st.container(border=True):
                st.write("### 👥 Clientes")
                st.write("Gestión de trámites rápidos.")
                if st.button("Abrir Trámites", use_container_width=True):
                    st.session_state['pagina'] = "Tramites"
                    st.rerun()
        
        with c2:
            with st.container(border=True):
                st.write("### 📊 Impuestos")
                st.write("Control SRI y Fijos.")
                if st.button("Ver Calendario", use_container_width=True):
                    st.session_state['pagina'] = "Fijos"
                    st.rerun()
        
        with c3:
            with st.container(border=True):
                st.write("### 💰 Devoluciones")
                st.write("Cálculo de IVA.")
                if st.button("Ver Devoluciones", use_container_width=True):
                    st.session_state['pagina'] = "IVA"
                    st.rerun()

        st.divider()
        st.subheader("🔔 Vencimientos Próximos (Clientes Fijos)")
        df_fijos = pd.read_sql_query("SELECT nombre, ruc, noveno_digito, celular FROM declaraciones_fijas", conn)
        
        if not df_fijos.empty:
            dia_hoy = datetime.now().day
            for i, row in df_fijos.iterrows():
                vence = obtener_dia_vencimiento(row['noveno_digito'])
                dias_faltan = vence - dia_hoy
                
                if 0 <= dias_faltan <= 3:
                    with st.warning(f"⚠️ **{row['nombre']}** (RUC finaliza en {row['noveno_digito']}) vence el día {vence}"):
                        mensaje = f"https://wa.me/593{row['celular']}?text=Estimado%20{row['nombre']},%20le%20recordamos%20que%20su%20declaración%20vence%20el%20día%20{vence}.%20Atentamente,%20Ashka%20Consultores."
                        st.link_button("📲 Enviar WhatsApp", mensaje)
        else:
            st.info("No hay vencimientos próximos.")

    # --- SECCIÓN TRAMITES ---
    elif pag == "Tramites":
        st.header("🆕 Registro de Trámites")
        with st.form("f_nuevo"):
            nombre = st.text_input("Nombre Cliente")
            ruc = st.text_input("RUC / Cédula")
            entidad = st.selectbox("Entidad", ["SRI", "IESS", "BIESS", "MUNICIPIO"])
            detalle = st.text_area("Descripción")
            if st.form_submit_button("Guardar"):
                conn.execute("INSERT INTO clientes_tramites (nombre, ruc, entidad, detalle_tarea, estado, usuario_id) VALUES (?,?,?,?,'Por realizar',?)",
                             (nombre, ruc, entidad, detalle, st.session_state['user_id']))
                conn.commit()
                st.success("Guardado!")

    # --- SECCIÓN FIJOS (NUEVA LÓGICA) ---
    elif pag == "Fijos":
        st.header("🗓️ Clientes Fijos y SRI")
        with st.expander("Añadir Cliente Fijo"):
            with st.form("f_fijo_new"):
                n = st.text_input("Nombre")
                r = st.text_input("RUC")
                c = st.text_input("Celular (Ej: 0987654321)")
                dig = st.number_input("Noveno Dígito", 0, 9)
                t = st.selectbox("Tipo", ["Mensual", "Semestral", "Renta"])
                if st.form_submit_button("Registrar"):
                    conn.execute("INSERT INTO declaraciones_fijas (nombre, ruc, celular, noveno_digito, tipo_dec, usuario_id) VALUES (?,?,?,?,?,?)",
                                 (n, r, c, dig, t, st.session_state['user_id']))
                    conn.commit()
                    st.rerun()
        
        df = pd.read_sql_query("SELECT nombre, noveno_digito, tipo_dec, celular FROM declaraciones_fijas", conn)
        st.dataframe(df, use_container_width=True)

    # (Las demás secciones IVA y Colaboradores se mantienen con tu lógica anterior)
    conn.close()

def main():
    st.set_page_config(page_title="Ashka Consultores", layout="wide")
    crear_tablas()
    if not st.session_state.get('autenticado'):
        login()
    else:
        menu_principal()

if __name__ == "__main__":
    main()