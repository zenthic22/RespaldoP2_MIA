import struct

def code_str(string, size):
    return string.encode('utf-8')[:size].ljust(size, b'\0')

#formatos de structs
formato_mbr = "i 19s i 1s"
formato_particion = "1s 1s 1s i i 16s"
formato_ebr = "1s 1s i i i 16s"
formato_superbloque = "i i i i i 19s 19s i i i i i i i i i i"
formato_inodo = "i i i 19s 19s 19s 15i 1s i"
formato_b_carpeta = "12s i"
formato_b_archivos = "64s"
formato_b_pointers = "16i"

#tamaños de cada estructura
sizeMBR = struct.calcsize(formato_mbr)
sizeEBR = struct.calcsize(formato_ebr)
sizePartition = struct.calcsize(formato_particion)
sizeSuperBlock = struct.calcsize(formato_superbloque)
sizeInodo = struct.calcsize(formato_inodo)
sizeBlock = 64

#clases para las estructuras
class BloqueApuntadores:
    def __init__(self):
        self.b_pointers = [-1]*16
    
    def setB_pointers(self, b_pointers):
        self.b_pointers = b_pointers
    
    def deserializar(self,data):
        self.b_pointers = struct.unpack(formato_b_pointers, data[:64])
    
    def serializar(self):
        res = struct.pack(formato_b_pointers, *self.b_pointers)
        return res
    
    def tree(self, num):
        c = ""
        dot = "B_"+str(num)+"""[shape=none label=<
        <TABLE border="0" cellspacing="0" cellpadding="10" bgcolor="lightgreen">
        <TR><TD border="1" port="top">B. apuntadores"""+str(num)+"</TD></TR>\n"
        for i in range(16):
            x = self.b_pointers[i]
            if x == -1:
                dot += '<TR>\n<TD border="1"> </TD>\n</TR>\n'
            else:
                dot += '<TR>\n<TD border="1" port="ap'+str(i+1)+'">'+str(x)+'</TD>\n</TR>\n'
            if x != -1:
                c += "B_"+str(num)+":ap"+str(i+1)+"->B_"+str(x)+":top\n"
        dot += "</TABLE>>];\n"
        
        return dot+c
    
    def graficar(self, num):
        dot = "B_"+str(num)+"""[shape=none label=<
        <TABLE border="0" cellspacing="0" cellpadding="10" bgcolor="lightgreen">
        <TR><TD border="1" port="top">B. apuntadores """+str(num)+"</TD></TR>\n"
        
        for i in range(16):
            x = self.b_pointers[i]
            if x == -1:
                dot += '<TR>\n<TD border="1"> </TD>\n</TR>\n'
            else:
                dot += '<TR>\n<TD border="1">'+str(x)+'</TD>\n</TR>\n'
        
        dot += "</TABLE>>];\n"
        return dot

class BloqueArchivos:
    def __init__(self):
        self.b_content = b'\0'*64
    
    def setB_content(self, b_content):
        self.b_content = code_str(b_content, 64)
    
    def deserializar(self, data):
        self.b_content = struct.unpack(formato_b_archivos, data[:64])[0]
    
    def serializar(self):
        res = struct.pack(formato_b_archivos, self.b_content)
        return res
    
    def tree(self, num):
        dot = "B_"+str(num)+"""[shape=none label=<
        <TABLE border="0" cellspacing="0" cellpadding="10" bgcolor="lightgoldenrod1">
        <TR><TD border="1" port="top">B. archivo """+str(num)+"</TD></TR>\n"
        
        dot += '<TR>\n<TD border="1">'+self.b_content.decode().strip('\x00')+'</TD>\n</TR>\n\n'
        dot += "</TABLE>>];\n"
        return dot
    
    def graficar(self, num):
        dot = "B_"+str(num)+"""[shape=none label=<
        <TABLE border="0" cellspacing="0" cellpadding="10" bgcolor="lightgoldenrod1">
        <TR><TD border="1" port="top">B. archivo """+str(num)+"</TD></TR>\n"
        
        dot += '<TR>\n<TD border="1">'+self.b_content.decode().strip('\x00')+'</TD>\n</TR>\n\n'
        dot += "</TABLE>>];\n"
        
        return dot
    
