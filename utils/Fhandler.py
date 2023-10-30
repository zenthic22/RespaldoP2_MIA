from estructuras.Estructuras import *
from datetime import datetime
import re

def activar_bit(sb,particion,bit,modo):
    if modo == "b":
        pre = particion[:sb.s_bm_block_start+bit]
        data_serializada = code_str("1",1)
        post = particion[sb.s_bm_block_start+bit+len(data_serializada):]
        particion = pre+data_serializada+post
        sb.s_free_blocks_count -= 1
    else:
        pre = particion[:sb.s_bm_inode_start+bit]
        data_serializada = code_str("1",1)
        post = particion[sb.s_bm_inode_start+bit+len(data_serializada):]
        particion = pre+data_serializada+post
        sb.s_free_inodes_count -= 1

    return particion

def desactivar_bit(sb,particion,bit,modo):
    if modo == "b":
        pre = particion[:sb.s_bm_block_start+bit]
        data_serializada = code_str("0",1)
        post = particion[sb.s_bm_block_start+bit+len(data_serializada):]
        particion = pre+data_serializada+post
        sb.s_free_blocks_count += 1
    else:
        pre = particion[:sb.s_bm_inode_start+bit]
        data_serializada = code_str("0",1)
        post = particion[sb.s_bm_inode_start+bit+len(data_serializada):]
        particion = pre+data_serializada+post
        sb.s_free_inodes_count += 1
    return particion

def sig_bit_libre(sb,particion,modo):
    if modo == "b":
        bitmap_bloque = particion[sb.s_bm_block_start:]
        for i_bit in range(sb.s_blocks_count):
            if bitmap_bloque[i_bit] != 49:
                sb.s_first_blo = i_bit
                break
    else:
        bitmap_inodo = particion[sb.s_bm_inode_start:]
        for i_bit in range(sb.s_inodes_count):
            if bitmap_inodo[i_bit] != 49:
                sb.s_first_ino = i_bit
                break

def guardar_bloque(sb, particion, blo, block_number):
    data_serializada = blo.serializar()
    pre = particion[:sb.s_block_start+block_number*sb.s_block_s]
    post = particion[sb.s_block_start+block_number*sb.s_block_s+len(data_serializada):]
    particion = pre+data_serializada+post
    return particion

def recuperar_bloque(sb, particion, blo, block_number):
    blo.deserializar(particion[sb.s_block_start+block_number*sb.s_block_s:])

def guardar_inodo(sb, particion, ino, ino_number):
    data_serializada =  ino.serializar()
    pre = particion[:sb.s_inode_start+ino_number*sb.s_inode_s]
    post = particion[sb.s_inode_start+ino_number*sb.s_inode_s+len(data_serializada):]
    particion = pre+data_serializada+post
    return particion

def recuperar_inodo(sb, particion, ino, ino_number):
    ino.deserializar(particion[sb.s_inode_start+ino_number*sb.s_inode_s:])

def guardar_sb(sb, particion):
    pre = sb.serializar()
    post = particion[len(pre):]
    particion = pre+post
    return particion

#regresa estado, permiso maximo, particion
def revisar_permisos(path, particion,sesion):
    sb = SuperBlock()
    ino = Inodo()
    
    sb.deserializar(particion)
    
    estado, ino_number, particion = encontrar_archivo(sb,particion,path)

    if not estado:
        return False, f'{0:03b}', particion
    
    if sesion["user"] == "root":
        return True, '111', particion
    
    recuperar_inodo(sb, particion, ino, ino_number)
    ino.setI_atime(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))

    permisos = []
    
    perm_usr = int(ino.i_perm/64)
    perm_grp = int((ino.i_perm-perm_usr*64)/8)
    perm_otr = int(ino.i_perm-perm_usr*64-perm_grp*8)

    if ino.i_uid == sesion["uid"]:
        permisos.append(perm_usr)
    if ino.i_gid == sesion["gid"]:
        permisos.append(perm_grp)
    if ino.i_gid != sesion["gid"] and ino.i_uid != sesion["uid"]:
        permisos.append(perm_otr)

    particion = guardar_inodo(sb, particion, ino, ino_number)
    return True, f'{max(permisos):03b}', particion

