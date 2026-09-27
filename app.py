import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import io
from streamlit_gsheets import GSheetsConnection

# Configuración inicial de la página
st.set_page_config(page_title="Gestión Climatización", page_icon="❄️", layout="wide")

st.title("❄️ Sistema de Gestión - Servicio Técnico & Climatización")

LOGO_FILE = "logo.png"

# Conexión a Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Función para cargar datos de Google Sheets
def cargar_datos():
    try:
        df = conn.read(ttl=0)
        df = df.dropna(how="all")
        return df
    except Exception as e:
        return pd.DataFrame(columns=[
            "ID", "Nombre", "Telefono", "Direccion", 
            "Marca_Equipo", "Modelo", "Frigorias", "Tipo_Gas", 
            "Ultimo_Servicio", "Proximo_Mantenimiento", "Notas"
        ])

# Función para guardar datos en Google Sheets
def guardar_datos(df):
    conn.update(data=df)
    st.cache_data.clear()

# Función para generar el presupuesto en PDF personalizado
def generar_pdf_presupuesto(empresa_nombre, empresa_contacto, cliente_nombre, cliente_tel, cliente_dir, items, notas, total):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []
    styles = getSampleStyleSheet()

    # Estilos
    style_empresa = ParagraphStyle('Empresa', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor("#003366"))
    style_sub = ParagraphStyle('Sub', parent=styles['Normal'], fontSize=9, textColor=colors.gray)
    style_body = ParagraphStyle('Body', parent=styles['Normal'], fontSize=10, leading=14)

    # Cabecera con Logo y Datos de la Empresa
    if os.path.exists(LOGO_FILE):
        try:
            img = Image(LOGO_FILE, width=120, height=60)
            img.hAlign = 'LEFT'
            story.append(img)
            story.append(Spacer(1, 10))
        except Exception:
            pass

    story.append(Paragraph(f"<b>{empresa_nombre}</b>", style_empresa))
    story.append(Paragraph(f"{empresa_contacto}", style_sub))
    story.append(Spacer(1, 15))

    story.append(Paragraph(f"<b>PRESUPUESTO DE SERVICIO TÉCNICO</b>", ParagraphStyle('Tit', fontSize=14, textColor=colors.HexColor("#333333"))))
    story.append(Paragraph(f"<b>Fecha:</b> {datetime.now().strftime('%d/%m/%Y')}", style_body))
    story.append(Spacer(1, 10))

    # Datos del cliente
    story.append(Paragraph(f"<b>Cliente:</b> {cliente_nombre}", style_body))
    story.append(Paragraph(f"<b>Teléfono:</b> {cliente_tel}", style_body))
    story.append(Paragraph(f"<b>Dirección:</b> {cliente_dir}", style_body))
    story.append(Spacer(1, 15))

    # Tabla de items
    tabla_data = [["Descripción del Trabajo / Material", "Monto ($)"]]
    for item in items:
        if item['desc'].strip() != "":
            tabla_data.append([item['desc'], f"${item['monto']:,.2f}"])

    tabla_data.append(["TOTAL ESTIMADO", f"${total:,.2f}"])

    t = Table(tabla_data, colWidths=[380, 120])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#003366")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#f0f2f6")),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
    ]))

    story.append(t)
    story.append(Spacer(1, 15))

    if notas:
        story.append(Paragraph(f"<b>Observaciones / Condición de pago:</b> {notas}", style_body))
    
    story.append(Spacer(1, 20))
    story.append(Paragraph("<i>Gracias por su confianza. Presupuesto válido por 10 días.</i>", style_sub))

    doc.build(story)
    buffer.seek(0)
    return buffer

df_clientes = cargar_datos()

# Menú lateral para navegación
st.sidebar.header("Menú de Opciones")
opcion = st.sidebar.radio("Ir a:", [
    "📋 Lista de Clientes & Equipos", 
    "➕ Registrar Nuevo Cliente / Equipo", 
    "📄 Crear Presupuesto PDF",
    "🔔 Recordatorios de Mantenimiento",
    "⚙️ Configuración del Negocio"
])

