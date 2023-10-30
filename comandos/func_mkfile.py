from estructuras.Estructuras import *
from utils.Fhandler import *
import os

def command_mkfile(params, lista_particiones, sesion_activa):
    path = None
    r = False
    size = 0
    cont = None
    
    cadena = "0123456789"
    texto_archivo = ""
    
    mensaje = ""
    
    if not sesion_activa:
        mensaje += "este comando requiere una sesion activa\n"
        return mensaje
    
    for x in params:
        param = [w.strip() for w in x.split("=")]
        
        if param[0].lower() == "r":
            r = True
        elif len(param) != 2:
            mensaje += "error en el parametro '"+param[0]+"', parametro incompleto\n"
            return mensaje
        
        if param[0].lower() == "path":
            if param[1][0] == '"':
                path = param[1][1:-1]
            else:
                path = param[1]
        
        if param[0].lower() == "size":
            try:
                size = int(param[1])
            except:
                mensaje += "size debe ser un numero positivo\n"
                return mensaje
        
        if param[0].lower() == "cont":
            if param[1][0] == '"':
                cont = param[1][1:-1]
            else:
                cont = param[1]
        
    if not path:
        mensaje += "no se encontro el parametro obligatorio 'path'\n"
        return mensaje
    
    texto_archivo = cadena*int(size/10)+cadena[:(size%10)]
    
    if cont:
        if not os.path.exists(cont):
            mensaje += "no existe un archivo en la ruta '"+cont+"'\n"
            return mensaje
        
        with open(cont, "r") as f:
            texto_archivo = f.read()
            f.close()
    
    res = [x for x in lista_particiones if x["identificador"] == sesion_activa["particion"]]
    if len(res) == 0:
        mensaje += "no existe el id '"+sesion_activa["particion"]+"' entre las particiones cargadas\n"
        return mensaje
    
    datos = res[0]["datos"]
    estado = integridadSB(datos)
    if not estado:
        mensaje += "la particion aun no ha sido formateada\n"
        return mensaje
    
    conjunto = path.rsplit("/",1)
    ruta = conjunto[0]
    archivo = conjunto[1]
    
    estado, permiso, datos = revisar_permisos(path, datos, sesion_activa)
    if estado:
        mensaje += "ya existe un archivo con ese nombre\n"
        return mensaje
    
    if r:
        estado, datos = crear_ruta(ruta,datos,sesion_activa)
        if not estado:
            res[0]["datos"] = datos
            return
    
        estado, datos = crear_archivo(path,datos,sesion_activa)
        if not estado:
            res[0]["datos"] = datos
            mensaje += "no se pudo crear el archivo\n"
            return mensaje
    
    else:
        estado, permiso, datos = revisar_permisos(ruta,datos,sesion_activa)
        res[0]["datos"] = datos
        if not estado:
            mensaje += "la ruta no existe\n"
            return mensaje
        
        if permiso[1] != "1":
            mensaje += "el usuario no tiene permiso de escritura en la carpeta "+ruta
            return mensaje
        
        estado, datos = crear_archivo(path,datos,sesion_activa)
        res[0]["datos"] = datos
        if not estado:
            mensaje += "no se puede crear el archivo\n"
            return mensaje
    
    datos = escribir_archivo(path,datos,texto_archivo)
    res[0]["datos"] = datos
    mensaje += "se ha creado el archivo '"+path+"' con exito\n"
    
    return mensaje