#retorna numero de inodo al final de la ruta
def encontrar_archivo(sb,particion,ruta):
    busqueda = ruta.split("/")[1:]
    busqueda = [i for i in busqueda if i.strip() != ""]
    ino = Inodo()
    blo = BloqueCarpeta()
    bloA1 = BloqueApuntadores()
    bloA2 = BloqueApuntadores()
    bloA3 = BloqueApuntadores()

    ino_number = 0
    block_number = -1
    
    for segmento in busqueda:
        recuperar_inodo(sb, particion, ino, ino_number)
        ino.setI_atime(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
        particion = guardar_inodo(sb, particion, ino, ino_number)

        sig_inodo = None

        for i in range(12):
            block_number = ino.i_block[i]
            if block_number != -1:
                recuperar_bloque(sb, particion, blo, block_number)
                for x in blo.b_content:
                    if x.b_name.decode().strip('\x00') == segmento:
                        sig_inodo = x.b_inodo
                        break

                if sig_inodo:
                    break

        block_number = ino.i_block[12]
        if not sig_inodo and block_number!=-1:
            recuperar_bloque(sb, particion, bloA1, block_number)
            for i in range(16):
                apuntador1 = bloA1.b_pointers[i]
                if apuntador1 != -1:
                    recuperar_bloque(sb, particion, blo, block_number)
                    for x in blo.b_content:
                        if x.b_name.decode().strip('\x00') == segmento:
                            sig_inodo = x.b_inodo
                            break

                    if sig_inodo:
                        break

        block_number = ino.i_block[13]
        if not sig_inodo and block_number!=-1:
            recuperar_bloque(sb, particion, bloA1, block_number)
            for i in range(16):
                apuntador1 = bloA1.b_pointers[i]
                if apuntador1 != -1:
                    recuperar_bloque(sb, particion, bloA2, block_number)
                    for j in range(16):
                        apuntador2 = bloA2.b_pointers[j]
                        if apuntador2 != -1:
                            for x in blo.b_content:
                                if x.b_name.decode().strip('\x00') == segmento:
                                    sig_inodo = x.b_inodo
                                    break

                            if sig_inodo:
                                break

                    if sig_inodo:
                        break

        block_number = ino.i_block[14]
        if not sig_inodo and block_number!=-1:
            recuperar_bloque(sb, particion, bloA1, block_number)
            for i in range(16):
                apuntador1 = bloA1.b_pointers[i]
                if apuntador1 != -1:
                    recuperar_bloque(sb, particion, bloA2, block_number)
                    for j in range(16):
                        apuntador2 = bloA2.b_pointers[j]
                        if apuntador2 != -1:
                            recuperar_bloque(sb, particion, bloA2, block_number)
                            for k in range(16):
                                apuntador3 = bloA3.b_pointers[k]
                                if apuntador3 != -1:
                                    for x in blo.b_content:
                                        if x.b_name.decode().strip('\x00') == segmento:
                                            sig_inodo = x.b_inodo
                                            break

                                    if sig_inodo:
                                        break

                            if sig_inodo:
                                break

                    if sig_inodo:
                        break
                    
        if sig_inodo:
            ino_number = sig_inodo
            continue
        else:
            return False, ino_number, particion
    return True, ino_number, particion

#regresa estado, particion, bloque, puntero
def bloque_que_contiene_inodo(sb,ino,ino_number,particion,sesion, ino_hijo = -1):
    blo = BloqueCarpeta()
    bloA1 = BloqueApuntadores()
    bloA2 = BloqueApuntadores()
    bloA3 = BloqueApuntadores()

    for i in range(12):
        block_number = ino.i_block[i]
        if block_number == -1:
            if ino_hijo != -1:
                continue
            block_number = sb.s_first_blo
            particion = guardar_bloque(sb, particion, BloqueCarpeta(), block_number)
            particion = activar_bit(sb,particion,sb.s_first_blo,"b")
            sig_bit_libre(sb,particion,"b")
            ino.i_block[i] = block_number

        recuperar_bloque(sb, particion, blo, block_number)
        for j in range(4):
            if blo.b_content[j].b_inodo == ino_hijo:                 
                particion = guardar_inodo(sb, particion, ino, ino_number)
                return True, particion, block_number, j 

    #indirecto 1
    block_number = ino.i_block[12]
    
    if block_number == -1:
        block_number = sb.s_first_blo
        particion = guardar_bloque(sb, particion, BloqueApuntadores(), block_number)
        particion = activar_bit(sb,particion,sb.s_first_blo,"b")
        sig_bit_libre(sb,particion,"b")
        ino.i_block[12] = block_number

    recuperar_bloque(sb, particion, bloA1, block_number)
    bloA1.b_pointers = list(bloA1.b_pointers)
    for i in range(16):
        apuntador1 = bloA1.b_pointers[i]
        if apuntador1 == -1:
            if ino_hijo != -1:
                continue
            apuntador1 = sb.s_first_blo
            particion = guardar_bloque(sb, particion, BloqueCarpeta(), apuntador1)
            particion = activar_bit(sb,particion,sb.s_first_blo,"b")
            sig_bit_libre(sb,particion,"b")
            bloA1.b_pointers[i] = apuntador1

        recuperar_bloque(sb, particion, blo, apuntador1)
        for j in range(4):
            if blo.b_content[j].b_inodo == ino_hijo:
                particion = guardar_bloque(sb, particion, bloA1, block_number)                    
                particion = guardar_inodo(sb, particion, ino, ino_number)
                return True, particion, apuntador1, j 

    #indirecto 2
    block_number = ino.i_block[13]
    if block_number == -1:
        block_number = sb.s_first_blo
        particion = guardar_bloque(sb, particion, BloqueApuntadores(), block_number)
        particion = activar_bit(sb,particion,sb.s_first_blo,"b")
        sig_bit_libre(sb,particion,"b")
        ino.i_block[13] = block_number

    recuperar_bloque(sb, particion, bloA1, block_number)
    bloA1.b_pointers = list(bloA1.b_pointers)
    for i in range(16):
        apuntador1 = bloA1.b_pointers[i]
        if apuntador1 == -1:
            if ino_hijo != -1:
                continue
            apuntador1 = sb.s_first_blo
            particion = guardar_bloque(sb, particion, BloqueApuntadores(), apuntador1)
            particion = activar_bit(sb,particion,sb.s_first_blo,"b")
            sig_bit_libre(sb,particion,"b")
            bloA1.b_pointers[i] = apuntador1

        recuperar_bloque(sb, particion, bloA2, apuntador1)
        bloA2.b_pointers = list(bloA2.b_pointers)
        for j in range(16):
            apuntador2 = bloA2.b_pointers[j]
            if apuntador2 == -1:
                if ino_hijo != -1:
                    continue
                apuntador2 = sb.s_first_blo
                particion = guardar_bloque(sb, particion, BloqueCarpeta(), apuntador2)
                particion = activar_bit(sb,particion,sb.s_first_blo,"b")
                sig_bit_libre(sb,particion,"b")
                bloA2.b_pointers[i] = apuntador2

            recuperar_bloque(sb, particion, blo, apuntador2)
            for k in range(4):
                if blo.b_content[k].b_inodo == ino_hijo:
                    particion = guardar_bloque(sb, particion, bloA2, apuntador1)
                    particion = guardar_bloque(sb, particion, bloA1, block_number)                    
                    particion = guardar_inodo(sb, particion, ino, ino_number)
                    return True, particion, apuntador2, k

    #indirecto 3
    block_number = ino.i_block[13]
    if block_number == -1:
        block_number = sb.s_first_blo
        particion = guardar_bloque(sb, particion, BloqueApuntadores(), block_number)
        particion = activar_bit(sb,particion,sb.s_first_blo,"b")
        sig_bit_libre(sb,particion,"b")
        ino.i_block[13] = block_number

    recuperar_bloque(sb, particion, bloA1, block_number)
    bloA1.b_pointers = list(bloA1.b_pointers)
    for i in range(16):
        apuntador1 = bloA1.b_pointers[i]
        if apuntador1 == -1:
            if ino_hijo != -1:
                continue
            apuntador1 = sb.s_first_blo
            particion = guardar_bloque(sb, particion, BloqueApuntadores(), apuntador1)
            particion = activar_bit(sb,particion,sb.s_first_blo,"b")
            sig_bit_libre(sb,particion,"b")
            bloA1.b_pointers[i] = apuntador1

        recuperar_bloque(sb, particion, bloA2, apuntador1)
        bloA2.b_pointers = list(bloA2.b_pointers)
        for j in range(16):
            apuntador2 = bloA2.b_pointers[j]
            if apuntador2 == -1:
                if ino_hijo != -1:
                    continue
                apuntador2 = sb.s_first_blo
                particion = guardar_bloque(sb, particion, BloqueApuntadores(), apuntador2)
                particion = activar_bit(sb,particion,sb.s_first_blo,"b")
                sig_bit_libre(sb,particion,"b")
                bloA2.b_pointers[i] = apuntador2

            recuperar_bloque(sb, particion, bloA3, block_number)
            bloA3.b_pointers = list(bloA1.b_pointers)
            for k in range(16):
                apuntador3 = bloA3.b_pointers[k]
                if apuntador3 == -1:
                    if ino_hijo != -1:
                        continue
                    apuntador3 = sb.s_first_blo
                    particion = guardar_bloque(sb, particion, BloqueCarpeta(), apuntador3)
                    particion = activar_bit(sb,particion,sb.s_first_blo,"b")
                    sig_bit_libre(sb,particion,"b")
                    bloA3.b_pointers[i] = apuntador3
                
                    recuperar_bloque(sb, particion, blo, apuntador3)
                    for l in range(4):
                        if blo.b_content[l].b_inodo == ino_hijo:
                            particion = guardar_bloque(sb, particion, bloA3, apuntador2)
                            particion = guardar_bloque(sb, particion, bloA2, apuntador1)
                            particion = guardar_bloque(sb, particion, bloA1, block_number)                    
                            particion = guardar_inodo(sb, particion, ino, ino_number)
                            return True, particion, apuntador3, l
    return False, particion, -1, -1

def crear_ruta(path, particion, sesion):

    sb = SuperBlock()
    sb.deserializar(particion)

    i = 0
    
    while True:
        conjunto = path.rsplit("/",i)
        existe, permiso, particion = revisar_permisos(conjunto[0],particion,sesion)
        
        if not existe:
            i+=1
            continue

        if permiso[1] != "1":
            print("--El usuario no tiene permiso de Escritura en la carpeta "+conjunto[0])
            print()
            return False, particion

        i-=1
        if i<0:
            break
        conjunto = path.rsplit("/",i)
        estado, particion = crear_carpeta(conjunto[0], particion, sesion)
        if not estado:
            return False, particion
        
    return True, particion


#retorna estado, particion
def crear_carpeta(path, particion, sesion):
    sb = SuperBlock()
    ino = Inodo()
    blo = BloqueCarpeta()
    
    sb.deserializar(particion)

    conjunto = path.rsplit("/",1)
    
    ruta = conjunto[0]
    archivo = conjunto[1]

    if len(archivo) > 12:
        print("El nombre de la carpeta debe tener como maximo 12 caracteres")
        print()
        return False, particion
    
    estado, ino_number, particion = encontrar_archivo(sb,particion,ruta)
    if not estado:
        print("--No se ha encontrado la ruta")
        print()
        return False, particion
    
    recuperar_inodo(sb, particion, ino, ino_number)
    ino.setI_mtime(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))

    n_ino = Inodo()
    i_uid = sesion["uid"]
    i_gid = sesion["gid"]
    i_s = 0
    i_atime = ""
    i_ctime = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    i_mtime = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    i_block = [-1 for x in range(15)]
    i_type = "0"
    i_perm = 6*8*8+6*8+4
    n_ino.setAll(i_uid, i_gid, i_s, i_atime, i_ctime, i_mtime, i_block, i_type, i_perm)


    n_block_number = sb.s_first_blo
    estado, b_ptr, particion = encontrar_archivo(sb,particion,path.rsplit("/",1)[0])
    estado, b_ptr2, particion = encontrar_archivo(sb,particion,path.rsplit("/",2)[0])
    blo.b_content[0].setAll(".",b_ptr)
    blo.b_content[1].setAll("..",b_ptr2)
    particion = guardar_bloque(sb, particion, blo, n_block_number)
    particion = activar_bit(sb,particion,n_block_number,"b")
    sig_bit_libre(sb,particion,"b")


    n_ino.i_block[0] = n_block_number
    n_ino_number = sb.s_first_ino
    particion = guardar_inodo(sb, particion, n_ino, n_ino_number)
    particion = activar_bit(sb,particion,n_ino_number,"i")
    sig_bit_libre(sb,particion,"i")
    estado, particion, block_number, indice = bloque_que_contiene_inodo(sb,ino,ino_number,particion,sesion)
        
    if not estado:
        particion = desactivar_bit(sb,particion,n_ino_number,"i")
        sig_bit_libre(sb,particion,"i")
        particion = desactivar_bit(sb,particion,n_block_number,"b")
        sig_bit_libre(sb,particion,"b")
        particion = guardar_sb(sb, particion)
        return False, particion

    recuperar_bloque(sb, particion, blo, block_number)
    blo.b_content[indice].setAll(archivo,n_ino_number)
    particion = guardar_bloque(sb, particion, blo, block_number)
    particion = guardar_inodo(sb, particion, ino, ino_number)
    particion = guardar_sb(sb, particion)
    
    return True, particion