class BloqueCarpeta:
    def __init__(self):
        self.b_content = [CarpetaContent() for x in range(4)]
    
    def deserializar(self, data):
        for i in range(4):
            self.b_content[i].deserializar(data[16*i:])
    
    def serializar(self):
        res = b""
        for i in range(4):
            res += self.b_content[i].serializar()
        return res
    
    def tree(self, num):
        c = ""
        dot = "B_"+str(num)+"""[shape=none label=<
        <TABLE border="0" cellspacing="0" cellpadding="10" bgcolor="lightcoral">
        <TR><TD border="1" colspan="2" port="top">B. carpeta """+str(num)+"</TD></TR>\n"
        for i in range(4):
            x = self.b_content[i]
            if x.b_inodo == -1:
                dot += '<TR>\n<TD border="1"> </TD>\n<TD border="1"> </TD>\n</TR>\n'
            else:
                dot += '<TR>\n<TD border="1">'+x.b_name.decode().strip('\x00')+'</TD>\n<TD border="1" port="ap'+str(i+1)+'">'+str(x.b_inodo)+'</TD>\n</TR>\n'
            
            if x.b_inodo != -1 and x.b_name.decode().strip('\x00') not in [".",".."]:
                c += "B_"+str(num)+":ap"+str(i+1)+"->I_"+str(x.b_inodo)+":top\n"
        dot += "</TABLE>>];\n"
        
        return dot+c
    
    def graficar(self, num):
        dot = "B_"+str(num)+"""shape=none label=<
        <TABLE border="0" cellspacing="0" cellpadding="10" bgcolor="lightcoral">
        <TR><TD border="1" colspan="2">B. carpeta """+str(num)+"</TD></TR>\n"
        
        for i in range(4):
            x = self.b_content[i]
            if x.b_inodo == -1:
                dot += '<TR>\n<TD border="1"> </TD>\n<TD border="1" > </TD>\n</TR>\n'
            else:
                dot += '<TR>\n<TD border="1">'+x.b_name.decode().strip('\x00')+'</TD>\n<TD border="1">'+str(x.b_inodo)+'</TD>\n</TR>\n'
        
        dot += "</TABLE>>];\n"
        
        return dot

class CarpetaContent:
    def __init__(self):
        self.b_name = b'\0'*12
        self.b_inodo = -1
    
    def setB_name(self, b_name):
        self.b_name = code_str(b_name, 12)
    
    def setB_inodo(self, b_inodo):
        self.b_inodo = b_inodo
    
    def setAll(self, b_name, b_inodo):
        self.setB_name(b_name)
        self.setB_inodo(b_inodo)
    
    def deserializar(self,data):
        self.b_name,self.b_inodo = struct.unpack(formato_b_carpeta, data[:16])
        
    def serializar(self):
        res = struct.pack(formato_b_carpeta, self.b_name, self.b_inodo)
        return res
    
