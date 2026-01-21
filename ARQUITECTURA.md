# Arquitectura del Sistema de Detección de Anomalías

## Visión General

El sistema de detección de anomalías utiliza **Facebook Prophet** para detectar anomalías en variables de proceso industrial. La arquitectura está diseñada para funcionar en tiempo real con datos almacenados en SQL Server.

## Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                    CAPA DE DATOS (SQL Server)                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────┐         ┌──────────────────────┐     │
│  │  otms_main           │         │  otms_analytics       │     │
│  │  ────────────────    │         │  ────────────────     │     │
│  │  ypf_process_data   │         │  ypf_anomaly_detector │     │
│  │                      │         │                      │     │
│  │  - datetime          │         │  - id (PK)           │     │
│  │  - variable_name     │         │  - ds                │     │
│  │  - value             │         │  - y (valor real)    │     │
│  │  - source_file       │         │  - yhat (predicho)   │     │
│  │  - created_at        │         │  - yhat_lower       │     │
│  └──────────────────────┘         │  - yhat_upper       │     │
│           ▲                        │  - residual         │     │
│           │                        │  - is_anomaly       │     │
│           │                        │  - anomaly_score    │     │
│           │                        │  - variable         │     │
│           │                        │  - processed_at      │     │
│           │                        └──────────────────────┘     │
│           │                                  ▲                   │
└───────────┼──────────────────────────────────┼───────────────────┘
            │                                  │
            │ LECTURA                          │ ESCRITURA
            │                                  │
┌───────────┼──────────────────────────────────┼───────────────────┐
│           │                                  │                    │
│  ┌────────▼──────────────────────────────────▼────────┐          │
│  │         CAPA DE APLICACIÓN                          │          │
│  │                                                      │          │
│  │  ┌──────────────────────────────────────────────┐   │          │
│  │  │  sql_utils.py                                │   │          │
│  │  │  - SQLConnection (clase)                     │   │          │
│  │  │    • connect()                               │   │          │
│  │  │    • execute_query()                         │   │          │
│  │  │    • write_dataframe()                       │   │          │
│  │  │    • create_table_if_not_exists()            │   │          │
│  │  └──────────────────────────────────────────────┘   │          │
│  │                                                      │          │
│  │  ┌──────────────────────────────────────────────┐   │          │
│  │  │  ProphetAnomalyDetector                       │   │          │
│  │  │  (pipeline/scripts/prophet_anomaly_detector.py)│   │          │
│  │  │                                                │   │          │
│  │  │  Métodos principales:                          │   │          │
│  │  │  • train_model() - Entrena modelo Prophet     │   │          │
│  │  │  • detect_anomalies() - Detecta anomalías     │   │          │
│  │  │  • train_multiple_variables() - Entrena varios│   │          │
│  │  │  • detect_anomalies_multiple() - Detecta varias│   │          │
│  │  │  • save_models() - Guarda modelos            │   │          │
│  │  │  • load_models() - Carga modelos             │   │          │
│  │  └──────────────────────────────────────────────┘   │          │
│  │                                                      │          │
│  └──────────────────────────────────────────────────────┘          │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    CAPA DE PROCESAMIENTO                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────┐  ┌──────────────────────┐            │
│  │  Modo Batch           │  │  Modo Tiempo Real    │            │
│  │  ─────────────        │  │  ─────────────       │            │
│  │                       │  │                      │            │
│  │  detect_from_sql.py   │  │  worker_procesamiento.py│        │
│  │  • Lee todos los datos│  │  • Verifica cada X min│            │
│  │  • Procesa todo       │  │  • Procesa solo nuevos│            │
│  │  • Escribe resultados │  │  • Escribe resultados│            │
│  │                       │  │  • Mantiene estado   │            │
│  └──────────────────────┘  └──────────────────────┘            │
│                                                                   │
│  ┌──────────────────────┐  ┌──────────────────────┐            │
│  │  Entrenamiento        │  │  Reentrenamiento     │            │
│  │  ─────────────        │  │  ─────────────       │            │
│  │                       │  │                      │            │
│  │  train_from_sql.py    │  │  worker_reentrenamiento.py│      │
│  │  • Lee datos históricos│  │  • Ejecuta diariamente│           │
│  │  • Entrena modelos    │  │  • Reentrena modelos │            │
│  │  • Guarda modelos     │  │  • Actualiza modelos │            │
│  └──────────────────────┘  └──────────────────────┘            │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    CAPA DE ALMACENAMIENTO                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  pipeline/models/prophet/                                 │   │
│  │  • prophet_model_[VARIABLE].pkl (16 modelos)            │   │
│  │  • detector_config.json (configuración)                 │   │
│  │  • variable_stats.json (estadísticas)                   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Flujo de Datos Principal

### 1. Fase de Entrenamiento (Inicial)

