from estructuras.Estructuras import *
from utils.Fhandler import *

def command_logout(lista_particiones, sesion_activa):
    mensaje = ""
    
    if not sesion_activa:
        mensaje += "no hay sesion activa\n"
        return mensaje, sesion_activa
    
    res = [x for x in lista_particiones if x["identificador"] == sesion_activa["particion"]]
    if len(res) == 0:
        mensaje += "no existe el id '"+sesion_activa["particion"]+"' entre las particiones cargadas\n"
        return mensaje, sesion_activa
    
    sesion_activa = None
    
    mensaje += "se ha cerrado sesion\n"
    
    return mensaje, sesion_activa