def eliminar_referencias_a_inodo(sb,particion, padre, num_hijo):
    blo = BloqueCarpeta()
    bloA1 = BloqueApuntadores()
    bloA2 = BloqueApuntadores()
    bloA3 = BloqueApuntadores()
    
    for i in range(12):
        block_number = padre.i_block[i]
        if  block_number != -1:
            recuperar_bloque(sb, particion, blo, block_number)
            for j in range(4):
                ino_num = blo.b_content[j].b_inodo
                if ino_num == num_hijo:
                     blo.b_content[j] = CarpetaContent()
                     particion = guardar_bloque(sb, particion, blo, block_number)
                     return particion

    #indirecto 1
    block_number = padre.i_block[12]
    if block_number != -1:
        recuperar_bloque(sb, particion, bloA1, block_number)
        for i in range(16):
            apuntador1 = bloA1.b_pointers[i]
            if apuntador1 != -1:
                recuperar_bloque(sb, particion, blo, apuntador1)
                for j in range(4):
                    ino_num = blo.b_content[j].b_inodo
                    if ino_num == num_hijo:
                         blo.b_content[j] = CarpetaContent()
                         particion = guardar_bloque(sb, particion, blo, apuntador1)
                         return particion
    #indirecto 2
    block_number = padre.i_block[13]
    if block_number != -1:
        recuperar_bloque(sb, particion, bloA1, block_number)
        for i in range(16):
            apuntador1 = bloA1.b_pointers[i]
            if apuntador1 != -1:
                recuperar_bloque(sb, particion, bloA2, apuntador1)
                for j in range(16):
                    apuntador2 = bloA2.b_pointers[j]
                    if apuntador2 != -1:
                        recuperar_bloque(sb, particion, blo, apuntador2)
                        for k in range(4):
                            ino_num = blo.b_content[k].b_inodo
                            if ino_num == num_hijo:
                                 blo.b_content[k] = CarpetaContent()
                                 particion = guardar_bloque(sb, particion, blo, apuntador2)
                                 return particion

    #indirecto 3
    block_number = padre.i_block[13]
    if block_number != -1:
        recuperar_bloque(sb, particion, bloA1, block_number)
        for i in range(16):
            apuntador1 = bloA1.b_pointers[i]
            if apuntador1 != -1:
                recuperar_bloque(sb, particion, bloA2, apuntador1)
                for j in range(16):
                    apuntador2 = bloA2.b_pointers[j]
                    if apuntador2 != -1:
                        recuperar_bloque(sb, particion, bloA3, apuntador2)
                        for k in range(16):
                            apuntador3 = bloA3.b_pointers[k]
                            if apuntador3 != -1:
                                recuperar_bloque(sb, particion, blo, apuntador3)
                                for l in range(4):
                                    ino_num = blo.b_content[l].b_inodo
                                    if ino_num == num_hijo:
                                         blo.b_content[l] = CarpetaContent()
                                         particion = guardar_bloque(sb, particion, blo, apuntador3)
                                         return particion

    return particion

#estado, particion                    
def eliminar_ruta(path,particion,sesion):
    sb = SuperBlock()
    sb.deserializar(particion)

    conjunto = path.rsplit("/",1)
    
    estado, ino_number, particion = encontrar_archivo(sb,particion,path)
    
    posibles = rutas_posibles(sb,particion,1,ino_number)

    estados = []
    for ruta in posibles:
        hijo_borrado, particion = eliminar_ruta(path+"/"+ruta,particion,sesion)
        estados.append(hijo_borrado)

    if False in estados:
        return False, particion
    
    existe, permiso, particion = revisar_permisos(path,particion,sesion)

    if permiso[1] != "1":
        return False, particion

    return eliminar(path,particion,sesion)


def cambiar_nombre(path,particion,n_nombre,sesion):
    sb = SuperBlock()
    ino_padre = Inodo()
    blo = BloqueCarpeta()
    sb.deserializar(particion)
    conjunto = path.rsplit("/",1)
    
    ruta = conjunto[0]
    archivo = conjunto[1]

    estado, ino_number, particion = encontrar_archivo(sb,particion,ruta)
    if not estado:
        return False, particion

    recuperar_inodo(sb, particion, ino_padre, ino_number)
    estado, h_ino_number, particion = encontrar_archivo(sb,particion,path)
    if not estado:
        return False, particion
    
    estado, particion, block_number, indice = bloque_que_contiene_inodo(sb,ino_padre,ino_number,particion,sesion,h_ino_number)
    
    recuperar_bloque(sb, particion, blo, block_number)

    blo.b_content[indice].setB_name(n_nombre)
    
    particion = guardar_bloque(sb, particion, blo, block_number)

    return True, particion
    

