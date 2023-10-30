from estructuras.Estructuras import *
from utils.Fhandler import *
from datetime import datetime
import math

def command_mkfs(params, lista_particiones):
    identificador = None
    file_system = 2
    mensaje = ""

    for x in params:
        param = [w.strip() for w in x.split("=")]
        
        if len(param) != 2:
            mensaje += "Error en el parametro '"+param[0]+"' parametro incompleto\n"
            return mensaje
        
        if param[0].lower() == "id":
            identificador = param[1]
            
        if param[0].lower() == "fs":
            if param[1] == "2fs":
                file_system = 2
            else:
                mensaje += "no reconoce el sistema "+param[1]+"\n"
                return mensaje
    
    if identificador == None:
        mensaje += "No se encontro el parametro obligatorio 'id'\n"
        return mensaje
    
    res = [x for x in lista_particiones if x["identificador"] == identificador]
    if len(res) == 0:
        mensaje += "no existe el id '"+identificador+"' entre las particiones montadas\n"
        return mensaje
    
    particion_montada = res[0]
    part = particion_montada["particion"]
    
    if file_system == 2:
        n = math.floor((part.part_size-sizeSuperBlock)/(4+sizeInodo+3*sizeBlock))
        s_filesystem_type = 2
    
    if n <= 0:
        mensaje += "no hay suficiente espacio en el disco para formatear\n"
        return mensaje
    
    n_superblock = SuperBlock()
    
    s_inodes_count = n
    s_blocks_count = 3*n
    s_free_inodes_count = n
    s_free_blocks_count = 3*n
    s_mtime = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    s_umtime = ""
    s_mnt_count = 1
    s_magic= 0xEF53
    s_inode_s = sizeInodo
    s_block_s = sizeBlock
    s_first_ino = 0
    s_first_blo = 0
    s_bm_inode_start = sizeSuperBlock
    s_bm_block_start = s_bm_inode_start + s_inodes_count
    s_inode_start = s_bm_block_start + s_blocks_count
    s_block_start = s_inode_start+s_inodes_count*s_inode_s
    n_superblock.setAll(s_filesystem_type, s_inodes_count, s_blocks_count, s_free_blocks_count, s_free_inodes_count, s_mtime, s_umtime, s_mnt_count, s_magic, s_inode_s, s_block_s, s_first_ino, s_first_blo, s_bm_inode_start, s_bm_block_start, s_inode_start, s_block_start)

    n_inodo = Inodo()
    i_uid = 1
    i_gid = 1
    i_s = -1
    i_atime = ""
    i_ctime = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    i_mtime = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    i_block = [0]+[-1 for x in range(14)]
    i_type = "0"
    i_perm = 6*8*8+6*8+6
    n_inodo.setAll(i_uid, i_gid, i_s, i_atime, i_ctime, i_mtime, i_block, i_type, i_perm)
    
    n_bloque = BloqueCarpeta()
    n_bloque.b_content[0].setAll(".",0)
    n_bloque.b_content[1].setAll("..",0)
    n_bloque.b_content[2].setAll("users.txt",1)


    data_serializada =  n_bloque.serializar()
    pre = particion_montada["datos"][:n_superblock.s_block_start+n_superblock.s_first_blo*n_superblock.s_block_s]
    post = particion_montada["datos"][n_superblock.s_block_start+n_superblock.s_first_blo*n_superblock.s_block_s+len(data_serializada):]
    particion_montada["datos"] = pre+data_serializada+post

    pre = particion_montada["datos"][:n_superblock.s_bm_block_start+n_superblock.s_first_blo]
    data_serializada = code_str("1",1)
    post = particion_montada["datos"][n_superblock.s_bm_block_start+n_superblock.s_first_blo+len(data_serializada):]
    particion_montada["datos"] = pre+data_serializada+post

    n_superblock.s_free_blocks_count -= 1
    n_superblock.s_first_blo += 1
    
    data_serializada =  n_inodo.serializar()
    pre = particion_montada["datos"][:n_superblock.s_inode_start+n_superblock.s_first_ino*n_superblock.s_inode_s]
    post = particion_montada["datos"][n_superblock.s_inode_start+n_superblock.s_first_ino*n_superblock.s_inode_s+len(data_serializada):]
    particion_montada["datos"] = pre+data_serializada+post

    pre = particion_montada["datos"][:n_superblock.s_bm_inode_start+n_superblock.s_first_ino]
    data_serializada = code_str("1",1)
    post = particion_montada["datos"][n_superblock.s_bm_inode_start+n_superblock.s_first_ino+len(data_serializada):]
    particion_montada["datos"] = pre+data_serializada+post

    n_superblock.s_free_inodes_count -= 1
    n_superblock.s_first_ino += 1        


    n_bloque = BloqueArchivos()
    n_bloque.setB_content("1,G,root\n1,U,root,root,123\n")

    data_serializada =  n_bloque.serializar()
    pre = particion_montada["datos"][:n_superblock.s_block_start+n_superblock.s_first_blo*n_superblock.s_block_s]
    post = particion_montada["datos"][n_superblock.s_block_start+n_superblock.s_first_blo*n_superblock.s_block_s+len(data_serializada):]
    particion_montada["datos"] = pre+data_serializada+post

    pre = particion_montada["datos"][:n_superblock.s_bm_block_start+n_superblock.s_first_blo]
    data_serializada = code_str("1",1)
    post = particion_montada["datos"][n_superblock.s_bm_block_start+n_superblock.s_first_blo+len(data_serializada):]
    particion_montada["datos"] = pre+data_serializada+post

    n_superblock.s_free_blocks_count -= 1
    n_superblock.s_first_blo += 1
    
    
    n_inodo = Inodo()
    i_uid = 1
    i_gid = 1
    i_s = 64
    i_atime = ""
    i_ctime = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    i_mtime = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    i_block = [1]+[-1 for x in range(14)]
    i_type = "1"
    i_perm = 6*8*8+6*8+4
    n_inodo.setAll(i_uid, i_gid, i_s, i_atime, i_ctime, i_mtime, i_block, i_type, i_perm)

    data_serializada =  n_inodo.serializar()
    pre = particion_montada["datos"][:n_superblock.s_inode_start+n_superblock.s_first_ino*n_superblock.s_inode_s]
    post = particion_montada["datos"][n_superblock.s_inode_start+n_superblock.s_first_ino*n_superblock.s_inode_s+len(data_serializada):]
    particion_montada["datos"] = pre+data_serializada+post

    pre = particion_montada["datos"][:n_superblock.s_bm_inode_start+n_superblock.s_first_ino]
    data_serializada = code_str("1",1)
    post = particion_montada["datos"][n_superblock.s_bm_inode_start+n_superblock.s_first_ino+len(data_serializada):]
    particion_montada["datos"] = pre+data_serializada+post

    n_superblock.s_free_inodes_count -= 1
    n_superblock.s_first_ino += 1

    pre = n_superblock.serializar()
    post = particion_montada["datos"][len(pre):]
    particion_montada["datos"] = pre+post

    res[0]["datos"] = particion_montada["datos"]

    mensaje += "Se ha inicializado el sistema de archivos EXT en la particion '"+identificador+"' exitosamente.\n"
    return mensaje