class Inodo:
    def __init__(self):
        self.i_uid = -1
        self.i_gid = -1
        self.i_s = -1
        self.i_atime = b'\0'*19
        self.i_ctime = b'\0'*19
        self.i_mtime = b'\0'*19
        self.i_block = [-1 for x in range(15)]
        self.i_type = b'\0'
        self.i_perm = -1
    
    def setI_uid(self, i_uid):
        self.i_uid = i_uid

    def setI_gid(self, i_gid):
            self.i_gid = i_gid

    def setI_s(self, i_s):
            self.i_s = i_s

    def setI_atime(self, i_atime):
        self.i_atime = code_str(i_atime,19)

    def setI_ctime(self, i_ctime):
        self.i_ctime = code_str(i_ctime,19)

    def setI_mtime(self, i_mtime):
        self.i_mtime = code_str(i_mtime,19)

    def setI_block(self, i_block):
            self.i_block = i_block

    def setI_type(self, i_type):
        self.i_type = code_str(i_type,1)

    def setI_perm(self, i_perm):
            self.i_perm = i_perm

    def setAll(self, i_uid, i_gid, i_s, i_atime, i_ctime, i_mtime, i_block, i_type, i_perm):
        self.setI_uid(i_uid)
        self.setI_gid(i_gid)
        self.setI_s(i_s)
        self.setI_atime(i_atime)
        self.setI_ctime(i_ctime)
        self.setI_mtime(i_mtime)
        self.setI_block(i_block)
        self.setI_type(i_type)
        self.setI_perm(i_perm)

    def deserializar(self,data):
        self.i_uid, self.i_gid, self.i_s, self.i_atime, self.i_ctime, self.i_mtime, *self.i_block, self.i_type, self.i_perm = struct.unpack(formato_inodo, data[:sizeInodo])

    def serializar(self):
        res = struct.pack(formato_inodo,  self.i_uid, self.i_gid, self.i_s, self.i_atime, self.i_ctime, self.i_mtime, *self.i_block, self.i_type, self.i_perm)
        return res
    
    def tree(self, num):
        c = ""
        dot = "I_"+str(num)+"""[shape=none label=<
        <TABLE border="0" cellspacing="0" cellpadding="10" bgcolor="lightskyblue2">
        <TR><TD border="1" colspan="2" port="top">Inodo """+str(num)+"</TD></TR>\n"
        
        dot += '<TR>\n<TD border="1">i_uid</TD>\n<TD border="1">'+str(self.i_uid)+'</TD>\n</TR>\n'
        dot += '<TR>\n<TD border="1">i_gid</TD>\n<TD border="1">'+str(self.i_gid)+'</TD>\n</TR>\n'
        dot += '<TR>\n<TD border="1">i_s</TD>\n<TD border="1">'+str(self.i_s)+'</TD>\n</TR>\n'
        dot += '<TR>\n<TD border="1">i_atime</TD>\n<TD border="1">'+self.i_atime.decode().strip('\x00')+'</TD>\n</TR>\n'
        dot += '<TR>\n<TD border="1">i_ctime</TD>\n<TD border="1">'+self.i_ctime.decode().strip('\x00')+'</TD>\n</TR>\n'
        dot += '<TR>\n<TD border="1">i_mtime</TD>\n<TD border="1">'+self.i_mtime.decode().strip('\x00')+'</TD>\n</TR>\n'
        dot += '<TR>\n<TD border="1">i_type</TD>\n<TD border="1">'+self.i_type.decode().strip('\x00')+'</TD>\n</TR>\n'
        perm_usr = int(self.i_perm/64)
        perm_grp = int((self.i_perm-perm_usr*64)/8)
        perm_otr = int(self.i_perm-perm_usr*64-perm_grp*8)
        dot += '<TR>\n<TD border="1">i_perm</TD>\n<TD border="1">'+str(perm_usr)+str(perm_grp)+str(perm_otr)+'</TD>\n</TR>\n'
        for i in range(15):
            dot += '<TR>\n<TD border="1">ap'+str(i+1)+'</TD>\n<TD border="1" port="ap'+str(i+1)+'">'+str(self.i_block[i])+'</TD>\n</TR>\n'
            if self.i_block[i] != -1:
                c += "I_"+str(num)+":ap"+str(i+1)+"->B_"+str(self.i_block[i])+":top\n"
        
        dot += "</TABLE>>];\n"
        return dot+c
    
    def graficar(self, num):
        dot = "I_"+str(num)+"""[shape=none label=<
        <TABLE border="0" cellspacing="0" cellpadding="10" bgcolor="lightskyblue2">
        <TR><TD border="1" colspan="2">Inodo """+str(num)+"</TD></TR>\n"
        
        dot += '<TR>\n<TD border="1">i_uid</TD>\n<TD border="1">'+str(self.i_uid)+'</TD>\n</TR>\n'
        dot += '<TR>\n<TD border="1">i_gid</TD>\n<TD border="1">'+str(self.i_gid)+'</TD>\n</TR>\n'
        dot += '<TR>\n<TD border="1">i_s</TD>\n<TD border="1">'+str(self.i_s)+'</TD>\n</TR>\n'
        dot += '<TR>\n<TD border="1">i_atime</TD>\n<TD border="1">'+self.i_atime.decode().strip('\x00')+'</TD>\n</TR>\n'
        dot += '<TR>\n<TD border="1">i_ctime</TD>\n<TD border="1">'+self.i_ctime.decode().strip('\x00')+'</TD>\n</TR>\n'
        dot += '<TR>\n<TD border="1">i_mtime</TD>\n<TD border="1">'+self.i_mtime.decode().strip('\x00')+'</TD>\n</TR>\n'
        dot += '<TR>\n<TD border="1">i_type</TD>\n<TD border="1">'+self.i_type.decode().strip('\x00')+'</TD>\n</TR>\n'
        perm_usr = int(self.i_perm/64)
        perm_grp = int((self.i_perm-perm_usr*64)/8)
        perm_otr = int(self.i_perm-perm_usr*64-perm_grp*8)
        dot += '<TR>\n<TD border="1">ap'+str(perm_usr)+str(perm_grp)+str(perm_otr)+'</TD>\n</TR>\n'
        for i in range(15):
            dot += '<TR>\n<TD border="1">ap'+str(i+1)+'</TD>\n<TD border="1">'+str(self.i_block[i])+'</TD>\n</TR>\n'
        
        dot += "</TABLE>>];\n"
        
        return dot