# estado, particion
def eliminar(path,particion,sesion):
    sb = SuperBlock()
    ino_padre = Inodo()
    ino_hijo = Inodo()
    blo = BloqueCarpeta()
    bloA1 = BloqueApuntadores()
    bloA2 = BloqueApuntadores()
    bloA3 = BloqueApuntadores()
    
    sb.deserializar(particion)

    conjunto = path.rsplit("/",1)
    
    ruta = conjunto[0]
    archivo = conjunto[1]
    
    estado, ino_number, particion = encontrar_archivo(sb,particion,ruta)
    if not estado:
        return False, particion

    
    estado, h_ino_number, particion = encontrar_archivo(sb,particion,path)

    if not estado:
        return False, particion

    recuperar_inodo(sb, particion, ino_padre, ino_number)
    ino_padre.setI_mtime(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    particion = guardar_inodo(sb, particion, ino_padre, ino_number)

    particion = eliminar_referencias_a_inodo(sb,particion, ino_padre, h_ino_number)
    particion = desactivar_bit(sb,particion,h_ino_number,"i")
    
    recuperar_inodo(sb, particion, ino_hijo, h_ino_number)

    for i in range(12):
        block_num = ino_padre.i_block[i]
        if  block_num != -1:
            ino_padre.i_block[i] = -1

    for i in range(12):
        block_number = ino_hijo.i_block[i]
        particion = desactivar_bit(sb,particion,block_number,"b")
        ino_hijo.i_block[i] = -1

    block_number = ino_hijo.i_block[12]
    if block_number != -1:
        particion = desactivar_bit(sb,particion,block_number,"b")
        recuperar_bloque(sb, particion, bloA1, block_number)
        ino_hijo.i_block[12] = -1
        for i in range(16):
            apuntador = bloA1.b_pointers[i]
            if apuntador != -1:
                particion = desactivar_bit(sb,particion,apuntador,"b")

    block_number = ino_hijo.i_block[13]
    if block_number != -1:
        particion = desactivar_bit(sb,particion,block_number,"b")
        recuperar_bloque(sb, particion, bloA1, block_number)
        ino_hijo.i_block[13] = -1
        for i in range(16):
            apuntador = bloA1.b_pointers[i]
            if apuntador != -1:
                particion = desactivar_bit(sb,particion,apuntador,"b")
                recuperar_bloque(sb, particion, bloA2, apuntador)
                for j in range(16):
                    apuntador2 = bloA2.b_pointers[j]
                    if apuntador2 != -1:
                        particion = desactivar_bit(sb,particion,apuntador2,"b")

    block_number = ino_hijo.i_block[14]
    if block_number != -1:
        particion = desactivar_bit(sb,particion,block_number,"b")
        recuperar_bloque(sb, particion, bloA1, block_number)
        ino_hijo.i_block[14] = -1
        for i in range(16):
            apuntador = bloA1.b_pointers[i]
            if apuntador != -1:
                particion = desactivar_bit(sb,particion,apuntador,"b")
                recuperar_bloque(sb, particion, bloA2, apuntador)
                for j in range(16):
                    apuntador2 = bloA2.b_pointers[j]
                    if apuntador2 != -1:
                        particion = desactivar_bit(sb,particion,apuntador2,"b")
                        recuperar_bloque(sb, particion, bloA3, apuntador2)
                        for k in range(16):
                            apuntador3 = bloA3.b_pointers[k]
                            particion = desactivar_bit(sb,particion,apuntador3,"b")

    


    sig_bit_libre(sb,particion,"i")
    sig_bit_libre(sb,particion,"b")
    particion = guardar_sb(sb, particion)
    return True, particion
    
#retorna estado, particion
def crear_archivo(path,particion,sesion):
    sb = SuperBlock()
    ino = Inodo()
    blo = BloqueCarpeta()
    
    sb.deserializar(particion)

    conjunto = path.rsplit("/",1)
    
    ruta = conjunto[0]
    archivo = conjunto[1]

    if len(archivo) > 12:
        print("--El nombre del archivo debe tener como maximo 12 caracteres")
        print()
        return False, particion
    
    estado, ino_number, particion = encontrar_archivo(sb,particion,ruta)
    if not estado:
        print("--No se ha encontrado la ruta")
        print()
        return False, particion
    
    
    recuperar_inodo(sb, particion, ino, ino_number)
    ino.setI_mtime(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))

    block_number = -1

    n_ino = Inodo()
    i_uid = sesion["uid"]
    i_gid = sesion["gid"]
    i_s = 0
    i_atime = ""
    i_ctime = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    i_mtime = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    i_block = [-1 for x in range(15)]
    i_type = "1"
    i_perm = 6*8*8+6*8+4
    n_ino.setAll(i_uid, i_gid, i_s, i_atime, i_ctime, i_mtime, i_block, i_type, i_perm)

    n_ino_number = sb.s_first_ino
    particion = guardar_inodo(sb, particion, n_ino, n_ino_number)
    particion = activar_bit(sb,particion,n_ino_number,"i")
    sig_bit_libre(sb,particion,"i")
    
    estado, particion, block_number, indice = bloque_que_contiene_inodo(sb,ino,ino_number,particion,sesion)

    
    
    if not estado:
        particion = desactivar_bit(sb,particion,n_ino_number,"i")
        sig_bit_libre(sb,particion,"i")
        particion = guardar_sb(sb, particion)
        return False, particion
    
    recuperar_bloque(sb, particion, blo, block_number)
    blo.b_content[indice].setAll(archivo,n_ino_number)
    particion = guardar_bloque(sb, particion, blo, block_number)
    particion = guardar_inodo(sb, particion, ino, ino_number)
    particion = guardar_sb(sb, particion)
    
    
    return True, particion
    

