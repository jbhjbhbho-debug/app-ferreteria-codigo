import streamlit as st
import pypdf
import re
import pandas as pd

# Configuración de la página
st.set_page_config(
    page_title="Extractor de Códigos Avanzado - Ferretería",
    page_icon="🛠️",
    layout="wide"
)

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
    th {
        background-color: #1E3A8A !important;
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🛠️ Extractor de Códigos por Bloques</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Optimizado para catálogos con código abajo del nombre (Formatos complejos)</div>', unsafe_allow_html=True)

# Barra lateral para cargar el catálogo
st.sidebar.header("📁 Carga del PDF")
uploaded_file = st.sidebar.file_uploader(
    "Sube el PDF de tu proveedor", 
    type=["pdf"]
)

# NUEVO MOTOR: Extrae todo el contenido del catálogo y pre-procesa la estructura
@st.cache_data(show_spinner="Procesando y extrayendo TODO el catálogo... Esto asegura encontrar los códigos ocultos abajo.")
def procesar_catalogo_completo(file):
    pdf_reader = pypdf.PdfReader(file)
    paginas_datos = []
    
    for num_pag, pagina in enumerate(pdf_reader.pages):
        texto = pagina.extract_text()
        if texto:
            # Guardamos las líneas limpias de la página para poder mirar hacia abajo
            lineas = [l.strip() for l in texto.split('\n') if l.strip()]
            paginas_datos.append({
                "pagina": num_pag + 1,
                "texto_completo": texto,
                "lineas": lineas
            })
    return paginas_datos

if uploaded_file is not None:
    catalogo_datos = procesar_catalogo_completo(uploaded_file)
    st.sidebar.success(f"✅ ¡Catálogo completo de '{uploaded_file.name}' indexado con éxito!")
    
    st.subheader("📝 Pega tu lista de productos (Hasta 50 o más)")
    lista_productos_raw = st.text_area(
        "Lista de productos a consultar (uno por línea):",
        height=200,
        placeholder="Ejemplo:\nUnión Americana h i de media\nBencina blanca"
    )
    
    if st.button("🚀 Buscar todos los códigos ahora"):
        productos_a_buscar = [p.strip() for p in lista_productos_raw.split('\n') if p.strip()]
        
        if not productos_a_buscar:
            st.warning("⚠️ Por favor, ingresa al menos un producto.")
        else:
            st.info(f"🔎 Analizando {len(productos_a_buscar)} productos en toda la base de datos del PDF...")
            
            tabla_resultados = []
            
            for producto in productos_a_buscar:
                palabras_clave = [palabra.lower() for palabra in producto.split() if len(palabra) > 0]
                
                codigo_encontrado = "No encontrado"
                contexto_encontrado = "No se halló el producto en el catálogo"
                pagina_encontrada = "-"
                
                if palabras_clave:
                    # Recorrer las páginas indexadas
                    for item in catalogo_datos:
                        texto_pag_lower = item["texto_completo"].lower()
                        
                        # Comprobar si la página contiene todas las palabras que buscas
                        if all(palabra in texto_pag_lower for palabra in palabras_clave):
                            pagina_encontrada = f"Pág. {item['pagina']}"
                            lineas = item["lineas"]
                            
                            # Buscar en qué línea está el nombre para mirar lo que hay ABAJO
                            for i, linea in enumerate(lineas):
                                if all(palabra in linea.lower() for palabra in palabras_clave):
                                    contexto_encontrado = linea
                                    
                                    # REVISIÓN EN BLOQUE: Miramos la línea del nombre y hasta 3 líneas más abajo
                                    bloque_texto_abajo = ""
                                    rango_lineas_abajo = lineas[i:i+4] # Agarra la línea actual y las 3 siguientes
                                    bloque_texto_abajo = " | ".join(rango_lineas_abajo)
                                    
                                    # NUEVO REGEX: Busca patrones tipo f300, F-300, letras+números o códigos numéricos limpios
                                    # Evita confundirse con palabras normales de la descripción
                                    todos_los_codigos = re.findall(r'\b[A-Za-z-]*\d+[A-Za-z0-9-]*\b', bloque_texto_abajo)
                                    
                                    # Filtrar códigos válidos (que no sean solo números de página o medidas simples como "10")
                                    codigos_filtrados = [c for c in todos_los_codigos if len(c) >= 3 and not c.lower() in ['pn10', 'pn16', 'html']]
                                    
                                    if codigos_filtrados:
                                        # Si encuentra un código tipo f300, lo rescata de una
                                        codigo_encontrado = codigos_filtrados[0]
                                    else:
                                        # Si no pilla el patrón limpio, te muestra el pedazo de texto de abajo para que lo veas tú
                                        codigo_encontrado = rango_lineas_abajo[1] if len(rango_lineas_abajo) > 1 else "Ver catálogo"
                                    break
                            
                            if codigo_encontrado != "No encontrado":
                                break
                
                tabla_resultados.append({
                    "Producto Solicitado": producto,
                    "Código Extraído": codigo_encontrado,
                    "Línea Detectada": contexto_encontrado,
                    "Ubicación": pagina_encontrada
                })
            
            df_resultados = pd.DataFrame(tabla_resultados)
            
            st.write("---")
            st.success("🎯 ¡Búsqueda masiva por bloques terminada!")
            st.dataframe(df_resultados, use_container_width=True, hide_index=True)
            
            csv = df_resultados.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar resultados a Excel",
                data=csv,
                file_name="codigos_ferretera_v5.csv",
                mime="text/csv",
            )
else:
    st.info("💡 Para comenzar, sube el archivo PDF del proveedor en la barra lateral izquierda.")
