import os
from dotenv import load_dotenv
import discord
import asyncio
from discord.ext import commands
import mysql.connector

load_dotenv()
TOKEN = os.getenv("TOKEN")

#tenemos las variables en un archivo .env en la misma carpeta que este archivo .py
conexion = mysql.connector.connect(host="mysql_db", user= os.getenv("MYSQL_USER"), password= os.getenv("MYSQL_PASSWORD"), database=os.getenv("MYSQL_DATABASE"))
cursor = conexion.cursor()
intents = discord.Intents.default()
intents.all()
intents.message_content = True  
intents.members = True
intents.reactions = True

#Instanciamos el bot, el comando help lo reescribiremos mas adelante
bot = commands.Bot(command_prefix='!', intents=intents)
bot.remove_command('help')

#para el grupo seleccionado, muestra el primer miembro
consultaEsLider= """SELECT Grupos_Miembros.id_miembro
            FROM Grupos_Miembros
            JOIN Grupos ON Grupos_Miembros.id_grupo = Grupos.id_grupo
            Where Grupos_Miembros.id_grupo = %(idGrupo)s
            ORDER BY fecha_unido ASC
            LIMIT 1;"""

#para el grupo seleccionado, busca el miembro exacto
consultaEsMiembro = """SELECT Grupos_Miembros.id_miembro
            FROM Grupos_Miembros
            JOIN Grupos ON Grupos_Miembros.id_grupo = Grupos.id_grupo
            Where Grupos_Miembros.id_grupo = %(idGrupo)s
            ORDER BY fecha_unido ASC;"""

#El rol que queremos que tenga permiso para crear su grupo
def verificado_required():
    async def predicate(ctx):
        verificado_role = discord.utils.get(ctx.guild.roles, id= int(os.getenv("VERIFIED_ROL_ID")))
        if verificado_role in ctx.author.roles:
            return True
        else:
            await ctx.send("Debes tener el rol 'verificado' para ejecutar este comando.")
            return False
    return commands.check(predicate)
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"El bot está saturado, por favor espera {error.retry_after:.2f} segundos.")


def esMiembro(ctx,grupo: discord.Role):
    cursor.execute(consultaEsMiembro,{'idGrupo':str(grupo.id)})
    miembros = cursor.fetchall()
    if miembros is not None:
        if miembros[0][0] == str(ctx.author.id) or len(miembros) == 1:
            pass
        else:
            for i in range(len(miembros)):
                if i is len(miembros):
                    continue
                else:
                    if miembros[i][0] == str(ctx.author.id):
                        return True
    return False

def esLider(ctx):
    roles = ctx.guild.roles
    for rol in roles:
        cursor.execute(consultaEsLider,{'idGrupo':str(rol.id)})
        primerMiembro = cursor.fetchone()
        if primerMiembro is not None:
            if primerMiembro[0] == str(ctx.author.id):
                print("se encontro un rol")
                return rol
    print("no se encontró el rol")
    return None

#Evento cuando el bot está listo
@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user.name}')
    actividad = discord.Game(name="!ayuda")
    # Establece la presencia del bot
    await bot.change_presence(activity=actividad)