# ---------------------------------------------------------
# OPCIÓN: CONFIGURACIÓN DEL NEGOCIO
# ---------------------------------------------------------
if opcion == "⚙️ Configuración del Negocio":
    st.subheader("Personalización de tu Negocio")
    st.write("Configura el nombre de tu empresa y el logo para que aparezcan en los presupuestos PDF.")

    empresa_nombre = st.text_input("Nombre comercial de tu negocio", value=st.session_state.get("empresa_nombre", "Servicio Técnico Climatización"))
    empresa_contacto = st.text_area("Datos de contacto (Teléfono, Email, Dirección)", value=st.session_state.get("empresa_contacto", "Tel: +54 9 3564 123456 | Morteros, Córdoba"))

    st.session_state["empresa_nombre"] = empresa_nombre
    st.session_state["empresa_contacto"] = empresa_contacto

    st.markdown("### 📷 Cargar Logo Personal")
    uploaded_logo = st.file_uploader("Sube tu logo (Formato PNG o JPG)", type=["png", "jpg", "jpeg"])

    if uploaded_logo is not None:
        with open(LOGO_FILE, "wb") as f:
            f.write(uploaded_logo.getbuffer())
        st.success("¡Logo cargado y guardado correctamente!")

    if os.path.exists(LOGO_FILE):
        st.image(LOGO_FILE, caption="Logo actual", width=150)

