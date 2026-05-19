import streamlit as st
import pypdf
import re
import pandas as pd

# Configuración de la página
st.set_page_config(
    page_title="Extractor de Códigos Inteligente - Ferretería",
    page_icon="🛠️",
    layout="wide"
)

# Estilos visuales
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

st.markdown('<div class="main-title">🛠️ Buscador Ferretero Inteligente</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Búsqueda flexible: Encuentra códigos sin necesidad de escribir el nombre exacto del catálogo</div>', unsafe_allow_html=True)

# Barra lateral para cargar el catálogo
st.sidebar.header("📁 Catálogo del Proveedor")
uploaded_file = st.sidebar.file_uploader(
    "Sube el PDF del proveedor (ej. Todo Ferretero, Ferstol)", 
    type=["pdf"]
)

# Función optimizada para extraer texto
@st.cache_data(show_spinner="Analizando catálogo... Por favor espera.")
def procesar_catalogo(file):
    pdf_reader = pypdf.PdfReader(file)
    paginas_texto = []
    for num_pag, pagina in enumerate(pdf_reader.pages):
        texto = pagina.extract_text()
        if texto:
            paginas_texto.append({"pagina": num_pag + 1, "contenido": texto})
    return paginas_texto

if uploaded_file is not None:
    catalogo_datos = procesar_catalogo(uploaded_file)
    st.sidebar.success(f"✅ Catálogo '{uploaded_file.name}' listo.")
    
    st.subheader("📝 Pega tu lista de productos")
    st.write("Escribe tus productos (uno por línea). ¡Ya no importa si no pones el nombre exacto o si te faltan detalles técnicos!")
    
    lista_productos_raw = st.text_area(
        "Lista de productos a consultar:",
        height=250,
        placeholder="Ejemplo:\nUnión Americana h i de media\nBencina blanca\nTornillo madera 4"
    )
    
    if st.button("🚀 Buscar todos los códigos ahora"):
        productos_a_buscar = [p.strip() for p in lista_productos_raw.split('\n') if p.strip()]
        
        if not productos_a_buscar:
            st.warning("⚠️ Por favor, ingresa al menos un producto.")
        else:
            st.info(f"🔎 Procesando {len(productos_a_buscar)} productos con búsqueda inteligente...")
            
            tabla_resultados = []
            
            for producto in productos_a_buscar:
                # NUEVO: Dividimos tu búsqueda en palabras individuales y limpiamos espacios
                palabras_clave = [palabra.lower() for palabra in producto.split() if len(palabra) > 0]
                
                codigo_encontrado = "No encontrado"
                pagina_encontrada = "-"
                
                if palabras_clave:
                    # Buscar en el catálogo
                    for item in catalogo_datos:
                        contenido_pagina_lower = item["contenido"].lower()
                        
                        # NUEVO: Verifica que TODAS tus palabras clave estén en la página (no importa el orden)
                        if all(palabra in contenido_pagina_lower for palabra in palabras_clave):
                            
                            # Si la página tiene todas las palabras, buscamos la línea exacta
                            lineas = item["contenido"].split('\n')
                            for linea in lineas:
                                linea_lower = linea.lower()
                                
                                # Si la línea contiene la mayoría o todas las palabras clave, extraemos el código
                                if all(palabra in linea_lower for palabra in palabras_clave):
                                    posibles_codigos = re.findall(r'[A-Z0-9-]{3,15}', linea.upper())
                                    posibles_codigos = [c for c in posibles_codigos if not c.isalpha() or len(c) > 4]
                                    
                                    if posibles_codigos:
                                        codigo_encontrado = posibles_codigos[0]
                                        pagina_encontrada = f"Pág. {item['pagina']}"
                                        break
                            
                            # Si ya encontramos el código en esta página, no seguimos buscando para ahorrar tiempo
                            if codigo_encontrado != "No encontrado":
                                break
                
                tabla_resultados.append({
                    "Producto que Tú Buscaste": producto,
                    "Código del Proveedor": codigo_encontrado,
                    "Ubicación": pagina_encontrada
                })
            
            df_resultados = pd.DataFrame(tabla_resultados)
            
            st.write("---")
            st.success("🎯 ¡Búsqueda completada con éxito!")
            st.dataframe(df_resultados, use_container_width=True, hide_index=True)
            
            csv = df_resultados.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar lista en Excel/CSV",
                data=csv,
                file_name="codigos_busqueda_inteligente.csv",
                mime="text/csv",
            )
else:
    st.info("💡 Para comenzar, sube el archivo PDF del proveedor en la barra lateral izquierda.")