class SuperBlock:
    def __init__(self):
        self.s_filesystem_type = -1
        self.s_inodes_count = -1
        self.s_blocks_count = -1
        self.s_free_blocks_count = -1
        self.s_free_inodes_count = -1
        self.s_mtime = b'\0'*19
        self.s_umtime = b'\0'*19
        self.s_mnt_count = -1
        self.s_magic = -1
        self.s_inode_s = -1
        self.s_block_s = -1
        self.s_first_ino = -1
        self.s_first_blo = -1
        self.s_bm_inode_start = -1
        self.s_bm_block_start = -1
        self.s_inode_start = -1
        self.s_block_start = -1
    
    def setS_filesystem_type(self, s_filesystem_type):
        self.s_filesystem_type = s_filesystem_type
    
    def setS_inodes_count(self, s_inodes_count):
        self.s_inodes_count = s_inodes_count
    
    def setS_blocks_count(self, s_blocks_count):
        self.s_blocks_count = s_blocks_count
    
    def setS_free_blocks_count(self, s_free_blocks_count):
        self.s_free_blocks_count = s_free_blocks_count
    
    def setS_mtime(self, s_mtime):
        self.s_mtime = code_str(s_mtime, 19)
    
    def setS_umtime(self, s_umtime):
        self.s_umtime = code_str(s_umtime, 19)
    
    def setS_free_inodes_count(self, s_free_inodes_count):
        self.s_free_inodes_count = s_free_inodes_count
    
    def setS_mnt_count(self, s_mnt_count):
        self.s_mnt_count = s_mnt_count
    
    def setS_magic(self, s_magic):
        self.s_magic = s_magic
    
    def setS_inode_s(self, s_inode_s):
        self.s_inode_s = s_inode_s
    
    def setS_block_s(self, s_block_s):
        self.s_block_s = s_block_s
    
    def setS_first_ino(self, s_first_ino):
        self.s_first_ino = s_first_ino
    
    def setS_first_blo(self, s_first_blo):
        self.s_first_blo = s_first_blo
    
    def setS_bm_inode_start(self, s_bm_inode_start):
        self.s_bm_inode_start = s_bm_inode_start
        
    def setS_bm_block_start(self, s_bm_block_start):
        self.s_bm_block_start = s_bm_block_start

    def setS_inode_start(self, s_inode_start):
        self.s_inode_start = s_inode_start

    def setS_block_start(self, s_block_start):
        self.s_block_start = s_block_start
    
    def setAll(self,s_filesystem_type, s_inodes_count, s_blocks_count, s_free_blocks_count, s_free_inodes_count, s_mtime, s_umtime, s_mnt_count, s_magic, s_inode_s, s_block_s, s_first_ino, s_first_blo, s_bm_inode_start, s_bm_block_start, s_inode_start, s_block_start):
        self.setS_filesystem_type(s_filesystem_type)
        self.setS_inodes_count(s_inodes_count)
        self.setS_blocks_count(s_blocks_count)
        self.setS_free_blocks_count(s_free_blocks_count)
        self.setS_free_inodes_count(s_free_inodes_count)
        self.setS_mtime(s_mtime)
        self.setS_umtime(s_umtime)
        self.setS_mnt_count(s_mnt_count)
        self.setS_magic(s_magic)
        self.setS_inode_s(s_inode_s)
        self.setS_block_s(s_block_s)
        self.setS_first_ino(s_first_ino)
        self.setS_first_blo(s_first_blo)
        self.setS_bm_inode_start(s_bm_inode_start)
        self.setS_bm_block_start(s_bm_block_start)
        self.setS_inode_start(s_inode_start)
        self.setS_block_start(s_block_start)

    def deserializar(self,data):
        self.s_filesystem_type, self.s_inodes_count, self.s_blocks_count, self.s_free_blocks_count, self.s_free_inodes_count, self.s_mtime, self.s_umtime, self.s_mnt_count, self.s_magic, self.s_inode_s, self.s_block_s, self.s_first_ino, self.s_first_blo, self.s_bm_inode_start, self.s_bm_block_start, self.s_inode_start, self.s_block_start = struct.unpack(formato_superbloque, data[:sizeSuperBlock])

    def serializar(self):
        res = struct.pack(formato_superbloque,  self.s_filesystem_type, self.s_inodes_count, self.s_blocks_count, self.s_free_blocks_count, self.s_free_inodes_count, self.s_mtime, self.s_umtime, self.s_mnt_count, self.s_magic, self.s_inode_s, self.s_block_s, self.s_first_ino, self.s_first_blo, self.s_bm_inode_start, self.s_bm_block_start, self.s_inode_start, self.s_block_start)
        return res
    
    def graficar(self):
        dot = """SB[shape=none label=<
        <TABLE border="0" cellspacing="0" cellpadding="10">
        <TR><TD border="1" colspan="2" bgcolor="darkgreen" ><FONT color="white">Reporte <B>SB</B></FONT></TD></TR>\n"""
        
        dot += '<TR>\n<TD border="1">s_filesystem_type</TD>\n<TD border="1">'+str(self.s_filesystem_type)+'</TD>\n</TR>\n'
        dot += '<TR>\n<TD border="1" bgcolor="mediumseagreen">s_inodes_count</TD>\n<TD border="1" bgcolor="mediumseagreen">'+str(self.s_inodes_count)+'</TD>\n</TR>\n'
        dot += '<TR>\n<TD border="1">s_blocks_count</TD>\n<TD border="1">'+str(self.s_blocks_count)+'</TD>\n</TR>\n'
        dot += '<TR>\n<TD border="1" bgcolor="mediumseagreen">s_free_inodes_count</TD>\n<TD border="1" bgcolor="mediumseagreen">'+str(self.s_free_inodes_count)+'</TD>\n</TR>\n'
        dot += '<TR>\n<TD border="1">s_free_blocks_count</TD>\n<TD border="1">'+str(self.s_free_blocks_count)+'</TD>\n</TR>\n'
        dot += '<TR>\n<TD border="1" bgcolor="mediumseagreen">s_mtime</TD>\n<TD border="1" bgcolor="mediumseagreen">'+self.s_mtime.decode().strip('\x00')+'</TD>\n</TR>\n'
        dot += '<TR>\n<TD border="1">s_umtime</TD>\n<TD border="1">'+self.s_umtime.decode().strip('\x00')+'</TD>\n</TR>\n'
        dot += '<TR>\n<TD border="1" bgcolor="mediumseagreen">s_mnt_count</TD>\n<TD border="1" bgcolor="mediumseagreen">'+str(self.s_mnt_count)+'</TD>\n</TR>\n'
        dot += '<TR>\n<TD border="1">s_magic</TD>\n<TD border="1">'+str(self.s_magic)+'</TD>\n</TR>\n'
        dot += '<TR>\n<TD border="1" bgcolor="mediumseagreen">s_inode_s</TD>\n<TD border="1" bgcolor="mediumseagreen">'+str(self.s_inode_s)+'</TD>\n</TR>\n'
        dot += '<TR>\n<TD border="1">s_block_s</TD>\n<TD border="1">'+str(self.s_block_s)+'</TD>\n</TR>\n'
        dot += '<TR>\n<TD border="1" bgcolor="mediumseagreen">s_first_ino</TD>\n<TD border="1" bgcolor="mediumseagreen">'+str(self.s_first_ino)+'</TD>\n</TR>\n'
        dot += '<TR>\n<TD border="1">s_first_blo</TD>\n<TD border="1">'+str(self.s_first_blo)+'</TD>\n</TR>\n'
        dot += '<TR>\n<TD border="1" bgcolor="mediumseagreen">s_bm_inode_start</TD>\n<TD border="1" bgcolor="mediumseagreen">'+str(self.s_bm_inode_start)+'</TD>\n</TR>\n'
        dot += '<TR>\n<TD border="1">s_bm_block_start</TD>\n<TD border="1">'+str(self.s_bm_block_start)+'</TD>\n</TR>\n'
        dot += '<TR>\n<TD border="1" bgcolor="mediumseagreen">s_inode_start</TD>\n<TD border="1" bgcolor="mediumseagreen">'+str(self.s_inode_start)+'</TD>\n</TR>\n'
        dot += '<TR>\n<TD border="1">s_block_start</TD>\n<TD border="1">'+str(self.s_block_start)+'</TD>\n</TR>\n'
        dot +="</TABLE>>];\n"
        
        return dot

