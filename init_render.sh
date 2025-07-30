#!/bin/bash

echo "🚀 Inicializando aplicación en Render..."

# Verificar drivers ODBC
echo "🔍 Verificando drivers ODBC..."
python -c "import pyodbc; print('Drivers:', pyodbc.drivers())" || echo "❌ Error verificando drivers"

# Ejecutar aplicación
echo "🎯 Iniciando Streamlit..."
streamlit run main.py --server.port=$PORT --server.address=0.0.0.0