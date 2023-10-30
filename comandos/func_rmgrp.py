from estructuras.Estructuras import *
from utils.Fhandler import *

def command_rmgrp(params, lista_particiones, sesion_activa):
    name = None
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
        
        if param[0].lower() == "name":
            if param[1][0] == '"':
                name = param[1][1:-1]
            else:
                name = param[1]
    
    if not name:
        mensaje += "no se encontro el parametro obligatorio 'name'\n"
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
    grupo = None
    
    try:
        grupo = [x for x in grupos if x[2] == name][0]
    except:
        mensaje += "no existe el grupo con nombre '"+name+"' entre los grupos creados\n"
        return mensaje
    
    usuarios_grupo = [x for x in usuarios if x[2] == name and x[0] != "0"]
    
    if len(usuarios_grupo) > 0:
        mensaje += "no se puede eliminar el grupo con nombre '"+name+"' porque tiene usuarios activos\n"
        return mensaje
    
    texto = ""
    
    for linea in usuarios:
        for palabra in linea:
            texto += palabra+","
        texto = texto[:-1]+"\n"
    
    for linea in grupos:
        if linea == grupo:
            continue
        for palabra in linea:
            texto += palabra+","
        texto = texto[:-1]+"\n"
    
    texto += "0,"+grupo[1]+","+grupo[2]+"\n"
    
    res[0]["datos"] = escribir_archivo("/users.txt", res[0]["datos"], texto)
    
    mensaje += "grupo '"+name+"' eliminado con exito\n"
    return mensaje