class MBR:
    def __init__(self):
        self.mbr_tamanio = -1
        self.mbr_fecha_creacion = b'\0'*19
        self.mbr_dsk_signature = -1
        self.dsk_fit = b'\0'
        self.mbr_partition = [Particion(),Particion(),Particion(),Particion()]
    
    def setTamanio(self, tam):
        self.mbr_tamanio = tam
    
    def setFecha(self, fecha):
        self.mbr_fecha_creacion = code_str(fecha, 19)
    
    def setSignature(self, signature):
        self.mbr_dsk_signature = signature
    
    def setFit(self, fit):
        self.dsk_fit = code_str(fit, 1)
    
    def setAll(self, tamanio, fecha, signature, fit):
        self.setFecha(fecha)
        self.setTamanio(tamanio)
        self.setSignature(signature)
        self.setFit(fit)
        
    def deserializar(self, data):
        self.mbr_tamanio,self.mbr_fecha_creacion,self.mbr_dsk_signature,self.dsk_fit = struct.unpack(formato_mbr, data[:sizeMBR])
        for i in range(4):
            self.mbr_partition[i].deserializar(data[sizeMBR+sizePartition*i:])
        
    def serializar(self):
        res = struct.pack(formato_mbr, self.mbr_tamanio, self.mbr_fecha_creacion, self.mbr_dsk_signature, self.dsk_fit)
        for x in self.mbr_partition:
            res += x.serializar()
        return res
    
    def imprimir(self, path):
        dot = """digraph G {
            fontname="Edu NSW ACT Foundation, cursive"
            node [fontname="Edu NSW ACT Foundation, cursive"]
            edge [fontname="Edu NSW ACT Foundation, cursive"]
            M [shape=none label=<
            <TABLE border="1" cellspacing="0" cellpadding="10">
            <TR><TD border="1" colspan="2" bgcolor="indigo"><FONT color="white"><B>MBR</B></FONT></TD></TR>\n"""
        
        dot += '<TR><TD>mbr_tamanio</TD><TD>'+str(self.mbr_tamanio)+'</TD></TR>\n'
        dot += '<TR><TD bgcolor="mediumpurple1">mbr_fecha_creacion</TD><TD bgcolor="mediumpurple1">'+self.mbr_fecha_creacion.decode()+'</TD></TR>\n'
        dot += '<TR><TD>mbr_dsk_signature</TD><TD>'+str(self.mbr_dsk_signature)+'</TD></TR>\n'
        for x in self.mbr_partition:
            if x.part_start == -1:
                continue
            dot += x.imprimir()
            if x.part_type.decode().upper() == "E":
                dot += imprimirExtendida(x, path)
        dot += "</TABLE>>];}"
        
        return dot
    
    def showdisk(self, path):
        s = """digraph G {
            fontname="Edu NSW ACT Foundation, cursive"
            node [fontname="Edu NSW ACT Foundation, cursive"]
            edge [fontname="Edu NSW ACT Foundation, cursive"]
            a0 [shape=none label=<
            <TABLE border="1" cellspacing="0" cellpadding="10">
            <TR>
            <TD>MBR</TD>
            """
        
        espacio_disponible = self.mbr_tamanio-sizeMBR-4*sizePartition
        self.mbr_partition.sort(key=lambda x:x.part_start)
        inicio = len(self.serializar())
        longitudes = []
        for i in range(len(self.mbr_partition)):
            x = self.mbr_partition[i]
            
            if x.part_start == 0:
                continue
            
            espacio_libre = x.part_start-inicio-1
            if round(espacio_libre/espacio_disponible*100, 2) > 0:
                s += "<TD> Libre <BR/><BR/>"+str(round(espacio_libre/espacio_disponible*100, 2))+"%</TD>"
                
            if x.part_type.decode().upper() == "P":
                s += "<TD> Primaria <BR/><BR/>"+str(round(x.part_size/espacio_disponible*100, 2))+"%</TD>"
            elif x.part_type.decode().upper() == "E":
                s += showExtendida(x, espacio_disponible, path)
            
            inicio = x.part_start+x.part_size
        
        espacio_libre = self.mbr_tamanio-inicio-1
        if espacio_libre > 0:
            s += "<TD> Libre <BR/><BR/>"+str(round(espacio_libre/espacio_disponible*100, 2))+"%</TD>"
        
        s += "</TR>"
        s += "</TABLE>>];}"
        
        return s