```
┌─────────────┐
│ Datos CSV   │
│ o SQL       │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│ write_training_data │
│ _to_sql.py          │
│                     │
│ • Lee datos CSV     │
│ • Transforma formato│
│ • Escribe a SQL     │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ otms_main           │
│ ypf_process_data   │
│ (Formato largo)     │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ train_from_sql.py   │
│                     │
│ • Lee desde SQL     │
│ • Convierte a ancho │
│ • Entrena modelos   │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ pipeline/models/    │
│ prophet/            │
│ • 16 modelos .pkl   │
└─────────────────────┘
```

### 2. Fase de Detección (Operativa)

```
┌─────────────────────┐
│ otms_main           │
│ ypf_process_data    │
│ (Nuevos datos)      │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ detect_from_sql.py  │
│ o                   │
│ worker_procesamiento│
│                     │
│ 1. Lee datos        │
│    (formato largo)  │
│                     │
│ 2. Convierte a      │
│    formato ancho    │
│                     │
│ 3. Carga modelos    │
│    Prophet          │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ ProphetAnomalyDetector│
│                     │
│ Para cada variable: │
│ • Prepara datos     │
│ • Predice (yhat)    │
│ • Calcula intervalo │
│ • Detecta anomalías │
│ • Calcula score     │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Resultados          │
│ DataFrame con:      │
│ • ds, y, yhat       │
│ • yhat_lower/upper  │
│ • is_anomaly        │
│ • anomaly_score     │
│ • variable          │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ otms_analytics      │
│ ypf_anomaly_detector│
│ (Resultados)        │
└─────────────────────┘
```

## Componentes Principales

### 1. ProphetAnomalyDetector (Núcleo del Sistema)

**Ubicación:** `pipeline/scripts/prophet_anomaly_detector.py`

**Responsabilidades:**
- Entrenar modelos Prophet por variable
- Detectar anomalías usando modelos entrenados
- Calcular scores de anomalía (0-100)
- Gestionar persistencia de modelos (guardar/cargar)

**Algoritmo de Detección:**
```python
# Para cada punto de datos:
1. Predicción: yhat = modelo.predict(fecha)
2. Intervalo: [yhat_lower, yhat_upper] (95% confianza)
3. Residual: residual = y - yhat
4. Detección:
   - outside_interval = (y < yhat_lower) OR (y > yhat_upper)
   - high_residual = |residual| > (threshold * std_residual)
   - is_anomaly = outside_interval OR high_residual
5. Score: Calculado basado en distancia al intervalo
```

### 2. SQLConnection (Capa de Datos)

**Ubicación:** `sql_utils.py`

**Responsabilidades:**
- Gestionar conexiones a SQL Server
- Ejecutar queries SELECT
- Escribir DataFrames a tablas
- Crear tablas e índices

**Características:**
- Soporte para múltiples bases de datos
- Escritura optimizada en chunks
- Manejo de errores y transacciones

### 3. Workers (Procesamiento Continuo)

**Worker de Procesamiento:** `worker_procesamiento.py`
- Verifica nuevos datos cada X minutos (configurable)
- Procesa solo datos nuevos (incremental)
- Mantiene estado del último datetime procesado
- Escribe resultados a `otms_analytics`

**Worker de Reentrenamiento:** `worker_reentrenamiento.py`
- Ejecuta diariamente a las 2:00 AM
- Reentrena todos los modelos con datos actualizados
- Actualiza modelos guardados

### 4. Scripts de Ejecución

**Modo Batch:**
- `detect_from_sql.py`: Procesa todos los datos de una vez
- `train_from_sql.py`: Entrena modelos desde SQL

**Modo Tiempo Real:**
- `worker_procesamiento.py`: Procesamiento continuo
- `procesar_tiempo_real.py`: Procesamiento en tiempo real
- `procesar_dato_individual.py`: Procesa datos individuales

## Flujo de Detección de Anomalías (Detallado)

### Paso 1: Lectura de Datos
```python
# Query SQL
SELECT datetime, variable_name, value 
FROM otms_main.dbo.ypf_process_data
WHERE datetime > 'último_procesado'
ORDER BY datetime, variable_name

# Resultado: DataFrame en formato largo
# datetime | variable_name | value
# 2024-10-01 00:00 | ARO_FC103 | 123.45
# 2024-10-01 00:00 | ARO_FC105 | 67.89
```

### Paso 2: Transformación a Formato Ancho
```python
# Pivot table
df_wide = df_long.pivot_table(
    index='datetime',
    columns='variable_name',
    values='value'
)

# Resultado: DataFrame en formato ancho
# datetime | ARO_FC103 | ARO_FC105 | ARO_LC101 | ...
# 2024-10-01 00:00 | 123.45 | 67.89 | 45.23 | ...
```

