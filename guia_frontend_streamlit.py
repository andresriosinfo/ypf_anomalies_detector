"""
Dashboard Streamlit - Guía para Desarrollo Front-End
Tabla: otms_analytics.dbo.ypf_anomaly_detector
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Agregar path para importar módulos
sys.path.append(str(Path(__file__).parent))
from sql_utils import SQLConnection

# Configuración de página
st.set_page_config(
    page_title="Guía Front-End - Detección de Anomalías",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuración de conexión SQL
SQL_CONFIG = {
    'server': '10.147.17.241',
    'database': 'otms_analytics',
    'username': 'sa',
    'password': 'OtmsSecure2024Dev123',
    'port': 1433
}

# Cache para conexión SQL
@st.cache_resource
def get_sql_connection():
    """Obtiene conexión a SQL Server"""
    conn = SQLConnection(**SQL_CONFIG)
    if conn.connect():
        return conn
    return None

# Cache para datos
@st.cache_data(ttl=300)  # Cache por 5 minutos
def load_data(query: str):
    """Carga datos desde SQL Server"""
    conn = get_sql_connection()
    if conn:
        df = conn.execute_query(query)
        return df
    return None

# Título principal
st.title("Guía de Desarrollo Front-End")
st.markdown("### Tabla: `otms_analytics.dbo.ypf_anomaly_detector`")
st.markdown("---")

# Sidebar para navegación
st.sidebar.title("Navegación")
page = st.sidebar.radio(
    "Secciones",
    [
        "Overview y Estructura",
        "Visualización 1: Timeline de Anomalías",
        "Visualización 2: Heatmap por Variable",
        "Visualización 3: Distribución de Scores",
        "Visualización 4: Tendencias Temporales",
        "Visualización 5: Dashboard de Anomalías",
        "Vista del Operario",
        "Queries SQL Comunes"
    ]
)

# ============================================================================
# PÁGINA 1: OVERVIEW Y ESTRUCTURA
# ============================================================================
if page == "Overview y Estructura":
    st.header("Overview y Estructura de la Tabla")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### Descripción General
        
        La tabla **`ypf_anomaly_detector`** contiene los resultados de la detección de anomalías 
        en variables de proceso industrial. Cada registro representa un punto de datos analizado 
        con su predicción, intervalo de confianza y clasificación como anomalía.
        
        ### Propósito
        
        Esta tabla permite a los desarrolladores front-end crear dashboards y visualizaciones 
        que ayuden a los operadores a:
        - **Identificar anomalías** en tiempo real
        - **Monitorear tendencias** de variables de proceso
        - **Analizar patrones** históricos de anomalías
        - **Tomar decisiones** basadas en datos
        """)
    
    with col2:
        st.info("""
        **Base de Datos:** `otms_analytics`  
        **Tabla:** `dbo.ypf_anomaly_detector`  
        **Registros:** ~71,000+  
        **Actualización:** En tiempo real
        """)
    
    st.markdown("---")
    
    # Estructura de la tabla
    st.subheader("Estructura de Columnas")
    
    estructura_data = {
        'Columna': [
            'id', 'ds', 'y', 'yhat', 'yhat_lower', 'yhat_upper',
            'residual', 'outside_interval', 'high_residual', 'is_anomaly',
            'anomaly_score', 'variable', 'prediction_error_pct', 
            'source_file', 'processed_at'
        ],
        'Tipo': [
            'BIGINT (PK)', 'DATETIME', 'DECIMAL(18,6)', 'DECIMAL(18,6)', 
            'DECIMAL(18,6)', 'DECIMAL(18,6)', 'DECIMAL(18,6)', 'BIT', 
            'BIT', 'BIT', 'DECIMAL(5,2)', 'VARCHAR(100)', 'DECIMAL(5,2)',
            'VARCHAR(255)', 'DATETIME'
        ],
        'Descripción': [
            'ID único del registro',
            'Fecha y hora del dato',
            'Valor real observado',
            'Valor predicho por el modelo',
            'Límite inferior del intervalo de confianza',
            'Límite superior del intervalo de confianza',
            'Diferencia entre valor real y predicho',
            '1 si está fuera del intervalo (95%)',
            '1 si el residual es alto',
            '1 si es anomalía (cualquiera de las condiciones)',
            'Score de anomalía (0-100, mayor = más anómalo)',
            'Nombre de la variable de proceso',
            'Error porcentual de predicción',
            'Archivo fuente de los datos',
            'Fecha de procesamiento'
        ]
    }
    
    df_estructura = pd.DataFrame(estructura_data)
    st.dataframe(df_estructura, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # Ejemplo de datos
    st.subheader("Ejemplo de Registros")
    
    query_ejemplo = """
        SELECT TOP 10 
            id, ds, variable, y, yhat, yhat_lower, yhat_upper,
            is_anomaly, anomaly_score, prediction_error_pct
        FROM dbo.ypf_anomaly_detector
        ORDER BY ds DESC
    """
    
    df_ejemplo = load_data(query_ejemplo)
    if df_ejemplo is not None:
        st.dataframe(df_ejemplo, use_container_width=True)
        
        st.markdown("""
        **Nota:** 
        - `is_anomaly = 1` significa que el punto es una anomalía
        - `anomaly_score` va de 0 a 100 (mayor = más anómalo)
        - `y` es el valor real, `yhat` es el valor predicho
        """)
    
    st.markdown("---")
    
    # Índices y optimizaciones
    st.subheader("Índices y Optimizaciones")
    
    st.markdown("""
    La tabla tiene los siguientes índices para optimizar consultas:
    
    - **`idx_ds`**: Sobre `ds` (fecha) - Para filtros temporales
    - **`idx_variable`**: Sobre `variable` - Para filtrar por variable
    - **`idx_is_anomaly`**: Sobre `is_anomaly` - Para filtrar solo anomalías
    - **`idx_anomaly_score`**: Sobre `anomaly_score` - Para ordenar por score
    - **`idx_processed_at`**: Sobre `processed_at` - Para consultas de procesamiento
    
    **Tip:** Siempre usa estos campos en tus WHERE y ORDER BY para mejor performance.
    """)

# ============================================================================
# PÁGINA 2: TIMELINE DE ANOMALÍAS
# ============================================================================
elif page == "Visualización 1: Timeline de Anomalías":
    st.header("Visualización 1: Timeline de Anomalías")
    
    st.markdown("""
    ### Finalidad
    
    Mostrar la **evolución temporal de las anomalías detectadas**, permitiendo identificar:
    - **Patrones temporales**: ¿Hay horas/días con más anomalías?
    - **Tendencias**: ¿Aumentan o disminuyen las anomalías?
    - **Eventos críticos**: Picos de anomalías que requieren atención
    
    ### Casos de Uso
    
    - Dashboard principal para monitoreo en tiempo real
    - Análisis histórico de eventos anómalos
    - Alertas cuando hay picos de anomalías
    """)
    
    st.markdown("---")
    
    # Controles
    col1, col2, col3 = st.columns(3)
    
    with col1:
        fecha_inicio = st.date_input(
            "Fecha Inicio",
            value=datetime.now().date() - timedelta(days=7),
            key="timeline_start"
        )
    
    with col2:
        fecha_fin = st.date_input(
            "Fecha Fin",
            value=datetime.now().date(),
            key="timeline_end"
        )
    
    with col3:
        variable_filtro = st.selectbox(
            "Variable (opcional)",
            options=["Todas"] + ["ARO_FC103", "ARO_FC105", "ARO_LC101", "ARO_PC101"],
            key="timeline_var"
        )
    
    # Query SQL
    st.subheader("Query SQL para esta Visualización")
    
    query_timeline = f"""
        SELECT 
            CAST(ds AS DATE) as fecha,
            COUNT(*) as total_puntos,
            SUM(CASE WHEN is_anomaly = 1 THEN 1 ELSE 0 END) as total_anomalias,
            AVG(anomaly_score) as score_promedio
        FROM dbo.ypf_anomaly_detector
        WHERE ds >= '{fecha_inicio}' 
          AND ds <= '{fecha_fin}'
    """
    
    if variable_filtro != "Todas":
        query_timeline += f" AND variable = '{variable_filtro}'"
    
    query_timeline += """
        GROUP BY CAST(ds AS DATE)
        ORDER BY fecha
    """
    
    st.code(query_timeline, language="sql")
    
    st.markdown("---")
    
    # Visualización
    st.subheader("Visualización de Ejemplo")
    
    df_timeline = load_data(query_timeline)
    
    if df_timeline is not None and len(df_timeline) > 0:
        # Gráfico de líneas
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df_timeline['fecha'],
            y=df_timeline['total_anomalias'],
            mode='lines+markers',
            name='Anomalías Detectadas',
            line=dict(color='#ff4444', width=2),
            marker=dict(size=8)
        ))
        
        fig.add_trace(go.Scatter(
            x=df_timeline['fecha'],
            y=df_timeline['total_puntos'],
            mode='lines',
            name='Total de Puntos',
            line=dict(color='#4444ff', width=1, dash='dash'),
            yaxis='y2'
        ))
        
        fig.update_layout(
            title='Timeline de Anomalías Detectadas',
            xaxis_title='Fecha',
            yaxis_title='Número de Anomalías',
            yaxis2=dict(title='Total de Puntos', overlaying='y', side='right'),
            hovermode='x unified',
            height=500,
            template='plotly_white'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.info("""
        **Cómo se ve esta visualización:**
        
        Esta es una visualización de línea temporal que muestra la cantidad de anomalías detectadas 
        por día. La línea roja muestra las anomalías y la línea azul punteada muestra el total de 
        puntos analizados. Los picos en la línea roja indican días con mayor número de anomalías.
        
        **Elementos clave para el front-end:**
        - Gráfico de líneas con dos ejes Y
        - Tooltip interactivo al pasar el mouse
        - Zoom y pan habilitados
        - Colores distintivos (rojo para anomalías, azul para total)
        """)
        
        # Métricas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Anomalías", f"{df_timeline['total_anomalias'].sum():,}")
        with col2:
            st.metric("Promedio Diario", f"{df_timeline['total_anomalias'].mean():.1f}")
        with col3:
            st.metric("Máximo Diario", f"{df_timeline['total_anomalias'].max():,}")
        with col4:
            st.metric("Score Promedio", f"{df_timeline['score_promedio'].mean():.1f}")
        
        # Tabla de datos
        with st.expander("Ver Datos"):
            st.dataframe(df_timeline, use_container_width=True)

# ============================================================================
# PÁGINA 3: HEATMAP POR VARIABLE
# ============================================================================
elif page == "Visualización 2: Heatmap por Variable":
    st.header("Visualización 2: Heatmap por Variable")
    
    st.markdown("""
    ### Finalidad
    
    Identificar **qué variables tienen más anomalías** y **cuándo ocurren**, permitiendo:
    - **Priorizar atención**: Variables con más anomalías
    - **Detectar correlaciones**: Variables que fallan juntas
    - **Análisis comparativo**: Comparar comportamiento entre variables
    
    ### Casos de Uso
    
    - Panel de control para identificar variables problemáticas
    - Análisis de causa raíz (¿qué variables fallan más?)
    - Reportes ejecutivos de resumen
    """)
    
    st.markdown("---")
    
    # Controles
    col1, col2 = st.columns(2)
    
    with col1:
        fecha_inicio_heat = st.date_input(
            "Fecha Inicio",
            value=datetime.now().date() - timedelta(days=30),
            key="heatmap_start"
        )
    
    with col2:
        fecha_fin_heat = st.date_input(
            "Fecha Fin",
            value=datetime.now().date(),
            key="heatmap_end"
        )
    
    # Query SQL
    st.subheader("Query SQL para esta Visualización")
    
    query_heatmap = f"""
        SELECT 
            variable,
            CAST(ds AS DATE) as fecha,
            SUM(CASE WHEN is_anomaly = 1 THEN 1 ELSE 0 END) as anomalias,
            COUNT(*) as total_puntos,
            CAST(SUM(CASE WHEN is_anomaly = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS DECIMAL(5,2)) as tasa_anomalias
        FROM dbo.ypf_anomaly_detector
        WHERE ds >= '{fecha_inicio_heat}' 
          AND ds <= '{fecha_fin_heat}'
        GROUP BY variable, CAST(ds AS DATE)
        ORDER BY variable, fecha
    """
    
    st.code(query_heatmap, language="sql")
    
    st.markdown("---")
    
    # Visualización
    st.subheader("Visualización de Ejemplo")
    
    df_heatmap = load_data(query_heatmap)
    
    if df_heatmap is not None and len(df_heatmap) > 0:
        # Preparar datos para heatmap
        df_pivot = df_heatmap.pivot_table(
            index='variable',
            columns='fecha',
            values='tasa_anomalias',
            aggfunc='mean',
            fill_value=0
        )
        
        # Heatmap
        fig = px.imshow(
            df_pivot.values,
            labels=dict(x="Fecha", y="Variable", color="Tasa de Anomalías (%)"),
            x=df_pivot.columns.astype(str),
            y=df_pivot.index,
            aspect="auto",
            color_continuous_scale="Reds",
            title="Heatmap: Tasa de Anomalías por Variable y Fecha"
        )
        
        fig.update_layout(height=600)
        st.plotly_chart(fig, use_container_width=True)
        
        st.info("""
        **Cómo se ve esta visualización:**
        
        Este es un heatmap (mapa de calor) donde cada celda representa la tasa de anomalías 
        para una variable en una fecha específica. Los colores más intensos (rojos) indican 
        mayores tasas de anomalías. Las filas son variables y las columnas son fechas.
        
        **Elementos clave para el front-end:**
        - Matriz de colores con escala de intensidad
        - Tooltip al pasar el mouse sobre cada celda
        - Leyenda de colores (escala)
        - Zoom para períodos largos
        """)
        
        # Top variables con más anomalías
        st.subheader("Top Variables con Más Anomalías")
        
        df_summary = df_heatmap.groupby('variable').agg({
            'anomalias': 'sum',
            'total_puntos': 'sum'
        }).reset_index()
        
        df_summary['tasa'] = (df_summary['anomalias'] / df_summary['total_puntos'] * 100).round(2)
        df_summary = df_summary.sort_values('anomalias', ascending=False)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.dataframe(df_summary.head(10), use_container_width=True)
        
        with col2:
            # Gráfico de barras
            fig_bar = px.bar(
                df_summary.head(10),
                x='variable',
                y='anomalias',
                title='Top 10 Variables con Más Anomalías',
                labels={'anomalias': 'Total Anomalías', 'variable': 'Variable'}
            )
            fig_bar.update_layout(height=400)
            st.plotly_chart(fig_bar, use_container_width=True)

# ============================================================================
# PÁGINA 4: DISTRIBUCIÓN DE SCORES
# ============================================================================
elif page == "Visualización 3: Distribución de Scores":
    st.header("Visualización 3: Distribución de Scores de Anomalía")
    
    st.markdown("""
    ### Finalidad
    
    Entender la **distribución de severidad de las anomalías** mediante el `anomaly_score`:
    - **Clasificar severidad**: Anomalías leves vs críticas
    - **Establecer umbrales**: ¿Qué score requiere acción inmediata?
    - **Análisis estadístico**: Distribución de scores por variable
    
    ### Casos de Uso
    
    - Sistema de alertas por niveles (bajo, medio, alto, crítico)
    - Dashboard de severidad de anomalías
    - Análisis de calidad del modelo
    """)
    
    st.markdown("---")
    
    # Controles
    variable_score = st.selectbox(
        "Variable (opcional)",
        options=["Todas"] + ["ARO_FC103", "ARO_FC105", "ARO_LC101", "ARO_PC101"],
        key="score_var"
    )
    
    # Query SQL
    st.subheader("Query SQL para esta Visualización")
    
    query_score = """
        SELECT 
            anomaly_score,
            COUNT(*) as frecuencia,
            SUM(CASE WHEN is_anomaly = 1 THEN 1 ELSE 0 END) as es_anomalia
        FROM dbo.ypf_anomaly_detector
        WHERE anomaly_score IS NOT NULL
    """
    
    if variable_score != "Todas":
        query_score += f" AND variable = '{variable_score}'"
    
    query_score += """
        GROUP BY anomaly_score
        ORDER BY anomaly_score
    """
    
    st.code(query_score, language="sql")
    
    st.markdown("---")
    
    # Visualización
    st.subheader("Visualización de Ejemplo")
    
    df_score = load_data(query_score)
    
    if df_score is not None and len(df_score) > 0:
        col1, col2 = st.columns(2)
        
        with col1:
            # Histograma
            fig_hist = px.histogram(
                df_score,
                x='anomaly_score',
                y='frecuencia',
                nbins=50,
                title='Distribución de Scores de Anomalía',
                labels={'anomaly_score': 'Score de Anomalía', 'frecuencia': 'Frecuencia'}
            )
            fig_hist.update_layout(height=400)
            st.plotly_chart(fig_hist, use_container_width=True)
            
            st.info("""
            **Cómo se ve esta visualización:**
            
            Histograma que muestra la frecuencia de cada rango de scores. Permite ver 
            si hay más anomalías leves o críticas. La mayoría de los scores deberían estar 
            en el rango bajo si el sistema funciona bien.
            """)
        
        with col2:
            # Box plot por variable (si se seleccionó "Todas")
            if variable_score == "Todas":
                query_box = """
                    SELECT variable, anomaly_score
                    FROM dbo.ypf_anomaly_detector
                    WHERE anomaly_score IS NOT NULL
                    AND is_anomaly = 1
                """
                df_box = load_data(query_box)
                
                if df_box is not None and len(df_box) > 0:
                    fig_box = px.box(
                        df_box,
                        x='variable',
                        y='anomaly_score',
                        title='Distribución de Scores por Variable',
                        labels={'anomaly_score': 'Score', 'variable': 'Variable'}
                    )
                    fig_box.update_layout(height=400, xaxis_tickangle=-45)
                    st.plotly_chart(fig_box, use_container_width=True)
                    
                    st.info("""
                    **Cómo se ve esta visualización:**
                    
                    Gráfico de cajas (box plot) que muestra la distribución de scores 
                    por variable. La caja muestra el rango intercuartílico y los puntos 
                    fuera de los bigotes son valores atípicos.
                    """)
        
        # Estadísticas
        st.subheader("Estadísticas")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Score Promedio", f"{df_score['anomaly_score'].mean():.2f}")
        with col2:
            st.metric("Score Mediano", f"{df_score['anomaly_score'].median():.2f}")
        with col3:
            st.metric("Score Máximo", f"{df_score['anomaly_score'].max():.2f}")
        with col4:
            st.metric("Score Mínimo", f"{df_score['anomaly_score'].min():.2f}")
        
        # Clasificación por niveles
        st.subheader("Clasificación por Niveles de Severidad")
        
        df_score['nivel'] = pd.cut(
            df_score['anomaly_score'],
            bins=[0, 25, 50, 75, 100],
            labels=['Bajo', 'Medio', 'Alto', 'Crítico']
        )
        
        df_niveles = df_score.groupby('nivel')['frecuencia'].sum().reset_index()
        
        fig_pie = px.pie(
            df_niveles,
            values='frecuencia',
            names='nivel',
            title='Distribución por Nivel de Severidad',
            color='nivel',
            color_discrete_map={
                'Bajo': '#90EE90',
                'Medio': '#FFD700',
                'Alto': '#FF8C00',
                'Crítico': '#FF4444'
            }
        )
        st.plotly_chart(fig_pie, use_container_width=True)
        
        st.info("""
        **Cómo se ve esta visualización:**
        
        Gráfico circular (pie chart) que muestra la proporción de anomalías por nivel 
        de severidad. Los colores van de verde (bajo) a rojo (crítico), facilitando 
        la identificación rápida de la distribución de severidad.
        """)

# ============================================================================
# PÁGINA 5: TENDENCIAS TEMPORALES
# ============================================================================
elif page == "Visualización 4: Tendencias Temporales":
    st.header("Visualización 4: Tendencias Temporales de Variables")
    
    st.markdown("""
    ### Finalidad
    
    Mostrar la **evolución de valores reales vs predichos** para una variable específica:
    - **Validar predicciones**: ¿El modelo predice bien?
    - **Detectar desviaciones**: Valores reales fuera del intervalo de confianza
    - **Análisis de comportamiento**: Tendencias y patrones de la variable
    
    ### Casos de Uso
    
    - Panel de monitoreo de variable específica
    - Análisis de calidad de predicción
    - Visualización de intervalos de confianza
    """)
    
    st.markdown("---")
    
    # Controles
    col1, col2, col3 = st.columns(3)
    
    with col1:
        variable_trend = st.selectbox(
            "Variable",
            options=["ARO_FC103", "ARO_FC105", "ARO_LC101", "ARO_PC101", "ARO_TC105"],
            key="trend_var"
        )
    
    with col2:
        fecha_inicio_trend = st.date_input(
            "Fecha Inicio",
            value=datetime.now().date() - timedelta(days=7),
            key="trend_start"
        )
    
    with col3:
        fecha_fin_trend = st.date_input(
            "Fecha Fin",
            value=datetime.now().date(),
            key="trend_end"
        )
    
    # Query SQL
    st.subheader("Query SQL para esta Visualización")
    
    query_trend = f"""
        SELECT 
            ds,
            y as valor_real,
            yhat as valor_predicho,
            yhat_lower as limite_inferior,
            yhat_upper as limite_superior,
            is_anomaly,
            anomaly_score
        FROM dbo.ypf_anomaly_detector
        WHERE variable = '{variable_trend}'
          AND ds >= '{fecha_inicio_trend}'
          AND ds <= '{fecha_fin_trend}'
        ORDER BY ds
    """
    
    st.code(query_trend, language="sql")
    
    st.markdown("---")
    
    # Visualización
    st.subheader("Visualización de Ejemplo")
    
    df_trend = load_data(query_trend)
    
    if df_trend is not None and len(df_trend) > 0:
        # Gráfico de líneas con intervalo de confianza
        fig = go.Figure()
        
        # Intervalo de confianza (área sombreada)
        fig.add_trace(go.Scatter(
            x=df_trend['ds'],
            y=df_trend['limite_superior'],
            mode='lines',
            name='Límite Superior',
            line=dict(width=0),
            showlegend=False
        ))
        
        fig.add_trace(go.Scatter(
            x=df_trend['ds'],
            y=df_trend['limite_inferior'],
            mode='lines',
            name='Intervalo de Confianza (95%)',
            fill='tonexty',
            fillcolor='rgba(0,100,80,0.2)',
            line=dict(width=0),
        ))
        
        # Valor predicho
        fig.add_trace(go.Scatter(
            x=df_trend['ds'],
            y=df_trend['valor_predicho'],
            mode='lines',
            name='Valor Predicho',
            line=dict(color='blue', width=2, dash='dash')
        ))
        
        # Valor real
        fig.add_trace(go.Scatter(
            x=df_trend['ds'],
            y=df_trend['valor_real'],
            mode='lines+markers',
            name='Valor Real',
            line=dict(color='green', width=2),
            marker=dict(size=4)
        ))
        
        # Anomalías (puntos rojos)
        df_anomalies = df_trend[df_trend['is_anomaly'] == 1]
        if len(df_anomalies) > 0:
            fig.add_trace(go.Scatter(
                x=df_anomalies['ds'],
                y=df_anomalies['valor_real'],
                mode='markers',
                name='Anomalías',
                marker=dict(
                    color='red',
                    size=10,
                    symbol='x'
                )
            ))
        
        fig.update_layout(
            title=f'Tendencias Temporales: {variable_trend}',
            xaxis_title='Fecha y Hora',
            yaxis_title='Valor',
            hovermode='x unified',
            height=600,
            template='plotly_white'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.info("""
        **Cómo se ve esta visualización:**
        
        Gráfico de líneas que muestra:
        - Área sombreada: Intervalo de confianza del 95% (zona de valores esperados)
        - Línea azul punteada: Valor predicho por el modelo
        - Línea verde: Valor real observado
        - Marcas rojas (X): Puntos identificados como anomalías
        
        Cuando la línea verde sale del área sombreada o se aleja mucho de la línea azul, 
        indica una posible anomalía.
        """)
        
        # Métricas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Puntos", f"{len(df_trend):,}")
        with col2:
            st.metric("Anomalías", f"{df_trend['is_anomaly'].sum():,}")
        with col3:
            st.metric("Tasa Anomalías", f"{df_trend['is_anomaly'].mean()*100:.2f}%")
        with col4:
            st.metric("Score Promedio", f"{df_trend['anomaly_score'].mean():.2f}")

# ============================================================================
# PÁGINA 6: DASHBOARD DE ANOMALÍAS
# ============================================================================
elif page == "Visualización 5: Dashboard de Anomalías":
    st.header("Visualización 5: Dashboard Completo de Anomalías")
    
    st.markdown("""
    ### Finalidad
    
    Crear un **dashboard interactivo completo** que combine múltiples visualizaciones:
    - **Vista general**: Métricas clave y resumen
    - **Tabla filtrable**: Lista de anomalías con filtros
    - **Visualizaciones combinadas**: Múltiples gráficos en un solo panel
    
    ### Casos de Uso
    
    - Dashboard principal para operadores
    - Panel de control ejecutivo
    - Herramienta de análisis interactivo
    """)
    
    st.markdown("---")
    
    # Controles globales
    col1, col2, col3 = st.columns(3)
    
    with col1:
        fecha_inicio_dash = st.date_input(
            "Fecha Inicio",
            value=datetime.now().date() - timedelta(days=7),
            key="dash_start"
        )
    
    with col2:
        fecha_fin_dash = st.date_input(
            "Fecha Fin",
            value=datetime.now().date(),
            key="dash_end"
        )
    
    with col3:
        min_score = st.slider(
            "Score Mínimo",
            min_value=0,
            max_value=100,
            value=0,
            key="dash_score"
        )
    
    # Query SQL
    st.subheader("Query SQL para esta Visualización")
    
    query_dashboard = f"""
        SELECT 
            ds,
            variable,
            y as valor_real,
            yhat as valor_predicho,
            is_anomaly,
            anomaly_score,
            prediction_error_pct
        FROM dbo.ypf_anomaly_detector
        WHERE ds >= '{fecha_inicio_dash}'
          AND ds <= '{fecha_fin_dash}'
          AND is_anomaly = 1
          AND anomaly_score >= {min_score}
        ORDER BY anomaly_score DESC, ds DESC
    """
    
    st.code(query_dashboard, language="sql")
    
    st.markdown("---")
    
    # Visualización
    st.subheader("Visualización de Ejemplo")
    
    df_dashboard = load_data(query_dashboard)
    
    if df_dashboard is not None and len(df_dashboard) > 0:
        # Métricas principales
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Total Anomalías", f"{len(df_dashboard):,}")
        with col2:
            st.metric("Variables Afectadas", f"{df_dashboard['variable'].nunique()}")
        with col3:
            st.metric("Score Promedio", f"{df_dashboard['anomaly_score'].mean():.2f}")
        with col4:
            st.metric("Score Máximo", f"{df_dashboard['anomaly_score'].max():.2f}")
        with col5:
            st.metric("Error Promedio", f"{df_dashboard['prediction_error_pct'].mean():.2f}%")
        
        st.markdown("---")
        
        # Gráficos
        col1, col2 = st.columns(2)
        
        with col1:
            # Anomalías por variable
            df_var_count = df_dashboard.groupby('variable').size().reset_index(name='count')
            df_var_count = df_var_count.sort_values('count', ascending=False).head(10)
            
            fig_var = px.bar(
                df_var_count,
                x='variable',
                y='count',
                title='Top 10 Variables con Más Anomalías',
                labels={'count': 'Número de Anomalías', 'variable': 'Variable'}
            )
            fig_var.update_layout(height=400, xaxis_tickangle=-45)
            st.plotly_chart(fig_var, use_container_width=True)
        
        with col2:
            # Distribución de scores
            fig_score = px.histogram(
                df_dashboard,
                x='anomaly_score',
                nbins=30,
                title='Distribución de Scores de Anomalías',
                labels={'anomaly_score': 'Score', 'count': 'Frecuencia'}
            )
            fig_score.update_layout(height=400)
            st.plotly_chart(fig_score, use_container_width=True)
        
        # Tabla de anomalías
        st.subheader("Tabla de Anomalías")
        
        # Filtros adicionales
        col1, col2 = st.columns(2)
        
        with col1:
            variable_filter = st.multiselect(
                "Filtrar por Variable",
                options=df_dashboard['variable'].unique().tolist(),
                key="dash_var_filter"
            )
        
        with col2:
            limit_rows = st.number_input(
                "Límite de Filas",
                min_value=10,
                max_value=1000,
                value=100,
                step=10,
                key="dash_limit"
            )
        
        # Aplicar filtros
        df_filtered = df_dashboard.copy()
        if variable_filter:
            df_filtered = df_filtered[df_filtered['variable'].isin(variable_filter)]
        
        # Mostrar tabla
        st.dataframe(
            df_filtered.head(limit_rows)[['ds', 'variable', 'valor_real', 'valor_predicho', 'anomaly_score', 'prediction_error_pct']],
            use_container_width=True,
            height=400
        )
        
        st.info("""
        **Cómo se ve esta visualización:**
        
        Dashboard completo que combina:
        - Métricas clave en la parte superior (tarjetas con números importantes)
        - Gráficos de barras y histogramas para análisis visual
        - Tabla filtrable con todas las anomalías detectadas
        
        Permite al operario tener una vista completa del estado del sistema en un solo lugar.
        """)

# ============================================================================
# PÁGINA 7: VISTA DEL OPERARIO
# ============================================================================
elif page == "Vista del Operario":
    st.header("Vista del Operario - Dashboard de Monitoreo")
    
    st.markdown("""
    ### Finalidad
    
    Esta página muestra cómo se vería un **dashboard real desde la perspectiva del operario** 
    que necesita monitorear el proceso en tiempo real. El operario necesita:
    - Ver el estado actual del sistema de forma clara y rápida
    - Identificar anomalías críticas que requieren acción inmediata
    - Monitorear tendencias de variables clave
    - Acceder a información detallada cuando sea necesario
    
    ### Elementos Clave del Dashboard
    
    - **Alertas críticas**: Anomalías de alto score que requieren atención
    - **Estado general**: Indicadores de salud del sistema
    - **Variables críticas**: Monitoreo de variables más importantes
    - **Timeline reciente**: Evolución de las últimas horas
    - **Tabla de anomalías activas**: Lista de anomalías actuales
    """)
    
    st.markdown("---")
    
    # Simular vista del operario
    st.subheader("Estado Actual del Sistema")
    
    # Métricas principales en estilo dashboard
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div style='background-color: #f0f2f6; padding: 20px; border-radius: 10px; text-align: center;'>
            <h3 style='color: #666; margin: 0;'>Anomalías Activas</h3>
            <h1 style='color: #ff4444; margin: 10px 0;'>12</h1>
            <p style='color: #999; margin: 0;'>Últimas 24 horas</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style='background-color: #f0f2f6; padding: 20px; border-radius: 10px; text-align: center;'>
            <h3 style='color: #666; margin: 0;'>Score Crítico</h3>
            <h1 style='color: #ff8800; margin: 10px 0;'>3</h1>
            <p style='color: #999; margin: 0;'>Score > 75</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style='background-color: #f0f2f6; padding: 20px; border-radius: 10px; text-align: center;'>
            <h3 style='color: #666; margin: 0;'>Variables Monitoreadas</h3>
            <h1 style='color: #4444ff; margin: 10px 0;'>16</h1>
            <p style='color: #999; margin: 0;'>Total activas</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div style='background-color: #f0f2f6; padding: 20px; border-radius: 10px; text-align: center;'>
            <h3 style='color: #666; margin: 0;'>Tasa de Anomalías</h3>
            <h1 style='color: #00aa00; margin: 10px 0;'>5.2%</h1>
            <p style='color: #999; margin: 0;'>Últimas 24 horas</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Alertas críticas
    st.subheader("Alertas Críticas Requieren Atención")
    
    query_criticas = """
        SELECT TOP 5
            ds,
            variable,
            y as valor_real,
            yhat as valor_predicho,
            anomaly_score,
            prediction_error_pct
        FROM dbo.ypf_anomaly_detector
        WHERE is_anomaly = 1
          AND anomaly_score >= 75
          AND ds >= DATEADD(hour, -24, GETDATE())
        ORDER BY anomaly_score DESC, ds DESC
    """
    
    df_criticas = load_data(query_criticas)
    
    if df_criticas is not None and len(df_criticas) > 0:
        for idx, row in df_criticas.iterrows():
            severity_color = "#ff4444" if row['anomaly_score'] >= 90 else "#ff8800"
            
            st.markdown(f"""
            <div style='background-color: {severity_color}20; border-left: 4px solid {severity_color}; 
                        padding: 15px; margin: 10px 0; border-radius: 5px;'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <div>
                        <strong style='color: {severity_color}; font-size: 18px;'>{row['variable']}</strong>
                        <p style='margin: 5px 0; color: #666;'>{row['ds']}</p>
                        <p style='margin: 5px 0;'>Valor Real: {row['valor_real']:.2f} | Predicho: {row['valor_predicho']:.2f}</p>
                    </div>
                    <div style='text-align: right;'>
                        <h2 style='color: {severity_color}; margin: 0;'>{row['anomaly_score']:.1f}</h2>
                        <p style='margin: 0; color: #666;'>Score</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("No hay alertas críticas en las últimas 24 horas")
    
    st.markdown("---")
    
    # Timeline reciente
    st.subheader("Timeline de Anomalías - Últimas 24 Horas")
    
    query_timeline_op = """
        SELECT 
            CAST(ds AS DATE) as fecha,
            DATEPART(hour, ds) as hora,
            COUNT(*) as total_anomalias,
            AVG(anomaly_score) as score_promedio
        FROM dbo.ypf_anomaly_detector
        WHERE is_anomaly = 1
          AND ds >= DATEADD(hour, -24, GETDATE())
        GROUP BY CAST(ds AS DATE), DATEPART(hour, ds)
        ORDER BY fecha, hora
    """
    
    df_timeline_op = load_data(query_timeline_op)
    
    if df_timeline_op is not None and len(df_timeline_op) > 0:
        fig_timeline = go.Figure()
        
        fig_timeline.add_trace(go.Scatter(
            x=df_timeline_op['fecha'].astype(str) + ' ' + df_timeline_op['hora'].astype(str) + ':00',
            y=df_timeline_op['total_anomalias'],
            mode='lines+markers',
            name='Anomalías por Hora',
            line=dict(color='#ff4444', width=3),
            marker=dict(size=8, color='#ff4444')
        ))
        
        fig_timeline.update_layout(
            title='Evolución de Anomalías - Últimas 24 Horas',
            xaxis_title='Hora',
            yaxis_title='Número de Anomalías',
            height=400,
            template='plotly_white',
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_timeline, use_container_width=True)
    
    st.markdown("---")
    
    # Variables más problemáticas
    st.subheader("Variables que Requieren Atención")
    
    query_vars_problem = """
        SELECT 
            variable,
            COUNT(*) as total_anomalias,
            AVG(anomaly_score) as score_promedio,
            MAX(anomaly_score) as score_maximo
        FROM dbo.ypf_anomaly_detector
        WHERE is_anomaly = 1
          AND ds >= DATEADD(hour, -24, GETDATE())
        GROUP BY variable
        HAVING COUNT(*) > 0
        ORDER BY total_anomalias DESC, score_maximo DESC
    """
    
    df_vars_problem = load_data(query_vars_problem)
    
    if df_vars_problem is not None and len(df_vars_problem) > 0:
        col1, col2 = st.columns(2)
        
        with col1:
            # Tabla de variables
            st.dataframe(
                df_vars_problem.head(10),
                use_container_width=True,
                column_config={
                    "variable": "Variable",
                    "total_anomalias": "Anomalías",
                    "score_promedio": st.column_config.NumberColumn("Score Promedio", format="%.2f"),
                    "score_maximo": st.column_config.NumberColumn("Score Máximo", format="%.2f")
                }
            )
        
        with col2:
            # Gráfico de barras
            fig_vars = px.bar(
                df_vars_problem.head(10),
                x='variable',
                y='total_anomalias',
                title='Top Variables con Más Anomalías',
                labels={'total_anomalias': 'Número de Anomalías', 'variable': 'Variable'},
                color='score_promedio',
                color_continuous_scale='Reds'
            )
            fig_vars.update_layout(height=400, xaxis_tickangle=-45)
            st.plotly_chart(fig_vars, use_container_width=True)
    
    st.markdown("---")
    
    # Tabla de anomalías recientes
    st.subheader("Anomalías Recientes - Detalle")
    
    query_recientes = """
        SELECT TOP 20
            ds,
            variable,
            y as valor_real,
            yhat as valor_predicho,
            anomaly_score,
            prediction_error_pct,
            CASE 
                WHEN anomaly_score >= 90 THEN 'Crítico'
                WHEN anomaly_score >= 75 THEN 'Alto'
                WHEN anomaly_score >= 50 THEN 'Medio'
                ELSE 'Bajo'
            END as severidad
        FROM dbo.ypf_anomaly_detector
        WHERE is_anomaly = 1
          AND ds >= DATEADD(hour, -24, GETDATE())
        ORDER BY anomaly_score DESC, ds DESC
    """
    
    df_recientes = load_data(query_recientes)
    
    if df_recientes is not None and len(df_recientes) > 0:
        st.dataframe(
            df_recientes,
            use_container_width=True,
            height=400,
            column_config={
                "ds": "Fecha/Hora",
                "variable": "Variable",
                "valor_real": st.column_config.NumberColumn("Valor Real", format="%.2f"),
                "valor_predicho": st.column_config.NumberColumn("Valor Predicho", format="%.2f"),
                "anomaly_score": st.column_config.NumberColumn("Score", format="%.2f"),
                "prediction_error_pct": st.column_config.NumberColumn("Error %", format="%.2f"),
                "severidad": "Severidad"
            }
        )
    
    st.markdown("---")
    
    # Query SQL para esta vista
    st.subheader("Queries SQL Utilizadas en esta Vista")
    
    with st.expander("Ver Queries SQL"):
        st.code(query_criticas, language="sql")
        st.code(query_timeline_op, language="sql")
        st.code(query_vars_problem, language="sql")
        st.code(query_recientes, language="sql")
    
    st.info("""
    **Cómo se ve esta visualización desde la perspectiva del operario:**
    
    Esta es la vista principal que vería un operario en su dashboard de monitoreo. Incluye:
    
    1. **Métricas principales**: Tarjetas grandes y visibles con números clave
    2. **Alertas críticas**: Lista destacada de anomalías que requieren acción inmediata
    3. **Timeline reciente**: Gráfico de línea mostrando la evolución de las últimas 24 horas
    4. **Variables problemáticas**: Lista y gráfico de las variables con más anomalías
    5. **Tabla detallada**: Lista completa de anomalías recientes con todos los detalles
    
    El diseño debe ser claro, con colores que indiquen severidad (verde = normal, amarillo = atención, 
    rojo = crítico) y permitir al operario tomar decisiones rápidas.
    """)

# ============================================================================
# PÁGINA 8: QUERIES SQL COMUNES
# ============================================================================
elif page == "Queries SQL Comunes":
    st.header("Queries SQL Comunes")
    
    st.markdown("""
    ### Colección de Queries SQL Listas para Usar
    
    Estas queries están optimizadas y listas para usar en tu desarrollo front-end.
    """)
    
    st.markdown("---")
    
    # Query 1: Anomalías recientes
    st.subheader("1. Anomalías Recientes (Últimas 24 horas)")
    
    query1 = """
    SELECT TOP 100
        ds,
        variable,
        y as valor_real,
        yhat as valor_predicho,
        anomaly_score,
        prediction_error_pct
    FROM dbo.ypf_anomaly_detector
    WHERE is_anomaly = 1
      AND ds >= DATEADD(hour, -24, GETDATE())
    ORDER BY anomaly_score DESC, ds DESC
    """
    
    st.code(query1, language="sql")
    st.info("Útil para: Dashboard principal, alertas recientes")
    
    st.markdown("---")
    
    # Query 2: Resumen por variable
    st.subheader("2. Resumen de Anomalías por Variable")
    
    query2 = """
    SELECT 
        variable,
        COUNT(*) as total_puntos,
        SUM(CASE WHEN is_anomaly = 1 THEN 1 ELSE 0 END) as total_anomalias,
        CAST(SUM(CASE WHEN is_anomaly = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS DECIMAL(5,2)) as tasa_anomalias,
        AVG(CASE WHEN is_anomaly = 1 THEN anomaly_score ELSE NULL END) as score_promedio,
        MAX(CASE WHEN is_anomaly = 1 THEN anomaly_score ELSE NULL END) as score_maximo
    FROM dbo.ypf_anomaly_detector
    WHERE ds >= DATEADD(day, -7, GETDATE())
    GROUP BY variable
    HAVING SUM(CASE WHEN is_anomaly = 1 THEN 1 ELSE 0 END) > 0
    ORDER BY total_anomalias DESC
    """
    
    st.code(query2, language="sql")
    st.info("Útil para: Panel de resumen, comparación de variables")
    
    st.markdown("---")
    
    # Query 3: Anomalías por rango de fechas
    st.subheader("3. Anomalías por Rango de Fechas")
    
    query3 = """
    SELECT 
        CAST(ds AS DATE) as fecha,
        DATEPART(hour, ds) as hora,
        COUNT(*) as total_anomalias,
        AVG(anomaly_score) as score_promedio
    FROM dbo.ypf_anomaly_detector
    WHERE is_anomaly = 1
      AND ds >= '2024-01-01'
      AND ds <= '2024-01-31'
    GROUP BY CAST(ds AS DATE), DATEPART(hour, ds)
    ORDER BY fecha, hora
    """
    
    st.code(query3, language="sql")
    st.info("Útil para: Análisis temporal, patrones horarios")
    
    st.markdown("---")
    
    # Query 4: Top anomalías críticas
    st.subheader("4. Top Anomalías Críticas (Score > 75)")
    
    query4 = """
    SELECT TOP 50
        ds,
        variable,
        y as valor_real,
        yhat as valor_predicho,
        yhat_lower,
        yhat_upper,
        anomaly_score,
        prediction_error_pct,
        CASE 
            WHEN anomaly_score >= 90 THEN 'Crítico'
            WHEN anomaly_score >= 75 THEN 'Alto'
            ELSE 'Medio'
        END as severidad
    FROM dbo.ypf_anomaly_detector
    WHERE is_anomaly = 1
      AND anomaly_score >= 75
    ORDER BY anomaly_score DESC, ds DESC
    """
    
    st.code(query4, language="sql")
    st.info("Útil para: Sistema de alertas, priorización")
    
    st.markdown("---")
    
    # Query 5: Estadísticas diarias
    st.subheader("5. Estadísticas Diarias")
    
    query5 = """
    SELECT 
        CAST(ds AS DATE) as fecha,
        COUNT(*) as total_puntos,
        SUM(CASE WHEN is_anomaly = 1 THEN 1 ELSE 0 END) as total_anomalias,
        COUNT(DISTINCT variable) as variables_unicas,
        AVG(anomaly_score) as score_promedio,
        MAX(anomaly_score) as score_maximo
    FROM dbo.ypf_anomaly_detector
    WHERE ds >= DATEADD(day, -30, GETDATE())
    GROUP BY CAST(ds AS DATE)
    ORDER BY fecha DESC
    """
    
    st.code(query5, language="sql")
    st.info("Útil para: Reportes diarios, tendencias")
    
    st.markdown("---")
    
    # Query 6: Anomalías por variable específica
    st.subheader("6. Anomalías de una Variable Específica")
    
    query6 = """
    SELECT 
        ds,
        y as valor_real,
        yhat as valor_predicho,
        yhat_lower,
        yhat_upper,
        is_anomaly,
        anomaly_score,
        prediction_error_pct
    FROM dbo.ypf_anomaly_detector
    WHERE variable = 'ARO_FC103'
      AND ds >= DATEADD(day, -7, GETDATE())
    ORDER BY ds
    """
    
    st.code(query6, language="sql")
    st.info("Útil para: Monitoreo de variable específica, análisis detallado")
    
    st.markdown("---")
    
    # Tips de optimización
    st.subheader("Tips de Optimización")
    
    st.markdown("""
    - **Usa índices**: Siempre filtra por `ds`, `variable`, o `is_anomaly` para mejor performance
    - **Límites**: Usa `TOP` o `LIMIT` para evitar cargar demasiados datos
    - **Agregaciones**: Prefiere agregaciones en SQL antes que en el front-end
    - **Fechas**: Usa rangos de fechas específicos en lugar de `GETDATE()` cuando sea posible
    - **Paginación**: Implementa paginación con `OFFSET` y `FETCH` para tablas grandes
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p>Guía de Desarrollo Front-End - Detección de Anomalías YPF</p>
    <p>Tabla: <code>otms_analytics.dbo.ypf_anomaly_detector</code></p>
</div>
""", unsafe_allow_html=True)
