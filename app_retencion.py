import streamlit as st
import sqlite3
import pandas as pd
from fpdf import FPDF
import hashlib
from datetime import datetime, timedelta
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
import os
import base64
import smtplib
import random
import math
import io
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import altair as alt
from PIL import Image, ImageDraw
import re
import time 

# ==========================================
# 🧠 INTELIGENCIA ARTIFICIAL (BIOMETRÍA)
# ==========================================
try:
    import face_recognition
    import numpy as np
    IA_DISPONIBLE = True
except ImportError:
    IA_DISPONIBLE = False

def comparar_rostros(documento_bytes, selfie_bytes):
    if not IA_DISPONIBLE: return False, "⚠️ Librerías de IA no instaladas."
    try:
        img_doc = face_recognition.load_image_file(io.BytesIO(documento_bytes))
        img_selfie = face_recognition.load_image_file(io.BytesIO(selfie_bytes))
        enc_doc = face_recognition.face_encodings(img_doc)
        enc_selfie = face_recognition.face_encodings(img_selfie)
        if not enc_doc: return False, "⚠️ No veo cara en el documento."
        if not enc_selfie: return False, "⚠️ No veo cara en la selfie."
        match = face_recognition.compare_faces([enc_doc[0]], enc_selfie[0], tolerance=0.6)
        return (True, "✅ Identidad Verificada Correctamente.") if match[0] else (False, "❌ Los rostros no coinciden.")
    except Exception as e: return False, f"Error técnico de IA: {str(e)}"

# ==========================================
# 🔐 GESTIÓN DE SECRETOS
# ==========================================
try:
    SMTP_EMAIL = st.secrets["email"]["address"]
    SMTP_PASSWORD = st.secrets["email"]["password"]
    GOOGLE_CLIENT_ID = st.secrets["google"]["client_id"]
    GOOGLE_CLIENT_SECRET = st.secrets["google"]["client_secret"]
except:
    SMTP_EMAIL = "error"; SMTP_PASSWORD = "error"
    GOOGLE_CLIENT_ID = "error"; GOOGLE_CLIENT_SECRET = "error"

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
REDIRECT_URI = "https://atomo-app-mzfqjvym9gu3wxb66dqueb.streamlit.app/"
SCOPES = ["openid", "https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/gmail.send"]

