from estructuras.Estructuras import *
import os
from datetime import datetime

def command_mkdisk(params):
    tamanio = None
    unidad = 1024*1024
    path = None
    fit = 'F'
    mensaje = ""
    for x in params:
        param = [w.strip() for w in x.split("=")]
        
        if len(param) != 2:
            mensaje += "Error en el parametro '"+param[0]+"'\n"
            return mensaje
        
        if param[0].lower() == "fit":
            if param[1].lower() == "bf":
                fit = "B"
            elif param[1].lower() == "wf":
                fit = "W"
            elif param[1].lower() == "ff":
                pass
            else:
                mensaje += "Error en el parametro 'fit', ajuste '"+param[1]+"' no reconocido\n"
                return mensaje
        
        if param[0].lower() == "size":
            try:
                tamanio = int(param[1])
            except:
                mensaje += "Error en el parametro 'size', se esperaba un numero entero positivo\n"
                return mensaje
        
        elif param[0].lower() == "unit":
            if param[1].lower() == "k":
                unidad = 1024
            elif param[1].lower() == "m":
                pass
            else:
                mensaje += "Error en el parametro 'unit', unidad '"+param[1]+"' no reconocido\n"
                return mensaje
        
        elif param[0].lower() == "path":
            if param[1][0] == '"':
                path = param[1][1:-1]
            else:
                path = param[1]
        else:
            mensaje += f"parametro no esperado: '{param[0]}'\n"
            return mensaje
    
    if tamanio == None:
        mensaje += "No se encontro el parametro obligatorio 'size'\n"
        return mensaje
    
    if tamanio <= 0:
        mensaje += "El parametro 'size' debe ser mayor que 0\n"
        return mensaje
    
    if path == None:
        mensaje += "No se encontro el parametro obligatorio 'path'\n"
        return mensaje
    
    ultimo_disco = path
    
    directorio = path.rsplit('/', 1)[0]
    
    if not os.path.exists(directorio):
        os.makedirs(directorio)
        
    tamanio_bytes = tamanio*unidad
    fecha_creacion = datetime.now()
    new_mbr = MBR()
    
    new_mbr.setAll(tamanio_bytes,fecha_creacion.strftime("%d/%m/%Y %H:%M:%S"), int(fecha_creacion.timestamp()), fit)
    serializar = new_mbr.serializar()
    
    with open(path, 'wb') as d:
        d.write(serializar)
        d.write(b'\0'*(tamanio_bytes-len(serializar)))
        d.close()
    
    
    mensaje += f"disco creado exitosamente en la ruta {ultimo_disco}\n"
    
    return mensaje