# ---------------------------------------------------------
# OPCIÓN 1: REGISTRAR NUEVO CLIENTE Y EQUIPO
# ---------------------------------------------------------
elif opcion == "➕ Registrar Nuevo Cliente / Equipo":
    st.subheader("Registrar Ficha de Cliente y Aire Acondicionado")

    with st.form("form_registro", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 👤 Datos del Cliente")
            nombre = st.text_input("Nombre y Apellido *")
            telefono = st.text_input("Teléfono / WhatsApp *")
            direccion = st.text_input("Dirección / Ubicación *")

        with col2:
            st.markdown("### ❄️ Datos del Equipo & Servicio")
            marca = st.text_input("Marca del Equipo (Ej: BGH, LG, Carrier)")
            modelo = st.text_input("Modelo / Código")
            frigorias = st.number_input("Frigorías / BTU", min_value=1000, max_value=20000, value=3000, step=500)
            tipo_gas = st.selectbox("Tipo de Gas Refrigerante", ["R410A", "R32", "R22", "Otro"])
            
            fecha_servicio = st.date_input("Fecha de Instalación / Service", datetime.now())
            
            fecha_prox_mantenimiento = fecha_servicio + timedelta(days=365)
            st.info(f"📅 El mantenimiento preventivo se programará para: **{fecha_prox_mantenimiento.strftime('%d/%m/%Y')}**")

        notas = st.text_area("Notas / Observaciones del trabajo realizado")

        enviado = st.form_submit_button("Guardar Cliente y Registro")

        if enviado:
            if not nombre or not telefono or not direccion:
                st.error("Por favor completa los campos obligatorios (*).")
            else:
                nuevo_id = len(df_clientes) + 1
                nueva_fila = {
                    "ID": nuevo_id,
                    "Nombre": nombre,
                    "Telefono": str(telefono),
                    "Direccion": direccion,
                    "Marca_Equipo": marca,
                    "Modelo": modelo,
                    "Frigorias": frigorias,
                    "Tipo_Gas": tipo_gas,
                    "Ultimo_Servicio": fecha_servicio.strftime('%Y-%m-%d'),
                    "Proximo_Mantenimiento": fecha_prox_mantenimiento.strftime('%Y-%m-%d'),
                    "Notas": notas
                }
                
                df_clientes = pd.concat([df_clientes, pd.DataFrame([nueva_fila])], ignore_index=True)
                guardar_datos(df_clientes)
                st.success(f"✅ ¡Cliente '{nombre}' registrado correctamente en Google Sheets!")

# ---------------------------------------------------------
# OPCIÓN 2: LISTA DE CLIENTES Y EQUIPOS
# ---------------------------------------------------------
elif opcion == "📋 Lista de Clientes & Equipos":
    st.subheader("Base de Datos de Clientes y Equipos")

    if df_clientes.empty:
        st.info("Aún no tienes clientes registrados. Ve a '➕ Registrar Nuevo Cliente / Equipo'.")
    else:
        busqueda = st.text_input("🔍 Buscar cliente por Nombre, Teléfono o Dirección:")
        if busqueda:
            df_filtrado = df_clientes[
                df_clientes['Nombre'].astype(str).str.contains(busqueda, case=False, na=False) |
                df_clientes['Telefono'].astype(str).str.contains(busqueda, case=False, na=False) |
                df_clientes['Direccion'].astype(str).str.contains(busqueda, case=False, na=False)
            ]
        else:
            df_filtrado = df_clientes

        st.dataframe(df_filtrado, use_container_width=True)

# ---------------------------------------------------------
# OPCIÓN 3: CREAR PRESUPUESTO PDF
# ---------------------------------------------------------
elif opcion == "📄 Crear Presupuesto PDF":
    st.subheader("Generador de Presupuestos en PDF")

    if df_clientes.empty:
        st.warning("Primero debes registrar al menos un cliente para crear un presupuesto.")
    else:
        cliente_sel_nombre = st.selectbox("Selecciona el Cliente:", df_clientes["Nombre"].unique())
        cliente_info = df_clientes[df_clientes["Nombre"] == cliente_sel_nombre].iloc[0]

        st.write(f"📍 **Dirección:** {cliente_info['Direccion']} | 📞 **Teléfono:** {cliente_info['Telefono']}")
        st.markdown("---")

        st.markdown("### Ítems del Presupuesto")
        num_items = st.number_input("¿Cuántos ítems/conceptos deseas agregar?", min_value=1, max_value=10, value=3)

        items = []
        total = 0.0

        for i in range(int(num_items)):
            col1, col2 = st.columns([3, 1])
            with col1:
                desc = st.text_input(f"Descripción ítem {i+1}", key=f"desc_{i}", placeholder="Ej: Mano de obra instalación / Caño 1/2 pulgada")
            with col2:
                monto = st.number_input(f"Monto ($) {i+1}", min_value=0.0, step=1000.0, key=f"monto_{i}")
            
            items.append({"desc": desc, "monto": monto})
            total += monto

        st.markdown(f"### 💰 **Total Presupuestado: ${total:,.2f}**")

        obs = st.text_area("Observaciones o validez de la oferta", "Validez del presupuesto: 10 días. Forma de pago: Contado / Transferencia.")

        if st.button("📄 Generar y Descargar PDF"):
            emp_nombre = st.session_state.get("empresa_nombre", "Servicio Técnico Climatización")
            emp_contacto = st.session_state.get("empresa_contacto", "Teléfono / Dirección de contacto")

            pdf_bytes = generar_pdf_presupuesto(
                emp_nombre,
                emp_contacto,
                cliente_info["Nombre"], 
                cliente_info["Telefono"], 
                cliente_info["Direccion"], 
                items, 
                obs, 
                total
            )

            st.download_button(
                label="⬇️ Haz clic aquí para descargar el PDF",
                data=pdf_bytes,
                file_name=f"Presupuesto_{str(cliente_info['Nombre']).replace(' ', '_')}.pdf",
                mime="application/pdf"
            )

# ---------------------------------------------------------
# OPCIÓN 4: RECORDATORIOS DE MANTENIMIENTO
# ---------------------------------------------------------
elif opcion == "🔔 Recordatorios de Mantenimiento":
    st.subheader("Alertas y Próximos Mantenimientos Preventivos")

    if df_clientes.empty:
        st.info("No hay registros para evaluar alertas de mantenimiento.")
    else:
        df_temp = df_clientes.copy()
        df_temp['Proximo_Mantenimiento'] = pd.to_datetime(df_temp['Proximo_Mantenimiento'])
        
        hoy = datetime.now()
        un_mes_despues = hoy + timedelta(days=30)

        mantenimientos_pendientes = df_temp[df_temp['Proximo_Mantenimiento'] <= un_mes_despues].sort_values(by="Proximo_Mantenimiento")

        if mantenimientos_pendientes.empty:
            st.success("🎉 No tienes mantenimientos pendientes para los próximos 30 días.")
        else:
            st.warning(f"⚠️ Tienes **{len(mantenimientos_pendientes)}** mantenimientos programados o pendientes para este mes:")

            for idx, cliente in mantenimientos_pendientes.iterrows():
                fecha_f = cliente['Proximo_Mantenimiento'].strftime('%d/%m/%Y')
                
                with st.expander(f"🔴 {cliente['Nombre']} - Vence: {fecha_f}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Teléfono:** {cliente['Telefono']}")
                        st.write(f"**Dirección:** {cliente['Direccion']}")
                    with col2:
                        st.write(f"**Equipo:** {cliente['Marca_Equipo']} ({cliente['Frigorias']} Frigorías)")
                        st.write(f"**Gas Refrigerante:** {cliente['Tipo_Gas']}")
                    
                    st.write(f"**Notas anteriores:** {cliente['Notas']}")

                    msg_wa = f"Hola {cliente['Nombre']}, te saludamos de tu servicio técnico. Te recordamos que según nuestro registro ya se cumple el plazo para realizar el mantenimiento preventivo anual a tu equipo de aire acondicionado {cliente['Marca_Equipo']}. ¿Te gustaría coordinar un turno?"
                    url_wa = f"https://wa.me/{str(cliente['Telefono']).replace('+', '').replace(' ', '')}?text={msg_wa.replace(' ', '%20')}"
                    
                    st.markdown(f"[📲 Enviar Recordatorio por WhatsApp]({url_wa})")