class Particion:
    def __init__(self):
        self.part_status = b'\0'
        self.part_type = b'\0'
        self.part_fit = b'\0'
        self.part_start = -1
        self.part_size = -1
        self.part_name = b'\0'*16
    
    def setStatus(self, status):
        self.part_status = code_str(status, 1)
    
    def setType(self, type):
        self.part_type = code_str(type, 1)
    
    def setFit(self, fit):
        self.part_fit = code_str(fit, 1)
    
    def setStart(self, start):
        self.part_start = start
    
    def setSize(self, size):
        self.part_size = size
    
    def setName(self, name):
        self.part_name = code_str(name, 16)
    
    def setAll(self, status, _type, fit, start, size, name):
        self.setStatus(status)
        self.setType(_type)
        self.setFit(fit)
        self.setStart(start)
        self.setSize(size)
        self.setName(name)
        
    def serializar(self):
        res = struct.pack(formato_particion, self.part_status, self.part_type, self.part_fit, self.part_start, self.part_size, self.part_name)
        return res
    
    def deserializar(self, data):
        self.part_status,self.part_type,self.part_fit,self.part_start,self.part_size,self.part_name = struct.unpack(formato_particion, data[:sizePartition])
    
    def imprimir(self):
        dot = """<TR><TD border="1" colspan="2" bgcolor="indigo" ><FONT color="white"><B>Particion</B></FONT></TD></TR>\n"""
        dot +='<TR><TD>part_status</TD><TD>'+self.part_status.decode().strip("\x00")+'</TD></TR>\n'
        dot +='<TR><TD bgcolor="mediumpurple1">part_type</TD><TD bgcolor="mediumpurple1">'+self.part_type.decode().strip("\x00")+'</TD></TR>\n'
        dot +='<TR><TD>part_fit</TD><TD>'+self.part_fit.decode().strip("\x00")+'</TD></TR>'
        dot +='<TR><TD bgcolor="mediumpurple1">part_start</TD><TD bgcolor="mediumpurple1">'+str(self.part_start)+'</TD></TR>\n'
        dot +='<TR><TD>part_s</TD><TD>'+str(self.part_size)+' byte(s)</TD></TR>'
        dot +='<TR><TD bgcolor="mediumpurple1">part_name</TD><TD bgcolor="mediumpurple1">'+self.part_name.decode().strip("\x00")+'</TD></TR>\n'
        return dot

