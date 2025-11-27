import streamlit as st
import pandas as pd
import unicodedata
import os  # <--- 1. Agregamos esta librería para manejar rutas

# Configuración de la página
st.set_page_config(page_title="Autoridades Locales", layout="wide")

# Carga de imagen lateral
# 2. Obtenemos la ruta exacta donde vive este archivo 'app.py'
carpeta_actual = os.path.dirname(os.path.abspath(__file__))

# 3. Unimos esa ruta con el nombre de tu imagen
ruta_logo = os.path.join(carpeta_actual, "logo_gobierno.gif")

# 4. Intentamos cargar la imagen directamente usando la ruta
if os.path.exists(ruta_logo):
    st.sidebar.image(ruta_logo, width=200)
else:
    # Manejo de error si el archivo no existe
    st.sidebar.warning(f"No se encontró el logo en: {ruta_logo}")

st.sidebar.markdown("---") # Separador visual
st.sidebar.subheader("Enlaces de interés")
st.sidebar.markdown("🔒 [Intranet Subdere](http://intranet.subdere.gov.cl/)")
st.sidebar.markdown("🌐 [Web Subdere](http://www.subdere.gov.cl)")

def normalizar_texto(texto):
    """
    Elimina acentos y caracteres especiales de una cadena, pasándola a minúsculas.
    Ejemplo: 'Código_territorial' -> 'codigo_territorial'
    """
    if not isinstance(texto, str):
        return str(texto)
    # Normalizar a forma NFD (descompone caracteres) y filtrar no-ASCII (acentos)
    texto = unicodedata.normalize('NFD', texto)
    texto = texto.encode('ascii', 'ignore').decode("utf-8")
    return texto.lower().strip()

@st.cache_data
def cargar_datos():
    """
    Carga los datos de los archivos CSV y normaliza las columnas clave.
    """
    try:
        # 1. Cargar CSVs
        # distribucion.csv: Mantenemos 'cp850'
        df_dist = pd.read_csv("distribucion.csv", sep=";", dtype=str, encoding='cp850')
        
        # alcalde.csv y consejales.csv: Cambiamos a 'latin-1'
        df_alc = pd.read_csv("alcalde.csv", sep=";", dtype=str, encoding='latin-1')
        df_con = pd.read_csv("consejales.csv", sep=";", dtype=str, encoding='latin-1')

        # 2. Normalizar nombres de columnas
        for df in [df_dist, df_alc, df_con]:
            df.columns = [normalizar_texto(col) for col in df.columns]

        return df_dist, df_alc, df_con

    except FileNotFoundError as e:
        st.error(f"Error: No se encontró el archivo '{e.filename}'. Asegúrate de que los archivos .csv estén en la misma carpeta que este script.")
        return None, None, None
    except Exception as e:
        st.error(f"Ha ocurrido un error inesperado al cargar los datos: {e}")
        return None, None, None

def main():
    st.title("Consulta de Autoridades Comunales")
    st.markdown("Seleccione una región y luego una comuna para revisar su Alcalde/Alcaldesa y su Consejo Municipal.")

    # 1. Cargar Datos
    df_dist, df_alc, df_con = cargar_datos()

    if df_dist is not None:
        
        # --- NUEVO: FILTRO DE REGIÓN ---
        # Obtenemos un dataframe con regiones únicas y su código
        regiones_unicas = df_dist[['codigo_region', 'region']].drop_duplicates()
        
        # Ordenamos por 'codigo_region' para que aparezcan en orden lógico (01, 02, etc.)
        # Nota: Como son strings ('01', '02', '13'), el orden alfabético funciona correctamente para este formato.
        regiones_unicas = regiones_unicas.sort_values('codigo_region')
        
        # Selector de Región
        region_seleccionada = st.selectbox(
            "Seleccione la Región:",
            options=regiones_unicas['region'],
            index=None,
            placeholder="Seleccione una región (Opcional)..."
        )

        # Filtrar el dataframe de distribución según la selección
        if region_seleccionada:
            # Filtramos las filas que coinciden con la región seleccionada
            df_filtrado = df_dist[df_dist['region'] == region_seleccionada]
        else:
            # Si no hay selección, usamos todas las comunas
            df_filtrado = df_dist
        
        # --------------------------------

        # 2. Crear lista de comunas (Usando el dataframe filtrado)
        lista_comunas = df_filtrado['municipio'].unique()
        lista_comunas.sort()

        # 3. Selector de Comuna
        comuna_seleccionada = st.selectbox(
            "Seleccione la Comuna:",
            lista_comunas,
            index=None,
            placeholder="Escriba para buscar (ej: Iquique)..."
        )

        if comuna_seleccionada:
            # 4. Buscar el ID de la comuna (codigo_territorial)
            # Usamos df_filtrado para obtener los datos de la comuna seleccionada
            fila_comuna = df_filtrado[df_filtrado['municipio'] == comuna_seleccionada].iloc[0]
            cod_territorial = fila_comuna['codigo_territorial']
            
            # Mostrar contexto geográfico
            st.info(f"📍 **Región:** {fila_comuna['region']} | **Provincia:** {fila_comuna['provincia']}")

            # Layout de columnas
            col1, col2 = st.columns([1, 2], gap="large")
            
            # 5. Sección Alcalde
            with col1:
                st.subheader("🏛️ Alcalde(sa)")
                # Filtramos por código territorial en el df de alcaldes
                alcalde_info = df_alc[df_alc['codigo_territorial'] == cod_territorial]
                
                if not alcalde_info.empty:
                    datos_alcalde = alcalde_info.iloc[0]
                    st.success(f"**{datos_alcalde['alcalde']}**")
                    st.caption("Partido / Pacto")
                    st.write(f"**Partido:** {datos_alcalde['partido_politico']}")
                    st.write(f"**Pacto:** {datos_alcalde['pacto']}")
                else:
                    st.warning("Información no disponible.")

            # 6. Sección Concejales
            with col2:
                st.subheader("👥 Concejo Municipal")
                consejales_info = df_con[df_con['codigo_territorial'] == cod_territorial]
                
                if not consejales_info.empty:
                    # Seleccionar y renombrar columnas para la tabla
                    df_tabla = consejales_info[['concejal', 'partido_politico']].copy()
                    df_tabla.columns = ['Nombre Concejal', 'Partido Político']
                    
                    st.dataframe(
                        df_tabla, 
                        use_container_width=True, 
                        hide_index=True
                    )
                else:
                    st.warning("Información no disponible.")
            
            # --- Leyenda después del resultado ---
            st.markdown("---") 
            st.caption("Fuente: SINIM 2025")        

if __name__ == "__main__":

    main()