async def crear_grupo(ctx,*nombres):
    print("El usuario "+str(ctx.author.name)+" esta entrando a la funcion crear grupo")
    nombre_grupo = ' '.join(nombres).lower()
    if esLider(ctx) is None:
        try:
            rol_ya_existe = discord.utils.get(ctx.guild.roles, name=nombre_grupo)
            categoria_existente = discord.utils.get(ctx.guild.categories, name=nombre_grupo)
            consulta = "SELECT nombre_grupo FROM Grupos WHERE nombre_grupo = %(nombre)s;"
            cursor.execute(consulta, {'nombre': str(nombre_grupo)})
            respuestaSQL = cursor.fetchone()
            print(str(respuestaSQL))
            if rol_ya_existe is None and categoria_existente is None and respuestaSQL is None:
                #vemos si el usuario ya existe en la base de datos
                consulta = "SELECT id_miembro FROM Miembros WHERE id_miembro = %(id_miembro)s;"
                cursor.execute(consulta, {'id_miembro': str(ctx.author.id)})
                resultado=cursor.fetchone()
                # Crea el rol con el nombre proporcionado y con su categoria
                nuevo_rol = await ctx.guild.create_role(name=nombre_grupo)
                await ctx.author.add_roles(nuevo_rol)
                nueva_categoria = await ctx.guild.create_category_channel(nombre_grupo)
                await ctx.guild.create_text_channel('general', category=nueva_categoria)
                await ctx.guild.create_voice_channel(nombre_grupo, category=nueva_categoria)
                #Ahora modificamos el orden de la categorias
                categorias = ctx.guild.categories

                #la ultima categoria (la que acabamos de crear) la movemos a la posicion que queramos variando la variable position
                await categorias[len(categorias)-1].edit(position=1)# no hace falta mover todas manualmente, al cambiar la pos de una desplaza el resto automatico

                #Asignacion de permisos
                verificado = discord.utils.get(ctx.guild.roles, name='verificado')
                permisoVerificado = discord.PermissionOverwrite()
                permisoVerificado.view_channel = False
                permisoVerificado.read_messages = False
                permisoVerificado.connect = False
                permisoVerificado.send_messages = False
                permisoVerificado.mention_everyone = False

                #Establecer permisos en la categoría para el nuevo rol
                permiso = discord.PermissionOverwrite()
                permiso.add_reactions = True
                permiso.attach_files = True
                permiso.connect = True
                permiso.create_instant_invite = True
                permiso.embed_links = True
                permiso.mention_everyone = True
                permiso.external_emojis = True
                permiso.external_stickers = True
                permiso.read_message_history = True
                permiso.request_to_speak = True
                permiso.send_messages = True
                permiso.send_tts_messages = True
                permiso.send_voice_messages = True
                permiso.speak = True
                permiso.stream = True
                permiso.use_application_commands = True
                permiso.use_embedded_activities = True
                permiso.use_soundboard = True
                permiso.view_channel = True
                permiso.send_messages_in_threads = True
                permiso.use_external_sounds = True
                permiso.use_voice_activation = True
                permiso.create_public_threads = True
                await nueva_categoria.set_permissions(nuevo_rol, overwrite=permiso)
                await nueva_categoria.set_permissions(verificado, overwrite=permisoVerificado)
                await ctx.send(f'Se ha creado el grupo "{nombre_grupo}". Ahora puedes invitar gente con !invitar @nombreUsuario')
                # Registramos todo en la base de datos
                if resultado is None:
                    cursor.execute("INSERT INTO Grupos (id_grupo, nombre_grupo) VALUES (%(id)s, %(nombre)s);",{'id': str(nuevo_rol.id),'nombre': str(nuevo_rol.name)})
                    cursor.execute("INSERT INTO Miembros (id_miembro, nombre_miembro) VALUES (%(id)s, %(nombre)s);",{'id': str(ctx.author.id),'nombre': str(ctx.author.name)}) #esta linea sobra
                    cursor.execute("INSERT INTO Grupos_Miembros (id_grupo, id_miembro) VALUES (%(idGrupo)s, %(idMiembro)s);",{'idGrupo': str(nuevo_rol.id),'idMiembro': str(ctx.author.id)})

                else:
                    cursor.execute("INSERT INTO Grupos (id_grupo, nombre_grupo) VALUES (%(id)s, %(nombre)s);",{'id': str(nuevo_rol.id),'nombre': str(nuevo_rol.name)})
                    cursor.execute("INSERT INTO Grupos_Miembros (id_grupo, id_miembro) VALUES (%(idGrupo)s, %(idMiembro)s);",{'idGrupo': str(nuevo_rol.id), 'idMiembro': str(ctx.author.id)})

                conexion.commit()
            else:
                await ctx.send("Ese grupo ya existe, prueba de nuevo con otro nombre")

        except Exception as e:
            await ctx.send(f'Ha habido un error al crear el grupo, habla con un admin')
    else:
        await ctx.send('Ya eres lider de un grupo, no puedes tener mas de un grupo.')#Falta añadir que te diga de que grupo supuestamente ya eres el lider

#Si eres user, se llama a esta funcion sin argumentos, borra TU grupo, Si eres administrador del server, se le pasa como argumento la etiqueta del grupo (@Elgrupo)
async def borrar_grupo(ctx, rol=None):
    async def borrar_categoria(ctx, rolName):
        categoria = discord.utils.get(ctx.guild.categories, name=rolName)
        if categoria is None:
            print("no hay ninguna categoria seleccionada")
            return
        channels = categoria.channels
        for channel in channels:
            await channel.delete()
        await categoria.delete()
    async def accionBorrado(rol):
        if rol is not None:
            consulta = """DELETE FROM Grupos_Miembros WHERE id_grupo = %(id)s;"""
            cursor.execute(consulta, {'id': str(rol.id)})
            consulta = "DELETE FROM Grupos WHERE id_grupo = %(id)s;"
            cursor.execute(consulta, {'id': str(rol.id)})
            await borrar_categoria(ctx, str(rol.name))
            await rol.delete()
            conexion.commit()

    if not ctx.author.guild_permissions.administrator:
        """print("no eres el dueño del server")
        rol = esLider(ctx)
        print(rol)"""
        if rol is not None:
            await accionBorrado(rol)
            await ctx.send(f"Eliminaste tu grupo")
        else:
            await ctx.send(f"No eres propietario de ningun grupo")

    else:
        """print("si eres administrador del server")
        print(type(rol))"""
        if isinstance(rol, discord.Role):
            await accionBorrado(rol)
        else:
            role_id = int(rol.strip("<@&>").strip())
            rol = discord.utils.get(ctx.guild.roles, id=role_id)
            await accionBorrado(rol)



async def cambiar_nombre_texto(ctx,*nombres):
    print("El usuario "+str(ctx.author.name)+" esta entrando a la funcion cambiar nombre texto")
    rol = esLider(ctx)
    if rol is not None:
        categoria = discord.utils.get(ctx.guild.categories, name=rol.name)
        if categoria is not None:
            canales = categoria.channels
            for canal in canales:
                print(str(canal.type))
                if str(canal.type) == "text":
                # ver esto no esta pillando los nombres separados por espacios solo por guiones # No se si esto sigue siendo así y me da flojera mirarlo lol
                    for i in range(len(nombres) - 1, -1, -1):
                        nombreAntiguoArray = nombres[:i]
                        nombreAntiguo = '-'.join(nombreAntiguoArray)
                        if canal.name == nombreAntiguo:
                            nombreNuevoArray = nombres[i:]
                            nombreNuevo = '-'.join(nombreNuevoArray)
                            await canal.edit(name=nombreNuevo)
                            await ctx.send(f"Se ha cambiado el nombre del canal de texto '{nombreAntiguo}' a '{nombreNuevo}'.")
                            return

            await ctx.send(f"No se encontró el canal especificado")
    else:
        await ctx.send(f"No puedes usar este comando si no tienes tu propio grupo")


