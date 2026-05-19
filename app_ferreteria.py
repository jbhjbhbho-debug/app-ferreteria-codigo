import streamlit as st
import pypdf
import re
import pandas as pd

# Configuración de la página para Computadora y Celular
st.set_page_config(
    page_title="Sistema de Catálogos - Ferretería",
    page_icon="🛠️",
    layout="wide"
)

# Estilos visuales profesionales
st.markdown("""
    <style>
    .main-title {
        font-size: 26pt;
        font-weight: bold;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 5px;
    }
    .subtitle {
        font-size: 12pt;
        color: #4B5563;
        text-align: center;
        margin-bottom: 25px;
    }
    .proveedor-box {
        background-color: #F3F4F6;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
        border-left: 4px solid #1E3A8A;
    }
    th {
        background-color: #1E3A8A !important;
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🛠️ Central de Códigos Ferreteros</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Sube y consulta los catálogos de tus 5 proveedores principales en un solo lugar</div>', unsafe_allow_html=True)

# Inicializar la memoria de los catálogos en la aplicación si no existen
if "catalogos" not do in st.session_state:
    st.session_state.catalogos = {
        "Todo Ferretero": None,
        "Ferres Tools": None,
        "Diferrio": None,
        "Inco": None,
        "Bosch": None
    }

# FUNCIÓN PARA PROCESAR EL PDF COMPLETAMENTE
def guardar_catalogo(file):
    pdf_reader = pypdf.PdfReader(file)
    paginas_datos = []
    for num_pag, pagina in enumerate(pdf_reader.pages):
        texto = pagina.extract_text()
        if texto:
            lineas = [l.strip() for l in texto.split('\n') if l.strip()]
            paginas_datos.append({
                "pagina": num_pag + 1,
                "texto_completo": texto,
                "lineas": lineas
            })
    return paginas_datos

# --- BARRA LATERAL: LOS 5 CASILLEROS PARA PROVEEDORES ---
st.sidebar.header("📁 Carga de Catálogos")
st.sidebar.write("Sube el PDF correspondiente a cada casilla:")

# Lista de tus 5 proveedores exactos
proveedores = ["Todo Ferretero", "Ferres Tools", "Diferrio", "Inco", "Bosch"]

for prov in proveedores:
    st.sidebar.markdown(f'<div class="proveedor-box"><b>{prov}</b></div>', unsafe_allow_html=True)
    archivo = st.sidebar.file_uploader(f"Seleccionar PDF para {prov}", type=["pdf"], key=prov, label_visibility="collapsed")
    
    if archivo is not None and st.session_state.catalogos[prov] is None:
        with st.sidebar.spinner(f"Indexando {prov}..."):
            st.session_state.catalogos[prov] = guardar_catalogo(archivo)
        st.sidebar.success(f"✅ {prov} Cargado")

# --- CUERPO CENTRAL: BUSCADOR Y SELECCIÓN ---
st.subheader("🔍 Módulo de Búsqueda Masiva")

# Selector para decirle a la app en cuál de los 5 catálogos buscar
proveedor_seleccionado = st.selectbox(
    "1. ¿A qué proveedor le vas a buscar códigos?",
    options=proveedores,
    help="Selecciona el proveedor del cual quieres los códigos"
)

# Verificar si el proveedor elegido tiene un catálogo cargado
if st.session_state.catalogos[proveedor_seleccionado] is None:
    st.warning(f"⚠️ El catálogo de **{proveedor_seleccionado}** aún no ha sido cargado. Por favor, súbelo en la barra lateral izquierda para empezar.")
else:
    st.success(f"👌 Buscador conectado correctamente al catálogo de **{proveedor_seleccionado}**.")
    
    # Cuadro para pegar la lista de 20, 40 o 50 productos
    st.write("**2. Pega tu lista de productos (uno por línea):**")
    lista_productos_raw = st.text_area(
        "Lista de productos:",
        height=250,
        placeholder="Ejemplo:\nUnión Americana h i de media\nBencina blanca\nBroca concreto 6mm"
    )
    
    if st.button("🚀 Obtener todos los códigos al instante"):
        productos_a_buscar = [p.strip() for p in lista_productos_raw.split('\n') if p.strip()]
        
        if not productos_a_buscar:
            st.warning("⚠️ Escribe o pega al menos un producto en el cuadro.")
        else:
            st.info(f"🔎 Buscando {len(productos_a_buscar)} productos en el catálogo de {proveedor_seleccionado}...")
            
            catalogo_actual = st.session_state.catalogos[proveedor_seleccionado]
            tabla_resultados = []
            
            for producto in productos_a_buscar:
                palabras_clave = [palabra.lower() for palabra in producto.split() if len(palabra) > 0]
                
                codigo_encontrado = "No encontrado"
                linea_completa = "No se encontró coincidencia"
                pagina_encontrada = "-"
                
                if palabras_clave:
                    for item in catalogo_actual:
                        texto_pag_lower = item["texto_completo"].lower()
                        
                        # Si todas las palabras clave están en la página
                        if all(palabra in texto_pag_lower for palabra in palabras_clave):
                            pagina_encontrada = f"Pág. {item['pagina']}"
                            lineas = item["lineas"]
                            
                            # Buscar la línea del nombre y analizar el bloque (por si el código está abajo)
                            for i, linea in enumerate(lineas):
                                if all(palabra in linea.lower() for palabra in palabras_clave):
                                    linea_completa = linea
                                    
                                    # Tomamos la línea actual y miramos hasta 3 líneas más abajo para no perder el código
                                    bloque_lineas = lineas[i:i+4]
                                    texto_bloque = " | ".join(bloque_lineas)
                                    
                                    # Buscador de códigos flexible (ej: f300, 1024, B-50)
                                    todos_los_codigos = re.findall(r'\b[A-Za-z-]*\d+[A-Za-z0-9-]*\b', texto_bloque)
                                    codigos_filtrados = [c for c in todos_los_codigos if len(c) >= 3 and not c.lower() in ['pn10', 'pn16', 'pn25', 'mm']]
                                    
                                    if codigos_filtrados:
                                        codigo_encontrado = codigos_filtrados[0]
                                    else:
                                        # Si el código viene raro o al lado, te deja la línea de abajo para que la veas directo
                                        codigo_encontrado = bloque_lineas[1] if len(bloque_lineas) > 1 else "Ver Línea"
                                    break
                            
                            if codigo_encontrado != "No encontrado":
                                break
                
                tabla_resultados.append({
                    "Tu Lista de Productos": producto,
                    "Código Extraído": codigo_encontrado,
                    "Detalle / Línea del Catálogo": linea_completa,
                    "Ubicación": pagina_encontrada
                })
            
            # Mostrar la tabla final organizada
            df_resultados = pd.DataFrame(tabla_resultados)
            st.write("---")
            st.success(f"🎯 ¡Códigos de {proveedor_seleccionado} extraídos con éxito!")
            st.dataframe(df_resultados, use_container_width=True, hide_index=True)
            
            # Descarga directa a Excel
            csv = df_resultados.to_csv(index=False).encode('utf-8')
            st.download_button(
                label=f"📥 Descargar Lista de {proveedor_seleccionado} a Excel",
                data=csv,
                file_name=f"codigos_{proveedor_seleccionado.lower().replace(' ', '_')}.csv",
                mime="text/csv",
            )