def escribir_archivo(path, particion, texto):
    sb = SuperBlock()
    ino = Inodo()
    blo = BloqueArchivos()
    bloA1 = BloqueApuntadores()
    bloA2 = BloqueApuntadores()
    bloA3 = BloqueApuntadores()
    
    sb.deserializar(particion)
    
    estado, ino_number, particion = encontrar_archivo(sb,particion,path)

    if ino_number == -1:
        print("--la ruta "+path+" no existe en el disco")
        print()
        return particion
    
    recuperar_inodo(sb, particion, ino, ino_number)
    ino.setI_atime(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    ino.setI_s(len(texto))

    ultimo_ptr = []
    continuar = True

    for i in range(12):
        caracteres_faltantes = len(texto)
        if caracteres_faltantes == 0:
            ultimo_ptr.append(i)
            continuar = False
            break
        if caracteres_faltantes <= 64:
            slicing = caracteres_faltantes
        else:
            slicing = 64

        texto_alocando = texto[:slicing]
        texto = texto[slicing:]

        block_number = ino.i_block[i]
        if block_number == -1:
            block_number = sb.s_first_blo
            particion = guardar_bloque(sb, particion, BloqueArchivos(), block_number)
            particion = activar_bit(sb,particion,sb.s_first_blo,"b")
            sig_bit_libre(sb,particion,"b")
            ino.i_block[i] = block_number

        blo.setB_content(texto_alocando)
        particion = guardar_bloque(sb, particion, blo, block_number)

    #indirecto 1
    if continuar:
        block_number = ino.i_block[12]
        if block_number == -1:
            block_number = sb.s_first_blo
            particion = guardar_bloque(sb, particion, BloqueApuntadores(), block_number)
            particion = activar_bit(sb,particion,sb.s_first_blo,"b")
            sig_bit_libre(sb,particion,"b")
            ino.i_block[12] = block_number

        recuperar_bloque(sb, particion, bloA1, block_number)
        bloA1.b_pointers = list(bloA1.b_pointers)
        
        for i in range(16):
            caracteres_faltantes = len(texto)
            if caracteres_faltantes == 0:
                ultimo_ptr.append(i)
                ultimo_ptr.append(12)
                continuar = False
                break
            if caracteres_faltantes <= 64:
                slicing = caracteres_faltantes
            else:
                slicing = 64

            texto_alocando = texto[:slicing]
            texto = texto[slicing:]

            apuntador1 = bloA1.b_pointers[i]
            if apuntador1 == -1:
                apuntador1 = sb.s_first_blo
                particion = guardar_bloque(sb, particion, BloqueArchivos(), apuntador1)
                particion = activar_bit(sb,particion,sb.s_first_blo,"b")
                sig_bit_libre(sb,particion,"b")
                bloA1.b_pointers[i] = apuntador1

            blo.setB_content(texto_alocando)
            particion = guardar_bloque(sb, particion, blo, apuntador1)

        particion = guardar_bloque(sb, particion, bloA1, block_number)
    
    #indirecto 2
    if continuar:
        block_number = ino.i_block[13]
        if block_number == -1:
            block_number = sb.s_first_blo
            particion = guardar_bloque(sb, particion, BloqueApuntadores(), block_number)
            particion = activar_bit(sb,particion,sb.s_first_blo,"b")
            sig_bit_libre(sb,particion,"b")
            ino.i_block[13] = block_number

        recuperar_bloque(sb, particion, bloA1, block_number)
        bloA1.b_pointers = list(bloA1.b_pointers)
        
        for i in range(16):
            if not continuar:
                ultimo_ptr.append(i)
                ultimo_ptr.append(13)
                break
            apuntador1 = bloA1.b_pointers[i]
            if apuntador1 == -1:
                apuntador1 = sb.s_first_blo
                particion = guardar_bloque(sb, particion, BloqueApuntadores(), apuntador1)
                particion = activar_bit(sb,particion,sb.s_first_blo,"b")
                sig_bit_libre(sb,particion,"b")
                bloA1.b_pointers[i] = apuntador1

            recuperar_bloque(sb, particion, bloA2, apuntador1)
            bloA2.b_pointers = list(bloA2.b_pointers)
            for j in range(16):
                caracteres_faltantes = len(texto)
                if caracteres_faltantes == 0:
                    ultimo_ptr.append(j)
                    continuar = False
                    break
                if caracteres_faltantes <= 64:
                    slicing = caracteres_faltantes
                else:
                    slicing = 64

                texto_alocando = texto[:slicing]
                texto = texto[slicing:]

                apuntador2 = bloA2.b_pointers[j]
                if apuntador2 == -1:
                    apuntador2 = sb.s_first_blo
                    particion = guardar_bloque(sb, particion, BloqueArchivos(), apuntador2)
                    particion = activar_bit(sb,particion,sb.s_first_blo,"b")
                    sig_bit_libre(sb,particion,"b")
                    bloA2.b_pointers[j] = apuntador2

                blo.setB_content(texto_alocando)
                particion = guardar_bloque(sb, particion, blo, apuntador2)

            particion = guardar_bloque(sb, particion, bloA2, apuntador1)
            
        particion = guardar_bloque(sb, particion, bloA1, block_number)


    #indirecto 3
    if continuar:
        block_number = ino.i_block[14]
        if block_number == -1:
            block_number = sb.s_first_blo
            particion = guardar_bloque(sb, particion, BloqueApuntadores(), block_number)
            particion = activar_bit(sb,particion,sb.s_first_blo,"b")
            sig_bit_libre(sb,particion,"b")
            ino.i_block[14] = block_number

        recuperar_bloque(sb, particion, bloA1, block_number)
        bloA1.b_pointers = list(bloA1.b_pointers)
        
        for i in range(16):
            if not continuar:
                ultimo_ptr.append(i)
                ultimo_ptr.append(14)
                break
            apuntador1 = bloA1.b_pointers[i]
            if apuntador1 == -1:
                apuntador1 = sb.s_first_blo
                particion = guardar_bloque(sb, particion, BloqueApuntadores(), apuntador1)
                particion = activar_bit(sb,particion,sb.s_first_blo,"b")
                sig_bit_libre(sb,particion,"b")
                bloA1.b_pointers[i] = apuntador1

            recuperar_bloque(sb, particion, bloA2, apuntador1)
            bloA2.b_pointers = list(bloA2.b_pointers)
            for j in range(16):
                if not continuar:
                    ultimo_ptr.append(j)
                    break
                apuntador2 = bloA2.b_pointers[j]
                if apuntador2 == -1:
                    apuntador2 = sb.s_first_blo
                    particion = guardar_bloque(sb, particion, BloqueApuntadores(), apuntador2)
                    particion = activar_bit(sb,particion,sb.s_first_blo,"b")
                    sig_bit_libre(sb,particion,"b")
                    bloA2.b_pointers[j] = apuntador2

                recuperar_bloque(sb, particion, bloA3, apuntador2)
                bloA3.b_pointers = list(bloA3.b_pointers)
                for k in range(16):
                    caracteres_faltantes = len(texto)
                    if caracteres_faltantes == 0:
                        ultimo_ptr.append(k)
                        continuar = False
                        break
                    if caracteres_faltantes <= 64:
                        slicing = caracteres_faltantes
                    else:
                        slicing = 64

                    texto_alocando = texto[:slicing]
                    texto = texto[slicing:]

                    apuntador3 = bloA3.b_pointers[k]
                    if apuntador3 == -1:
                        apuntador3 = sb.s_first_blo
                        particion = guardar_bloque(sb, particion, BloqueArchivos(), apuntador3)
                        particion = activar_bit(sb,particion,sb.s_first_blo,"b")
                        sig_bit_libre(sb,particion,"b")
                        bloA3.b_pointers[k] = apuntador3

                    blo.setB_content(texto_alocando)
                    particion = guardar_bloque(sb, particion, blo, apuntador3)

                particion = guardar_bloque(sb, particion, bloA3, apuntador2)

            particion = guardar_bloque(sb, particion, bloA2, apuntador1)
            
        particion = guardar_bloque(sb, particion, bloA1, block_number)

    ultimo_ptr.reverse()

    if len(ultimo_ptr) == 1:
        for i in range(ultimo_ptr[0],12):
            block_number = ino.i_block[i]
            if block_number == -1:
                break
            particion = desactivar_bit(sb,particion,block_number,"b")
            ino.i_block[i] = -1

        block_number = ino.i_block[12]
        if block_number != -1:
            particion = desactivar_bit(sb,particion,block_number,"b")
            recuperar_bloque(sb, particion, bloA1, block_number)
            ino.i_block[12] = -1
            for i in range(16):
                apuntador = bloA1.b_pointers[i]
                if apuntador != -1:
                    particion = desactivar_bit(sb,particion,apuntador,"b")

        block_number = ino.i_block[13]
        if block_number != -1:
            particion = desactivar_bit(sb,particion,block_number,"b")
            recuperar_bloque(sb, particion, bloA1, block_number)
            ino.i_block[13] = -1
            for i in range(16):
                apuntador = bloA1.b_pointers[i]
                if apuntador != -1:
                    particion = desactivar_bit(sb,particion,apuntador,"b")
                    recuperar_bloque(sb, particion, bloA2, apuntador)
                    for j in range(16):
                        apuntador2 = bloA2.b_pointers[j]
                        if apuntador2 != -1:
                            particion = desactivar_bit(sb,particion,apuntador2,"b")

        block_number = ino.i_block[14]
        if block_number != -1:
            particion = desactivar_bit(sb,particion,block_number,"b")
            recuperar_bloque(sb, particion, bloA1, block_number)
            ino.i_block[14] = -1
            for i in range(16):
                apuntador = bloA1.b_pointers[i]
                if apuntador != -1:
                    particion = desactivar_bit(sb,particion,apuntador,"b")
                    recuperar_bloque(sb, particion, bloA2, apuntador)
                    for j in range(16):
                        apuntador2 = bloA2.b_pointers[j]
                        if apuntador2 != -1:
                            particion = desactivar_bit(sb,particion,apuntador2,"b")
                            recuperar_bloque(sb, particion, bloA3, apuntador2)
                            for k in range(16):
                                apuntador3 = bloA3.b_pointers[k]
                                particion = desactivar_bit(sb,particion,apuntador3,"b")
        
    particion = guardar_inodo(sb, particion, ino, ino_number)
    particion = guardar_sb(sb, particion)
    
    return particion

def traer_archivo(path,particion):
    sb = SuperBlock()
    ino = Inodo()
    blo = None
    bloA1 = BloqueApuntadores()
    bloA2 = BloqueApuntadores()
    bloA3 = BloqueApuntadores()
    
    sb.deserializar(particion)
    
    estado, ino_number, particion = encontrar_archivo(sb,particion,path)

    if not estado:
        return "--No se ha encontrado la ruta", particion
    
    block_number = -1
    
    recuperar_inodo(sb, particion, ino, ino_number)
    ino.setI_atime(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))

    particion = guardar_inodo(sb, particion, ino, ino_number)
    if ino.i_type.decode() == "0":
        return "--La ruta es una carpeta", particion
    
    res = ""
    blo = BloqueArchivos()
    for i in range(12):
        block_number = ino.i_block[i]
        if block_number == -1:
            break    
        blo.deserializar(particion[sb.s_block_start+block_number*sb.s_block_s:])
        res += blo.b_content.decode().strip('\x00')

    block_number = ino.i_block[12]
    if block_number != -1:
        bloA1.deserializar(particion[sb.s_block_start+block_number*sb.s_block_s:])
        for directo in bloA1.b_pointers:
            if directo == -1:
                break
            blo.deserializar(particion[sb.s_block_start+directo*sb.s_block_s:])
            res += blo.b_content.decode().strip('\x00')

    block_number = ino.i_block[13]
    if block_number != -1:
        bloA1.deserializar(particion[sb.s_block_start+block_number*sb.s_block_s:])
        for directo in bloA1.b_pointers:
            if directo == -1:
                break
            bloA2.deserializar(particion[sb.s_block_start+directo*sb.s_block_s:])
            for directo2 in bloA2.b_pointers:
                if directo2 == -1:
                    break
                blo.deserializar(particion[sb.s_block_start+directo2*sb.s_block_s:])
                res += blo.b_content.decode().strip('\x00')

    block_number = ino.i_block[14]
    if block_number != -1:
        bloA1.deserializar(particion[sb.s_block_start+block_number*sb.s_block_s:])
        for directo in bloA1.b_pointers:
            if directo == -1:
                break
            bloA2.deserializar(particion[sb.s_block_start+directo*sb.s_block_s:])
            for directo2 in bloA2.b_pointers:
                if directo2 == -1:
                    break

                bloA3.deserializar(particion[sb.s_block_start+directo2*sb.s_block_s:])
                for directo3 in bloA3.b_pointers:
                    if directo3 == -1:
                        break
                    blo.deserializar(particion[sb.s_block_start+directo3*sb.s_block_s:])
                    res += blo.b_content.decode().strip('\x00')
    
    return res, particion