async def cambiar_nombre_voz(ctx,*nombres):
    print("El usuario " + str(ctx.author.name) + " esta entrando a la funcion cambiar nombre voz")

    rol =esLider(ctx)
    if rol is not None:
        categoria = discord.utils.get(ctx.guild.categories, name=rol.name)
        if categoria is not None:
            canales = categoria.channels
            for canal in canales:
                #la logica aquí hace cosas muy extrañas hacer mas pruebas # No se si esto lo solucioné tampoco me acuerdo jeje
                if str(canal.type) == "voice":
                    for i in range(len(nombres) - 1, -1, -1):
                        nombreAntiguoArray = nombres[:i]
                        nombreAntiguo = ' '.join(nombreAntiguoArray)
                        print("nombre canal "+str(canal.name)+" nombre antiguo "+str(nombreAntiguo))
                        print("nombre antiguo array es "+str(nombreAntiguoArray)+" nombre antiguo es "+str(nombreAntiguo))

                        if canal.name == nombreAntiguo:
                            nombreNuevoArray = nombres[i:]
                            nombreNuevo = ' '.join(nombreNuevoArray)
                            await canal.edit(name=nombreNuevo)
                            await ctx.send(f"Se ha cambiado el nombre del canal de voz '{nombreAntiguo}' a '{nombreNuevo}'.")
                            return
            await ctx.send(f"No se encontró el canal especificado")
    else:
        await ctx.send(f"No puedes usar este comando si no tienes tu propio grupo")



async def crear_canal_texto(ctx,*nombre: str):
    rol =esLider(ctx)
    if rol is not None:
        nombreCanal = ' '.join(nombre)
        categoria = discord.utils.get(ctx.guild.categories, name=rol.name)
        if categoria is not None:
            canales_texto = [canal for canal in categoria.channels if isinstance(canal, discord.TextChannel)]
            if len(canales_texto) < 5:
                await ctx.guild.create_text_channel(name=nombreCanal, category=categoria)
                await ctx.send(f"se creo el canal de texto '{nombreCanal}'")
                return
            else:
                await ctx.send(f"Llegaste al maximo de canales de texto")

    else:
        await ctx.send(f"No puedes usar este comando si no tienes tu propio grupo")
    

async def crear_canal_voz(ctx,*nombre:str):
    rol =esLider(ctx)
    if rol is not None:
        nombreCanal = ' '.join(nombre)
        categoria = discord.utils.get(ctx.guild.categories, name=rol.name)
        if categoria is not None:
            canales_voz = [canal for canal in categoria.channels if isinstance(canal, discord.VoiceChannel)]
            if len(canales_voz) < 5:
                await ctx.guild.create_voice_channel(name=nombreCanal, category=categoria)
                await ctx.send(f"se creo el canal de voz '{nombreCanal}'")
                return
            else:
                await ctx.send(f"Llegaste al maximo de canales de audio")
    else:
        await ctx.send(f"No eres propietario de ningun grupo en el que crear canales")

async def borrar_canal_texto(ctx,*nombre: str):
    rol =esLider(ctx)
    if rol is not None:
        nombreAntiguo = '-'.join(nombre)
        categoria = discord.utils.get(ctx.guild.categories, name=rol.name)
        if categoria is not None:
            canales_texto = [canal for canal in categoria.channels if isinstance(canal, discord.TextChannel)]
            if len(canales_texto) == 1:
                await ctx.send(f"no puedes borrar el ultimo canal de texto que tienes, puedes cambiarle el nombre, mira `!ayuda cambiar nombre canal texto`")
                return
            else:
                for canal in canales_texto:
                    #print(canal.name)
                    if canal.name == nombreAntiguo:
                        await canal.delete()
                        await ctx.send(f"se borro el canal de texto '{nombreAntiguo}'")
                        return #para evitar q borre todos los canales del mismo nombre, si es que los ubiera


        await ctx.send(f"No se encontró el canal especificado")
    else:
        await ctx.send(f"No puedes usar este comando si no tienes tu propio grupo")


async def borrar_canal_voz(ctx,*nombre:str):
    rol =esLider(ctx)
    if rol is not None:
        nombreAntiguo =' '.join(nombre)
        categoria = discord.utils.get(ctx.guild.categories, name=rol.name)
        if categoria is not None:
            canales_voz = [canal for canal in categoria.channels if isinstance(canal, discord.VoiceChannel)]
            for canal in canales_voz:
                print(canal.name)
                if canal.name == nombreAntiguo:
                    await canal.delete()
                    await ctx.send(f"se borro el canal de voz '{nombreAntiguo}'")
                    return #con esto evitamos que borre todos los canales que tengan el mismo nombre
        await ctx.send(f"No se encontró el canal especificado")
    else:
        await ctx.send(f"No puedes usar este comando si no tienes tu propio grupo")

