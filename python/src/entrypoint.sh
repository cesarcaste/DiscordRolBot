#!/bin/sh

# Instalar dependencias
pip install python-dotenv
pip install mysql-connector-python==8.3.0 discord.py==2.3.2
pip install --upgrade pip

# Crear directorio de logs
mkdir -p /usr/src/app/logs

# Iniciar el bot de Discord
python /usr/src/app/main.py
