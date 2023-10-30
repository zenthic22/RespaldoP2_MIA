import os

def command_rmdisk(params):
    path = None
    mensaje = ""
    
    for x in params:
        param = [w.strip() for w in x.split("=")]
        
        if param[0].lower() != "path":
            mensaje += "Parametro '"+param[0]+"' no reconocido para el comando\n"
            return mensaje
        
        if len(param) < 2:
            mensaje += "Parametro 'path' necesita una direccion\n"
            return mensaje
        
        if param[1][0] == '"':
            path = param[1][1:-1]
        else:
            path = param[1]
    
    if path == None:
        mensaje += "No se encontro el parametro 'path'\n"
        return mensaje
    
    if not os.path.isfile(path):
        mensaje += "No existe un disco en '"+path+"'\n"
        return mensaje
    
    os.remove(path)
    
    mensaje += "se ha eliminado el disco\n"
    return mensaje