def repTree(particion):
    sb = SuperBlock()
    sb.deserializar(particion)
    s = """digraph G {
  fontname="Edu NSW ACT Foundation, cursive"
  rankdir=LR;
  node [fontname="Edu NSW ACT Foundation, cursive"]
  edge [fontname="Edu NSW ACT Foundation, cursive"]\n"""
    s+= _repTree(sb,particion,1,0)+"\n}"
    
    return s
    

def _repTree(sb,particion,tipo,num, tipo_secundario = 0, nivel = 0):
    # 1 inodo | 2 archivos | 3 carpetas | 4 apuntadores
    s=""
    obj = None
    if tipo == 1:
        obj = Inodo()
        recuperar_inodo(sb, particion, obj, num)
        s+=obj.tree(num)
        for i in range(12):
            block_num = obj.i_block[i]
            if block_num != -1:
                if obj.i_type.decode() == "1":
                    #inodo de archivos
                    s+= _repTree(sb,particion,2,block_num)
                else:
                    #inodo de carpetas
                    s+= _repTree(sb,particion,3,block_num)

        for i in range(12,15):
            #apuntadores
            block_num = obj.i_block[i]
            if block_num != -1:
                if obj.i_type.decode() == "1":
                    #inodo de archivos
                    s+= _repTree(sb,particion,4,block_num,2,i-12)
                else:
                    #inodo de carpetas
                    s+= _repTree(sb,particion,4,block_num,3,i-12)

    elif tipo == 2:
        obj = BloqueArchivos()
        recuperar_bloque(sb, particion, obj, num)
        s+=obj.tree(num)

    elif tipo == 3:
        obj = BloqueCarpeta()
        recuperar_bloque(sb, particion, obj, num)
        s+=obj.tree(num)
        no_ir =[".",".."]
        for i in obj.b_content:
            if i.b_name.decode().strip("\x00") not in no_ir and i.b_inodo != -1:
                s+= _repTree(sb,particion,1,i.b_inodo)

    elif tipo == 4:
        obj = BloqueApuntadores()
        recuperar_bloque(sb, particion, obj, num)
        s+=obj.tree(num)
        for i in obj.b_pointers:
            if i != -1:
                if nivel == 0:
                    s+= _repTree(sb,particion,tipo_secundario,i)
                else:
                    s+= _repTree(sb,particion,4,i,tipo_secundario,nivel-1)
    return s

def copiar(rutaOriginal,rutaNueva,particion,sesion):
    padreoriginal = Inodo()
    padreNuevo = Inodo()
    hijo = Inodo()
    sb = SuperBlock()
    sb.deserializar(particion)

    existe, ino_number_o, particion = encontrar_archivo(sb,particion,rutaOriginal)
    if not existe:
        print("--No se ha encontrado la ruta Original")
        print()
        return particion
    existe, permiso, particion = revisar_permisos(rutaOriginal,particion,sesion)
    if permiso[0] != "1":
        return particion
    recuperar_inodo(sb, particion, padreoriginal, ino_number_o)

    existe, ino_number_n, particion = encontrar_archivo(sb,particion,rutaNueva)
    if not existe:
        print("--No se ha encontrado la ruta en donde se copiara")
        print()
        return particion

    existe, permiso, particion = revisar_permisos(rutaNueva,particion,sesion)
    if permiso[1] != "1":
        print("--No se tiene permisos en la ruta en donde se copiara")
        print()
        return particion
    
    recuperar_inodo(sb, particion, padreNuevo, ino_number_n)

    if padreNuevo.i_type.decode() == "1":
        print("--la ruta destino no es una carpeta")
        print()
        return particion

    if padreoriginal.i_type.decode() == "1":
        conjunto = rutaOriginal.rsplit("/",1)
        ruta = conjunto[0]
        archivo = conjunto[1]

        texto, particion = traer_archivo(rutaOriginal,particion)
        estado,particion = crear_archivo(rutaNueva+"/"+archivo,particion,sesion)
        particion = escribir_archivo(rutaNueva+"/"+archivo, particion, texto)
        return particion


    posibles_rutas = rutas_posibles(sb,particion,1,ino_number_o)
    if rutaOriginal.strip() == "/":
        rutaOriginal = ""
    if rutaNueva.strip() == "/":
        rutaNueva = ""
    for final in posibles_rutas:
        nuevaOriginal = rutaOriginal+"/"+final
        existe, ino_number_h, particion = encontrar_archivo(sb,particion,nuevaOriginal)
        recuperar_inodo(sb, particion, hijo, ino_number_h)

        if hijo.i_type.decode() == "1":
            conjunto = rutaOriginal.rsplit("/",1)
            ruta = conjunto[0]
            archivo = conjunto[1]
            texto, particion = traer_archivo(nuevaOriginal,particion)
            estado,particion = crear_archivo(rutaNueva+"/"+final,particion,sesion)
            particion = escribir_archivo(rutaNueva+"/"+final, particion, texto)
        else:
            estado, particion = crear_carpeta(rutaNueva+"/"+final, particion, sesion)
            particion = copiar(nuevaOriginal,rutaNueva+"/"+final,particion,sesion)

    return particion
    
