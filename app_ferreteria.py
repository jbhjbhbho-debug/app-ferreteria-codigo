import streamlit as st
import pypdf
import re
import pandas as pd

# Configuración de la página
st.set_page_config(
    page_title="Extractor de Códigos Universal - Ferretería",
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

st.markdown('<div class="main-title">🛠️ Buscador Universal de Códigos</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Compatible con múltiples proveedores: Todo Ferretero, Ferstol y más</div>', unsafe_allow_html=True)

# Barra lateral para cargar el catálogo
st.sidebar.header("📁 Catálogo del Proveedor")
uploaded_file = st.sidebar.file_uploader(
    "Sube el PDF de CUALQUIER proveedor", 
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
    st.write("Escribe tus productos (uno por línea). El sistema buscará de forma inteligente adaptándose al formato del proveedor.")
    
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
            st.info(f"🔎 Procesando {len(productos_a_buscar)} productos...")
            
            tabla_resultados = []
            
            for producto in productos_a_buscar:
                palabras_clave = [palabra.lower() for palabra in producto.split() if len(palabra) > 0]
                
                codigo_encontrado = "No encontrado"
                linea_texto_proveedor = "No encontrado en el PDF"
                pagina_encontrada = "-"
                
                if palabras_clave:
                    for item in catalogo_datos:
                        contenido_pagina_lower = item["contenido"].lower()
                        
                        # Comprobar si todas las palabras clave están en la página
                        if all(palabra in contenido_pagina_lower for palabra in palabras_clave):
                            lineas = item["contenido"].split('\n')
                            
                            for linea in lineas:
                                linea_lower = linea.lower()
                                
                                # Comprobar si la línea tiene las palabras clave
                                if all(palabra in linea_lower for palabra in palabras_clave):
                                    pagina_encontrada = f"Pág. {item['pagina']}"
                                    linea_texto_proveedor = linea.strip()
                                    
                                    # Intentar extraer un código limpio con una fórmula más flexible (letras, números, puntos, guiones)
                                    posibles_codigos = re.findall(r'[A-Z0-9.-]{2,15}', linea.upper())
                                    # Filtrar palabras comunes cortas
                                    posibles_codigos = [c for c in posibles_codigos if not c.isalpha() or len(c) > 3]
                                    
                                    if posibles_codigos:
                                        codigo_encontrado = posibles_codigos[0]
                                    else:
                                        # SI NO ENCUENTRA UN CÓDIGO LIMPIO: Te muestra la línea entera del catálogo para que lo veas tú mismo
                                        codigo_encontrado = "Revisar línea ➔"
                                    break
                            
                            if pagina_encontrada != "-":
                                break
                
                tabla_resultados.append({
                    "Producto que Buscaste": producto,
                    "Código Sugerido": codigo_encontrado,
                    "Texto Original en Catálogo (Información del Proveedor)": linea_texto_proveedor,
                    "Ubicación": pagina_encontrada
                })
            
            df_resultados = pd.DataFrame(tabla_resultados)
            
            st.write("---")
            st.success("🎯 ¡Búsqueda completada!")
            st.dataframe(df_resultados, use_container_width=True, hide_index=True)
            
            csv = df_resultados.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar lista en Excel/CSV",
                data=csv,
                file_name="codigos_proveedores_ferreteria.csv",
                mime="text/csv",
            )
else:
    st.info("💡 Para comenzar, sube el archivo PDF de tu proveedor en la barra lateral izquierda.")