class EBR:
    def __init__(self):
        self.part_status = b'\0'
        self.part_fit = b'\0'
        self.part_start = -1
        self.part_size = -1
        self.part_next = -1
        self.part_name = b'\0'*16
    
    def setStatus(self, status):
        self.part_status = code_str(status, 1)
    
    def setNext(self, _next):
        self.part_next = _next
    
    def setFit(self, fit):
        self.part_fit = code_str(fit, 1)
    
    def setStart(self, start):
        self.part_start = start
    
    def setSize(self, size):
        self.part_size = size
    
    def setName(self, name):
        self.part_name = code_str(name, 16)
    
    def setAll(self, status, fit, start, size, _next, name):
        self.setStatus(status)
        self.setFit(fit)
        self.setStart(start)
        self.setSize(size)
        self.setNext(_next)
        self.setName(name)
    
    def serializar(self):
        res = struct.pack(formato_ebr, self.part_status, self.part_fit, self.part_start, self.part_size, self.part_next, self.part_name)
        return res

    def deserializar(self, data):
        self.part_status,self.part_fit,self.part_start,self.part_size,self.part_next,self.part_name = struct.unpack(formato_ebr, data[:sizeEBR])
    
    def imprimir(self):
        dot = """<TR><TD border="1" colspan="2" bgcolor="lightcoral"><FONT color="white"><B>Particion Logica</B></FONT></TD></TR>\n"""
        dot += '<TR><TD>part_status</TD><TD>'+self.part_status.decode().strip("\x00")+'</TD></TR>\n'
        dot += '<TR><TD bgcolor="lightpink">part_next</TD><TD bgcolor="lightpink">'+str(self.part_next)+'</TD></TR>\n'
        dot += '<TR><TD>part_fit</TD><TD>'+self.part_fit.decode().strip("\x00")+'</TD></TR>\n'
        dot += '<TR><TD bgcolor="lightpink">part_start</TD><TD bgcolor="lightpink">'+str(self.part_start)+'</TD></TR>\n'
        dot += '<TR><TD>part_size</TD><TD>'+str(self.part_size)+' byte(s)</TD></TR>\n'
        dot += '<TR><TD bgcolor="lightpink">part_name</TD><TD bgcolor="lightpink">'+self.part_name.decode().strip("\x00")+'</TD></TR>\n'
        return dot

