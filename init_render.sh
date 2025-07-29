#!/bin/bash

echo "🚀 Inicializando aplicación en Render..."

# Verificar drivers ODBC
echo "🔍 Verificando drivers ODBC..."
python -c "import pyodbc; print('Drivers:', pyodbc.drivers())" || echo "❌ Error verificando drivers"

# Verificar variables de entorno
echo "🔧 Verificando variables de entorno..."
echo "DB_SERVER: $DB_SERVER"
echo "DB_DATABASE: $DB_DATABASE"
echo "DB_USERNAME: $DB_USERNAME"
echo "DB_DRIVER: $DB_DRIVER"

# Ejecutar aplicación
echo "🎯 Iniciando Streamlit..."
streamlit run main.py --server.port=$PORT --server.address=0.0.0.0