def revisar_permiso_recursivo(ruta,tipo,particion,sesion):
    #0 leer, 1 escribir, 2 ejecutar
    padreoriginal = Inodo()
    sb = SuperBlock()
    sb.deserializar(particion)

    existe, ino_number_o, particion = encontrar_archivo(sb,particion,ruta)
    existe, permiso, particion = revisar_permisos(ruta,particion,sesion)
    if permiso[tipo] != "1":
        return False

    posibles_rutas = rutas_posibles(sb,particion,1,ino_number_o)
    if ruta.strip() == "/":
        ruta = ""
    perm_hijos = []
    for final in posibles_rutas:
        nuevaRuta = ruta+"/"+final
        perm_hijos.append(revisar_permiso_recursivo(nuevaRuta,tipo,particion,sesion))

    return False not in perm_hijos

def mover(rutaOriginal,rutaNueva,particion,sesion):
    padreoriginal = Inodo()
    padreNuevo = Inodo()
    hijo = Inodo()
    blo = BloqueCarpeta()
    sb = SuperBlock()
    sb.deserializar(particion)

    conjunto = rutaOriginal.rsplit("/",1)
    ruta = conjunto[0]
    archivo = conjunto[1]
    
    existe, ino_number_o, particion = encontrar_archivo(sb,particion,ruta)
    if not existe:
        print("--No se ha encontrado la ruta Original")
        print()
        return particion
    existe, permiso, particion = revisar_permisos(ruta,particion,sesion)
    if permiso[1] != "1":
        print("--No se tiene permisos en la ruta Original")
        print()
        return particion
    recuperar_inodo(sb, particion, padreoriginal, ino_number_o)

    existe, ino_number_n, particion = encontrar_archivo(sb,particion,rutaNueva)
    if not existe:
        print("--No se ha encontrado la ruta en donde se movera")
        print()
        return particion

    existe, permiso, particion = revisar_permisos(rutaNueva,particion,sesion)
    if permiso[1] != "1":
        print("--No se tiene permisos en la ruta en donde se movera")
        print()
        return particion


    if not revisar_permiso_recursivo(rutaOriginal,1,particion,sesion):
        print("--No se tiene permisos en la ruta Original")
        print()
        return particion
    
    recuperar_inodo(sb, particion, padreNuevo, ino_number_n)

    if padreNuevo.i_type.decode() == "1":
        print("--la ruta destino no es una carpeta")
        print()
        return particion

    existe, ino_number_h, particion = encontrar_archivo(sb,particion,rutaOriginal)

    particion = eliminar_referencias_a_inodo(sb,particion, padreoriginal, ino_number_h)

    estado, particion, block_number, indice = bloque_que_contiene_inodo(sb,padreNuevo,ino_number_n,particion,sesion)
        
    if not estado:
        return particion

    recuperar_bloque(sb, particion, blo, block_number)
    blo.b_content[indice].setAll(archivo,ino_number_h)
    particion = guardar_bloque(sb, particion, blo, block_number)
    print("Se ha movido la ruta con exito")
    print()
    return particion


def crear_diccionario_ruta(lista_rutas):
    arbol = {"/":{}}
    for ruta in lista_rutas:
        aux_dict = arbol["/"]
        for palabra in ruta.split("/")[1:]:
            if not aux_dict.get(palabra):
                aux_dict[palabra] = {}
            aux_dict = aux_dict[palabra]

    s="/\n"
    s+=crear_arbol(arbol["/"],[])
    return s

def crear_arbol(diccionario,indentacion):
    s=""
    i = 0
    for k,v in diccionario.items():
        i+=1
        for x in indentacion:
            s+=x
        s+="|_"+k+"\n"
        if len(v) >0:
            if i<len(diccionario):
                n_indentacion = indentacion[:]+["| "]
            else:
                n_indentacion = indentacion[:]+["  "]
            s+=crear_arbol(diccionario[k],n_indentacion)
    return s
        

def cambiar_permiso_r(ruta, particion, sesion, u, g, o):
    ino = Inodo()
    sb = SuperBlock()
    sb.deserializar(particion)

    existe, ino_number, particion = encontrar_archivo(sb,particion,ruta)
    if not existe:
        print("--La ruta no existe")
        print()
        return particion

    recuperar_inodo(sb, particion, ino, ino_number)
    ino.setI_perm(8*8*u+8*g+o)
    ino.setI_mtime(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    particion = guardar_inodo(sb, particion, ino, ino_number)
    posibles_rutas = rutas_posibles(sb,particion,1,ino_number)

    if ruta.strip() == "/":
        ruta = ""
    for r in posibles_rutas:
        particion = cambiar_permiso_r(ruta+"/"+r,particion,sesion, u, g, o)

    return particion

def cambiar_permiso(ruta, particion, sesion, u, g, o):
    ino = Inodo()
    sb = SuperBlock()
    sb.deserializar(particion)

    existe, ino_number, particion = encontrar_archivo(sb,particion,ruta)
    if not existe:
        print("--La ruta no existe")
        print()
        return particion

    recuperar_inodo(sb, particion, ino, ino_number)
    ino.setI_perm(8*8*u+8*g+o)
    ino.setI_mtime(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))

    particion = guardar_inodo(sb, particion, ino, ino_number)
    return particion