async def cambiar_nombre_grupo(ctx,*nombres):
    nombre_grupo = ' '.join(nombres).lower()
    rol = esLider(ctx)
    print("el rol es "+str(rol))
    if rol is not None:
        rol_ya_existe = discord.utils.get(ctx.guild.roles, name=nombre_grupo)
        categoria_existente = discord.utils.get(ctx.guild.categories, name=nombre_grupo)
        consulta = "SELECT nombre_grupo FROM Grupos WHERE nombre_grupo = %(nombre)s;"
        cursor.execute(consulta, {'nombre': str(nombre_grupo)})
        respuestaSQL = cursor.fetchone()
        if rol_ya_existe is None and categoria_existente is None and respuestaSQL is None:
            consulta = "UPDATE Grupos SET nombre_grupo = %(nombre)s WHERE id_grupo = %(id)s;"
            cursor.execute(consulta, {'nombre': str(nombre_grupo), 'id': str(rol.id)})
            categoria = discord.utils.get(ctx.guild.categories, name=rol.name)
            await categoria.edit(name=nombre_grupo)
            await rol.edit(name=nombre_grupo)
            conexion.commit()
            await ctx.send(f"Se cambio el nombre del grupo a '{nombre_grupo}'")
        else:
            await ctx.send(f"Ya existe un grupo con ese nombre, prueba con otro nombre")
    else:
        await ctx.send(f"No puedes usar este comando si no tienes tu propio grupo")

#funciones llamables desde discord
@bot.command(name='hola', aliases=['greet'])
@verificado_required()
async def saludo(ctx):
    await ctx.send(f'pa ti mi cola')

#solo se puede invitar desde canales publicos, buscar formas alternativas de invitar a tu grupo
#si se invita a una misma persona varias veces en el mismo string se acumulan los mensajes en el md
#añadir comportamiento por si no se reciben argumentos
@bot.command(name='invitar', aliases=['invite'])
@verificado_required()
@commands.cooldown(1, 2, commands.BucketType.default)
async def invitar(ctx,*usuarios: discord.Member):
    print("El usuario " + str(ctx.author.name) + " esta entrando a la funcion invitar")
    rol = esLider(ctx)
    tareas = []
    async def invitacion(ctx,usuario: discord.Member):
        if rol is not None:
            print("se le envia la solicitud al usuario")
            if rol in usuario.roles:
                await ctx.send(f"El usuario ya está en tu grupo")
            else:
                await usuario.send(f"'{ctx.author.name}' te ha inviado a su grupo \n¿quieres unirte al grupo'{rol.name}'? escribe SI o NO")
                def check(m):
                    return m.author == usuario and m.channel.type == discord.ChannelType.private
                try:
                    respuesta = await bot.wait_for('message', check=check, timeout=1000)
                    #await ctx.send(f"Respuesta recibida: {respuesta.content}")
                    if respuesta.content.lower() == "si" or respuesta.content.lower() == "!si":
                        try:
                            cursor.execute("INSERT INTO Miembros (id_miembro, nombre_miembro) VALUES (%(idMiembro)s, %(nombreUsuario)s);",{'idMiembro': str(usuario.id), 'nombreUsuario': str(usuario.name)})
                        except Exception as error:
                            print("El miembro ya existia en la base de datos, en la tabla miembros")
                        try:
                            cursor.execute("INSERT INTO Grupos_Miembros (id_grupo, id_miembro) VALUES (%(idGrupo)s, %(idMiembro)s);",{'idGrupo':str(rol.id), 'idMiembro':str(usuario.id)})
                        except Exception as error:
                            print("el miembro ya pertenecia al grupo")
                        await usuario.add_roles(rol)
                        conexion.commit()
                        await usuario.send(f"Te uniste al grupo :)")
                    else:
                        await usuario.send(f"No te has unido al grupo")

                except asyncio.TimeoutError:
                    print("se agoto el tiempo de espera para la respuesta")
    if rol is not None:
        print("len usuarios es")
        print(len(usuarios))
        if 0 < len(usuarios) < 6:
            for usuario in usuarios:
                print("y el usuario es" + str(usuario.name))# si falla es por esto
                tarea = invitacion(ctx, usuario)
                tareas.append(tarea)
            await ctx.message.delete()
            await ctx.author.send(f"Se enviaron las invitaciones, diles que la acepten 👀 ")
            await asyncio.gather(*tareas)
        elif len(usuarios) == 0:
            await ctx.send(f"Has olvidado etiquetar usuarios, usa `!ayuda invitar` para ver como es")
        else:
            await ctx.send(f"Estas invitando a demasiados usuarios, ve mas suave")
    else:
        await ctx.send(f"No puedes usar este comando si no tienes tu propio grupo")

@bot.command()
@verificado_required()
@commands.cooldown(1, 1, commands.BucketType.default)
async def eliminar(ctx,*miembros: discord.Member):
    print("El usuario " + str(ctx.author.name) + " esta entrando a la funcion eliminar grupo")
    rol= esLider(ctx)
    if rol is not None:
        print("imprimiendo miembros")
        print(len(miembros))
        if len(miembros) !=0:

            for miembro in miembros:
                consulta = """DELETE FROM Grupos_Miembros WHERE id_grupo = %(idGrupo)s AND id_miembro = %(idMiembro)s;"""
                cursor.execute(consulta, {'idGrupo':str(rol.id),'idMiembro': str(miembro.id)})
                await miembro.remove_roles(rol)
                conexion.commit()
            await ctx.message.delete()
            await ctx.author.send(f"Se eliminó a los usuarios de tu grupo")
        else:
            await ctx.send(f"Debes etiquetar los miembros que quieres eliminar, usa !ayuda para ver como.")

    else:
        await ctx.send(f"No puedes eliminar miembros por que no eres el propietario del grupo")

