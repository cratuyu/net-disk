from os import path,makedirs
ADDR = ("127.0.0.1", 8888)   # 176.20.85.252
# 文件默认存储路径
FILE_PATH = "/home/tarena/桌面/网盘文件/"
if not path.isdir(FILE_PATH):
    makedirs(FILE_PATH)