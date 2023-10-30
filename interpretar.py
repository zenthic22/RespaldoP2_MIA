from comandos.func_mkdisk import *
from comandos.func_rmdisk import *
from comandos.func_fdisk import *
from comandos.func_mount import *
from comandos.func_mkfs import *
from comandos.func_login import *
from comandos.func_logout import *
from comandos.func_mkgrp import *
from comandos.func_rmgrp import *
from comandos.func_mkusr import *
from comandos.func_rmusr import *
from comandos.func_mkdir import *
from comandos.func_mkfile import *
from comandos.func_rep import *

particiones_montadas = []
sesion_activa = None
ultimo_disco = ''
last_response = None

def interpretar_comando(comando):
    comando = comando.split("#",1)[0].strip()
    
    if len(comando) == 0:
        return "", ""
    
    global ultimo_disco, sesion_activa, particiones_montadas
    mensaje = ""
    reporte = None
    params = [param.strip() for param in comando.split("-")]
    
    if params[0].lower() == 'mkdisk':
        mensaje = command_mkdisk(params[1:])
    elif params[0].lower() == 'rmdisk':
        mensaje = command_rmdisk(params[1:])
    elif params[0].lower() == 'fdisk':
        mensaje = command_fdisk(params[1:])
    elif params[0].lower() == 'mount':
        mensaje = command_mount(params[1:], particiones_montadas)
        print("lista de particiones montadas")
        for p in particiones_montadas:
            mensaje += "--> "+p["identificador"]
        mensaje += "\n"
    elif params[0].lower() == 'mkfs':
        mensaje = command_mkfs(params[1:], particiones_montadas)
    elif params[0].lower() == 'login':
        mensaje, sesion_activa = command_login(params[1:], particiones_montadas, sesion_activa)
        #validaremos credenciales
        # if validar_credenciales(params[1], params[2], params[3]):
        #     mensajes.append("Credenciales validas\n")
        #     mensajes.append("Recibidas: user={}, pass={}, idParticion{}\n".format(params[1], params[2], params[3]))
        # else:
        #     mensajes.append("Credenciales invalidas")
            
    elif params[0].lower() == 'logout':
        mensaje, sesion_activa = command_logout(particiones_montadas, sesion_activa)
    elif params[0].lower() == 'mkgrp':
        mensaje = command_mkgrp(params[1:], particiones_montadas, sesion_activa)
    elif params[0].lower() == 'rmgrp':
        mensaje = command_rmgrp(params[1:], particiones_montadas, sesion_activa)
    elif params[0].lower() == 'mkusr':
        mensaje = command_mkusr(params[1:], particiones_montadas, sesion_activa)
    elif params[0].lower() == 'rmusr':
        mensaje = command_rmusr(params[1:], particiones_montadas, sesion_activa)
    elif params[0].lower() == 'mkfile':
        mensaje = command_mkfile(params[1:], particiones_montadas, sesion_activa)
    elif params[0].lower() == 'mkdir':
        mensaje = command_mkdir(params[1:], particiones_montadas, sesion_activa)
    elif params[0].lower() == 'pause':
        mensaje = "programa pausado, presione cualquier tecla para continuar...\n"
    elif params[0].lower() == 'rep':
        mensaje, reporte = command_rep(params[1:], particiones_montadas)
    else:
        mensaje = "comando '"+params[0]+"' no reconocido\n"
            
    return mensaje, reporte

def ejecutar_comando(s):
    lineas = s.split("\n")
    for l in lineas:
        interpretar_comando(l)

def ejecutar(comandos):
    res = ""
    listaReportes = []
    lineas = comandos.split("\n")
    for l in lineas:
        res += l+"\n"
        res1, rep = interpretar_comando(l)
        
        if rep:
            listaReportes.append(rep)
    
    return {"consola": res, "reportes": listaReportes}

def cerrar_sesion():
    global sesion_activa
    
    sesion_activa = None
    
    print("Cerrando sesion")