### Paso 3: Carga de Modelos
```python
detector = ProphetAnomalyDetector()
detector.load_models("pipeline/models/prophet/")
# Carga 16 modelos Prophet (uno por variable)
```

### Paso 4: Detección por Variable
```python
for variable in variables:
    # Preparar datos para Prophet
    prophet_df = prepare_data_for_prophet(df, variable)
    
    # Obtener modelo
    model = detector.models[variable]
    
    # Predecir
    forecast = model.predict(prophet_df[['ds']])
    
    # Calcular anomalías
    results = detect_anomalies(model, df, variable)
```

### Paso 5: Cálculo de Scores
```python
# Score basado en distancia al intervalo
if y > yhat_upper:
    score = ((y - yhat_upper) / (yhat_upper - yhat)) * 50
elif y < yhat_lower:
    score = ((yhat_lower - y) / (yhat - yhat_lower)) * 50

# Ajustar por residuales
score = max(score, (|residual| / std_residual) * 20)
score = clip(score, 0, 100)
```

### Paso 6: Escritura de Resultados
```python
# Preparar datos para SQL
results['is_anomaly'] = results['is_anomaly'].astype(int)
results['anomaly_score'] = results['anomaly_score'].clip(0, 100)

# Escribir a SQL
sql_conn.write_dataframe(
    results,
    table_name='ypf_anomaly_detector',
    if_exists='append'
)
```

## Configuración del Modelo Prophet

**Parámetros actuales:**
- `interval_width = 0.95` (95% intervalo de confianza)
- `changepoint_prior_scale = 0.05` (flexibilidad moderada)
- `seasonality_mode = 'multiplicative'` (mejor para datos de proceso)
- `daily_seasonality = True` (estacionalidad diaria)
- `weekly_seasonality = True` (estacionalidad semanal)
- `yearly_seasonality = False` (sin estacionalidad anual)
- `anomaly_threshold = 2.0` (2 desviaciones estándar)

## Arquitectura de Datos

### Formato de Entrada (ypf_process_data)
```
Formato LARGO (normalizado):
datetime          | variable_name    | value
2024-10-01 00:00  | ARO_FC103        | 123.45
2024-10-01 00:00  | ARO_FC105        | 67.89
2024-10-01 00:10  | ARO_FC103        | 124.12
```

### Formato de Salida (ypf_anomaly_detector)
```
Formato ANCHO (un registro por punto):
ds                | variable    | y      | yhat   | is_anomaly | anomaly_score
2024-10-01 00:00  | ARO_FC103   | 123.45 | 120.00 | 1          | 45.2
2024-10-01 00:00  | ARO_FC105   | 67.89  | 68.00  | 0          | 2.1
```

## Patrones de Uso

### Patrón 1: Procesamiento Batch
```python
# Uso: Procesar todos los datos históricos
python detect_from_sql.py

# Flujo:
1. Lee todos los datos de ypf_process_data
2. Procesa todo de una vez
3. Escribe todos los resultados
```

### Patrón 2: Procesamiento Incremental
```python
# Uso: Procesar solo datos nuevos
python worker_procesamiento.py

# Flujo:
1. Verifica último datetime procesado
2. Lee solo datos nuevos
3. Procesa incrementos
4. Actualiza último datetime
```

### Patrón 3: Procesamiento en Tiempo Real
```python
# Uso: Procesar datos tan pronto como llegan
python procesar_tiempo_real.py

# Flujo:
1. Polling cada X segundos
2. Detecta nuevos datetimes
3. Procesa inmediatamente
4. Escribe resultados
```

## Optimizaciones

### 1. Índices SQL
- `idx_ds`: Búsquedas temporales rápidas
- `idx_variable`: Filtros por variable
- `idx_is_anomaly`: Filtros de anomalías
- `idx_anomaly_score`: Ordenamiento por score

### 2. Cache de Modelos
- Modelos cargados una vez y reutilizados
- No se recargan en cada detección

### 3. Procesamiento en Chunks
- Escritura SQL en chunks de 1000 filas
- Evita problemas de memoria

### 4. Conexiones Separadas
- Conexión de entrada (lectura)
- Conexión de salida (escritura)
- Permite diferentes bases de datos

## Escalabilidad

**Actual:**
- 16 variables monitoreadas
- ~71,000 registros procesados
- Procesamiento en tiempo real

**Capacidad:**
- Soporta cientos de variables
- Millones de registros
- Procesamiento paralelo por variable

## Seguridad y Robustez

- Manejo de errores en cada capa
- Transacciones SQL (rollback en errores)
- Validación de datos antes de escribir
- Logging detallado de operaciones
- Verificación de modelos antes de usar

## Dependencias Principales

- **Prophet**: Modelos de series temporales
- **pandas**: Manipulación de datos
- **pyodbc**: Conexión a SQL Server
- **numpy**: Cálculos numéricos

