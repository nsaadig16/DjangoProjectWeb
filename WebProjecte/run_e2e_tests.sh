#!/bin/bash

if [ -z "$VIRTUAL_ENV" ]; then
    echo "Se recomienda ejecutar las pruebas dentro de un entorno virtual"
    echo "Puedes crear uno con: python3 -m venv env"
    echo "Y activarlo con: source env/bin/activate (Linux/Mac) o env\\Scripts\\activate (Windows)"
    read -p "¿Deseas continuar de todos modos? (s/n): " response
    if [ "$response" != "s" ]; then
        exit 0
    fi
fi

# Instalar dependencias
echo "Instalando dependencias..."
pip install -r requirements_test.txt

# Ejecutar pruebas
echo "Ejecutando pruebas E2E..."
python3 -m pytest tests/e2e -v

# Mostrar resultados
echo "Pruebas finalizadas."