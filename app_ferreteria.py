import streamlit as st
import pypdf
import re
import pandas as pd

# Configuración de la página
st.set_page_config(
    page_title="Extractor de Códigos Múltiple - Ferretería",
    page_icon="🛠️",
    layout="wide"
)

# Estilos visuales optimizados
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

st.markdown('<div class="main-title">🛠️ Extractor de Códigos en Lote</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Pega una lista de hasta 50 productos y obtén todos los códigos al instante</div>', unsafe_allow_html=True)

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
    
    st.subheader("📝 Pega tu lista de productos aquí")
    st.write("Escribe o pega tus productos (uno por línea). Por ejemplo, puedes copiar una lista desde Excel o WhatsApp:")
    
    # Cuadro de texto grande para recibir múltiples líneas
    lista_productos_raw = st.text_area(
        "Lista de productos a consultar:",
        height=250,
        placeholder="Ejemplo:\nBencina Blanca\nTornillo Madera 4\nCinta aisladora\nSilicona líquida"
    )
    
    if st.button("🚀 Buscar todos los códigos ahora"):
        # Limpiar la lista: separar por saltos de línea y quitar espacios en blanco
        productos_a_buscar = [p.strip() for p in lista_productos_raw.split('\n') if p.strip()]
        
        if not productos_a_buscar:
            st.warning("⚠️ Por favor, ingresa al menos un producto en la lista.")
        else:
            st.info(f"🔎 Procesando {len(productos_a_buscar)} productos en tiempo real...")
            
            # Lista para guardar los resultados finales
            tabla_resultados = []
            
            # Recorrer cada producto de la lista del usuario
            for producto in productos_a_buscar:
                termino = producto.lower()
                codigo_encontrado = "No encontrado"
                pagina_encontrada = "-"
                
                # Buscar en el catálogo
                for item in catalogo_datos:
                    if termino in item["contenido"].lower():
                        # Si lo encuentra, extraer las líneas de esa página para aislar el código
                        lineas = item["contenido"].split('\n')
                        for linea in lineas:
                            if termino in linea.lower():
                                # Buscar patrones de códigos (números, letras y guiones)
                                posibles_codigos = re.findall(r'[A-Z0-9-]{3,15}', linea.upper())
                                posibles_codigos = [c for c in posibles_codigos if not c.isalpha() or len(c) > 4]
                                
                                if posibles_codigos:
                                    codigo_encontrado = posibles_codigos[0]
                                    pagina_encontrada = f"Pág. {item['pagina']}"
                                    break
                        if codigo_encontrado != "No encontrado":
                            break
                
                # Agregar a nuestra estructura de resultados
                tabla_resultados.append({
                    "Producto Solicitado": producto,
                    "Código del Proveedor": codigo_encontrado,
                    "Ubicación": pagina_encontrada
                })
            
            # Convertir a un formato de tabla (Pandas DataFrame) para mostrarlo impecable
            df_resultados = pd.DataFrame(tabla_resultados)
            
            st.write("---")
            st.success("🎯 ¡Búsqueda en lote completada!")
            
            # Mostrar la tabla en pantalla completa
            st.dataframe(df_resultados, use_container_width=True, hide_index=True)
            
            # Opción extra: Permitir al usuario descargar la lista a Excel o CSV
            csv = df_resultados.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar esta lista en formato Excel/CSV",
                data=csv,
                file_name="codigos_ferreteria_encontrados.csv",
                mime="text/csv",
            )
else:
    st.info("💡 Para comenzar, sube el archivo PDF del proveedor en la barra lateral izquierda.")
    st.markdown("""
    ### Cómo usar el modo masivo:
    1. **Sube el catálogo** del proveedor a la izquierda.
    2. **Copia tu lista** de notas, WhatsApp o un Excel (hasta 50 productos o más).
    3. **Pégala** en el cuadro central.
    4. Presiona **"Buscar todos los códigos ahora"** y el sistema te entregará una lista limpia con todos los códigos ordenados al tiro. ¡Incluso puedes descargar el resultado!
    """)