@bot.command(name='abandonar', aliases=['leave'])
@verificado_required()
@commands.cooldown(1, 2, commands.BucketType.default)
async def abandonar(ctx, palabraGrupo,grupo: discord.Role): #para que usuarios no dueños del rol lo puedan abandonar si quieren
    print("El usuario " + str(ctx.author.name) + " esta entrando a la funcion abandonar grupo")
    if palabraGrupo == "grupo" or palabraGrupo == "group":
        if esLider(ctx) == grupo or ctx.author.guild_permissions.administrator:
            print("el valor de esLider es "+str(grupo.name))
            await borrar_grupo(ctx,grupo)
            await ctx.message.delete()
            await ctx.author.send(f"abandonaste el grupo'{grupo.name}'")
        elif esMiembro(ctx,grupo):

            consulta = """DELETE FROM Grupos_Miembros
                        WHERE id_grupo = %(idGrupo)s AND id_miembro = %(idMiembro)s;"""
            cursor.execute(consulta,{'idGrupo':str(grupo.id),'idMiembro': str(ctx.author.id)})
            await ctx.author.remove_roles(grupo)
            await ctx.message.delete()
            await ctx.author.send(f"abandonaste el grupo'{grupo.name}'")
            conexion.commit()
        else:
            await ctx.message.delete()
            await ctx.send(f"no perteneces al grupo '{grupo.name}' para abandonar un grupo primero debes ser parte de él")


    else:
        await ctx.send(f"Error al escribir el comando, mira !ayuda para mas información")

#Para que todo el mundo pueda ver que tienes canales de voz y texto de tu grupo, pero no pueden entrar ni leer su contenido(creo).
#@bot.command(name='ocultar', aliases=['hide'])
@verificado_required()
async def ocultar(ctx):
    rol = esLider(ctx)
    if rol is not None:
        verificado = discord.utils.get(ctx.guild.roles, name='verificado')
        permiso = discord.PermissionOverwrite()
        permiso.view_channel = False
        categoria = discord.utils.get(ctx.guild.categories, name=rol.name)
        await categoria.set_permissions(verificado, overwrite=permiso)
    else:
        await ctx.send(f"No eres lider de un grupo, solo el lider puede usar este comando")


#@bot.command(name='mostrar', aliases=['show'])
@verificado_required()
async def mostrar(ctx):
    rol = esLider(ctx)
    if rol is not None:
        verificado = discord.utils.get(ctx.guild.roles, name='verificado')
        permiso = discord.PermissionOverwrite()
        permiso.view_channel = True
        categoria = discord.utils.get(ctx.guild.categories, name=rol.name)
        await categoria.set_permissions(verificado, overwrite=permiso)
    else:
        await ctx.send(f"No eres lider de un grupo, solo el lider puede usar este comando")



#funciones gestoras
#Para que funcione como lo hacen el resto de bots, las llamadas se hacen en lenguaje natural y estas funciones llaman a la funcion que toque

@bot.command(name='crear', aliases=['create'])
@verificado_required()
@commands.cooldown(1, 2, commands.BucketType.default)
async def crear(ctx,*argumentos):
    print("El usuario " + str(ctx.author.name) + " esta entrando a la funcion crear (la gestora)")

    stringArgumentos = ' '.join(argumentos).lower()
    if argumentos is not None:
        if argumentos[0] == "grupo" or argumentos[0] == "group":
            nuevosArgumentos = argumentos[1:]
            print(nuevosArgumentos)
            await ctx.message.delete()
            await crear_grupo(ctx,*nuevosArgumentos)
        elif "canal voz" in stringArgumentos:
            nuevosArgumentos = argumentos[2:]
            print(nuevosArgumentos)
            await crear_canal_voz(ctx,*nuevosArgumentos)
        elif "canal texto" in stringArgumentos:
            nuevosArgumentos = argumentos[2:]
            print(nuevosArgumentos)
            await crear_canal_texto(ctx,*nuevosArgumentos)

        elif "canal de voz" in stringArgumentos:
            nuevosArgumentos = argumentos[3:]
            print(nuevosArgumentos)
            await crear_canal_voz(ctx,*nuevosArgumentos)
        elif "canal de texto" in stringArgumentos:
            nuevosArgumentos = argumentos[3:]
            print(nuevosArgumentos)
            await crear_canal_texto(ctx,*nuevosArgumentos)
        elif argumentos[0] == "canal":
            nuevosArgumentos = argumentos[1:]
            await ctx.send("¿Lo quieres de texto o de voz? Escribe 'texto' o 'voz'.")
            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel
            respuesta = await bot.wait_for('message', check=check, timeout=60)  # Esperar 120 segundos como máximo
            await ctx.send(f"Se creo el canal de {respuesta.content}")
            if respuesta.content == "voz":
                await crear_canal_voz(ctx, *nuevosArgumentos)
            elif respuesta.content == "texto":
                await crear_canal_texto(ctx, *nuevosArgumentos)
        elif "voice channel" in stringArgumentos:
            nuevosArgumentos = argumentos[2:]
            print(nuevosArgumentos)
            await crear_canal_voz(ctx,*nuevosArgumentos)
        elif "text channel" in stringArgumentos:
            nuevosArgumentos = argumentos[2:]
            print(nuevosArgumentos)
            await crear_canal_texto(ctx,*nuevosArgumentos)
        else:
            await ctx.send(f"Haz escrito mal el comando, mira `!ayuda crear` para mas información")
    else:
        await ctx.send(f"Haz escrito mal el comando, mira `!ayuda crear` para mas información")


