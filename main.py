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
                        nombre TEXT, ruc TEXT, clave TEXT, tipo_dec TEXT, usuario_id INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS devoluciones_iva (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nombre TEXT, ruc TEXT, correo TEXT, celular TEXT,
                        tipo_devolucion TEXT, valor_solicitado REAL, porcentaje REAL, 
                        abono REAL, saldo REAL, usuario_id INTEGER)''')
    
    cursor.execute("INSERT OR IGNORE INTO usuarios VALUES (1, 'admin', 'admin123', 'admin')")
    conn.commit()
    conn.close()

def main():
    st.set_page_config(page_title="Consultoría Klever Pro", layout="wide")
    crear_tablas()
    
    if 'autenticado' not in st.session_state:
        st.session_state['autenticado'] = False

    if not st.session_state['autenticado']:
        login()
    else:
        menu_principal()

def login():
    # 1. Centramos el logo y los títulos
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100) 
        st.title("🏢 ASHKA CONSULTORES")
        st.subheader("Gestión Tributaria y Laboral")
    
    st.divider() # Una línea elegante para separar

    # 2. Formulario de ingreso
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
                st.session_state.update({"autenticado": True, "user_id": datos[0], "username": datos[1], "rol": datos[2]})
                st.rerun()
            else: 
                st.error("⚠️ Usuario o clave incorrectos")

def menu_principal():
    # --- LOGO Y BIENVENIDA EN LA BARRA LATERAL ---
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/609/609034.png", width=80)
    st.sidebar.header(f"Sesión: {st.session_state['username']}")
    
    # --- RESTO DEL MENÚ ---
    opciones = ["🏠 Inicio / Resumen", "🆕 Clientes Nuevo (Trámites)", "📊 Devoluciones IVA", "🗓️ Declaraciones Fijas", "⚠️ Trabajos Pendientes"]
    
    if st.session_state['rol'] == 'admin':
        opciones.append("👥 Gestionar Colaboradores")
    
    choice = st.sidebar.radio("Navegación", opciones)
    
    if st.sidebar.button("Salir"):
        st.session_state['autenticado'] = False
        st.rerun()

    conn = conectar_db()
    
    # Aquí siguen los "if choice == ..." que ya tienes programados

    # --- 🏠 INICIO / RESUMEN ---
    if choice == "🏠 Inicio / Resumen":
        st.header("📊 Resumen de Trabajos Pendientes")
        # Lógica: Reflejar lo que está "Por realizar" en Trámites
        df_resumen = pd.read_sql_query("SELECT nombre, entidad, detalle_tarea FROM clientes_tramites WHERE estado='Por realizar'", conn)
        if not df_resumen.empty:
            st.warning(f"Atención: Tienes {len(df_resumen)} tareas pendientes en el equipo.")
            st.table(df_resumen)
        else:
            st.success("No hay trabajos pendientes registrados.")

    # --- 🆕 CLIENTES NUEVO (CON BUSCADOR) ---
    elif choice == "🆕 Clientes Nuevo (Trámites)":
        st.header("Registro de Trámites Rápidos")
        
        with st.expander("🔍 Buscar Cliente Existente"):
            busc = st.text_input("Buscar por Nombre o RUC")
            if busc:
                res = pd.read_sql_query(f"SELECT * FROM clientes_tramites WHERE nombre LIKE '%{busc}%' OR ruc LIKE '%{busc}%'", conn)
                st.dataframe(res)

        with st.form("f_nuevo"):
            col1, col2 = st.columns(2)
            nombre = col1.text_input("Nombre Cliente")
            ruc = col1.text_input("RUC / Cédula")
            entidad = col1.selectbox("Entidad", ["SRI", "IESS", "BIESS", "MUNICIPIO"])
            detalle = col2.text_area("¿Qué se debe realizar? (Ej: Declarar Mayo)")
            estado = col2.radio("Estado Inicial", ["Por realizar", "Realizado"])
            if st.form_submit_button("Guardar"):
                conn.execute("INSERT INTO clientes_tramites (nombre, ruc, entidad, detalle_tarea, estado, usuario_id) VALUES (?,?,?,?,?,?)",
                             (nombre, ruc, entidad, detalle, estado, st.session_state['user_id']))
                conn.commit()
                st.success("Trámite registrado correctamente.")

    # --- 📊 DEVOLUCIONES IVA (RESTAURADO) ---
    elif choice == "📊 Devoluciones IVA":
        st.header("Plantilla de Devoluciones de IVA")
        with st.expander("➕ Registrar Nueva Devolución"):
            with st.form("f_iva"):
                c1, c2, c3 = st.columns(3)
                nom = c1.text_input("Nombre")
                id_ruc = c1.text_input("RUC")
                mail = c1.text_input("Correo")
                tel = c2.text_input("Celular")
                tipo_dev = c2.selectbox("Tipo", ["Tercera Edad", "Discapacidad", "Exportadores"])
                val_sol = c2.number_input("Valor Solicitado $", min_value=0.0)
                porc = c3.slider("Porcentaje Contrato (%)", 1, 25, 10)
                abono = c3.number_input("Abono $", min_value=0.0)
                
                if st.form_submit_button("Calcular y Guardar"):
                    total_comision = val_sol * (porc / 100)
                    saldo = total_comision - abono
                    conn.execute("INSERT INTO devoluciones_iva (nombre, ruc, correo, celular, tipo_devolucion, valor_solicitado, porcentaje, abono, saldo, usuario_id) VALUES (?,?,?,?,?,?,?,?,?,?)",
                                 (nom, id_ruc, mail, tel, tipo_dev, val_sol, porc, abono, saldo, st.session_state['user_id']))
                    conn.commit()
                    st.success(f"Guardado. Saldo calculado: ${saldo:.2f}")

        df_iva = pd.read_sql_query("SELECT nombre, ruc, celular, valor_solicitado, porcentaje, abono, saldo FROM devoluciones_iva", conn)
        st.dataframe(df_iva, use_container_width=True)

    # --- 🗓️ DECLARACIONES FIJAS (CAMPOS NUEVOS) ---
    elif choice == "🗓️ Declaraciones Fijas":
        st.header("Base de Datos: Clientes Fijos Mensuales")
        with st.form("f_fijas"):
            c1, c2 = st.columns(2)
            n_fijo = c1.text_input("Nombres")
            r_fijo = c1.text_input("Cédula o RUC")
            cl_fijo = c2.text_input("Clave")
            t_fijo = c2.selectbox("Tipo de Declaración", ["Mensual", "Semestral", "Impuesto a la Renta", "Otros"])
            if st.form_submit_button("Registrar Cliente Fijo"):
                conn.execute("INSERT INTO declaraciones_fijas (nombre, ruc, clave, tipo_dec, usuario_id) VALUES (?,?,?,?,?)",
                             (n_fijo, r_fijo, cl_fijo, t_fijo, st.session_state['user_id']))
                conn.commit()
                st.success("Cliente fijo añadido a la base de datos.")
        
        df_fijas = pd.read_sql_query("SELECT nombre, ruc, tipo_dec FROM declaraciones_fijas", conn)
        st.table(df_fijas)

    # --- ⚠️ TRABAJOS PENDIENTES ---
    elif choice == "⚠️ Trabajos Pendientes":
        st.header("Tablero de Tareas por Realizar")
        df_p = pd.read_sql_query("SELECT id, nombre, entidad, detalle_tarea FROM clientes_tramites WHERE estado='Por realizar'", conn)
        if df_p.empty:
            st.info("No hay trabajos pendientes.")
        else:
            for i, row in df_p.iterrows():
                with st.expander(f"📌 {row['nombre']} - {row['entidad']}"):
                    st.write(f"**Detalle:** {row['detalle_tarea']}")
                    if st.button("Marcar como REALIZADO", key=row['id']):
                        conn.execute(f"UPDATE clientes_tramites SET estado='Realizado' WHERE id={row['id']}")
                        conn.commit()
                        st.rerun()

    # --- 👥 GESTIONAR COLABORADORES (RESTAURADO) ---
    elif choice == "👥 Gestionar Colaboradores":
        st.header("Gestión de Usuarios y Claves")
        with st.form("crear_user"):
            u = st.text_input("Nuevo Usuario")
            p = st.text_input("Nueva Clave")
            if st.form_submit_button("Crear Acceso"):
                try:
                    conn.execute("INSERT INTO usuarios (usuario, password, rol) VALUES (?,?,'colaborador')", (u, p))
                    conn.commit()
                    st.success(f"Usuario '{u}' creado correctamente.")
                except: st.error("El usuario ya existe.")

    conn.close()

if __name__ == "__main__":
    main()