from estructuras.Estructuras import *
from utils.Fhandler import *
import os
#import graphviz
import codecs

def command_rep(params, lista_particiones):
    name = None
    path = None
    identificador = None
    ruta = None
    mensaje = ""
    reporte = None
    
    for x in params:
        param = [w.strip() for w in x.split("=")]
        
        if len(param) != 2:
            mensaje += "error en el parametro '"+param[0]+"', parametro incompleto\n"
            return mensaje, reporte
        
        if param[0].lower() == "name":
            if param[1][0] == '"':
                name = param[1][1:-1]
            else:
                name = param[1]
        
        if param[0].lower() == "path":
            if param[1][0] == '"':
                path = param[1][1:-1]
            else:
                path = param[1]
        
        if param[0].lower() == "id":
            if param[1][0] == '"':
                identificador = param[1][1:-1]
            else:
                identificador = param[1]
        
        if param[0].lower() == "ruta":
            if param[1][0] == '"':
                ruta = param[1][1:-1]
            else:
                ruta = param[1]
    
    if not name:
        mensaje += "no se encontro el parametro obligatorio 'name'\n"
        return mensaje, reporte
    
    if not path:
        mensaje += "no se encontro el parametro obligatorio 'path'\n"
        return mensaje, reporte
    
    if not identificador:
        mensaje += "no se encontro el parametro obligatorio 'id'\n"
        return mensaje, reporte
    
    res = [x for x in lista_particiones if x["identificador"] == identificador]
    if len(res) == 0:
        mensaje += "no existe el id '"+identificador+"' entre las particiones cargadas\n"
        return mensaje, reporte
    
    datos = res[0]["datos"]
    
    if name == "tree":
        estado = integridadSB(datos)
        if not estado:
            mensaje += "la particion aun no ha sido formateada\n"
            return mensaje, reporte
        
        s = repTree(datos)
        
        reporte = {"tipo":"g", "name":path, "rep":s}
        
    elif name == "bm_bloc":
        estado = integridadSB(datos)
        if not estado:
            mensaje += "la particion aun no ha sido formateada\n"
            return mensaje, reporte
        
        reporte = {"tipo":"t", "name":path, "rep":repBitmap(datos, "b")}
        
        
    elif name == "bm_inode":
        estado = integridadSB(datos)
        if not estado:
            mensaje += "la particion aun no ha sido formateada\n"
            return mensaje, reporte
        
        reporte = {"tipo":"t", "name":path, "rep":repBitmap(datos, "i")}
    
    elif name == "sb":
        estado, s = repSB(datos)
        if not estado:
            mensaje += "la particion aun no ha sido formateada\n"
            return mensaje, reporte
        
        reporte = {"tipo":"g", "name":path, "rep": s}
    
    elif name == "file":
        estado = integridadSB(datos)
        if not estado:
            mensaje += "la particion aun no ha sido formateada\n"
            return mensaje, reporte
        if ruta == None:
            mensaje += "no se encontro el parametro obligatorio 'ruta'\n"
            return mensaje, reporte
        
        s, datos = traer_archivo(ruta,datos)
        reporte = {"tipo":"t", "name":path, "rep":s}
    
    elif name == "disk":
        p = res[0]["path"]
        mbr = MBR()
        with open(p, "rb") as f:
            mbr.deserializar(f.read())
            f.close()
        
        reporte = {"tipo":"g", "name":path, "rep":mbr.showdisk()}
        
    elif name == "mbr":
        p = res[0]["path"]
        mbr = MBR()
        with open(p, "rb") as f:
            mbr.deserializar(f.read())
            f.close()
        
        reporte = {"tipo":"g", "name":path, "rep":mbr.imprimir(p)}
    
    else:
        mensaje += "no se reconoce el nombre del reporte\n"
        
    
    datos = res[0]["datos"]
    mensaje += "reporte creado con exito\n"

    return mensaje, reporte