@bot.command(name='borrar', aliases=['delete'])
@verificado_required()
@commands.cooldown(1, 2, commands.BucketType.default)
async def borrar(ctx, *argumentos):
    print("El usuario " + str(ctx.author.name) + " esta entrando a la funcion borrar (la gestora)")
    await ctx.message.delete()
    stringArgumentos = ' '.join(argumentos)
    if argumentos is not None:
        if argumentos[0] == "grupo" or argumentos[0] == "group":
            print("entramos al if borrar gurpo")
            if not ctx.author.guild_permissions.administrator:
                print("ahora estamos dentro del if")
                await borrar_grupo(ctx)
                await ctx.message.delete()
            else:
                nuevosArgumentos = argumentos[1:]
                for i in range(len(nuevosArgumentos)):
                    await borrar_grupo(ctx, nuevosArgumentos[i])

        elif "canal voz" in stringArgumentos:
            nuevosArgumentos = argumentos[2:]
            print(nuevosArgumentos)
            await borrar_canal_voz(ctx, *nuevosArgumentos)
        elif "canal texto" in stringArgumentos:
            nuevosArgumentos = argumentos[2:]
            print(nuevosArgumentos)
            await borrar_canal_texto(ctx, *nuevosArgumentos)
        elif "canal de voz" in stringArgumentos:
            nuevosArgumentos = argumentos[3:]
            print(nuevosArgumentos)
            await borrar_canal_voz(ctx,*nuevosArgumentos)
        elif "canal de texto" in stringArgumentos:
            nuevosArgumentos = argumentos[3:]
            print(nuevosArgumentos)
            await borrar_canal_texto(ctx,*nuevosArgumentos)
        elif argumentos[0] == "canal":
            nuevosArgumentos = argumentos[1:]
            await ctx.send("¿Quieres borrar el canal de voz o el de texto? Escribe 'texto' o 'voz'.")
            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel
            respuesta = await bot.wait_for('message', check=check, timeout=60)  # Esperar 120 segundos como máximo
            await ctx.send(f"Respuesta recibida: {respuesta.content}")
            if respuesta.content == "voz":
                await borrar_canal_voz(ctx,*nuevosArgumentos)
            elif respuesta.content == "texto":
                await borrar_canal_texto(ctx,*nuevosArgumentos)
        elif "voice channel" in stringArgumentos:
            nuevosArgumentos = argumentos[2:]
            print(nuevosArgumentos)
            await borrar_canal_voz(ctx,*nuevosArgumentos)
        elif "text channel" in stringArgumentos:
            nuevosArgumentos = argumentos[2:]
            print(nuevosArgumentos)
            await borrar_canal_texto(ctx,*nuevosArgumentos)
        else:
            await ctx.send(f"Haz escrito mal el comando, mira `!ayuda borrar` para mas información")
    else:
        await ctx.send(f"Haz escrito mal el comando, mira `!ayuda borrar` para mas información")

@bot.command(name='cambiar', aliases=['change'])
@verificado_required()
@commands.cooldown(1, 2, commands.BucketType.default)
async def cambiar(ctx, *argumentos):
    print("El usuario " + str(ctx.author.name) + " esta entrando a la funcion cambiar (la gestora)")
    stringArgumentos = ' '.join(argumentos)
    if argumentos is not None:
        if "nombre del grupo" in stringArgumentos or "nombre de grupo" in stringArgumentos:
            nuevosArgumentos = argumentos[3:]
            await cambiar_nombre_grupo(ctx, *nuevosArgumentos)
        elif "nombre grupo" in stringArgumentos:
            nuevosArgumentos = argumentos[2:]
            await cambiar_nombre_grupo(ctx, *nuevosArgumentos)
        elif "nombre canal voz" in stringArgumentos:
            nuevosArgumentos = argumentos[3:]
            await cambiar_nombre_voz(ctx,*nuevosArgumentos)
        elif "nombre canal de voz" in stringArgumentos:
            nuevosArgumentos = argumentos[4:]
            await cambiar_nombre_voz(ctx,*nuevosArgumentos)
        elif "nombre de canal de voz" in stringArgumentos or "nombre del canal de voz" in stringArgumentos:
            nuevosArgumentos = argumentos[5:]
            await cambiar_nombre_voz(ctx,*nuevosArgumentos)
        elif "nombre canal texto" in stringArgumentos:
            nuevosArgumentos = argumentos[3:]
            await cambiar_nombre_texto(ctx,*nuevosArgumentos)
        elif "nombre canal de texto" in stringArgumentos:
            nuevosArgumentos = argumentos[4:]
            await cambiar_nombre_texto(ctx,*nuevosArgumentos)
        elif "nombre de canal de texto" in stringArgumentos or "nombre del canal de texto" in stringArgumentos:
            nuevosArgumentos = argumentos[5:]
            await cambiar_nombre_texto(ctx,*nuevosArgumentos)
        elif "group name" in stringArgumentos:
            nuevosArgumentos = argumentos[2:]
            await cambiar_nombre_grupo(ctx, *nuevosArgumentos)
        elif "voice channel name" in stringArgumentos:
            nuevosArgumentos = argumentos[3:]
            await cambiar_nombre_voz(ctx, *nuevosArgumentos)
        elif "text channel name" in stringArgumentos:
            nuevosArgumentos = argumentos[3:]
            await cambiar_nombre_texto(ctx,*nuevosArgumentos)
        else:
            await ctx.send(f"Haz escrito mal el comando, mira `!ayuda borrar` para mas información")
    else:
        await ctx.send(f"Haz escrito mal el comando, mira `!ayuda borrar` para mas información")



