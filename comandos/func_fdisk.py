from estructuras.Estructuras import *
import os

def command_fdisk(params):
    size = None
    unit = 1024
    path = None
    name = None
    fit = "W"
    _type = "P"
    skip = False
    mensaje = ""
    
    for x in params:
        param = [w.strip() for w in x.split("=")]
        if skip:
            skip = False
            continue
        
        if len(param) != 2:
            mensaje += "Error en el parametro '"+param[0]+"', parametro incompleto\n"
            return mensaje
        
        if param[0].lower() == "size":
            try:
                size = int(param[1])
            except:
                mensaje += "Error en el parametro 'size', se espera un numero entero positivo\n"
                return mensaje
        
        elif param[0].lower() == "unit":
            if param[1].lower() == "k":
                pass
            elif param[1].lower() == "m":
                unit = 1024*1024
            elif param[1].lower() == "b":
                unit = 1
            else:
                mensaje += "Error en el parametro 'unit', unidad '"+param[1]+"' no reconocida\n"
                return mensaje
            
        elif param[0].lower() == "path":
            if param[1][0] == '"':
                path = param[1][1:-1]
            else:
                path = param[1]
        
        elif param[0].lower() == "name":
            if param[1][0] == '"':
                name = param[1][1:-1]
            else:
                name = param[1]
        
        elif param[0].lower() == "type":
            if param[1][0] == '"':
                _type = param[1][1:-1]
            else:
                _type = param[1]
        
    if path == None:
        mensaje += "No se encontro el parametro obligatorio 'path'\n"
        return mensaje
    
    if name == None:
        mensaje += "No se encontro el parametro obligatorio 'name'\n"
        return mensaje
    
    if not os.path.exists(path):
        mensaje += "No exite un disco en '"+path+"'\n"
        return mensaje
    
    mbr = MBR()
    ultimo_disco = path
    
    with open(path, "rb") as f:
        mbr.deserializar(f.read())
        f.close()
        
    if size == None:
        mensaje += "No se encontro el parametro obligatorio 'size'\n"
        return mensaje
    
    if size < 0:
        mensaje += "el parametro 'size' debe ser un entero mayor o igual que 0\n"
        return mensaje
    
    for x in mbr.mbr_partition:
        if x.part_name == name:
            mensaje += "Error: ya existe una particion con el nombre '"+name+"'\n"
            return mensaje
    
    if _type.lower() == "l":
        part = [x for x in mbr.mbr_partition if x.part_type.decode().lower() == "e"]
        if len(part) == 0:
            mensaje += "Error: no se puede crear una particion logica sin una extendida\n"
            return mensaje
        
        part = part[0]
        with open(path, "rb") as f:
            f.seek(part.part_start)
            contenido = f.read(part.part_size)
            f.close()
        
        ebr = EBR()
        new_ebr = EBR()
        porcion = contenido
        aceptados = ["1", "0"]
        nombres = []
        while True:
            ebr.deserializar(porcion)
            nombres.append(ebr.part_name.decode().strip("\x00"))
            if ebr.part_status.decode() not in aceptados or ebr.part_next == -1:
                break
            porcion = contenido[ebr.part_next:]
        
        if name in nombres:
            mensaje += "Error: ya existe una particion logica con ese nombre\n"
            return mensaje
        
        porcion = contenido
        ebr.deserializar(porcion)
        rangos_ocupados = []
        inicio = 0
        size = size*unit
        indice_inicio = None
        
        if ebr.part_status.decode() not in aceptados:
            if part.part_size < sizeEBR+size:
                mensaje += "Error: no hay espacio en la particion extendida para la particion logica\n"
                return mensaje
            
            indice_inicio = 0
        else:
            while True:
                ebr.deserializar(porcion)
                rangos_ocupados.append((inicio,inicio+sizeEBR+ebr.part_size))
                inicio = inicio+sizeEBR+ebr.part_size
                if ebr.part_next == -1:
                    break
                porcion = contenido[ebr.part_next:]
        
        if indice_inicio == None:
            rangos_ocupados.sort(key=lambda x:x[0])
            longitudes = []
            f = 0
            for i in range(len(rangos_ocupados)-1):
                f = i+1
                longitudes.append((rangos_ocupados[i][1],rangos_ocupados[i+1][0]-rangos_ocupados[i][1]))
            longitudes.append((rangos_ocupados[f][1],part.part_size-rangos_ocupados[f][1]))
            
            if part.part_fit.decode() == 'F':
                for x in longitudes:
                    if x[1] >= size+sizeEBR:
                        indice_inicio = x[0]
                        break
            elif part.part_fit.decode() == 'F':
                longitudes.sort(key=lambda x:x[1]-size)
                for x in longitudes:
                    if x[1] >= size+sizeEBR:
                        indice_inicio = x[0]
                        break
            else:
                longitudes.sort(key=lambda x:x[1]-size, reverse=True)
                for x in longitudes:
                    if x[1] >= size+sizeEBR:
                        indice_inicio = x[0]
                        break
        
        if indice_inicio == None:
            error += "no hay espacio en la particion extendida para la particion logica\n"
        
        new_ebr.setAll("0",fit,indice_inicio+sizeEBR, size,-1,name)
        serializado = new_ebr.serializar()
        
        pre = contenido[:indice_inicio]
        post = contenido[indice_inicio+len(serializado):]
        contenido = pre+serializado+post
        
        if indice_inicio != 0:
            ebr.setNext(indice_inicio)
            serializado = ebr.serializar()
            pre = contenido[:ebr.part_start-sizeEBR]
            post = contenido[ebr.part_start-sizeEBR+len(serializado):]
            contenido = pre+serializado+post
        
        with open(path, 'r+b') as d:
            pre = d.read()[:part.part_start]
            d.seek(0)
            post = d.read()[part.part_start+part.part_size:]
            d.seek(0)
            d.write(pre+contenido+post)
            d.close()
        
        mensaje += "se ha creado la particion "+name+" de manera exitosa\n"
        return mensaje
    
    size = size*unit
    inicio = len(mbr.serializar())
    mbr.mbr_partition.sort(key=lambda x:x.part_start)
    
    particion_disponible = 5
    
    longitudes = []
    
    for i in range(len(mbr.mbr_partition)):
        x = mbr.mbr_partition[i]
        
        if x.part_start <= 0 and i < particion_disponible:
            particion_disponible = i
            continue
        
        if x.part_start <= 0:
            continue
        
        longitudes.append((inicio, x.part_start-inicio))
        inicio = x.part_start+x.part_size
    
    if particion_disponible == 5:
        mensaje += "Error: no se ha podido completar la operacion, particiones llenas\n"
        return mensaje
    
    longitudes.append((inicio, mbr.mbr_tamanio-inicio))
    
    encontrado = False
    
    if _type.lower() == "e":
        tipos = [x.part_type.decode().lower() for x in mbr.mbr_partition]
        if "e" in tipos:
            mensaje += "Error: no se puede crear mas de una particion extendida\n"
            return mensaje
    
    if mbr.dsk_fit.decode() == 'F':
        for x in longitudes:
            if x[1] >= size:
                mbr.mbr_partition[particion_disponible].setAll('0',_type,fit,x[0]+1,size,name)
                encontrado = True
                break
    
    elif mbr.dsk_fit.decode() == 'B':
        longitudes.sort(key=lambda x:x[1]-size)
        for x in longitudes:
            if x[1] >= size:
                mbr.mbr_partition[particion_disponible].setAll('0',_type,fit,x[0]+1,size,name)
                encontrado = True
                break
    else:
        longitudes.sort(key=lambda x:x[1]-size, reverse=True)
        for x in longitudes:
            if x[1] >= size:
                mbr.mbr_partition[particion_disponible].setAll('0',_type,fit,x[0]+1,size,name)
                encontrado = True
                break
    
    if not encontrado:
        mensaje += "Error: No se ha podido completar la operacion, el tamano maximo que hay disponible en disco es "+str(sorted(longitudes, key=lambda x: x[1], reverse=True)[0][1])+" byte(s) y se intento alocar "+str(size)+" byte(s)\n"
        return mensaje
    
    serializado = mbr.serializar()
    
    with open(path, 'r+b') as d:
        post = d.read()[len(serializado):]
        d.seek(0)
        d.write(serializado)
        d.write(post)
        d.close()
    
    mensaje += "se ha creado la particion "+name+" con tamaño de "+str(size)+" byte(s) exitosamente\n"
    return mensaje