from estructuras.Estructuras import *
from utils.Fhandler import *

def command_mkdir(params, lista_particiones, sesion_activa):
    path = None
    r = False
    mensaje = ""

    if not sesion_activa:
        mensaje += "este comando requiere una sesion activa!!\n"
        return mensaje
    
    for x in params:
        param = [w.strip() for w in x.split("=")]
        
        if param[0].lower() == "r":
            r = True
        
        elif len(param) != 2:
            mensaje += "error en el parametro '"+param[0]+"' parametro incompleto\n"
            return mensaje
        
        if param[0].lower() == "path":
            if param[1][0] == '"':
                path = param[1][1:-1]
            else:
                path = param[1]
    
    if not path:
        mensaje += "no se encontro el parametro obligatorio 'path'\n"
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
    
    conjunto = path.rsplit("/", 1)
    ruta = conjunto[0]
    archivo = conjunto[1]
    
    estado, permiso, datos = revisar_permisos(path,datos,sesion_activa)
    if estado:
        mensaje += "ya existe una carpeta con ese nombre\n"
        return mensaje
    
    if r:
        estado, datos = crear_ruta(path,datos,sesion_activa)
        if not estado:
            res[0]["datos"] = datos
            return
    
    else:
        estado, permiso, datos = revisar_permisos(ruta, datos, sesion_activa)
        res[0]["datos"] = datos
        if not estado:
            mensaje += "la ruta no existe\n"
            return mensaje
        
        if permiso[1] != "1":
            mensaje += "el usuario no tiene permiso de escritura en la carpeta "+ruta+"\n"
            return mensaje
        
        estado, datos = crear_carpeta(path,datos,sesion_activa)
        res[0]["datos"] = datos
        
        if not estado:
            mensaje += "no se pudo crear la carpeta"
            return mensaje
        
    res[0]["datos"] = datos
    mensaje += "se ha creado la carpeta '"+path+"' con exito\n"

    return mensaje