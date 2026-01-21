# Sistema de Detección de Anomalías - YPF

Sistema completo de detección de anomalías en tiempo real para variables de proceso industrial utilizando **Facebook Prophet**. El sistema está diseñado para integrarse con SQL Server y proporcionar detección continua de anomalías.

## Características Principales

- **Detección en Tiempo Real**: Procesamiento continuo de datos nuevos
- **Modelos Prophet**: Un modelo por variable con estacionalidad diaria y semanal
- **Integración SQL Server**: Lectura y escritura en bases de datos separadas
- **Workers Automáticos**: Procesamiento incremental y reentrenamiento automático
- **Dashboard Streamlit**: Guía completa para desarrolladores front-end
- **Métricas de Evaluación**: Sistema completo de evaluación de modelos

## Tabla de Contenidos

- [Arquitectura](#arquitectura)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Uso Rápido](#uso-rápido)
- [Documentación](#documentación)
- [Estructura del Proyecto](#estructura-del-proyecto)

## Arquitectura

El sistema utiliza una arquitectura en capas:

```
┌─────────────────────────────────────────┐
│   SQL Server (Datos)                     │
│   • otms_main.ypf_process_data          │
│   • otms_analytics.ypf_anomaly_detector │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│   Capa de Aplicación                     │
│   • ProphetAnomalyDetector               │
│   • SQLConnection                        │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│   Capa de Procesamiento                 │
│   • Workers (tiempo real)               │
│   • Scripts batch                       │
└─────────────────────────────────────────┘
```

Para más detalles, ver [ARQUITECTURA.md](ARQUITECTURA.md)

## Instalación

### Requisitos

- Python 3.8+
- SQL Server (con acceso a las bases de datos)
- ODBC Driver 17 for SQL Server

### Instalación de Dependencias

```bash
# Instalar dependencias principales
pip install -r requirements_sql.txt

# Para el dashboard Streamlit (opcional)
pip install -r requirements_streamlit.txt
```

### Dependencias Principales

- `pandas>=1.5.0` - Manipulación de datos
- `numpy>=1.23.0` - Cálculos numéricos
- `prophet>=1.1.0` - Modelos de series temporales
- `pyodbc>=4.0.0` - Conexión a SQL Server
- `streamlit>=1.28.0` - Dashboard (opcional)
- `plotly>=5.17.0` - Visualizaciones (opcional)

## Configuración

### Configuración de Base de Datos

El sistema requiere dos bases de datos:

1. **Base de Datos de Entrada**: `otms_main`
   - Tabla: `ypf_process_data`
   - Formato: `(datetime, variable_name, value)`

2. **Base de Datos de Salida**: `otms_analytics`
   - Tabla: `ypf_anomaly_detector`
   - Contiene resultados de detección

### Configuración de Conexión

Edita los archivos de configuración SQL en:
- `detect_from_sql.py`
- `train_from_sql.py`
- `worker_procesamiento.py`
- `worker_reentrenamiento.py`

```python
SQL_CONFIG_INPUT = {
    'server': 'tu_servidor',
    'database': 'otms_main',
    'username': 'usuario',
    'password': 'contraseña',
    'port': 1433
}

SQL_CONFIG_OUTPUT = {
    'server': 'tu_servidor',
    'database': 'otms_analytics',
    'username': 'usuario',
    'password': 'contraseña',
    'port': 1433
}
```

## Uso Rápido

### 1. Entrenar Modelos

```bash
# Desde SQL Server
python train_from_sql.py

# Desde archivos CSV
python pipeline/scripts/train_anomaly_detector.py
```

### 2. Detectar Anomalías

```bash
# Procesamiento batch (todos los datos)
python detect_from_sql.py

# Procesamiento en tiempo real (worker)
python worker_procesamiento.py
```

### 3. Evaluar Modelos

```bash
python evaluar_modelo.py
```

### 4. Dashboard de Guía Front-End

```bash
streamlit run guia_frontend_streamlit.py
```

## Documentación

- **[ARQUITECTURA.md](ARQUITECTURA.md)**: Arquitectura completa del sistema
- **[README_SQL.md](README_SQL.md)**: Guía de integración con SQL Server
- **[README_WORKER.md](README_WORKER.md)**: Documentación de workers
- **[README_TIEMPO_REAL.md](README_TIEMPO_REAL.md)**: Procesamiento en tiempo real

## Estructura del Proyecto

```
ypf_anomalies_detector/
├── pipeline/
│   ├── scripts/
│   │   ├── prophet_anomaly_detector.py    # Clase principal
│   │   ├── train_anomaly_detector.py      # Entrenamiento
│   │   └── detect_anomalies.py            # Detección
│   ├── models/
│   │   └── prophet/                       # Modelos entrenados
│   └── results/                          # Resultados
├── sql_utils.py                           # Utilidades SQL
├── train_from_sql.py                      # Entrenar desde SQL
├── detect_from_sql.py                     # Detectar desde SQL
├── worker_procesamiento.py                # Worker principal
├── worker_reentrenamiento.py              # Worker reentrenamiento
├── evaluar_modelo.py                      # Evaluación de modelos
├── guia_frontend_streamlit.py             # Dashboard Streamlit
├── requirements_sql.txt                   # Dependencias SQL
├── requirements_streamlit.txt             # Dependencias Streamlit
└── README.md                              # Este archivo
```

## Componentes Principales

### ProphetAnomalyDetector

Clase principal para detección de anomalías:

```python
from pipeline.scripts.prophet_anomaly_detector import ProphetAnomalyDetector

detector = ProphetAnomalyDetector(
    interval_width=0.95,
    anomaly_threshold=2.0
)

# Entrenar
detector.train_multiple_variables(df, variables)

# Detectar
results = detector.detect_anomalies_multiple(df, variables)
```

### SQLConnection

Utilidad para conexión a SQL Server:

```python
from sql_utils import SQLConnection

conn = SQLConnection(server, database, username, password, port)
conn.connect()

# Leer datos
df = conn.execute_query("SELECT * FROM tabla")

# Escribir datos
conn.write_dataframe(df, "tabla")
```

## Resultados

El sistema genera los siguientes campos:

- `ds`: Fecha y hora del dato
- `y`: Valor real observado
- `yhat`: Valor predicho por el modelo
- `yhat_lower/upper`: Intervalo de confianza (95%)
- `is_anomaly`: Indicador de anomalía (0/1)
- `anomaly_score`: Score de anomalía (0-100)
- `variable`: Nombre de la variable
- `residual`: Diferencia entre real y predicho

## Flujo de Trabajo

### Modo Batch

1. Leer datos desde SQL
2. Transformar formato (largo → ancho)
3. Cargar modelos Prophet
4. Detectar anomalías
5. Escribir resultados a SQL

### Modo Tiempo Real

1. Worker verifica nuevos datos cada X minutos
2. Procesa solo datos nuevos (incremental)
3. Escribe resultados inmediatamente
4. Actualiza último datetime procesado

## Dashboard Streamlit

El dashboard `guia_frontend_streamlit.py` proporciona:

- Visualizaciones interactivas de anomalías
- Queries SQL de ejemplo
- Guía para desarrolladores front-end
- Vista del operario (dashboard real)

Ejecutar:
```bash
streamlit run guia_frontend_streamlit.py
```

## Métricas del Modelo

El sistema incluye evaluación completa:

- **MAE, RMSE, MAPE**: Métricas de predicción
- **R²**: Coeficiente de determinación
- **Cobertura del Intervalo**: Validación del 95%
- **Distribución de Scores**: Análisis de severidad

Ejecutar evaluación:
```bash
python evaluar_modelo.py
```

## Seguridad

**Importante**: No subir credenciales a Git. Usa variables de entorno o archivos de configuración locales (no versionados).

## Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## Licencia

Este proyecto es privado y confidencial.

## Autor

Andrés Ríos

## Agradecimientos

- Facebook Prophet para el modelo de series temporales
- Comunidad de Python para las librerías utilizadas