@bot.command()
async def obtener(ctx, *argumentos):
    pass


@bot.command(name='help', aliases=['ayuda'])
async def help(ctx, *args):
    print("El usuario " + str(ctx.author.name) + " esta pidiendo ayuda")
    
    stringArgumentos = ' '.join(args)
    if len(args) == 0:
        embed = discord.Embed(title="Comandos Disponibles", color=0x00ff00)
        embed.add_field(name="!crear grupo <nombre>", value="Crea tu propio grupo privado.", inline=False)
        embed.add_field(name="!invitar @usuario1 @usuario2...", value="Invita usuarios a tu grupo.", inline=False)
        embed.add_field(name="!eliminar @usuario1 @usuario2...", value="Elimina usuarios de tu grupo.", inline=False)
        embed.add_field(name="!abandonar grupo @grupo", value="Abandona un grupo específico.", inline=False)
        embed.add_field(name="!crear canal texto <nombre>", value="Crea un nuevo canal de texto en tu grupo.", inline=False)
        embed.add_field(name="!crear canal voz <nombre>", value="Crea un nuevo canal de voz en tu grupo.", inline=False)
        embed.add_field(name="!borrar grupo", value="Elimina por completo tu grupo.", inline=False)
        embed.add_field(name="!borrar canal texto <nombre>", value="Elimina un canal de texto de tu grupo.", inline=False)
        embed.add_field(name="!borrar canal voz <nombre>", value="Elimina un canal de voz de tu grupo.", inline=False)
        embed.add_field(name="!cambiar nombre grupo <nuevo_nombre>", value="Cambia el nombre de tu grupo.", inline=False)
        embed.add_field(name="!cambiar nombre canal voz <nombre_actual> <nuevo_nombre>", value="Cambia el nombre de un canal de voz en tu grupo.", inline=False)
        embed.add_field(name="!cambiar nombre canal texto <nombre_actual> <nuevo_nombre>", value="Cambia el nombre de un canal de texto en tu grupo.", inline=False)
        await ctx.send(embed=embed)
    elif "crear grupo" in stringArgumentos:
        embed = discord.Embed(
            title="!crear grupo",
            description="Crea tu propio grupo privado dentro del servidor. Puedes manejar este grupo casi como si fuera un servidor aparte, puedes invitar a personas que hayas conocido en este server para evitar tener que crear una llamada grupal. Solo debes escribir: `!crear grupo` `nombre del grupo`",
            color=0x00ff00
        )
        await ctx.send(embed=embed)
    elif "invitar" in stringArgumentos:
        embed = discord.Embed(
            title="!invitar",
            description="Invita a miembros del servidor a tu grupo privado, ellos deberán confirmar respondiendo al MD del bot durante el proximo minuto. Puedes invitar varias personas a la vez así `!invitar` `@usuario1` `@usuario2` `@usuario3...`",
            color=0x00ff00
        )
        await ctx.send(embed=embed)
    elif "eliminar" in stringArgumentos:
        embed = discord.Embed(
            title="!eliminar",
            description="Elimina miembros de tu grupo privado, ellos no serán notificados y no podrán volver a ver los canales a menos que tu quieras, escribeló así: `!eliminar` `@usuario`",
            color=0x00ff00
        )
        await ctx.send(embed=embed)
    elif "abandonar grupo" in stringArgumentos:
        embed = discord.Embed(
            title="!abandonar grupo",
            description="Con este comando abandonas directamente un grupo en el que estuvieras, la forma de escribirlo es `!abandonar grupo` `@Grupo`",
            color=0x00ff00
        )
        await ctx.send(embed=embed)
    elif "crear canal texto" in stringArgumentos or "crear canal de texto" in stringArgumentos:
        embed = discord.Embed(
            title="!crear canal texto",
            description="Creas un canal de texto dentro de tu grupo, solo los miembros de tu grupo pueden verlo, crealo así: `!crear canal texto` `nombre del canal`",
            color=0x00ff00
        )
        await ctx.send(embed=embed)
    elif "crear canal voz" in stringArgumentos or "crear canal de voz" in stringArgumentos:
        embed = discord.Embed(
            title="!crear canal voz",
            description="Creas un canal de voz dentro de tu grupo, solo los miembros de tu grupo pueden unirse, crealo así: `!crear canal voz` `nombre del canal`",
            color=0x00ff00
        )
        await ctx.send(embed=embed)
    elif "borrar grupo" in stringArgumentos:
        embed = discord.Embed(
            title="!borrar grupo",
            description="Expulsa a todos los miembros y borra tu grupo, no te preocupes, ahora puedes crear otro grupo, para borrar el grupo solo escribe `!borrar grupo`",
            color=0x00ff00
        )
        await ctx.send(embed=embed)
    elif "borrar canal texto" in stringArgumentos or "borrar canal de texto" in stringArgumentos:
        embed = discord.Embed(
            title="!borrar canal texto",
            description="Borras un canal de texto dentro de tu grupo, todo lo que hubiera escrito se pierde para siempre, hazlo así: `!borrar canal texto` `nombre canal`",
            color=0x00ff00
        )
        await ctx.send(embed=embed)
    elif "borrar canal voz" in stringArgumentos or "borrar canal de voz" in stringArgumentos:
        embed = discord.Embed(
            title="!borrar canal voz",
            description="Borras un canal de voz dentro de tu grupo, hazlo así: `!borrar canal voz` `nombre canal`",
            color=0x00ff00
        )
        await ctx.send(embed=embed)
    elif "cambiar nombre grupo" in stringArgumentos or "cambiar nombre del grupo" in stringArgumentos:
        embed = discord.Embed(
            title="!Cambiar nombre grupo",
            description="Cambias el nombre de tu grupo, esto cambia vuestro rol y el nombre de vuestra categoría, hazlo así: `!cambiar nombre grupo` `nombre nuevo`",
            color=0x00ff00
        )
        await ctx.send(embed=embed)
    elif "cambiar nombre canal voz" in stringArgumentos or "cambiar nombre canal de voz" in stringArgumentos:
        embed = discord.Embed(
            title="!Cambiar nombre canal voz",
            description="Cambias el nombre de uno de tus canales de voz, especifica primero el nombre antiguo y luego el nombre nuevo, hazlo así: `!cambiar nombre canal voz` `nombre antiguo` `nombre nuevo`",
            color=0x00ff00
        )
        await ctx.send(embed=embed)
    elif "cambiar nombre canal texto" in stringArgumentos or "cambiar nombre canal de texto" in stringArgumentos:
        embed = discord.Embed(
            title="!Cambiar nombre canal texto",
            description="Cambias el nombre de uno de tus canales de texto, especifica primero el nombre antiguo y luego el nombre nuevo, hazlo así: `!cambiar nombre canal texto` `nombre antiguo` `nombre nuevo`",
            color=0x00ff00
        )
        await ctx.send(embed=embed)
    elif "no puedes" in stringArgumentos:
        embed = discord.Embed(
            title="No puedes usar este comando si no tienes tu propio grupo",
            description="Si estas viendo este mensaje y estas seguro de que tienes un grupo, ponte en contancto con un admin",
            color=0x00ff00
        )
        await ctx.send(embed=embed)
    elif "crear" in stringArgumentos:
        embed = discord.Embed(title="!crear", color=0x00ff00)
        embed.add_field(name="!crear grupo", value="Crea tu propio grupo privado dentro del servidor. Puedes manejar este discord casi como si fuera un servidor aparte, puedes invitar a personas que hayas conocido en este server para evitar tener que crear una llamada grupal privada. Solo debes escribir: `!crear grupo` `nombre del grupo`", inline=False)
        embed.add_field(name="!crear canal texto", value="Creas un canal de texto dentro de tu grupo, solo los miembros de tu grupo pueden verlo, crealo así: `!crear canal texto` `nombre del canal`",inline=False)
        embed.add_field(name="!crear canal voz", value="Creas un canal de voz dentro de tu grupo, solo los miembros de tu grupo pueden verlo, crealo así: `!crear canal voz` `nombre del canal`", inline=False)
        await ctx.send(embed=embed)
    elif "borrar" in stringArgumentos:
        embed = discord.Embed(title="!borrar", color=0x00ff00)
        embed.add_field(name="!borrar grupo", value="Expulsa a todos los miembros y borra tu grupo, no te preocupes, ahora puedes crear otro grupo, para borrar el grupo solo escribe `!borrar grupo`", inline=False)
        embed.add_field(name="!borrar canal texto", value="Borras un canal de texto dentro de tu grupo, todo lo que hubiera escrito se pierde para siempre, hazlo así: `!borrar canal texto` `nombre canal`",inline=False)
        embed.add_field(name="!borrar canal voz", value="Borras un canal de voz dentro de tu grupo, hazlo así: `!borrar canal voz` `nombre canal`", inline=False)
        await ctx.send(embed=embed)
    elif "cambiar" in stringArgumentos:
        embed = discord.Embed(title="!cambiar", color=0x00ff00)
        embed.add_field(name="!cambiar nombre grupo", value="Cambias el nombre de tu grupo, esto cambia vuestro rol y el nombre de vuestra categoría, hazlo así: `!cambiar nombre grupo` `nombre nuevo`", inline=False)
        embed.add_field(name="!cambiar nombre canal texto", value="Cambias el nombre de uno de tus canales de texto, especifica primero el nombre antiguo y luego el nombre nuevo, hazlo así: `!cambiar nombre canal texto` `nombre antiguo` `nombre nuevo`",inline=False)
        embed.add_field(name="!cambiar nombre canal voz", value="Cambias el nombre de uno de tus canales de voz, especifica primero el nombre antiguo y luego el nombre nuevo, hazlo así: `!cambiar nombre canal voz` `nombre antiguo` `nombre nuevo`", inline=False)
        await ctx.send(embed=embed)


#conseguir que los canales visibles de tu rol sean inleibles, no solo si no estabas dentro previamente (historial de mensajes) #alomejor es mejor que esten ocultos para los que no sean miembros y ya está...
#modificar el comando help para variante inglés

bot.run(TOKEN)