def imprimirExtendida(part, path):
    dot = ""
    with open(path, "rb") as f:
        f.seek(part.part_start)
        contenido = f.read(part.part_size)
        f.close()
        
    ebr = EBR()
    porcion = contenido
    ebr.deserializar(porcion)
    aceptados = ["1","0"]
    if ebr.part_status.decode() not in aceptados:
        return dot
    else:
        while True:
            ebr.deserializar(porcion)
            dot += ebr.imprimir()
            if ebr.part_next == -1:
                break
            porcion = contenido[ebr.part_next:]
    return dot

def showExtendida(part, espacio_disponible, path):
    dot = ""
    colspan = 0
    with open(path, "rb") as f:
        f.seek(part.part_start)
        contenido = f.read(part.part_size)
        f.close()
    
    ebr = EBR()
    porcion = contenido
    ebr.deserializar(porcion)
    aceptados = ["1","0"]
    
    if ebr.part_status.decode() not in aceptados:
        dot += "<TD>"+str(round(part.part_size/espacio_disponible*100,2))+"%</TD>\n"
        colspan += 1
    else:
        inicio = 0
        rangos_ocupados = []
        while True:
            ebr.deserializar(porcion)
            rangos_ocupados.append((inicio,ebr.part_start+ebr.part_size))
            inicio = inicio+sizeEBR+ebr.part_size
            if ebr.part_next == -1:
                break
            porcion = contenido[ebr.part_next:]
        rangos_ocupados.sort(key=lambda x:x[0])
        for i in range(len(rangos_ocupados)):
            size = rangos_ocupados[i][1]-rangos_ocupados[i][0]
            dot += "<TD>EBR</TD>\n"
            dot += "<TD> Logica <BR/><BR/>"+str(round(size/espacio_disponible*100,2))+"%</TD>\n"
            colspan += 2
            if i < len(rangos_ocupados)-1:
                size = rangos_ocupados[i+1][0]-rangos_ocupados[i][1]
                size = round(size/espacio_disponible*100,2)
                if size > 0:
                    dot += "<TD> Libre <BR/><BR/>"+str(size)+"%</TD>\n"
                    colspan += 1
            else:
                size = part.part_size-rangos_ocupados[i][1]
                size = round(size/espacio_disponible*100,2)
                if size > 0:
                    dot += "<TD> Libre <BR/><BR/>"+str(size)+"%</TD>\n"
                    colspan += 1
    
    dot = '<TD><TABLE border="1" cellspacing="0" cellpadding="10">\n<TR>\n<TD colspan="'+str(colspan)+'">Extendida</TD>\n</TR>\n<TR>\n'+dot+"</TR>\n</TABLE>\n</TD>\n"
    return dot