# ==========================================
# 📱 CONFIGURACIÓN VISUAL (CSS CORREGIDO FINAL)
# ==========================================
st.set_page_config(page_title="Átomo.co", page_icon="⚛️", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Montserrat', sans-serif; }
    
    /* FONDO OSCURO APP */
    .stApp { background-color: #0B1120; background-image: radial-gradient(at 50% 0%, #172554 0%, transparent 70%); color: #FFFFFF !important; }
    
    /* TEXTO GENERAL BLANCO (Títulos, párrafos, etiquetas) */
    h1, h2, h3, h4, h5, h6, p, label, li { color: #FFFFFF !important; }

    /* ==============================
       FIX GLOBAL: EXPANDERS (st.expander)
       - Texto visible en fondos oscuros
       - Hover azul
       ============================== */

    div[data-testid="stExpander"] summary {
        background: rgba(15, 23, 42, 0.85) !important; /* azul oscuro */
        border: 1px solid rgba(148, 163, 184, 0.35) !important;
        border-radius: 12px !important;
        padding: 10px 14px !important;
    }

    /* Texto del título del expander (ej: “Nuevo Cliente”, preguntas FAQ) */
    div[data-testid="stExpander"] summary p,
    div[data-testid="stExpander"] summary span,
    div[data-testid="stExpander"] summary div {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        font-weight: 700 !important;
    }

    /* Iconos del expander (flecha / + / etc.) */
    div[data-testid="stExpander"] summary svg {
        fill: #FFFFFF !important;
        color: #FFFFFF !important;
    }

    /* Hover: azul */
    div[data-testid="stExpander"] summary:hover {
        background: rgba(14, 165, 233, 0.25) !important; /* azul */
        border-color: rgba(34, 211, 238, 0.6) !important;
    }

    /* Cuerpo del expander (contenido desplegado) */
    div[data-testid="stExpander"] div[role="region"] {
        border: 1px solid rgba(148, 163, 184, 0.20) !important;
        border-radius: 12px !important;
        padding: 12px !important;
        background: rgba(2, 6, 23, 0.15) !important; /* sutil */
    }
    
    /* --- INPUTS BLANCOS CON LETRA NEGRA --- */
    input, textarea { 
        color: #000000 !important; 
        -webkit-text-fill-color: #000000 !important; 
        background-color: #FFFFFF !important; 
        font-weight: 600 !important;
    }
    div[data-baseweb="input"], div[data-baseweb="base-input"], div[data-testid="stForm"] { 
        background-color: #FFFFFF !important; 
        border-radius: 8px !important; 
        border: 1px solid #E2E8F0 !important; 
    }
    
    /* --- FIX SELECTBOX Y MENÚS DESPLEGABLES --- */
    div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }
    div[data-testid="stSelectbox"] div[data-baseweb="select"] div {
        color: #000000 !important;
    }
    ul[data-baseweb="menu"] li {
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }
    ul[data-baseweb="menu"] li div, ul[data-baseweb="menu"] li span {
        color: #000000 !important;
    }

    /* --- FIX CRÍTICO: CÓDIGO DE REFERIDOS (st.code) --- */
    /* Caja contenedora: Blanca */
    [data-testid="stCodeBlock"] {
        background-color: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 8px !important;
    }
    [data-testid="stCodeBlock"] pre {
        background-color: #FFFFFF !important;
    }
    /* Texto del código: NEGRO FORZADO */
    [data-testid="stCodeBlock"] code {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        font-weight: bold !important;
    }
    /* SPANS internos del código: NEGRO FORZADO (Sobrescribe la regla global blanca) */
    [data-testid="stCodeBlock"] code span {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
    }
    /* FORZAR COLOR NEGRO A TODO LO INTERNO DEL CODEBLOCK */
    [data-testid="stCodeBlock"] span,
    [data-testid="stCodeBlock"] div,
    [data-testid="stCodeBlock"] pre,
    [data-testid="stCodeBlock"] code {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        opacity: 1 !important;
        text-shadow: none !important;
        filter: none !important;
    }
    /* Botón de copiar y su icono: NEGRO */
    [data-testid="stCodeBlock"] button {
        color: #000000 !important;
    }
    [data-testid="stCodeBlock"] button svg {
        fill: #000000 !important;
        color: #000000 !important;
    }

    /* --- FIX CRÍTICO: DATAFRAME (TABLA) Y BARRA DE HERRAMIENTAS --- */
    div[data-testid="stDataFrame"] div { color: #000000 !important; }
    div[data-testid="stDataFrame"] span { color: #000000 !important; }
    
    /* Iconos de la tabla (3 puntos, lupa, descarga) */
    [data-testid="stElementToolbar"] button {
        color: #000000 !important;
    }
    [data-testid="stElementToolbar"] svg {
        fill: #000000 !important;
        color: #000000 !important;
    }
    
    /* Popups de la tabla */
    div[role="dialog"] div, div[role="menu"] div, div[class*="MuiPaper"] div { color: #000000 !important; }

    /* Etiquetas de Inputs (que se vean grises sobre el azul oscuro) */
    div[data-testid="stTextInput"] label p, 
    div[data-testid="stSelectbox"] label p, 
    div[data-testid="stTextArea"] label p { 
        color: #CBD5E1 !important; 
    }
    div[data-testid="stForm"] label p { 
        color: #0F172A !important; 
    }

    /* --- FIX CARGADOR DE ARCHIVOS (File Uploader) --- */
    div[data-testid="stFileUploader"] section {
        background-color: #FFFFFF !important;
        border: 2px dashed #94A3B8 !important;
    }
    div[data-testid="stFileUploader"] section span,
    div[data-testid="stFileUploader"] section small,
    div[data-testid="stFileUploader"] section div {
        color: #000000 !important;
    }
    div[data-testid="stFileUploader"] section button {
        background-color: #F1F5F9 !important;
        color: #000000 !important;
        border: 1px solid #CBD5E1 !important;
        font-weight: 600 !important;
    }
    
    /* --- UNIFICACIÓN DE BOTONES PRINCIPALES (AZUL CIAN CON TEXTO NEGRO) --- */
    .stButton > button, 
    div[data-testid="stFormSubmitButton"] > button,
    div[data-testid="stLinkButton"] > a { 
        background: linear-gradient(90deg, #0EA5E9 0%, #22D3EE 100%) !important; 
        border: none !important; 
        border-radius: 8px !important; 
        height: 45px !important; 
        width: 100% !important; 
        color: #000000 !important; 
        font-weight: 900 !important; 
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        text-decoration: none !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1) !important;
        transition: all 0.3s ease !important;
    }
    
    /* Texto dentro del Link Button */
    div[data-testid="stLinkButton"] > a > div { color: #000000 !important; }
    
    .stButton > button:hover, 
    div[data-testid="stFormSubmitButton"] > button:hover,
    div[data-testid="stLinkButton"] > a:hover {
        opacity: 0.9 !important;
        transform: scale(1.02) !important;
        color: #000000 !important;
    }

    /* Botones internos de los inputs (ojo contraseña, etc) */
    div[data-testid="stTextInput"] button svg { fill: #000000 !important; stroke: #000000 !important; }
    div[data-testid="stTextInput"] button { border: none !important; background: transparent !important; }
    
    section[data-testid="stSidebar"] { background-color: #020617 !important; border-right: 1px solid #1E293B; }
    
    /* TARJETAS DE PRECIOS */
    .price-card { background-color: #1E293B; padding: 20px; border-radius: 15px; border: 1px solid #334155; text-align: center; margin-bottom: 10px; }
    .price-title { font-size: 18px; font-weight: bold; color: #22D3EE !important; }
    .price-amount { font-size: 28px; font-weight: 800; color: #FFFFFF !important; margin: 10px 0; }
    .price-desc { font-size: 12px; color: #94A3B8 !important; }
</style>
""", unsafe_allow_html=True)

DB_FILE = 'atomo_v15.db' 

# ==========================================
# 🗄️ BASE DE DATOS
# ==========================================
def generar_codigo_ref(nombre):
    base = "".join([c for c in nombre if c.isalnum()]).upper()[:4]
    return f"{base}{random.randint(100, 999)}"

def init_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
        email TEXT PRIMARY KEY, password TEXT, nombre TEXT, nit TEXT, telefono TEXT, 
        firma_digital BLOB, membrete BLOB, rol TEXT DEFAULT 'proveedor', link_pago TEXT, 
        slogan TEXT, direccion TEXT, email_contacto TEXT, color_marca TEXT,
        creditos INTEGER DEFAULT 5, premium_hasta TEXT, codigo_propio TEXT,
        referido_por TEXT, tipo_documento TEXT, foto_documento BLOB, verificado_biometria INTEGER DEFAULT 0
    )''')
    try: c.execute("ALTER TABLE usuarios ADD COLUMN verificado_biometria INTEGER DEFAULT 0"); conn.commit()
    except: pass
    c.execute('''CREATE TABLE IF NOT EXISTS clientes (id INTEGER PRIMARY KEY AUTOINCREMENT, user_email TEXT, nombre_cliente TEXT, nit_cliente TEXT, ciudad_cliente TEXT, email_cliente TEXT, telefono_cliente TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS cuentas_bancarias (id INTEGER PRIMARY KEY AUTOINCREMENT, user_email TEXT, banco TEXT, numero_cuenta TEXT, tipo_cuenta TEXT, bre_b TEXT, qr_imagen BLOB)''')
    c.execute('''CREATE TABLE IF NOT EXISTS facturas (id INTEGER PRIMARY KEY AUTOINCREMENT, user_email TEXT, consecutivo INTEGER, fecha TEXT, cliente_nombre TEXT, cliente_nit TEXT, concepto TEXT, valor_base REAL, val_retefuente REAL, val_reteica REAL, neto_pagar REAL, ciudad TEXT, estado TEXT, fecha_pago TEXT, metodo_pago TEXT, banco_snapshot_id INTEGER, ciudad_ica TEXT)''')
    conn.commit()
    return conn

conn = init_db()
def make_hashes(password): return hashlib.sha256(str.encode(password)).hexdigest()

# ==========================================
# 🛡️ UTILIDADES
# ==========================================
if 'pr' not in st.session_state: st.session_state['pr'] = None
if 'pn' not in st.session_state: st.session_state['pn'] = "Doc.pdf"
if 'ml' not in st.session_state: st.session_state['ml'] = ""

def es_numero(texto): return bool(re.match(r'^\d+$', str(texto))) if texto else False
def get_image_ext(data): return 'png' if data.startswith(b'\x89PNG') else 'jpg'
def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def enviar_codigo_otp(para, codigo):
    if SMTP_EMAIL == "error": return False
    try:
        msg = MIMEMultipart(); msg['From'] = SMTP_EMAIL; msg['To'] = para; msg['Subject'] = f"Código: {codigo}"
        msg.attach(MIMEText(f"Código: {codigo}", 'plain'))
        server = smtplib.SMTP('smtp.gmail.com', 587); server.starttls(); server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.sendmail(SMTP_EMAIL, para, msg.as_string()); server.quit()
        return True
    except: return False

def get_google_auth_url():
    flow = google_auth_oauthlib.flow.Flow.from_client_config(client_config={"web": {"client_id": GOOGLE_CLIENT_ID, "client_secret": GOOGLE_CLIENT_SECRET, "auth_uri": "https://accounts.google.com/o/oauth2/auth", "token_uri": "https://oauth2.googleapis.com/token"}}, scopes=SCOPES, redirect_uri=REDIRECT_URI)
    auth_url, _ = flow.authorization_url(prompt='consent'); return auth_url

def get_google_user_info_and_creds(code):
    try:
        flow = google_auth_oauthlib.flow.Flow.from_client_config(client_config={"web": {"client_id": GOOGLE_CLIENT_ID, "client_secret": GOOGLE_CLIENT_SECRET, "auth_uri": "https://accounts.google.com/o/oauth2/auth", "token_uri": "https://oauth2.googleapis.com/token"}}, scopes=SCOPES, redirect_uri=REDIRECT_URI)
        flow.fetch_token(code=code); return flow.credentials 
    except: return None

def enviar_email_con_gmail(creds, para, asunto, cuerpo, pdf_bytes, nombre_archivo):
    try:
        service = build('gmail', 'v1', credentials=creds)
        message = MIMEMultipart(); message['to'] = para; message['subject'] = asunto
        message.attach(MIMEText(cuerpo, 'plain')); part = MIMEApplication(pdf_bytes, Name=nombre_archivo)
        part['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'; message.attach(part)
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        service.users().messages().send(userId='me', body={'raw': raw}).execute()
        return True
    except Exception as e: st.error(f"Error email: {e}"); return False

# ==========================================
# 📄 MOTOR PDF
# ==========================================
def motor_pdf(usuario, cli_sel, nit_cli, conc, val, rf_val, ica_val, neto, ciudad_emision, id_banco_in, consecutivo, fecha):
    c_fresh = conn.cursor()
    u = c_fresh.execute('SELECT * FROM usuarios WHERE email=?', (usuario,)).fetchone()
    bank = c_fresh.execute('SELECT * FROM cuentas_bancarias WHERE id=?', (id_banco_in,)).fetchone()
    if not bank: return None
    COLOR_HEX = u[12] if len(u) > 12 and u[12] else "#2E86C1"; R, G, B = hex_to_rgb(COLOR_HEX)
    SLOGAN = u[9] if len(u) > 9 and u[9] else ""; DIR = u[10] if len(u) > 10 and u[10] else ""; EMAIL_CONT = u[11] if len(u) > 11 and u[11] else u[0]
    
    pdf = FPDF('P', 'mm', 'A4'); pdf.add_page()
    start_x_logo = 15; target_h_logo = 20; logo_width = 0
    if u[6]:
        ext_l = get_image_ext(u[6]); fname_l = f"logo.{ext_l}"; 
        with open(fname_l, "wb") as f: f.write(u[6])
        try: 
            with Image.open(fname_l) as img_pil:
                w_orig, h_orig = img_pil.size; aspect_ratio = w_orig / h_orig; logo_width = target_h_logo * aspect_ratio
            pdf.image(fname_l, x=start_x_logo, y=12, h=target_h_logo)
        except: pass
    
    text_start_x = start_x_logo + logo_width + 8 if logo_width > 0 else 15
    pdf.set_xy(text_start_x, 15); pdf.set_font("Arial", 'B', 16); pdf.set_text_color(50, 50, 50); pdf.cell(0, 8, u[2].upper(), ln=1)
    if SLOGAN: pdf.set_xy(text_start_x, 22); pdf.set_font("Arial", 'I', 10); pdf.set_text_color(100, 100, 100); pdf.cell(0, 6, SLOGAN, ln=1)
    
    pdf.set_draw_color(R, G, B); pdf.set_line_width(0.5); pdf.line(15, 35, 195, 35)
    pdf.set_xy(100, 38); pdf.set_font("Arial", '', 10); pdf.set_text_color(0, 0, 0); pdf.cell(0, 6, f"Fecha: {fecha} | Ciudad: {ciudad_emision}", align='R', ln=1)
    pdf.ln(10); pdf.set_font("Arial", 'B', 14); pdf.set_text_color(R, G, B); pdf.cell(0, 8, f"CUENTA DE COBRO N° {consecutivo:04d}", ln=1, align='L')
    pdf.set_font("Arial", '', 9); pdf.set_text_color(100, 100, 100); pdf.cell(0, 5, "Documento soporte para no obligados a facturar", ln=1, align='L'); pdf.ln(5)
    
    pdf.set_fill_color(248, 249, 250); pdf.set_draw_color(220, 220, 220); pdf.rect(15, pdf.get_y(), 180, 25, 'FD')
    pdf.set_xy(20, pdf.get_y() + 3); pdf.set_font("Arial", 'B', 10); pdf.set_text_color(0,0,0); pdf.cell(20, 6, "CLIENTE:"); pdf.set_font("Arial", '', 10); pdf.cell(100, 6, cli_sel, ln=1)
    pdf.set_x(20); pdf.set_font("Arial", 'B', 10); pdf.cell(20, 6, "NIT/CC:"); pdf.set_font("Arial", '', 10); pdf.cell(100, 6, nit_cli, ln=1); pdf.ln(15)
    
    pdf.set_font("Arial", 'B', 10); pdf.set_text_color(255, 255, 255); pdf.set_fill_color(R, G, B)
    pdf.cell(130, 8, "Descripción del Servicio", 1, 0, 'L', 1); pdf.cell(50, 8, "Valor Total", 1, 1, 'R', 1)
    pdf.set_font("Arial", '', 10); pdf.set_text_color(0, 0, 0); pdf.multi_cell(130, 8, conc, 1)
    y_curr = pdf.get_y(); pdf.set_xy(145, y_curr - 8); pdf.cell(50, 8, f"${val:,.0f}", 1, 1, 'R'); pdf.ln(5)
    if rf_val > 0: pdf.set_x(100); pdf.cell(45, 6, "Retención Fuente (-)", 0, 0, 'R'); pdf.cell(50, 6, f"${rf_val:,.0f}", 1, 1, 'R')
    if ica_val > 0: pdf.set_x(100); pdf.cell(45, 6, f"ReteICA (-)", 0, 0, 'R'); pdf.cell(50, 6, f"${ica_val:,.0f}", 1, 1, 'R')
    pdf.set_font("Arial", 'B', 12); pdf.set_text_color(R, G, B); pdf.set_x(100); pdf.cell(45, 10, "NETO A PAGAR", 0, 0, 'R'); pdf.cell(50, 10, f"${neto:,.0f}", 1, 1, 'R'); pdf.ln(10)
    
    pdf.set_font("Arial", 'B', 10); pdf.set_text_color(0, 0, 0); pdf.cell(0, 6, "DATOS PARA PAGO:", ln=1); pdf.set_font("Arial", '', 10)
    txt_banco = f"Banco: {bank[2]}\nTipo: {bank[4]}\nNo. Cuenta: {bank[3]}"
    if bank[5]: txt_banco += f"\nLlave Bre-B: {bank[5]}"
    y_qr = pdf.get_y(); pdf.multi_cell(100, 5, txt_banco)
    if bank[6]:
        ext_q = get_image_ext(bank[6]); fname_q = f"tqr.{ext_q}"; 
        with open(fname_q, "wb") as f: f.write(bank[6])
        try: pdf.image(fname_q, x=130, y=y_qr, w=30); pdf.set_xy(130, y_qr+31); pdf.cell(30, 5, "Escanear", align='C')
        except: pass
    pdf.set_auto_page_break(False); Y_FIRMA = 225
    if u[5]:
        ext_f = get_image_ext(u[5]); fname_f = f"tsig.{ext_f}"; 
        with open(fname_f, "wb") as f: f.write(u[5])
        try: pdf.image(fname_f, x=25, y=Y_FIRMA-15, w=35) 
        except: pass
    pdf.set_draw_color(0,0,0); pdf.line(20, Y_FIRMA, 80, Y_FIRMA); pdf.set_xy(20, Y_FIRMA+2); pdf.cell(60, 5, "Firma Autorizada", align='C')
    pdf.set_xy(20, Y_FIRMA+7); pdf.set_font("Arial",'',8); pdf.cell(60, 5, f"CC/NIT: {u[3]}", align='C')
    Y_FOOTER = 265; pdf.set_draw_color(R, G, B); pdf.set_line_width(0.5); pdf.line(15, Y_FOOTER, 195, Y_FOOTER)
    pdf.set_xy(15, Y_FOOTER + 2); pdf.set_font("Arial", '', 8); pdf.set_text_color(100, 100, 100); footer_txt = f"Dirección: {DIR}  |  Teléfono: {u[4]}  |  Email: {EMAIL_CONT}"
    pdf.cell(0, 5, footer_txt, align='C'); pdf.set_display_mode('fullpage', 'single')
    return pdf.output(dest='S').encode('latin-1')

# ==========================================
# 🚀 APP
# ==========================================
if 'usuario_activo' not in st.session_state: st.session_state['usuario_activo'] = None
if 'registro_paso' not in st.session_state: st.session_state['registro_paso'] = 1
if 'temp_reg_data' not in st.session_state: st.session_state['temp_reg_data'] = {}

ref_from_url = st.query_params.get("ref", "")

# 🔔 DETECCIÓN DE PAGO AUTOMÁTICO (Wompi/MercadoPago Redirección)
# Si la URL tiene ?plan=...&status=approved, activamos el plan
if st.session_state['usuario_activo'] and "status" in st.query_params:
    status = st.query_params["status"]
    plan_comprado = st.query_params.get("plan", "Desconocido")
    
    if status == "approved":
        # Calcular días
        dias = 7
        if plan_comprado == "Mensual": dias = 30
        elif plan_comprado == "Trimestral": dias = 90
        elif plan_comprado == "Semestral": dias = 180
        elif plan_comprado == "Anual": dias = 365
        
        # Activar en DB
        new_date = (datetime.now() + timedelta(days=dias)).strftime('%Y-%m-%d')
        c = conn.cursor()
        c.execute("UPDATE usuarios SET premium_hasta=? WHERE email=?", (new_date, st.session_state['usuario_activo']))
        conn.commit()
        
        st.balloons()
        st.toast(f"✅ ¡Pago Exitoso! Plan {plan_comprado} activado.", icon="💎")
        # Limpiar URL para que no se reactive al refrescar
        st.query_params.clear()
        time.sleep(2)
        st.rerun()

if "code" in st.query_params and st.session_state['usuario_activo'] is None:
    creds = get_google_user_info_and_creds(st.query_params["code"])
    if creds:
        user_info = build('oauth2', 'v2', credentials=creds).userinfo().get().execute()
        email = user_info['email']; name = user_info.get('name', 'Usuario')
        c = conn.cursor(); c.execute('SELECT * FROM usuarios WHERE email =?', (email,))
        if not c.fetchone(): 
            new_code = generar_codigo_ref(name)
            c.execute('INSERT INTO usuarios (email, password, nombre, rol, creditos, codigo_propio) VALUES (?,?,?,?,?,?)', (email, "GOOGLE", name, "proveedor", 5, new_code)); conn.commit()
        st.session_state['usuario_activo'] = email; st.session_state['google_creds'] = creds; st.query_params.clear(); st.rerun()

if st.session_state['usuario_activo'] is None:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        try: st.image("logo_nuevo.png", use_container_width=True)
        except: st.markdown("<h1 style='text-align: center; color: white;'>Átomo</h1>", unsafe_allow_html=True)
        t_log, t_reg = st.tabs(["INICIAR SESIÓN", "REGISTRARSE"])
        with t_log:
            st.markdown("<br>", unsafe_allow_html=True)
            if GOOGLE_CLIENT_ID != "error":
                url = get_google_auth_url()
                google_icon_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/><path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/><path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/><path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/><path fill="none" d="M0 0h48v48H0z"/></svg>"""
                b64_icon = base64.b64encode(google_icon_svg.encode('utf-8')).decode('utf-8')
                st.markdown(f'''<div style="text-align: center; margin-bottom: 25px;"><a href="{url}" target="_self" style="text-decoration:none;"><button style="background-color: #ffffff; border: 1px solid #dadce0; border-radius: 4px; color: #3c4043; font-family: 'Roboto', arial, sans-serif; font-size: 14px; font-weight: 500; height: 40px; width: 100%; display: flex; align-items: center; justify-content: center; cursor: pointer; gap: 10px; transition: background-color .2s; box-shadow: 0 1px 3px rgba(0,0,0,0.08);" onmouseover="this.style.backgroundColor='#f7faff'" onmouseout="this.style.backgroundColor='#ffffff'"><img src="data:image/svg+xml;base64,{b64_icon}" width="18" height="18">Ingresar con Google</button></a></div>''', unsafe_allow_html=True)
                st.markdown("<div style='text-align:center; color: #FFFFFF; margin: 15px 0; font-size: 14px;'>— O CON TU CORREO ELECTRÓNICO —</div>", unsafe_allow_html=True)
            
            le = st.text_input("Correo Electrónico", key="le")
            lp = st.text_input("Contraseña", type="password", key="lp")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("ACCEDER A MI CUENTA", type="primary"):
                c = conn.cursor(); u = c.execute('SELECT * FROM usuarios WHERE email=? AND password=?', (le.lower().strip(), make_hashes(lp))).fetchone()
                if u: st.session_state['usuario_activo'] = u[0]; st.rerun()
                else: st.error("Credenciales incorrectas")
        
        with t_reg:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.session_state['registro_paso'] == 1:
                rn = st.text_input("Nombre Completo")
                tipo_doc_opts = ["Cédula de Ciudadanía", "NIT", "Tarjeta de Identidad", "Pasaporte", "Cédula de Extranjería"]
                r_td = st.selectbox("Tipo de Identificación", tipo_doc_opts)
                r_nit = st.text_input("Número de Documento (Sin puntos ni guiones)")
                re = st.text_input("Tu Correo"); rp = st.text_input("Define tu Contraseña", type="password")
                ref_code = st.text_input("¿Tienes un código de referido?", value=ref_from_url)
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("ENVIAR CÓDIGO"):
                    if not rn or not r_nit or not re or not rp: st.error("⚠️ Todos los campos son obligatorios."); st.stop()
                    if not es_numero(r_nit): st.error("⚠️ El número de documento debe contener solo números."); st.stop()
                    c = conn.cursor()
                    if c.execute("SELECT email FROM usuarios WHERE nit=?", (r_nit,)).fetchone(): st.error(f"⚠️ Este documento ({r_nit}) ya está registrado."); st.stop()
                    if c.execute("SELECT email FROM usuarios WHERE email=?", (re.lower().strip(),)).fetchone(): st.error("⚠️ Este correo ya está registrado."); st.stop()
                    otp = str(random.randint(100000, 999999))
                    st.session_state['temp_reg_data'] = {'n':rn, 'e':re.lower().strip(), 'p':make_hashes(rp), 'otp':otp, 'ref':ref_code, 'td': r_td, 'nid': r_nit}
                    if enviar_codigo_otp(re, otp): st.session_state['registro_paso'] = 2; st.rerun()
                    else: st.error("Error al enviar el correo. Revisa SMTP.")
            elif st.session_state['registro_paso'] == 2:
                st.info(f"Revisa tu correo {st.session_state['temp_reg_data']['e']}")
                otp_in = st.text_input("Ingresa el código de 6 dígitos")
                if st.button("VERIFICAR Y CREAR"):
                    if otp_in == st.session_state['temp_reg_data']['otp']:
                        d = st.session_state['temp_reg_data']
                        mi_nuevo_codigo = generar_codigo_ref(d['n']); creditos_iniciales = 5; padrino = d['ref'].strip()
                        if padrino:
                            c = conn.cursor(); p = c.execute("SELECT email, creditos FROM usuarios WHERE codigo_propio=?", (padrino,)).fetchone()
                            if p: c.execute("UPDATE usuarios SET creditos=? WHERE email=?", ((p[1] if p[1] else 0) + 5, p[0]))
                        c = conn.cursor()
                        c.execute('''INSERT INTO usuarios (email, password, nombre, rol, creditos, codigo_propio, referido_por, tipo_documento, nit) VALUES (?,?,?,?,?,?,?,?,?)''', (d['e'], d['p'], d['n'], 'proveedor', creditos_iniciales, mi_nuevo_codigo, padrino, d['td'], d['nid']))
                        conn.commit()
                        st.success("¡Bienvenido a Átomo! Registro exitoso."); st.session_state['registro_paso'] = 1
                    else: st.error("Código incorrecto.")
else:
    usuario = st.session_state['usuario_activo']
    c = conn.cursor(); u_data = c.execute('SELECT * FROM usuarios WHERE email=?', (usuario,)).fetchone()
    
    with st.sidebar:
        if u_data[6]:
            try: st.image(u_data[6], use_container_width=True)
            except: pass
        else:
            try: st.image("logo_nuevo.png", use_container_width=True)
            except: st.markdown("<h2 style='color:#22D3EE;'>Átomo.co</h2>", unsafe_allow_html=True)
        st.markdown(f"<div style='margin-bottom: 20px; color: #CBD5E1;'>Hola, <b style='color:#FFFFFF; font-size:18px;'>{u_data[2].split()[0]}</b></div>", unsafe_allow_html=True)
        
        premium_hasta = u_data[14]
        es_premium = False
        if premium_hasta:
            try:
                if datetime.strptime(premium_hasta, '%Y-%m-%d') >= datetime.now(): es_premium = True
            except: pass
            
        if es_premium: st.success(f"💎 PREMIUM\nVence: {premium_hasta}")
        else: st.info(f"⚡ Créditos: {u_data[13]}")
        st.markdown("---")
        
        # ⚠️ ADMIN
        ADMIN_EMAIL = "atomoapp.co@gmail.com" 
        
        opciones_menu = ["📊 Panel de Control", "🗂️ Historial", "👥 Clientes", "📝 Facturar", "⚙️ Mi Perfil", "📞 Soporte"]
        if usuario == ADMIN_EMAIL: opciones_menu.append("🔧 ADMINISTRADOR")
        menu = st.radio("Navegación", opciones_menu)
        st.markdown("---")
        if st.button("Cerrar Sesión"): st.session_state['usuario_activo'] = None; st.rerun()

    if menu == "⚙️ Mi Perfil":
        st.title("⚙️ Configuración")
        t1, t2, t3, t4, t5, t6 = st.tabs(["MARCA", "DATOS", "BANCOS", "💎 SUSCRIPCIÓN", "🎁 REFERIDOS", "🔐 VERIFICACIÓN"])
        
        with t1:
            st.markdown("#### 🎨 Personalización")
            with st.form("estilo"):
                c1, c2 = st.columns(2)
                with c1: c_marca = st.color_picker("Color Principal", u_data[12] if len(u_data)>12 and u_data[12] else "#2E86C1")
                with c2: slogan = st.text_input("Eslogan de tu negocio", u_data[9] if len(u_data)>9 and u_data[9] else "")
                logo_up = st.file_uploader("Logo (PNG/JPG)", type=['png','jpg','jpeg'])
                if st.form_submit_button("Guardar Cambios"):
                    q = "UPDATE usuarios SET color_marca=?, slogan=?"; p = [c_marca, slogan]
                    if logo_up: q+=", membrete=?"; p.append(logo_up.getvalue())
                    q+=" WHERE email=?"; p.append(usuario)
                    c.execute(q, tuple(p)); conn.commit(); st.success("Estilo Actualizado"); st.rerun()
            if u_data[6]: st.image(u_data[6], width=150)
        
        with t2:
            st.markdown("#### 📝 Información Legal")
            with st.form("datos"):
                c1, c2 = st.columns(2)
                with c1: n = st.text_input("Razón Social / Nombre", u_data[2]); ni = st.text_input("NIT / Documento", u_data[3]) 
                with c2: tl = st.text_input("Celular", u_data[4]); em = st.text_input("Email Público", u_data[11] if len(u_data)>11 and u_data[11] else u_data[0])
                di = st.text_input("Dirección", u_data[10] if len(u_data)>10 and u_data[10] else ""); firma_up = st.file_uploader("Firma Digital (Imagen)", type=['png','jpg'])
                if st.form_submit_button("Actualizar Datos"):
                    q = "UPDATE usuarios SET nombre=?, nit=?, telefono=?, direccion=?, email_contacto=?"; p = [n, ni, tl, di, em]
                    if firma_up: q+=", firma_digital=?"; p.append(firma_up.getvalue())
                    q+=" WHERE email=?"; p.append(usuario)
                    c.execute(q, tuple(p)); conn.commit(); st.success("Datos Guardados"); st.rerun()
        
        with t3:
            st.markdown("#### 🏦 Cuentas Bancarias")
            with st.form("bk"):
                c1, c2 = st.columns(2)
                with c1: b = st.text_input("Banco"); nm = st.text_input("Número de Cuenta")
                with c2: t = st.selectbox("Tipo", ["Ahorros", "Corriente"]); br = st.text_input("Llave Bre-B (Opcional)")
                qr = st.file_uploader("Código QR (Imagen)", type=['png','jpg'])
                if st.form_submit_button("Agregar Nueva Cuenta"):
                    if not es_numero(nm): st.error("⚠️ Error: Número de cuenta inválido."); st.stop()
                    qrb = qr.getvalue() if qr else None
                    c.execute("INSERT INTO cuentas_bancarias (user_email, banco, numero_cuenta, tipo_cuenta, bre_b, qr_imagen) VALUES (?,?,?,?,?,?)", (usuario, b, nm, t, br, qrb)); conn.commit(); st.rerun()
            st.markdown("---")
            bks = pd.read_sql_query(f"SELECT id, banco, numero_cuenta FROM cuentas_bancarias WHERE user_email='{usuario}'", conn)
            for i, r in bks.iterrows():
                with st.expander(f"{r['banco']} - {r['numero_cuenta']}"):
                    if st.button("Eliminar", key=f"del_{r['id']}"): c.execute("DELETE FROM cuentas_bancarias WHERE id=?", (r['id'],)); conn.commit(); st.rerun()

        with t4:
            st.markdown("### 💎 Planes de Suscripción")
            st.info("Suscríbete para tener uso **ILIMITADO**.")
            
            # LINKS REALES (CONFIGURA ESTO EN TU PASARELA)
            # URL DE RETORNO EN PASARELA DEBE SER: http://localhost:8501/?status=approved&plan=Semanal (Ejemplo)
            
            # SIMULADOR (Para que lo pruebes YA)
            def tarjeta_precio(titulo, precio, desc, link_pago):
                st.markdown(f"""<div class="price-card"><div class="price-title">{titulo}</div><div class="price-amount">${precio}</div><div class="price-desc">{desc}</div></div>""", unsafe_allow_html=True)
                # ENLACE REAL
                st.link_button(f"Pagar {titulo}", link_pago)

            # TUS LINKS REALES DE MERCADO PAGO:
            LINK_SEMANAL = "https://mpago.li/2ZAwZMe"
            LINK_MENSUAL = "https://mpago.li/1zKwouG"
            LINK_TRIMESTRAL = "https://mpago.li/1D94kdu"
            LINK_SEMESTRAL = "https://mpago.li/1ysMpvK"
            LINK_ANUAL = "https://mpago.li/324S4jg"

            p1, p2, p3 = st.columns(3)
            with p1: tarjeta_precio("SEMANAL", "8.000", "Acceso 7 días", LINK_SEMANAL)
            with p2: tarjeta_precio("MENSUAL", "20.000", "Acceso 30 días", LINK_MENSUAL)
            with p3: tarjeta_precio("TRIMESTRAL", "50.000", "Acceso 90 días", LINK_TRIMESTRAL)
            p4, p5 = st.columns(2)
            with p4: tarjeta_precio("SEMESTRAL", "93.000", "Acceso 180 días", LINK_SEMESTRAL)
            with p5: tarjeta_precio("ANUAL", "156.000", "Acceso 365 días", LINK_ANUAL)
            
            st.markdown("---")
            st.caption("🔒 Pagos seguros. Activación automática inmediata.")

        with t5:
            st.markdown("#### 🎁 Gana Créditos Gratis")
            st.info("Invita amigos. Cuando se registren, ambos ganan **5 créditos**.")
            mi_codigo = u_data[15] if len(u_data)>15 else "ERROR"; base_url = "http://localhost:8501"; link_ref = f"{base_url}/?ref={mi_codigo}"
            st.code(link_ref, language="text"); st.divider(); st.markdown("##### 👥 Tus Referidos")
            refs = c.execute("SELECT nombre FROM usuarios WHERE referido_por=?", (mi_codigo,)).fetchall()
            if refs:
                for r in refs: st.success(f"👤 {r[0]}")
            else: st.warning("Aún no tienes referidos.")

        with t6:
            st.markdown("#### 🔐 Verificación de Identidad")
            try: estado_bio = c.execute("SELECT verificado_biometria FROM usuarios WHERE email=?", (usuario,)).fetchone()
            except: estado_bio = None
            es_verificado = estado_bio[0] if estado_bio else 0
            
            if es_verificado == 1: st.success("✅ ¡Tu identidad ya está verificada!"); st.balloons()
            else:
                st.info("💡 Verifica tu cuenta para evitar bloqueos si se acaban tus créditos.")
                col_vol1, col_vol2 = st.columns(2)
                with col_vol1: foto_doc_vol = st.file_uploader("1. Documento (Cédula/NIT)", type=['jpg','png','jpeg'], key="doc_vol")
                with col_vol2: foto_selfie_vol = st.camera_input("2. Selfie", key="selfie_vol")
                if st.button("Validar Identidad Ahora"):
                    if foto_doc_vol and foto_selfie_vol:
                        with st.spinner("Verificando..."):
                            exito, msg = comparar_rostros(foto_doc_vol.getvalue(), foto_selfie_vol.getvalue())
                            if exito:
                                c.execute("UPDATE usuarios SET verificado_biometria=1 WHERE email=?", (usuario,)); conn.commit(); st.success(msg); st.rerun()
                            else: st.error(msg)
                    else: st.warning("Faltan fotos.")

    elif menu == "🗂️ Historial":
        st.title("🗂️ Historial")
        hist = pd.read_sql_query(f"SELECT * FROM facturas WHERE user_email='{usuario}' ORDER BY consecutivo DESC", conn)
        if hist.empty: st.info("No tienes cuentas de cobro generadas.")
        else:
            for i, row in hist.iterrows():
                st_color = "#44E5E7" if row['estado']=='Pagada' else "#FACC15" if row['estado']=='Pendiente' else "#F87171"
                with st.expander(f"#{row['consecutivo']} — {row['cliente_nombre']} (${row['neto_pagar']:,.0f})"):
                    c1, c2 = st.columns([2, 1])
                    with c1: st.markdown(f"**Estado:** <span style='color:{st_color}; font-weight:bold;'>{row['estado']}</span>", unsafe_allow_html=True); st.write(f"📅 Fecha: {row['fecha']}"); st.write(f"📝 Concepto: {row['concepto'][:50]}...")
                    with c2:
                        if st.button("📄 Generar PDF", key=f"btn_{row['id']}"):
                            pdf_r = motor_pdf(usuario, row['cliente_nombre'], row['cliente_nit'], row['concepto'], row['valor_base'], row['val_retefuente'], row['val_reteica'], row['neto_pagar'], row['ciudad'], row['banco_snapshot_id'], row['consecutivo'], row['fecha'])
                            st.session_state[f'pdf_{row["id"]}'] = pdf_r
                            c_mail = c.execute("SELECT email_cliente FROM clientes WHERE nit_cliente=?", (row['cliente_nit'],)).fetchone()
                            st.session_state[f'mail_{row["id"]}'] = c_mail[0] if c_mail else ""
                        if f'pdf_{row["id"]}' in st.session_state:
                            col_d, col_e = st.columns(2); col_d.download_button("📥 Bajar", st.session_state[f'pdf_{row["id"]}'], f"Factura_{row['consecutivo']}.pdf", mime="application/pdf", key=f"dl_{row['id']}")
                            if col_e.button("📧 Enviar", key=f"em_{row['id']}"):
                                if enviar_email_con_gmail(st.session_state['google_creds'], st.session_state[f'mail_{row["id"]}'], f"Cuenta de Cobro #{row['consecutivo']}", "Hola, adjunto documento soporte.", st.session_state[f'pdf_{row["id"]}'], f"Factura_{row['consecutivo']}.pdf"): st.success("Enviado")
                                else: st.error("Error envío")

    elif menu == "👥 Clientes":
        st.title("👥 Clientes")
        with st.expander("➕ Nuevo Cliente", expanded=True):
            with st.form("cl"):
                c1, c2 = st.columns(2)
                with c1: n = st.text_input("Nombre"); ni = st.text_input("NIT/CC"); ci = st.text_input("Ciudad")
                with c2: em = st.text_input("Email"); tel = st.text_input("Celular")
                if st.form_submit_button("Guardar Cliente"): 
                    if not es_numero(ni) or not es_numero(tel): st.error("⚠️ Solo números en NIT y Teléfono"); st.stop()
                    dup = c.execute("SELECT * FROM clientes WHERE user_email=? AND nit_cliente=?", (usuario, ni)).fetchone()
                    if dup: st.error(f"⚠️ El cliente {ni} ya existe."); st.stop()
                    c.execute("INSERT INTO clientes (user_email, nombre_cliente, nit_cliente, ciudad_cliente, email_cliente, telefono_cliente) VALUES (?,?,?,?,?,?)", (usuario, n, ni, ci, em, tel)); conn.commit(); st.rerun()
        st.markdown("<br>", unsafe_allow_html=True)
        st.dataframe(pd.read_sql_query(f"SELECT nombre_cliente as Cliente, nit_cliente as NIT, telefono_cliente as Telefono FROM clientes WHERE user_email='{usuario}'", conn), hide_index=True, use_container_width=True)

    elif menu == "📝 Facturar":
        st.title("📝 Nueva Cuenta")
        c = conn.cursor()
        try: data_user = c.execute("SELECT creditos, verificado_biometria, premium_hasta FROM usuarios WHERE email=?", (usuario,)).fetchone()
        except:
            c.execute("ALTER TABLE usuarios ADD COLUMN verificado_biometria INTEGER DEFAULT 0"); conn.commit()
            data_user = c.execute("SELECT creditos, verificado_biometria, premium_hasta FROM usuarios WHERE email=?", (usuario,)).fetchone()

        creditos = data_user[0] if data_user else 0
        verificado = data_user[1] if data_user else 0
        premium_date = data_user[2] if data_user else None
        es_premium = False
        if premium_date:
            try: 
                if datetime.strptime(premium_date, '%Y-%m-%d') >= datetime.now(): es_premium = True
            except: pass

        if es_premium or creditos > 0:
            if es_premium: st.success("💎 Eres Premium. Uso ilimitado.")
            else: st.info(f"⚡ Tienes **{creditos}** créditos disponibles.")
            
            cls = pd.read_sql_query(f"SELECT * FROM clientes WHERE user_email='{usuario}'", conn)
            bks = pd.read_sql_query(f"SELECT * FROM cuentas_bancarias WHERE user_email='{usuario}'", conn)
            if cls.empty or bks.empty: st.warning("⚠️ Primero configura clientes y bancos."); st.stop()
            
            c.execute(f"SELECT MAX(consecutivo) FROM facturas WHERE user_email='{usuario}'"); last = c.fetchone()[0]; prox = 1 if last is None else last + 1
            c1, c2 = st.columns([2,1])
            with c1:
                st.markdown("##### Información del Servicio")
                cli = st.selectbox("Cliente", cls['nombre_cliente']); cli_o = cls[cls['nombre_cliente']==cli].iloc[0]
                ciudad_emision = st.text_input("Ciudad Emisión", value=cli_o['ciudad_cliente'])
                conc = st.text_area("Descripción detallada", height=100); val = st.number_input("Valor Base ($)", step=50000)
            with c2:
                st.markdown(f"##### Documento #{prox}")
                bk_s = st.selectbox("Banco Destino", bks.apply(lambda x: f"{x['id']} - {x['banco']}", axis=1)); bid = int(bk_s.split(' - ')[0])
                st.markdown("##### Impuestos")
                rf = st.checkbox("Retención en la Fuente", True); rf_v = val*0.1 if rf else 0
                if rf:
                    trf = st.selectbox("Tarifa", ["Honorarios (10%)", "Honorarios Declarante (11%)", "Servicios (4%)", "Servicios Declarante (6%)", "Arrendamiento (3.5%)"])
                    tasa = 0.10; rf_v = val*tasa
                ica = st.checkbox("ReteICA"); ica_v=0; cica="N/A"
                if ica: cica=st.text_input("Ciudad ICA", cli_o['ciudad_cliente']); tica=st.number_input("Tarifa (x1000)", 9.66); ica_v=(val*tica)/1000
                neto = val-rf_v-ica_v; st.divider(); st.metric("TOTAL A COBRAR", f"${neto:,.0f}")

            if st.button("⚡ GENERAR DOCUMENTO"):
                if not es_premium: c.execute("UPDATE usuarios SET creditos = creditos - 1 WHERE email=?", (usuario,))
                c.execute("INSERT INTO facturas (user_email, consecutivo, fecha, cliente_nombre, cliente_nit, concepto, valor_base, val_retefuente, val_reteica, neto_pagar, estado, banco_snapshot_id, ciudad_ica, ciudad) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (usuario, prox, datetime.now().strftime('%Y-%m-%d'), cli, cli_o['nit_cliente'], conc, val, rf_v, ica_v, neto, "Pendiente", bid, cica, ciudad_emision)); conn.commit()
                p = motor_pdf(usuario, cli, cli_o['nit_cliente'], conc, val, rf_v, ica_v, neto, ciudad_emision, bid, prox, datetime.now().strftime('%Y-%m-%d'))
                st.session_state['pr'] = p; st.session_state['pn'] = f"Cuenta_{prox}.pdf"; st.session_state['ml'] = cli_o['email_cliente']; st.success("¡Creado con éxito!"); st.rerun()

            if st.session_state['pr']:
                c1, c2 = st.columns(2); c1.download_button("📥 Descargar", st.session_state['pr'], st.session_state['pn'], mime="application/pdf")
                if c2.button("📧 Enviar Email"):
                    if enviar_email_con_gmail(st.session_state['google_creds'], st.session_state['ml'], f"Cuenta de Cobro #{prox}", "Hola, adjunto soporte de pago.", st.session_state['pr'], "Cuenta.pdf"): st.success("Correo enviado")

        else:
            if verificado == 1:
                st.error("🚫 Se han agotado tus créditos gratuitos.")
                st.info("💎 Como ya verificaste tu identidad, puedes activar un plan ILIMITADO en **Mi Perfil > 💎 Suscripción**.")
            else:
                st.error("🚫 Tus créditos gratuitos se han agotado.")
                st.warning("🔒 Para continuar, verifica tu identidad.")
                col_bio1, col_bio2 = st.columns(2)
                with col_bio1: foto_doc = st.file_uploader("Sube foto de tu Cédula/NIT", type=['jpg','png','jpeg'])
                with col_bio2: foto_selfie = st.camera_input("Tómate una foto ahora")
                if st.button("🔍 Validar Identidad"):
                    if foto_doc and foto_selfie:
                        with st.spinner("Analizando..."):
                            exito, mensaje = comparar_rostros(foto_doc.getvalue(), foto_selfie.getvalue())
                            if exito:
                                st.balloons(); st.success("✅ Verificado. +1 Crédito gratis.")
                                c.execute("UPDATE usuarios SET verificado_biometria=1, creditos=1 WHERE email=?", (usuario,)); conn.commit(); st.rerun()
                            else: st.error(mensaje)
                    else: st.warning("⚠️ Faltan fotos.")

    elif menu == "📊 Panel de Control":
        st.title("📊 Panel Financiero")
        df = pd.read_sql_query(f"SELECT * FROM facturas WHERE user_email='{usuario}' ORDER BY consecutivo DESC", conn)
        if not df.empty:
            df_ok = df[df['estado']!='Anulada']
            total = df_ok['neto_pagar'].sum()
            pagado = df_ok[df_ok['estado'] == 'Pagada']['neto_pagar'].sum()
            pendiente = total - pagado
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Emitido", f"${total:,.0f}"); k2.metric("Cobrado", f"${pagado:,.0f}"); k3.metric("Pendiente", f"${pendiente:,.0f}"); k4.metric("Utilidad", f"${pagado:,.0f}")
            st.markdown("---"); c1, c2 = st.columns([3, 1])
            with c1: st.subheader("Últimos Movimientos"); st.dataframe(df[['consecutivo','cliente_nombre','neto_pagar','estado']], hide_index=True, use_container_width=True)
            with c2:
                st.subheader("Acciones")
                lista_fac = df.apply(lambda x: f"#{x['consecutivo']} - {x['cliente_nombre']}", axis=1)
                fac_elegida = st.selectbox("Factura", lista_fac)
                nuevo_est = st.selectbox("Estado", ["Pagada", "Pendiente", "Anulada"])
                if st.button("Actualizar"):
                    id_fac = df.iloc[lista_fac[lista_fac == fac_elegida].index[0]]['id']
                    c.execute("UPDATE facturas SET estado=? WHERE id=?", (nuevo_est, int(id_fac))); conn.commit(); st.success("Ok"); st.rerun()
        else: st.info("No hay datos financieros aún.")
        
    # ==========================
    # 🔧 PANEL ADMINISTRADOR
    # ==========================
    elif menu == "🔧 ADMINISTRADOR":
        st.title("🔧 Panel de Administrador")
        st.write("Gestiona las suscripciones manualmente.")
        email_buscar = st.text_input("Buscar usuario por correo:")
        if email_buscar:
            c = conn.cursor()
            user_found = c.execute("SELECT nombre, creditos, premium_hasta FROM usuarios WHERE email=?", (email_buscar,)).fetchone()
            if user_found:
                st.success(f"Usuario: {user_found[0]} | Créditos: {user_found[1]} | Vence: {user_found[2]}")
                st.markdown("---"); st.subheader("Activar Plan Manualmente")
                plan_activar = st.selectbox("Seleccionar Plan", ["Semanal (7 días)", "Mensual (30 días)", "Trimestral (90 días)", "Semestral (180 días)", "Anual (365 días)"])
                if st.button("✅ Activar Plan"):
                    dias = 7
                    if "Mensual" in plan_activar: dias = 30
                    if "Trimestral" in plan_activar: dias = 90
                    if "Semestral" in plan_activar: dias = 180
                    if "Anual" in plan_activar: dias = 365
                    nueva_fecha = (datetime.now() + timedelta(days=dias)).strftime('%Y-%m-%d')
                    c.execute("UPDATE usuarios SET premium_hasta=? WHERE email=?", (nueva_fecha, email_buscar)); conn.commit(); st.success(f"Plan activado hasta: {nueva_fecha}")
            else: st.error("Usuario no encontrado.")

    # ==========================
    # 📞 SOPORTE (NUEVO)
    # ==========================
    elif menu == "📞 Soporte":
        st.title("📞 Centro de Soporte")
        st.markdown("¿Tienes dudas o problemas? Estamos aquí para ayudarte.")

        c1, c2 = st.columns([1, 1])

        with c1:
            st.subheader("📩 Envíanos un mensaje")
            with st.form("contact_form"):
                asunto = st.selectbox("Motivo", ["Soporte Técnico", "Pagos y Suscripción", "Reportar Error", "Otro"])
                mensaje = st.text_area("Detalle de tu solicitud")
                # El botón de envío ahora tendrá el diseño cian correcto con letras negras
                enviar = st.form_submit_button("Enviar Mensaje")
                if enviar:
                    cuerpo = f"Usuario: {usuario}\nMotivo: {asunto}\n\nMensaje:\n{mensaje}"
                    msg = MIMEMultipart()
                    msg['From'] = SMTP_EMAIL
                    msg['To'] = "atomoapp.co@gmail.com" 
                    msg['Subject'] = f"Soporte Átomo: {asunto}"
                    msg.attach(MIMEText(cuerpo, 'plain'))
                    try:
                        server = smtplib.SMTP('smtp.gmail.com', 587)
                        server.starttls()
                        server.login(SMTP_EMAIL, SMTP_PASSWORD)
                        server.sendmail(SMTP_EMAIL, "atomoapp.co@gmail.com", msg.as_string())
                        server.quit()
                        st.success("✅ Mensaje enviado. Te responderemos pronto.")
                    except:
                        st.error("Error enviando mensaje. Escríbenos por WhatsApp.")

        with c2:
            st.subheader("💬 Chat en Vivo")
            st.info("Para una atención inmediata, escríbenos a WhatsApp.")
            # El botón de enlace ahora tendrá el diseño cian correcto con letras negras
            st.link_button("📲 Abrir WhatsApp", "https://wa.me/573000000000")

            st.markdown("---")
            st.subheader("❓ Preguntas Frecuentes")
            with st.expander("¿Cómo activo mi plan después de pagar?"):
                st.write("El sistema lo activa automáticamente al finalizar el pago en Mercado Pago. Si no se activa, envíanos el comprobante por WhatsApp.")
            with st.expander("¿Cómo funcionan los créditos gratuitos?"):
                st.write("Tienes 5 créditos al registrarte. Cada documento generado gasta 1 crédito. Si invitas amigos, ganas más.")
