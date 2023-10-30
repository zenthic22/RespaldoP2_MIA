from estructuras.Estructuras import *
from utils.Fhandler import *

def command_rmusr(params, lista_particiones, sesion_activa):
    user = None
    mensaje = ""
    
    if not sesion_activa:
        mensaje += "este comando requiere una sesion activa\n"
        return mensaje
    
    if sesion_activa["user"] != "root":
        mensaje += "solo el usuario root puede realizar este comando\n"
        return mensaje
    
    for x in params:
        param = [w.strip() for w in x.split("=")]
        
        if len(param) != 2:
            mensaje += "error en el parametro '"+param[0]+"', parametro incompleto\n"
            return mensaje

        if param[0].lower() == "user":
            if param[1][0] == '"':
                user = param[1][1:-1]
            else:
                user = param[1]
    
    if not user:
        mensaje += "no se encontro el parametro obligatorio 'user'\n"
        return mensaje
    
    if user == "root":
        mensaje += "no puede eliminar el usuario root\n"
        return mensaje
    
    res = [x for x in lista_particiones if x["identificador"] == sesion_activa["particion"]]
    if len(res) == 0:
        mensaje += "no existe el id '"+sesion_activa["particion"]+"' entre las particiones cargadas\n"
        return mensaje
    
    datos = res[0]["datos"]
    estado = integridadSB(datos)
    if not estado:
        mensaje += "la particion aun no ha sido formateada\n"
        return mensaje
    
    users_creados, datos = traer_archivo("/users.txt", datos)
    lineas = users_creados.split("\n")
    usuarios = [x.split(",") for x in lineas if len(x.split(",")) == 5]
    grupos = [x.split(",") for x in lineas if len(x.split(",")) == 3]
    us = [x for x in usuarios if x[3] == user]
    
    if len(us) == 0:
        mensaje += "no existe un usuario con nombre '"+user+"' entre los usuarios creados\n"
        return mensaje
    
    us = us[0]
    grupo = [x for x in grupos if x[2] == us[2]]
    texto = ""
    
    for linea in usuarios:
        if linea == us:
            continue
        for palabra in linea:
            texto += palabra+","
        texto = texto[:-1]+"\n"
    
    texto += "0,U,"+us[2]+","+us[3]+","+us[4]+"\n"
    
    for linea in grupos:
        for palabra in linea:
            texto += palabra+","
        texto = texto[:-1]+"\n"
    
    datos = escribir_archivo("/users.txt", datos, texto)
    res[0]["datos"] = datos
    
    mensaje += "usuario '"+user+"' eliminado con exito\n"
    
    return mensaje