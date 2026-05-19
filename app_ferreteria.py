import streamlit as st
import pypdf
import re

# Configuración de la página para que se adapte a Computadora y Celular
st.set_page_config(
    page_title="Extractor de Códigos - Ferretería",
    page_icon="🛠️",
    layout="centered"
)

# Estilos personalizados para mejorar la visualización en móviles y PC
st.markdown("""
    <style>
    .main-title {
        font-size: 24pt;
        font-weight: bold;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 10px;
    }
    .subtitle {
        font-size: 11pt;
        color: #4B5563;
        text-align: center;
        margin-bottom: 25px;
    }
    .code-box {
        background-color: #F3F4F6;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #10B981;
        margin-top: 10px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🛠️ Asistente de Códigos Ferreteros</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Sube el catálogo de tu proveedor y cambia nombres de productos por sus códigos al instante</div>', unsafe_allow_html=True)

# 1. Zona de Carga del Catálogo en la barra lateral
st.sidebar.header("📁 Carga de Catálogos")
uploaded_file = st.sidebar.file_uploader(
    "Sube el PDF del proveedor (ej. Todo Ferretero, Ferstol)", 
    type=["pdf"],
    help="Soporta PDFs pesados con texto e imágenes"
)

# Función optimizada para leer el PDF en memoria sin ralentizar la app
@st.cache_data(show_spinner="Analizando y extrayendo los códigos del catálogo... Por favor espera.")
def procesar_catalogo(file):
    pdf_reader = pypdf.PdfReader(file)
    paginas_texto = []
    
    # Recorremos el PDF extrayendo el texto de cada página
    for num_pag, pagina in enumerate(pdf_reader.pages):
        texto = pagina.extract_text()
        if texto:
            paginas_texto.append({
                "pagina": num_pag + 1,
                "contenido": texto
            })
    return paginas_texto

# Lógica principal de la aplicación
if uploaded_file is not None:
    # Procesar el archivo subido
    catalogo_datos = procesar_catalogo(uploaded_file)
    st.success(f"✅ ¡Catálogo '{uploaded_file.name}' procesado con éxito! Listo para buscar.")
    
    st.write("---")
    st.subheader("🔍 Buscador de Productos")
    
    # Campo de entrada de texto para el usuario
    producto_buscado = st.text_input(
        "Escribe el nombre del producto que necesitas (ej: Bencina Blanca, Tornillo 4, etc.):",
        placeholder="Escribe aquí..."
    )
    
    if producto_buscado:
        st.info(f"Buscando código para: **{producto_buscado}**...")
        
        encontrado = False
        resultados = []
        
        # Convertimos a minúsculas para que la búsqueda no falle por mayúsculas/minúsculas
        termino_busqueda = producto_buscado.lower()
        
        for item in catalogo_datos:
            contenido_pagina = item["contenido"]
            if termino_busqueda in contenido_pagina.lower():
                encontrado = True
                
                # Intentar buscar patrones comunes de códigos cerca del texto (letras y números guiones)
                # Este regex busca códigos comunes como TF-1234, FE-445, 1024-A, etc.
                lineas = contenido_pagina.split('\n')
                for linea in lineas:
                    if termino_busqueda in linea.lower():
                        # Buscar posibles códigos en la misma línea (secuencias de números o alfanuméricas)
                        posibles_codigos = re.findall(r'[A-Z0-9-]{3,15}', linea.upper())
                        # Filtrar palabras comunes que el regex pueda confundir como código
                        posibles_codigos = [c for c in posibles_codigos if not c.isalpha() or len(c) > 4]
                        
                        resultados.append({
                            "pagina": item["pagina"],
                            "linea_texto": linea,
                            "codigos": posibles_codigos
                        })
        
        # Mostrar los resultados al usuario
        if encontrado:
            st.success("🎯 ¡Código encontrado!")
            
            for res in resultados:
                st.markdown(f"**En la página {res['pagina']} se encontró la siguiente coincidencia:**")
                st.markdown(f"*Texto original en catálogo:* `... {res['linea_texto']} ...`")
                
                if res['codigos']:
                    codigo_sugerido = res['codigos'][0]
                    st.markdown(
                        f"""<div class="code-box">
                        <strong>Intercambio Exitoso:</strong><br>
                        El nombre <b>'{producto_buscado}'</b> corresponde al Código: <span style='font-size:14pt; color:#065F46;'><b>{codigo_sugerido}</b></span>
                        </div>""", 
                        unsafe_allow_html=True
                    )
                else:
                    st.warning("Se encontró el producto, pero no pudimos separar automáticamente el código del texto. Por favor revisa la línea de arriba.")
        else:
            st.error(f"❌ No se encontró ningún producto con el nombre '{producto_buscado}' en este catálogo. Intenta con otra palabra clave.")

else:
    # Pantalla de espera cuando no se ha subido ningún archivo
    st.info("💡 Para empezar, arrastra o selecciona el archivo PDF de tu proveedor en la barra lateral izquierda.")
    
    # Instrucciones de uso rápido para el trabajador
    st.markdown("""
    ### ¿Cómo usar la aplicación en tu día a día?
    1. **Sube el PDF:** En la barra izquierda subes el catálogo de *Ferstol* o *Todo Ferretero* (puedes guardarlo en tu celular o PC).
    2. **Escribe el Producto:** En el buscador del centro pones el artículo que te pide el cliente.
    3. **Obtén el Código:** La aplicación reemplazará el nombre por el código en un cuadro verde al instante, indicándote la página del catálogo.
    """)
