from estructuras.Estructuras import *
from utils.Fhandler import *
import os

def command_login(params, lista_particiones, sesion_activa):
    user = None
    password = None
    identificador = None
    mensaje = ""
    
    if sesion_activa:
        mensaje += "ya se ha iniciado sesion\n"
        return mensaje, sesion_activa
    
    for x in params:
        param = [w.strip() for w in x.split("=")]
        
        if len(param) != 2:
            mensaje += "error en el parametro '"+param[0]+"', parametro incompleto\n"
            return mensaje, sesion_activa
        
        if param[0].lower() == "user":
            if param[1][0] == '"':
                user = param[1][1:-1]
            else:
                user = param[1]
        
        elif param[0].lower() == "pass":
            if param[1][0] == '"':
                password = param[1][1:-1]
            else:
                password = param[1]
        
        elif param[0].lower() == "id":
            if param[1][0] == '"':
                identificador = param[1][1:-1]
            else:
                identificador = param[1]
    
    if user == None:
        mensaje += "no se encontro el parametro obligatorio 'user'\n"
        return mensaje, sesion_activa
    
    if password == None:
        mensaje += "no se encontro el parametro obligatorio 'pass'\n"
        return mensaje, sesion_activa
    
    if identificador == None:
        mensaje += "no se encontro el parametro obligatorio 'id'\n"
        return mensaje, sesion_activa
    
    res = [x for x in lista_particiones if x["identificador"] == identificador]
    if len(res) == 0:
        mensaje += "no existe el id '"+identificador+"' entre las particiones cargadas\n"
        return mensaje, sesion_activa
    
    datos = res[0]["datos"]
    estado = integridadSB(datos)
    if not estado:
        mensaje += "la particion aun no ha sido formateada\n"
        return mensaje, sesion_activa
    
    users_creados, datos = traer_archivo("/users.txt", datos)
    lineas = users_creados.split("\n")
    usuarios = [x.split(",") for x in lineas if len(x.split(",")) == 5]
    grupos = [x.split(",") for x in lineas if len(x.split(",")) == 3]
    
    try:
        usuarios = [x for x in usuarios if x[3] == user][0]
    except:
        mensaje += "no existe el usuario con el nombre '"+user+"' en la particion\n"
        return mensaje, sesion_activa
    
    if usuarios[0] == "0":
        mensaje += "el usuario con el nombre '"+user+"' ha sido borrado\n"
        return mensaje, sesion_activa
    
    if usuarios[4] != password:
        mensaje += "password incorrecto\n"
        return mensaje, sesion_activa
    
    grupo = [x for x in grupos if x[2] == usuarios[2]][0]
    
    uid = int(usuarios[0])
    gid = int(grupo[0])
    
    sesion_activa = {"particion":identificador, "user":user, "grupo":usuarios[2], "uid":uid, "gid":gid}
    mensaje += "sesion del usuario '"+user+"' iniciada con exito en el disco '"+identificador+"'\n"
    
    return mensaje, sesion_activa