def cambiar_propietario_r(ruta, particion, sesion, uid_nuevo, gid_nuevo):
    ino = Inodo()
    sb = SuperBlock()
    sb.deserializar(particion)

    existe, ino_number, particion = encontrar_archivo(sb,particion,ruta)
    if not existe:
        print("--La ruta no existe")
        print()
        return particion

    recuperar_inodo(sb, particion, ino, ino_number)
    if ino.i_uid == sesion["uid"] or sesion["uid"] == 1:
        ino.setI_uid(uid_nuevo)
        ino.setI_mtime(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
        ino.setI_gid(gid_nuevo)

    particion = guardar_inodo(sb, particion, ino, ino_number)
    posibles_rutas = rutas_posibles(sb,particion,1,ino_number)

    if ruta.strip() == "/":
        ruta = ""
    for r in posibles_rutas:
        particion = cambiar_propietario_r(ruta+"/"+r,particion,sesion, uid_nuevo, gid_nuevo)

    return particion

def cambiar_propietario(ruta, particion, sesion, uid_nuevo, gid_nuevo):
    ino = Inodo()
    sb = SuperBlock()
    sb.deserializar(particion)

    existe, ino_number, particion = encontrar_archivo(sb,particion,ruta)
    if not existe:
        print("--La ruta no existe")
        print()
        return particion

    recuperar_inodo(sb, particion, ino, ino_number)
    if ino.i_uid == sesion["uid"] or sesion["uid"] == 1:
        ino.setI_uid(uid_nuevo)
        ino.setI_mtime(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
        ino.setI_gid(gid_nuevo)

    particion = guardar_inodo(sb, particion, ino, ino_number)
    return particion

def encontrar(ruta,expresion,particion,sesion):
    padreoriginal = Inodo()
    sb = SuperBlock()
    sb.deserializar(particion)

    res = []

    existe, ino_number_o, particion = encontrar_archivo(sb,particion,ruta)
    existe, permiso, particion = revisar_permisos(ruta,particion,sesion)
    if permiso[0] != "1":
        return res

    posibles_rutas = rutas_posibles(sb,particion,1,ino_number_o)
    if ruta.strip() == "/":
        ruta = ""
    for final in posibles_rutas:
        if re.search(expresion, final):
            res.append(ruta+"/"+final)
        res+=encontrar(ruta+"/"+final,expresion,particion,sesion)

    return res

def rutas_posibles(sb,particion,tipo,num, tipo_secundario = 0, nivel = 0):
    # 1 inodo | 2 archivos | 3 carpetas | 4 apuntadores
    s=[]
    obj = None
    if tipo == 1:
        obj = Inodo()
        recuperar_inodo(sb, particion, obj, num)
        for i in range(12):
            block_num = obj.i_block[i]
            if block_num != -1:
                if obj.i_type.decode() == "1":
                    #inodo de archivos
                    pass
                else:
                    #inodo de carpetas
                    s+=rutas_posibles(sb,particion,3,block_num)

        for i in range(12,15):
            #apuntadores
            block_num = obj.i_block[i]
            if block_num != -1:
                if obj.i_type.decode() == "1":
                    #inodo de archivos
                    pass
                else:
                    #inodo de carpetas
                    s+= rutas_posibles(sb,particion,4,block_num,3,i-12)

    elif tipo == 3:
        obj = BloqueCarpeta()
        recuperar_bloque(sb, particion, obj, num)
        no_ir =[".",".."]
        for i in obj.b_content:
            if i.b_name.decode().strip("\x00") not in no_ir and i.b_inodo != -1:
                s.append(i.b_name.decode().strip("\x00"))

    elif tipo == 4:
        obj = BloqueApuntadores()
        recuperar_bloque(sb, particion, obj, num)
        for i in obj.b_pointers:
            if i != -1:
                if nivel == 0:
                    s+=rutas_posibles(sb,particion,tipo_secundario,i)
                else:
                    s+=rutas_posibles(sb,particion,4,i,tipo_secundario,nivel-1)
    return s


def repSB(particion):
    
    sb = SuperBlock()
    sb.deserializar(particion)
    s = """digraph G {
  fontname="Edu NSW ACT Foundation, cursive"
  node [fontname="Edu NSW ACT Foundation, cursive"]
  edge [fontname="Edu NSW ACT Foundation, cursive"]\n"""
    if integridadSB(particion):
        s+=sb.graficar()+"}"
        return True, s
    else:
        return False,""


def integridadSB(particion):
    sb = SuperBlock()
    sb.deserializar(particion)
    tipos = [2,3]
    if sb.s_filesystem_type not in tipos:
       return False
    return True

def repBitmap(particion,modo):
    sb = SuperBlock()
    sb.deserializar(particion)

    s = ""
    i = 0
    if modo == "b":
        bitmap_bloque = particion[sb.s_bm_block_start:]
        for i_bit in range(sb.s_blocks_count):
            i+=1
            if bitmap_bloque[i_bit] != 49:
                s+="0"
            else:
                s+="1"
            if i == 20:
                s+="\n"
                i=0
    else:
        bitmap_inodo = particion[sb.s_bm_inode_start:]
        for i_bit in range(sb.s_inodes_count):
            i+=1
            if bitmap_inodo[i_bit] != 49:
                s+="0"
            else:
                s+="1"
            if i == 20:
                s+="\n"
                i=0
    return s


def repInodo(particion):
    sb = SuperBlock()
    sb.deserializar(particion)
    ino = Inodo()
    s = """digraph G {
  fontname="Edu NSW ACT Foundation, cursive"
  node [fontname="Edu NSW ACT Foundation, cursive"]
  edge [fontname="Edu NSW ACT Foundation, cursive"]\n"""
    bitmap_inodo = particion[sb.s_bm_inode_start:]
    for i_bit in range(sb.s_inodes_count):
        if bitmap_inodo[i_bit] == 49:
            recuperar_inodo(sb, particion, ino, i_bit)
            s+=ino.graficar(i_bit)

    s+="}"
    return s

def repBlock(particion):
    sb = SuperBlock()
    sb.deserializar(particion)
    blo = None
    s = """digraph G {
  fontname="Edu NSW ACT Foundation, cursive"
  node [fontname="Edu NSW ACT Foundation, cursive"]
  edge [fontname="Edu NSW ACT Foundation, cursive"]\n"""
    bitmap_bloque = particion[sb.s_bm_block_start:]
    for i_bit in range(sb.s_blocks_count):
        if bitmap_bloque[i_bit] == 49:
            imprimir = True
            blo = BloqueApuntadores()
            recuperar_bloque(sb, particion, blo, i_bit)
            for x in blo.b_pointers:
                if x > sb.s_blocks_count or x == 0:
                    imprimir = False
                    break

            if not imprimir:
                imprimir = True
                ignorar = [".",".."]
                blo = BloqueCarpeta()
                recuperar_bloque(sb, particion, blo, i_bit)
                for x in blo.b_content:
                    if x.b_inodo > sb.s_inodes_count or (x.b_inodo == 0 and x.b_name.decode().strip("\x00") not in ignorar):
                        imprimir = False
                        break

            if not imprimir:
                blo = BloqueArchivos()
                recuperar_bloque(sb, particion, blo, i_bit)

            s+=blo.graficar(i_bit)

    s+="}"
    return s
    
def repLs(ruta,particion):
    ino = Inodo()
    sb = SuperBlock()
    sb.deserializar(particion)

    res = """digraph G {
  fontname="Helvetica,Arial,sans-serif"
  node [fontname="Helvetica,Arial,sans-serif"]
  edge [fontname="Helvetica,Arial,sans-serif"]\nLs[shape=none label=<
<TABLE border="0" cellspacing="0" cellpadding="10">
<TR>\n<TD border="1">Permisos</TD>\n<TD border="1">UID propietario</TD>\n<TD border="1">GID propietario</TD>\n<TD border="1">Fecha de creacion</TD>\n<TD border="1">Tipo</TD>\n<TD border="1">Nombre</TD>\n</TR>\n"""

    existe, ino_number_o, particion = encontrar_archivo(sb,particion,ruta)
    if not existe:
        return res+'<TR>\n<TD border="1" colspan="6">No se puede ir a ningun lugar</TD></TR></TABLE>>];\n}', particion

    

    posibles_rutas = rutas_posibles(sb,particion,1,ino_number_o)
    if ruta.strip() == "/":
        ruta = ""
    for final in posibles_rutas:
        existe, ino_number, particion = encontrar_archivo(sb,particion,ruta+"/"+final)
        recuperar_inodo(sb, particion, ino, ino_number)
        u=int(ino.i_perm/64)
        g=int((ino.i_perm-u*64)/8)
        o=int(ino.i_perm-u*64-g*8)
        perm_usr = f'{u:03b}'
        perm_grp = f'{g:03b}'
        perm_otr = f'{o:03b}'
        
        res+= '<TR>\n<TD border="1">'+formato_permiso(perm_usr)+"|"+formato_permiso(perm_usr)+"|"+formato_permiso(perm_otr)+'</TD>\n<TD border="1">'+str(ino.i_uid)+'</TD>\n<TD border="1">'+str(ino.i_gid)+'</TD>\n<TD border="1">'+ino.i_ctime.decode().strip("\x00")+'</TD>\n<TD border="1">'+formato_tipo(ino.i_type.decode().strip("\x00"))+'</TD>\n<TD border="1">'+final+'</TD>\n</TR>\n'
    res+="</TABLE>>];\n"
    res+="}"
    return res, particion

def formato_tipo(tipo):
    if tipo == "1":
        return "Archivo"
    return "Carpeta"

def formato_permiso(permiso):
    res = ""
    if permiso[0] == "1":
        res+="r"
    else:
        res+="-"
    if permiso[1] == "1":
        res+="w"
    else:
        res+="-"

    if permiso[2] == "1":
        res+="x"
    else:
        res+="-"
    return res

def borrarTodo(particion):
    sb = SuperBlock()
    sb.deserializar(particion)
    if not integridadSB(particion):
        return particion
    limite = sb.s_block_start+sb.s_blocks_count*sb.s_block_s
    post = particion[limite:]
    pre = b'\0' * limite
    return pre+post

def mSb(particion):
    sb = SuperBlock()
    sb.deserializar(particion)
    if integridadSB(particion):
        sb.s_mnt_count += 1
        sb.setS_mtime(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
        particion = guardar_sb(sb, particion)
    return particion

def umSb(particion):
    sb = SuperBlock()
    sb.deserializar(particion)
    if integridadSB(particion):
        sb.setS_umtime(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
        particion = guardar_sb(sb, particion)
    return particion
    