# 🤖 Bot de Discord para Gestión de Grupos

Este proyecto es un bot para servidores de Discord que permite a usuarios con un rol específico gestionar sus propios grupos dentro del servidor. Estos grupos se crean como roles sobre los que los líderes tienen control completo, sin necesidad de permisos administrativos adicionales. Cada grupo cuenta con una categoría de Discord con canales de texto y de voz accesibles solo para el líder y los miembros del grupo. El líder puede utilizar comandos del bot para gestionar su categoría, añadiendo canales, invitando a otros usuarios, y realizando acciones específicas en su propio grupo.

## 🚀 Instalación

### Requisitos

- Un servidor Linux
- Docker instalado
- Docker compose

### Pasos de Instalación

1. **Clonar el repositorio** en tu servidor:
    ```bash
    git clone Link-del-repo
    cd Tu-carpeta
    ```

2. **Crear archivos `.env`** en las carpetas `docker` y `src`:
   
   - En la carpeta `docker` crear un archivo `.env` con las siguientes variables:
     ```env
     MYSQL_ROOT_PASSWORD=ejemplo_root_password
     MYSQL_USER=ejemplo_admin
     MYSQL_PASSWORD=ejemplo_password
     MYSQL_DATABASE=bot_database
     ```
   
   - En la carpeta `src` crear un archivo `.env` con las siguientes variables:
     ```env
     TOKEN='YOUR_DISCORD_BOT_TOKEN'
     MYSQL_ROOT_PASSWORD=ejemplo_root_password
     MYSQL_USER=ejemplo_admin
     MYSQL_PASSWORD=ejemplo_password
     MYSQL_DATABASE=bot_database
     VERIFIED_ROL_ID=YOUR_VERIFIED_ROLE_ID
     ```
     > 📌 Nota: Reemplaza `YOUR_DISCORD_BOT_TOKEN` y `YOUR_VERIFIED_ROLE_ID` con los valores correspondientes para tu bot y rol de Discord.

3. **Iniciar el bot** usando Docker Compose:
    ```bash
    cd docker
    docker-compose up -d
    ```

## 📁 Estructura de Carpetas

La estructura principal del proyecto es la siguiente:

```plaintext
├── docker
│   ├── .env
│   └── docker-compose.yml
├── mysql
│   ├── initSQL.sql
│   └── data
└── python
    └── src
        ├── .env
        ├── entrypoint.sh
        ├── logs
        └── main.py
```

### Explicación de Carpetas y Archivos Relevantes

- **docker**: Contiene el archivo `docker-compose.yml` necesario para levantar el contenedor del bot y de la base de datos MySQL.
  
- **mysql**: 
  - `initSQL.sql`: Contiene el script SQL de configuración inicial para la base de datos.
  - `data/`: Carpeta donde se almacenan los datos persistentes de MySQL.
  
- **python/src**:
  - `entrypoint.sh`: Script de inicio que se ejecuta cuando el contenedor del bot arranca.
  - `logs/`: Carpeta destinada a almacenar los archivos de log del bot.
  - `main.py`: Archivo principal que ejecuta la lógica del bot.

## ✨ Características

- **Creación de Grupos**: Permite a ciertos usuarios crear su propio rol y categoría de Discord.
- **Gestión de Canales**: El líder del grupo puede crear y gestionar canales dentro de su propia categoría.
- **Invitación de Miembros**: Los líderes pueden invitar a otros usuarios del servidor a unirse a sus grupos.

## 📋 Notas Adicionales

- Recuerda revisar y ajustar los permisos en Discord para asegurar que el bot funcione correctamente.
- Este bot está diseñado para delegar ciertas capacidades de administración dentro de un grupo específico, sin otorgar permisos administrativos generales a los líderes de grupo.
