from estructuras.Estructuras import *
from utils.Fhandler import *
import os

def command_mount(params, lista_particiones):
    path = None
    name = None
    identificador = "69"
    contenido = None
    mensaje = ""
    
    for x in params:
        param = [w.strip() for w in x.split("=")]
        
        if len(param) != 2:
            mensaje += "Error de parametro '"+param[0]+"', parametro incompleto\n"
            return mensaje
        
        if param[0].lower() == "path":
            if param[1][0] == '"':
                path = param[1][1:-1]
            else:
                path = param[1]
        
        if param[0].lower() == "name":
            name = param[1]
    
    if name == None:
        mensaje += "no se encontro el parametro obligatorio 'name'\n"
        return mensaje
    
    if path == None:
        mensaje += "No se encontro el parametro obligatorio 'path'\n"
        return mensaje
    
    if not os.path.exists(path):
        mensaje += "no existe un disco en '"+path+"'\n"
        return mensaje
    
    nombre_disco = path.rsplit("/",1)[1].split(".")[0]
    
    mbr = MBR()
    with open(path,"rb") as f:
        mbr.deserializar(f.read())
        f.close()

    part = None
    ext = False
    cont = None
    extendida = None
    for x in mbr.mbr_partition:
        if x.part_name.decode().strip('\x00') == name:
            if x.part_type.decode().upper() == "e":
                mensaje += "No se puede montar una particion extendida\n"
                return mensaje
            part = x
            break

    if part == None:
        extendida = [x for x in mbr.mbr_partition if x.part_type.decode().lower() == "e"]
        if len(extendida) != 0:
            extendida = extendida[0]
            with open(path,"rb") as f:
                f.seek(extendida.part_start)
                contenido = f.read(extendida.part_size)
                f.close()
            ebr = EBR()
            porcion = contenido 
            aceptados = ["1","0"]
            while True:
                ebr.deserializar(porcion)
                if ebr.part_name.decode().strip('\x00') == name:
                    part = ebr
                    ext = True
                    cont = contenido
                    break
                if ebr.part_status.decode() not in aceptados or ebr.part_next == -1:
                    break
                porcion = contenido[ebr.part_next:]
            

    if part == None:
        mensaje += "No existe una particion con nombre '"+name+"' en  el disco '"+nombre_disco+"'\n"
        return mensaje

    if part.part_status.decode() == "1":
        mensaje += "particion '"+name+"' ya montada\n"
        return mensaje

    part.setStatus("1")

    montadas_disco = [x for x in lista_particiones if x["identificador"].endswith(nombre_disco)]

    identificador += str(len(montadas_disco)+1) + nombre_disco

    if ext:
        data_serializada = part.serializar()
        pre = cont[:part.part_start-sizeEBR]
        post = cont[part.part_start-sizeEBR+len(data_serializada):]
        cont = pre+data_serializada+post

        contenido = cont[part.part_start:part.part_start+part.part_size]
        with open(path,'r+b') as d:
            pre = d.read()[:extendida.part_start]
            d.seek(0)
            post = d.read()[extendida.part_start+extendida.part_size:]
            d.seek(0)
            d.write(pre+cont+post)
            d.close()

        data_serializada = mbr.serializar()

        with open(path,'r+b') as d:
            post = d.read()[len(data_serializada):]
            d.seek(0)
            d.write(data_serializada)
            d.write(post)
            d.close()
            
    else:
        with open(path,"rb") as f:
            f.seek(part.part_start)
            contenido = f.read(part.part_size)
            f.close()

        data_serializada = mbr.serializar()

        with open(path,'r+b') as d:
            post = d.read()[len(data_serializada):]
            d.seek(0)
            d.write(data_serializada)
            d.write(post)
            d.close()

    contenido = mSb(contenido)
    lista_particiones.append({"identificador":identificador, "nombre":name, "path": path,"datos":contenido, "particion": part})
    mensaje += "Particion '"+name+"' montada con exito, identificador generado: "+identificador+"\n"
    return mensaje